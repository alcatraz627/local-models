#!/usr/bin/env python3
"""Deterministic script baselines for the cases tagged script_beats_model.

Each baseline answers the case with plain pixel work or an existing no-model
lane (`see --ocr`, the vis-compare E5 grid). Its answer is scored through the
same scorer as a model reply, so the report can show script and model side by
side. A baseline that cannot run here (a missing OCR tool) returns None and the
selftest reports it as skipped, never as passed.

    .venv/bin/python probe/vision/baselines.py [--seeds 0,1,2]
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops

from common import REPO, ROOT, SEE, case_dir, case_map, load_truth, seeds_for
from gen import generate_one
from score import score

VIS_COMPARE = REPO / "lib" / "vis-compare.py"


def _components(mask):
    """4-connected components of a boolean mask, as lists of (y, x)."""
    h, w = mask.shape
    todo = {(int(y), int(x)) for y, x in zip(*np.nonzero(mask))}
    comps = []
    while todo:
        seed = todo.pop()
        stack, comp = [seed], [seed]
        while stack:
            y, x = stack.pop()
            for n in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if n in todo:
                    todo.remove(n)
                    stack.append(n)
                    comp.append(n)
        comps.append(comp)
    return comps


def c02(folder):
    """Dark blobs whose pixels fill most of their bounding box are filled dots; rings fill about a third."""
    gray = np.asarray(Image.open(folder / "image.png").convert("L"))
    filled = 0
    for comp in _components(gray < 100):
        ys, xs = zip(*comp)
        box = (max(ys) - min(ys) + 1) * (max(xs) - min(xs) + 1)
        if len(comp) / box > 0.6:
            filled += 1
    return {"answer": str(filled), "method": "threshold, connected components, keep fill ratio above 0.6"}


def o03(folder):
    """The cell whose mean colour sits farthest from the median cell is the odd one."""
    px = np.asarray(Image.open(folder / "image.png").convert("RGB"), dtype=float)
    means = np.array([px[r * 160 + 40:r * 160 + 120, c * 160 + 40:c * 160 + 120].mean(axis=(0, 1))
                      for r in range(3) for c in range(4)])
    dist = np.linalg.norm(means - np.median(means, axis=0), axis=1)
    return {"answer": str(int(dist.argmax()) + 1), "method": "per-cell mean RGB, farthest from the median cell"}


def d02(folder):
    """The vis-compare E5 grid (what `see diff --no-read --grid 4` ships), top cell, 1-based."""
    out = subprocess.run([sys.executable, str(VIS_COMPARE), str(folder / "a.png"), str(folder / "b.png"),
                          "--grid", "4", "--only", "E5"], capture_output=True, text=True)
    top = json.loads(out.stdout)["grid_heat"]["top_cells"][0]["cell"]
    return {"answer": f"r{top[0] + 1}c{top[1] + 1}", "method": "vis-compare E5 --grid 4, top cell"}


def _see_ocr_text(image):
    if not shutil.which("mac-ocr"):
        return None
    out = subprocess.run([str(SEE), str(image), "--ocr", "--json"], capture_output=True, text=True, timeout=120)
    try:
        return json.loads(out.stdout).get("text", "")
    except ValueError:
        return None


def t06(folder):
    text = _see_ocr_text(folder / "image.png")
    if text is None:
        return None
    return {"answer": text, "method": "see --ocr --json (Apple Vision)", "raw": True}


def _content_center(im):
    box = ImageChops.difference(im.convert("RGB"), Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)


def d07(folder):
    """Centre of the non-white content in A and B; the dominant axis of the shift is the direction.

    The catalog expected vis-compare E1 to report this move, but E1 only lists a
    move when the 3x3 position label changes, and a 24 px shift stays inside one
    label. `e1_moved` records what E1 really said so the gap stays visible.
    """
    a, b = Image.open(folder / "a.png"), Image.open(folder / "b.png")
    (ax, ay), (bx, by) = _content_center(a), _content_center(b)
    dx, dy = bx - ax, by - ay
    if abs(dx) >= abs(dy):
        direction = "right" if dx > 0 else "left"
    else:
        direction = "down" if dy > 0 else "up"
    name = _see_ocr_text(folder / "b.png")
    if name is None:
        return None
    return {"answer": f"{name.strip()} moved {direction}", "method": "centre of non-white content, A vs B",
            "shift_px": round(max(abs(dx), abs(dy))), "e1_moved": _e1_moved(folder)}


def _e1_moved(folder):
    with tempfile.TemporaryDirectory() as td:
        paths = {}
        for side in ("a", "b"):
            paths[side] = Path(td) / f"{side}.jsonl"
            with open(paths[side], "w") as fh:
                subprocess.run(["mac-ocr", "--format", "jsonl", str(folder / f"{side}.png")], stdout=fh,
                               stderr=subprocess.DEVNULL)
        out = subprocess.run([sys.executable, str(VIS_COMPARE), str(folder / "a.png"), str(folder / "b.png"),
                              "--ocr-a", str(paths["a"]), "--ocr-b", str(paths["b"])], capture_output=True, text=True)
    try:
        return bool(json.loads(out.stdout)["text_diff"]["moved"])
    except (ValueError, KeyError):
        return None


BASELINES = {"C02": c02, "O03": o03, "D02": d02, "T06": t06, "D07": d07}


def baseline_cases(catalog=None):
    return [c for c in case_map(catalog).values() if "script_beats_model" in c.get("capability", [])]


def run_baseline(case_id, seed, folder=None):
    """Run one baseline on a fixture folder and score its answer. Returns None when it cannot run."""
    folder = Path(folder or case_dir(case_id, seed))
    fn = BASELINES.get(case_id)
    if fn is None:
        raise ValueError(f"{case_id} is tagged script_beats_model but has no baseline")
    result = fn(folder)
    if result is None:
        return None
    truth = json.loads((folder / "truth.json").read_text())
    reply = result["answer"] if result.get("raw") else "ANSWER: " + result["answer"]
    return {"case": case_id, "seed": seed, **result, "score": score(case_id, reply, truth)}


def run_all(seeds=(0, 1, 2), catalog=None):
    rows = []
    for case in baseline_cases(catalog):
        for seed in seeds_for(case["id"], seeds):
            if not case_dir(case["id"], seed).exists():
                generate_one(case["id"], seed, case)
            row = run_baseline(case["id"], seed)
            if row:
                rows.append(row)
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--seeds", default="0,1,2")
    p.add_argument("--output", default=str(ROOT / "baselines.json"))
    a = p.parse_args()
    rows = run_all(tuple(int(s) for s in a.seeds.split(",")))
    Path(a.output).write_text(json.dumps(
        [{k: v for k, v in r.items() if k != "raw"} for r in rows], indent=2, ensure_ascii=False) + "\n")
    bad = [r for r in rows if r["score"]["status"] != "pass"]
    for r in rows:
        print("ok" if r["score"]["status"] == "pass" else "FAIL", r["case"], f"s{r['seed']}", repr(r["answer"][:60]))
    print(f"{len(rows) - len(bad)}/{len(rows)} baselines passed")
    raise SystemExit(bool(bad))


if __name__ == "__main__":
    main()
