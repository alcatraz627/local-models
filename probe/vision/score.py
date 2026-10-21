#!/usr/bin/env python3
"""Score one model reply against one generated fixture's truth.

Every case has its own scorer, registered by id. A scorer reads the truth
dict, so changing the truth changes the verdict (selftest proves this).
Result status is `pass`, `fail` or `format_fail`; `flags` records the named
failure shapes from the catalog (answered_decoy, band_trap, and so on).
"""

import argparse
import json
import re
from pathlib import Path

from common import case_dir
from score_lib import (absent_answer, cell_of, color_of, direction_of, extract_answer,
                       levenshtein, month_of, norm_str, pos_of, to_int, to_num)


class Spec:
    def __init__(self, fn, cands=None, key=None, raw=False):
        self.fn, self.cands, self.key, self.raw = fn, cands, key, raw


SPECS = {}


def scorer(*ids, cands=None, key=None, raw=False):
    def wrap(fn):
        for cid in ids:
            SPECS[cid] = Spec(fn, cands, key, raw)
        return fn
    return wrap


# ---- candidate finders used for the no-ANSWER-line fallback

def _vocab(*words):
    def find(text):
        up = norm_str(text)
        return {w for w in words if re.search(r"(?<![A-Z0-9])" + re.escape(w.upper()) + r"(?![A-Z0-9])", up)}
    return find


def _regex(pattern):
    def find(text):
        return {re.sub(r"\s+", " ", m).strip() for m in re.findall(pattern, norm_str(text))}
    return find


def _letters(text):
    found = set(re.findall(r"(?<![A-Za-z])[A-E](?![A-Za-z])", str(text)))
    bare = str(text).strip().strip("`*'\". ")
    if re.fullmatch(r"[a-eA-E]", bare):
        found.add(bare.upper())
    return found


def _int_cands(text):
    return to_int(text)


_ABSENCE_WORDS = re.compile(r"\b(NONE|ABSENT|NOTHING|N/A|NO SUCH|NOT PRESENT|THERE (?:IS|ARE) NO|NO (?:[A-Z]+ )?(?:SERIES|BUTTON|TEXT|DIFFERENCES?|CHANGES?))\b")


def _absent_or(extra):
    """Candidates for a no-ANSWER-line reply: an absence claim, plus whatever `extra` finds."""
    def find(text):
        found = {str(x) for x in extra(text)}
        if absent_answer(text) or _ABSENCE_WORDS.search(norm_str(text)):
            found.add("ABSENT")
        return found
    return find


_nothing = lambda text: set()
_cands_text_absent = _absent_or(_nothing)
_cands_number_absent = _absent_or(to_num)
_cands_color_absent = _absent_or(color_of)
_cands_count_absent = _absent_or(to_int)


_PAIR = r"\$?(\d+(?:\.\d+)?)\s*(?:->|→|=>|\bto\b)\s*\$?(\d+(?:\.\d+)?)"


def _pairs(text):
    return {(float(a), float(b)) for a, b in re.findall(_PAIR, str(text), re.I)}


def _shapes(text):
    return _vocab("circle", "square")(text)


def _yesno(text):
    return _vocab("YES", "NO")(text)


# ---- counting

@scorer("C01", "C02", "C03", "C04", cands=_int_cands, key=None)
def _count(a, truth, flags, raw):
    ints = to_int(a)
    expected = truth.get("count", truth.get("rows"))
    if "decoys" in truth and ints == {expected + truth["decoys"]}:
        flags["decoy_counted"] = True
    if "total" in truth and ints == {truth["total"]}:
        flags["answered_total"] = True
    if "rows" in truth and ints == {truth["rows"] + 1}:
        flags["counted_header"] = True
    if len(ints) == 1:
        flags["abs_err"] = abs(next(iter(ints)) - expected)
    return ints == {expected}, f"counted {sorted(ints)}, expected {expected}"


# ---- reading text

