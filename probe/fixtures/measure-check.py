#!/usr/bin/env python3
"""Model-free checks for the measuring lane (`see count`, `see odd`, lib/measure.py).

Runs the measurer on every generated vision fixture it is meant to solve, then on
the cases where the right answer is "I cannot tell": a blank image, two identical
items, and the busy rug border. No model runs. Exit 0 = every check passed.

    .venv/bin/python probe/fixtures/measure-check.py
"""
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "probe", "vision"))

from common import FIXTURES, case_dir, case_map, seeds_for  # noqa: E402
from gen import generate_one  # noqa: E402

MEASURE = [os.path.join(ROOT, ".venv/bin/python"), os.path.join(ROOT, "lib/measure.py")]
CHECKS = []


def check(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))


def measure(*args):
    """Run measure.py and return (exit code, parsed JSON). A traceback or non-JSON output raises."""
    out = subprocess.run(MEASURE + [str(a) for a in args], capture_output=True, text=True)
    return out.returncode, json.loads(out.stdout)


def fixture(case_id, seed):
    folder = case_dir(case_id, seed)
    if not (folder / "truth.json").exists():
        generate_one(case_id, seed, case_map()[case_id])
    return folder / "image.png", json.loads((folder / "truth.json").read_text())


def temp_png(draw_fn, size=(400, 300)):
    im = Image.new("RGB", size, (255, 255, 255))
    draw_fn(ImageDraw.Draw(im))
    fh = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    im.save(fh.name)
    return fh.name


for seed in seeds_for("C01"):
    img, truth = fixture("C01", seed)
    _, r = measure("count", img)
    check(f"C01 s{seed}: counts {truth['count']} dots", r["answer"] == truth["count"] and not r["ambiguous"],
          f"got {r['answer']}")

for seed in seeds_for("C02"):
    img, truth = fixture("C02", seed)
    _, r = measure("count", img, "--filled-only")
    check(f"C02 s{seed}: {truth['count']} solid dots, {truth['decoys']} rings dropped", r["answer"] == truth["count"],
          f"got {r['answer']}")
img, truth = fixture("C02", 0)
_, r = measure("count", img)
check("C02 without --filled-only counts the rings too (the flag does the work)",
      r["answer"] == truth["count"] + truth["decoys"], f"got {r['answer']}")

for seed in seeds_for("C03"):
    img, truth = fixture("C03", seed)
    _, r = measure("count", img, "--color", truth["color"])
    check(f"C03 s{seed}: {truth['count']} {truth['color']} squares of {truth['total']}", r["answer"] == truth["count"],
          f"got {r['answer']}")
    _, r_all = measure("count", img)
    check(f"C03 s{seed}: no colour filter counts all {truth['total']}", r_all["answer"] == truth["total"],
          f"got {r_all['answer']}")

for case_id in ("O01", "O02", "O03"):
    for seed in seeds_for(case_id):
        img, truth = fixture(case_id, seed)
        _, r = measure("odd", img)
        check(f"{case_id} s{seed}: odd one is {truth['index']}", r["answer"] == truth["index"] and not r["ambiguous"],
              f"got {r['answer']}, why: {r['why'][:80]}")

# The rug border: motifs touch a line and a band, so the general method cannot isolate them.
# Right answer is 9; "ambiguous" is the honest second best. A wrong index is the failure.
img, truth = fixture("O04", 0)
_, r = measure("odd", img)
check("O04 rug: answers 9 or says ambiguous, never a wrong index",
      r["answer"] == truth["index"] or (r["answer"] is None and r["ambiguous"]), f"got {r['answer']}")

# Blank page: nothing to count, nothing to pick.
blank = temp_png(lambda d: None)
_, r = measure("count", blank)
check("blank image: count is 0", r["ok"] and r["answer"] == 0, str(r.get("answer")))
_, r = measure("odd", blank)
check("blank image: odd invents no index", r["ok"] and r["answer"] is None and r["ambiguous"], str(r.get("answer")))

# Two identical items: there is no outlier.
twins = temp_png(lambda d: [d.rectangle(b, fill=(0, 0, 0)) for b in ((50, 100, 120, 170), (250, 100, 320, 170))])
_, r = measure("odd", twins)
check("two identical items: odd is ambiguous", r["answer"] is None and r["ambiguous"], str(r))

# Identical items in a grid: no outlier either.
same = temp_png(lambda d: [d.rectangle((40 + 90 * i, 100, 90 + 90 * i, 150), fill=(0, 0, 0)) for i in range(4)])
_, r = measure("odd", same)
check("four identical items: odd is ambiguous, not a pick", r["answer"] is None and r["ambiguous"], str(r["answer"]))

# Touching objects must widen the count instead of reporting a confident number.
touch = temp_png(lambda d: [d.rectangle((20 + 40 * i, 100, 55 + 40 * i, 135), fill=(0, 0, 0)) for i in range(4)] +
                 [d.rectangle((260, 100, 380, 135), fill=(0, 0, 0))])
_, r = measure("count", touch)
check("one blob three times the size of the rest: count is flagged ambiguous with a range",
      r["ambiguous"] and r["range"][0] < r["range"][1], str(r.get("range")))

# Failing closed: structured errors, right exit codes, no traceback.
code, r = measure("count", os.path.join(tempfile.gettempdir(), "no-such-image.png"))
check("missing file: exit 12, structured error", code == 12 and not r["ok"] and r["code"] == "img_unreadable", f"exit {code}")
code, r = measure("count", blank, "--color", "mauve")
check("unknown colour: exit 2, structured error", code == 2 and not r["ok"] and r["code"] == "invalid_args", f"exit {code}")
code, r = measure("count")
check("no image: exit 2, structured error", code == 2 and not r["ok"], f"exit {code}")
notimg = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
notimg.write(b"not a picture")
notimg.close()
code, r = measure("odd", notimg.name)
check("unreadable bytes: exit 12, structured error", code == 12 and not r["ok"], f"exit {code}")

failed = [c for c in CHECKS if not c[1]]
for name, good, detail in CHECKS:
    print(("ok   " if good else "FAIL ") + name + ("" if good or not detail else "  [" + detail + "]"))
print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} passed")
sys.exit(1 if failed else 0)
