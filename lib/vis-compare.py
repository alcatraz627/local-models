#!/usr/bin/env python3
"""Visual-compare evidence extractors — the deterministic, $0, fabrication-proof
layer (L1) of the visual-compare capability.

This is the "scripts measure" half of the week's doctrine: every number in a
compare report traces to a function here; no model estimates a value. The judge
(a gcc skill, native vision) reads this pack as trusted fact and is barred from
disputing it — so an extractor that invents a difference is worse than none,
which is why the identical-pair guard (F3) is the first thing the battery checks.

Pure Python + PIL only (PIL ships in the project .venv via mflux). No numpy, no
opencv — dHash/aHash plus grid metrics deliberately replace DCT-pHash and SSIM to
stay dependency-free while covering the same decisions at this scale.

Run standalone (extractors only, size-based modality):
    .venv/bin/python lib/vis-compare.py A.png B.png --json
Fed by bin/see (real OCR word counts + text diff):
    .venv/bin/python lib/vis-compare.py A B --words-a 12 --words-b 12 \
        --text-diff '{...}' --contact out/contact.png --json

Output: evidence-pack JSON on stdout (schema: docs/10 §5).
"""
import argparse
import hashlib
import json
import os
import sys
import time
import warnings

from PIL import Image, ImageFilter

# getdata() is deprecated in Pillow 14 but its replacement isn't in every
# installed version; the calls here are read-only and correct. Silence the
# noise so it can't leak into stderr a caller (bin/see) parses.
warnings.filterwarnings("ignore", category=DeprecationWarning)


