#!/usr/bin/env python3
"""Print recorded per-fixture candidate comparisons; never calls a model."""
import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def slug(model):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", model).strip("_")


def load(stage, model):
    path = RESULTS / stage / f"{slug(model)}.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text())
        out = {}
        for row in data.get("checks", []):
            for probe in row.get("probe_items", []):
                out[probe["fixture"]] = {"pass": probe.get("pass"), "auto": probe.get("auto"),
                                          "human_verdict": probe.get("human_verdict")}
            if "fixture" in row:
                out[row["fixture"]] = {"pass": row.get("pass"), "auto": row.get("auto"),
                                       "human_verdict": row.get("human_verdict")}
        return out
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", nargs="?", choices=["see-diff", "see-read", "image-tools", "text-small", "embed"])
    args = parser.parse_args()
    stages = [args.stage] if args.stage else ["see-diff", "see-read", "image-tools", "text-small", "embed"]
    comparisons = {
        "see-diff": ("gemma4:26b", ["minicpm-v4.6", "mlx:mlx-community/Qwen3-VL-8B-Instruct-4bit"]),
        "see-read": ("minicpm-v4.6", ["mlx:mlx-community/Qwen3-VL-8B-Instruct-4bit", "XiaomiMiMo/MiMo-V2.6-Distill-Qwen-9B", "Qwen/Qwen2.5-VL-7B-Instruct", "mistralai/Pixtral-12B-2409", "ibm-granite/granite-docling-258M"]),
        "text-small": ("gemma4-e4b-warm", ["Nemotron 3.5 Bolt", "openbmb/MiniCPM5-2B"]),
        "image-tools": ("no incumbent", ["mflux qwen-edit", "FLUX.1-Kontext-dev 4-bit", "RMBG-2.0", "Real-ESRGAN x4"]),
        "embed": ("nomic-embed-text", ["embeddinggemma-2:740m"]),
    }
    for stage in stages:
        incumbent, candidates = comparisons[stage]
        print(f"[{stage}] incumbent: {incumbent}")
        base = load(stage, incumbent)
        for candidate in candidates:
            challenger = load(stage, candidate)
            names = sorted(set(base) | set(challenger))
            if not names:
                print(f"  {candidate}: no result file")
                continue
            print(f"  candidate: {candidate}")
            for name in names:
                def label(row):
                    result = row.get(name)
                    if not result:
                        return "NO DATA"
                    if result.get("human_verdict") == "pass":
                        return "HUMAN PASS"
                    if result.get("human_verdict") == "fail":
                        return "HUMAN FAIL"
                    if result.get("pass") is True:
                        return "PASS"
                    if result.get("pass") is False:
                        return "FAIL"
                    if result.get("auto"):
                        return "AUTO " + result["auto"]
                    return "NO DATA"
                a = label(base)
                b = label(challenger)
                print(f"    {name}: incumbent={a} candidate={b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
