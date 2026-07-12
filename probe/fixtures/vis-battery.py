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

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
VP = [os.path.join(ROOT, ".venv/bin/python"), os.path.join(ROOT, "lib/vis-compare.py")]
HAVE_OCR = shutil.which("mac-ocr") is not None


def _p(x):
    return x if os.path.isabs(x) else os.path.join(HERE, x)


def run(a, b, *args, ocr=False):
    cmd = VP + [_p(a), _p(b)] + list(args)
    if ocr and HAVE_OCR:
        td = tempfile.mkdtemp()
        for side, path in (("a", a), ("b", b)):
            with open(os.path.join(td, side + ".jsonl"), "w") as f:
                subprocess.run(["mac-ocr", "--format", "jsonl", _p(path)],
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

# F3b · perceptual-identity guard — a JPEG re-encode is perceptually identical but
# perturbs the low-population palette tail; the fabrication guard must hold HERE too
# (byte-identity F3 never exercises re-encode/anti-alias jitter — the real-world case)
_td = tempfile.mkdtemp()
_jpg = os.path.join(_td, "f4-reencode.jpg")
Image.open(os.path.join(HERE, "f4-a.png")).convert("RGB").save(_jpg, quality=85)
p = run("f4-a.png", _jpg)
s = p["scores"]
check("F3b perceptual-identity: JPEG re-encode stays clean (no fabricated palette diff)",
      s["dhash"] <= 3 and s["grid_delta_pct"] < 5.0 and s["palette_delta_avg"] < 5.0,
      "dhash=%s grid%%=%s palette_avg=%s" % (s["dhash"], s["grid_delta_pct"], s["palette_delta_avg"]))
shutil.rmtree(_td, ignore_errors=True)

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

# F9 · E1 numeric moved coords — synthesized OCR jsonl (model-free; runs without
# mac-ocr, unlike F4/F6's text checks). Plants a known 0.5,0.6 displacement, an
# unmoved line, and an ambiguous 2-vs-1 duplicate ("OK") whose pairing must NOT
# fabricate a scalar delta.
def _obs(*items):
    return {"observations": [
        {"text": t, "boundingBox": {"x": x, "y": y, "width": w, "height": h}}
        for t, x, y, w, h in items]}


_td = tempfile.mkdtemp()
_oa, _ob = os.path.join(_td, "oa.json"), os.path.join(_td, "ob.json")
json.dump(_obs(("Submit button", 0.1, 0.1, 0.2, 0.05),    # center (0.2, 0.125)
               ("Static footer text", 0.4, 0.8, 0.2, 0.05),
               ("OK", 0.05, 0.05, 0.1, 0.05),
               ("OK", 0.85, 0.05, 0.1, 0.05)), open(_oa, "w"))
json.dump(_obs(("Submit button", 0.6, 0.7, 0.2, 0.05),    # center (0.7, 0.725)
               ("Static footer text", 0.4, 0.8, 0.2, 0.05),
               ("OK", 0.45, 0.45, 0.1, 0.05)), open(_ob, "w"))
p = run("f3-a.png", "f3-b.png", "--ocr-a", _oa, "--ocr-b", _ob)
mv = {m["text"]: m for m in p["text_diff"]["moved"]}


def _near(got, want, tol=1e-6):
    return got is not None and len(got) == len(want) and \
        all(abs(g - w) < tol for g, w in zip(got, want))


sub = mv.get("Submit button", {})
check("F9 E1 coords: planted move carries from_xy/to_xy/delta_xy",
      _near(sub.get("from_xy", [[]])[0], [0.2, 0.125])
      and _near(sub.get("to_xy", [[]])[0], [0.7, 0.725])
      and _near(sub.get("delta_xy"), [0.5, 0.6]), "sub=%s" % sub)
check("F9 E1 coords: unmoved text stays out of `moved`",
      "Static footer text" not in mv
      and not p["text_diff"]["removed"] and not p["text_diff"]["added"],
      "moved=%s" % sorted(mv))
ok = mv.get("OK", {})
check("F9 E1 coords: ambiguous 2-vs-1 duplicate ships coords but NO scalar delta",
      "OK" in mv and ok.get("delta_xy") is None
      and ok.get("from_xy") == [[0.1, 0.075], [0.9, 0.075]]  # sorted by (cy, cx)
      and ok.get("to_xy") == [[0.5, 0.475]],
      "ok=%s" % ok)
shutil.rmtree(_td, ignore_errors=True)

# F9b · malformed-geometry guard — an observation missing its boundingBox (or with
# non-finite fields) must NOT fabricate a position/motion; it is skipped like
# text-less observations, so the text degrades to ADDED, and the pack stays
# strict-JSON (no NaN tokens).
_td = tempfile.mkdtemp()
_oa, _ob = os.path.join(_td, "oa.json"), os.path.join(_td, "ob.json")
_a = _obs(("Anchor line here please", 0.1, 0.1, 0.2, 0.05))
_a["observations"].append({"text": "Ghost label"})  # no boundingBox at all
_a["observations"].append({"text": "Nan box", "boundingBox":
                           {"x": 0.2, "y": 0.2, "width": float("nan"), "height": 0.05}})
json.dump(_a, open(_oa, "w"))
json.dump(_obs(("Anchor line here please", 0.1, 0.1, 0.2, 0.05),
               ("Ghost label", 0.8, 0.8, 0.1, 0.05),
               ("Nan box", 0.6, 0.6, 0.1, 0.05)), open(_ob, "w"))
p = run("f3-a.png", "f3-b.png", "--ocr-a", _oa, "--ocr-b", _ob)
td = p["text_diff"]
check("F9b malformed geometry: no fabricated move, text degrades to ADDED",
      not td["moved"] and sorted(td["added"]) == ["Ghost label", "Nan box"]
      and not td["removed"], "td=%s" % td)
try:
    json.dumps(p, allow_nan=False)
    check("F9b malformed geometry: pack is strict JSON (no NaN/Infinity)", True)
except ValueError as e:
    check("F9b malformed geometry: pack is strict JSON (no NaN/Infinity)", False, str(e))
shutil.rmtree(_td, ignore_errors=True)

# F10 · loop ledger — transitions + convergence stop-rules (pure JSON, no images).
# Drives lib/vis-ledger.py through a synthesized 5-round loop: fix, regress, stall,
# converge. Status words are set-comparisons over divergence ids — script territory,
# so the battery owns their correctness.
VL = [os.path.join(ROOT, ".venv/bin/python"), os.path.join(ROOT, "lib/vis-ledger.py")]


def _verdict(path, overall, ids_judgments, iteration):
    json.dump({"overall": overall, "policy_version": "v3", "iteration": iteration,
               "divergences": [{"id": i, "class": "brand-color", "judgment": j,
                                "gestalt": False} for i, j in ids_judgments]},
              open(path, "w"))


def _ladd(loopdir, vpath, *args):
    out = subprocess.run(VL + ["add", loopdir, vpath] + list(args),
                         capture_output=True, text=True)
    try:
        return out.returncode, json.loads(out.stdout)
    except Exception:
        return out.returncode, {"_raw": (out.stdout + out.stderr)[:300]}


_ld = os.path.join(tempfile.mkdtemp(), "loop1")
_vp = os.path.join(tempfile.mkdtemp(), "v.json")

_verdict(_vp, "diverges", [("d-a", "looks-worse"), ("d-b", "neutral")], 1)
rc1, r1 = _ladd(_ld, _vp)
check("F10 ledger r1: both divergences enter as new",
      rc1 == 0 and sorted(r1.get("transitions", {}).get("new", [])) == ["d-a", "d-b"]
      and not r1.get("signals", {}).get("stop"), "r1=%s" % r1)

_verdict(_vp, "diverges", [("d-b", "neutral"), ("d-c", "looks-worse")], 2)
rc2, r2 = _ladd(_ld, _vp)
t2 = r2.get("transitions", {})
check("F10 ledger r2: d-a fixed, d-b persisting, d-c new",
      rc2 == 0 and t2.get("fixed") == ["d-a"] and t2.get("persisting") == ["d-b"]
      and t2.get("new") == ["d-c"], "r2=%s" % r2)

_verdict(_vp, "diverges", [("d-a", "looks-worse"), ("d-b", "neutral"), ("d-c", "looks-worse")], 3)
rc3, r3 = _ladd(_ld, _vp)
check("F10 ledger r3: d-a regressed (was fixed, is back); no stall yet",
      rc3 == 0 and r3.get("transitions", {}).get("regressed") == ["d-a"]
      and not r3.get("signals", {}).get("stall"), "r3=%s" % r3)

_verdict(_vp, "diverges", [("d-a", "looks-worse"), ("d-b", "neutral"), ("d-c", "looks-worse")], 4)
rc4, r4 = _ladd(_ld, _vp)
t4, s4 = r4.get("transitions", {}), r4.get("signals", {})
check("F10 ledger r4: identical round fabricates nothing (all persisting) AND stalls",
      rc4 == 0 and sorted(t4.get("persisting", [])) == ["d-a", "d-b", "d-c"]
      and not t4.get("new") and not t4.get("fixed") and not t4.get("regressed")
      and s4.get("stall") is True and s4.get("next"), "r4=%s" % r4)

_verdict(_vp, "pass", [], 5)
rc5, r5 = _ladd(_ld, _vp)
check("F10 ledger r5: policy-pass stop, remaining divergences all fixed",
      rc5 == 0 and r5.get("signals", {}).get("stop") == "policy-pass"
      and sorted(r5.get("transitions", {}).get("fixed", [])) == ["d-a", "d-b", "d-c"],
      "r5=%s" % r5)

# comparability hard block (§5.6): a loop round against a poor pair is rejected
# with a fix-proposing error, and the ledger file is left untouched
def _ledger_raw(loopdir):
    try:
        return open(os.path.join(loopdir, "ledger.json")).read()
    except OSError:
        return ""


_pp = os.path.join(os.path.dirname(_vp), "pack-poor.json")
json.dump({"meta": {"comparable": "poor", "comparable_why": "aspect 3.1x"}}, open(_pp, "w"))
_verdict(_vp, "diverges", [("d-z", "looks-worse")], 6)
_before = _ledger_raw(_ld)
rc6, r6 = _ladd(_ld, _vp, "--pack", _pp)
check("F10 ledger: comparable-poor round rejected, ledger untouched, error explains",
      rc6 != 0 and _before != "" and _before == _ledger_raw(_ld) and bool(r6),
      "rc=%s r6=%s" % (rc6, r6))

# F10b · malformed SHAPES (valid JSON, wrong structure) — every case must produce
# the structured fix-proposing error (exit 2, parseable ok:false), never a
# traceback, and add/status must agree on a corrupted ledger instead of status
# fabricating an empty loop.
def _structured(rc, out):
    return rc == 2 and isinstance(out, dict) and out.get("ok") is False and out.get("fix")


_bd = tempfile.mkdtemp()
_bad = os.path.join(_bd, "bad.json")

open(_bad, "w").write('["not", "an", "object"]')
rc, out = _ladd(os.path.join(_bd, "l1"), _bad)
check("F10b shape: array verdict → structured error", _structured(rc, out), "rc=%s out=%s" % (rc, out))

open(_bad, "w").write('{"overall": "diverges", "divergences": "nope"}')
rc, out = _ladd(os.path.join(_bd, "l2"), _bad)
check("F10b shape: string divergences → structured error", _structured(rc, out), "rc=%s out=%s" % (rc, out))

_cl = os.path.join(_bd, "l3")
os.makedirs(_cl)
open(os.path.join(_cl, "ledger.json"), "w").write("{}")
_verdict(_bad, "diverges", [("d-x", "looks-worse")], 1)
rc, out = _ladd(_cl, _bad)
rc2, out2 = (lambda o: (o.returncode, json.loads(o.stdout) if o.stdout.strip() else {}))(
    subprocess.run(VL + ["status", _cl], capture_output=True, text=True))
check("F10b shape: corrupt ledger → add AND status both error (no fabricated empty loop)",
      _structured(rc, out) and _structured(rc2, out2),
      "add rc=%s %s | status rc=%s %s" % (rc, out, rc2, out2))

_fl = os.path.join(_bd, "im-a-file")
open(_fl, "w").write("x")
rc, out = _ladd(_fl, _bad)
check("F10b shape: loop-dir is a file → structured error", _structured(rc, out), "rc=%s out=%s" % (rc, out))

# F10c · write atomicity — poison json.dump to crash mid-write: the pre-existing
# ledger must survive byte-identical (a de-atomized direct write corrupts it).
import importlib.util

_spec = importlib.util.spec_from_file_location("vis_ledger", os.path.join(ROOT, "lib/vis-ledger.py"))
_vlm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vlm)
_at = os.path.join(_bd, "ledger.json")
_orig_content = '{"loop": "orig", "rounds": []}'
open(_at, "w").write(_orig_content)
_orig_dump = _vlm.json.dump


