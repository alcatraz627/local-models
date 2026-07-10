#!/usr/bin/env python3
"""Model-free assertions for the visual-compare fixtures — the fabrication guard
and every extractor's detect/stay-silent contract, run by verify.sh.

Each fixture plants known ground truth (see make-fixtures.py); this checks the
deterministic extractors detect the planted difference AND stay silent on the
identical pair. No model runs here — these are the $0 assertions that must be
green before the capability is called done. Text-lane checks (E1) run only when
mac-ocr is present; they skip cleanly otherwise, matching the soft-failure design.

Exit 0 = all assertions pass. Run: .venv/bin/python probe/fixtures/vis-battery.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
VP = [os.path.join(ROOT, ".venv/bin/python"), os.path.join(ROOT, "lib/vis-compare.py")]
HAVE_OCR = shutil.which("mac-ocr") is not None


def run(a, b, *args, ocr=False):
    cmd = VP + [os.path.join(HERE, a), os.path.join(HERE, b)] + list(args)
    if ocr and HAVE_OCR:
        td = tempfile.mkdtemp()
        for side, path in (("a", a), ("b", b)):
            with open(os.path.join(td, side + ".jsonl"), "w") as f:
                subprocess.run(["mac-ocr", "--format", "jsonl", os.path.join(HERE, path)],
                               stdout=f, stderr=subprocess.DEVNULL)
        cmd += ["--ocr-a", os.path.join(td, "a.jsonl"), "--ocr-b", os.path.join(td, "b.jsonl")]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("vis-compare failed: " + out.stderr[:200])
    return json.loads(out.stdout)


CHECKS = []


def check(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))


# F1 · login pair (pre-existing diff-a/b) — regression guard: pack still builds
p = run("diff-a.png", "diff-b.png")
check("F1 login pair: pack builds, comparable",
      "scores" in p and p["meta"]["comparable"] != "poor")

# F2 · icon pair — dhash>0, E3 catches the hue, E6 ranks the corner cells
p = run("f2-a.png", "f2-b.png")
top4 = {tuple(c["cell"]) for c in p["edge_shape"]["top_cells"][:4]}
check("F2 icon: dhash > 0 (structure differs)", p["scores"]["dhash"] > 0,
      "dhash=%s" % p["scores"]["dhash"])
check("F2 icon: E3 catches hue (a 'different' palette pair)",
      any(x["word"] == "different" for x in p["color"]["palette_pairs"]))
check("F2 icon: E6 ranks the 4 corner cells",
      all(r in (1, 6) and c in (1, 6) for r, c in top4) and len(top4) == 4,
      "top4=%s" % sorted(top4))

# F3 · identical pair — THE FABRICATION GUARD: every signal exactly zero
p = run("f3-a.png", "f3-b.png")
s = p["scores"]
check("F3 fabrication guard: ALL extractors zero on identical input",
      s["dhash"] == 0 and s["ahash"] == 0 and s["grid_delta_pct"] == 0.0
      and s["palette_delta_avg"] == 0.0 and p["edge_shape"]["hot_cell_pct"] == 0.0,
      "scores=%s edge_hot=%s" % (s, p["edge_shape"]["hot_cell_pct"]))

# F4 · theme pair — systematic ΔE (E5 hot everywhere); with OCR, E1 empty + texty
p = run("f4-a.png", "f4-b.png", ocr=True)
check("F4 theme: E5 systematically hot (>50% cells)", p["grid_heat"]["hot_cell_pct"] > 50,
      "hot%%=%s" % p["grid_heat"]["hot_cell_pct"])
if "text_diff" in p:
    td = p["text_diff"]
    check("F4 theme: E1 empty (same text, theme flip)",
          not (td["removed"] or td["added"] or td["moved"]), "td=%s" % td)
    check("F4 theme: modality texty", p["meta"]["modality"] == "texty")

# F5 · incomparable pair — comparability gate fires
p = run("f5-a.png", "f5-b.png")
check("F5 incomparable: comparable=poor", p["meta"]["comparable"] == "poor",
      p["meta"].get("comparable_why"))

# F6 · chart pair — E5 localizes the taller bar; with OCR, Q3→Q5 relabel
p = run("f6-a.png", "f6-b.png", ocr=True)
topcols = {c["cell"][1] for c in p["grid_heat"]["top_cells"][:5]}
check("F6 chart: E5 localizes the taller bar (cols 9-11)", bool(topcols & {9, 10, 11}),
      "cols=%s" % sorted(topcols))
if "text_diff" in p:
    td = p["text_diff"]
    check("F6 chart: E1 catches Q3→Q5 relabel",
          "Q3" in td["removed"] and "Q5" in td["added"], "td=%s" % td)

# F7 · slice rerun — a full run seeds the cache, --only re-runs one extractor at
# a new grid and returns a delta (not the whole pack); the cached pack is patched
cache = tempfile.mkdtemp()
run("f2-a.png", "f2-b.png", "--cache-dir", cache)  # seed at default grid 8
d = run("f2-a.png", "f2-b.png", "--only", "E5", "--grid", "32", "--cache-dir", cache)
check("F7 slice rerun: delta-only output, grid 8→32",
      "delta" in d and d["delta"]["E5"]["before"]["grid_n"] == 8
      and d["delta"]["E5"]["after"]["grid_n"] == 32, "delta=%s" % d.get("delta"))
shutil.rmtree(cache, ignore_errors=True)

# F8 · failure salvage — without OCR the pack still ships E3-E6 (salvage-first);
# E1 is recorded as skipped, not fatal; exit 0
p = run("diff-a.png", "diff-b.png")
check("F8 salvage: E3-E6 ship without OCR, E1 skipped, exit 0",
      "grid_heat" in p and "edge_shape" in p and "color" in p
      and "E1" in p["meta"]["skipped_extractors"])

fails = [c for c in CHECKS if not c[1]]
for name, ok, detail in CHECKS:
    tail = ("  [%s]" % detail) if (detail and not ok) else ""
    print("  %s %s%s" % ("ok  " if ok else "FAIL", name, tail))
if not HAVE_OCR:
    print("  note: mac-ocr absent — E1 text-lane assertions skipped")
print("%d/%d vis-compare assertions passed" % (len(CHECKS) - len(fails), len(CHECKS)))
sys.exit(1 if fails else 0)
