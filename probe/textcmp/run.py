#!/usr/bin/env python3
"""A small text-model comparison: exact-answer questions run through `q` on each model.

Every case has one checkable answer (a number, a name, a list), so the score is a
fact about the model, not a judgment. The prompt asks for a final `ANSWER:` line;
the check reads that line, and a reply without one is scored format_fail, which is
kept apart from a wrong answer.

Usage: run.py MODEL [MODEL ...]   writes results/<model>.json and prints a table
       run.py --report            table from the saved results only
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = "\nEnd your reply with exactly one line of the form: ANSWER: <answer>"

CASES = [
    ("arith-crates", "A crate holds 24 bottles. A shop has 7 full crates and 5 loose bottles, and 13 bottles are broken. How many intact bottles are there?", "int", 160),
    ("weekday", "What day of the week was 22 October 2026?", "word", "thursday"),
    ("extract-total", "Invoice 8812 from Halden Supply. Subtotal $1,190.00, shipping $42.50, tax $52.00, discount none. What is the invoice total in dollars?", "num", 1284.5),
    ("letter-count", "How many times does the letter r appear in the phrase 'strawberry raspberry'?", "int", 6),
    ("logic-order", "Ana is taller than Ben. Ben is taller than Cy. Dee is taller than Ana. Who is the shortest?", "word", "cy"),
    ("sort", "Sort these numbers ascending: 42, 7, 19, 88, 3, 19.", "list", [3, 7, 19, 19, 42, 88]),
    ("code-trace", "What does this Python print?\nx = [1, 2, 3, 4, 5]\nprint(sum(i * i for i in x if i % 2))", "int", 35),
    ("units", "How many minutes are in 3.5 hours plus 45 seconds? Give a decimal.", "num", 210.75),
    ("regex", "Which of these strings fully match the regex ^a.c$ : abc, ac, abbc, axc, a.c, Abc ? List the matches separated by commas.", "set", {"abc", "axc", "a.c"}),
    ("false-premise", "In what year was the Eiffel Tower moved to London?", "absent", None),
    ("buried-fact", "Notes from the call: the team discussed hiring, the office move to the third floor, and the budget. Priya said the server migration finishes on day 19 of the sprint, not day 12 as planned. Lunch is now at 1pm. On which sprint day does the migration finish?", "int", 19),
    ("percent", "A price rises from 80 to 92. By what percent did it rise?", "num", 15.0),
    ("negation", "List the even numbers between 1 and 10 that are NOT divisible by 4.", "list", [2, 6, 10]),
    ("count-words", "How many words are in this sentence: 'the quick brown fox jumps over the lazy dog'?", "int", 9),
]
ABSENT = re.compile(r"\b(never|none|not|no such|did not|didn't|wasn't|was not|hasn't|has not|false premise|n/a)\b", re.I)


def answer_line(text):
    # Some models put "ANSWER:" mid-line instead of on its own line, or wrap the
    # value in the <answer> placeholder; both still count as following the contract.
    hits = [m.group(1) for m in re.finditer(r"(?i)\bANSWER\W*[:：]\s*(.+?)\s*$", text, re.M)]
    if not hits:
        return None
    ans = re.sub(r"</?answer>|^<|>$", "", hits[-1].strip(), flags=re.I)
    return ans.strip().strip("*`_ .")


def nums(s):
    return [float(x.replace(",", "")) for x in re.findall(r"-?\d[\d,]*\.?\d*", s)]


def score(kind, truth, text):
    ans = answer_line(text)
    if ans is None:
        return "format_fail", "no ANSWER line"
    low = ans.casefold()
    if kind == "int" or kind == "num":
        got = set(nums(ans))
        ok = len(got) == 1 and abs(next(iter(got)) - truth) < 0.01
        return ("pass" if ok else "fail"), ans
    if kind == "word":
        ok = re.search(r"\b%s\b" % re.escape(truth), low) is not None
        return ("pass" if ok else "fail"), ans
    if kind == "list":
        got = [int(x) for x in nums(ans)]
        return ("pass" if got == truth else "fail"), ans
    if kind == "set":
        got = {t.strip().strip("'\"").casefold() for t in ans.split(",") if t.strip()}
        return ("pass" if got == truth else "fail"), ans
    if kind == "absent":
        ok = ABSENT.search(ans) is not None and not re.search(r"\b1[89]\d\d|20\d\d\b", ans)
        return ("pass" if ok else "fail"), ans
    return "fail", "unknown kind"


def run_model(model):
    rows = []
    for cid, prompt, kind, truth in CASES:
        t0 = time.time()
        proc = subprocess.run([str(ROOT / "bin/q"), "--json", "--timeout", "300", "-m", model, prompt + CONTRACT],
                              capture_output=True, text=True, cwd=ROOT)
        ms = int((time.time() - t0) * 1000)
        try:
            env = json.loads(proc.stdout)
            text = env.get("text", "") if env.get("ok") else ""
            served = env.get("model", model)
        except ValueError:
            env, text, served = {}, "", model
        verdict, detail = score(kind, truth, text) if text else ("error", (proc.stdout + proc.stderr)[:160])
        rows.append({"case": cid, "verdict": verdict, "detail": detail, "ms": ms, "served": served, "text": text})
        print(f"  {verdict:<11} {cid:<14} {ms:>6}ms  {detail[:60]}", flush=True)
    out = HERE / "results" / (re.sub(r"[^A-Za-z0-9._-]+", "_", model) + ".json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"model": model, "rows": rows}, indent=2) + "\n")


def report():
    print(f"{'model':<28} pass fail fmt err  median_ms")
    for f in sorted((HERE / "results").glob("*.json")):
        d = json.loads(f.read_text())
        v = [r["verdict"] for r in d["rows"]]
        ms = sorted(r["ms"] for r in d["rows"])
        print(f"{d['model']:<28} {v.count('pass'):>4} {v.count('fail'):>4} {v.count('format_fail'):>3} {v.count('error'):>3}  {ms[len(ms) // 2]:>9}")


def rescore():
    """Re-judge saved replies with the current scorer, without calling any model."""
    kinds = {cid: (kind, truth) for cid, _, kind, truth in CASES}
    for f in sorted((HERE / "results").glob("*.json")):
        d = json.loads(f.read_text())
        for r in d["rows"]:
            if r["verdict"] != "error":
                r["verdict"], r["detail"] = score(*kinds[r["case"]], r["text"])
        f.write_text(json.dumps(d, indent=2) + "\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--rescore"]:
        rescore()
        args = ["--report"]
    if not args or args == ["--report"]:
        report()
        sys.exit(0)
    for m in args:
        print(f"model {m}", flush=True)
        run_model(m)
    report()