@scorer("T01", cands=_regex(r"[A-Z0-9]{3}-[A-Z0-9]{4}(?:-[0-9]{4})?"), key="text")
def _t01(a, truth, flags, raw):
    expected = norm_str(truth["text"]).replace(" ", "")
    found = _regex(r"[A-Z0-9]{3}-[A-Z0-9]{4}(?:-[0-9]{4})?")(a)
    got = norm_str(a).replace(" ", "")
    ok = got == expected or found == {expected}
    flags["edit_distance"] = levenshtein(next(iter(found)) if len(found) == 1 else got, expected)
    return ok, f"id {sorted(found) or got!r}, expected {expected}"


@scorer("T02", cands=_regex(r"INVOICE\s+[0-9A-Z]{2}-[0-9A-Z]{4}\s+DUE\s+[0-9A-Z]{1,2}\s+[A-Z]{3}"), key="text")
def _t02(a, truth, flags, raw):
    expected = re.sub(r"\s+", " ", norm_str(truth["text"]))
    got = re.sub(r"\s+", " ", norm_str(a))
    found = _regex(r"INVOICE\s+[0-9A-Z]{2}-[0-9A-Z]{4}\s+DUE\s+[0-9A-Z]{1,2}\s+[A-Z]{3}")(a)
    flags["edit_distance"] = levenshtein(next(iter(found)) if len(found) == 1 else got, expected)
    return got == expected or found == {expected}, f"line {sorted(found) or got!r}, expected {expected}"


def _two_line_text(a, truth, flags, raw):
    expected = re.sub(r"\s+", " ", norm_str(truth["text"]))
    found = _regex(r"[A-Z]{4,8}\s?\d{4}")(a)
    got = re.sub(r"\s+", " ", norm_str(a))
    decoy = norm_str(truth.get("decoy", ""))
    if decoy and decoy in found and expected not in found:
        flags["answered_decoy"] = True
    return got == expected or found == {expected}, f"text {sorted(found) or got!r}, expected {expected}"


scorer("T04", cands=_regex(r"[A-Z]{4,8}\s?\d{4}"), key="text")(_two_line_text)
scorer("T05", cands=_regex(r"[A-Z]{4,8}\s?\d{4}"), key="text")(_two_line_text)


@scorer("T03", raw=True, key="tokens")
def _t03(a, truth, flags, raw):
    toks = set(re.findall(r"[A-Z0-9]+", norm_str(raw)))
    missing = sorted(set(truth["tokens"]) - toks)
    for real in truth.get("autocorrect_traps", {}).values():
        if real in toks:
            flags.setdefault("autocorrected", []).append(real)
    flags["recall"] = round(1 - len(missing) / max(1, len(truth["tokens"])), 3)
    return not missing, f"missing tokens {missing}"


def _strip_transcript(raw):
    lines = []
    for line in str(raw).splitlines():
        s = line.strip()
        if not s or s.startswith("```") or re.match(r"^\W*ANSWER\W*[:：]", s, re.I):
            continue
        s = re.sub(r"^(?:[-*•]\s+|\d+[.)]\s+)", "", s)
        if s.endswith(":") and len(s) < 60:
            continue
        lines.append(s)
    return " ".join(lines)


@scorer("T06", raw=True, key="lines")
def _t06(a, truth, flags, raw):
    got = norm_str(_strip_transcript(raw))
    want = norm_str(" ".join(truth["lines"]))
    cer = levenshtein(got, want) / max(1, len(want))
    flags["cer"] = round(cer, 4)
    return cer <= 0.01, f"character error rate {cer:.4f} (limit 0.01)"


# ---- spatial and colour

@scorer("S01", cands=_shapes, key="left")
def _s01(a, truth, flags, raw):
    found = _shapes(a)
    return found == {truth["left"]}, f"shape {sorted(found)}, expected {truth['left']}"


@scorer("S02", cands=_letters, key="letter")
def _s02(a, truth, flags, raw):
    found = _letters(a)
    return found == {truth["letter"].upper()}, f"box {sorted(found)}, expected {truth['letter']}"


