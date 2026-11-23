#!/usr/bin/env python3
"""Imagine Kit: make and rework images on your own Mac, from a prompt and optional source images.

This one file is the whole program: the image engine, the command line, and the
small web server behind the app in your browser. It needs only the Python
standard library; the image models run through mflux, which install.sh sets up.

Run `./imagine` for the app, or `./imagine help` for the commands.
"""
import argparse
import base64
import hashlib
import json
import os
import pathlib
import platform
import random
import re
import shutil
import signal
import struct
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "0.1.0"
HOME = pathlib.Path(__file__).resolve().parent


class Settings:
    """Everything the kit reads from the environment, in one place.

    The IMAGINE_KIT_FAKE group exists for the tests and screen checks: with it
    on, a render draws a flat PNG and no model is loaded.
    """

    env = os.environ
    data = pathlib.Path(env.get("IMAGINE_KIT_DATA", HOME / "data"))
    bin = pathlib.Path(env.get("IMAGINE_KIT_BIN", HOME / ".venv" / "bin"))
    hf_home = pathlib.Path(env.get("HF_HOME", pathlib.Path.home() / ".cache" / "huggingface"))
    ollama = env.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    net = pathlib.Path(env.get("IMAGINE_KIT_NET") or pathlib.Path.home() / ".config" / "lm" / "net")
    fake = env.get("IMAGINE_KIT_FAKE") == "1"
    fake_missing = env.get("IMAGINE_KIT_FAKE_MISSING", "").split(",")
    fake_step_s = float(env.get("IMAGINE_KIT_FAKE_STEP_S", "0.05"))
    fake_fail = env.get("IMAGINE_KIT_FAKE_FAIL") == "1"
    fake_ram_gb = int(env.get("IMAGINE_KIT_FAKE_RAM_GB", "0"))
    fake_gpu_gb = int(env.get("IMAGINE_KIT_FAKE_GPU_GB", "0"))
    fake_no_engine = env.get("IMAGINE_KIT_FAKE_NO_ENGINE") == "1"


DATA, BIN, FAKE = Settings.data, Settings.bin, Settings.fake
OUT, SRC, TRASH = DATA / "images", DATA / "sources", DATA / "trash"
HISTORY = DATA / "history.jsonl"

# Each model the kit knows. `edit` is the program that takes source images and
# an instruction; a model without one can only start loosely from one image.
MODELS = {
    "klein": {
        "name": "FLUX.2 klein 4B",
        "blurb": "Fast, and the one that can rework source images. Runs on a 16 GB Mac.",
        "repo": "black-forest-labs/FLUX.2-klein-4B",
        "include": ["transformer/*", "text_encoder/*", "vae/*", "tokenizer/*", "scheduler/*", "model_index.json"],
        "disk_gb": 16, "min_ram_gb": 16, "grant_gb": 28, "engine": "mflux",
        "gen": "mflux-generate-flux2", "edit": "mflux-generate-flux2-edit",
        "args": ["--model", "flux2-klein-4b"],
        "steps": 4, "guidance": None, "licence": "Apache 2.0",
    },
    "qwen": {
        "name": "Qwen-Image",
        "blurb": "Slower and much larger. The best at readable text inside an image. Needs a 64 GB Mac.",
        "repo": "Qwen/Qwen-Image",
        "include": ["transformer/*", "text_encoder*/*", "vae/*", "tokenizer*/*", "scheduler/*", "model_index.json"],
        "disk_gb": 50, "min_ram_gb": 48, "grant_gb": 44, "engine": "mflux",
        "gen": "mflux-generate-qwen", "edit": None,
        "args": [],
        "steps": 20, "guidance": 4, "licence": "Apache 2.0",
    },
}

# Models that run at a company, not on this computer. Each needs that company's
# key, and everything in a request (the prompt and any source images) is sent there.
CLOUD = {
    "gemini": {"who": "Google", "env": "GEMINI_API_KEY", "page": "https://aistudio.google.com/apikey",
               "pick": "IMAGINE_KIT_GEMINI_MODEL"},
    "openai": {"who": "OpenAI", "env": "OPENAI_API_KEY", "page": "https://platform.openai.com/api-keys",
               "pick": "IMAGINE_KIT_OPENAI_MODEL"},
}
for _key, _name, _cloud in (("gemini", "Gemini image", "gemini"), ("gpt", "GPT image", "openai")):
    MODELS[_key] = {
        "name": _name, "cloud": _cloud, "engine": _cloud, "edit": True, "repo": "", "include": [],
        "blurb": f"Runs at {CLOUD[_cloud]['who']}, not on this computer. Your prompt and source images are sent there.",
        "disk_gb": 0, "min_ram_gb": 0, "grant_gb": 0, "gen": "", "args": [], "steps": 1, "guidance": None,
        "licence": f"{CLOUD[_cloud]['who']}'s terms",
    }

STYLES = {
    "photo": "photorealistic, shot on a 35mm lens, natural light, sharp focus",
    "cinematic": "a cinematic film still with dramatic lighting and shallow depth of field",
    "illustration": "a clean editorial illustration with flat colours and confident line work",
    "watercolor": "a watercolour painting with soft washes on textured paper",
    "anime": "anime style with clean line art and cel shading",
    "3d": "a 3D render with soft global illumination",
    "product": "a studio product photograph on a plain backdrop with soft, even light",
}


class KitError(Exception):
    """A problem the person can act on. `code` is stable; `message` is for reading."""

    def __init__(self, code, message, fix=""):
        super().__init__(message)
        self.code, self.message, self.fix = code, message, fix

    def as_dict(self):
        return {"ok": False, "code": self.code, "message": self.message, "fix": self.fix}


# The machine: memory, disk, and which models are ready.

def ram_gb():
    """This machine's memory in GB, or 0 when it cannot be read."""
    if Settings.fake_ram_gb:
        return Settings.fake_ram_gb
    try:
        if hasattr(os, "sysconf") and "SC_PHYS_PAGES" in os.sysconf_names:      # macOS and Linux
            return round(os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") / 2**30)
        import ctypes                                                           # Windows

        class Memory(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong) for name in ("total", "avail", "page_total", "page_avail",
                                                        "virtual_total", "virtual_avail", "extended")]
        mem = Memory(length=ctypes.sizeof(Memory))
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
        return round(mem.total / 2**30)
    except (ValueError, OSError, AttributeError):
        return 0


def machine():
    """What this computer is and how much it can run: its system, chip, memory and tier.

    The tier decides how a local model is loaded. `full` loads it as is, `tight`
    loads a lighter copy, and `none` means no local model fits, with `why` saying
    so in words a person can act on.
    """
    system = {"Darwin": "mac", "Linux": "linux", "Windows": "windows"}.get(platform.system(), "linux")
    chip = "apple" if system == "mac" and platform.machine() == "arm64" else platform.machine().lower()
    ram = ram_gb()
    if ram == 0 or ram >= 24:
        tier, why = "full", ""
    elif ram >= 16:
        tier, why = "tight", f"With {ram} GB of memory the model loads a lighter copy, which is a little slower."
    else:
        tier, why = "none", (f"This computer has {ram} GB of memory, and the smallest local model needs 16. "
                             "Use a model that runs on another machine.")
    return {"os": system, "chip": chip, "ram_gb": ram, "gpu_gb": gpu_gb(), "tier": tier, "why": why}


def gpu_gb():
    """Memory on this computer's NVIDIA graphics card in GB, or 0 when it has none."""
    if Settings.fake_gpu_gb:
        return Settings.fake_gpu_gb
    if not shutil.which("nvidia-smi"):
        return 0
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10).stdout
        return round(max(int(line) for line in out.split()) / 1024)
    except (ValueError, OSError, subprocess.SubprocessError):
        return 0


def hf_cache(repo):
    return Settings.hf_home / "hub" / ("models--" + repo.replace("/", "--"))


def dir_gb(path):
    """Size on disk in GB. Counts each real file once, because the cache links to its own blobs."""
    total, seen = 0, set()
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                st = os.stat(os.path.join(root, name))
            except OSError:
                continue
            if st.st_ino in seen:
                continue
            seen.add(st.st_ino)
            total += st.st_blocks * 512 if hasattr(st, "st_blocks") else st.st_size      # Windows has no block count
    return total / 2**30


