#!/usr/bin/env python3
"""Build every catalog case into probe/vision/fixtures/<id>/s<seed>/.

Each folder gets image.png (or a.png and b.png for diff cases), truth.json and
prompt.txt. Truth comes only from the generator's own parameters, and the same
seed always writes byte-identical files. Fixed repo images (the F-series charts,
the Affinity rug) are copied, not redrawn.

    .venv/bin/python probe/vision/gen.py [--cases C01,T01] [--seeds 0,1,2] [--out DIR]
"""

import argparse
import io
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from common import FIXTURES, REPO, case_map, load_cases, seeds_for

FONT_FILES = {
    "arial": "/System/Library/Fonts/Supplemental/Arial.ttf",
    "bold": "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "menlo": "/System/Library/Fonts/Menlo.ttc",
    "courier": "/System/Library/Fonts/Supplemental/Courier New.ttf",
    "verdana": "/System/Library/Fonts/Supplemental/Verdana.ttf",
}
_FONT_CACHE = {}

WHITE = (255, 255, 255)
INK = (0, 0, 0)
BLUE = (37, 99, 235)
RED = (220, 38, 38)
GREEN = (22, 163, 74)
YELLOW = (234, 179, 8)
ORANGE = (234, 88, 12)
PURPLE = (147, 51, 234)
RGB = {"red": RED, "blue": BLUE, "green": GREEN, "yellow": YELLOW, "purple": PURPLE, "orange": ORANGE}
FIXTURE_SRC = REPO / "probe" / "fixtures"
RUG_DIR = REPO / "probe" / "candidates" / "fixtures" / "see-read" / "rug-border-twelve-motifs"


def font(key, size):
    """A TrueType font by short name. Missing fonts stop the run on purpose."""
    if (key, size) not in _FONT_CACHE:
        path = Path(FONT_FILES[key])
        if not path.is_file():
            raise FileNotFoundError(f"required font is missing: {path}")
        _FONT_CACHE[(key, size)] = ImageFont.truetype(str(path), size)
    return _FONT_CACHE[(key, size)]


def new(w, h, color=WHITE):
    return Image.new("RGB", (w, h), color)


def centered(d, xy, text, f, fill):
    d.text(xy, text, font=f, fill=fill, anchor="mm")


def place(rng, n, bounds, far_enough, tries=20000):
    """n points inside bounds=(x0,y0,x1,y1), each `far_enough(p, q)` from the others."""
    x0, y0, x1, y1 = bounds
    pts = []
    for _ in range(n):
        for _try in range(tries):
            p = (rng.randint(x0, x1), rng.randint(y0, y1))
            if all(far_enough(p, q) for q in pts):
                pts.append(p)
                break
        else:
            raise RuntimeError("could not place fixture objects without overlap")
    return pts


def euclid(gap):
    return lambda p, q: math.dist(p, q) >= gap


def chebyshev(gap):
    return lambda p, q: max(abs(p[0] - q[0]), abs(p[1] - q[1])) >= gap


def delta_e(c1, c2):
    """CIE76 colour distance between two sRGB triples."""
    def lab(rgb):
        lin = [(v / 255 / 12.92) if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4 for v in rgb]
        x = (0.4124 * lin[0] + 0.3576 * lin[1] + 0.1805 * lin[2]) / 0.95047
        y = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
        z = (0.0193 * lin[0] + 0.1192 * lin[1] + 0.9505 * lin[2]) / 1.08883
        f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
        return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))
    return round(math.dist(lab(c1), lab(c2)), 1)


def checkbox(d, x, y, checked):
    """18 px box at (x, y); checked boxes are blue with a white tick."""
    if checked:
        d.rectangle((x, y, x + 18, y + 18), fill=BLUE)
        d.line((x + 4, y + 9, x + 8, y + 13, x + 15, y + 4), fill=WHITE, width=2)
    else:
        d.rectangle((x, y, x + 18, y + 18), outline=(107, 114, 128), width=2)



def table_image(rng, seed):
    """The B01/C04 table. Returns (image, rows) with rows as dicts in drawn order."""
    names = ["Halvorsen", "Okafor", "Brandt", "Ivanova", "Mendes", "Tanaka", "Novak"]
    if seed:
        rng.shuffle(names)
    regions = ["North", "South", "East", "West"]
    units = rng.sample(range(10, 100), 7)
    if seed == 0:
        names = ["Okafor", "Brandt", "Halvorsen", "Ivanova", "Mendes", "Tanaka", "Novak"]
        units[2] = 57
        if units.count(57) > 1:
            units = [34, 82, 57, 21, 68, 90, 43]
    rows = [{"name": n, "region": rng.choice(regions), "units": u,
             "price": f"${rng.randint(5, 95)}.{rng.choice([0, 25, 50, 75, 95, 99]):02d}"}
            for n, u in zip(names, units)]
    im = new(900, 420)
    d = ImageDraw.Draw(im)
    f, fb = font("arial", 18), font("bold", 18)
    xs = [40, 280, 480, 640]
    for x in (30, 270, 470, 630, 860):
        d.line((x, 20, x, 388), fill=(170, 170, 170), width=1)
    for i in range(9):
        d.line((30, 20 + 46 * i, 860, 20 + 46 * i), fill=(170, 170, 170), width=1)
    for x, head in zip(xs, ["Name", "Region", "Units", "Price"]):
        d.text((x, 32), head, fill=INK, font=fb)
    for i, row in enumerate(rows):
        for x, val in zip(xs, [row["name"], row["region"], str(row["units"]), row["price"]]):
            d.text((x, 32 + 46 * (i + 1)), val, fill=INK, font=f)
    return im, rows


