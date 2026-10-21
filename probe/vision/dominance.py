#!/usr/bin/env python3
"""Where does a challenger do worse than the incumbent, case by case?

The owner's rule for replacing a `see` model: the challenger must match the
incumbent on every case the incumbent passes. A higher total can hide a case the
incumbent handled and the challenger drops, so this lists those cases.

Usage: dominance.py INCUMBENT CHALLENGER [CHALLENGER ...]   (model names as in report.json)
"""
import json
import sys
from pathlib import Path

report = json.loads((Path(__file__).resolve().parent / "report.json").read_text())
matrix = report["matrix"]


def rate(cell):
    return cell["pass"] / cell["n"] if cell["n"] else 0.0


inc = sys.argv[1]
for ch in sys.argv[2:]:
    worse, better = [], []
    for cid, cell in matrix[inc].items():
        other = matrix[ch].get(cid)
        if other is None:
            continue
        if rate(other) < rate(cell):
            worse.append(f"{cid} {cell['pass']}/{cell['n']}->{other['pass']}/{other['n']}")
        elif rate(other) > rate(cell):
            better.append(f"{cid} {cell['pass']}/{cell['n']}->{other['pass']}/{other['n']}")
    print(f"{ch} vs {inc}: worse on {len(worse)}, better on {len(better)}")
    print(f"  worse:  {', '.join(worse) or 'none'}")
    print(f"  better: {', '.join(better) or 'none'}")