def model_status(key):
    """Whether a model can render right now, and if not, why."""
    m = MODELS[key]
    if m.get("cloud"):
        have_key = (key not in Settings.fake_missing) if FAKE else bool(api_key(m["cloud"]))
        about = CLOUD[m["cloud"]]
        return {"id": key, "name": m["name"], "blurb": m["blurb"], "licence": m["licence"], "disk_gb": 0, "have_gb": 0,
                "ready": have_key, "min_ram_gb": 0, "ram_ok": True, "can_edit": True, "steps": 1,
                "cloud": m["cloud"], "who": about["who"], "key_page": about["page"]}
    if FAKE:
        have, partial = (0 if key in Settings.fake_missing else m["disk_gb"]), False
    else:
        cache = hf_cache(m["repo"])
        have = dir_gb(cache) if cache.is_dir() else 0
        partial = any((cache / "blobs").glob("*.incomplete")) if cache.is_dir() else False
    ready = have >= m["disk_gb"] * 0.9 and not partial
    ram = ram_gb()
    engine_ok, engine_fix = ENGINES[m["engine"]].ready() if m["engine"] in ENGINES else (False, "")
    return {
        # Whether this computer can run the model at all, apart from whether it is downloaded.
        "engine_ok": engine_ok, "engine_fix": engine_fix,
        "id": key, "name": m["name"], "blurb": m["blurb"], "licence": m["licence"],
        "disk_gb": m["disk_gb"], "have_gb": round(have, 1), "ready": ready,
        "min_ram_gb": m["min_ram_gb"], "ram_ok": ram == 0 or ram >= m["min_ram_gb"],
        "can_edit": bool(m["edit"]), "steps": m["steps"],
    }


def api_key(provider):
    """The key for a company's models: from the environment first, then the one saved in the app."""
    found = Settings.env.get(CLOUD[provider]["env"], "").strip() or _saved_keys().get(provider, "")
    if not found and provider == "gemini" and not FAKE:
        # Google's own command-line tool keeps its key here, so a person who uses it need not paste it again.
        try:
            for line in (pathlib.Path.home() / ".gemini" / ".env").read_text().splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    found = line.split("=", 1)[1].strip().strip("'\"")
        except OSError:
            pass
    return found


def _saved_keys():
    try:
        return json.loads((DATA / "keys.json").read_text())
    except (OSError, ValueError):
        return {}


def save_key(provider, key):
    """Keep a company's key on this computer, readable only by its owner. An empty key forgets it."""
    if provider not in CLOUD:
        raise KitError("unknown_model", "There is no such service.")
    key = "".join(str(key).split())
    if key and len(key) < 20:
        raise KitError("bad_key", "That does not look like a whole key.", "Copy all of it and paste it again.")
    keys = _saved_keys()
    keys.pop(provider, None)
    if key:
        keys[provider] = key
    DATA.mkdir(parents=True, exist_ok=True)
    path = DATA / "keys.json"
    path.write_text(json.dumps(keys) + "\n")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def default_model():
    """The first model this computer can use right now; klein when none is."""
    for key in MODELS:
        s = model_status(key)
        if s["ready"] and s["ram_ok"] and s.get("engine_ok", True):
            return key
    return "klein"


# History: one JSON line per image, holding everything needed to make it again.

_hist_lock = threading.Lock()


def read_history(include_deleted=False):
    if not HISTORY.is_file():
        return []
    rows = []
    for line in HISTORY.read_text().splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    # An image made before threads existed joins the thread of the image it came from.
    by_id = {r.get("id"): r for r in rows}
    for row in rows:
        if row.get("thread"):
            continue
        top, seen = row, set()
        while top.get("parent") in by_id and top.get("id") not in seen:
            seen.add(top.get("id"))
            top = by_id[top["parent"]]
        row["thread"] = top.get("thread") or f"e{top.get('id')}"
    return [r for r in rows if include_deleted or not r.get("deleted")]


def thread_names():
    """The names people gave their threads. A thread with no name shows its first prompt."""
    try:
        return json.loads((DATA / "threads.json").read_text())
    except (OSError, ValueError):
        return {}


def name_thread(thread, title):
    with _hist_lock:
        names = thread_names()
        names[str(thread)] = " ".join(str(title).split())[:80]
        DATA.mkdir(parents=True, exist_ok=True)
        (DATA / "threads.json").write_text(json.dumps(names, indent=2) + "\n")


def write_history(rows):
    DATA.mkdir(parents=True, exist_ok=True)
    tmp = HISTORY.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(r) + "\n" for r in rows))
    tmp.replace(HISTORY)


def add_entry(entry):
    with _hist_lock:
        rows = read_history(include_deleted=True)
        entry["id"] = max([r.get("id", 0) for r in rows] + [0]) + 1
        if not entry.get("thread"):          # a follow-up stays in its image's thread; anything else starts one
            parent = next((r for r in rows if r.get("id") == entry.get("parent")), None)
            entry["thread"] = parent["thread"] if parent else f"t{time.time_ns()}"
        rows.append(entry)
        write_history(rows)
    return entry


def update_entry(entry_id, **changes):
    with _hist_lock:
        rows = read_history(include_deleted=True)
        hit = None
        for row in rows:
            if row.get("id") == entry_id:
                row.update(changes)
                hit = row
        if hit is None:
            raise KitError("no_such_image", f"There is no image number {entry_id}.")
        write_history(rows)
    return hit


def get_entry(entry_id):
    for row in read_history():
        if row.get("id") == entry_id:
            return row
    raise KitError("no_such_image", f"There is no image number {entry_id}.", "Run: ./imagine history")


def remove_entry(entry_id):
    """Take an image out of the history. Its files move to data/trash, so it can be put back by hand."""
    e = get_entry(entry_id)
    TRASH.mkdir(parents=True, exist_ok=True)
    for src in (pathlib.Path(e["output"]), details_path(e["output"])):
        if src.is_file():
            shutil.move(str(src), str(TRASH / src.name))
    update_entry(entry_id, deleted=True)


# Source images: the pictures a person hands in to be reworked.

IMAGE_TYPES = {b"\x89PNG": ".png", b"\xff\xd8\xff": ".jpg", b"RIFF": ".webp", b"GIF8": ".gif"}


def save_source(data, name="image"):
    """Keep a copy of a source image, named by its content so the same image is stored once."""
    ext = next((e for magic, e in IMAGE_TYPES.items() if data.startswith(magic)), None)
    if ext is None and name.lower().endswith((".heic", ".heif", ".tiff", ".tif", ".bmp")):
        ext = pathlib.Path(name).suffix.lower()
    if ext is None:
        raise KitError("not_an_image", f"{name} is not an image the kit can read.",
                       "Use a PNG, JPEG, WebP, HEIC or TIFF file.")
    SRC.mkdir(parents=True, exist_ok=True)
    path = SRC / (hashlib.sha256(data).hexdigest()[:16] + ext)
    if not path.exists():
        path.write_bytes(data)
    if ext not in (".png", ".jpg"):      # the models read PNG and JPEG, so the rest are converted
        png = path.with_suffix(".png")
        if not png.exists():
            to_png(path, png)
        if png.exists():
            path = png
    return path


def to_png(src, dst):
    """Convert an image to PNG with whatever this machine has: Pillow first, then the macOS image tool."""
    try:
        from PIL import Image
        with Image.open(src) as im:
            im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB").save(dst)
        return
    except Exception:                    # no Pillow, or a format it cannot open (HEIC without its plugin)
        pass
    if shutil.which("sips"):
        subprocess.run(["sips", "-s", "format", "png", str(src), "--out", str(dst)], capture_output=True)


def resolve_source(ref):
    """A source can be a stored file name, a past image (`#12`), or a path on disk."""
    ref = str(ref)
    if ref.startswith("#") and ref[1:].isdigit():
        return pathlib.Path(get_entry(int(ref[1:]))["output"])
    stored = SRC / pathlib.Path(ref).name
    if stored.is_file() and "/" not in ref:
        return stored
    kept = pathlib.Path(ref)
    if kept.is_file() and kept.parent in (SRC, OUT):
        return kept
    path = pathlib.Path(ref).expanduser()
    if not path.is_file():
        raise KitError("source_missing", f"The source image {ref} was not found.")
    return save_source(path.read_bytes(), path.name)


def image_size(path):
    """Width and height of an image, read from the file itself. Falls back to 1024 by 1024."""
    try:
        head = pathlib.Path(path).read_bytes()[:64 * 1024]
        if head.startswith(b"\x89PNG"):
            return struct.unpack(">II", head[16:24])
        if head.startswith(b"GIF8"):
            return struct.unpack("<HH", head[6:10])
        if head.startswith(b"\xff\xd8"):                  # JPEG: walk the segments to the frame header
            at = 2
            while at + 9 < len(head):
                marker, length = head[at + 1], struct.unpack(">H", head[at + 2:at + 4])[0]
                if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                    h, w = struct.unpack(">HH", head[at + 5:at + 9])
                    return w, h
                at += 2 + length
        from PIL import Image
        with Image.open(path) as im:
            return im.size
    except Exception:
        return 1024, 1024


def fit_size(w, h, long_edge=1024):
    """Scale to a long edge the models handle well, in the 16-pixel steps they need."""
    scale = long_edge / max(w, h)
    snap = lambda v: max(256, int(round(v * scale / 16)) * 16)
    return snap(w), snap(h)