def bar_values(seed):
    if seed == 0:
        return [23, 47, 35, 62, 18]
    rng = random.Random(f"bars:{seed}")
    while True:
        vals = [rng.randint(10, 78) for _ in range(5)]
        spread = all(abs(a - b) >= 8 for i, a in enumerate(vals) for b in vals[i + 1:])
        if spread and vals[3] % 10 != 0:
            return vals


def bar_chart(vals):
    """640x420 chart, 4 px per unit, bars at x=100..500, no value labels."""
    im = new(640, 420)
    d = ImageDraw.Draw(im)
    f = font("arial", 14)
    for v in range(0, 81, 10):
        y = 360 - 4 * v
        d.line((78, y, 590, y), fill=(220, 220, 220), width=1)
        d.text((70, y), str(v), fill=(30, 30, 30), font=f, anchor="rm")
    d.line((80, 40, 80, 360), fill=INK, width=2)
    d.line((80, 360, 590, 360), fill=INK, width=2)
    for i, (v, label) in enumerate(zip(vals, ["Mon", "Tue", "Wed", "Thu", "Fri"])):
        x = 100 + 100 * i
        d.rectangle((x, 360 - 4 * v, x + 60, 359), fill=BLUE)
        d.text((x + 30, 378), label, fill=INK, font=f, anchor="mm")
    return im


def buttons_image(seed):
    """The U02/H04 image: Save, Export, Delete with one disabled."""
    labels = ["Save", "Export", "Delete"]
    disabled = labels[[1, 0, 2][seed % 3]]
    im = new(700, 200)
    d = ImageDraw.Draw(im)
    f = font("arial", 20)
    for i, label in enumerate(labels):
        x = 40 + 200 * i
        off = label == disabled
        d.rounded_rectangle((x, 76, x + 160, 124), radius=8, fill=(229, 231, 235) if off else BLUE)
        centered(d, (x + 80, 100), label, f, (156, 163, 175) if off else WHITE)
    return im, disabled


def jpeg_roundtrip(im, quality=85):
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


# Each takes (seed, rng, prompt) and returns (files, truth, prompt).

BUILDERS = {}


def case(*ids):
    def wrap(fn):
        for cid in ids:
            BUILDERS[cid] = fn
        return fn
    return wrap


@case("C01")
def c01(seed, rng, prompt):
    n = [7, 5, 9][seed % 3]
    im = new(640, 400)
    d = ImageDraw.Draw(im)
    for x, y in place(rng, n, (30, 30, 610, 370), euclid(56)):
        d.ellipse((x - 22, y - 22, x + 22, y + 22), fill=(15, 23, 42))
    return {"image.png": im}, {"count": n}, prompt


@case("C02")
def c02(seed, rng, prompt):
    im = new(800, 600)
    d = ImageDraw.Draw(im)
    pts = place(rng, 27, (20, 20, 780, 580), euclid(22))
    rings = set(rng.sample(range(27), 4))
    for i, (x, y) in enumerate(pts):
        box = (x - 7, y - 7, x + 7, y + 7)
        if i in rings:
            d.ellipse(box, outline=(30, 30, 30), width=2)
        else:
            d.ellipse(box, fill=(30, 30, 30))
    return {"image.png": im}, {"count": 23, "decoys": 4}, prompt


@case("C03")
def c03(seed, rng, prompt):
    counts = [6, 4, 5] if seed == 0 else rng.sample([3, 4, 5, 6], 3)
    names = ["red", "blue", "green"]
    asked = ["blue", "red", "green"][seed % 3]
    im = new(720, 480)
    d = ImageDraw.Draw(im)
    pts = place(rng, sum(counts), (40, 40, 680, 440), chebyshev(50))
    rng.shuffle(pts)
    k = 0
    for name, n in zip(names, counts):
        for x, y in pts[k:k + n]:
            d.rectangle((x - 18, y - 18, x + 18, y + 18), fill=RGB[name])
        k += n
    want = counts[names.index(asked)]
    prompt = prompt.replace("BLUE", asked.upper())
    return {"image.png": im}, {"color": asked, "count": want, "total": sum(counts)}, prompt


@case("C04")
def c04(seed, rng, prompt):
    im, rows = table_image(rng, seed)
    return {"image.png": im}, {"rows": len(rows)}, prompt