def _poison(obj, f, **kw):
    f.write('{"torn')
    raise RuntimeError("simulated crash mid-write")


_vlm.json.dump = _poison
try:
    try:
        _vlm.write_atomic(_at, {"x": 1})
        _crashed = False
    except RuntimeError:
        _crashed = True
finally:
    _vlm.json.dump = _orig_dump
check("F10c atomic write: crash mid-dump leaves the ledger byte-identical",
      _crashed and open(_at).read() == _orig_content,
      "crashed=%s content=%r" % (_crashed, open(_at).read()[:40]))
shutil.rmtree(_bd, ignore_errors=True)

# F11 · asset-derivation verify — each derived rung is judged against a freshly
# synthesized best-achievable resample at its own size: a competent rung passes,
# a double-resampled (visibly soft) rung is flagged with a regeneration hint, and
# any flag makes the exit code nonzero (grep-able gate for scripts).
from PIL import ImageDraw

AV = [os.path.join(ROOT, ".venv/bin/python"), os.path.join(ROOT, "lib/asset-verify.py")]
_ad = tempfile.mkdtemp()
_im = Image.new("RGBA", (256, 256), (71, 112, 76, 255))
_dr = ImageDraw.Draw(_im)
_dr.ellipse([40, 40, 216, 216], outline=(38, 193, 208, 255), width=8)
_dr.ellipse([80, 80, 176, 176], outline=(241, 187, 52, 255), width=8)
_src = os.path.join(_ad, "src.png")
_im.save(_src)

