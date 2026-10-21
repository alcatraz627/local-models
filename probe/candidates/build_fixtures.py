#!/usr/bin/env python3
"""Copy source-faithful fixtures and create synthetic image-tool fixtures."""
import json
import struct
import shutil
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "fixtures"
VIS = ROOT / "probe/fixtures"
AFF = Path("/Users/alcatraz627/Code/Claude/Affinity/AffinityWork/guard/test/cases")


def fixture(name, truth, files):
    dest = OUT / name
    dest.mkdir(parents=True, exist_ok=True)
    for source, target in files:
        shutil.copy2(source, dest / target)
    (dest / "truth.json").write_text(json.dumps(truth, indent=2) + "\n")


def png_chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)


def write_png(path, width, height, channels, pixels):
    rows = b"".join(b"\0" + bytes(pixels[y * width * channels:(y + 1) * width * channels]) for y in range(height))
    color_type = {1: 0, 3: 2, 4: 6}[channels]
    data = b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0))
    data += png_chunk(b"IDAT", zlib.compress(rows, 9)) + png_chunk(b"IEND", b"")
    path.write_bytes(data)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    visual = {
        "f2-a": ["play", "icon"], "f2-b": ["play", "icon"],
        "f3-a": ["play", "icon"], "f3-b": ["play", "icon"],
        "f4-a": ["dashboard", "revenue", "1,240"], "f4-b": ["dashboard", "revenue", "1,240"],
        "f5-a": ["icon"], "f5-b": ["analytics", "users", "revenue"],
        "f6-a": ["sales", "q1", "q2", "q3", "q4"],
        "f6-b": ["sales", "q1", "q2", "q5", "q4"],
    }
    diffs = {
        "f2": {"kind": "contains_all", "expected": ["different", "color", "border"]},
        "f3": {"kind": "absence", "required": ["identical", "no difference", "unchanged"], "forbidden": ["different", "changed"]},
        "f4": {"kind": "contains_all", "expected": ["light", "dark", "same text"]},
        "f5": {"kind": "contains_all", "expected": ["incomparable", "aspect"]},
        "f6": {"kind": "contains_all", "expected": ["q3", "q5", "bar"]},
    }
    for key, truth in diffs.items():
        fixture("see-diff/" + key, truth,
                [(VIS / f"{key}-a.png", "a.png"), (VIS / f"{key}-b.png", "b.png")])
    for key, expected in visual.items():
        pair, side = key.split("-")
        fixture("see-read/ui-" + key, {"kind": "contains_all", "expected": expected},
                [(VIS / f"{pair}-{side}.png", "image.png")])
    fixture("see-diff/diff-login", {
        "kind": "contains_all", "expected": ["12", "47", "last sync"]
    }, [(VIS / "diff-a.png", "a.png"), (VIS / "diff-b.png", "b.png")])
    fixture("see-read/ocr", {
        "kind": "contains_all", "expected": ["verify fixture", "corner"]
    }, [(VIS / "ocr-fixture.png", "image.png")])

    for case_dir in sorted(AFF.glob("rug-*/")):
        image = case_dir / "fixture.png"
        case = case_dir / "case.json"
        if not image.is_file() or not case.is_file():
            continue
        data = json.loads(case.read_text())
        numbers = data.get("numbers", {})
        if data["id"] == "rug-border-twelve-motifs":
            truth = {"kind": "item_position", "expected_item": "motif 9", "position": "ninth",
                     "context": data.get("context")}
        elif data["id"] == "rug-crescents-match-bottom":
            truth = {"kind": "contains_all", "expected": [str(numbers["top_points"][0]), str(numbers["top_points"][1]), str(numbers["bottom_points"])]}
        elif data["id"] == "rug-rim-scallops-new-points":
            truth = {"kind": "contains_all", "expected": ["six", str(numbers["rim_points_each"]), str(numbers["needed_points_min_per_piece"])]}
        elif data["id"] == "rug-brick-column-fanning":
            truth = {"kind": "contains_all", "expected": [str(numbers["bricks_per_side"]), str(numbers["gap_lines_per_side"])]}
        elif data["id"] == "rug-smooth-pink-stripe":
            truth = {"kind": "contains_all", "expected": [str(numbers["pieces"]), str(numbers["slivers"])]}
        else:
            truth = {"kind": "contains_all", "expected": [str(numbers["shapes_total"]), str(numbers["working_only"]), str(numbers["copy_only"])]}
        truth["source_files"] = ["case.json"]
        truth["context"] = data.get("context")
        fixture("see-read/" + data["id"], truth, [(image, "image.png"), (case, "case.json")])

    synth = OUT / "image-tools/rmbg-shape"
    synth.mkdir(parents=True, exist_ok=True)
    size = 128
    pix = []
    mask = []
    fg = []
    composite = []
    for y in range(size):
        for x in range(size):
            v = (x * 37 + y * 53 + x * y * 7) % 70
            inside = ((x - 64) ** 2 / (36 ** 2) + (y - 64) ** 2 / (44 ** 2) <= 1) or (44 <= x <= 84 and 80 <= y <= 116)
            pix.extend((35 + v, 50 + (v * 3) % 80, 65 + (v * 5) % 90))
            m = 255 if inside else 0
            mask.append(m)
            fg.extend((240, 80, 40, 255 if inside else 0))
            bg_rgb = (35 + v, 50 + (v * 3) % 80, 65 + (v * 5) % 90)
            composite.extend((240, 80, 40) if inside else bg_rgb)
    write_png(synth / "foreground.png", size, size, 4, fg)
    write_png(synth / "mask.png", size, size, 1, mask)
    write_png(synth / "noisy-background.png", size, size, 3, pix)
    write_png(synth / "input.png", size, size, 3, composite)
    (synth / "truth.json").write_text(json.dumps({
        "kind": "alpha_mae_percent", "result_field": "alpha_mismatch_percent",
        "mask": "mask.png", "max_percent": 2,
        "shape": "ellipse with centered rectangle stem", "noise_seed": "integer-coordinate deterministic"
    }, indent=2) + "\n")

    edit_dir = OUT / "image-tools/edit-region"
    edit_dir.mkdir(parents=True, exist_ok=True)
    w = h = 256
    reference = []
    edited = []
    for y in range(h):
        for x in range(w):
            color = (245, 245, 247) if not (40 <= x <= 216 and 40 <= y <= 216) else (37, 99, 235)
            reference.extend(color)
            edited.extend((235, 80, 70) if 96 <= x <= 159 and 96 <= y <= 159 else color)
    write_png(edit_dir / "reference.png", w, h, 3, reference)
    write_png(edit_dir / "edited.png", w, h, 3, edited)
    (edit_dir / "truth.json").write_text(json.dumps({
        "kind": "grid_cells_changed_only", "result_field": "changed_cells",
        "expected_cells": [[3, 3], [3, 4], [4, 3], [4, 4]],
        "target_region_px": [96, 96, 159, 159], "source_files": ["edited.png"]
    }, indent=2) + "\n")
    fixture("image-tools/upscale", {"kind": "psnr_beats_lanczos", "candidate_field": "model_psnr",
                                     "baseline_field": "lanczos_psnr", "second_check": "affinity rug tip crop read beats raw",
                                     "source_files": ["case.json"]},
            [(AFF / "rug-border-twelve-motifs/fixture.png", "rug.png"),
             (AFF / "rug-border-twelve-motifs/case.json", "case.json")])
    fixture("text-small/probe-items", {
        "kind": "reuse_probe_markers", "source": "items.toml",
        "human_verdict_required": True, "envelope": "ok=true and nonempty text"
    }, [(ROOT / "probe/items.toml", "items.toml")])
    fixture("embed/archived-rag", {
        "kind": "skipped", "reason": "no archived RAG eval harness or dataset is present in this worktree"
    }, [])


if __name__ == "__main__":
    main()