def draw_id(rng, seed):
    if seed == 0:
        return "K7Q-48XZ-2093"
    alnum = [c for c in "ABCDEFGHJKMNPQRSTUVWXYZ0123456789"]
    pick = lambda n, pool: "".join(rng.choice(pool) for _ in range(n))
    return f"{pick(3, alnum)}-{pick(4, alnum)}-{pick(4, '0123456789')}"


@case("T01")
def t01(seed, rng, prompt):
    ident = draw_id(rng, seed)
    im = new(900, 220)
    d = ImageDraw.Draw(im)
    d.text((40, 24), "Release notes", fill=INK, font=font("bold", 32))
    d.text((40, 120), "Build ID: " + ident, fill=INK, font=font("menlo", 14))
    d.text((40, 160), "Ref: " + ident[:8], fill=INK, font=font("menlo", 14))
    return {"image.png": im}, {"text": ident}, prompt


@case("T02")
def t02(seed, rng, prompt):
    px = [9, 12, 7][seed % 3]
    text = ["Invoice 55-0193 due 14 Mar", "Invoice 82-6401 due 07 Jun", "Invoice 39-2715 due 22 Oct"][seed % 3]
    im = new(1200, 300)
    ImageDraw.Draw(im).text((40, 130), text, fill=INK, font=font("arial", px))
    return {"image.png": im}, {"text": text, "px": px}, prompt


T03_VARIANTS = [
    (["vorplex trindle", "quaso maffin", "glent 4417 drubb", "ostrawe nym"],
     {"MAFFIN": "MUFFIN", "GLENT": "GLINT", "NYM": "NYMPH"}),
    (["draxil wemp", "nuvor kessel", "flarn 5824 brint", "opali zenth"],
     {"WEMP": "WIMP", "KESSEL": "KETTLE", "BRINT": "BRING", "ZENTH": "ZENITH"}),
    (["mervix plone", "tavro quindle", "sharn 9036 vrel", "ulmeti grom"],
     {"PLONE": "PHONE", "SHARN": "SHARD", "VREL": "VEAL", "GROM": "GROOM"}),
]


@case("T03")
def t03(seed, rng, prompt):
    lines, traps = T03_VARIANTS[seed % 3]
    im = new(800, 260)
    d = ImageDraw.Draw(im)
    for i, line in enumerate(lines):
        d.text((40, 30 + 55 * i), line, fill=INK, font=font("arial", 26))
    tokens = " ".join(lines).upper().split()
    return {"image.png": im}, {"tokens": tokens, "autocorrect_traps": traps}, prompt


T04_PAIRS = [("ORBIT 7731", "LUMEN 2208"), ("VAULT 4096", "PRISM 8350"), ("NODAL 6127", "FERRO 9514")]


@case("T04")
def t04(seed, rng, prompt):
    target, decoy = T04_PAIRS[seed % 3]
    im = new(600, 600)
    f = font("bold", 34)
    vert = Image.new("RGBA", (300, 60), (255, 255, 255, 0))
    ImageDraw.Draw(vert).text((10, 8), target, fill=INK, font=f)
    vert = vert.rotate(90, expand=True)
    im.paste(vert, (12, 150), vert)
    tilt = Image.new("RGBA", (260, 60), (255, 255, 255, 0))
    ImageDraw.Draw(tilt).text((10, 8), decoy, fill=INK, font=f)
    tilt = tilt.rotate(30, expand=True, resample=Image.BICUBIC)
    im.paste(tilt, (190, 230), tilt)
    return {"image.png": im}, {"text": target, "decoy": decoy}, prompt


@case("T05")
def t05(seed, rng, prompt):
    target = ["delta 5508", "sigma 7812", "omega 3046"][seed % 3]
    decoy = ["alpha 1234", "gamma 9021", "theta 4455"][seed % 3]
    im = new(800, 300, (210, 210, 210))
    d = ImageDraw.Draw(im)
    top_first = seed % 2 == 0
    d.text((60, 60 if top_first else 180), decoy, fill=(20, 20, 20), font=font("arial", 30))
    d.text((60, 180 if top_first else 60), target, fill=(196, 196, 196), font=font("arial", 30))
    return {"image.png": im}, {"text": target.upper(), "decoy": decoy.upper()}, prompt


T06_LINES = ["Shipment 7 of 12 left Rotterdam on 03/09.",
             "Net weight 1,482.6 kg; tare 212 kg.",
             "Contact: ops-desk@example.test, ext. 4471."]


@case("T06")
def t06(seed, rng, prompt):
    im = new(900, 300)
    d = ImageDraw.Draw(im)
    for i, line in enumerate(T06_LINES):
        d.text((36, 40 + 72 * i), line, fill=INK, font=font("verdana", 16))
    return {"image.png": im}, {"lines": list(T06_LINES)}, prompt


@case("S01")
def s01(seed, rng, prompt):
    left = ["circle", "square", "square", "circle"][seed % 4]
    im = new(600, 400)
    d = ImageDraw.Draw(im)
    jitter = rng.randint(-30, 30)
    circle_x, square_x = (150, 450) if left == "circle" else (450, 150)
    d.ellipse((circle_x - 50, 200 + jitter - 50, circle_x + 50, 200 + jitter + 50), fill=RED)
    d.rectangle((square_x - 50, 200 - jitter - 50, square_x + 50, 200 - jitter + 50), fill=BLUE)
    return {"image.png": im}, {"left": left}, prompt