@scorer("S03", cands=pos_of, key="position")
def _s03(a, truth, flags, raw):
    found = pos_of(a)
    return found == {truth["position"]}, f"position {sorted(found)}, expected {truth['position']}"


@scorer("S04", key="order")
def _s04(a, truth, flags, raw):
    seq = []
    for part in re.split(r"[,;>/]|->|→|\band\b|\bthen\b", a):
        cols = color_of(part)
        if len(cols) == 1:
            seq.append(next(iter(cols)))
        elif len(cols) > 1:
            seq.append(None)
    return seq == truth["order"], f"order {seq}, expected {truth['order']}"


@scorer("K03", cands=color_of, key="ink")
def _k03(a, truth, flags, raw):
    cols = color_of(a)
    if truth.get("prior") in cols and truth["ink"] not in cols:
        flags["answered_prior"] = True
    return cols == {truth["ink"]}, f"ink {sorted(cols)}, expected {truth['ink']}"


# ---- charts and tables

@scorer("G01", cands=to_num, key="value")
def _g01(a, truth, flags, raw):
    nums = to_num(a)
    tol = truth.get("tol", 3)
    ok = len(nums) == 1 and abs(next(iter(nums)) - truth["value"]) <= tol
    return ok, f"value {sorted(nums)}, expected {truth['value']} +/- {tol}"


@scorer("G03", cands=month_of, key="month")
def _g03(a, truth, flags, raw):
    found = month_of(a)
    return found == month_of(truth["month"]), f"month {sorted(found)}, expected {truth['month']}"


@scorer("G04", key="tallest")
def _g04(a, truth, flags, raw):
    up = norm_str(a)
    tall = re.search(r"TALLEST(?:\s+BAR)?\W{0,4}(Q\d)", up)
    short = re.search(r"SHORTEST(?:\s+BAR)?\W{0,4}(Q\d)", up)
    got = (tall and tall.group(1), short and short.group(1))
    ok = got == (truth["tallest"], truth["shortest"])
    return ok, f"tallest/shortest {got}, expected {(truth['tallest'], truth['shortest'])}"


@scorer("B01", cands=_int_cands, key="value")
def _b01(a, truth, flags, raw):
    ints = to_int(a)
    if ints & set(truth.get("neighbor_values", [])) and ints != {truth["value"]}:
        flags["row_off_by_one"] = True
    return ints == {truth["value"]}, f"units {sorted(ints)}, expected {truth['value']}"


@scorer("B02", cands=_vocab("OPEN", "HOLD", "DONE", "VOID"), key="value")
def _b02(a, truth, flags, raw):
    found = _vocab("OPEN", "HOLD", "DONE", "VOID")(a)
    return found == {norm_str(truth["value"])}, f"status {sorted(found)}, expected {truth['value']}"


@scorer("R01", cands=to_num, key="value")
def _r01(a, truth, flags, raw):
    nums = to_num(a)
    if truth.get("decoy") in nums and truth["value"] not in nums:
        flags["answered_decoy"] = True
    return nums == {truth["value"]}, f"latency {sorted(nums)}, expected {truth['value']}"


@scorer("U07", cands=to_int, key="value")
def _u07(a, truth, flags, raw):
    want = truth["value"]
    if want.isdigit():
        return to_int(a) == {int(want)}, f"badge {sorted(to_int(a))}, expected {want}"
    got = norm_str(a).replace(" ", "")
    return got in (want, want.replace("+", "PLUS")), f"badge {got!r}, expected {want}"


# ---- UI state

def _labels(a):
    parts = re.split(r"[,;\n]|\band\b", a)
    return {re.sub(r"[^A-Z0-9]", "", norm_str(re.sub(r"^[-*•\d.)\s]+", "", p))) for p in parts} - {""}


@scorer("U01", key="checked")
def _u01(a, truth, flags, raw):
    got = _labels(a)
    want = {re.sub(r"[^A-Z0-9]", "", norm_str(x)) for x in truth["checked"]}
    return got == want, f"checked {sorted(got)}, expected {sorted(want)}"


