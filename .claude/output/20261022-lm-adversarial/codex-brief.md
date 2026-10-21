# Build brief: fix the lm CLI review findings

Read `/Users/alcatraz627/Code/local-models/.claude/output/20261022-lm-adversarial/review.md` in full.
It is an adversarial review of this repo's CLI tools with 23 defects (D1-D23) and 10 ideas, each with
evidence and a proposed fix. Your job is to fix them in this worktree.

## Scope

Fix every defect D1 through D23, with these notes:

- D21 is mostly done already: `lm gemini` routes large input to `lib/gemini-direct.py` (see `--direct`
  in `lib/gemini`), the docstring is fixed, and history is written by the wrapper. Only check that
  nothing in D21 is still true; do not rebuild it.
- D2 and D3: build ONE shared helper set in `bin/_lib.sh` (unknown-flag rejection with a `--`
  escape, and `need_arg` for flags that take a value) and use it in q, see, imagine, warm, review and
  lib/gemini, so the messages read the same everywhere. Negative numbers used as history indexes
  (`q show -1`) and documented short flags must keep working. Check every parser's existing flags
  before adding the rejection branch so no real flag is rejected.
- D9: show local time as `MM-DD HH:MM` in all history views and timeline.
- D10: extend `lm doctor` as described and add `lm doctor --json`.
- D14: add `--json` where listed; history `--json` entries carry their line number `n`.

Also build these ideas: 1 (timeline rows carry `tool#N`, plus `lm timeline --errors`, `--tool T`,
`--json`, and an `lm last [tool]` verb), 2 (q `--json` gains `intent`, `entry`, `cold_load`),
5 (did-you-mean for unknown `lm` verbs and q intents), 6 (`lm --version`), 7 (tok/s from the
model's eval time, not wall time), 9 (`lm status` shows lease TTL and tier names), and 10 (write one
exit-code table into `docs/CAPABILITIES.md` and move warm, imagine and lm onto it where they use 1
for everything). Skip ideas 3 and 4.

## How to verify (required)

- `bash -n` every shell file you touch.
- Re-run every command quoted in the review's evidence and confirm the new behaviour. Paste the
  before and after for each defect into `.claude/output/lm-fixes-evidence.md` in this worktree.
- `lm timeline 20` must finish in under 3 seconds (time it).
- You may run `q "say ok"` at most 5 times (small local tier). Do NOT run imagine generation, review,
  fleet, bench, `see` on images with a model, or any `lm gemini` prompt (they cost money or minutes).
  `lm gemini -h`, `lm gemini models`, `lm gemini history`, `lm gemini watch abc` are fine.
- Run `bash scripts/verify.sh` at the end and record the pass and fail counts. Four failures are
  known and pre-existing (vis battery F6 is now fixed; guard-model-tier block path, warm-morning
  missing, warm-evening-off not loaded). Any new failure is yours to fix.

## Constraints

- The repo venv is at `/Users/alcatraz627/Code/local-models/.venv` (this worktree has none).
- Keep the existing style: short human comments that say why, no em dashes in prose, no
  "Phase N" or dated archaeology in comments.
- Do not change model names, tiers, residency policy or the disk budget.
- Do not edit `probe/vision/` or `probe/candidates/`.
- Commit in small logical commits with plain imperative subjects and NO AI attribution trailers.
- Finish with a summary at `.claude/output/lm-fixes-summary.md`: a table of D1-D23 and the built ideas,
  each marked fixed, partly fixed, or not fixed with the reason.