def star_points(cx, cy, r_out=18, r_in=8):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


@case("S02")
def s02(seed, rng, prompt):
    while True:
        spots = place(rng, 5, (20, 20, 710, 430), euclid(130))
        letters = rng.sample("ABCDE", 5)
        star = (rng.randint(40, 760), rng.randint(40, 460))
        centers = [(x + 35, y + 25) for x, y in spots]
        clear = all(max(x - star[0], star[0] - (x + 70), 0) ** 2 + max(y - star[1], star[1] - (y + 50), 0) ** 2 >= 28 ** 2
                    for x, y in spots)
        ranked = sorted(range(5), key=lambda i: math.dist(centers[i], star))
        margin = math.dist(centers[ranked[1]], star) - math.dist(centers[ranked[0]], star)
        if clear and margin >= 60:
            break
    im = new(800, 500)
    d = ImageDraw.Draw(im)
    for (x, y), letter in zip(spots, letters):
        d.rectangle((x, y, x + 70, y + 50), outline=INK, width=2)
        centered(d, (x + 35, y + 25), letter, font("bold", 26), INK)
    d.polygon(star_points(*star), fill=(52, 199, 89))
    return {"image.png": im}, {"letter": letters[ranked[0]], "margin_px_min": 60, "margin_px": round(margin, 1)}, prompt


POSITIONS = ["top-left", "top", "top-right", "left", "center", "right", "bottom-left", "bottom", "bottom-right"]


@case("S03")
def s03(seed, rng, prompt):
    order = random.Random("S03-order").sample(POSITIONS, 9)
    pos = order[seed % 9]
    row, col = divmod(POSITIONS.index(pos), 3)
    x, y = 100 + 200 * col, 100 + 200 * row
    im = new(600, 600)
    ImageDraw.Draw(im).polygon([(x, y - 46), (x - 40, y + 23), (x + 40, y + 23)], fill=YELLOW)
    return {"image.png": im}, {"position": pos}, prompt


@case("S04")
def s04(seed, rng, prompt):
    names = ["red", "blue", "green", "yellow", "purple"]
    order = ["green", "red", "purple", "blue", "yellow"] if seed == 0 else rng.sample(names, 5)
    im = new(900, 200)
    d = ImageDraw.Draw(im)
    for x, name in zip((110, 280, 450, 620, 790), order):
        d.ellipse((x - 40, 60, x + 40, 140), fill=RGB[name])
    return {"image.png": im}, {"order": order}, prompt


K03_WORDS = ["APPLE", "LEMON", "GRAPE"]
K03_BAN = {"APPLE": {"red", "green"}, "LEMON": {"yellow"}, "GRAPE": {"purple"}}


@case("K03")
def k03(seed, rng, prompt):
    lemon = ["red", "green", "blue"][seed % 3]
    pool = [c for c in ("yellow", "red", "green", "blue", "orange") if c != lemon]
    while True:
        apple, grape = rng.sample(pool, 2)
        if seed == 0:
            apple, grape = "yellow", "green"
        if apple not in K03_BAN["APPLE"] and grape not in K03_BAN["GRAPE"]:
            break
    inks = {"APPLE": apple, "LEMON": lemon, "GRAPE": grape}
    im = new(700, 300)
    d = ImageDraw.Draw(im)
    for i, word in enumerate(K03_WORDS):
        d.text((40, 30 + 80 * i), word, fill=RGB[inks[word]], font=font("bold", 48))
    return {"image.png": im}, {"word": "LEMON", "ink": lemon, "prior": "yellow", "inks": inks}, prompt


@case("G01")
def g01(seed, rng, prompt):
    vals = bar_values(seed)
    return {"image.png": bar_chart(vals)}, {"label": "Thu", "value": vals[3], "tol": 3, "values": vals}, prompt


def dashed(d, pts, fill, width, dash=10, gap=6):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        length = math.dist((x0, y0), (x1, y1))
        t = 0.0
        while t < length:
            e = min(t + dash, length)
            d.line((x0 + (x1 - x0) * t / length, y0 + (y1 - y0) * t / length,
                    x0 + (x1 - x0) * e / length, y0 + (y1 - y0) * e / length), fill=fill, width=width)
            t += dash + gap


