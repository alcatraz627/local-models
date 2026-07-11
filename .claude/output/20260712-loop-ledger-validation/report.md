# Phase C loop ledger — adversarial validation report

<!-- sessions: vis-ab-3c@2026-07-12 -->

**Under test:** F10 battery + lib/vis-ledger.py + `see diff --no-read` (3 commits on
feat/vis-compare). **Validator:** one sonnet adversarial sub-agent (pinned, no nesting,
mutation-testing mandated); findings returned inline per /bloop Phase 4.4; persisted by
the parent. Delivery clause worked — findings arrived without a chase-up ping.

## VERDICT: ISSUES-FOUND

### BLOCKER — no JSON-shape validation; malformed shapes traceback

`load_json`/`die` guard syntax and file errors correctly, but nothing validates parsed
shape before `.get()`/`["rounds"]`/`os.makedirs()`. Confirmed tracebacks (exit 1, not
the promised structured exit-2 error): array verdict · string/dict/list-of-strings
`divergences` · array `--pack` · ledger corrupted to `[]` or `{}` · loop-dir is a FILE ·
unwritable parent. Systemic gap vs the errors-propose-fixes convention.

### MAJOR 1 — status fabricates an empty loop on a corrupt ledger

`add` uses `ledger["rounds"]` (crashes on `{}`); `status` uses `.get("rounds", [])` and
silently reports "0 rounds" for a ledger that may have had history — a fabrication in a
codebase strict about exactly that. The two commands disagree on identical input.

### MAJOR 2 — F10 cannot detect a de-atomized write

Mutating `write_atomic` to a plain direct write leaves the battery 25/25 green. The
shipped mechanism is correct (tmp + same-dir `os.replace`); the guard just can't see it
regress. Other mutations (stall threshold, new/regressed swap, poor-pair block) were all
caught.

### MINOR — --no-read mislabels the model in the human audit trail

`read.md` and `see-history.jsonl` echo `gemma4:26b` on runs where no model fired
(`evidence.json` cost is correctly empty). Machine truth accurate, human trail not.

### NIT — no ledger file locking

Two concurrent `add`s to one loop-dir would lose an update (not corrupt — os.replace
keeps writes whole). Loop rounds are sequential by design; documented, not fixed.

## What held (validator coverage)

Transition algebra incl. flapping ids (never re-`new`, always `regressed` on return) ·
5× identical rounds → persisting only · poor-pair rejection strictly before ledger IO ·
stall exactly at ≥2 with reset-on-fixed · policy-pass ≠ pass-with-notes · status/add
signal agreement (uncorrupted) · --no-read pack parity key-by-key, no ollama probe,
artifacts + both history journals intact · flag rejected outside diff · bare-python3
claim true (3.14.5) · battery baseline and post-revert 25/25; tree clean after all
mutation tests.

## Resolution (see commits after this report)

- BLOCKER fixed with a mechanism: a shape-validation layer (`expect()`) after every
  parse — verdict/pack/ledger/rounds each checked before use; loop-dir pre-checked;
  makedirs wrapped. Both `add` and `status` share the same strict ledger loader
  (fixes MAJOR 1 — status now errors with a restore-proposing fix instead of lying).
- MAJOR 2: F10c imports the module and poisons `json.dump` mid-write — the original
  ledger must survive the crash byte-identical. Catches the de-atomization mutation.
- F10b covers the exploited malformed-shape classes end-to-end (exit 2 + parseable
  `ok:false` JSON + no traceback, for add AND status).
- MINOR: read.md/history model field says `none (--no-read)` on deliberate skips.
- NIT: sequential-adds-by-design documented in the module docstring.
