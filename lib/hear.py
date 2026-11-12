#!/usr/bin/env python3
"""Turn speech into text on this Mac: a voice note, a recording, or a whole call.

`lm hear FILE` gives the words. `lm hear FILE --speakers` gives who said what and when.
`lm hear call FILE` adds a digest of what the call meant. `lm hear intent FILE` says
what a spoken note is asking for (a command for an agent, a note, an app action)
without acting on it. `lm hear check FILE` runs a second, unrelated transcriber and
reports where the two disagree, which is the cheap way to know how far to trust
a transcript nobody has listened to. Every run lands in outputs/hear/ and
logs/hear-history.jsonl. Design and measurements: docs/11-speech-lane.md.
"""
import argparse
import atexit
import calendar
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

# The model loaders print a download progress bar on every run, cached or not.
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "logs" / "hear-history.jsonl"
OUT = ROOT / "outputs" / "hear"
# The test suite sets this so its runs land in a throwaway folder, not in the owner's history.
if os.environ.get("LM_HEAR_SANDBOX"):
    LOG = Path(os.environ["LM_HEAR_SANDBOX"]) / "hear-history.jsonl"
    OUT = Path(os.environ["LM_HEAR_SANDBOX"]) / "outputs"

# One model per job. `words` is the most exact on plain speech and the fastest,
# `speakers` is the only one that says who is talking, `stamps` gives per-sentence
# times and is the independent second opinion for `check`.
MODELS = {
    "words": "mlx-community/Qwen3-ASR-0.6B-bf16",
    "speakers": "mlx-community/VibeVoice-ASR-4bit",
    "stamps": "mlx-community/parakeet-tdt-0.6b-v3",
}
# The speakers model's memory grows with the length of the audio: a 41-minute call in
# one pass went past 29 GB. Read in windows instead (10 minutes measured 11.4 GB and
# 145 s), overlapping so speakers can be matched from one window to the next.
WINDOW_S = 600
OVERLAP_S = 60
RATE = 16000


class HearError(Exception):
    """A failure the caller can act on: a stable code, a sentence, and the fix."""

    def __init__(self, code, message, remedy=""):
        super().__init__(message)
        self.code, self.message, self.remedy = code, message, remedy


def to_wav(src: Path, tmp: Path) -> Path:
    """Get 16 kHz mono audio out of any file macOS can read (mp4, mov, m4a, mp3, wav)."""
    if not src.is_file():
        raise HearError("no_such_file", f"no such file: {src}")
    dst = tmp / "audio.wav"
    r = subprocess.run(["afconvert", "-f", "WAVE", "-d", f"LEI16@{RATE}", "-c", "1", str(src), str(dst)],
                       capture_output=True, text=True)
    if r.returncode != 0 or not dst.is_file():
        raise HearError("audio_unreadable", f"macOS could not read audio from {src.name}",
                        "mkv and webm need converting first: brew install ffmpeg, then ffmpeg -i IN -vn out.m4a")
    return dst


def wav_seconds(wav: Path) -> float:
    with wave.open(str(wav), "rb") as w:
        return w.getnframes() / w.getframerate()


def split_wav(wav: Path, tmp: Path):
    """Cut a recording into overlapping windows; returns (file, start second) pairs."""
    parts, step = [], WINDOW_S - OVERLAP_S
    with wave.open(str(wav), "rb") as w:
        total, n = w.getnframes(), 0
        while True:
            start = n * step
            w.setpos(start * RATE)
            p = tmp / f"part{n}.wav"
            with wave.open(str(p), "wb") as o:
                o.setnchannels(1)
                o.setsampwidth(2)
                o.setframerate(RATE)
                o.writeframes(w.readframes(WINDOW_S * RATE))
            parts.append((p, start))
            n += 1
            if start * RATE + WINDOW_S * RATE >= total:
                return parts