@case("G03")
def g03(seed, rng, prompt):
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]
    k = [4, 3, 6][seed % 3]
    a = [rng.randint(30, 42)]
    while len(a) < 8:
        a.append(max(24, min(56, a[-1] + rng.choice([-1, 1]) * rng.randint(2, 8))))
    gaps = [rng.randint(6, 14) for _ in range(8)]
    b = [a[i] + (gaps[i] if i >= k else -gaps[i]) for i in range(8)]
    im = new(720, 420)
    d = ImageDraw.Draw(im)
    f = font("arial", 14)
    xs = [100 + 80 * i for i in range(8)]
    y = lambda v: 360 - 4 * v
    for v in range(0, 81, 20):
        d.line((70, y(v), 680, y(v)), fill=(225, 225, 225))
        d.text((62, y(v)), str(v), fill=(40, 40, 40), font=f, anchor="rm")
    d.line((70, 40, 70, 360), fill=INK, width=2)
    d.line((70, 360, 680, 360), fill=INK, width=2)
    for x, m in zip(xs, months):
        d.text((x, 378), m, fill=INK, font=f, anchor="mm")
    d.line([(x, y(v)) for x, v in zip(xs, a)], fill=BLUE, width=4)
    dashed(d, [(x, y(v)) for x, v in zip(xs, b)], ORANGE, 3)
    d.line((600, 56, 630, 56), fill=BLUE, width=4)
    d.text((640, 56), "A", fill=INK, font=f, anchor="lm")
    dashed(d, [(600, 80), (630, 80)], ORANGE, 3, dash=7, gap=4)
    d.text((640, 80), "B", fill=INK, font=f, anchor="lm")
    return {"image.png": im}, {"month": months[k], "series_a": a, "series_b": b}, prompt


F6_VALUES = [80, 120, 60, 100]
F6_LABELS = ["Q1", "Q2", "Q3", "Q4"]


def copy_png(name):
    return Image.open(FIXTURE_SRC / name).convert("RGB")


@case("G04")
def g04(seed, rng, prompt):
    truth = {"tallest": F6_LABELS[F6_VALUES.index(max(F6_VALUES))], "shortest": F6_LABELS[F6_VALUES.index(min(F6_VALUES))]}
    return {"image.png": copy_png("f6-a.png")}, truth, prompt


@case("B01")
def b01(seed, rng, prompt):
    im, rows = table_image(rng, seed)
    i = next(i for i, r in enumerate(rows) if r["name"] == "Halvorsen")
    near = [rows[j]["units"] for j in (i - 1, i + 1) if 0 <= j < len(rows)]
    return {"image.png": im}, {"row": "Halvorsen", "col": "Units", "value": rows[i]["units"], "neighbor_values": near}, prompt


@case("B02")
def b02(seed, rng, prompt):
    im = new(1400, 900)
    d = ImageDraw.Draw(im)
    f, fb = font("arial", 11), font("bold", 11)
    xs = [24, 230, 430, 610, 760, 980]
    owners = ["Alvarez", "Brandt", "Chen", "Dube", "Eriksen", "Farouk", "Gupta", "Haddad"]
    notes = ["recount", "awaiting vendor", "ok", "escalated", "see ticket", "dup of earlier", "none"]
    statuses = [rng.choice(["OPEN", "HOLD", "DONE", "VOID"]) for _ in range(15)]
    statuses[10], statuses[11], statuses[12] = "OPEN", "HOLD", "DONE"
    for x, head in zip(xs, ["ID", "Owner", "Status", "Qty", "Updated", "Note"]):
        d.text((x, 24), head, fill=INK, font=fb)
    d.line((20, 48, 1380, 48), fill=(120, 120, 120))
    for i in range(15):
        y = 70 + 52 * i
        vals = [f"R-{401 + i:04d}", rng.choice(owners), statuses[i], str(rng.randint(1, 240)),
                f"2026-10-{rng.randint(1, 28):02d}", rng.choice(notes)]
        for x, val in zip(xs, vals):
            d.text((x, y), val, fill=INK, font=f)
        d.line((20, y + 26, 1380, y + 26), fill=(205, 205, 205))
    return {"image.png": im}, {"value": "HOLD", "crop": "700x300+0+560"}, prompt


@case("U01")
def u01(seed, rng, prompt):
    labels = ["Email alerts", "Dark mode", "Auto-save", "Beta features", "Analytics"]
    on = labels[:2] if seed == 0 else sorted(rng.sample(labels, 2), key=labels.index)
    im = new(600, 360)
    d = ImageDraw.Draw(im)
    for i, label in enumerate(labels):
        y = 40 + 60 * i
        checkbox(d, 40, y, label in on)
        d.text((74, y - 2), label, fill=INK, font=font("arial", 20))
    return {"image.png": im}, {"checked": on}, prompt


@case("U02")
def u02(seed, rng, prompt):
    im, disabled = buttons_image(seed)
    return {"image.png": im}, {"disabled": disabled}, prompt


@case("U03")
def u03(seed, rng, prompt):
    labels = ["Overview", "Logs", "Metrics", "Alerts", "Settings"]
    selected = labels[[1, 3, 4][seed % 3]]
    im = new(900, 120)
    d = ImageDraw.Draw(im)
    for i, label in enumerate(labels):
        x = 30 + 170 * i
        if label == selected:
            f = font("bold", 20)
            d.text((x, 36), label, fill=BLUE, font=f)
            d.line((x, 80, x + f.getlength(label), 80), fill=BLUE, width=3)
        else:
            d.text((x, 36), label, fill=INK, font=font("arial", 20))
    return {"image.png": im}, {"selected": selected}, prompt


