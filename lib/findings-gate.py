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
    findings = obj.get("findings")
    if findings is None and isinstance(obj.get("data"), dict):
        findings = obj["data"].get("findings")
    if not isinstance(findings, list):
        return None
    kept, dropped = [], []
    for f in findings:
        if not isinstance(f, dict):
            dropped.append({"finding": f, "why": "not an object"})
            continue
        path = os.path.join(root, str(f.get("file", "")))
        if not os.path.isfile(path):
            dropped.append({**f, "why": "file does not exist: %s" % f.get("file")})
            continue
        line = f.get("line")
        if isinstance(line, int) and line > 0:
            with open(path, errors="replace") as fh:
                n = sum(1 for _ in fh)
            if line > n:
                dropped.append({**f, "why": "line %s > file length %s" % (line, n)})
                continue
        kept.append(f)
    return kept, dropped


def self_test():
    import tempfile
    d = tempfile.mkdtemp()
    real = os.path.join(d, "real.py")
    open(real, "w").write("a = 1\nb = 2\nc = 3\n")
    obj = {"findings": [
        {"file": "real.py", "line": 2, "severity": "minor", "finding": "ok case"},
        {"file": "ghost.py", "line": 1, "severity": "major", "finding": "fabricated file"},
        {"file": "real.py", "line": 99, "severity": "major", "finding": "fabricated line"},
    ]}
    kept, dropped = gate(obj, d)
    ok = (len(kept) == 1 and kept[0]["finding"] == "ok case" and len(dropped) == 2
          and any("ghost" in x["why"] for x in dropped if "why" in x)
          and any("99" in x["why"] for x in dropped if "why" in x))
    print("findings-gate self-test: %s (kept=%d dropped=%d)"
          % ("ok" if ok else "FAIL", len(kept), len(dropped)))
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