def stitch(windows):
    """Join per-window speaker transcripts into one, keeping each person's label.

    Speaker numbers restart in every window. Two windows share OVERLAP_S seconds of
    audio, so a label in the new window is the same person as the earlier label it
    shares the most talking time with there. A person silent during the overlap
    cannot be matched and gets a new label; the count of those is returned so the
    caller can say so instead of presenting a guess as fact.
    """
    merged, unmatched, next_id = [], 0, 0
    for i, (segs, start) in enumerate(windows):
        if i == 0:
            mapping = {}
            for s in segs:
                if s["speaker"] not in mapping:
                    mapping[s["speaker"]] = next_id
                    next_id += 1
        else:
            lo, hi = start, start + OVERLAP_S
            shared = {}
            for new in segs:
                for old in merged:
                    t = min(new["end"], old["end"], hi) - max(new["start"], old["start"], lo)
                    if t > 0:
                        key = (new["speaker"], old["speaker"])
                        shared[key] = shared.get(key, 0) + t
            mapping, taken = {}, set()
            for (new_l, old_l), t in sorted(shared.items(), key=lambda kv: -kv[1]):
                if t >= 1.0 and new_l not in mapping and old_l not in taken:
                    mapping[new_l] = old_l
                    taken.add(old_l)
            for s in segs:
                if s["speaker"] not in mapping:
                    mapping[s["speaker"]] = next_id
                    next_id += 1
                    unmatched += 1
            # Each window owns the audio up to the middle of its overlap with the next.
            cut = start + OVERLAP_S / 2
            merged = [s for s in merged if s["start"] < cut]
            segs = [s for s in segs if s["start"] >= cut]
        merged += [{**s, "speaker": mapping[s["speaker"]]} for s in segs]
    for s in merged:
        s["speaker"] = str(s["speaker"])
    return merged, unmatched


def zrecover_grant(gb: int, note: str):
    """Ask the desktop memory guard for room for this process, and give it back on exit.

    zrecover stops any python process at 8 GB. The speakers model sits near 6 GB on a
    one-minute clip and grows with the length of the call.
    """
    if not shutil.which("zrecover"):
        return
    r = subprocess.run(["zrecover", "allow", "--pid", str(os.getpid()), "--gb", str(gb),
                        "--for", "90m", "--note", note, "--json"], capture_output=True, text=True)
    try:
        gid = json.loads(r.stdout)["id"]
    except (ValueError, KeyError):
        print("hear: no zrecover grant; a long call may be stopped at 8 GB", file=sys.stderr)
        return
    atexit.register(lambda: subprocess.run(["zrecover", "revoke", gid], capture_output=True))


def load_model(kind: str):
    from mlx_audio.stt.utils import load
    import mlx.core as mx

    # Left alone, MLX keeps freed buffers and the footprint climbs for no benefit.
    mx.set_cache_limit(2 * 1024**3)
    return load(MODELS[kind])


def run_model(model, kind: str, wav: Path, context: str = "", seconds: float = 0.0):
    """Run one transcriber over one audio file and return its segments.

    Every segment is {start, end, text} and, for the speakers model, {speaker}.
    """
    kw = {}
    if kind == "speakers":
        # The default token cap silently ends a long call early; size it to the audio.
        kw["max_tokens"] = int(min(60000, max(8192, seconds * 10)))
        if context:
            kw["context"] = context
    elif kind == "words" and context:
        kw["context"] = context
    elif kind == "stamps":
        # In one piece, 41 minutes asked the GPU for a single 60 GB buffer.
        kw["chunk_duration"], kw["overlap_duration"] = 120.0, 15.0
    out = model.generate(str(wav), **kw)
    segs = []
    if kind == "stamps":
        for s in out.sentences:
            segs.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})
    else:
        for s in out.segments or []:
            seg = {"start": round(float(s.get("start", 0)), 2), "end": round(float(s.get("end", 0)), 2),
                   "text": (s.get("text") or "").strip()}
            if kind == "speakers":
                if s.get("speaker_id") is None:
                    continue   # the model marks music and silence without a speaker
                seg["speaker"] = int(s["speaker_id"])
            segs.append(seg)
    truncated = kind == "speakers" and getattr(out, "generation_tokens", 0) >= kw.get("max_tokens", 1 << 30)
    return segs, truncated