@case("U04")
def u04(seed, rng, prompt):
    labels = ["Wi-Fi", "Bluetooth", "AirDrop", "Hotspot"]
    on = ["Wi-Fi", "AirDrop"] if seed == 0 else sorted(rng.sample(labels, 2), key=labels.index)
    im = new(600, 320)
    d = ImageDraw.Draw(im)
    for i, label in enumerate(labels):
        y = 42 + 68 * i
        d.text((40, y + 15), label, fill=INK, font=font("arial", 20), anchor="lm")
        is_on = label in on
        d.rounded_rectangle((480, y, 532, y + 30), radius=15, fill=(52, 199, 89) if is_on else (209, 213, 219))
        kx = 480 + 27 if is_on else 480 + 3
        d.ellipse((kx, y + 3, kx + 24, y + 27), fill=WHITE)
    return {"image.png": im}, {"on": on, "off": [x for x in labels if x not in on]}, prompt


U06_CHECKED = [["Send weekly digest"], ["Enable two-factor"], ["Send weekly digest", "Enable two-factor"]]


@case("U06")
def u06(seed, rng, prompt):
    checked = U06_CHECKED[seed % 3]
    im = new(900, 640)
    d = ImageDraw.Draw(im)
    f = font("arial", 16)
    d.text((40, 24), "Account settings", fill=INK, font=font("bold", 28))
    elements = []
    for i, label in enumerate(["Full name", "Email", "Company", "Phone"]):
        y = 90 + 70 * i
        d.text((40, y), label, fill=INK, font=f)
        d.rectangle((40, y + 24, 400, y + 60), outline=(140, 140, 140), width=1)
        elements.append({"text": label, "type": "input"})
    for i, label in enumerate(["Send weekly digest", "Enable two-factor"]):
        y = 390 + 40 * i
        checkbox(d, 40, y, label in checked)
        d.text((68, y - 1), label, fill=INK, font=f)
        elements.append({"text": label, "type": "checkbox", "state": "checked" if label in checked else "unchecked"})
    x = 40
    for label in ["Privacy policy", "Terms", "Help center"]:
        d.text((x, 490), label, fill=BLUE, font=f)
        width = f.getlength(label)
        d.line((x, 512, x + width, 512), fill=BLUE, width=1)
        x += width + 36
        elements.append({"text": label, "type": "link"})
    for label, box, fill, ink, outline in [
        ("Cancel", (40, 560, 170, 604), WHITE, INK, (120, 120, 120)),
        ("Save changes", (190, 560, 350, 604), BLUE, WHITE, None),
        ("Delete account", (370, 560, 540, 604), RED, WHITE, None),
    ]:
        d.rounded_rectangle(box, radius=6, fill=fill, outline=outline, width=1)
        centered(d, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), label, f, ink)
        elements.append({"text": label, "type": "button"})
    return {"image.png": im}, {"elements": elements, "neutral": ["Account settings"]}, prompt


@case("U07")
def u07(seed, rng, prompt):
    value = ["12", "99+", "3", "27", "9"][seed % 5]
    im = new(300, 200)
    d = ImageDraw.Draw(im)
    dark = (40, 40, 48)
    d.ellipse((95, 62, 145, 112), fill=dark)
    d.rectangle((95, 87, 145, 120), fill=dark)
    d.polygon([(86, 124), (154, 124), (146, 112), (94, 112)], fill=dark)
    d.ellipse((112, 124, 128, 138), fill=dark)
    f = font("bold", 14)
    if len(value) > 2:
        d.rounded_rectangle((130, 52, 172, 78), radius=13, fill=RED)
        centered(d, (151, 65), value, f, WHITE)
    else:
        d.ellipse((135, 52, 161, 78), fill=RED)
        centered(d, (148, 65), value, f, WHITE)
    return {"image.png": im}, {"value": value}, prompt


R01_SERVICES = ["api", "web", "db", "queue", "cache", "auth", "search", "billing"]
R01_KINDS = ["CPU", "Memory", "Errors", "Throughput", "Saturation", "Requests"]


@case("R01")
def r01(seed, rng, prompt):
    names = [f"{s} {k}" for s in R01_SERVICES for k in R01_KINDS]
    rng.shuffle(names)
    names = iter(names)
    im = new(2400, 1500, (245, 245, 247))
    d = ImageDraw.Draw(im)
    for r in range(6):
        for c in range(8):
            x, y = 20 + 295 * c, 40 + 240 * r
            d.rectangle((x, y, x + 280, y + 160), fill=WHITE)
            if (r, c) == (5, 7):
                label, value = "Latency p99", "412 ms"
            elif (r, c) == (5, 6):
                label, value = "Latency p95", "388 ms"
            else:
                label = next(names)
                value = f"{rng.choice([n for n in range(100, 400) if n not in (412, 388)])} ms"
            d.text((x + 12, y + 12), label, fill=INK, font=font("arial", 11))
            d.text((x + 12, y + 40), value, fill=INK, font=font("arial", 13))
    return {"image.png": im}, {"value": 412, "decoy": 388, "crop": "700x500+1700+1000"}, prompt


