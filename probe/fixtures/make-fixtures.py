#!/usr/bin/env python3
"""Reproducible fixtures for the visual-compare battery.

Every fixture plants known ground truth so a model-free assertion can check it.
The art has no meaning of its own — it exists so an extractor can be caught
inventing a difference (F3) or missing a planted one (F2/F4/F5/F6).

Run with the project venv python (PIL lives there, not in bare python3):
    .venv/bin/python probe/fixtures/make-fixtures.py

Pairs written (F1 already exists as diff-a/b.png — today's login-pair regression):
  F2 icon pair       f2-a/b.png  glyph + perturbed copy (hue +15°, radius 4→10, stroke 3→2)
  F3 identical pair  f3-a/b.png  byte-identical — the fabrication guard
  F4 theme pair      f4-a/b.png  same text/layout, light↔dark palette
  F5 incomparable    f5-a/b.png  icon (1:1) vs dashboard (3:1) — comparability gate
  F6 chart pair      f6-a/b.png  axis relabel (Q3→Q5) + one bar taller

Each fixture's ground truth is documented inline next to where it is planted.
"""
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = __file__.rsplit("/", 1)[0] if "/" in __file__ else "."


def font(size):
    """A legible truetype for OCR-bearing fixtures; falls back to PIL's bitmap.

    Apple Vision needs real glyph shapes at a readable size — the default
    bitmap font reads poorly, which would make an OCR-empty result ambiguous
    between 'no text' and 'unreadable text'.
    """
    for path in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNS.ttf",
        "/Library/Fonts/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def hue_shift(img, degrees):
    """Rotate hue by `degrees` (PIL H channel is 0-255, so 360°==256)."""
    hsv = img.convert("RGB").convert("HSV")
    h, s, v = hsv.split()
    off = round(degrees / 360.0 * 256) % 256
    h = h.point(lambda p: (p + off) % 256)
    return Image.merge("HSV", (h, s, v)).convert("RGB")


def make_icon(radius, stroke, fill=(37, 99, 235)):
    """A rounded-rect badge with a white play-glyph — the F2 base shape.

    The glyph is identical across the pair; only the badge radius, the outline
    stroke width, and (on B) the hue differ, so the divergences are isolated.
    """
    img = Image.new("RGB", (256, 256), (245, 245, 247))
    d = ImageDraw.Draw(img)
    outline = tuple(max(0, c - 60) for c in fill)
    d.rounded_rectangle([40, 40, 216, 216], radius=radius, fill=fill,
                        outline=outline, width=stroke)
    # centered play triangle — held constant across the pair
    d.polygon([(108, 96), (108, 160), (168, 128)], fill=(255, 255, 255))
    return img


def make_card(bg, fg, accent, sub):
    """A tiny stat card. Same text across the theme pair (F4) so the only
    signal is a systematic palette flip, and E1's text diff stays empty."""
    img = Image.new("RGB", (400, 300), bg)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 400, 64], fill=accent)
    d.text((24, 20), "Dashboard", font=font(30), fill=(255, 255, 255))
    d.text((24, 96), "Revenue", font=font(24), fill=sub)
    d.text((24, 136), "$1,240", font=font(52), fill=fg)
    d.text((24, 210), "3 items tracked", font=font(24), fill=sub)
    d.rounded_rectangle([24, 250, 180, 284], radius=8, fill=accent)
    d.text((44, 256), "View all", font=font(22), fill=(255, 255, 255))
    return img


def make_dashboard():
    """A wide, text-dense surface — the incomparable partner for the icon (F5)."""
    img = Image.new("RGB", (900, 300), (250, 250, 250))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 900, 48], fill=(30, 41, 59))
    d.text((20, 12), "Analytics  ·  Users  ·  Revenue  ·  Settings",
           font=font(24), fill=(255, 255, 255))
    for i, (label, val) in enumerate(
        [("Users", "12,405"), ("Sessions", "48,201"),
         ("Bounce", "42%"), ("Revenue", "$92,140")]):
        x = 20 + i * 220
        d.rounded_rectangle([x, 80, x + 200, 220], radius=10,
                            outline=(200, 200, 200), width=2)
        d.text((x + 16, 100), label, font=font(22), fill=(100, 116, 139))
        d.text((x + 16, 140), val, font=font(36), fill=(15, 23, 42))
    return img


def make_chart(heights, labels):
    """A 4-bar chart with x-axis tick labels. F6 perturbs one label and one
    bar height so E1 catches the relabel and E5 localizes the taller bar."""
    img = Image.new("RGB", (400, 300), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((150, 12), "Sales", font=font(26), fill=(15, 23, 42))
    base_y = 250
    d.line([50, base_y, 380, base_y], fill=(15, 23, 42), width=2)
    for i, (h, lab) in enumerate(zip(heights, labels)):
        x = 70 + i * 80
        d.rectangle([x, base_y - h, x + 48, base_y], fill=(37, 99, 235))
        d.text((x + 8, base_y + 8), lab, font=font(22), fill=(15, 23, 42))
    return img


def save(img, name):
    p = f"{HERE}/{name}"
    img.save(p)
    print(f"  wrote {name}  ({img.width}x{img.height})")
    return p


def main():
    print("fixtures →", HERE)

    # F2 · icon pair — ground truth: dHash/aHash > 0; E3 palette ΔE 'different'
    # from the +15° hue; E6 edge-density fires on the border/corner cells from the
    # thicker stroke (3→7) and rounder corners (4→20). The shape delta is sized to
    # the grid: a 1px change is below an 8×8 (32px) cell floor, so it must be
    # cell-scale to be detectable — a fixture plants what the extractor can see.
    a = make_icon(radius=4, stroke=3)
    b = make_icon(radius=20, stroke=7)
    b = hue_shift(b, 15)
    save(a, "f2-a.png")
    save(b, "f2-b.png")

    # F3 · identical pair — ground truth: EVERY extractor ~zero, judge says clean.
    # Byte-identical so any non-zero signal is a fabrication.
    f3 = make_icon(radius=8, stroke=3, fill=(16, 185, 129))
    save(f3, "f3-a.png")
    save(f3, "f3-b.png")

    # F4 · theme pair — ground truth: E1 text diff EMPTY (same words), systematic
    # ΔE everywhere (light↔dark), E5 hot across the whole grid not one region.
    light = make_card(bg=(255, 255, 255), fg=(15, 23, 42),
                      accent=(37, 99, 235), sub=(100, 116, 139))
    dark = make_card(bg=(17, 24, 39), fg=(241, 245, 249),
                     accent=(37, 99, 235), sub=(148, 163, 184))
    save(light, "f4-a.png")
    save(dark, "f4-b.png")

    # F5 · incomparable pair — ground truth: comparable:'poor' (aspect 1:1 vs 3:1),
    # graceful, next: nudge carries a crop command.
    save(make_icon(radius=8, stroke=3), "f5-a.png")
    save(make_dashboard(), "f5-b.png")

    # F6 · chart pair — ground truth: E1 catches Q3→Q5 relabel (removed Q3/added
    # Q5); E5 localizes the taller bar (index 2: 60→140) to its column cells.
    save(make_chart([80, 120, 60, 100], ["Q1", "Q2", "Q3", "Q4"]), "f6-a.png")
    save(make_chart([80, 120, 140, 100], ["Q1", "Q2", "Q5", "Q4"]), "f6-b.png")

    print("done — 5 pairs (F2–F6). F1 = diff-a/b.png (pre-existing).")


if __name__ == "__main__":
    sys.exit(main())