def unload(model) -> None:
    """Free the transcriber before a text model is asked to load beside it."""
    import gc
    import mlx.core as mx

    del model
    gc.collect()
    mx.clear_cache()


def transcribe(src: Path, speakers: bool, context: str, tmp: Path, kind: str = ""):
    wav = to_wav(src, tmp)
    seconds = wav_seconds(wav)
    kind = kind or ("speakers" if speakers else "words")
    notes = []
    model = load_model(kind)
    if kind == "speakers":
        zrecover_grant(16, f"hear {src.name}")
        parts = [(wav, 0)] if seconds <= WINDOW_S else split_wav(wav, tmp)
        # Each finished window is written down at once. A long call takes minutes per
        # window, and a run stopped part way (the memory guard, a closed lid, ctrl-c)
        # picks up at the first window it has no file for.
        st = src.stat()
        key = hashlib.sha1(f"{src.resolve()}|{st.st_size}|{int(st.st_mtime)}|{MODELS[kind]}|{WINDOW_S}|{OVERLAP_S}|{context}".encode()).hexdigest()[:16]
        partial = OUT / ".partial" / key
        partial.mkdir(parents=True, exist_ok=True)
        windows, reused = [], 0
        for i, (p, offset) in enumerate(parts):
            done = partial / f"window-{i}.json"
            if done.is_file():
                saved = json.loads(done.read_text())
                part_segs, truncated = saved["segments"], saved["truncated"]
                reused += 1
            else:
                if len(parts) > 1:
                    print(f"hear: reading {stamp(offset)} to {stamp(min(seconds, offset + WINDOW_S))} ({i + 1} of {len(parts)})", file=sys.stderr)
                part_segs, truncated = run_model(model, kind, p, context, min(seconds, WINDOW_S))
                for s in part_segs:
                    s["start"], s["end"] = round(s["start"] + offset, 2), round(s["end"] + offset, 2)
                staged = done.with_suffix(".tmp")
                staged.write_text(json.dumps({"segments": part_segs, "truncated": truncated}))
                staged.replace(done)   # a half-written file must never look finished
            if truncated:
                notes.append(f"the window starting at {stamp(offset)} hit the model's output limit; its end may be missing")
            windows.append((part_segs, offset))
        if reused:
            print(f"hear: picked up {reused} of {len(parts)} windows from an earlier run that did not finish", file=sys.stderr)
        segs, unmatched = stitch(windows)
        shutil.rmtree(partial, ignore_errors=True)
        unload(model)
        if len(parts) > 1:
            # Matching by the shared minute misses anyone quiet during it. Their voice settles it.
            segs, note = settle_voices(segs, wav)
            notes.append(note)
    else:
        segs, _ = run_model(model, kind, wav, context, seconds)
        unload(model)
    return {"seconds": round(seconds, 1), "model": MODELS[kind], "segments": segs, "notes": notes,
            "text": " ".join(s["text"] for s in segs).strip()}


def settle_voices(segs, wav: Path):
    """Join speaker labels that are one person's voice; return the turns and a sentence on what was done."""
    import numpy as np
    import voiceprint
    with wave.open(str(wav), "rb") as w:
        audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    before = len({s["speaker"] for s in segs})
    segs, st = voiceprint.merge_voices(segs, audio)
    note = f"{before} speaker labels were checked by voice and came down to {st['people']}"
    if st["likely"]:
        note += f"; {st['likely']} brief label(s) were attached to the closest voice, which is likely but not certain"
    if st["unchecked"]:
        note += f"; {st['unchecked']} had too little speech to check"
    return segs, note


def stamp(t: float) -> str:
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60:02d}:{t % 60:02d}"


def as_markdown(tr: dict) -> str:
    """The transcript a person or a model reads: one line per turn, time and speaker first."""
    if not any("speaker" in s for s in tr["segments"]):
        return tr["text"] + "\n"
    return "".join(f"[{stamp(s['start'])}] Speaker {s['speaker']}: {s['text']}\n" for s in tr["segments"])


