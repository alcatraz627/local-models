#!/usr/bin/env python3
"""Compare embedding models on one fixed answer-bearing passage set."""

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / ".venv/bin/python"
CORE = ROOT / "lib/rag.py"


def run(model, db, command, *args):
    env = {**os.environ, "RAG_EMBED_MODEL": model}
    start = time.monotonic()
    proc = subprocess.run([str(PY), str(CORE), command, str(db), *args], cwd=ROOT,
                          env=env, text=True, capture_output=True, timeout=600)
    if proc.returncode:
        raise RuntimeError(f"{model} {command}: {proc.stderr[-500:] or proc.stdout[-500:]}")
    return json.loads(proc.stdout), int((time.monotonic() - start) * 1000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="probe/bench/retrieval.json")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--models", nargs="+", default=["nomic-embed-text", "qwen3-embedding:0.6b"])
    args = ap.parse_args()
    fixture = json.loads((ROOT / args.set).read_text())
    out = Path(args.out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {"fixture": args.set, "models": {}}
    for model in args.models:
        db = out / (model.replace(":", "-") + ".db")
        indexed, index_ms = run(model, db, "index", *[str(ROOT / f) for f in fixture["corpus"]])
        cases = []
        for q in fixture["queries"]:
            found, ms = run(model, db, "search", "-k", "5", q["query"])
            matching = [c["ref"] for c in found["chunks"]
                        if Path(c["path"]).resolve() == (ROOT / q["file"]).resolve()
                        and c["heading"] == q["heading"]]
            cases.append({"query": q["query"], "expected": q["file"] + " § " + q["heading"],
                          "hit": bool(matching), "rank": matching[0] if matching else None,
                          "search_ms": ms,
                          "top5": [c["path"] + " § " + c["heading"] for c in found["chunks"]]})
        report["models"][model] = {"indexed": indexed, "index_ms": index_ms,
                                   "db_bytes": db.stat().st_size, "top5_recall": sum(c["hit"] for c in cases) / len(cases),
                                   "cases": cases}
    path = out / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(path), "scores": {m: v["top5_recall"] for m, v in report["models"].items()}}))


if __name__ == "__main__":
    main()