@scorer("U02", cands=_vocab("Save", "Export", "Delete"), key="disabled")
def _u02(a, truth, flags, raw):
    found = _vocab("Save", "Export", "Delete")(a)
    return found == {truth["disabled"]}, f"disabled {sorted(found)}, expected {truth['disabled']}"


@scorer("U03", cands=_vocab("Overview", "Logs", "Metrics", "Alerts", "Settings"), key="selected")
def _u03(a, truth, flags, raw):
    found = _vocab("Overview", "Logs", "Metrics", "Alerts", "Settings")(a)
    return found == {truth["selected"]}, f"tab {sorted(found)}, expected {truth['selected']}"


def _ui_payload(reply, data):
    if isinstance(data, dict):
        return data
    try:
        loaded = json.loads(reply) if isinstance(reply, str) else reply
    except ValueError:
        # same fallback as see's .data: the outermost {...} span, for fenced replies
        s = reply if isinstance(reply, str) else ""
        a, b = s.find("{"), s.rfind("}")
        try:
            loaded = json.loads(s[a:b + 1]) if 0 <= a < b else None
        except ValueError:
            return None
    return loaded if isinstance(loaded, dict) else None


def _elements(payload):
    elems = []
    for region in payload.get("regions", []) or []:
        elems.extend(region.get("elements", []) or [])
    elems.extend(payload.get("elements", []) or [])
    return [e if isinstance(e, dict) else {"text": str(e)} for e in elems]


def _state_of(state):
    s = norm_str(state)
    if re.search(r"\b(OFF|DISABLED|UNCHECKED|INACTIVE|FALSE|NOT CHECKED|UNTICKED|EMPTY)\b", s):
        return "off"
    if re.search(r"\b(ON|ENABLED|CHECKED|ACTIVE|TRUE|TICKED|SELECTED)\b", s):
        return "on"
    return None


@scorer("U04", raw=True, key=None)
def _u04(a, truth, flags, raw):
    payload, elems = raw
    # A model may give a row as a label element plus a separate, textless toggle
    # element in the same region; that toggle's state belongs to the label.
    regions = [[e for e in (r.get("elements") or []) if isinstance(e, dict)]
               for r in (payload or {}).get("regions", []) or [] if isinstance(r, dict)]
    found = {}
    for label, want in [(x, "on") for x in truth["on"]] + [(x, "off") for x in truth["off"]]:
        states = [_state_of(e.get("state", "")) for e in elems if norm_str(label) in norm_str(e.get("text", ""))]
        for reg in regions:
            if any(norm_str(label) in norm_str(e.get("text", "")) for e in reg):
                states += [_state_of(e.get("state", "")) for e in reg
                           if not norm_str(e.get("text", "")) and re.search(r"TOGGLE|SWITCH|CHECKBOX", norm_str(e.get("type", "")))]
        states = [s for s in states if s]
        found[label] = bool(states) and want in states and not ({"on", "off"} - {want}) & set(states)
    flags["labels"] = found
    return all(found.values()), f"toggle states {found}"


_TYPE_SYNONYMS = {
    "input": {"input", "text field", "textbox", "text box", "field", "textfield"},
    "link": {"link", "hyperlink"},
    "button": {"button"},
    "checkbox": {"checkbox", "check box"},
}
_NEUTRAL_TYPES = {"heading", "title", "label", "text", "image", "icon", "header", "logo"}


def _same_text(want, got):
    w, g = norm_str(want), norm_str(got)
    return bool(g) and (w == g or w in g or (len(g) >= 3 and g in w))


