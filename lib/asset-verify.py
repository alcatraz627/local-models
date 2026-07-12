#!/usr/bin/env python3
"""Checks that every derived size rung of a source asset (icon sets, favicon
rungs, resized exports) still looks as good as its size allows — flagging rungs
a fresh resample would visibly beat.

    asset-verify.py <source> <derived...> [--json]

Judgment-free: each rung is compared not to the source but to a best-achievable
resample synthesized at the rung's own size (derived-size doctrine, docs/10 §10),
using the vis-compare extractors on alpha-composited appearance. Floors are the
battery-proven perceptual-identity class (F3b). Exit 0 = all rungs ok; 1 = at
least one flagged; 2 = structured input error (with a proposed fix).
"""
import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("vis_compare", os.path.join(HERE, "vis-compare.py"))
VC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(VC)
Image = VC.Image  # single PIL import path — same venv contract as vis-compare

# perceptual-identity floors (the F3b class) + an acuity floor: blur preserves
# cell means and gradient signs, so softness only shows in edge energy (E6 —
# measured 0.0 on a competent rung vs 43.8 on a double-resample, 82.8 on the
# real soft-icon case)
DHASH_MAX, GRID_MAX_PCT, PALETTE_MAX_DE, EDGE_MAX_PCT = 3, 5.0, 5.0, 10.0


def die(msg, fix):
    print(json.dumps({"ok": False, "error": msg, "fix": fix}))
    sys.exit(2)


def load_image(path, what):
    try:
        img = Image.open(path)
        img.load()  # PIL is lazy: without this the decode of a TRUNCATED file
        return img  # (interrupted build, disk-full write) escapes this guard and
    except Exception as e:  # tracebacks later inside flatten()
        die("%s unreadable as an image: %s" % (what, e),
            "check the path — %s must be a complete raster image PIL can open "
            "(a truncated/partial write fails here)" % path)


def flatten(img, size=None):
    """Composited appearance on white — compare what a user sees, not the
    under-alpha channel data (which legitimately differs between pipelines)."""
    rgba = img.convert("RGBA")
    if size:
        rgb = rgba.convert("RGB").resize(size, Image.LANCZOS)
        a = rgba.getchannel("A").resize(size, Image.LANCZOS)
        rgba = rgb.convert("RGBA")
        rgba.putalpha(a)
    base = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    return Image.alpha_composite(base, rgba).convert("RGB")


def main():
    ap = argparse.ArgumentParser(description="derived-asset rung verifier")
    ap.add_argument("source")
    ap.add_argument("derived", nargs="+")
    ap.add_argument("--json", action="store_true", help="machine output (always JSON on stdout; --json suppresses the human table)")
    args = ap.parse_args()

    src = load_image(args.source, "source")
    rungs, any_flag = [], False
    for path in args.derived:
        d = load_image(path, "derived rung")
        entry = {"path": path, "size": list(d.size)}
        sa, da = src.width / src.height, d.width / d.height
        if max(sa / da, da / sa) > 1.02:
            entry.update(verdict="aspect-mismatch",
                         fix="rung aspect %.3f vs source %.3f — a letterboxed or cropped "
                             "derivation needs its own review; this tool compares same-aspect rungs" % (da, sa))
            any_flag = True
            rungs.append(entry)
            continue
        best = flatten(src, size=d.size)
        got = flatten(d)
        h = VC.e4_hashes(best, got)
        g = VC.e5_grid(best, got, 8)
        c = VC.e3_palette(best, got)
        e = VC.e6_edges(best, got, 8)
        entry.update(dhash=h["dhash"], grid_delta_pct=g["hot_cell_pct"],
                     palette_delta_avg=c["avg_dE"], edge_delta_pct=e["hot_cell_pct"])
        ok = (h["dhash"] <= DHASH_MAX and g["hot_cell_pct"] < GRID_MAX_PCT
              and c["avg_dE"] < PALETTE_MAX_DE and e["hot_cell_pct"] < EDGE_MAX_PCT)
        entry["verdict"] = "ok" if ok else "soft"
        if not ok:
            any_flag = True
            entry["fix"] = ("regenerate: single-pass unpremultiplied LANCZOS from %s at %dx%d "
                            "(python: rgb+alpha resized separately, docs/10 §10)"
                            % (args.source, d.width, d.height))
        rungs.append(entry)

    out = {"ok": not any_flag, "source": args.source, "floors":
           {"dhash": DHASH_MAX, "grid_pct": GRID_MAX_PCT, "palette_dE": PALETTE_MAX_DE,
            "edge_pct": EDGE_MAX_PCT},
           "rungs": rungs}
    print(json.dumps(out, indent=1))
    if not args.json:
        for r in rungs:
            print("  %-4s %-40s %s" % (r["verdict"], os.path.basename(r["path"]),
                                       "dhash=%s grid=%.1f%% dE=%.1f" % (r.get("dhash"), r.get("grid_delta_pct", -1), r.get("palette_delta_avg", -1))
                                       if "dhash" in r else r.get("fix", "")), file=sys.stderr)
    sys.exit(1 if any_flag else 0)


if __name__ == "__main__":
    main()
