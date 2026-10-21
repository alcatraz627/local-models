#!/usr/bin/env python3
"""Model-free checks for the vision harness: generation, truth, baselines and scorers.

No model runs here. Every scorer is shown to pass the right answer, fail the
wrong ones, refuse an empty reply, and to read its truth (a corrupted truth
turns the same right answer into a failure). Exit 0 means all checks passed.

    .venv/bin/python probe/vision/selftest.py
"""

import json
import shutil
import tempfile
from pathlib import Path

from baselines import baseline_cases, run_baseline
from common import ROOT, case_dir, load_cases, seeds_for
from gen import generate_all
from score import SPECS, mutation_key, score
from score_lib import (absent_answer, cell_of, color_of, mentions, month_of, norm_str, pos_of, to_int, to_num)

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))


def tree_bytes(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(Path(root).rglob("*")) if p.is_file()}


def read_truth(root, cid, seed):
    return json.loads((case_dir(cid, seed, root) / "truth.json").read_text())


# ---- a correct reply built from any seed's truth, and a way to corrupt that truth

def ui_data(elements):
    return {"regions": [{"name": "page", "elements": elements}]}


def good_reply(cid, t):
    """(reply, data) that is correct for truth t."""
    a = lambda s: (f"ANSWER: {s}", None)
    if cid in ("C01", "C02", "C03"):
        return a(t["count"])
    if cid == "C04":
        return a(t["rows"])
    if cid in ("T01", "T02", "T04", "T05"):
        return a(t["text"])
    if cid == "T03":
        return (" ".join(t["tokens"]), None)
    if cid == "T06":
        return ("\n".join(t["lines"]) + "\nANSWER: DONE", None)
    if cid == "S01":
        return a(t["left"])
    if cid == "S02":
        return a(t["letter"])
    if cid == "S03":
        return a(t["position"])
    if cid == "S04":
        return a(", ".join(t["order"]))
    if cid == "K03":
        return a(t["ink"])
    if cid == "G01":
        return a(t["value"])
    if cid == "G03":
        return a(t["month"])
    if cid == "G04":
        return a(f"tallest={t['tallest']}, shortest={t['shortest']}")
    if cid == "B01":
        return a(t["value"])
    if cid == "B02":
        return a(t["value"])
    if cid == "U01":
        return a(", ".join(t["checked"]))
    if cid == "U02":
        return a(t["disabled"])
    if cid == "U03":
        return a(t["selected"])
    if cid == "U04":
        states = [{"text": x, "state": "on"} for x in t["on"]] + [{"text": x, "state": "off"} for x in t["off"]]
        return ("", ui_data(states))
    if cid == "U06":
        return ("", ui_data([dict(e) for e in t["elements"]]))
    if cid == "U07":
        return a(t["value"])
    if cid == "R01":
        return a(f"{t['value']} ms")
    if cid in ("D01", "D06", "H01", "H03"):
        return a("NONE")
    if cid in ("H02", "H04"):
        return a("ABSENT")
    if cid == "D02":
        return a(f"r{t['cell'][0]}c{t['cell'][1]}")
    if cid == "D03":
        return a(f"{t['old']:.2f} -> {t['new']:.2f}")
    if cid == "D04":
        return ("- Q3 changed to Q5\n- The third bar grew taller\nANSWER: 2", None)
    if cid == "D05":
        return a("NO")
    if cid == "D07":
        return a(f"{t['element']} moved {t['direction']}")
    if cid in ("O01", "O02", "O03", "O04"):
        return a(t["index"])
    raise KeyError(cid)


def corrupt(cid, t):
    """A copy of truth t with its answer field changed to something else."""
    t = json.loads(json.dumps(t))
    if cid == "U04":
        t["on"], t["off"] = t["off"], t["on"]
        return t
    if cid == "U06":
        for e in t["elements"]:
            if e.get("state") == "checked":
                e["state"] = "unchecked"
        return t
    key = mutation_key(cid)
    v = t[key]
    if v is None:
        t[key] = "ZZZ"
    elif isinstance(v, bool):
        t[key] = not v
    elif isinstance(v, (int, float)):
        t[key] = v + 10
    elif isinstance(v, str):
        t[key] = v + "ZZZ"
    elif v and isinstance(v[0], str):
        t[key] = [v[0] + "XXXXXX"] + v[1:]
    else:
        t[key] = [v[0] + 1] + v[1:]
    return t


def type_matches(want, got):
    if isinstance(want, bool) or isinstance(got, bool):
        return isinstance(want, bool) and isinstance(got, bool)
    if isinstance(want, (int, float)):
        return isinstance(got, (int, float))
    if want is None:
        return got is None
    return type(want) is type(got)


