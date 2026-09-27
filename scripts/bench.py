#!/usr/bin/env python3
"""Run a fixed LM fixture set and record behavior, latency, disk, and process RSS."""

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def disk_kib():
    paths = [Path.home() / ".ollama/models", Path.home() / ".cache/huggingface"]
    found = [str(p) for p in paths if p.exists()]
    if not found:
        return None
    run = subprocess.run(["du", "-sk", *found], capture_output=True, text=True)
    if run.returncode:
        return None
    return sum(int(line.split()[0]) for line in run.stdout.splitlines())


def resident_models():
    run = subprocess.run(["ollama", "ps"], capture_output=True, text=True, timeout=3)
    if run.returncode:
        return []
    return [line.split()[0] for line in run.stdout.splitlines()[1:] if line.strip()]


def get_field(data, path):
    for part in path.split("."):
        if not isinstance(data, dict):
            return None
        data = data.get(part)
    return data


def response_failures(case, data):
    failed = {path: {"expected": want, "actual": get_field(data, path)}
              for path, want in case.get("checks", {}).items()
              if get_field(data, path) != want}
    if "text_regex" in case:
        actual = get_field(data, "text")
        if not isinstance(actual, str) or re.fullmatch(case["text_regex"], actual) is None:
            failed["text"] = {"expected_regex": case["text_regex"], "actual": actual}
    return failed


def run_case(case, timeout):
    argv = [str(ROOT / item) if i == 0 else item for i, item in enumerate(case["argv"])]
    before = resident_models()
    start = time.monotonic()
    prefix = ["/usr/bin/time", "-l"] if sys.platform == "darwin" else []
    try:
        run = subprocess.run(prefix + argv, cwd=ROOT, capture_output=True, text=True,
                             timeout=timeout, env=os.environ.copy())
    except subprocess.TimeoutExpired:
        return {"name": case["name"], "ok": False, "error": "timeout", "wall_ms": int((time.monotonic() - start) * 1000)}
    wall = int((time.monotonic() - start) * 1000)
    try:
        data = json.loads(run.stdout)
    except json.JSONDecodeError:
        data = None
    failed = response_failures(case, data)
    rss = re.search(r"(\d+)\s+maximum resident set size", run.stderr)
    return {"name": case["name"], "ok": run.returncode == 0 and not failed,
            "exit": run.returncode, "wall_ms": wall,
            "process_peak_rss_mb": round(int(rss.group(1)) / 1e6, 1) if rss else None,
            "resident_before": before, "resident_after": resident_models(),
            "failed_checks": failed, "stdout_excerpt": run.stdout[:800],
            "stderr_excerpt": run.stderr[:400] if run.returncode else ""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fixture_set", help="JSON fixture set under probe/bench/ or an explicit path")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--out")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.repeat < 1 or args.timeout < 1:
        ap.error("--repeat and --timeout must be positive")
    path = Path(args.fixture_set)
    if not path.exists():
        path = ROOT / "probe/bench" / (args.fixture_set + ".json")
    fixture = json.loads(path.read_text())
    if not fixture.get("cases"):
        ap.error("fixture set has no cases")
    before = disk_kib()
    results = [run_case(case, args.timeout) for _ in range(args.repeat) for case in fixture["cases"]]
    after = disk_kib()
    summary = {}
    for case in fixture["cases"]:
        rows = [r for r in results if r["name"] == case["name"]]
        times = [r["wall_ms"] for r in rows]
        summary[case["name"]] = {"passed": sum(r["ok"] for r in rows), "runs": len(rows),
                                  "median_ms": int(statistics.median(times)), "max_ms": max(times)}
    report = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "fixture_set": str(path), "repeat": args.repeat, "summary": summary,
              "disk_before_kib": before, "disk_after_kib": after,
              "disk_delta_kib": after - before if before is not None and after is not None else None,
              "memory_scope": "peak command-process RSS; external Ollama/MLX model processes excluded",
              "results": results}
    out = Path(args.out) if args.out else ROOT / "outputs/bench" / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{fixture['name']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    if args.json:
        print(json.dumps({"ok": all(r["ok"] for r in results), "report": str(out), "summary": summary,
                          "disk_delta_kib": report["disk_delta_kib"]}))
    else:
        print(f"bench: {out}")
        for name, item in summary.items():
            print(f"  {name}: {item['passed']}/{item['runs']} pass, median {item['median_ms']} ms")
    if not all(r["ok"] for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
