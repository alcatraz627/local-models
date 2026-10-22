#!/usr/bin/env python3
"""Count objects and find the odd one out by measuring pixels, with no model.

Local vision models guess at counts of many small shapes and at which of
several look-alikes differs. A script is exact at both, so `see count` and
`see odd` call this file. It says "ambiguous" instead of guessing.

    measure.py count IMG [--color NAME|#hex] [--min-area N] [--filled-only]
    measure.py odd IMG [--min-area N]

Prints one JSON object: {ok, job, answer, objects, confidence, ambiguous, why}.
Exit 0 on an answer (even an ambiguous one), 2 on bad usage, 12 on an unreadable image.
"""

import argparse
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

# Pixels this far (CIE76) from the background count as foreground.
FG_DELTA_E = 12.0
# A component covering this share of the frame is a panel, not an object.
PANEL_SHARE = 0.5
# Odd-one-out: how far the runner-up may trail the winner before we refuse to pick.
AMBIGUOUS_RATIO = 0.6
# Count: a blob this many times the median area is probably touching objects.
MERGED_AREA_X = 2.0
SHAPE_GRID = 16

# Canonical colour names. The values match the vision fixtures' palette.
NAMED = {
    "red": (220, 38, 38), "green": (22, 163, 74), "blue": (37, 99, 235),
    "yellow": (234, 179, 8), "orange": (234, 88, 12), "purple": (147, 51, 234),
    "gray": (128, 128, 128), "black": (0, 0, 0), "white": (255, 255, 255),
}
NAMED["grey"] = NAMED["gray"]
HEX_MATCH_DE = 25.0


class MeasureError(Exception):
    def __init__(self, code, message, exit_code):
        super().__init__(message)
        self.code, self.exit_code = code, exit_code


def to_lab(rgb):
    """sRGB (0-255, any leading shape, last axis 3) to CIE Lab, D65."""
    c = np.asarray(rgb, dtype=float) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = (lin @ m.T) / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


def delta_e(a, b):
    return np.linalg.norm(to_lab(a) - to_lab(b), axis=-1)


def load(path):
    try:
        im = Image.open(path)
        im.load()
    except (OSError, ValueError) as exc:
        raise MeasureError("img_unreadable", f"cannot read {path}: {exc}", 12)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        base = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(base, im)
    return np.asarray(im.convert("RGB"))


