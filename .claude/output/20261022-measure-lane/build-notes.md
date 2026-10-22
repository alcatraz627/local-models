# Build notes: measuring lane for `see` (count and odd)

Worktree: /Users/alcatraz627/Code/local-models-measure, branch `measure-lane` (6 commits off main d70f6b3, not pushed, not merged).
The worktree has a `.venv` symlink to the main repo's venv (untracked, not committed).

## What was built

- `/Users/alcatraz627/Code/local-models-measure/lib/measure.py`: `count IMG [--color] [--min-area] [--filled-only]` and `odd IMG [--min-area]`. PIL + numpy + scipy (scipy is already in the venv; `ndimage.label` does the connected components).
  - Background is the dominant border colour (binned mode of a border ring). Foreground is CIE76 distance above 12. I wrote a small vectorised Lab conversion rather than import `vis-compare.py` (hyphenated filename, scalar-only helper).
  - A blob covering at least half the frame is treated as a panel and objects are segmented inside it (only kept if that yields 2+ objects).
  - `count`: min area defaults to `max(6, 2e-5 * W * H)`; `--filled-only` keeps fill ratio above 0.6 (area over hole-filled area); `--color` matches the nearest canonical name in Lab, or a hex within delta E 25. Flags `ambiguous` plus a `range` when a blob is over 2x the median area (touching objects).
  - `odd`: picks the largest group of similar-sized objects by total ink (so digit captions are not compared with the items; counting members picked the captions first, which I fixed). Features against the median: Lab colour, shape mask 16x16, area, aspect, each scaled so about 1.0 is "just noticeable". Reading-order index is row-major, 1-based. Ambiguous when the top score is under 1.0 or the runner-up is at least 0.6 of the top, or fewer than 3 comparable objects. Ambiguous replies carry `answer: null` and two `candidates`.
  - JSON shape: `{ok, job, answer, objects[{i,bbox,area,color,rgb}], confidence, ambiguous, why}` plus `range` (count), `margin`/`candidates`/`bbox` (odd). The objects list is capped at 60 rows. Errors are `{ok:false, code, message}` with exit 2 (usage) or 12 (unreadable); a catch-all turns any crash into a structured error.
- `bin/see`: verbs `see count` and `see odd` (flags `--color`, `--min-area`, `--filled-only`, `--json`), in `-h`, no model and no ollama. They reuse the shared tail, so each run writes an artifact folder (`read.md`, `meta.json`, source copy) and a history row with mode `count`/`odd`, model `measure`. `--json` puts the measurement under `.data`, the one-line answer in `.text`. Misuse (`--color` on a normal read, odd with count-only flags, extra positionals) exits 2.
- `docs/CAPABILITIES.md`: examples next to `see diff` and a short paragraph.
- `probe/vision/run.py`: pseudo-model `measure` (cases C01, C02, C03, O01-O04; C02 uses `--filled-only`, C03 `--color <asked>`). The answer is wrapped as `ANSWER: <n>`, or `ANSWER: ambiguous` when null, and scored by the existing scorer. Results in `probe/vision/results/measure.jsonl`; `REPORT.md`/`report.json` regenerated (now 9 models).
- `probe/fixtures/measure-check.py` (32 checks), wired into `scripts/verify.sh` after the vision selftest.

## Check output

`measure-check.py`: 32/32 passed. Covers every seed of C01, C02 (filled-only), C03 (asked colour, plus unfiltered total), O01, O02, O03; O04; blank image (count 0, odd answer null and ambiguous); two identical items and four identical items (odd ambiguous); merged blob (count ambiguous with range); exit codes 2 and 12 with no traceback.
`probe/vision/selftest.py`: 26/26 passed. `bash -n` clean on `bin/see` and `scripts/verify.sh`. The full `scripts/verify.sh` was not run (it needs live models, which the brief forbids).
Harness: `run.py --model measure`: 18/18 pass on the generated cases, O04 is `ANSWER: ambiguous` (scored fail, honestly).

## Red then green proof

1. `AMBIGUOUS_RATIO = 0.6` changed to `9.0` (never ambiguous): 31/32, exit 1. `FAIL O04 rug: answers 9 or says ambiguous, never a wrong index [got 354]`. The measurer invented an index on the rug.
2. `FG_DELTA_E = 12` changed to `400` (nothing is foreground): 9/32, exit 1, every count and odd fixture red.
Both mutations reverted with `git checkout lib/measure.py`; rerun is 32/32 green.
Note: the two-identical-items checks stayed green under mutation 1, because with identical items the top score is 0 and the "under 1.0" rule still catches them. Those checks are guarded by that rule, not by the ratio.

## O04 (the real rug border): not solved, reports ambiguous

The general method cannot isolate the twelve motifs. A thin sage line runs through all of them and a pink band overlaps motifs 3 to 5, so they merge into one big blob that is dropped from the comparison. The biggest group of similar objects left is the roughly 700 diamonds in the pattern rows, where two diamonds tie, so `odd` returns `answer: null`, `ambiguous: true`, with a why that names the ignored larger blob ("touching items can hide the real outlier"). Candidate numbers in that case (e.g. 354, 349) are diamond indices and are meaningless to the user; only `ambiguous` is the useful signal. I did not special-case the fixture. A real fix would need colour-class splitting plus line removal, which I judged to be fixture-shaped work.

## Not done / caveats

- Not merged or pushed; the worktree is left in place with the symlinked `.venv`.
- `odd` on busy scenes returns candidates from the wrong object group (see O04); a future improvement is to name the ignored blobs' bboxes in the output.
- Shapes are measured per component, so an item made of several disconnected pieces (an icon with a gap) counts as several objects.
- The 2x merged-area test in `count` cannot see touching objects of equal count when all objects merge into one blob that is the only one (needs 3+ objects).
- `--color` names are canonical Tailwind-ish values; dark navy reads as black.
