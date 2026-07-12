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
# alpha is part of the color: dropping it once reported transparent → opaque black
# as dE 0.0 "negligible" — a false negative, worse than a fabricated divergence
_RGB = re.compile(r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s/]+([\d.%]+))?")
_ZERO = re.compile(r"^0(px|em|rem|%)?$")
# strings the browser reports differently for identical rendering
_EQUIV = {"letter-spacing": {"normal": "0px"}, "line-height": {"normal": None}}


def _zeroish(v):
    return all(_ZERO.match(t) for t in (v or "0px").split())


def unseen(sa, sb):
    """Is this element invisible on BOTH sides? Then nothing about it can be a
    divergence — a change nobody can see is not a change."""
    return all((s.get("opacity") or "1").strip() in ("0", "0.0", "0%") for s in (sa, sb))


def invisible(prop, sa, sb):
    """A computed property the user cannot possibly see is not a divergence — the
    fabricated-difference class the extractors exist to prevent. Each case here was
    found by running a real browser, not by imagination:
      border-color  · follows currentColor, so a text recolor drags a phantom
                      border diff along even at border-width: 0
      box-shadow    · same, when the shadow has no offset/blur/spread to render
    """
    def no_border(s):
        return _zeroish(s.get("border-width")) or (s.get("border-style") or "none") in ("none", "hidden")

    if prop == "border-color":
        return no_border(sa) and no_border(sb)
    if prop == "box-shadow":
        def no_shadow(s):
            geo = re.findall(r"(-?[\d.]+px)", s.get("box-shadow") or "")
            return bool(geo) and all(_ZERO.match(g) for g in geo)
        return no_shadow(sa) and no_shadow(sb)
    return False


def equivalent(prop, va, vb):
    """Two strings, one rendering: `letter-spacing: normal` and `0px` are the same
    type — a CSS reset must not fabricate a typography divergence."""
    table = _EQUIV.get(prop)
    if not table:
        return False
    return table.get(va, va) == table.get(vb, vb)


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
    """(r, g, b, a) with alpha 0-1, or None when the string isn't an rgb()/rgba().
    Alpha matters: a transparent→opaque change is maximally visible."""
    if not isinstance(v, str):
        return None
    m = _RGB.search(v)
    if not m:
        return None
    r, g, b = (int(float(x)) for x in m.groups()[:3])
    raw = m.group(4)
    a = 1.0
    if raw is not None:
        a = float(raw.rstrip("%")) / 100 if raw.endswith("%") else float(raw)
    return (r, g, b, a)


def color_delta(ca, cb):
    """ΔE over the colors AS SEEN: composite each onto white by its alpha first,
    so alpha changes register instead of being silently dropped."""
    def on_white(c):
        r, g, b, a = c
        return tuple(round(x * a + 255 * (1 - a)) for x in (r, g, b))
    return VC.delta_e(on_white(ca), on_white(cb))


def index(cap, side):
    """selector → element, refusing to lose one silently. A dict comprehension
    would let a duplicate id (a real authoring mistake) overwrite its twin and
    quietly shrink the comparison; a dropped element is a lie of omission."""
    out = {}
    for e in cap["elements"]:
        if not isinstance(e, dict):
            continue
        sel = e.get("selector")
        if not isinstance(sel, str) or not sel:
            die("capture %s has an element with no selector" % side,
                "re-capture with lib/e8-extract.js — every element needs a stable "
                "selector (an id or a data-e8 attribute)")
        if sel in out:
            die("capture %s has duplicate selector %s — one element would be "
                "silently dropped from the comparison" % (side, sel),
                "ids must be unique on the page; fix the duplicate %s or mark the "
                "elements with distinct data-e8 values" % sel)
        styles = e.get("styles")
        if styles is not None and not isinstance(styles, dict):
            die("capture %s: element %s has a non-object `styles`" % (side, sel),
                "re-capture with lib/e8-extract.js — styles is a {prop: value} object")
        out[sel] = e
    return out


def main():
    ap = argparse.ArgumentParser(description="E8 · computed-style diff for live web surfaces")
    ap.add_argument("capture_a")
    ap.add_argument("capture_b")
    ap.add_argument("--json", action="store_true", help="accepted for symmetry; output is always JSON")
    args = ap.parse_args()

    A, B = load(args.capture_a, "A"), load(args.capture_b, "B")
    a_els, b_els = index(A, "A"), index(B, "B")

    diffs = []
    for sel in sorted(set(a_els) & set(b_els)):
        sa = a_els[sel].get("styles") or {}
        sb = b_els[sel].get("styles") or {}
        if unseen(sa, sb):   # invisible element: nothing about it is a divergence
            continue
        for prop in sorted(set(sa) & set(sb)):
            va, vb = sa[prop], sb[prop]
            if va == vb or equivalent(prop, va, vb) or invisible(prop, sa, sb):
                continue
            d = {"selector": sel, "prop": prop, "a": va, "b": vb}
            if prop in COLOR_PROPS:
                ca, cb = parse_rgb(va), parse_rgb(vb)
                if ca and cb:
                    d["dE"] = round(color_delta(ca, cb), 1)
                    d["word"] = VC.de_word(d["dE"])
            diffs.append(d)

    # Coverage is honest or the lane lies by omission: only MARKED elements
    # (id / data-e8) are captured, so an unmarked element's divergence is
    # invisible — say how many were skipped instead of looking complete.
    dom_a, dom_b = A.get("dom_elements"), B.get("dom_elements")
    captured = len(set(a_els) & set(b_els))
    only_a, only_b = sorted(set(a_els) - set(b_els)), sorted(set(b_els) - set(a_els))
    coverage = {"captured": captured}
    if isinstance(dom_a, int) and isinstance(dom_b, int):
        dom = max(dom_a, dom_b)
        coverage["dom_elements"] = dom
        marked = len(set(a_els) | set(b_els))
        if dom < marked:
            # captured elements are a subset of the DOM: this input contradicts
            # itself, and clamping it to 0 would report a clean "fully covered"
            coverage["uncaptured"] = None
            coverage["warning"] = ("dom_elements (%d) < marked elements (%d) — the "
                                   "capture is inconsistent; coverage is unknown" % (dom, marked))
        else:
            coverage["uncaptured"] = dom - marked   # marked-but-unpaired is NOT unmarked
            notes = []
            if coverage["uncaptured"]:
                notes.append("%d DOM element(s) carry no id/data-e8 and were never "
                             "captured — mark them to include them" % coverage["uncaptured"])
            if only_a or only_b:
                notes.append("%d marked element(s) exist on only one side (see "
                             "only_in_a/only_in_b) — captured, but not comparable"
                             % (len(only_a) + len(only_b)))
            coverage["note"] = "; ".join(notes) or None

    out = {"ok": True, "elements_compared": captured, "coverage": coverage,
           "only_in_a": only_a, "only_in_b": only_b, "diffs": diffs}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