_rgb = _im.convert("RGB").resize((32, 32), Image.LANCZOS)
_a = _im.getchannel("A").resize((32, 32), Image.LANCZOS)
_g = _rgb.convert("RGBA")
_g.putalpha(_a)
_g.save(os.path.join(_ad, "good-32.png"))
_im.convert("RGB").resize((12, 12), Image.LANCZOS).resize((32, 32), Image.LANCZOS) \
   .save(os.path.join(_ad, "bad-32.png"))
_im.save(os.path.join(_ad, "same.png"))

_out = subprocess.run(AV + [_src, os.path.join(_ad, "good-32.png"),
                            os.path.join(_ad, "bad-32.png"),
                            os.path.join(_ad, "same.png"), "--json"],
                      capture_output=True, text=True)
try:
    _av = json.loads(_out.stdout)
except Exception:
    _av = {"_raw": (_out.stdout + _out.stderr)[:200]}
_rungs = {os.path.basename(r.get("path", "")): r for r in _av.get("rungs", [])}
check("F11 asset-verify: best-achievable rung passes",
      _rungs.get("good-32.png", {}).get("verdict") == "ok", "av=%s" % _av)
check("F11 asset-verify: double-resampled rung flagged, fix proposed",
      _rungs.get("bad-32.png", {}).get("verdict") == "soft"
      and bool(_rungs.get("bad-32.png", {}).get("fix")), "rung=%s" % _rungs.get("bad-32.png"))
check("F11 asset-verify: identical copy passes; any flag → nonzero exit",
      _rungs.get("same.png", {}).get("verdict") == "ok" and _out.returncode != 0,
      "rc=%s same=%s" % (_out.returncode, _rungs.get("same.png")))
shutil.rmtree(_ad, ignore_errors=True)

fails = [c for c in CHECKS if not c[1]]
for name, ok, detail in CHECKS:
    tail = ("  [%s]" % detail) if (detail and not ok) else ""
    print("  %s %s%s" % ("ok  " if ok else "FAIL", name, tail))
if not HAVE_OCR:
    print("  note: mac-ocr absent — E1 text-lane assertions skipped")
print("%d/%d vis-compare assertions passed" % (len(CHECKS) - len(fails), len(CHECKS)))
sys.exit(1 if fails else 0)
