#!/usr/bin/env python3
"""The mechanical judge for local-model code-review findings: keeps only
findings that point at a real place in the tree, so a fabricated file or line
never reaches a human (or a paid validator) as if it were evidence.

    review --findings --json | findings-gate.py [--root DIR]
    findings-gate.py --self-test

Reads a review envelope (or bare findings object) on stdin, drops any finding
whose file does not exist under --root (default: cwd) or whose line is outside
the file's bounds, and prints {ok, kept, dropped, findings}. Exit 0 = every
finding survived; 1 = something was dropped (read `dropped` before trusting the
rest); 2 = input unreadable. Bare python3, no deps.
"""
import argparse
import json
import os
import sys


def gate(obj, root):
    """Fail-CLOSED on every axis: a finding survives only by proving it points at
    a real line of a real file inside root. Anything unproven — an absolute path,
    a `..` escape, a line that isn't a plain positive int — is dropped, because
    the whole point is that a fabricated location never passes as evidence."""
    findings = obj.get("findings")
    if findings is None and isinstance(obj.get("data"), dict):
        findings = obj["data"].get("findings")
    if not isinstance(findings, list):
        return None
    real_root = os.path.realpath(root)
    kept, dropped = [], []
    for f in findings:
        if not isinstance(f, dict):
            dropped.append({"finding": f, "why": "not an object"})
            continue
        rel = f.get("file")
        if not isinstance(rel, str) or not rel:
            dropped.append({**f, "why": "file is missing or not a string"})
            continue
        # containment: os.path.join DISCARDS root on an absolute component, and
        # `..` walks out of it — so resolve and prove the result is still inside
        path = os.path.realpath(os.path.join(real_root, rel))
        if os.path.commonpath([real_root, path]) != real_root:
            dropped.append({**f, "why": "file escapes --root: %s" % rel})
            continue
        if not os.path.isfile(path):
            dropped.append({**f, "why": "file does not exist: %s" % rel})
            continue
        line = f.get("line")
        if line is not None:
            # bool is an int subclass; a string/float/NaN/Infinity line is a
            # malformed claim, not a licence to skip the bounds check
            if isinstance(line, bool) or not isinstance(line, int):
                dropped.append({**f, "why": "line is not an integer: %r" % (line,)})
                continue
            if line < 1:
                dropped.append({**f, "why": "line %s is not a positive line number" % line})
                continue
            with open(path, errors="replace") as fh:
                n = sum(1 for _ in fh)
            if line > n:
                dropped.append({**f, "why": "line %s > file length %s" % (line, n)})
                continue
        kept.append(f)
    return kept, dropped


def self_test():
    """Every escape the adversarial gate found on 2026-07-13, plus the happy path.
    A finding kept here that shouldn't be is a fabricated location reaching a human."""
    import tempfile
    d = tempfile.mkdtemp()
    root = os.path.join(d, "root")
    os.makedirs(root)
    open(os.path.join(root, "real.py"), "w").write("a = 1\nb = 2\nc = 3\n")
    open(os.path.join(d, "outside.txt"), "w").write("secrets\n")
    cases = [
        ({"file": "real.py", "line": 2, "finding": "ok case"}, True),
        ({"file": "real.py", "finding": "ok, no line claim"}, True),
        ({"file": "ghost.py", "line": 1, "finding": "fabricated file"}, False),
        ({"file": "real.py", "line": 99, "finding": "fabricated line"}, False),
        ({"file": "/etc/hosts", "line": 1, "finding": "absolute-path escape"}, False),
        ({"file": "../outside.txt", "line": 1, "finding": "traversal escape"}, False),
        ({"file": "real.py", "line": "2", "finding": "string line"}, False),
        ({"file": "real.py", "line": 99.0, "finding": "float line"}, False),
        ({"file": "real.py", "line": float("inf"), "finding": "infinite line"}, False),
        ({"file": "real.py", "line": 0, "finding": "zero line"}, False),
        ({"file": "real.py", "line": -5, "finding": "negative line"}, False),
        ({"file": "", "line": 1, "finding": "empty file"}, False),
        ({"file": 42, "line": 1, "finding": "non-string file"}, False),
    ]
    kept, dropped = gate({"findings": [c for c, _ in cases]}, root)
    want_keep = {c["finding"] for c, k in cases if k}
    got_keep = {f["finding"] for f in kept}
    ok = got_keep == want_keep and len(dropped) == len(cases) - len(want_keep)
    if not ok:
        print("  leaked: %s" % sorted(got_keep - want_keep), file=sys.stderr)
        print("  lost:   %s" % sorted(want_keep - got_keep), file=sys.stderr)
    print("findings-gate self-test: %s (%d cases, kept=%d dropped=%d)"
          % ("ok" if ok else "FAIL", len(cases), len(kept), len(dropped)))
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(description="mechanical gate for review findings")
    ap.add_argument("--root", default=".", help="tree the file/line claims are checked against")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
    try:
        obj = json.load(sys.stdin)
    except ValueError as e:
        print(json.dumps({"ok": False, "error": "stdin is not JSON: %s" % e,
                          "fix": "pipe `review --findings --json` output in"}))
        sys.exit(2)
    if not isinstance(obj, dict):
        print(json.dumps({"ok": False, "error": "input is not a JSON object",
                          "fix": "pipe `review --findings --json` output in"}))
        sys.exit(2)
    res = gate(obj, args.root)
    if res is None:
        print(json.dumps({"ok": False, "error": "no findings[] in input (nor .data.findings)",
                          "fix": "run review with --findings so the output is schema-constrained"}))
        sys.exit(2)
    kept, dropped = res
    print(json.dumps({"ok": not dropped, "kept": len(kept), "dropped": dropped,
                      "findings": kept}, indent=1))
    sys.exit(1 if dropped else 0)


if __name__ == "__main__":
    main()
