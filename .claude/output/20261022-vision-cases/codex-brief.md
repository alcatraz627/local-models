# Build brief: the vision comparison harness (probe/vision/)

You are building a model-comparison harness for the `see` vision tool in this repo.
The case catalog is already designed. Read these first, in full:

- `.claude/output/20261022-vision-cases/ideation.md` (the catalog, scoring rules in section 1)
- `.claude/output/20261022-vision-cases/cases.json` (42 cases, machine-readable)
- `bin/see` help (`bin/see -h` is fine to run; it calls no model)
- `probe/candidates/` (an earlier, weaker suite; do not modify it)
- `probe/fixtures/vis-battery.py` (house style for a model-free check script)

One correction to the catalog: `see diff` now accepts MLX models (`-m mlx:<repo>` or `--mlx`),
so diff cases run on every model, MLX included.

## What to build

All new files go under `probe/vision/`. Use the repo venv python (`.venv/bin/python`, has PIL and numpy if present; check with an import and fall back to PIL-only if numpy is absent).

1. `gen.py` builds every case in cases.json into `probe/vision/fixtures/<case-id>/s<seed>/`
   with `image.png` (or `a.png` and `b.png` for diff), `truth.json`, and `prompt.txt`.
   Three seeds per case (0, 1, 2) unless the case is a fixed repo fixture (for example O04, the
   Affinity rug: copy it from `probe/candidates/fixtures/see-read/rug-border-twelve-motifs/`).
   Truth comes ONLY from the generator's own parameters. Deterministic: running gen twice
   gives byte-identical PNGs. Use the macOS font paths named in ideation.md; fail loudly if a font is missing.
   Implement all 42 cases. If one is genuinely impossible, implement the rest and list it with the reason in `probe/vision/GAPS.md`.

2. `score_lib.py` implements the normalisers in ideation.md section 1.2 exactly (`norm_str`,
   `to_int` incl. number words, `to_num`, `color_of`, `pos_of`, `cell_of`, negation-aware
   `mentions`, `absent_answer`) plus the ANSWER-line extraction and the single-candidate fallback
   from 1.1. Result per check is one of `pass`, `fail`, `format_fail`, with a short `why`.

3. `score.py` scores one model answer against a case truth using the case's scoring rule.
   One scorer function per case id (or per shared rule shape), dispatched by id. No keyword
   bag-of-words scoring anywhere.

4. `baselines.py` implements the deterministic script baselines for every case tagged
   `script_beats_model` (connected components with fill ratio, per-cell pixel means, etc.)
   and runs them on the generated fixtures. Each baseline must hit its truth on every seed.

5. `run.py` runs cases against one model:
   `run.py --model M [--cases C01,T01 | --core] [--seeds 0,1,2] [--dry-run]`.
   It builds the `see` command from the mode table in ideation.md section 1.6 (always pass `-m M`
   explicitly, always `--json`), runs it with a 420 s timeout, records the raw `.text`/`.data`,
   wall ms, the `see` exit code, and the score, and appends one JSON line per (case, seed) to
   `probe/vision/results/<model-slug>.jsonl`. It skips (case, seed) pairs already present for
   that model unless `--fresh`. Before an `mlx:` model it must refuse to run if any Ollama model of 7 GB or
   more is resident (`ollama ps`); before an Ollama model it does nothing special.
   `--dry-run` prints the commands and runs no model.
   `ocr`-mode cases run once (model independent) under the pseudo-model name `apple-vision`.

6. `report.py` reads every results file and writes `probe/vision/REPORT.md`: one matrix of
   cases (rows) by models (columns) showing the pass rate over seeds, a per-capability rollup,
   the format_fail count per model, median wall time per model, and the script-baseline column.
   It also writes `probe/vision/report.json` with the same numbers.

7. `selftest.py`, a model-free check in the house style of vis-battery.py (prints `ok`/`FAIL`
   lines and a final `N/M passed`, exits non-zero on any failure):
   - gen is deterministic (generate twice into temp dirs, compare bytes)
   - every truth.json parses and matches the case's schema
   - every baseline hits its truth on every seed
   - for every scorer: a hand-written correct answer passes, a hand-written wrong answer fails,
     a reply with no ANSWER line and two candidates is `format_fail`, an empty reply is never `pass`,
     and a correct answer phrased differently (synonym, number word, "row 3 col 2" vs "r3c2") passes.
     Write these canned answers in `probe/vision/canned.json`, at least 4 per core case.
   - negation: "there is no circle" does not count as mentioning circle.
   - a mutation check: deliberately corrupt one truth in memory and confirm its scorer then fails
     the canned correct answer (proves the scorer reads the truth).

8. `README.md` in `probe/vision/`: how to generate, run one model, and report, in plain prose.

## Constraints

- Do NOT run `see` with a model, `ollama run/pull`, `imagine`, or any network model call. Running
  `bin/see -h` and `see --ocr` is fine but not needed. The parent agent runs models.
- Do not edit anything outside `probe/vision/` except adding one line to `scripts/verify.sh` that runs
  `.venv/bin/python probe/vision/selftest.py` next to the existing vis-battery line, following its pattern.
- Comments follow the repo style: short, human, explain why. No em dashes in prose.
- Commit your work on the current branch in small commits with plain imperative messages and NO AI attribution trailers.
- When done, run `selftest.py` and `run.py --model minicpm-v4.6 --core --dry-run` and put both outputs at the end of
  `probe/vision/BUILD-NOTES.md`, with anything you could not do.