@scorer("U06", raw=True, key=None)
def _u06(a, truth, flags, raw):
    payload, elems = raw
    wanted = truth["elements"]
    neutral = [norm_str(x) for x in truth.get("neutral", [])]
    interactive = [e for e in elems
                   if norm_str(e.get("text", "")) not in neutral
                   and norm_str(e.get("type", "")) not in {t.upper() for t in _NEUTRAL_TYPES}
                   and norm_str(e.get("text", ""))]
    matched = [w for w in wanted if any(_same_text(w["text"], e.get("text", "")) for e in elems)]
    good_got = [e for e in interactive if any(_same_text(w["text"], e.get("text", "")) for w in wanted)]
    recall = len(matched) / max(1, len(wanted))
    precision = len(good_got) / len(interactive) if interactive else 0.0
    state_ok, typed = True, 0
    for w in wanted:
        rows = [e for e in elems if _same_text(w["text"], e.get("text", ""))]
        if rows and norm_str(rows[0].get("type", "")) in {t.upper() for t in _TYPE_SYNONYMS.get(w["type"], ())}:
            typed += 1
        if "state" in w:
            seen = {_state_of(e.get("state", "")) for e in rows}
            if w["state"] == "checked":
                state_ok &= "on" in seen
            else:
                state_ok &= "on" not in seen
    flags.update(recall=round(recall, 3), precision=round(precision, 3), type_acc=round(typed / max(1, len(matched)), 3),
                 hallucinated=[e.get("text") for e in interactive if e not in good_got])
    ok = recall >= 0.9 and precision >= 0.9 and state_ok
    return ok, f"inventory recall {recall:.2f}, precision {precision:.2f}, checkbox state ok {state_ok}"


# ---- diff cases

@scorer("D01", "D06", cands=_cands_count_absent, key="differences")
def _d01(a, truth, flags, raw):
    n = truth["differences"]
    if n == 0:
        return absent_answer(a) or to_int(a) == {0}, "expected no differences"
    return to_int(a) == {n}, f"expected {n} differences"


@scorer("D02", cands=cell_of, key="cell")
def _d02(a, truth, flags, raw):
    found = cell_of(a)
    return found == {tuple(truth["cell"])}, f"cell {sorted(found)}, expected {truth['cell']}"


@scorer("D03", cands=_pairs, key="old")
def _d03(a, truth, flags, raw):
    pairs = _pairs(a)
    want = (float(truth["old"]), float(truth["new"]))
    if pairs == {(want[1], want[0])}:
        flags["swapped"] = True
    return pairs == {want}, f"change {sorted(pairs)}, expected {want}"


@scorer("D04", key="count")
def _d04(a, truth, flags, raw):
    bullets = [norm_str(x.strip()[1:]) for x in str(raw).splitlines() if re.match(r"\s*[-*•]\s", x)]
    relabel = any("Q3" in b and "Q5" in b for b in bullets)
    grew = any(re.search(r"(THIRD|3RD|Q3|Q5).*(TALLER|HIGHER|INCREASED|GREW)|(TALLER|HIGHER|INCREASED|GREW).*(THIRD|3RD|Q3|Q5)", b)
               for b in bullets)
    ok = to_int(a) == {truth["count"]} and relabel and grew
    return ok, f"count {sorted(to_int(a))}, relabel bullet {relabel}, taller bullet {grew}"


@scorer("D05", cands=_yesno, key="text_changed")
def _d05(a, truth, flags, raw):
    m = re.match(r"(YES|NO)\b", norm_str(a))
    want = "YES" if truth["text_changed"] else "NO"
    return bool(m) and m.group(1) == want, f"answered {m and m.group(1)}, expected {want}"


@scorer("D07", cands=direction_of, key="direction")
def _d07(a, truth, flags, raw):
    dirs = direction_of(a)
    named = norm_str(truth["element"]) in norm_str(a)
    return named and dirs == {truth["direction"]}, f"named element {named}, direction {sorted(dirs)}, expected {truth['direction']}"


# ---- hallucination traps (each pairs the absence check with a positive answer)

@scorer("H01", "H03", cands=_cands_text_absent, key="text")
def _h01(a, truth, flags, raw):
    if truth.get("text") is None:
        return absent_answer(a), "expected an explicit NONE"
    return norm_str(a) == norm_str(truth["text"]), "expected the transcription"


@scorer("H02", cands=_cands_number_absent, key="absent")
def _h02(a, truth, flags, raw):
    if truth.get("absent"):
        return absent_answer(a), "expected ABSENT, a number fails even if it matches the blue series"
    return to_num(a) == {truth.get("value")}, "expected the value"