def grid_pair(seed, rng):
    cells = [(3, 2)]
    while len(cells) < 3:
        c = (rng.randint(1, 4), rng.randint(1, 4))
        if c not in cells:
            cells.append(c)
    cell = cells[seed % 3]
    hard = seed % 3 == 2
    changed = (37, 118, 235) if hard else RED
    a, b = new(512, 512), new(512, 512)
    da, db = ImageDraw.Draw(a), ImageDraw.Draw(b)
    for r in range(1, 5):
        for c in range(1, 5):
            cx, cy = 128 * (c - 1) + 64, 128 * (r - 1) + 64
            box = (cx - 36, cy - 36, cx + 36, cy + 36)
            da.ellipse(box, fill=BLUE)
            db.ellipse(box, fill=changed if (r, c) == cell else BLUE)
    return a, b, cell, ("hard" if hard else "easy"), delta_e(BLUE, changed)


@case("D02")
def d02(seed, rng, prompt):
    a, b, cell, variant, de = grid_pair(seed, rng)
    return {"a.png": a, "b.png": b}, {"cell": list(cell), "variant": variant, "deltaE": de}, prompt


D03_RECEIPTS = [("Corner Cafe", [("Latte", 450), ("Bagel", 320)], 62, 50),
                ("Harbor Deli", [("Soup", 640), ("Roll", 210)], 68, 40),
                ("Pine Bakery", [("Scone", 375), ("Tea", 280)], 55, 70)]


def money(cents):
    return f"{cents // 100}.{cents % 100:02d}"


@case("D03")
def d03(seed, rng, prompt):
    shop, items, tax, bump = D03_RECEIPTS[seed % 3]
    old = sum(c for _, c in items) + tax
    ims = []
    for total in (old, old + bump):
        im = new(420, 560)
        d = ImageDraw.Draw(im)
        lines = [shop] + [f"{n} {money(c)}" for n, c in items] + [f"Tax {money(tax)}", f"Total {money(total)}"]
        for i, line in enumerate(lines):
            d.text((40, 50 + 80 * i), line, fill=INK, font=font("arial", 22))
        ims.append(im)
    return {"a.png": ims[0], "b.png": ims[1]}, {"old": old / 100, "new": (old + bump) / 100, "line": "Total"}, prompt


@case("D01")
def d01(seed, rng, prompt):
    return {"a.png": copy_png("f3-a.png"), "b.png": copy_png("f3-b.png")}, {"differences": 0}, prompt


@case("D04")
def d04(seed, rng, prompt):
    facts = [{"label_old": "Q3", "label_new": "Q5"}, {"bar_index": 3, "direction": "taller"}]
    return {"a.png": copy_png("f6-a.png"), "b.png": copy_png("f6-b.png")}, {"count": 2, "facts": facts}, prompt


@case("D05")
def d05(seed, rng, prompt):
    truth = {"text_changed": False, "theme": "light to dark"}
    return {"a.png": copy_png("f4-a.png"), "b.png": copy_png("f4-b.png")}, truth, prompt


@case("D06")
def d06(seed, rng, prompt):
    a = copy_png("f4-a.png")
    return {"a.png": a, "b.png": jpeg_roundtrip(a)}, {"differences": 0}, prompt


D07_SHIFTS = [("right", 24, 0), ("down", 20, 1), ("left", 30, 0)]


@case("D07")
def d07(seed, rng, prompt):
    direction, px, vertical = D07_SHIFTS[seed % 3]
    dx, dy = {"right": (px, 0), "left": (-px, 0), "down": (0, px), "up": (0, -px)}[direction]
    ims = []
    for ox, oy in ((0, 0), (dx, dy)):
        im = new(600, 300)
        d = ImageDraw.Draw(im)
        x, y = 220 + ox, 126 + oy
        d.rounded_rectangle((x, y, x + 160, y + 48), radius=6, fill=BLUE)
        centered(d, (x + 80, y + 24), "Continue", font("arial", 20), WHITE)
        ims.append(im)
    return {"a.png": ims[0], "b.png": ims[1]}, {"element": "Continue", "direction": direction, "px": px}, prompt


@case("H01")
def h01(seed, rng, prompt):
    color = [WHITE, (17, 24, 39), (245, 245, 245)][seed % 3]
    return {"image.png": new(800, 600, color)}, {"text": None, "background": list(color)}, prompt


@case("H02")
def h02(seed, rng, prompt):
    vals = bar_values(seed)
    return {"image.png": bar_chart(vals)}, {"absent": True, "wednesday_blue": vals[2]}, prompt


@case("H03")
def h03(seed, rng, prompt):
    try:
        import numpy as np
        arr = np.random.default_rng(seed).normal(128, 6, (600, 800, 3)).clip(0, 255).astype("uint8")
        im = Image.fromarray(arr, "RGB")
    except ImportError:
        im = new(800, 600, (128, 128, 128))
        px = im.load()
        for y in range(600):
            for x in range(800):
                px[x, y] = tuple(max(0, min(255, round(rng.gauss(128, 6)))) for _ in range(3))
    return {"image.png": im}, {"text": None, "sigma": 6}, prompt