def words(text: str):
    # "40,000", "40 000" and "40000" are one number written three ways, not a disagreement.
    return re.findall(r"[a-z0-9']+", re.sub(r"(\d)[, ]+(?=\d{3}\b)", r"\1", text.lower()))


def agreement(a: str, b: str, samples: int = 8):
    """How much two transcripts of the same audio agree, word for word.

    Two unrelated models rarely make the same mistake, so a place where they differ
    is a place one of them is wrong. Returns the share of words both have in the
    same order, and a few of the differing spots to look at.
    """
    wa, wb = words(a), words(b)
    sm = difflib.SequenceMatcher(None, wa, wb, autojunk=False)
    same, diffs = 0, []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            same += i2 - i1
        else:
            diffs.append({"first": " ".join(wa[max(0, i1 - 3):i2 + 3]), "second": " ".join(wb[max(0, j1 - 3):j2 + 3])})
    step = max(1, len(diffs) // samples)
    return {"words_first": len(wa), "words_second": len(wb),
            "agree": round(same / max(1, max(len(wa), len(wb))), 4),
            "differing_spots": len(diffs), "samples": diffs[::step][:samples]}


def ask_q(intent: str, text: str, tier: str, schema: str = "", timeout: int = 900) -> dict:
    """Hand text to the local `q` tool under a named intent and return its JSON reply."""
    cmd = [str(ROOT / "bin" / "q"), "--intent", intent, "-m", tier, "--json", "--no-route",
           "--ctx", "-", "--max-ctx", "600000", "--timeout", str(timeout)]
    if schema:
        cmd += ["--format", str(ROOT / "intents" / schema)]
    r = subprocess.run(cmd, input=text, capture_output=True, text=True)
    try:
        reply = json.loads(r.stdout)
    except ValueError:
        raise HearError("model_failed", f"q {intent} gave no JSON: {(r.stderr or r.stdout)[-300:]}", "lm doctor")
    if not reply.get("ok", True) or reply.get("error"):
        raise HearError("model_failed", f"q {intent} failed: {json.dumps(reply)[:300]}", "lm doctor")
    return reply


def cited_times(line: str):
    """The transcript times a digest line cites: [04:12], or several as [04:12, 19:30]."""
    out = []
    for group in re.findall(r"\[([0-9:,\s]+)\]", line):
        out += re.findall(r"\d{1,2}:\d{2}(?::\d{2})?", group)
    return out


def check_digest(digest: str, tr: dict) -> dict:
    """Test that every point in a digest names a moment that exists in the transcript.

    This proves a point is anchored to something that was said at that time. It does
    not prove the point describes it correctly; that still takes a reader.
    """
    times = {stamp(s["start"]) for s in tr["segments"]}
    points = [ln for ln in digest.splitlines() if ln.lstrip().startswith(("-", "*"))]
    uncited, dangling = [], []
    for ln in points:
        cites = cited_times(ln)
        if not cites:
            uncited.append(ln.strip()[:120])
        dangling += [c for c in cites if c not in times]
    return {"points": len(points), "uncited": uncited, "times_not_in_transcript": sorted(set(dangling))}


def digest_evidence(digest: str, tr: dict) -> str:
    """Each digest point followed by the transcript lines it cites, for a reader to judge.

    The citation check proves a time exists. Whether the point describes that
    moment fairly is a judgment, and this page puts the two side by side so the
    judgment takes seconds per point instead of a re-listen.
    """
    by_time = {}
    for s in tr["segments"]:
        by_time.setdefault(stamp(s["start"]), []).append(f"Speaker {s.get('speaker', '?')}: {s['text']}")
    out = []
    for ln in digest.splitlines():
        out.append(ln)
        if ln.lstrip().startswith(("-", "*")):
            for c in cited_times(ln):
                for said in by_time.get(c, ["(no transcript line starts at this time)"]):
                    out.append(f"    > [{c}] {said}")
    return "\n".join(out) + "\n"


def save(name: str, payload: dict, files: dict, audio: Path = None) -> Path:
    """Write one run's folder: its result, its readable files, and the audio it heard.

    The audio is kept so the run can be done again with other options (`lm hear
    again`) and so there is always a recording to go back to. It is the 16 kHz
    mono copy, about 115 MB per hour.
    """
    d = OUT / f"{time.strftime('%Y%m%dT%H%M%S')}-{re.sub(r'[^A-Za-z0-9]+', '-', name)[:40].strip('-')}"
    d.mkdir(parents=True, exist_ok=True)
    for fname, body in files.items():
        (d / fname).write_text(body)
    if audio and audio.is_file():
        shutil.copy(audio, d / "audio.wav")
    (d / "result.json").write_text(json.dumps(payload, indent=1))
    return d


def log(row: dict) -> None:
    LOG.parent.mkdir(exist_ok=True)
    # Which terminal ran this, as bin/hear worked it out, so "my last run" means mine.
    who = {"tty": os.environ.get("LM_TTY") or None, "session": os.environ.get("LM_SESSION") or None}
    row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **row, **who}
    with LOG.open("a") as f:
        f.write(json.dumps(row) + "\n")


