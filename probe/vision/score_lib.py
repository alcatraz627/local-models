"""Answer extraction and normalisers shared by every scorer.

These turn a free-text model reply into comparable values (an integer, a colour,
a grid cell). Scorers compare those values to the generator's truth, never
keywords against a bag of words.
"""

import re
import unicodedata

UNITS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
        "seventy": 70, "eighty": 80, "ninety": 90}
ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
            "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "eleventh": 11,
            "twelfth": 12}

COLORS = {
    "red": ("red", "crimson", "scarlet"),
    "green": ("green", "lime green", "emerald"),
    "blue": ("blue", "royal blue", "azure", "cobalt"),
    "yellow": ("yellow", "gold", "golden"),
    "orange": ("orange", "amber"),
    "purple": ("purple", "violet"),
    "gray": ("gray", "grey", "silver"),
    "black": ("black",),
    "white": ("white",),
}
NEGATIONS = {"no", "not", "without", "none", "absent", "never", "nor", "neither",
             "isn't", "aren't", "doesn't", "don't", "didn't", "cannot", "can't",
             "won't", "nothing"}
ABSENT_STARTS = ("NONE", "ABSENT", "N/A", "NO SUCH", "NOT PRESENT", "NOTHING",
                 "NO TEXT", "NO DIFFERENCE", "NO VISIBLE", "NO CHANGE")
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
MONTH_NAMES = ["january", "february", "march", "april", "may", "june", "july",
               "august", "september", "october", "november", "december"]


def _nfkc(value):
    return unicodedata.normalize("NFKC", str(value if value is not None else ""))


def norm_str(value):
    """Upper-cased, whitespace-collapsed text with wrapping quotes and trailing punctuation removed."""
    text = re.sub(r"\s+", " ", _nfkc(value).upper()).strip()
    previous = None
    while previous != text:
        previous = text
        text = text.strip("\"'`*_ “”‘’")
        text = re.sub(r"[\s.,;:!?]+$", "", text)
    return text



def _words_to_ints(text):
    """Integers written as English words, 'twenty-three' and 'four hundred twelve' included."""
    found, total, last = [], 0, None

    def flush():
        nonlocal total, last
        if last is not None:
            found.append(total)
        total, last = 0, None

    for word in re.findall(r"[a-z]+", text.lower()):
        if word in UNITS:
            if last in ("unit",):
                flush()
            total += UNITS[word]
            last = "unit"
        elif word in TENS:
            if last in ("unit", "tens"):
                flush()
            total += TENS[word]
            last = "tens"
        elif word == "hundred" and last == "unit" and 1 <= total <= 9:
            total *= 100
            last = "hundred"
        elif word == "and" and last == "hundred":
            continue
        else:
            flush()
    flush()
    return found


def _digit_tokens(text):
    text = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", _nfkc(text))
    return re.findall(r"(?<![A-Za-z0-9_.])\d+(?:\.\d+)?", text)


def to_int(value, ordinals=False):
    """Set of distinct integers in the text, digits or number words.

    With ordinals=True, "ninth" counts as 9. That is for answers that name a
    position in a row; in running prose "first" and "second" are not numbers.
    """
    out = set()
    for tok in _digit_tokens(value):
        if "." not in tok:
            out.add(int(tok))
    out.update(_words_to_ints(_nfkc(value)))
    if ordinals:
        for word in re.findall(r"[a-z]+", _nfkc(value).lower()):
            if word in ORDINALS:
                out.add(ORDINALS[word])
    return out


def to_num(value):
    """Set of distinct numbers (decimals allowed). Currency and unit suffixes fall away."""
    out = set()
    for tok in _digit_tokens(value):
        out.add(float(tok) if "." in tok else int(tok))
    out.update(_words_to_ints(_nfkc(value)))
    return out



def _word_hit(text, name):
    return re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", text) is not None


def color_of(value):
    text = _nfkc(value).lower()
    return {canon for canon, names in COLORS.items() if any(_word_hit(text, n) for n in names)}


_VERT = {"top": "top", "upper": "top", "north": "top", "up": "top",
         "bottom": "bottom", "lower": "bottom", "south": "bottom", "down": "bottom"}
_HORIZ = {"left": "left", "west": "left", "right": "right", "east": "right"}
_CENTER = {"center", "centre", "middle", "central"}
_ABBR = {"nw": "top-left", "ne": "top-right", "sw": "bottom-left", "se": "bottom-right"}


def pos_of(value):
    """Set of canonical positions (top-left, top, ..., bottom-right) named in the text."""
    text = _nfkc(value).lower().replace("-", " ").replace("_", " ")
    found = set()
    for clause in re.split(r"[,;/]|\band\b|\bor\b", text):
        words = re.findall(r"[a-z]+", clause)
        v = next((_VERT[w] for w in words if w in _VERT), None)
        h = next((_HORIZ[w] for w in words if w in _HORIZ), None)
        if v and h:
            found.add(f"{v}-{h}")
        elif v:
            found.add(v)
        elif h:
            found.add(h)
        elif any(w in _CENTER for w in words):
            found.add("center")
        for w in words:
            if w in _ABBR:
                found.add(_ABBR[w])
    return found