@case("H04")
def h04(seed, rng, prompt):
    im, _ = buttons_image(seed)
    return {"image.png": im}, {"absent": True}, prompt


def rotate_pts(pts, deg, cx, cy):
    t = math.radians(deg)
    return [(cx + (x - cx) * math.cos(t) - (y - cy) * math.sin(t),
             cy + (x - cx) * math.sin(t) + (y - cy) * math.cos(t)) for x, y in pts]


def odd_index(case_id, seed, example):
    rng = random.Random(f"{case_id}-index")
    picks = [example]
    while len(picks) < 3:
        n = rng.randint(1, 12)
        if n not in picks:
            picks.append(n)
    return picks[seed % 3]


@case("O01")
def o01(seed, rng, prompt):
    idx = odd_index("O01", seed, 7)
    im = new(640, 480)
    d = ImageDraw.Draw(im)
    for i in range(12):
        r, c = divmod(i, 4)
        cx, cy = 80 + 160 * c, 80 + 160 * r
        box = (cx - 40, cy - 40, cx + 40, cy + 40)
        (d.rectangle if i + 1 == idx else d.ellipse)(box, fill=BLUE)
        centered(d, (cx, cy + 60), str(i + 1), font("arial", 14), INK)
    return {"image.png": im}, {"index": idx}, prompt


@case("O02")
def o02(seed, rng, prompt):
    idx = odd_index("O02", seed, 10)
    im = new(640, 480)
    d = ImageDraw.Draw(im)
    arrow = [(-35, -10), (8, -10), (8, -26), (38, 0), (8, 26), (8, 10), (-35, 10)]
    for i in range(12):
        r, c = divmod(i, 4)
        cx, cy = 80 + 160 * c, 80 + 160 * r
        pts = [(cx + x, cy + y) for x, y in arrow]
        if i + 1 == idx:
            pts = rotate_pts(pts, 12, cx, cy)
        d.polygon(pts, fill=INK)
    return {"image.png": im}, {"index": idx, "rotation_deg": 12}, prompt


@case("O03")
def o03(seed, rng, prompt):
    idx = odd_index("O03", seed, 4)
    odd_green = [106, 107, 105][seed % 3]
    im = new(640, 480)
    d = ImageDraw.Draw(im)
    for i in range(12):
        r, c = divmod(i, 4)
        cx, cy = 80 + 160 * c, 80 + 160 * r
        fill = (37, odd_green, 235) if i + 1 == idx else BLUE
        d.rectangle((cx - 50, cy - 50, cx + 50, cy + 50), fill=fill)
        centered(d, (cx, cy + 65), str(i + 1), font("arial", 14), INK)
    return {"image.png": im}, {"index": idx, "deltaE": delta_e(BLUE, (37, odd_green, 235))}, prompt


@case("O04")
def o04(seed, rng, prompt):
    meta = json.loads((RUG_DIR / "case.json").read_text())
    idx = meta["numbers"]["off_motif_index_from_left"]
    return {"image.png": Image.open(RUG_DIR / "image.png").convert("RGB")}, {"index": idx, "band_trap": [3, 4, 5]}, prompt



def build(case_id, seed, catalog_case):
    rng = random.Random(f"{case_id}:{seed}")
    builder = BUILDERS.get(case_id)
    if builder is None:
        raise ValueError(f"no generator implemented for {case_id}")
    return builder(seed, rng, catalog_case["prompt"])


def generate_one(case_id, seed, catalog_case, out_root=None):
    files, truth, prompt = build(case_id, seed, catalog_case)
    out = Path(out_root or FIXTURES) / case_id / f"s{seed}"
    out.mkdir(parents=True, exist_ok=True)
    for name, im in files.items():
        im.save(out / name, format="PNG", compress_level=9)
    (out / "truth.json").write_text(json.dumps(truth, indent=2, ensure_ascii=False) + "\n")
    (out / "prompt.txt").write_text(prompt.rstrip() + "\n")
    return out


def generate_all(cases=None, seeds=(0, 1, 2), out_root=None, catalog=None):
    by_id = case_map(catalog)
    chosen = list(cases or by_id)
    unknown = sorted(set(chosen) - set(by_id))
    if unknown:
        raise ValueError("unknown case ids: " + ", ".join(unknown))
    return [generate_one(cid, s, by_id[cid], out_root) for cid in chosen for s in seeds_for(cid, seeds)]


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--cases", help="comma-separated ids (default: all 42)")
    p.add_argument("--seeds", default="0,1,2")
    p.add_argument("--out", help="output root (default: probe/vision/fixtures)")
    p.add_argument("--catalog", help="alternate cases.json")
    a = p.parse_args()
    paths = generate_all(a.cases.split(",") if a.cases else None, tuple(int(s) for s in a.seeds.split(",")), a.out, a.catalog)
    print(f"wrote {len(paths)} fixture folders")


if __name__ == "__main__":
    main()
