#!/usr/bin/env python3
"""E8 — the live-web evidence lane: diffs two pages' computed styles so the judge
reads EXACT values (this hex, this padding) instead of estimating them from pixels.

    e8-dom.py <capture-a.json> <capture-b.json> [--json]

Captures come from any browser driver via lib/e8-extract.js (Playwright/CDP/CI) —
this tool owns the diff, not the browser, exactly as vis-compare.py owns the text
diff while bin/see owns the OCR. Color props carry a measured CIE76 dE (same
converter as E3, so a number here means what it means there). Lane docs: docs/10 §10.
"""
import argparse
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("vis_compare", os.path.join(HERE, "vis-compare.py"))
VC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(VC)

COLOR_PROPS = {"color", "background-color", "border-color"}
_RGB = re.compile(r"rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)")
_ZERO = re.compile(r"^0(px|em|rem|%)?$")


def invisible(prop, sa, sb):
    """A computed property the user cannot possibly see is not a divergence.
    The live case (2026-07-13): border-color follows `currentColor`, so recoloring
    text drags a phantom border diff along even when border-width is 0 — the exact
    fabricated-difference class the extractors exist to prevent."""
    if prop != "border-color":
        return False
    def no_border(s):
        return (all(_ZERO.match(t) for t in (s.get("border-width") or "0px").split())
                or (s.get("border-style") or "none") == "none")
    return no_border(sa) and no_border(sb)


def die(msg, fix):
    print(json.dumps({"ok": False, "error": msg, "fix": fix}))
    sys.exit(2)


def load(path, side):
    try:
        cap = json.load(open(path))
    except OSError as e:
        die("capture %s unreadable: %s" % (side, e),
            "produce it: run lib/e8-extract.js in your browser driver on the %s page "
            "and save the returned object as JSON" % side)
    except ValueError as e:
        die("capture %s is not valid JSON: %s" % (side, e),
            "re-capture — a truncated write is the usual cause")
    if not isinstance(cap, dict) or not isinstance(cap.get("elements"), list):
        die("capture %s has no elements[] — wrong shape" % side,
            "captures must come from lib/e8-extract.js (an object with elements[])")
    return cap


def parse_rgb(v):
    m = _RGB.search(v or "")
    return tuple(int(g) for g in m.groups()) if m else None


def main():
    ap = argparse.ArgumentParser(description="E8 · computed-style diff for live web surfaces")
    ap.add_argument("capture_a")
    ap.add_argument("capture_b")
    ap.add_argument("--json", action="store_true", help="accepted for symmetry; output is always JSON")
    args = ap.parse_args()

    A, B = load(args.capture_a, "A"), load(args.capture_b, "B")
    a_els = {e.get("selector"): e for e in A["elements"] if isinstance(e, dict)}
    b_els = {e.get("selector"): e for e in B["elements"] if isinstance(e, dict)}

    diffs = []
    for sel in sorted(set(a_els) & set(b_els)):
        sa = a_els[sel].get("styles", {}) or {}
        sb = b_els[sel].get("styles", {}) or {}
        for prop in sorted(set(sa) & set(sb)):
            va, vb = sa[prop], sb[prop]
            if va == vb or invisible(prop, sa, sb):
                continue
            d = {"selector": sel, "prop": prop, "a": va, "b": vb}
            if prop in COLOR_PROPS:
                ca, cb = parse_rgb(va), parse_rgb(vb)
                if ca and cb:
                    d["dE"] = round(VC.delta_e(ca, cb), 1)
                    d["word"] = VC.de_word(d["dE"])
            diffs.append(d)

    # Coverage is honest or the lane lies by omission: only MARKED elements
    # (id / data-e8) are captured, so an unmarked element's divergence is
    # invisible — say how many were skipped instead of looking complete.
    dom_a, dom_b = A.get("dom_elements"), B.get("dom_elements")
    captured = len(set(a_els) & set(b_els))
    coverage = {"captured": captured}
    if isinstance(dom_a, int) and isinstance(dom_b, int):
        coverage["dom_elements"] = max(dom_a, dom_b)
        coverage["uncaptured"] = max(0, coverage["dom_elements"] - captured)
        coverage["note"] = ("only elements marked with id/data-e8 are compared; "
                            "%d DOM element(s) were not — mark them to include them"
                            % coverage["uncaptured"]) if coverage["uncaptured"] else None

    out = {"ok": True, "elements_compared": captured, "coverage": coverage,
           "only_in_a": sorted(set(a_els) - set(b_els)),
           "only_in_b": sorted(set(b_els) - set(a_els)),
           "diffs": diffs}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