def dominant_color(pixels):
    """The most common colour among N x 3 pixels, binned so noise and JPEG fuzz do not split it."""
    bins = (pixels // 8).astype(np.int32)
    key = bins[:, 0] * 1024 + bins[:, 1] * 32 + bins[:, 2]
    vals, counts = np.unique(key, return_counts=True)
    top = vals[counts.argmax()]
    return pixels[key == top].mean(axis=0)


def border_pixels(arr):
    h, w = arr.shape[:2]
    t = max(1, min(h, w) // 100)
    ring = np.zeros((h, w), bool)
    ring[:t], ring[-t:], ring[:, :t], ring[:, -t:] = True, True, True, True
    return arr[ring]


def foreground(arr, region=None, bg=None):
    """Boolean foreground mask: pixels far from the background colour, inside region if given."""
    if bg is None:
        bg = dominant_color(border_pixels(arr) if region is None else arr[region])
    fg = delta_e(arr.astype(float), bg) > FG_DELTA_E
    if region is not None:
        fg &= region
    return fg, bg


def default_min_area(arr):
    h, w = arr.shape[:2]
    return max(6, int(round(2e-5 * h * w)))


def blobs(mask, min_area):
    """Connected components of a mask as (label image, [slice, area, filled_area])."""
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    out = []
    if n == 0:
        return lab, out
    areas = np.bincount(lab.ravel(), minlength=n + 1)
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        if sl is None or areas[i] < min_area:
            continue
        comp = lab[sl] == i
        out.append({"label": i, "slice": sl, "area": int(areas[i]),
                    "filled": int(ndimage.binary_fill_holes(comp).sum())})
    return lab, out


def segment(arr, min_area):
    """Find the objects. A frame-sized blob is treated as a panel and its inside is segmented instead."""
    fg, bg = foreground(arr)
    lab, found = blobs(fg, min_area)
    notes = []
    frame = arr.shape[0] * arr.shape[1]
    for _ in range(2):
        big = [b for b in found if b["area"] >= PANEL_SHARE * frame] if found else []
        if not big:
            break
        panel = lab == big[0]["label"]
        region = ndimage.binary_fill_holes(panel)
        fg2, bg2 = foreground(arr, region=region)
        lab2, found2 = blobs(fg2, min_area)
        if len(found2) < 2:
            break
        notes.append("a panel covered most of the frame, so objects were measured inside it")
        lab, found, fg = lab2, found2, fg2
    objs = []
    for b in found:
        sl, comp = b["slice"], lab[b["slice"]] == b["label"]
        px = arr[sl][comp].astype(float)
        mean = px.mean(axis=0)
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        objs.append({"bbox": [int(x0), int(y0), int(x1 - x0), int(y1 - y0)], "area": b["area"],
                     "fill": round(b["area"] / b["filled"], 3), "rgb": mean, "mask": comp})
    return objs, notes


def name_color(rgb):
    lab = to_lab(rgb)
    best = min(NAMED, key=lambda n: float(np.linalg.norm(lab - to_lab(NAMED[n]))))
    return "gray" if best == "grey" else best


def parse_color(spec):
    s = spec.strip().lower()
    if s.startswith("#") and len(s) in (4, 7):
        h = s[1:] if len(s) == 7 else "".join(ch * 2 for ch in s[1:])
        try:
            return ("hex", np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float))
        except ValueError:
            pass
    elif s in NAMED:
        return ("name", "gray" if s == "grey" else s)
    raise MeasureError("invalid_args", f"--color must be one of {', '.join(sorted(set(NAMED) - {'grey'}))} or #hex, got '{spec}'", 2)


def matches(obj, want):
    kind, val = want
    if kind == "name":
        return name_color(obj["rgb"]) == val
    return float(delta_e(obj["rgb"], val)) <= HEX_MATCH_DE


def reading_order(objs):
    """Row-major order: rows are bands of similar vertical centre, each read left to right."""
    if not objs:
        return []
    cy = lambda o: o["bbox"][1] + o["bbox"][3] / 2
    cx = lambda o: o["bbox"][0] + o["bbox"][2] / 2
    tol = 0.5 * float(np.median([o["bbox"][3] for o in objs]))
    rows, cur = [], []
    for o in sorted(objs, key=cy):
        if cur and cy(o) - cy(cur[0]) > tol:
            rows.append(cur)
            cur = []
        cur.append(o)
    rows.append(cur)
    return [o for r in rows for o in sorted(r, key=cx)]


MAX_LISTED = 60


def listed(objs):
    """Public rows for at most MAX_LISTED objects, so a busy image does not flood the output."""
    return [public(i, o) for i, o in enumerate(objs[:MAX_LISTED], 1)]


def public(i, o):
    return {"i": i, "bbox": o["bbox"], "area": o["area"], "color": name_color(o["rgb"]),
            "rgb": [int(round(v)) for v in o["rgb"]]}


def job_count(arr, color, min_area, filled_only):
    objs, notes = segment(arr, min_area)
    total = len(objs)
    if filled_only:
        objs = [o for o in objs if o["fill"] > 0.6]
        notes.append(f"dropped {total - len(objs)} hollow outline(s)")
    if color:
        want = parse_color(color)
        before = len(objs)
        objs = [o for o in objs if matches(o, want)]
        notes.append(f"kept {len(objs)} of {before} objects matching {color}")
    objs = reading_order(objs)
    n = len(objs)
    res = {"ok": True, "job": "count", "answer": n, "objects": listed(objs),
           "ambiguous": False, "confidence": 1.0}
    if n >= 3:
        med = float(np.median([o["area"] for o in objs]))
        merged = [o for o in objs if o["area"] > MERGED_AREA_X * med]
        if merged:
            hi = n - len(merged) + sum(max(2, int(round(o["area"] / med))) for o in merged)
            res.update(ambiguous=True, confidence=0.5, range=[n, hi])
            notes.append(f"{len(merged)} blob(s) are much larger than the median, so objects may touch or merge")
    why = f"{n} object(s) found by background-distance segmentation, min area {min_area}px"
    res["why"] = "; ".join([why] + notes)
    return res


def shape_vec(o):
    """The object's mask shrunk to a fixed grid, so rotation and shape changes show up."""
    im = Image.fromarray((o["mask"] * 255).astype(np.uint8)).resize((SHAPE_GRID, SHAPE_GRID), Image.BILINEAR)
    return np.asarray(im, dtype=float) / 255.0


def repeated_group(objs):
    """The set of similar-sized objects with the most total ink, so captions and specks are not compared with the items.

    Counting members would pick the numerous small captions over the few big items.
    """
    order = sorted(objs, key=lambda o: o["area"])
    groups, cur = [], [order[0]]
    for o in order[1:]:
        if o["area"] > 2.0 * cur[-1]["area"]:
            groups.append(cur)
            cur = []
        cur.append(o)
    groups.append(cur)
    return max(groups, key=lambda g: (len(g) >= 3, sum(o["area"] for o in g)))


def job_odd(arr, min_area):
    objs, notes = segment(arr, min_area)
    if not objs:
        return {"ok": True, "job": "odd", "answer": None, "objects": [], "ambiguous": True, "confidence": 0.0,
                "candidates": [], "why": "no objects found, so there is nothing to compare"}
    group = reading_order(repeated_group(objs))
    n = len(group)
    pub = listed(group)
    if len(objs) != n:
        notes.append(f"compared the {n} similar-sized objects and ignored {len(objs) - n} others")
        big = max(o["area"] for o in group)
        larger = sum(1 for o in objs if o["area"] > 2.0 * big)
        if larger:
            notes.append(f"{larger} larger blob(s) were not compared, and touching items can hide the real outlier there")
    if n < 3:
        return {"ok": True, "job": "odd", "answer": None, "objects": pub, "ambiguous": True, "confidence": 0.0,
                "candidates": list(range(1, n + 1)),
                "why": "; ".join([f"only {n} comparable object(s); an outlier needs at least 3"] + notes)}
    lab = np.array([to_lab(o["rgb"]) for o in group])
    area = np.array([o["area"] for o in group], float)
    aspect = np.log(np.array([o["bbox"][2] / o["bbox"][3] for o in group]))
    shapes = np.array([shape_vec(o) for o in group])
    med_shape = np.median(shapes, axis=0)
    med_lab, med_area, med_aspect = np.median(lab, axis=0), np.median(area), np.median(aspect)
    # Each term is scaled so 1.0 means "about as large as a person would just notice".
    parts = {
        "colour": np.linalg.norm(lab - med_lab, axis=1) / 2.0,
        "shape": np.abs(shapes - med_shape).sum(axis=(1, 2)) / max(med_shape.sum(), 1e-9) / 0.08,
        "area": np.abs(area - med_area) / med_area / 0.06,
        "aspect": np.abs(aspect - med_aspect) / 0.06,
    }
    score = np.sqrt(sum(v ** 2 for v in parts.values()))
    order = np.argsort(-score)
    top, runner = float(score[order[0]]), float(score[order[1]])
    ambiguous = top < 1.0 or runner >= AMBIGUOUS_RATIO * top
    margin = round(1 - runner / top, 3) if top > 0 else 0.0
    res = {"ok": True, "job": "odd", "objects": pub, "ambiguous": ambiguous, "confidence": margin if not ambiguous else 0.0,
           "margin": margin}
    if ambiguous:
        cands = [int(order[0]) + 1, int(order[1]) + 1]
        res.update(answer=None, candidates=cands)
        reason = ("no object differs noticeably" if top < 1.0 else
                  f"objects {cands[0]} and {cands[1]} both stand out (scores {top:.1f} and {runner:.1f})")
        res["why"] = "; ".join([f"ambiguous: {reason}"] + notes)
    else:
        i = int(order[0])
        what = max(parts, key=lambda k: parts[k][i])
        res.update(answer=i + 1, bbox=group[i]["bbox"])
        res["why"] = "; ".join([f"object {i + 1} of {n} differs most, mainly in {what} (score {top:.1f}, runner-up {runner:.1f})"] + notes)
    return res


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise MeasureError("invalid_args", message, 2)


def run(argv):
    p = _Parser(prog="measure.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="job", required=True, parser_class=_Parser)
    c = sub.add_parser("count")
    c.add_argument("image")
    c.add_argument("--color")
    c.add_argument("--min-area", type=int)
    c.add_argument("--filled-only", action="store_true")
    o = sub.add_parser("odd")
    o.add_argument("image")
    o.add_argument("--min-area", type=int)
    a = p.parse_args(argv)
    if a.min_area is not None and a.min_area < 1:
        raise MeasureError("invalid_args", "--min-area must be at least 1", 2)
    arr = load(a.image)
    min_area = a.min_area or default_min_area(arr)
    if a.job == "count":
        return job_count(arr, a.color, min_area, a.filled_only)
    return job_odd(arr, min_area)


def main():
    try:
        res = run(sys.argv[1:])
        code = 0
    except MeasureError as exc:
        res, code = {"ok": False, "code": exc.code, "message": str(exc)}, exc.exit_code
    except Exception as exc:  # fail closed: a structured error, never a traceback
        res, code = {"ok": False, "code": "measure_failed", "message": f"{type(exc).__name__}: {exc}"}, 12
    print(json.dumps(res, ensure_ascii=False))
    sys.exit(code)


if __name__ == "__main__":
    main()