# Prompts: styles, and turning a short idea into a fuller prompt.

GEN_SYSTEM = ("You write prompts for an image model. Rewrite the idea as ONE prompt in plain flowing "
              "sentences, never a comma list of keywords. Cover, in this order: the subject, the setting, "
              "the composition and camera, the light, the style and the mood. Keep every detail the "
              "person gave. Add no text in the image unless they asked for it. 40 to 70 words. "
              "Reply with the prompt only.")
EDIT_SYSTEM = ("You write instructions for an image-editing model that is given source images. Rewrite the "
               "request as ONE instruction with three parts: what to change, where in the image, and what "
               "must stay exactly the same (identity, pose, background, lighting, unless the request "
               "changes them). One change per instruction. Under 50 words. Reply with the instruction only.")


def compose_prompt(prompt, style=""):
    prompt = " ".join(prompt.split())
    extra = STYLES.get(style, "")
    return f"{prompt.rstrip('.')}. Rendered as {extra}." if extra else prompt


def improve_prompt(prompt, editing=False):
    """Turn a short idea into a fuller prompt. Uses a local language model when one is running, else a template."""
    prompt = " ".join(prompt.split())
    if not prompt:
        raise KitError("empty_prompt", "Write a few words first.")
    if not FAKE:
        try:
            with urllib.request.urlopen(Settings.ollama + "/api/tags", timeout=1.5) as r:
                names = [m["name"] for m in json.load(r).get("models", [])]
            names = [n for n in names if "embed" not in n and "minicpm" not in n]
            pick = next((n for want in ("gemma", "qwen", "llama", "mistral", "phi") for n in names if want in n),
                        names[0] if names else None)
            if pick:
                body = json.dumps({"model": pick, "stream": False, "think": False, "options": {"temperature": 0.4},
                                   "messages": [{"role": "system", "content": EDIT_SYSTEM if editing else GEN_SYSTEM},
                                                {"role": "user", "content": prompt}]}).encode()
                req = urllib.request.Request(Settings.ollama + "/api/chat", data=body,
                                             headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=90) as r:
                    text = json.load(r)["message"]["content"].strip().strip('"')
                if text:
                    return {"prompt": text, "by": f"the local model {pick}"}
        except (OSError, ValueError, KeyError):
            pass
    if editing:
        text = (f"{prompt.rstrip('.')}. Keep everything else exactly as it is in the source image: "
                "the subject's identity, the pose, the background and the lighting.")
    else:
        text = (f"{prompt.rstrip('.')}, as the clear main subject in the centre of the frame. "
                "Soft natural light from one side, a simple uncluttered background, sharp detail.")
    return {"prompt": text, "by": "the built-in template (no local language model is running)"}


# The engine: plan a render, build its command, run it, record it.

def plan(req):
    """Turn a request into every setting a render needs, filling the ones not given.

    A request names a prompt and, optionally, source images, a model, a style and
    numbers. The result is the full, reproducible record that goes into history.
    """
    prompt = " ".join(str(req.get("prompt", "")).split())
    if not prompt:
        raise KitError("empty_prompt", "Write what you want to see first.")
    key = req.get("model") or default_model()
    if key not in MODELS:
        raise KitError("unknown_model", f"There is no model called {key}.", "Models: " + ", ".join(MODELS))
    m = MODELS[key]
    asked = [str(s) for s in (req.get("sources") or [])][:4]
    parent = req.get("parent")
    if parent is None:                       # building on a past image continues that image's thread
        parent = next((int(s[1:]) for s in asked if s.startswith("#") and s[1:].isdigit()), None)
    sources = [str(resolve_source(s)) for s in asked]
    region = req.get("region")
    if region:
        if not sources or not m["edit"]:
            raise KitError("region_needs_source", "Marking an area works on one existing image.",
                           "Open an image, mark the area, and say what should change there.")
        try:
            x, y, w, h = (float(v) for v in region)
        except (TypeError, ValueError):
            raise KitError("bad_region", "The marked area could not be read.")
        if not (0 <= x < 1 and 0 <= y < 1 and w >= 0.02 and h >= 0.02 and x + w <= 1.001 and y + h <= 1.001):
            raise KitError("bad_region", "The marked area must sit inside the image.", "Mark it again.")
        region, sources = [round(v, 4) for v in (x, y, w, h)], sources[:1]
    use = req.get("use") or ("edit" if m["edit"] else "start")
    if not sources:
        mode = "new"
    elif use == "edit" and m["edit"]:
        mode = "edit"
    else:
        mode = "start"
        sources = sources[:1]
    if sources:
        default_w, default_h = fit_size(*image_size(sources[0]))
    else:
        default_w, default_h = 1024, 1024
    tight = machine()["tier"] != "full"
    seed = req.get("seed")
    # A rework instruction says what to change; a style sentence on the end reads as a second change.
    style = "" if mode == "edit" else (req.get("style") or "")
    return {
        "prompt": prompt, "style": style, "full_prompt": compose_prompt(prompt, style),
        "model": key, "mode": mode, "sources": sources,
        "strength": float(req.get("strength") or 0.5),
        "steps": int(req.get("steps") or m["steps"]),
        "guidance": req.get("guidance") if req.get("guidance") is not None else m["guidance"],
        "width": int(req.get("width") or default_w), "height": int(req.get("height") or default_h),
        "quant": int(req.get("quant") or (4 if tight else 8)),
        "seed": int(seed) if seed not in (None, "") else random.randrange(1, 2**31),
        "parent": parent, "kind": req.get("kind") or "new", "thread": req.get("thread") or "",
        "region": region or None,               # the marked area as left, top, width, height, each 0 to 1
        "low_ram": tight,
        "server": req.get("server") or "",        # the machine that draws it; empty means this one
    }


def command(p, out):
    """The exact mflux command line for a planned render."""
    m = MODELS[p["model"]]
    cmd = [str(BIN / (m["edit"] if p["mode"] == "edit" else m["gen"])), *m["args"],
           "--prompt", p["full_prompt"], "--steps", str(p["steps"]), "--seed", str(p["seed"]),
           "--width", str(p["width"]), "--height", str(p["height"]),
           "--quantize", str(p["quant"]), "--mlx-cache-limit-gb", "4", "--output", str(out)]
    if p["guidance"] is not None:
        cmd += ["--guidance", str(p["guidance"])]
    if p["mode"] == "edit":
        cmd += ["--image-paths", *p["sources"]]
    elif p["mode"] == "start":
        cmd += ["--image-path", p["sources"][0], "--image-strength", str(p["strength"])]
    if p["low_ram"]:
        cmd.append("--low-ram")
    return cmd


def fake_png(path, seed, w=256, h=256):
    """A flat-colour PNG, so tests and screen checks run without a model."""
    rnd = random.Random(seed)
    r, g, b = (rnd.randrange(40, 220) for _ in range(3))
    row = b"\x00" + bytes((r, g, b)) * w
    chunk = lambda tag, data: struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(row * h)) + chunk(b"IEND", b""))
    pathlib.Path(path).write_bytes(png)


def render(p, on_step=lambda step, total: None, should_stop=lambda: False):
    """Draw one image and record it. Returns the history entry.

    Refuses before loading anything when the model is not fully downloaded: a
    half-downloaded model does not fail, it quietly starts a download of many
    gigabytes that looks exactly like a very slow render.
    """
    status = model_status(p["model"])
    if not p.get("server") and not status["ready"] and status.get("cloud"):
        raise KitError("needs_key", f"{status['name']} needs a key from {status['who']}.",
                       f"Get one at {status['key_page']} and add it in the app, or set {CLOUD[status['cloud']]['env']}.")
    if not p.get("server") and not status["ready"]:
        raise KitError("model_missing", f"{status['name']} is not downloaded yet "
                       f"({status['have_gb']} of {status['disk_gb']} GB).",
                       f"Download it in the app, or run: ./imagine download {p['model']}")
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"img-{int(time.time())}-{p['seed']}.png"
    started = time.time()
    engine = ENGINES["remote" if p.get("server") else MODELS[p["model"]]["engine"]]
    ok, fix = engine.ready()
    if not ok:
        raise KitError("not_installed", f"{engine.name[0].upper()}{engine.name[1:]} is not installed.", fix)
    if p.get("region"):
        render_region(engine, p, out, on_step, should_stop)
    else:
        engine.run(p, out, on_step, should_stop)
    if should_stop():
        raise KitError("cancelled", "Stopped.")
    if not out.is_file():
        raise KitError("render_failed", "The model finished without making an image.")
    entry = {k: p[k] for k in ("prompt", "style", "full_prompt", "model", "mode", "sources", "strength", "steps",
                               "guidance", "width", "height", "quant", "seed", "parent", "kind", "server",
                               "thread", "region")}
    if p.get("cloud_model"):
        entry["cloud_model"] = p["cloud_model"]         # the exact model the company's service used
    entry.update(ts=time.strftime("%Y-%m-%dT%H:%M:%S"), output=str(out), secs=round(time.time() - started),
                 star=False)
    entry = add_entry(entry)
    details_path(out).write_text(json.dumps(entry, indent=2) + "\n")
    return entry