def main():
    cases = load_cases()
    ids = [c["id"] for c in cases]
    tmp = Path(tempfile.mkdtemp(prefix="vision-selftest-"))
    try:
        a, b = tmp / "a", tmp / "b"
        generate_all(out_root=a)
        generate_all(out_root=b)
        check(f"gen: all {len(ids)} cases build", len(list(a.glob("*"))) == len(ids))
        check("gen deterministic: two full runs are byte-identical", tree_bytes(a) == tree_bytes(b))

        bad = []
        for c in cases:
            for seed in seeds_for(c["id"]):
                folder = case_dir(c["id"], seed, a)
                names = {p.name for p in folder.iterdir()}
                need = {"a.png", "b.png"} if c["mode"] == "diff" else {"image.png"}
                if not need <= names or not {"truth.json", "prompt.txt"} <= names:
                    bad.append(f"{c['id']} s{seed} files {sorted(names)}")
                    continue
                truth = json.loads((folder / "truth.json").read_text())
                if not isinstance(truth, dict):
                    bad.append(f"{c['id']} s{seed} truth is not an object")
                    continue
                for k, want in c["truth"].items():
                    if k not in truth or not type_matches(want, truth[k]):
                        bad.append(f"{c['id']} s{seed} truth key {k}")
        check("truth.json parses and matches the catalog schema for every case and seed", not bad, "; ".join(bad[:5]))

        prompts = []
        for c in cases:
            text = (case_dir(c["id"], 0, a) / "prompt.txt").read_text()
            if c["mode"] not in ("read", "ui-json") and "ANSWER:" not in text:
                prompts.append(f"{c['id']} lacks the ANSWER contract")
        d02 = (case_dir("D02", 0, a) / "prompt.txt").read_text()
        check("prompts carry the ANSWER contract", not prompts, "; ".join(prompts))
        check("D02 prompt keeps the r<row>c<col> placeholder (truth is not leaked)", "r<row>c<col>" in d02)

        seeds_differ = []
        for cid in ("C01", "C03", "T01", "S02", "U01", "G01", "O01", "D02", "K03"):
            blobs = {(case_dir(cid, s, a) / ("b.png" if cid == "D02" else "image.png")).read_bytes() for s in (0, 1, 2)}
            truths = {json.dumps(read_truth(a, cid, s), sort_keys=True) for s in (0, 1, 2)}
            if len(blobs) < 3 or len(truths) < 2:
                seeds_differ.append(cid)
        check("seeds change the image and the truth (priors cannot score)", not seeds_differ, ", ".join(seeds_differ))

        # script baselines on every seed
        base_cases = [c["id"] for c in baseline_cases()]
        failed, skipped, ran = [], [], 0
        for cid in base_cases:
            for seed in seeds_for(cid):
                row = run_baseline(cid, seed, case_dir(cid, seed, a))
                if row is None:
                    skipped.append(f"{cid} s{seed}")
                elif row["score"]["status"] != "pass":
                    failed.append(f"{cid} s{seed} -> {row['answer'][:30]!r}")
                else:
                    ran += 1
        check(f"baselines hit truth on every seed ({ran} runs over {', '.join(base_cases)})", not failed and not skipped,
              "; ".join(failed + [f"skipped {s} (OCR tool missing)" for s in skipped]))

        # every case has a scorer, every scorer has canned replies
        canned = json.loads((ROOT / "canned.json").read_text())
        check("every catalog case has a registered scorer", set(ids) <= set(SPECS), ", ".join(set(ids) - set(SPECS)))
        thin = [c["id"] for c in cases if len(canned.get(c["id"], [])) < (4 if c.get("core") else 3)]
        check("canned.json: at least 4 replies per core case, 3 per other case", not thin, ", ".join(thin))
        kinds_missing = [cid for cid in ids if not {"pass", "fail", "format_fail"} <= {e[0] for e in canned.get(cid, [])}]
        check("canned.json: every case has a pass, a fail and a format_fail reply", not kinds_missing, ", ".join(kinds_missing))

        wrong = []
        for cid in ids:
            truth = read_truth(a, cid, 0)
            for entry in canned.get(cid, []):
                expect, reply = entry[0], entry[1]
                data = entry[2] if len(entry) > 2 else None
                got = score(cid, reply, truth, data)["status"]
                if got != expect:
                    wrong.append(f"{cid} {reply[:40]!r} expected {expect} got {got}")
        check("canned replies score as written (pass, fail, format_fail, synonyms, number words, cell forms)", not wrong,
              "; ".join(wrong[:6]))

        empties = [cid for cid in ids if score(cid, "", read_truth(a, cid, 0))["status"] == "pass"
                   or score(cid, "   \n", read_truth(a, cid, 0), {})["status"] == "pass"]
        check("an empty reply never passes, for every scorer", not empties, ", ".join(empties))

        # truth-derived correct reply on every seed, and the mutation check
        misses, unread = [], []
        for cid in ids:
            for seed in seeds_for(cid):
                truth = read_truth(a, cid, seed)
                reply, data = good_reply(cid, truth)
                r = score(cid, reply, truth, data)
                if r["status"] != "pass":
                    misses.append(f"{cid} s{seed}: {r['why']}")
                if score(cid, reply, corrupt(cid, truth), data)["status"] == "pass":
                    unread.append(f"{cid} s{seed}")
        check("each scorer passes the correct reply built from every seed's truth", not misses, "; ".join(misses[:5]))
        check("mutation: corrupting the truth makes that same correct reply fail, for every scorer", not unread,
              ", ".join(unread[:8]))
        c01 = read_truth(a, "C01", 0)
        mutant = dict(c01, count=c01["count"] + 1)
        check("mutation (C01 spelled out): count+1 in memory fails the canned correct answer",
              score("C01", "ANSWER: %d" % c01["count"], mutant)["status"] == "fail")

        flagged = {
            ("C02", "ANSWER: 27"): "decoy_counted", ("C03", "ANSWER: 15"): "answered_total", ("K03", "ANSWER: yellow"): "answered_prior",
            ("T05", "ANSWER: ALPHA 1234"): "answered_decoy", ("T04", "ANSWER: LUMEN 2208"): "answered_decoy",
            ("R01", "ANSWER: 388 ms"): "answered_decoy", ("O04", "ANSWER: 4"): "band_trap", ("B01", "ANSWER: 84"): "row_off_by_one",
            ("C04", "ANSWER: 8"): "counted_header", ("D03", "ANSWER: 8.82 -> 8.32"): "swapped",
        }
        missing_flags = [f"{cid} {reply} -> {flag}" for (cid, reply), flag in flagged.items()
                         if not score(cid, reply, read_truth(a, cid, 0))["flags"].get(flag)]
        check("named failure flags fire on the near-miss answers", not missing_flags, "; ".join(missing_flags))

        # normalisers
        check("to_int: digits, thousands separators, number words, compounds",
              to_int("1,240") == {1240} and to_int("twenty-three") == {23} and to_int("four hundred twelve") == {412}
              and to_int("5.") == {5} and to_int("7 or 8") == {7, 8} and to_int("r3c2") == set())
        check("to_num: decimals, currency, units", to_num("$8.32") == {8.32} and to_num("412 ms") == {412} and to_num("1,482.6 kg") == {1482.6})
        check("norm_str: case, quotes, backticks, trailing punctuation", norm_str(" `'Hello  World'`. ") == "HELLO WORLD")
        check("color_of: synonyms", color_of("crimson") == {"red"} and color_of("royal blue") == {"blue"}
              and color_of("silver") == {"gray"} and color_of("red, not yellow") == {"red", "yellow"})
        check("pos_of: compound names are not split into parts",
              pos_of("upper left") == {"top-left"} and pos_of("top-left") == {"top-left"} and pos_of("NW") == {"top-left"}
              and pos_of("bottom right corner") == {"bottom-right"} and pos_of("middle") == {"center"} and pos_of("top") == {"top"})
        check("cell_of: r3c2, row 3 col 2, (3,2), ordinals, swapped order",
              all(cell_of(s) == {(3, 2)} for s in ("r3c2", "R3 C2", "row 3 col 2", "row 3, column 2", "(3,2)",
                                                   "third row, second column", "column 2, row 3")))
        check("month_of: names and abbreviations", month_of("May") == {"may"} and month_of("September") == {"sep"} and month_of("AUG") == {"aug"})

        # negation
        check("negation: 'there is no circle' does not mention circle", not mentions("there is no circle", "circle"))
        check("negation: affirmed and unrelated terms still count",
              mentions("a circle and a square", "circle") and not mentions("no text. Circle here", "square")
              and mentions("No text. A circle is here", "circle") and not mentions("it doesn't show a button", "button")
              and not mentions("without any logo", "logo"))
        check("absent_answer: absence words and 'there is no ...'; numbers and quotes are not absence",
              all(absent_answer(s) for s in ("NONE", "absent", "N/A", "There is no text.", "no such series", "nothing"))
              and not any(absent_answer(s) for s in ("", "35", "none, but I read 'abc'", "title", "12 differences")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failures = [c for c in CHECKS if not c[1]]
    for name, ok, detail in CHECKS:
        print(("ok  " if ok else "FAIL"), name + (f"  [{detail}]" if detail and not ok else ""))
    print(f"{len(CHECKS) - len(failures)}/{len(CHECKS)} passed")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
