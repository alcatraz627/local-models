#!/usr/bin/env python3
"""Run catalog cases against one model through `see` and append scored result rows.

    run.py --model minicpm-v4.6 --core --dry-run     # print the commands only
    run.py --model gemma4:26b --cases C01,T01        # run two cases, seeds 0 1 2
    run.py --model apple-vision --cases T06          # OCR lane only, no model
    run.py --model measure --cases C02,O03           # `see count` / `see odd`, no model

One JSON line per (case, seed) goes to results/<model-slug>.jsonl. Pairs already
present for that model are skipped unless --fresh. OCR-lane runs are model
independent and go to results/apple-vision.jsonl, once.
"""

import argparse
import json
import re
import shlex
import subprocess
import time

from common import SEE, case_dir, case_map, load_cases, result_dir, seeds_for, slug
from gen import generate_one
from score import score, score_blank_read

TIMEOUT_S = 420
OCR_MODEL = "apple-vision"
BIG_OLLAMA_GB = 7
# The model-free measuring lane: `see count` / `see odd` answer these cases by pixel measurement.
MEASURE_MODEL = "measure"
MEASURE_CASES = ("C01", "C02", "C03", "O01", "O02", "O03", "O04")


def resident_big_ollama():
    """The `ollama ps` line of a resident model of 7 GB or more, else None."""
    out = subprocess.run(["ollama", "ps"], capture_output=True, text=True, timeout=15)
    if out.returncode:
        raise RuntimeError("`ollama ps` failed, so resident memory is unknown; not starting an MLX run")
    for line in out.stdout.splitlines()[1:]:
        m = re.search(r"(\d+(?:\.\d+)?)\s*(GB|MB)\b", line)
        if m and float(m.group(1)) / (1024 if m.group(2) == "MB" else 1) >= BIG_OLLAMA_GB:
            return line.strip()
    return None


def lanes(case, folder, model):
    """The `see` invocations for one case: a list of {name, cmd, gated, kind}."""
    mode = case["mode"]
    prompt = (folder / "prompt.txt").read_text().strip()
    see, img = str(SEE), str(folder / "image.png")
    tail = ["--json", "-m", model]
    truth = json.loads((folder / "truth.json").read_text())
    if model == MEASURE_MODEL:
        if case["id"] not in MEASURE_CASES:
            raise ValueError(f"the measure lane does not cover {case['id']}")
        if mode == "odd":
            return [dict(name="main", cmd=[see, "odd", img, "--json"], measure=True)]
        cmd = [see, "count", img, "--json"]
        if case["id"] == "C02":
            cmd.append("--filled-only")
        if case["id"] == "C03":
            cmd += ["--color", truth["color"]]
        return [dict(name="main", cmd=cmd, measure=True)]
    if mode == "diff":
        return [dict(name="main", cmd=[see, "diff", str(folder / "a.png"), str(folder / "b.png"), prompt, *tail])]
    if mode == "ui-json":
        return [dict(name="main", cmd=[see, img, "--ui", *tail])]
    if mode == "read":
        return [dict(name="main", cmd=[see, img, *tail])]
    if mode == "crop":
        return [dict(name="full", cmd=[see, img, prompt, *tail]),
                dict(name="crop", cmd=[see, img, "--crop", truth["crop"], prompt, *tail]),
                dict(name="region", cmd=[see, img, "--region", "right", prompt, *tail])]
    if mode == "qa+crop":
        return [dict(name="full", cmd=[see, img, prompt, *tail]),
                dict(name="crop", cmd=[see, img, "--crop", truth["crop"], prompt, *tail])]
    if mode == "ocr+read":
        return [dict(name="main", cmd=[see, img, prompt, *tail])]
    if mode in ("qa", "odd"):
        out = [dict(name="main", cmd=[see, img, prompt, *tail])]
        if case["id"] == "H01":
            out.append(dict(name="read", cmd=[see, img, *tail], gated=False, kind="blank-read"))
        return out
    raise ValueError(f"unsupported mode {mode!r} for {case['id']}")


def ocr_lane(folder):
    return dict(name="ocr", cmd=[str(SEE), str(folder / "image.png"), "--ocr", "--json"])


def parse_envelope(stdout):
    try:
        return json.loads(stdout)
    except ValueError:
        start = stdout.find("{")
        try:
            return json.loads(stdout[start:]) if start >= 0 else {}
        except ValueError:
            return {}