AREA_MARGIN = 0.25      # how much of the surroundings the model sees around a marked area, as a share of its size


def area_box(region, width, height):
    """The marked area in pixels, and the larger piece cut out around it: (box, cut), each left, top, right, bottom."""
    x, y, w, h = region
    box = (int(x * width), int(y * height), min(width, int((x + w) * width) + 1), min(height, int((y + h) * height) + 1))
    cut = (max(0, int((x - w * AREA_MARGIN) * width)), max(0, int((y - h * AREA_MARGIN) * height)),
           min(width, int((x + w * (1 + AREA_MARGIN)) * width) + 1),
           min(height, int((y + h * (1 + AREA_MARGIN)) * height) + 1))
    return box, cut


def render_region(engine, p, out, on_step, should_stop):
    """Change only a marked area of an image, and leave every pixel outside its cut-out exactly as it was.

    The piece around the marked area is cut out, the model reworks that piece
    alone, and the result is blended back with a soft edge. The rest of the
    image is never shown to the model, so it cannot drift.
    """
    try:
        from PIL import Image, ImageFilter
    except ImportError:
        raise KitError("needs_pillow", "Changing a marked area needs the kit's own environment.", "Run: ./install.sh")
    base = Image.open(p["sources"][0]).convert("RGB")
    box, cut = area_box(p["region"], *base.size)
    piece = base.crop(cut)
    piece_in, piece_out = OUT / f".piece-in-{p['seed']}.png", OUT / f".piece-out-{p['seed']}.png"
    piece.save(piece_in)
    width, height = fit_size(*piece.size)
    try:
        engine.run(dict(p, sources=[str(piece_in)], width=width, height=height, region=None), piece_out,
                   on_step, should_stop)
        if should_stop() or not piece_out.is_file():
            return
        changed = Image.open(piece_out).convert("RGB").resize(piece.size, Image.LANCZOS)
        mask = Image.new("L", piece.size, 0)
        mask.paste(255, (box[0] - cut[0], box[1] - cut[1], box[2] - cut[0], box[3] - cut[1]))
        soft = max(2, int(min(box[2] - box[0], box[3] - box[1]) * 0.06))
        base.paste(Image.composite(changed, piece, mask.filter(ImageFilter.GaussianBlur(soft))), cut[:2])
        base.save(out)
        p["width"], p["height"] = base.size
    finally:
        for leftover in (piece_in, piece_out):
            leftover.unlink(missing_ok=True)


def check_change(entry_id):
    """Measure what a rework changed against the image it started from. No model is involved.

    Returns the share of pixels that changed overall and, for a marked area,
    the share inside the area and outside its cut-out.
    """
    try:
        from PIL import Image, ImageChops
    except ImportError:
        raise KitError("needs_pillow", "Measuring a change needs the kit's own environment.", "Run: ./install.sh")
    e = get_entry(entry_id)
    if not e.get("sources"):
        raise KitError("nothing_to_compare", "This image was made from a prompt alone, so there is nothing to compare it with.")
    after = Image.open(e["output"]).convert("RGB")
    before = Image.open(e["sources"][0]).convert("RGB").resize(after.size, Image.LANCZOS)
    moved = ImageChops.difference(before, after).convert("L").point(lambda v: 255 if v > 12 else 0)
    share = lambda im: round(100 * im.histogram()[255] / max(1, im.size[0] * im.size[1]), 1)
    report = {"changed_pct": share(moved)}
    if e.get("region"):
        box, cut = area_box(e["region"], *after.size)
        outside = moved.copy()
        outside.paste(0, cut)
        outside_px = after.size[0] * after.size[1] - (cut[2] - cut[0]) * (cut[3] - cut[1])
        report.update(inside_changed_pct=share(moved.crop(box)),
                      outside_changed_pct=round(100 * outside.histogram()[255] / max(1, outside_px), 1))
        report["words"] = (f"{report['inside_changed_pct']}% of the marked area changed. "
                           + ("Nothing outside it changed." if report["outside_changed_pct"] == 0
                              else f"{report['outside_changed_pct']}% of the rest changed too."))
    else:
        report["words"] = f"{report['changed_pct']}% of the image changed from its first source."
    return report


def details_path(image):
    """The file beside an image that holds its full record, so the picture can travel with its recipe."""
    return pathlib.Path(image).with_suffix(".metadata.json")


def stop_process(proc):
    """Ask a running engine or download to stop, along with anything it started."""
    try:
        if hasattr(os, "killpg"):
            os.killpg(proc.pid, signal.SIGTERM)
        else:                                   # Windows has no process groups of this kind
            proc.terminate()
    except OSError:
        pass


# Engines: each one knows how to draw a planned image with one kind of model.
# An engine has a `name` for messages, `ready()` returning (True, "") or
# (False, how to fix it), and `run(p, out, on_step, should_stop)`, which writes
# the image to `out` or raises a KitError.

def run_engine_process(cmd, p, out, on_step, should_stop):
    """Run an engine's program for one image, passing its `step/total` lines on as progress.

    Every local engine draws in a separate program, so a crash or a stop takes
    that program down and leaves the kit running.
    """
    tail = []
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, start_new_session=True)
    buf = b""
    while True:
        chunk = proc.stderr.read1(4096)
        if not chunk:
            break
        if should_stop():
            stop_process(proc)
        buf += chunk
        *lines, buf = re.split(rb"[\r\n]", buf)
        for raw in lines:
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            tail = (tail + [line])[-20:]
            hit = re.search(r"(\d+)/(\d+)", line)
            if hit and int(hit.group(2)) == p["steps"]:
                on_step(int(hit.group(1)), int(hit.group(2)))
    code = proc.wait()
    if should_stop():
        raise KitError("cancelled", "Stopped.")
    if code != 0 or not pathlib.Path(out).is_file():
        killed = code in (-9, -15, 137, 143)
        raise KitError("render_failed",
                       "The model was stopped before it finished, most likely for memory."
                       if killed else "The model failed before it finished.",
                       "Close other large apps and try again, or pick a smaller size."
                       if killed else (tail[-1] if tail else ""))


class MfluxEngine:
    """Draws on an Apple Silicon Mac, with the models held on this machine."""

    name = "the image engine (mflux)"

    def ready(self):
        if machine()["chip"] != "apple":
            return False, "This engine runs only on a Mac with an M-series chip. Pick a model that runs elsewhere."
        if not (BIN / "mflux-generate-flux2").exists():
            return False, "Run: ./install.sh"
        return True, ""

    def run(self, p, out, on_step, should_stop):
        cmd = command(p, out)
        grant = memory_grant(pathlib.Path(cmd[0]).name, p["seed"], MODELS[p["model"]]["grant_gb"])
        try:
            run_engine_process(cmd, p, out, on_step, should_stop)
        finally:
            if grant:
                subprocess.run(["zrecover", "revoke", grant], capture_output=True)


def card_plan(gpu_gb, sources):
    """How to load the model on an NVIDIA card of this size: (bits, longest side of a source image).

    Returns None when the card is too small. The numbers come from runs on a
    16 GB card: at full precision a rework did not fit at any source size; in
    4-bit, one source fit at 768 and two fit at 512.
    """
    if gpu_gb >= 20:
        return 16, 1024
    if gpu_gb >= 12:
        return 4, (768 if sources <= 1 else 512)
    return None


class DiffusersEngine:
    """Draws on a Linux or Windows computer with an NVIDIA graphics card."""

    name = "the image engine (diffusers)"

    def ready(self):
        here = machine()
        if here["chip"] == "apple":
            return False, "On a Mac the kit uses its Mac engine instead."
        if card_plan(here["gpu_gb"], 0) is None:
            return False, ("This engine needs an NVIDIA graphics card with 12 GB of memory or more"
                           + (f"; this one has {here['gpu_gb']} GB." if here["gpu_gb"] else ", and none was found.")
                           + " Use a machine that can draw for this one: ./imagine servers")
        if not any((BIN.parent / "lib").glob("python*/site-packages/diffusers")):
            return False, "Run: ./install.sh"
        return True, ""

    def run(self, p, out, on_step, should_stop):
        bits, ref_side = card_plan(machine()["gpu_gb"], len(p["sources"]))
        job = {"repo": MODELS[p["model"]]["repo"], "prompt": p["full_prompt"], "steps": p["steps"], "seed": p["seed"],
               "width": p["width"], "height": p["height"], "guidance": p["guidance"], "sources": p["sources"],
               "bits": bits, "ref_side": ref_side, "out": str(out)}
        p["quant"] = bits
        run_engine_process([str(BIN / "python"), str(HOME / "engine_diffusers.py"), json.dumps(job)],
                           p, out, on_step, should_stop)


