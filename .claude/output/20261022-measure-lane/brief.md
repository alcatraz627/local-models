# Build brief: a measuring lane for `see` (count and odd-one-out)

## Why

The vision comparison (docs/20261022-model-comparison.md, probe/vision/REPORT.md) showed that
local vision models are unreliable at two jobs where a script is exact:

- counting many small similar shapes (case C02: 23 small dots plus hollow decoys; most models
  were off, the script baseline was right on every seed)
- finding the one item that differs among repeated items (O03 colour, O02 rotation, O04 the
  real Affinity rug border, where motif 9 is the outlier)

The owner wants EFFICACY for vision work: answers that are right, not plausible. Build a
model-free measuring lane so these jobs are answered by measurement.

## What to build

1. `lib/measure.py` (repo venv python, PIL + numpy) with two jobs:
   - `count IMG [--color NAME|#hex] [--min-area N] [--filled-only]` counts distinct foreground
     objects. Background comes from the image border (dominant border colour), not a fixed
     threshold; foreground is everything far enough from it (perceptual distance, e.g. CIE76
     on Lab, the repo already has a ΔE helper in lib/vis-compare.py you may reuse). Connected
     components with a minimum area (default scales with image size) drop specks. `--color`
     restricts to objects whose mean colour is that colour (accept canonical names: red, green,
     blue, yellow, orange, purple, gray, black, white, plus hex). `--filled-only` drops hollow
     outlines (fill ratio of the component vs its filled bounding region).
   - `odd IMG` finds the single outlier among repeated objects. Segment objects as above,
     compute a feature vector per object (area, bbox aspect, mean colour in Lab, a normalised
     downsampled shape mask so rotation and shape changes register), and pick the object whose
     distance from the median feature vector is largest. Report its index in reading order
     (row-major, top-to-bottom then left-to-right, 1-based) and its bbox.
   - Both return JSON: `{ok, job, answer, objects:[{i, bbox, area, color}], confidence, why}`.
     `confidence` must be honest: for `odd`, report the margin between the top outlier and the
     runner-up; if the margin is small, set `"ambiguous": true` and name the two candidates
     instead of guessing. For `count`, flag `"ambiguous": true` when objects touch or merge
     (component area far above the median) and report the count range.
   - Fail closed with a structured error (exit 2 usage, 12 unreadable image) and never a
     traceback.
2. Wire it into `bin/see` as verbs: `see count IMG [opts] [--json]` and `see odd IMG [--json]`,
   following how existing verbs (`see diff`, `see more`) are dispatched and how `--json` and the
   history and artifact store work. Text mode prints a one-line answer plus the why. Histories:
   log a row with mode `count`/`odd` like other reads. Add both to `see -h` and to
   docs/CAPABILITIES.md next to `see diff`.
3. Add the measuring answers as a lane in the vision harness so the report compares them to the
   models: in `probe/vision/run.py`, a pseudo-model `measure` that runs `see count`/`see odd` on
   the cases where it applies (C01, C02, C03, O01, O02, O03, O04) and scores the answer with the
   existing scorer (wrap the answer as `ANSWER: <x>`).
4. A model-free check script `probe/fixtures/measure-check.py` in the house style of
   vis-battery.py (ok/FAIL lines, N/M passed, non-zero exit on failure), wired into
   scripts/verify.sh next to the vision selftest. It must cover: every seed of C01, C02, C03 (with
   the asked colour), O01, O02, O03 from probe/vision/fixtures (run probe/vision/gen.py first if
   missing); the O04 rug (truth: motif 9); a blank image (count 0, odd → error or ambiguous, never
   an invented index); two identical items (odd → ambiguous); and a red-then-green proof that at
   least one check fails when you break the measurer (record that in the build notes).

## Constraints

- Work in the git worktree /Users/alcatraz627/Code/local-models-measure (branch measure-lane,
  create it from main with `git -C /Users/alcatraz627/Code/local-models worktree add ...`).
  Python: /Users/alcatraz627/Code/local-models/.venv/bin/python.
- Do not run any vision model, ollama, mlx, imagine or gemini. Model-free only.
- If O04 (the real rug) cannot be solved robustly by the general method, say so honestly in
  the build notes and make `odd` report ambiguous on it rather than special-casing the fixture.
  Never special-case a fixture to pass a check.
- Comments: short, human, say why. No em dashes in prose.
- Commit in small commits, plain imperative subjects, no AI attribution trailers.
- Write /Users/alcatraz627/Code/local-models/.claude/output/20261022-measure-lane/build-notes.md
  before returning: what was built, the check output, the red/green proof, the O04 result, and
  anything not done.