def past_runs():
    """Every run in the history file, oldest first. A run's number is its line number."""
    if not LOG.is_file():
        return []
    return [json.loads(ln) for ln in LOG.read_text().splitlines() if ln.strip()]


def pick_run(n_text: str):
    """One past run by number: 12 is the twelfth run, -1 (the default) is the latest."""
    runs = past_runs()
    try:
        n = int(n_text or -1)
    except ValueError:
        raise HearError("no_such_run", f"'{n_text}' is not a run number", "lm hear history")
    i = n - 1 if n > 0 else len(runs) + n
    if not 0 <= i < len(runs):
        raise HearError("no_such_run", f"there is no run {n}", "lm hear history")
    return i + 1, runs[i]


def history_line(n: int, r: dict) -> str:
    when = time.strftime("%b %d %H:%M", time.localtime(calendar.timegm(time.strptime(r["ts"], "%Y-%m-%dT%H:%M:%SZ"))))
    what = r.get("snippet") or (Path(r["file"]).name if r.get("file") else "")
    state = "" if r.get("ok") else f"failed: {r.get('error')}  "
    return f"{n:>4}  {when}  {r.get('verb') or '?':<10} {stamp(r.get('seconds') or 0):>7}  {state}{what}"


def audio_of(n: int, r: dict) -> Path:
    """The recording a past run heard: its kept copy, or the original file if that is still there."""
    kept = Path(r["artifact"]) / "audio.wav" if r.get("artifact") else None
    if kept and kept.is_file():
        return kept
    if r.get("file") and Path(r["file"]).is_file():
        return Path(r["file"])
    raise HearError("no_audio", f"run {n} kept no audio and its source file is gone", "lm hear history")