class FakeEngine:
    """Stands in for a real engine in the tests and screen checks: it draws a flat PNG and loads no model."""

    name = "the stand-in engine"

    def ready(self):
        if Settings.fake_no_engine:         # lets the screen check show a computer that cannot draw by itself
            return False, ("This engine needs an NVIDIA graphics card with 12 GB of memory or more; this one has 8 GB. "
                           "Use a machine that can draw for this one: ./imagine servers")
        return True, ""

    def run(self, p, out, on_step, should_stop):
        for step in range(1, p["steps"] + 1):
            if should_stop():
                raise KitError("cancelled", "Stopped.")
            time.sleep(Settings.fake_step_s)
            on_step(step, p["steps"])
        if Settings.fake_fail:
            raise KitError("render_failed", "The model failed before it finished.", "A test asked for this failure.")
        fake_png(out, p["seed"])


# Other machines: a render can be sent to a computer that offers its image models
# with `lm net serve`. The two files below are shared with lm net, so a machine
# set up there is already known here, and the kit can also set itself up alone.

def _read_json(path, default):
    try:
        return json.loads(pathlib.Path(path).read_text())
    except (OSError, ValueError):
        return default


def _write_private(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def net_identity():
    """This computer's name and private key, as other machines know it. Made on first use."""
    path = Settings.net / "identity.json"
    me = _read_json(path, None)
    if not me or not me.get("secret"):
        me = {"name": platform.node().split(".")[0] or "computer", "secret": os.urandom(24).hex()}
        _write_private(path, me)
    return me


def net_servers():
    """The machines this computer knows that can draw images for it."""
    return [s for s in _read_json(Settings.net / "servers.json", []) if "imagine" in s.get("services", [])]


def net_call(url, path, body=None, timeout=930):
    """Ask another machine for something as this computer. Raises a KitError in that machine's own words."""
    me = net_identity()
    req = urllib.request.Request(url.rstrip("/") + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "Bearer " + me["secret"], "X-LM-Device": me["name"],
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as err:
        try:
            got = json.load(err)
        except ValueError:
            got = {}
        raise KitError(got.get("code", "refused"), got.get("plain", "The other machine refused the request."))
    except (OSError, ValueError):
        raise KitError("unreachable", "The other machine did not answer.",
                       "It may be asleep, switched off, or not offering its models right now.")


def add_server(name, address):
    """Remember another machine, after it answers. Tells it this computer exists, which is how approval is asked for."""
    url = address if "://" in address else "http://" + address
    if url.count(":") < 2:
        url += ":5119"
    hello = net_call(url, "/v1/hello", timeout=8)
    path = Settings.net / "servers.json"
    rows = [s for s in _read_json(path, []) if s["name"].lower() != name.lower()]
    rows.append({"name": name, "url": url, "host": hello.get("host", ""), "services": hello.get("services", []),
                 "added": time.strftime("%Y-%m-%dT%H:%M:%S")})
    _write_private(path, rows)
    return hello


class RemoteEngine:
    """Draws on another machine: sends the request and the source images, and saves the picture that comes back."""

    name = "the other machine"

    def ready(self):
        return True, ""

    def run(self, p, out, on_step, should_stop):
        server = next((s for s in net_servers() if s["name"] == p["server"]), None)
        if server is None:
            raise KitError("no_such_server", f"This computer does not know a machine called {p['server']}.",
                           "Add it with: ./imagine server add NAME ADDRESS")
        pack = lambda path: {"name": pathlib.Path(path).name,
                             "image": base64.b64encode(pathlib.Path(path).read_bytes()).decode()}
        request = {k: p[k] for k in ("prompt", "style", "model", "strength", "steps", "seed", "width", "height")}
        request["use"] = "start" if p["mode"] == "start" else "edit"
        got = net_call(server["url"], "/v1/imagine/render", {"request": request, "sources": [pack(s) for s in p["sources"]]})
        pathlib.Path(out).write_bytes(base64.b64decode(got["image"]))
        p.update({k: v for k, v in (got.get("record") or {}).items() if k in ("steps", "guidance", "quant")})


def cloud_call(provider, url, body=None, headers=None, timeout=300):
    """One request to a company's service. Raises a KitError carrying that company's own explanation."""
    who = CLOUD[provider]["who"]
    req = urllib.request.Request(url, data=body, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as err:
        try:
            said = (json.load(err).get("error") or {}).get("message", "")
        except (ValueError, AttributeError):
            said = ""
        if err.code in (401, 403):
            raise KitError("bad_key", f"{who} did not accept the key.", said or "Check the key, or make a new one.")
        raise KitError("cloud_failed", f"{who} could not make this image.", said or f"It answered with error {err.code}.")
    except (OSError, ValueError):
        raise KitError("unreachable", f"{who} could not be reached.", "Check the internet connection and try again.")


_picked = {}


def cloud_model(provider, listed):
    """The image model to ask for: the one named in the environment, else the newest the service lists."""
    named = Settings.env.get(CLOUD[provider]["pick"], "").strip()
    if named:
        return named
    if provider not in _picked:
        names = sorted(n for n in listed() if "image" in n and "embed" not in n)
        if not names:
            raise KitError("cloud_failed", f"{CLOUD[provider]['who']} lists no image model for this key.")
        # Prefer a settled model over a preview, then the highest name, which is the newest version.
        _picked[provider] = sorted(names, key=lambda n: ("preview" not in n, n))[-1]
    return _picked[provider]


def image_part(path):
    kind = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(pathlib.Path(path).suffix.lower(),
                                                                                    "image/png")
    return kind, pathlib.Path(path).read_bytes()


def save_picture(data, out):
    """Write the picture a service sent back as a PNG, whatever format it arrived in."""
    if data.startswith(b"\x89PNG"):
        pathlib.Path(out).write_bytes(data)
        return
    tmp = pathlib.Path(out).with_suffix(".tmp")
    tmp.write_bytes(data)
    to_png(tmp, out)
    tmp.unlink(missing_ok=True)


class GeminiEngine:
    """Draws with Google's image model. The prompt and any source images are sent to Google."""

    name = "Google's image model"
    base = "https://generativelanguage.googleapis.com/v1beta"

    def ready(self):
        return True, ""

    def request(self, p):
        parts = [{"text": p["full_prompt"]}]
        for src in p["sources"]:
            kind, data = image_part(src)
            parts.append({"inline_data": {"mime_type": kind, "data": base64.b64encode(data).decode()}})
        return {"contents": [{"parts": parts}], "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}}

    def run(self, p, out, on_step, should_stop):
        key = api_key("gemini")
        head = {"x-goog-api-key": key, "Content-Type": "application/json"}
        model = cloud_model("gemini", lambda: [m["name"].split("/")[-1] for m in cloud_call(
            "gemini", f"{self.base}/models?pageSize=200", headers=head).get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])])
        got = cloud_call("gemini", f"{self.base}/models/{model}:generateContent",
                         json.dumps(self.request(p)).encode(), head)
        for part in (got.get("candidates") or [{}])[0].get("content", {}).get("parts", []):
            blob = part.get("inlineData") or part.get("inline_data")
            if blob and blob.get("data"):
                save_picture(base64.b64decode(blob["data"]), out)
                p["width"], p["height"] = image_size(out)
                p["cloud_model"] = model
                return
        raise KitError("cloud_failed", "Google answered without a picture.",
                       "It may have declined the request. Try different words.")


class OpenAIEngine:
    """Draws with OpenAI's image model. The prompt and any source images are sent to OpenAI."""

    name = "OpenAI's image model"
    base = "https://api.openai.com/v1"

    def ready(self):
        return True, ""

    def size(self, p):
        if p["width"] > p["height"] * 1.15:
            return "1536x1024"
        return "1024x1536" if p["height"] > p["width"] * 1.15 else "1024x1024"

    def form(self, fields, files):
        """A multipart form body: text fields, then each source image as an `image[]` part."""
        edge = "kit" + os.urandom(12).hex()
        body = b""
        for name, value in fields.items():
            body += f'--{edge}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        for path in files:
            kind, data = image_part(path)
            body += (f'--{edge}\r\nContent-Disposition: form-data; name="image[]"; '
                     f'filename="{pathlib.Path(path).name}"\r\nContent-Type: {kind}\r\n\r\n').encode() + data + b"\r\n"
        return body + f"--{edge}--\r\n".encode(), f"multipart/form-data; boundary={edge}"

    def run(self, p, out, on_step, should_stop):
        auth = {"Authorization": "Bearer " + api_key("openai")}
        model = cloud_model("openai", lambda: [m["id"] for m in cloud_call(
            "openai", f"{self.base}/models", headers=auth).get("data", []) if m["id"].startswith("gpt-image")])
        fields = {"model": model, "prompt": p["full_prompt"], "size": self.size(p)}
        if p["sources"]:
            body, kind = self.form(fields, p["sources"])
            got = cloud_call("openai", f"{self.base}/images/edits", body, dict(auth, **{"Content-Type": kind}))
        else:
            got = cloud_call("openai", f"{self.base}/images/generations", json.dumps(fields).encode(),
                             dict(auth, **{"Content-Type": "application/json"}))
        blob = (got.get("data") or [{}])[0].get("b64_json")
        if not blob:
            raise KitError("cloud_failed", "OpenAI answered without a picture.")
        save_picture(base64.b64decode(blob), out)
        p["width"], p["height"] = image_size(out)
        p["cloud_model"] = model


ENGINES = {"mflux": MfluxEngine(), "diffusers": DiffusersEngine(), "fake": FakeEngine(), "remote": RemoteEngine(),
           "gemini": GeminiEngine(), "openai": OpenAIEngine()}
if platform.system() != "Darwin":
    MODELS["klein"]["engine"] = "diffusers"         # off a Mac, the one model the second engine can draw with
if FAKE:
    for _model in MODELS.values():
        _model["engine"] = "fake"


def memory_grant(program, seed, gb):
    """On a Mac that runs the zrecover memory guard, ask it for room for this one render."""
    if not shutil.which("zrecover"):
        return ""
    try:
        r = subprocess.run(["zrecover", "allow", "--match", f"{program} .*--seed {seed}( |$)", "--gb", str(gb),
                            "--for", "45m", "--note", "imagine-kit render", "--json"],
                           capture_output=True, text=True, timeout=10)
        return str(json.loads(r.stdout).get("id", ""))
    except (OSError, ValueError, subprocess.SubprocessError):
        return ""


def download(key, on_step=lambda step, total: None, should_stop=lambda: False):
    """Fetch a model's files. Safe to stop and run again: it resumes."""
    m = MODELS[key]
    if FAKE:
        for step in range(1, 6):
            if should_stop():
                raise KitError("cancelled", "Stopped. Run it again to resume.")
            time.sleep(Settings.fake_step_s)
            on_step(step * m["disk_gb"] // 5, m["disk_gb"])
        return
    hf = BIN / "hf"
    if not hf.exists():
        raise KitError("not_installed", "The downloader is not installed.", "Run: ./install.sh")
    cmd = [str(hf), "download", m["repo"]]
    for pattern in m["include"]:        # one flag per pattern, or the extras are read as file names
        cmd += ["--include", pattern]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, start_new_session=True)
    cache = hf_cache(m["repo"])
    while proc.poll() is None:
        if should_stop():
            stop_process(proc)
            proc.wait()
            raise KitError("cancelled", "Stopped. Run it again to resume.")
        on_step(round(dir_gb(cache), 1) if cache.is_dir() else 0, m["disk_gb"])
        time.sleep(2)
    if proc.returncode != 0:
        err = proc.stderr.read().decode("utf-8", "replace").strip().splitlines()
        raise KitError("download_failed", f"The download of {m['name']} stopped.",
                       (err[-1] if err else "") + " Run it again to resume.")


def follow_up(kind, entry_id, change=""):
    """Build the request for a second try at a past image.

    again   the same request with a new roll of the dice
    refine  the same starting point, with the prompt changed
    rework  the past image itself becomes the source, and `change` says what to do to it
    """
    e = get_entry(entry_id)
    base = {k: e.get(k) for k in ("prompt", "style", "model", "sources", "strength", "steps", "guidance",
                                  "width", "height", "quant", "server")}
    base.update(parent=entry_id, kind=kind, use="edit" if e["mode"] == "edit" else "start")
    if kind == "again":
        return base
    if not change.strip():
        raise KitError("empty_prompt", "Say what to change.")
    if kind == "refine":
        base.update(seed=e["seed"], prompt=f"{e['prompt'].rstrip('.')}. {change.strip()}")
        return base
    if kind == "rework":
        model = e["model"] if MODELS[e["model"]]["edit"] else "klein"
        base.update(model=model, sources=[f"#{entry_id}"], use="edit", prompt=change.strip(), style="",
                    steps=None, guidance=None, width=None, height=None)
        return base
    raise KitError("bad_request", f"Unknown follow-up: {kind}")


# The app server: one page, a few JSON calls, one job at a time.

class Queue:
    """The line of work waiting to be done. The kit draws one image at a time, and the rest wait their turn.

    A job is a dict the page reads: `state` is queued, running, done, failed or
    stopped. `add` returns straight away; one background thread works down the line.
    """

    LIMIT = 12          # more than this waiting is almost always a slip, and each one holds a model for a while

    def __init__(self):
        self.lock = threading.Lock()
        self.jobs = []
        self.work = {}              # job id -> (the work to do, its stop signal)
        self.count = 0
        self.runner = None

    def add(self, kind, label, work, where="", thread=""):
        """Put work in the line. `thread` is the thread its image will join, when that is already known."""
        with self.lock:
            if sum(j["state"] in ("queued", "running") for j in self.jobs) >= self.LIMIT:
                raise KitError("queue_full", f"{self.LIMIT} things are already waiting.",
                               "Let some finish, or stop a few, then ask again.")
            self.count += 1
            job = {"id": self.count, "kind": kind, "label": label, "state": "queued", "step": 0, "total": 0,
                   "added": time.time(), "started": None, "entry": None, "error": None, "where": where,
                   "thread": thread}
            self.jobs.append(job)
            self.work[job["id"]] = (work, threading.Event())
            if self.runner is None or not self.runner.is_alive():
                self.runner = threading.Thread(target=self._run, daemon=True)
                self.runner.start()
        return job

    def _run(self):
        while True:
            with self.lock:
                job = next((j for j in self.jobs if j["state"] == "queued"), None)
                if job is None:
                    return
                job["state"], job["started"] = "running", time.time()
                work, stop = self.work[job["id"]]

            def on_step(step, total, job=job):
                job["step"], job["total"] = step, total

            try:
                result = work(on_step, stop.is_set)
                job["entry"] = result.get("id") if isinstance(result, dict) else None
                job["state"] = "done"
            except KitError as err:
                job["state"] = "stopped" if err.code == "cancelled" else "failed"
                job["error"] = err.as_dict()
            except Exception as err:                      # a bug must reach the screen, not vanish in a thread
                job["state"], job["error"] = "failed", KitError("internal", f"{type(err).__name__}: {err}").as_dict()
            job["ended"] = time.time()
            self.work.pop(job["id"], None)

    def stop(self, job_id=None):
        """Stop one job, or the running one when no id is given. A waiting job simply leaves the line."""
        with self.lock:
            for job in self.jobs:
                if job["state"] == "queued" and job["id"] == job_id:
                    job["state"], job["ended"] = "stopped", time.time()
                    job["error"] = KitError("cancelled", "Taken out of the line.").as_dict()
                    self.work.pop(job["id"], None)
                elif job["state"] == "running" and job_id in (None, job["id"]):
                    self.work[job["id"]][1].set()

    def stop_thread(self, thread):
        """Stop everything still headed for one thread, so a deleted thread is not brought back by a late image."""
        with self.lock:
            ids = [j["id"] for j in self.jobs if j["state"] in ("queued", "running") and j.get("thread") == thread]
        for job_id in ids:
            self.stop(job_id)

    def view(self):
        """What the page shows: everything waiting or running, and the last few that ended."""
        with self.lock:
            live = [j for j in self.jobs if j["state"] in ("queued", "running")]
            ended = [j for j in self.jobs if j["state"] not in ("queued", "running")][-6:]
            self.jobs = ended + live
            now = time.time()
            return [dict(j, elapsed=round((j.get("ended") or now) - j["started"]) if j["started"] else 0)
                    for j in self.jobs]


QUEUE = Queue()


def app_state():
    jobs = QUEUE.view()
    # `job` is the newest piece of work, kept for anything that only follows one at a time.
    job = dict(jobs[-1], state="running" if jobs[-1]["state"] == "queued" else jobs[-1]["state"]) if jobs else None
    history = read_history()
    for row in history:
        row["url"] = "/img/" + pathlib.Path(row["output"]).name
        row["source_urls"] = [("/img/" if pathlib.Path(s).parent == OUT else "/src/") + pathlib.Path(s).name
                              for s in row.get("sources", [])]
    return {"ok": True, "version": VERSION, "models": [model_status(k) for k in MODELS],
            "default_model": default_model(), "styles": list(STYLES), "ram_gb": ram_gb(),
            "installed": any(ENGINES[m["engine"]].ready()[0] for m in MODELS.values() if not m.get("cloud")),
            "machine": machine(),
            "servers": [{"name": s["name"], "host": s.get("host", "")} for s in net_servers()],
            "history": history[::-1], "job": job, "jobs": jobs, "thread_names": thread_names(),
            "library": [{"ref": f.name, "url": "/src/" + f.name} for f in sorted(
                (f for f in SRC.glob("*") if f.suffix.lower() in (".png", ".jpg")),
                key=lambda f: f.stat().st_mtime, reverse=True)[:40]] if SRC.is_dir() else []}


class Handler(BaseHTTPRequestHandler):
    server_version = "ImagineKit/" + VERSION

    def log_message(self, *args):
        pass

    def send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "max-age=3600" if ctype.startswith("image/") else "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_file(self, folder, name):
        path = folder / pathlib.Path(name).name      # the last part only, so a request cannot leave the folder
        if not path.is_file():
            return self.send(404, {"ok": False, "code": "not_found", "message": "No such file."})
        ctype = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
        self.send(200, path.read_bytes(), ctype.get(path.suffix.lower(), "application/octet-stream"))

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            return self.send(200, (HOME / "app.html").read_bytes(), "text/html; charset=utf-8")
        if path == "/api/state":
            return self.send(200, app_state())
        if FAKE and path == "/__frame":      # the screen check's fixed-width frame; never served in real use
            return self.send(200, (HOME / "tests" / "frame.html").read_bytes(), "text/html; charset=utf-8")
        if path.startswith("/img/"):
            return self.send_file(OUT, path[5:])
        if path.startswith("/src/"):
            return self.send_file(SRC, path[5:])
        self.send(404, {"ok": False, "code": "not_found", "message": "No such page."})

    def do_POST(self):
        # Only this Mac's own browser page may ask for work.
        host = self.headers.get("Host", "").split(":")[0]
        if host not in ("127.0.0.1", "localhost"):
            return self.send(403, {"ok": False, "code": "forbidden", "message": "Local requests only."})
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        path = self.path.split("?")[0]
        try:
            if path == "/api/upload":
                saved = save_source(raw, urllib.request.unquote(self.headers.get("X-Filename", "image")))
                return self.send(200, {"ok": True, "source": saved.name, "url": "/src/" + saved.name})
            body = json.loads(raw or b"{}")
            if path == "/api/generate":
                asked = body
                if body.get("follow"):
                    body = follow_up(body["follow"], int(body["id"]), body.get("change", ""))
                    if asked.get("server") is not None:     # the page says where to draw; the past image's machine is only the default
                        body["server"] = asked["server"]
                    if asked.get("region"):
                        body["region"] = asked["region"]
                # Several tries of one request share a thread and differ only in their seed.
                tries = max(1, min(4, int(asked.get("count") or 1)))
                thread = body.get("thread") or (f"t{time.time_ns()}" if tries > 1 and not body.get("parent")
                                                and not any(str(s).startswith("#") for s in body.get("sources") or [])
                                                else "")
                plans = []
                for n in range(tries):
                    p = plan(dict(body, thread=thread, seed=body.get("seed") if n == 0 else None))
                    plans.append(p)
                # A follow-up has no thread of its own yet; it will join its parent's.
                threads = {r["id"]: r.get("thread", "") for r in read_history()}
                jobs = [QUEUE.add("render", p["prompt"], lambda step, stop, p=p: render(p, step, stop), p["server"],
                                  p["thread"] or threads.get(p["parent"], ""))
                        for p in plans]
                return self.send(200, {"ok": True, "plan": plans[0], "jobs": [j["id"] for j in jobs]})
            if path == "/api/download":
                key = body.get("model")
                if key not in MODELS:
                    raise KitError("unknown_model", "There is no such model.")
                QUEUE.add("download", MODELS[key]["name"], lambda step, stop: download(key, step, stop))
                return self.send(200, {"ok": True})
            if path == "/api/stop":
                QUEUE.stop(body.get("job"))
                return self.send(200, {"ok": True})
            if path == "/api/key":
                save_key(body.get("provider"), body.get("key", ""))
                return self.send(200, {"ok": True})
            if path == "/api/thread":
                name_thread(body["id"], body.get("title", ""))
                return self.send(200, {"ok": True})
            if path == "/api/thread/delete":
                # A whole thread goes the way single images go: each image and its details file to the trash folder.
                # Its requests still in the line stop first, or the image they make would bring the thread back.
                QUEUE.stop_thread(body["id"])
                ids = [r["id"] for r in read_history() if r.get("thread") == body["id"]]
                for entry_id in ids:
                    remove_entry(entry_id)
                return self.send(200, {"ok": True, "removed": len(ids)})
            if path == "/api/check":
                return self.send(200, dict(check_change(int(body["id"])), ok=True))
            if path == "/api/improve":
                return self.send(200, dict(improve_prompt(body.get("prompt", ""), bool(body.get("editing"))), ok=True))
            if path == "/api/star":
                e = get_entry(int(body["id"]))
                return self.send(200, {"ok": True, "star": update_entry(e["id"], star=not e.get("star"))["star"]})
            if path == "/api/delete":
                remove_entry(int(body["id"]))
                return self.send(200, {"ok": True})
            raise KitError("not_found", "No such action.")
        except KitError as err:
            self.send(409 if err.code == "busy" else 400, err.as_dict())
        except (ValueError, KeyError, TypeError) as err:
            self.send(400, KitError("bad_request", f"The request could not be read: {err}").as_dict())


def serve(port, open_browser=True):
    for candidate in range(port, port + 20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", candidate), Handler)
            break
        except OSError:
            continue
    else:
        raise KitError("port_busy", f"Ports {port} to {port + 19} are all in use.", "Pass another: ./imagine app --port 7900")
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Imagine Kit is running at {url}\nLeave this window open. Press Ctrl-C to stop.", flush=True)
    if open_browser:
        threading.Timer(0.4, webbrowser.open, [url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


# The command line.

HELP = """imagine: make and rework images on this Mac, from a prompt and optional source images

USAGE
  ./imagine [command] [options]

EXAMPLES
  ./imagine                                    open the app in your browser
  ./imagine gen "a red bicycle in the rain"    one image from a prompt
  ./imagine gen "make the jacket red" --from photo.jpg
                                               rework a source image
  ./imagine gen "put the cup on the desk" --from cup.png --from desk.png
                                               combine up to four source images
  ./imagine rework 12 "warmer light"           change image 12 itself
  ./imagine again 12                           the same request, a new roll
  ./imagine history                            past images, numbered

COMMANDS
  app [--port N] [--no-open]     the app (the default)
  gen "prompt" [options]         one image; prints the file it wrote
  again N                        image N's request with a new roll of the dice
  refine N "change"              image N's starting point, with the prompt changed
  rework N "change"              image N itself as the source, changed as you say
  check N                        measure what image N changed from its source
  improve "idea" [--edit]        turn a short idea into a fuller prompt
  history [N]                    the last N images (default 15)
  models                         each model, its size, and whether it is ready
  download MODEL                 fetch a model; safe to stop and run again
  doctor                         check that everything needed is in place
  servers | server add NAME ADDRESS   other machines that can draw for this one

OPTIONS FOR gen
  --from IMAGE          a source image; repeat for up to four
  --loose [0.1-0.9]     start loosely from the first source, not a strict edit
  --model NAME          klein (default), qwen, gemini or gpt
  --style NAME          photo, cinematic, illustration, watercolor, anime, 3d, product
  --size WxH  --steps N  --seed N   output size (default follows the source), steps, a seed to repeat a result
  --area X,Y,W,H        with one source or rework: keep the change inside this part (shares, 0 to 1)
  --on NAME  --json     draw on another machine; print the record, or an error, as JSON

More: README.md for the guide, PROMPTING.md for how to write prompts that work."""


def area_arg(text):
    """Read `--area X,Y,W,H`: the left, top, width and height of the part to change, as shares of the image."""
    try:
        box = [float(v) for v in text.split(",")]
    except ValueError:
        box = []
    if len(box) != 4:
        raise KitError("bad_usage", "--area wants four numbers from 0 to 1: left,top,width,height. "
                       "For the middle of the image: --area 0.25,0.25,0.5,0.5")
    return box


def print_entry(e, as_json=False):
    if as_json:
        print(json.dumps(e))
    else:
        print(f"#{e['id']}  {e['output']}\n    {e['model']} · {e['steps']} steps · seed {e['seed']} · "
              f"{e['width']}x{e['height']} · {e['secs']} s")


def cli(argv):
    if not argv or argv[0] in ("app",):
        ap = argparse.ArgumentParser(prog="imagine app", add_help=False)
        ap.add_argument("--port", type=int, default=7717)
        ap.add_argument("--no-open", action="store_true")
        a = ap.parse_args(argv[1:])
        return serve(a.port, not a.no_open)
    cmd, rest = argv[0], argv[1:]
    if cmd in ("-h", "--help", "help"):
        return print(HELP)
    if cmd in ("-V", "--version"):
        return print(f"imagine {VERSION}")

    def show_step(step, total):
        if sys.stderr.isatty():
            print(f"\r  step {step} of {total}", end="", file=sys.stderr, flush=True)

    def run(req, as_json=False):
        p = plan(req)
        if not as_json:
            print(f"  {MODELS[p['model']]['name']} · {p['mode']} · {p['steps']} steps · seed {p['seed']}", file=sys.stderr)
        e = render(p, show_step)
        if sys.stderr.isatty():
            print(file=sys.stderr)
        print_entry(e, as_json)

    if cmd == "gen":
        ap = argparse.ArgumentParser(prog="imagine gen", add_help=False)
        ap.add_argument("prompt", nargs="+")
        ap.add_argument("--from", dest="sources", action="append", default=[])
        ap.add_argument("--loose", nargs="?", const=0.5, type=float)
        ap.add_argument("--model")
        ap.add_argument("--style", choices=list(STYLES))
        ap.add_argument("--size")
        ap.add_argument("--steps", type=int)
        ap.add_argument("--seed", type=int)
        ap.add_argument("--json", action="store_true")
        ap.add_argument("--on", dest="server")
        ap.add_argument("--area")
        a = ap.parse_args(rest)
        req = {"prompt": " ".join(a.prompt), "sources": a.sources, "model": a.model, "style": a.style,
               "steps": a.steps, "seed": a.seed, "server": a.server}
        if a.area:
            req["region"] = area_arg(a.area)
        if a.loose is not None:
            req.update(use="start", strength=a.loose)
        if a.size:
            hit = re.fullmatch(r"(\d+)[xX](\d+)", a.size)
            if not hit:
                raise KitError("bad_usage", f"--size wants WIDTHxHEIGHT, for example 1024x768, not {a.size}.")
            req.update(width=int(hit.group(1)), height=int(hit.group(2)))
        return run(req, a.json)
    if cmd in ("again", "refine", "rework"):
        if not rest or not rest[0].lstrip("#").isdigit():
            raise KitError("bad_usage", f"Usage: ./imagine {cmd} N" + ('' if cmd == 'again' else ' "change"'))
        as_json, words, area, where = "--json" in rest, [], None, None
        args = iter(rest[1:])
        for arg in args:
            if arg == "--area":
                area = area_arg(next(args, ""))
            elif arg == "--on":
                where = next(args, "")
            elif arg != "--json":
                words.append(arg)
        req = follow_up(cmd, int(rest[0].lstrip("#")), " ".join(words))
        if area:
            req["region"] = area
        if where:
            req["server"] = where
        return run(req, as_json)
    if cmd == "check":
        if not rest or not rest[0].lstrip("#").isdigit():
            raise KitError("bad_usage", "Usage: ./imagine check N")
        report = check_change(int(rest[0].lstrip("#")))
        return print(json.dumps(report) if "--json" in rest else report["words"])
    if cmd == "improve":
        editing = "--edit" in rest
        got = improve_prompt(" ".join(r for r in rest if r != "--edit"), editing)
        print(got["prompt"])
        return print(f"  (written by {got['by']})", file=sys.stderr)
    if cmd == "history":
        rows = read_history()[-(int(rest[0]) if rest and rest[0].isdigit() else 15):]
        if not rows:
            return print('No images yet. Make one: ./imagine gen "a red bicycle in the rain"')
        for e in rows:
            star = "*" if e.get("star") else " "
            print(f"{star} #{e['id']:<4} {e['ts'][5:16].replace('T', ' ')}  {e['mode']:<5} {e['model']:<6} {e['prompt'][:60]}")
        return None
    if cmd == "models":
        if "--json" in rest:
            return print(json.dumps([model_status(k) for k in MODELS]))
        for s in (model_status(k) for k in MODELS):
            state = ("ready" if s["ready"] else f"needs a key from {s['who']}: {s['key_page']}") if s.get("cloud") \
                else "ready" if s["ready"] else f"not downloaded ({s['have_gb']} of {s['disk_gb']} GB)"
            fit = "" if s["ram_ok"] else f"  needs {s['min_ram_gb']} GB of memory; this Mac has {ram_gb()}"
            print(f"{s['id']:<7} {s['name']:<18} {state}{fit}\n        {s['blurb']}")
        return None
    if cmd == "download":
        local = [k for k in MODELS if not MODELS[k].get("cloud")]
        if not rest or rest[0] not in local:
            raise KitError("bad_usage", "Usage: ./imagine download MODEL", "Models to download: " + ", ".join(local))
        m = MODELS[rest[0]]
        print(f"Downloading {m['name']} (about {m['disk_gb']} GB). Safe to stop with Ctrl-C and run again.")
        download(rest[0], lambda have, total: print(f"\r  {have} of {total} GB", end="", flush=True))
        return print("\nDone.")
    if cmd == "doctor":
        if "--json" in rest:        # for a program: what this computer is, and which models it can use now
            models = [model_status(k) for k in MODELS]
            return print(json.dumps({"machine": machine(), "models": models, "default_model": default_model(),
                                     "can_draw": any(s["ready"] and s["ram_ok"] and s.get("engine_ok", True)
                                                     for s in models),
                                     "servers": [s["name"] for s in net_servers()]}))
        return doctor()
    if cmd == "servers":
        known = net_servers()
        if not known:
            return print("No other machines yet. Add one: ./imagine server add NAME ADDRESS")
        for s in known:
            print(f"  {s['name']:<16} {s['url']}  ({s.get('host') or 'unnamed'})")
        return None
    if cmd == "server":
        if len(rest) != 3 or rest[0] != "add":
            raise KitError("bad_usage", "Usage: ./imagine server add NAME ADDRESS")
        hello = add_server(rest[1], rest[2])
        print(f"{rest[1]} is remembered ({hello.get('host')}).")
        if "imagine" not in hello.get("services", []):
            print("It does not offer image models, so it will not appear as a place to draw.")
        if (hello.get("device") or {}).get("state") != "approved":
            print(f"This computer is waiting for approval there. Its owner runs: lm net approve {net_identity()['name']}")
        return None
    raise KitError("bad_usage", f"There is no command called {cmd}.", "Run: ./imagine help")


def doctor():
    """Check each thing a render needs and say how to fix what is missing. Exits 1 on any problem."""
    problems = 0

    def line(ok, what, fix=""):
        nonlocal problems
        problems += 0 if ok else 1
        print(f"  {'ok  ' if ok else 'FIX '} {what}" + (f"\n        {fix}" if fix and not ok else ""))

    here = machine()
    print(f"       this computer: {here['os']}, {here['chip']} chip, {here['ram_gb']} GB of memory")
    line(here["tier"] != "none", "enough memory for a local model (16 GB or more)", here["why"])
    # The default model's engine is the one that must work; another model's engine is reported, not required.
    ok, fix = ENGINES[MODELS["klein"]["engine"]].ready()
    line(ok, f"{ENGINES[MODELS['klein']['engine']].name} can run here", fix)
    free = shutil.disk_usage(pathlib.Path.home()).free / 2**30
    any_ready = False
    for key in MODELS:
        s = model_status(key)
        if s.get("cloud"):
            print(f"  {'ok  ' if s['ready'] else '    '} model {key}: runs at {s['who']}, "
                  + ("key found" if s["ready"] else "no key yet (optional)"))
            continue
        any_ready = any_ready or (s["ready"] and s["ram_ok"])
        note = "ready" if s["ready"] else f"not downloaded ({s['have_gb']} of {s['disk_gb']} GB)"
        print(f"  {'ok  ' if s['ready'] else '    '} model {key}: {note}" + ("" if s["ram_ok"] else ", too large for this computer"))
    line(any_ready, "at least one model is ready", f"Run: ./imagine download klein  (16 GB; {free:.0f} GB free on this disk)")
    print("All set. Run: ./imagine" if not problems else f"{problems} thing(s) to fix.")
    sys.exit(1 if problems else 0)


def main():
    try:
        cli(sys.argv[1:])
    except KitError as err:
        if "--json" in sys.argv:        # a program asked for JSON, so the refusal is JSON too, with its stable code
            print(json.dumps(err.as_dict()))
        print(f"imagine: {err.message}" + (f"\n  {err.fix}" if err.fix else ""), file=sys.stderr)
        sys.exit(2 if err.code == "bad_usage" else 1)
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