def cell_of(value):
    """Set of (row, col) pairs, 1-based: r3c2, row 3 col 2, (3,2), third row second column."""
    text = _nfkc(value).lower()
    for word, n in ORDINALS.items():
        text = re.sub(r"\b" + word + r"\b", str(n), text)
    for word, n in UNITS.items():
        if 1 <= n <= 10:
            text = re.sub(r"\b" + word + r"\b", str(n), text)
    found = set()
    ordn = r"(\d+)(?:st|nd|rd|th)?"
    for r, c in re.findall(r"\br\s*(\d+)\s*,?\s*c\s*(\d+)\b", text):
        found.add((int(r), int(c)))
    for r, c in re.findall(r"\brow\s*#?" + ordn + r"\W+(?:and\W+)?(?:column|col)\s*#?" + ordn, text):
        found.add((int(r), int(c)))
    for c, r in re.findall(r"\b(?:column|col)\s*#?" + ordn + r"\W+(?:and\W+)?row\s*#?" + ordn, text):
        found.add((int(r), int(c)))
    for r, c in re.findall(ordn + r"\s+row\W+(?:and\W+)?" + ordn + r"\s+col(?:umn)?\b", text):
        found.add((int(r), int(c)))
    for c, r in re.findall(ordn + r"\s+col(?:umn)?\W+(?:and\W+)?" + ordn + r"\s+row\b", text):
        found.add((int(r), int(c)))
    for r, c in re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", text):
        found.add((int(r), int(c)))
    return found


def month_of(value):
    """Set of 3-letter month codes named in the text."""
    text = _nfkc(value).lower()
    found = set()
    for short, name in zip(MONTHS, MONTH_NAMES):
        if _word_hit(text, name) or _word_hit(text, short):
            found.add(short)
    return found


def direction_of(value):
    text = _nfkc(value).lower()
    found = set()
    if re.search(r"\bright(?:ward|wards)?\b", text):
        found.add("right")
    if re.search(r"\bleft(?:ward|wards)?\b", text):
        found.add("left")
    if re.search(r"\b(?:up|upward|upwards|above)\b", text):
        found.add("up")
    if re.search(r"\b(?:down|downward|downwards|below)\b", text):
        found.add("down")
    return found



def mentions(text, term):
    """True when `term` appears and is not negated (no/not/without... within 4 tokens, same sentence)."""
    tokens = re.findall(r"[\w'-]+|[.;:!?\n]", _nfkc(text).lower())
    target = re.findall(r"[\w'-]+", str(term).lower())
    if not target:
        return False
    for i in range(len(tokens) - len(target) + 1):
        if tokens[i:i + len(target)] != target:
            continue
        negated = False
        for tok in reversed(tokens[max(0, i - 4):i]):
            if tok in ".;:!?\n":
                break
            if tok in NEGATIONS:
                negated = True
                break
        if not negated:
            return True
    return False


def absent_answer(value):
    """True for NONE / ABSENT / 'there is no ...' answers that carry no number and no quoted string."""
    text = norm_str(value)
    if not text:
        return False
    nums = to_num(text)
    if nums and nums != {0}:
        return False
    if re.search(r"""["'`“‘].+?["'`”’]""", _nfkc(value)):
        return False
    if any(re.match(re.escape(s) + r"(?![A-Z0-9])", text) for s in ABSENT_STARTS):
        return True
    return bool(re.match(r"(THERE\s+(IS|ARE)\s+NO\b|NO\s+[A-Z]+\s+(SERIES|BUTTON|TEXT)\b)", text))



# Models put the marker mid-line ("... checked. ANSWER: X") or shorten it to
# "ANS:"; both still follow the contract, so both count. Only the last one wins.
ANSWER_RE = re.compile(r"(?:^|[\s*_`(>])ANS(?:WER)?\W{0,3}[:：]\s*(.+)$", re.IGNORECASE)


def answer_line(reply):
    """The last 'ANSWER: ...' (or 'ANS:') value with markdown stars and backticks removed, or None."""
    last = None
    for line in str(reply or "").splitlines():
        for m in ANSWER_RE.finditer(line.strip()):
            value = re.sub(r"</?answer>", "", m.group(1), flags=re.I)
            value = value.strip().strip("*`_ <>").strip()
            if value:
                last = value
    return last


def extract_answer(reply, cands=None):
    """Return (answer, source). source is answer_line, fallback or format_fail.

    Without an ANSWER line the whole reply is accepted only if `cands(reply)`
    finds exactly one candidate; two or more, or none, is a format failure.
    """
    line = answer_line(reply)
    if line is not None:
        return line, "answer_line"
    text = str(reply or "").strip()
    if not text or cands is None:
        return "", "format_fail"
    if len(cands(text)) == 1:
        return text, "fallback"
    return "", "format_fail"


def levenshtein(a, b):
    row = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        nxt = [i]
        for j, cb in enumerate(b, 1):
            nxt.append(min(nxt[-1] + 1, row[j] + 1, row[j - 1] + (ca != cb)))
        row = nxt
    return row[-1]
