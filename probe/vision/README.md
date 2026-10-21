# Vision comparison harness

This folder compares vision models on the jobs `see` does every day. It holds 42 cases (20 of them core), each built from a generator whose own parameters are the answer key, so no result depends on a person's or a model's guess. `CATALOG.md` explains every case and the scoring rules, and `cases.json` is the same catalog in machine form. Nothing here calls a model unless you run `run.py` yourself.

Everything runs with the repo venv: `.venv/bin/python`.

## Build the fixtures

    .venv/bin/python probe/vision/gen.py

This writes `fixtures/<case>/s<seed>/` with `image.png` (or `a.png` and `b.png` for diff cases), `truth.json` and `prompt.txt`. Seeds 0, 1 and 2 are built for every case except the ones that copy a fixed repo image (G04, D01, D04, D05, D06, O04) and T06, which have only seed 0. Running it twice gives byte-identical files, so the folder is not committed. Use `--cases C01,T01` or `--seeds 0,1,2,3` to build less or more.

## Check the harness (no model)

    .venv/bin/python probe/vision/selftest.py

It proves the generators are deterministic, every truth matches its schema, the script baselines hit the truth on every seed, and every scorer passes a correct answer, fails wrong ones, refuses an empty reply and notices when its truth is corrupted. `scripts/verify.sh` runs it too.

## Run one model

    .venv/bin/python probe/vision/run.py --model minicpm-v4.6 --core --dry-run   # print the see commands only
    .venv/bin/python probe/vision/run.py --model minicpm-v4.6 --core
    .venv/bin/python probe/vision/run.py --model mlx:mlx-community/Qwen3-VL-8B-Instruct-4bit --cases C01,D02

`-m` is always passed to `see` explicitly, with `--json`, and each call has a 420 second timeout. One line per (case, seed) is appended to `results/<model>.jsonl` with the raw reply, the wall time, the `see` exit code and the score. Pairs already in that file are skipped, so an interrupted run resumes; add `--fresh` to redo them (the report keeps the latest line). Before an `mlx:` model the runner refuses to start if an Ollama model of 7 GB or more is resident.

Some cases run more than one `see` call and keep them all in the row: the crop cases (R01, B02) run full frame, `--crop` and for R01 `--region right`, and H01 adds a plain-read companion that is reported but not gated. T06 also runs the Apple Vision OCR lane once, under the pseudo-model `apple-vision`, whatever model you pass. `--model apple-vision --cases T06` runs only that lane.

## Report

    .venv/bin/python probe/vision/report.py

This writes `REPORT.md` and `report.json`: a case by model matrix of pass counts, a per-capability rollup, format_fail counts and median wall time per model, the script-baseline column, crop lift, and counts of the named failure shapes (answered_decoy, band_trap and so on). `format_fail` means the model broke the `ANSWER:` contract, which is counted apart from a wrong answer.

## Script baselines

    .venv/bin/python probe/vision/baselines.py

Runs the deterministic baselines for the five cases tagged `script_beats_model` (C02, O03, D02, D07, T06), scores them with the same scorers and writes `baselines.json`, which the report reads.

## How scoring works

A reply is scored from its last `ANSWER:` line. Without one, the whole reply is accepted only if it holds exactly one candidate of the right kind; two candidates, or none, is `format_fail`. Numbers, colours, positions and grid cells go through the normalisers in `score_lib.py`, so "twenty-three", "row 3 col 2" and "scarlet" match their truth. Each case has its own scorer in `score.py`, and every hallucination trap pairs its "must not invent" rule with a positive answer, so silence cannot pass.

## Files

| File | Job |
|---|---|
| `gen.py` | builds every case from seeded parameters |
| `score_lib.py` | answer-line extraction and the normalisers |
| `score.py` | one scorer per case, dispatched by id |
| `baselines.py` | script baselines for the `script_beats_model` cases |
| `run.py` | runs cases through `see` for one model |
| `report.py` | builds `REPORT.md` and `report.json` |
| `selftest.py`, `canned.json` | model-free checks and the hand-written replies they use |
| `cases.json`, `CATALOG.md` | the catalog, copied from the design folder |
| `BUILD-NOTES.md` | how it was verified, and where it differs from the catalog |