@scorer("H04", cands=_cands_color_absent, key="absent")
def _h04(a, truth, flags, raw):
    if truth.get("absent"):
        return absent_answer(a), "expected ABSENT, there is no Cancel button"
    return color_of(a) == {truth.get("color")}, "expected the colour"


# ---- odd one out

@scorer("O01", "O02", "O03", "O04", cands=_int_cands, key="index")
def _odd(a, truth, flags, raw):
    ints = to_int(a, ordinals=True)
    if ints & set(truth.get("band_trap", [])) and ints != {truth["index"]}:
        flags["band_trap"] = True
    return ints == {truth["index"]}, f"item {sorted(ints)}, expected {truth['index']}"


BLANK_READ_MUST_NOT = ["button", "chart", "logo", "menu", "icon", "lorem", "title"]


def score_blank_read(reply):
    """Companion check for H01: a plain `see IMG` read of a blank image should invent none of these things.

    Reported but never gated, because the default read prompt asks for structure.
    An empty reply fails, so silence cannot pass.
    """
    from score_lib import mentions
    if not str(reply or "").strip():
        return {"status": "format_fail", "why": "empty reply", "flags": {}, "answer": "", "source": "reply"}
    invented = [w for w in BLANK_READ_MUST_NOT if mentions(reply, w)]
    return {"status": "fail" if invented else "pass", "why": f"invented {invented}" if invented else "nothing invented",
            "flags": {"invented": invented}, "answer": "", "source": "reply"}


# C0x scorers read different truth keys, so name the mutation target per case.
MUTATION_KEY = {"C01": "count", "C02": "count", "C03": "count", "C04": "rows"}


def mutation_key(case_id):
    return MUTATION_KEY.get(case_id) or SPECS[case_id].key


def score(case_id, reply, truth, data=None):
    """Score `reply` (and, for ui-json cases, `data`) against `truth`."""
    spec = SPECS.get(case_id)
    if spec is None:
        return {"status": "fail", "why": f"no scorer registered for {case_id}", "flags": {}, "answer": "", "source": ""}
    flags = {}
    text = reply if isinstance(reply, str) else json.dumps(reply, ensure_ascii=False)
    if case_id in ("U04", "U06"):
        payload = _ui_payload(reply, data)
        if payload is None or not _elements(payload):
            return {"status": "format_fail", "why": "no structured elements in .data", "flags": flags, "answer": "", "source": ""}
        ok, why = spec.fn("", truth, flags, (payload, _elements(payload)))
        return {"status": "pass" if ok else "fail", "why": why, "flags": flags, "answer": "", "source": "data"}
    if not text.strip():
        return {"status": "format_fail", "why": "empty reply", "flags": flags, "answer": "", "source": "format_fail"}
    if spec.raw:
        ok, why = spec.fn(text, truth, flags, text)
        return {"status": "pass" if ok else "fail", "why": why, "flags": flags, "answer": "", "source": "reply"}
    answer, source = extract_answer(text, spec.cands)
    if source == "format_fail":
        return {"status": "format_fail", "why": "no ANSWER line and not exactly one candidate in the reply",
                "flags": flags, "answer": "", "source": source}
    ok, why = spec.fn(answer, truth, flags, text)
    return {"status": "pass" if ok else "fail", "why": why, "flags": flags, "answer": answer, "source": source}


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("case")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--reply", help="reply text, or a path to a file holding it")
    p.add_argument("--truth", help="truth.json path (default: the generated fixture's)")
    p.add_argument("--data", help="path to the .data JSON for ui-json cases")
    a = p.parse_args()
    truth = json.loads(Path(a.truth or case_dir(a.case, a.seed) / "truth.json").read_text())
    reply = a.reply or ""
    if reply and Path(reply).is_file():
        reply = Path(reply).read_text()
    data = json.loads(Path(a.data).read_text()) if a.data else None
    print(json.dumps(score(a.case, reply, truth, data), ensure_ascii=False))


if __name__ == "__main__":
    main()