# ── color science: sRGB → CIE-Lab, ΔE76 (pure python, ~20 lines) ──────────────
def _srgb_to_lab(rgb):
    """One sRGB triple (0-255) to CIE-Lab. ΔE is measured in this space because
    euclidean distance in Lab tracks perceived color difference far better than
    in RGB — an 8-unit ΔE reads as 'noticeable' to a human regardless of hue."""
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(v) for v in rgb)
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = (r * 0.2126 + g * 0.7152 + b * 0.0722)
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def delta_e(rgb1, rgb2):
    """CIE76 ΔE between two sRGB triples."""
    l1, a1, b1 = _srgb_to_lab(rgb1)
    l2, a2, b2 = _srgb_to_lab(rgb2)
    return ((l1 - l2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2) ** 0.5


def de_word(de):
    """The plain-word bucket the report shows next to a raw ΔE, so a consumer
    who can't judge '9.1' still gets 'noticeable'."""
    return ("negligible" if de < 2 else "subtle" if de < 8
            else "noticeable" if de < 20 else "different")


# ── E4 · perceptual hashes (dHash + aHash), pure PIL ──────────────────────────
def _dhash(img, size=8):
    """dHash: each bit is 'is this pixel brighter than the one to its right'.
    Robust to scale/compression, sensitive to structure — the icon case's
    cheapest silhouette signal."""
    g = img.convert("L").resize((size + 1, size), Image.LANCZOS)
    px = list(g.getdata())
    bits = 0
    for row in range(size):
        for col in range(size):
            i = row * (size + 1) + col
            bits = (bits << 1) | (1 if px[i] > px[i + 1] else 0)
    return bits


def _ahash(img, size=8):
    """aHash: each bit is 'is this pixel above the image mean'. Cheap global
    brightness fingerprint; complements dHash's structural read."""
    g = img.convert("L").resize((size, size), Image.LANCZOS)
    px = list(g.getdata())
    avg = sum(px) / len(px)
    bits = 0
    for p in px:
        bits = (bits << 1) | (1 if p > avg else 0)
    return bits


def _hamming(a, b):
    return bin(a ^ b).count("1")


def e4_hashes(a, b):
    dh = _hamming(_dhash(a), _dhash(b))
    ah = _hamming(_ahash(a), _ahash(b))
    combined = dh + ah
    sim = ("near-identical" if combined <= 4 else "close" if combined <= 14
           else "related" if combined <= 28 else "different")
    return {"dhash": dh, "ahash": ah, "similarity": sim}


# ── E5 · grid-ΔE heatmap ──────────────────────────────────────────────────────
def _cell_means(img, n):
    """Downsample to n×n where each output pixel is the AREA MEAN of its cell
    (BOX filter), giving one representative color per grid cell."""
    small = img.convert("RGB").resize((n, n), Image.BOX)
    return list(small.getdata())  # row-major, len n*n


def e5_grid(a, b, n, topk=6, hot_de=8.0):
    ca, cb = _cell_means(a, n), _cell_means(b, n)
    cells = []
    hot = 0
    for i, (pa, pb) in enumerate(zip(ca, cb)):
        de = delta_e(pa, pb)
        if de >= hot_de:
            hot += 1
        cells.append(((i // n, i % n), de))
    cells.sort(key=lambda c: c[1], reverse=True)
    top = [{"cell": list(rc), "dE": round(de, 1)} for rc, de in cells[:topk]]
    hot_pct = round(100.0 * hot / (n * n), 1)
    return {"n": n, "top_cells": top, "hot_cell_pct": hot_pct,
            "mean_dE": round(sum(de for _, de in cells) / len(cells), 1)}


def _ascii_heat(a, b, n=12, hot_de=8.0):
    """A compact heatmap for the prose report — five density levels so a human
    scanning text output sees WHERE divergence clusters without opening images."""
    ca, cb = _cell_means(a, n), _cell_means(b, n)
    ramp = " .:+*#"
    rows = []
    for r in range(n):
        line = ""
        for c in range(n):
            de = delta_e(ca[r * n + c], cb[r * n + c])
            lvl = min(len(ramp) - 1, int(de / (hot_de * 2) * (len(ramp) - 1)))
            line += ramp[lvl]
        rows.append(line)
    return "\n".join(rows)


# ── E6 · edge/shape grid (the silhouette lane) ────────────────────────────────
def _edge_density(img, n):
    """Per-cell mean edge intensity after PIL FIND_EDGES. Catches stroke-weight
    and corner-radius character even when colors match — the icon divergences
    E3/E5 miss. Reports THAT and WHERE shape changed, never WHAT it became
    (that description is the judge's, who can see)."""
    edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
    small = edges.resize((n, n), Image.BOX)
    return [p / 255.0 for p in small.getdata()]


def e6_edges(a, b, n, topk=6, hot_delta=0.03):
    da, db = _edge_density(a, n), _edge_density(b, n)
    cells = []
    hot = 0
    for i, (pa, pb) in enumerate(zip(da, db)):
        d = abs(pa - pb)
        if d >= hot_delta:
            hot += 1
        cells.append(((i // n, i % n), pa, pb, d))
    cells.sort(key=lambda c: c[3], reverse=True)
    top = [{"cell": list(rc), "density_a": round(pa, 3),
            "density_b": round(pb, 3), "delta": round(d, 3)}
           for rc, pa, pb, d in cells[:topk]]
    return {"n": n, "top_cells": top,
            "hot_cell_pct": round(100.0 * hot / (n * n), 1)}


# ── E3 · palette + region color ───────────────────────────────────────────────
def _palette(img, k=6):
    """k dominant colors via median-cut (deterministic), largest first."""
    q = img.convert("RGB").quantize(colors=k, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()
    counts = sorted(q.getcolors() or [], reverse=True)  # (count, idx)
    total = sum(c for c, _ in counts) or 1
    out = []
    for count, idx in counts:
        r, g, bl = pal[idx * 3:idx * 3 + 3]
        out.append({"hex": "#%02x%02x%02x" % (r, g, bl), "rgb": [r, g, bl],
                    "frac": round(count / total, 3)})
    return out


def e3_palette(a, b, k=6):
    pa, pb = _palette(a, k), _palette(b, k)
    used = set()
    pairs, unmatched_a = [], []
    for ca in pa:
        best, bidx = None, -1
        for j, cb in enumerate(pb):
            if j in used:
                continue
            de = delta_e(ca["rgb"], cb["rgb"])
            if best is None or de < best:
                best, bidx = de, j
        if bidx >= 0:
            used.add(bidx)
            pairs.append({"a": ca["hex"], "b": pb[bidx]["hex"],
                          "dE": round(best, 1), "word": de_word(best)})
        else:
            unmatched_a.append(ca["hex"])
    unmatched_b = [pb[j]["hex"] for j in range(len(pb)) if j not in used]
    avg = round(sum(p["dE"] for p in pairs) / len(pairs), 1) if pairs else 0.0
    return {"palette_pairs": pairs, "unmatched_a": unmatched_a,
            "unmatched_b": unmatched_b, "avg_dE": avg}


# ── E1 · text + position diff (from mac-ocr jsonl, fed by bin/see) ────────────
def _load_ocr(path):
    """Parse a mac-ocr `--format jsonl` file into {lowered_text: {text, pos}}.
    mac-ocr emits one JSON object with an `observations` array; each carries the
    text and a normalized top-left boundingBox. The 3×3 pos label matches the
    grid `see --ocr` already computes, so labels stay consistent across the tool."""
    try:
        obs = json.load(open(path)).get("observations", [])
    except Exception:
        return {}, 0
    out, words = {}, 0
    for o in obs:
        t = " ".join(o.get("text", "").split())
        if not t:
            continue
        words += len(t.split())
        bb = o.get("boundingBox", {})
        cx = bb.get("x", 0) + bb.get("width", 0) / 2
        cy = bb.get("y", 0) + bb.get("height", 0) / 2
        row = "top" if cy < 0.333 else ("middle" if cy < 0.667 else "bottom")
        col = "left" if cx < 0.333 else ("center" if cx < 0.667 else "right")
        pos = "center" if (row == "middle" and col == "center") else row + "-" + col
        out.setdefault(t.lower(), {"text": t, "pos": set()})["pos"].add(pos)
    return out, words


def e1_text_diff(a_jsonl, b_jsonl):
    """REMOVED/ADDED/MOVED between two OCR reads, plus a human summary string
    (for the VLM prompt) and each side's word count (for the modality probe)."""
    A, wa = _load_ocr(a_jsonl)
    B, wb = _load_ocr(b_jsonl)
    removed = [A[k]["text"] for k in A if k not in B]
    added = [B[k]["text"] for k in B if k not in A]
    moved = [{"text": A[k]["text"], "from": sorted(A[k]["pos"]), "to": sorted(B[k]["pos"])}
             for k in A if k in B and A[k]["pos"] != B[k]["pos"]]
    lines = []
    if removed:
        lines.append("REMOVED (in A only): " + " | ".join('"%s"' % t for t in removed[:25]))
    if added:
        lines.append("ADDED (in B only): " + " | ".join('"%s"' % t for t in added[:25]))
    if moved:
        lines.append("MOVED: " + " | ".join('"%s" %s -> %s'
                     % (m["text"], ",".join(m["from"]), ",".join(m["to"])) for m in moved[:25]))
    if not lines:
        lines.append("(no text-layer differences detected)")
    return ({"removed": removed, "added": added, "moved": moved},
            "\n".join(lines), wa, wb)


# ── E0 · normalize + modality probe + comparability gate ──────────────────────
def modality(a, b, words_a, words_b):
    """Which extractors apply. texty needs the text lanes (E1/E2); iconlike
    skips them silently (recorded in the pack so the judge knows what evidence
    exists). Word counts come from OCR (bin/see); size is the fallback signal."""
    min_dim = min(a.width, a.height, b.width, b.height)
    if words_a is None or words_b is None:
        # standalone / no-OCR: infer from size alone
        return "iconlike" if min_dim <= 256 else "mixed"
    if words_a >= 5 and words_b >= 5:
        return "texty"
    if min_dim <= 256 or (words_a <= 2 and words_b <= 2):
        return "iconlike"
    return "mixed"


def comparability(a, b, dhash_dist):
    """poor when the pair is not meaningfully comparable — the judge leads with
    this instead of manufacturing a comparison. Aspect mismatch >2× or a dHash
    beyond the sanity ceiling both trip it."""
    ara, arb = a.width / a.height, b.width / b.height
    aspect_ratio = max(ara / arb, arb / ara)
    if aspect_ratio > 2.0:
        return "poor", "aspect ratios differ %.1f× (%dx%d vs %dx%d)" % (
            aspect_ratio, a.width, a.height, b.width, b.height)
    if dhash_dist >= 56:  # of 64 bits — essentially unrelated structure
        return "poor", "perceptual hash distance %d/64 — structurally unrelated" % dhash_dist
    return "good", None


# ── pack assembly ─────────────────────────────────────────────────────────────
ALL_EXTRACTORS = ["E3", "E4", "E5", "E6"]


def _nudges(pack):
    """The `next:` block — the tool telling the controlling agent when a rerun
    would help, each an exact paste-ready command (agent-first-tools: errors and
    hints propose the fix). Empty when nothing is worth rerunning."""
    out = []
    m, s = pack["meta"], pack["scores"]
    a, b = m["a"], m["b"]
    if m["comparable"] == "poor":
        out.append({"reason": "pair not comparable (%s)" % (m.get("comparable_why") or "see meta"),
                    "cmd": "see diff <cropped-A> <cropped-B>  # crop to a shared region first"})
    if s.get("grid_delta_pct", 0) > 60:
        out.append({"reason": "grid heatmap saturated (%.0f%% cells hot) — refine to localize"
                    % s["grid_delta_pct"],
                    "cmd": "see diff %s %s --grid 32" % (a, b)})
    if m["modality"] == "texty" and pack.get("text_diff") and \
       not (pack["text_diff"]["removed"] or pack["text_diff"]["added"] or pack["text_diff"]["moved"]):
        # texty pair but E1 empty can mean OCR under-read (low contrast, small type)
        if s.get("grid_delta_pct", 0) > 5:
            out.append({"reason": "texty pair but text diff empty while pixels differ — OCR may have under-read",
                        "cmd": "see diff %s %s --only E5,E6  # shape/color still differ; recheck text by eye" % (a, b)})
    if s.get("dhash", 0) <= 6 and s.get("grid_delta_pct", 0) > 30:
        out.append({"reason": "structure close but color/region diverges — likely a theme or palette shift",
                    "cmd": "see diff %s %s --only E3  # inspect the palette pairs" % (a, b)})
    return out


def build_pack(a_path, b_path, grid=None, only=None,
               ocr_a=None, ocr_b=None, contact_path=None, force_modality=None):
    t0 = time.time()
    failures = []
    a = Image.open(a_path).convert("RGB")
    b = Image.open(b_path).convert("RGB")

    # E1 text diff + word counts, only when bin/see fed OCR jsonl for both sides
    text_diff, text_summary, words_a, words_b = None, None, None, None
    if ocr_a and ocr_b:
        text_diff, text_summary, words_a, words_b = e1_text_diff(ocr_a, ocr_b)

    mod = force_modality or modality(a, b, words_a, words_b)
    # grid resolution adapts to modality (icons want a finer relative grid);
    # --grid overrides. Clamp to the documented 4–64 window.
    n = grid if grid else (8 if mod == "iconlike" else 16)
    n = max(4, min(64, n))

    run = set(only) if only else set(ALL_EXTRACTORS)
    scores, color, grid_heat, edge_shape = {}, {}, {}, {}

    # E4 first — its dHash feeds the comparability gate.
    dhash_dist = 0
    if "E4" in run:
        h = e4_hashes(a, b)
        dhash_dist = h["dhash"]
        scores.update(h)
    else:
        dhash_dist = e4_hashes(a, b)["dhash"]  # gate still needs it, cheaply

    comp, comp_why = comparability(a, b, dhash_dist)

    if "E5" in run:
        g = e5_grid(a, b, n)
        grid_heat = g
        scores["grid_delta_pct"] = g["hot_cell_pct"]
    if "E3" in run:
        c = e3_palette(a, b)
        color = c
        scores["palette_delta_avg"] = c["avg_dE"]
    if "E6" in run:
        edge_shape = e6_edges(a, b, n)

    # modality-driven silent skips (recorded, not run). E1 runs only when texty
    # AND OCR was fed; E2 (spacing deltas) is a texty-only lane, not yet built.
    skipped = []
    if not (mod == "texty" and text_diff is not None):
        skipped.append("E1")
    skipped.append("E2")
    skipped += [e for e in ALL_EXTRACTORS if e not in run]

    # contact sheet — A | B | ΔE-heat tint (best-effort; a failure is soft)
    if contact_path:
        try:
            contact_sheet(a, b, n, contact_path)
        except Exception as e:  # noqa: BLE001 — soft failure, pack still ships
            failures.append({"stage": "contact", "code": "contact_failed",
                             "retriable": False, "fix": str(e)[:120]})

    pack = {
        "meta": {"a": a_path, "b": b_path, "normalized": [a.width, a.height],
                 "modality": mod, "comparable": comp,
                 "comparable_why": comp_why, "grid_n": n,
                 "skipped_extractors": sorted(set(skipped))},
        "scores": scores,
    }
    if text_diff is not None:
        pack["text_diff"] = text_diff
        pack["text_summary"] = text_summary
    if color:
        pack["color"] = color
    if grid_heat:
        pack["grid_heat"] = grid_heat
        pack["heatmap_ascii"] = _ascii_heat(a, b, min(16, max(8, n)))
    if edge_shape:
        pack["edge_shape"] = edge_shape

    pack["cost"] = {"wall_ms": int((time.time() - t0) * 1000),
                    "extractors_ms": int((time.time() - t0) * 1000),
                    "model_calls": []}
    pack["failures"] = failures
    pack["params_hash"] = _params_hash(a_path, b_path, n, sorted(run))
    pack["next"] = _nudges(pack)
    return pack


def contact_sheet(a, b, n, out_path, pad=12):
    """A | B | ΔE-heat side-by-side sheet. For human eyes AND the single
    attachment the native-vision judge reads. The heat panel tints B by per-cell
    ΔE (red = diverges), upsampled from the grid so structure stays legible."""
    h = max(a.height, b.height)
    def fit(im):
        if im.height != h:
            im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
        return im
    fa, fb = fit(a), fit(b)
    # heat panel: per-cell ΔE → red tint over a dimmed B, box-upsampled to fb size
    ca, cb = _cell_means(a, n), _cell_means(b, n)
    heat = Image.new("RGB", (n, n))
    hp = []
    for pa, pb in zip(ca, cb):
        de = min(1.0, delta_e(pa, pb) / 30.0)
        hp.append((int(30 + 225 * de), int(30 * (1 - de)), int(40 * (1 - de))))
    heat.putdata(hp)
    heat = heat.resize(fb.size, Image.BOX)
    tint = Image.blend(fb.point(lambda p: int(p * 0.45)), heat, 0.65)
    w = fa.width + fb.width + tint.width + pad * 4
    sheet = Image.new("RGB", (w, h + pad * 2), (245, 245, 247))
    x = pad
    for im in (fa, fb, tint):
        sheet.paste(im, (x, pad))
        x += im.width + pad
    sheet.save(out_path)


def _params_hash(a_path, b_path, n, run):
    """Content-addressed key for the pack cache: reruns with identical inputs
    and params return the cached pack; a changed --grid/--only busts only what
    changed. Hashes file BYTES so a re-saved image with the same path re-runs."""
    h = hashlib.sha256()
    for p in (a_path, b_path):
        try:
            with open(p, "rb") as f:
                h.update(hashlib.sha256(f.read()).digest())
        except OSError:
            h.update(b"missing")
    h.update(("|%d|%s" % (n, ",".join(run))).encode())
    return h.hexdigest()[:16]


def _ab_hash(a_path, b_path):
    """Cache key for a pair — the two files' content, independent of params, so a
    slice rerun can find the prior full pack to diff against."""
    h = hashlib.sha256()
    for p in (a_path, b_path):
        try:
            with open(p, "rb") as f:
                h.update(hashlib.sha256(f.read()).digest())
        except OSError:
            h.update(b"missing")
    return h.hexdigest()[:16]


def _slice_summary(pack, key):
    """The delta-relevant fields for one extractor — what a rerun compares."""
    s = pack.get("scores", {})
    if key == "E4":
        return {"dhash": s.get("dhash"), "ahash": s.get("ahash"), "similarity": s.get("similarity")}
    if key == "E5":
        g = pack.get("grid_heat", {})
        return {"grid_delta_pct": s.get("grid_delta_pct"), "mean_dE": g.get("mean_dE"),
                "grid_n": g.get("n"), "top_cells": [c["cell"] for c in g.get("top_cells", [])[:3]]}
    if key == "E3":
        return {"palette_delta_avg": s.get("palette_delta_avg")}
    if key == "E6":
        e = pack.get("edge_shape", {})
        return {"hot_cell_pct": e.get("hot_cell_pct"), "grid_n": e.get("n"),
                "top_cells": [c["cell"] for c in e.get("top_cells", [])[:3]]}
    return {}


def _merge_rerun(old, new, only):
    """Patch the cached full pack with a rerun's fresh values for the rerun
    extractors only, so the cache stays current without a full recompute."""
    merged = json.loads(json.dumps(old))
    for k in ("dhash", "ahash", "similarity", "grid_delta_pct", "palette_delta_avg"):
        if k in new.get("scores", {}):
            merged.setdefault("scores", {})[k] = new["scores"][k]
    for field in ("grid_heat", "edge_shape", "color"):
        if field in new:
            merged[field] = new[field]
    merged["params_hash"] = new["params_hash"]
    return merged


def main():
    ap = argparse.ArgumentParser(description="visual-compare evidence extractors")
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--grid", type=int, default=None, help="grid N (4–64)")
    ap.add_argument("--only", default=None,
                    help="comma list of extractors to run (E3,E4,E5,E6)")
    ap.add_argument("--ocr-a", default=None, help="mac-ocr jsonl for A (enables E1 + modality)")
    ap.add_argument("--ocr-b", default=None, help="mac-ocr jsonl for B")
    ap.add_argument("--contact", default=None, help="write contact sheet here")
    ap.add_argument("--cache-dir", default=None,
                    help="content-addressed pack cache — enables --only delta reruns")
    ap.add_argument("--force-modality", default=None, choices=["iconlike", "texty", "mixed"],
                    help="override the modality probe (e.g. --only an extractor it skipped)")
    ap.add_argument("--json", action="store_true", help="(default) emit JSON")
    args = ap.parse_args()

    # hard block: --grid must be in the documented window (reject early, explain)
    if args.grid is not None and not (4 <= args.grid <= 64):
        print(json.dumps({"error": "grid %d out of range — must be 4–64" % args.grid}),
              file=sys.stderr)
        return 2
    only = [x.strip().upper() for x in args.only.split(",")] if args.only else None
    if only:
        bad = [e for e in only if e not in ALL_EXTRACTORS]
        if bad:
            print(json.dumps({"error": "unknown extractor(s): %s" % bad,
                              "known": ALL_EXTRACTORS}), file=sys.stderr)
            return 2

    pack = build_pack(args.a, args.b, grid=args.grid, only=only,
                      ocr_a=args.ocr_a, ocr_b=args.ocr_b, contact_path=args.contact,
                      force_modality=args.force_modality)

    # cache + slice-rerun delta: a full run seeds the cache; a --only rerun diffs
    # against it and returns just what changed — observation never costs a re-read.
    if args.cache_dir:
        os.makedirs(args.cache_dir, exist_ok=True)
        cache_file = os.path.join(args.cache_dir, _ab_hash(args.a, args.b) + ".json")
        if only and os.path.exists(cache_file):
            try:
                old = json.load(open(cache_file))
            except Exception:
                old = None
            if old:
                delta = {k: {"before": _slice_summary(old, k), "after": _slice_summary(pack, k)}
                         for k in only}
                json.dump(_merge_rerun(old, pack, only), open(cache_file, "w"))
                print(json.dumps({"delta": delta, "rerun": only,
                                  "grid_n": pack["meta"]["grid_n"],
                                  "params_hash": pack["params_hash"],
                                  "meta": {"a": args.a, "b": args.b}}))
                return 0
        if not only:  # only full runs seed the cache
            try:
                json.dump(pack, open(cache_file, "w"))
            except OSError:
                pass
    print(json.dumps(pack))
    return 0


if __name__ == "__main__":
    sys.exit(main())
