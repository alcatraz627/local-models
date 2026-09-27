#!/usr/bin/env python3
"""Sample and record human checks of a fleet run without changing model results."""

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path


def error(message):
    print(f"lm fleet: {message}", file=sys.stderr)
    raise SystemExit(2)


def load_run(directory):
    root = Path(directory).expanduser().resolve()
    path = root / "index.jsonl"
    if not path.is_file():
        error(f"no fleet index at {path}")
    try:
        rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    except (OSError, json.JSONDecodeError) as e:
        error(f"cannot read fleet index: {e}")
    if not rows:
        error(f"fleet index is empty: {path}")
    return root, rows


def latest_reviews(root):
    path = root / "reviews.jsonl"
    if not path.exists():
        return {}
    try:
        records = [json.loads(line) for line in path.read_text().splitlines() if line]
    except (OSError, json.JSONDecodeError) as e:
        error(f"cannot read reviews: {e}")
    return {int(r["i"]): r for r in records}


def source_path(root, row):
    source = Path(row["item"]).expanduser()
    if source.is_absolute():
        return source
    meta_path = root / "meta.json"
    if meta_path.is_file():
        try:
            cwd = json.loads(meta_path.read_text()).get("cwd")
            if cwd:
                return Path(cwd) / source
        except (OSError, json.JSONDecodeError):
            pass
    if root.parent.name == "fleet" and root.parent.parent.name == "outputs":
        return root.parent.parent.parent / source
    return Path.cwd() / source


def review_hashes(root, row, require_source=True):
    result_path = (root / row["result"]).resolve()
    if not result_path.is_relative_to(root) or not result_path.is_file():
        if require_source:
            error(f"missing or escaped result path for item {row['i']}")
        return None
    source = source_path(root, row)
    if not source.is_file():
        if require_source:
            error(f"source file is unavailable for item {row['i']}: {source}")
        return None
    row_bytes = json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
    return {
        "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "index_row_sha256": hashlib.sha256(row_bytes).hexdigest(),
    }


def current_review(root, row, reviews):
    review = reviews.get(row["i"])
    if review is None:
        return None
    hashes = review_hashes(root, row, require_source=False)
    if hashes is None:
        return {**review, "status": "stale"}
    if any(review.get(key) != value for key, value in hashes.items()):
        return {**review, "status": "stale"}
    return review


def sample(root, rows, count, machine):
    n = min(count, len(rows))
    failures = [r for r in rows if r.get("gate", r.get("judge")) != "pass"]
    chosen = failures[:n]
    pending = [r for r in rows if r not in chosen]
    if len(chosen) < n:
        boundaries = [pending[0], pending[len(pending) // 2], pending[-1]] if pending else []
        for row in boundaries:
            if row not in chosen and len(chosen) < n:
                chosen.append(row)
    if len(chosen) < n:
        rng = random.Random(str(root))
        chosen.extend(rng.sample([r for r in rows if r not in chosen], n - len(chosen)))
    reviews = latest_reviews(root)
    packet = []
    for row in sorted(chosen, key=lambda r: r["i"]):
        result_path = (root / row["result"]).resolve()
        if not result_path.is_relative_to(root) or not result_path.is_file():
            error(f"missing or escaped result path for item {row['i']}")
        result = json.loads(result_path.read_text())
        source = source_path(root, row)
        if source.suffix.lower() in (".xlsx", ".xlsm", ".xls", ".pdf", ".png", ".jpg", ".jpeg"):
            excerpt = f"[binary source: {source.name}; inspect the source file before verdict]"
        else:
            excerpt = source.read_text(errors="replace")[:600] if source.is_file() else "[source unavailable]"
        packet.append({"i": row["i"], "item": row["item"], "gate": row.get("gate", row.get("judge")),
                       "answer": result.get("text", "")[:1600], "source_excerpt": excerpt,
                       "review": current_review(root, row, reviews)})
    if machine:
        print(json.dumps({"ok": True, "run": str(root), "sample": packet}))
    else:
        for p in packet:
            print(f"[{p['i']}] {p['item']} · {p['gate']}")
            print(f"SOURCE: {p['source_excerpt']}\nANSWER: {p['answer']}")
            print(f"REVIEW: {(p['review'] or {}).get('status', 'unreviewed')}\n")


def mark(root, rows, item, status, note):
    row = next((r for r in rows if r.get("i") == item), None)
    if row is None:
        error(f"no item {item} in this run")
    record = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "i": item, "status": status, "note": note, **review_hashes(root, row)}
    with (root / "reviews.jsonl").open("a") as f:
        f.write(json.dumps(record) + "\n")
    print(json.dumps({"ok": True, "review": record}))


def audit(root, rows):
    reviews = latest_reviews(root)
    statuses = [(current_review(root, row, reviews) or {}).get("status", "unreviewed") for row in rows]
    counts = {s: statuses.count(s) for s in ("accepted", "rejected", "unsure", "stale")}
    print(json.dumps({"ok": True, "run": str(root), "items": len(rows),
                      "gate_pass": sum(r.get("gate", r.get("judge")) == "pass" for r in rows),
                      "human": counts, "unreviewed": statuses.count("unreviewed")}))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("sample")
    p.add_argument("run")
    p.add_argument("--count", type=int, default=5)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("verdict")
    p.add_argument("run")
    p.add_argument("--item", type=int, required=True)
    p.add_argument("--status", choices=("accepted", "rejected", "unsure"), required=True)
    p.add_argument("--note", required=True)
    p = sub.add_parser("audit")
    p.add_argument("run")
    args = ap.parse_args()
    root, rows = load_run(args.run)
    if args.command == "sample":
        if args.count < 1:
            error("--count must be positive")
        sample(root, rows, args.count, args.json)
    elif args.command == "verdict":
        mark(root, rows, args.item, args.status, args.note)
    else:
        audit(root, rows)


if __name__ == "__main__":
    main()