def execute(lane, case_id, truth):
    started = time.monotonic()
    try:
        proc = subprocess.run(lane["cmd"], capture_output=True, text=True, timeout=TIMEOUT_S)
        code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr = 124, (exc.stdout or b"").decode() if isinstance(exc.stdout, bytes) else (exc.stdout or ""), "timeout"
    wall_ms = round((time.monotonic() - started) * 1000)
    env = parse_envelope(stdout)
    text, data = env.get("text") or "", env.get("data")
    if lane.get("measure") and isinstance(data, dict):
        # an ambiguous measurement is an honest non-answer, so it must not score as a pick
        text = f"ANSWER: {data['answer']}" if data.get("answer") is not None else "ANSWER: ambiguous"
    if lane.get("kind") == "blank-read":
        verdict = score_blank_read(text)
    else:
        verdict = score(case_id, text, truth, data)
    return {"name": lane["name"], "cmd": shlex.join(lane["cmd"]), "text": text, "data": data, "wall_ms": wall_ms,
            "see_exit_code": code, "stderr": stderr[-400:], "gated": lane.get("gated", True), "score": verdict}


def already_done(path):
    seen = set()
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                row = json.loads(line)
                seen.add((row["case"], row["seed"]))
            except (ValueError, KeyError):
                continue
    return seen


def folder_for(case, seed):
    folder = case_dir(case["id"], seed)
    if not (folder / "truth.json").exists():
        generate_one(case["id"], seed, case)
    return folder


def append(path, row):
    with path.open("a") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def row_for(model, case, seed, truth, results):
    primary = results[0]
    return {"model": model, "case": case["id"], "seed": seed, "truth": truth, "text": primary["text"],
            "data": primary["data"], "wall_ms": primary["wall_ms"], "see_exit_code": primary["see_exit_code"],
            "score": primary["score"], "lanes": {r["name"]: r for r in results}}


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--model", required=True, help="Ollama tag, mlx:<hf-repo>, or apple-vision for the OCR lane only")
    p.add_argument("--cases", help="comma-separated case ids")
    p.add_argument("--core", action="store_true", help="the 20 core cases")
    p.add_argument("--seeds", default="0,1,2")
    p.add_argument("--dry-run", action="store_true", help="print the see commands, run nothing")
    p.add_argument("--fresh", action="store_true", help="rerun pairs that already have a result")
    p.add_argument("--catalog")
    a = p.parse_args()

    wanted = set(a.cases.split(",")) if a.cases else None
    cases = [c for c in load_cases(a.catalog) if (wanted is None or c["id"] in wanted) and (not a.core or c.get("core"))]
    if a.model == MEASURE_MODEL:
        cases = [c for c in cases if c["id"] in MEASURE_CASES]
    if wanted and wanted - {c["id"] for c in cases}:
        raise SystemExit("unknown case ids: " + ", ".join(sorted(wanted - {c["id"] for c in cases})))
    seeds = tuple(int(s) for s in a.seeds.split(","))
    ocr_only = a.model == OCR_MODEL

    if a.model.startswith("mlx:") and not a.dry_run:
        busy = resident_big_ollama()
        if busy:
            raise SystemExit(f"refusing MLX run, a large Ollama model is resident: {busy}")

    out_dir = result_dir()
    if not ocr_only:
        path = out_dir / (slug(a.model) + ".jsonl")
        done = set() if a.fresh else already_done(path)
        for case in cases:
            for seed in seeds_for(case["id"], seeds):
                if (case["id"], seed) in done:
                    print(f"skip {case['id']} s{seed} (already in {path.name})")
                    continue
                folder = folder_for(case, seed)
                truth = json.loads((folder / "truth.json").read_text())
                plan = lanes(case, folder, a.model)
                if a.dry_run:
                    for lane in plan:
                        print(f"[{case['id']} s{seed} {lane['name']}] {shlex.join(lane['cmd'])}")
                    continue
                append(path, row_for(a.model, case, seed, truth, [execute(l, case["id"], truth) for l in plan]))
                print(f"ran {case['id']} s{seed}")

    ocr_path = out_dir / (slug(OCR_MODEL) + ".jsonl")
    ocr_done = set() if a.fresh else already_done(ocr_path)
    for case in cases:
        if case["mode"] != "ocr+read":
            continue
        for seed in seeds_for(case["id"], seeds):
            if (case["id"], seed) in ocr_done:
                continue
            folder = folder_for(case, seed)
            truth = json.loads((folder / "truth.json").read_text())
            lane = ocr_lane(folder)
            if a.dry_run:
                print(f"[{case['id']} s{seed} ocr] {shlex.join(lane['cmd'])}")
                continue
            append(ocr_path, row_for(OCR_MODEL, case, seed, truth, [execute(lane, case["id"], truth)]))
            print(f"ran {case['id']} s{seed} (ocr lane)")

    if ocr_only and not any(c["mode"] == "ocr+read" for c in cases):
        raise SystemExit("apple-vision only runs ocr+read cases such as T06")
    if not a.dry_run:
        print(f"results in {out_dir}")


if __name__ == "__main__":
    main()
