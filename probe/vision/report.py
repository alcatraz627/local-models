#!/usr/bin/env python3
"""Turn every results/*.jsonl file into REPORT.md and report.json.

The matrix has one row per case and one column per model, each cell the pass
count over seeds. Beside it: a per-capability rollup, the format_fail count and
median wall time per model, the script-baseline column, crop lift, and the
non-gated H01 plain-read companion. When a (model, case, seed) appears twice
(a --fresh rerun), the latest line wins.
"""

import argparse
import json
import statistics
from collections import defaultdict

from common import ROOT, load_cases

SCRIPT_TAG = "script_beats_model"


def read_results():
    models = {}
    for path in sorted((ROOT / "results").glob("*.jsonl")):
        for line in path.read_text().splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            models.setdefault(row.get("model", path.stem), {})[(row["case"], row["seed"])] = row
    return {m: list(rows.values()) for m, rows in models.items()}


def tally(statuses):
    n = len(statuses)
    p = statuses.count("pass")
    return {"pass": p, "fail": statuses.count("fail"), "format_fail": statuses.count("format_fail"),
            "n": n, "rate": p / n if n else None}


def baseline_summary():
    path = ROOT / "baselines.json"
    out = {}
    if path.is_file():
        for row in json.loads(path.read_text()):
            out.setdefault(row["case"], []).append(row["score"]["status"] == "pass")
    return {cid: {"pass": sum(v), "n": len(v), "rate": sum(v) / len(v)} for cid, v in out.items()}


def build(catalog=None):
    cases = load_cases(catalog)
    results = read_results()
    matrix, stats, flags, lift, companion = {}, {}, {}, {}, {}
    for model, rows in results.items():
        by_case = defaultdict(list)
        lanes = defaultdict(lambda: defaultdict(list))
        walls, flag_count = [], defaultdict(int)
        for row in rows:
            by_case[row["case"]].append(row["score"]["status"])
            if isinstance(row.get("wall_ms"), (int, float)):
                walls.append(row["wall_ms"])
            for k, v in (row["score"].get("flags") or {}).items():
                if v is True or (isinstance(v, list) and v):
                    flag_count[k] += 1
            for name, lane in (row.get("lanes") or {}).items():
                lanes[row["case"]][name].append(lane["score"]["status"])
        matrix[model] = {cid: tally(s) for cid, s in by_case.items()}
        total = [s for sts in by_case.values() for s in sts]
        stats[model] = {**tally(total), "median_wall_s": round(statistics.median(walls) / 1000, 1) if walls else None}
        flags[model] = dict(flag_count)
        for cid, ln in lanes.items():
            if "crop" in ln:
                lift.setdefault(cid, {})[model] = {name: tally(s) for name, s in ln.items()}
            if "read" in ln:
                companion.setdefault(cid, {})[model] = tally(ln["read"])

    caps = defaultdict(list)
    for c in cases:
        for cap in c.get("capability", []):
            if cap != SCRIPT_TAG:
                caps[cap].append(c["id"])
    rollup = {}
    for model, m in matrix.items():
        rollup[model] = {}
        for cap, ids in sorted(caps.items()):
            rates = [m[i]["rate"] for i in ids if i in m and m[i]["rate"] is not None]
            if rates:
                rollup[model][cap] = {"rate": sum(rates) / len(rates), "cases": len(rates)}
    return {"models": list(matrix), "cases": [c["id"] for c in cases], "matrix": matrix, "model_stats": stats,
            "capability_rollup": rollup, "script_baseline": baseline_summary(), "crop_lift": lift,
            "plain_read_companion": companion, "flags": flags}


def cell(t):
    return "-" if not t or not t["n"] else f"{t['pass']}/{t['n']}"


def markdown(data, catalog=None):
    cases = {c["id"]: c for c in load_cases(catalog)}
    models = data["models"]
    out = ["# Vision comparison report", "",
           "Cells are passes over seeds. A dash means that model has no run for that case. "
           "`format_fail` is a reply that broke the ANSWER contract, counted apart from wrong answers.", ""]
    out += ["| Case | Core | Capability | Script | " + " | ".join(models) + " |",
            "|---|---|---|---|" + "---|" * len(models)]
    for cid in data["cases"]:
        b = data["script_baseline"].get(cid)
        caps = ", ".join(x for x in cases[cid]["capability"] if x != SCRIPT_TAG)
        row = [cid, "yes" if cases[cid].get("core") else "", caps, f"{b['pass']}/{b['n']}" if b else "-"]
        row += [cell(data["matrix"][m].get(cid)) for m in models]
        out.append("| " + " | ".join(row) + " |")
    if models:
        out += ["", "## Model totals", "", "| Model | Pass | Fail | format_fail | Median wall (s) |", "|---|---:|---:|---:|---:|"]
        for m in models:
            s = data["model_stats"][m]
            out.append(f"| {m} | {s['pass']}/{s['n']} | {s['fail']} | {s['format_fail']} | {s['median_wall_s'] if s['median_wall_s'] is not None else '-'} |")
        out += ["", "## Capability rollup", "", "Mean of per-case pass rates, over the cases that have a run.", "",
                "| Capability | " + " | ".join(models) + " |", "|---|" + "---:|" * len(models)]
        caps = sorted({c for m in models for c in data["capability_rollup"][m]})
        for cap in caps:
            vals = [data["capability_rollup"][m].get(cap) for m in models]
            out.append(f"| {cap} | " + " | ".join(f"{v['rate']:.0%} ({v['cases']})" if v else "-" for v in vals) + " |")
    if data["crop_lift"]:
        out += ["", "## Crop lift", "", "Pass counts per lane. Lift is the crop lane minus the full-frame lane.", "",
                "| Case | Model | Full | Crop | Region |", "|---|---|---|---|---|"]
        for cid, per in data["crop_lift"].items():
            for m, ln in per.items():
                out.append(f"| {cid} | {m} | {cell(ln.get('full'))} | {cell(ln.get('crop'))} | {cell(ln.get('region'))} |")
    if data["plain_read_companion"]:
        out += ["", "## Plain-read companion (not gated)", "", "H01 asked with the default read prompt; pass means nothing invented.", "",
                "| Model | Pass |", "|---|---|"]
        for per in data["plain_read_companion"].values():
            for m, t in per.items():
                out.append(f"| {m} | {cell(t)} |")
    named = {m: f for m, f in data["flags"].items() if f}
    if named:
        out += ["", "## Named failure shapes", "", "Counts of flagged rows per model (answered_decoy, band_trap, and so on).", ""]
        for m, f in named.items():
            out.append(f"- {m}: " + ", ".join(f"{k} {v}" for k, v in sorted(f.items())))
    return "\n".join(out) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--catalog")
    a = p.parse_args()
    data = build(a.catalog)
    (ROOT / "report.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    (ROOT / "REPORT.md").write_text(markdown(data, a.catalog))
    print(f"wrote {ROOT / 'REPORT.md'} and {ROOT / 'report.json'} ({len(data['models'])} models)")


if __name__ == "__main__":
    main()
