#!/usr/bin/env python3
"""Re-judge every saved vision result with the current scorers, without calling a model.

Use it after fixing a scorer: the stored replies are evidence, and a scorer bug
should not cost a re-run of hours of model calls. Rewrites results/*.jsonl in place
and prints how many verdicts changed per model.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from score import score, score_blank_read  # noqa: E402


def rescore_lane(case_id, name, lane, truth):
    if name == "read":   # the blank-image structured read in H01
        return score_blank_read(lane.get("text") or "")
    return score(case_id, lane.get("text") or "", truth, lane.get("data"))


def main():
    for path in sorted((HERE / "results").glob("*.jsonl")):
        rows, changed = [], 0
        for line in path.read_text().splitlines():
            row = json.loads(line)
            for name, lane in (row.get("lanes") or {}).items():
                if lane.get("see_exit_code") not in (0, None):
                    continue   # a failed call has no reply to judge
                new = rescore_lane(row["case"], name, lane, row["truth"])
                is_primary = lane.get("text") == row.get("text") and lane.get("wall_ms") == row.get("wall_ms")
                if is_primary and new.get("status") != (row.get("score") or {}).get("status"):
                    changed += 1
                lane["score"] = new
                if is_primary:
                    row["score"] = new
            rows.append(row)
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        print(f"{path.stem}: {changed} verdict(s) changed")


if __name__ == "__main__":
    main()