def main() -> int:
    ap = argparse.ArgumentParser(prog="lm hear", description="speech to text on this Mac: words, speakers, call digests, spoken intent")
    ap.add_argument("verb_or_file", help="call | intent | check, or a recording to transcribe")
    ap.add_argument("file", nargs="?", help="the recording (audio or video)")
    ap.add_argument("--speakers", action="store_true", help="say who is talking, with times (slower)")
    ap.add_argument("--context", default="", help="names and terms likely to be spoken, to get them spelled right")
    ap.add_argument("--text", default="", help="intent only: classify this text instead of a recording")
    ap.add_argument("--against", default="", help="check only: a result.json from an earlier hear run to judge against both transcribers")
    ap.add_argument("--notes", action="store_true", help="live only: keep listening and print each sentence as it ends")
    ap.add_argument("--intent", action="store_true", help="live only: also say what the spoken note is asking for")
    ap.add_argument("--seconds", type=float, default=0, help="live only: stop by itself after this long")
    ap.add_argument("--__feed", dest="feed", default="", help=argparse.SUPPRESS)   # tests: a wav played in place of the microphone
    ap.add_argument("--__feed-speed", dest="feed_speed", type=float, default=25.0, help=argparse.SUPPRESS)   # 1 plays it at life speed
    ap.add_argument("--state", default="", help=argparse.SUPPRESS)   # the folder the live screen and the listener share
    ap.add_argument("--plain", action="store_true", help="live notes only: plain lines, no screen")
    ap.add_argument("--as", dest="as_verb", default="", choices=["", "call", "intent", "check", "voices"],
                    help="again only: do the past run over as a call digest, an intent or a check; "
                         "voices re-checks who is who by voice without transcribing again")
    ap.add_argument("--json", action="store_true", help="one JSON object on stdout")
    a = ap.parse_args()

    verb = a.verb_or_file if a.verb_or_file in ("call", "intent", "check", "live", "history", "show", "again") else "words"
    src = Path(os.path.expanduser(a.file if verb != "words" else a.verb_or_file or "")) if (a.file or verb == "words") else None
    if verb in ("live", "history", "show", "again"):
        src = None
    elif src is None and not (verb == "intent" and a.text):
        ap.error(f"hear {verb} needs a recording")
    t0 = time.time()
    tmp = Path(tempfile.mkdtemp(prefix="hear-"))
    name = src.stem if src else "live"
    try:
        if verb == "history":
            runs = past_runs()
            count = int(a.file) if (a.file or "").isdigit() else 15
            shown = list(enumerate(runs, 1))[-count:]
            if a.json:
                print(json.dumps([{"n": n, **r} for n, r in shown]))
            else:
                print("\n".join(history_line(n, r) for n, r in shown) or "no runs yet", flush=True)
                print("lm hear show N opens one. lm hear again N does it over with other options.", file=sys.stderr)
            return 0
        if verb == "show":
            n, r = pick_run(a.file)
            d = Path(r["artifact"]) if r.get("artifact") else None
            if not d or not (d / "result.json").is_file():
                raise HearError("no_such_run", f"run {n} left no folder to open (it failed, or it was typed text)", "lm hear history")
            if a.json:
                print((d / "result.json").read_text())
            else:
                for fname in ("digest.md", "transcript.md"):
                    if (d / fname).is_file():
                        sys.stdout.write((d / fname).read_text().rstrip() + "\n\n")
                if not (d / "transcript.md").is_file():
                    print(json.loads((d / "result.json").read_text()).get("text", ""))
                print(f"run {n}: {d}", file=sys.stderr)
            return 0
        if verb == "again":
            n, r = pick_run(a.file)
            src = audio_of(n, r)
            verb = a.as_verb or "words"
            name = (Path(r["file"]).stem if r.get("file") else "live") + f"-again-{n}"
            if verb == "voices":
                old = json.loads((Path(r["artifact"]) / "result.json").read_text()) if r.get("artifact") else {}
                if not any("speaker" in s for s in old.get("segments", [])):
                    raise HearError("no_speakers", f"run {n} has no speaker labels to re-check", f"lm hear again {n} --speakers")
                segs, note = settle_voices(old["segments"], to_wav(src, tmp))
                tr = {**{k: old.get(k) for k in ("seconds", "model")}, "segments": segs, "notes": [note],
                      "text": " ".join(s["text"] for s in segs).strip()}
                payload = {"ok": True, "verb": "voices", **tr}
                md = as_markdown(tr)
                files, human = {"transcript.md": md}, md
                print(f"hear: {note}", file=sys.stderr)
        if verb == "voices":
            pass   # done above, from the past run's own words
        elif verb == "live":
            import hear_live
            payload = hear_live.run(a, tmp)
            files = {}
            # Notes mode has already printed every line as it was heard.
            human = "" if a.notes else payload["text"] + "\n" + (f"→ {json.dumps(payload['intent'])}\n" if a.intent else "")
        elif verb == "intent":
            tr = {"text": a.text, "seconds": 0, "model": None, "segments": [], "notes": []} if a.text \
                else transcribe(src, False, a.context, tmp)
            if not tr["text"].strip():
                raise HearError("no_speech", "nothing was said in that recording")
            reply = ask_q("voice-intent", tr["text"], "small", "voice-intent.schema.json", 120)
            payload = {"ok": True, "verb": verb, "text": tr["text"], "intent": reply.get("data"), "seconds": tr["seconds"]}
            human = f"{tr['text']}\n→ {json.dumps(reply.get('data'))}\n"
            files = {}
        elif verb == "check":
            first = transcribe(src, False, a.context, tmp, "words")
            second = transcribe(src, False, "", tmp, "stamps")
            ag = agreement(first["text"], second["text"])
            payload = {"ok": True, "verb": verb, "seconds": first["seconds"], "first": first["model"],
                       "second": second["model"], "agreement": ag}
            human = (f"{ag['agree']:.1%} of words agree between two unrelated transcribers "
                     f"({ag['differing_spots']} differing spots in {ag['words_first']} words)\n"
                     + "".join(f"  {d['first']!r}  vs  {d['second']!r}\n" for d in ag["samples"]))
            files = {"first.txt": first["text"], "second.txt": second["text"]}
            if a.against:
                # A transcript made earlier (say, the speakers one) judged against both fresh reads.
                given = json.loads(Path(os.path.expanduser(a.against)).read_text())["text"]
                payload["against"] = {"first": agreement(given, first["text"]), "second": agreement(given, second["text"])}
                for name in ("first", "second"):
                    g = payload["against"][name]
                    human += (f"the given transcript agrees {g['agree']:.1%} with the {name} transcriber "
                              f"({g['words_first']} words against {g['words_second']})\n"
                              + "".join(f"  {d['first']!r}  vs  {d['second']!r}\n" for d in g["samples"][:4]))
        else:
            tr = transcribe(src, a.speakers or verb == "call", a.context, tmp)
            if not tr["text"].strip():
                raise HearError("no_speech", "nothing was said in that recording")
            md = as_markdown(tr)
            payload = {"ok": True, "verb": verb, **tr}
            files, human = {"transcript.md": md}, md
            if verb == "call":
                # The transcript is the expensive half. Keep it even when the digest fails.
                try:
                    reply = ask_q("call-digest", md, "big")
                    digest = reply.get("text") or reply.get("response") or ""
                    payload["digest"], payload["digest_check"] = digest, check_digest(digest, tr)
                    files["digest.md"] = digest
                    files["digest-evidence.md"] = digest_evidence(digest, tr)
                    dc = payload["digest_check"]
                    human = (digest + f"\n\n({dc['points']} points; {len(dc['uncited'])} without a time, "
                             f"{len(dc['times_not_in_transcript'])} citing a time that is not in the transcript)\n")
                except HearError as e:
                    payload["digest"], payload["digest_error"] = None, e.message
                    print(f"hear: transcript kept, digest failed: {e.message}", file=sys.stderr)
            for n in tr["notes"]:
                print(f"hear: {n}", file=sys.stderr)
        payload["ms"] = int((time.time() - t0) * 1000)
        # Live notes made their own folder as they went. Typed text has nothing to keep.
        if not payload.get("artifact") and (src or (tmp / "audio.wav").is_file()):
            payload["artifact"] = str(save(name, payload, files, tmp / "audio.wav"))
        log({k: payload.get(k) for k in ("verb", "seconds", "model", "ms", "artifact", "intent")}
            | {"file": str(src) if src else None, "ok": True, "snippet": " ".join((payload.get("text") or "").split())[:80]})
        if a.json:
            print(json.dumps(payload))
        else:
            sys.stdout.write(human)
            if payload.get("artifact") and not (verb == "live" and a.notes):
                print(f"saved: {payload['artifact']}", file=sys.stderr)
        return 0
    except HearError as e:
        if verb not in ("history", "show"):   # looking at the history is not itself a run
            log({"verb": verb, "file": str(src) if src else None, "ok": False, "error": e.code})
        if a.json:
            print(json.dumps({"ok": False, "error": e.code, "message": e.message, "remedy": e.remedy}))
        else:
            print(f"hear: {e.message}" + (f"\n  fix: {e.remedy}" if e.remedy else ""), file=sys.stderr)
        return 12 if e.code in ("no_such_file", "audio_unreadable", "no_such_run", "no_audio") else 10
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
