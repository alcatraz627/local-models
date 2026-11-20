#!/usr/bin/env python3
"""Check that the docs index is complete and that none of its links are dead.

docs/README.md is the one list of every doc. This fails when a markdown file
under docs/ has no row there, or when a link in the index points at a file
that does not exist. Run it from anywhere; it needs no model and no network.

Usage: docs-index.py [DOCS_DIR]     exit 0 = index complete, 1 = something is off
"""
import pathlib
import re
import sys

docs = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[2] / "docs"
index = docs / "README.md"
if not index.is_file():
    sys.exit(f"docs-index: no index at {index}")

text = index.read_text()
linked = set()
for target in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", text):
    if "://" not in target:
        linked.add((docs / target).resolve())

on_disk = {p.resolve() for p in docs.rglob("*.md") if p.resolve() != index.resolve()}

unlisted = sorted(str(p.relative_to(docs.resolve())) for p in on_disk - linked)
dead = sorted(str(p) for p in linked if not p.exists())

for name in unlisted:
    print(f"FAIL not in the index: docs/{name}")
for name in dead:
    print(f"FAIL the index links a missing file: {name}")
checked = len(on_disk) + len(linked)
print(f"docs index: {checked - len(unlisted) - len(dead)}/{checked} checks passed")
sys.exit(1 if unlisted or dead else 0)
