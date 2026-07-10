# unfinished-v1 — exercise results

The finish-a-codebase procedure exercise: can the local coder complete a
partial multi-file package when a test suite defines done? Run 2026-07-07,
model `qwen3.6:35b-a3b`, conducted by Claude per docs/07 Phase 1 (worker =
`q complete --ctx -`, Judge = pytest, retry = judge evidence fed back).

## Verdict: completed, 16/16 tests

| step | file | attempt | result |
|---|---|---|---|
| 1 | stats.py (3 stubs, 11 tests) | 1 | all green first shot (~25s, 794 tok) |
| 2 | report.py (2 stubs, 4 tests) | 1 | 15/16 — render_table read "padded right to 8" as right-*aligned* |
| 2 | report.py + judge evidence | 2 | still 15/16 — fixed alignment, added a stray separator space |
| 2 | report.py + character-precise evidence | 3 | 16/16 |

Worker cost: 4 calls, ~80s local compute, $0. The worker even excluded
bool from numerics in stats.py (bool subclasses int) — untested subtlety.

## What generalizes

- The Judge is the trust surface. Both report.py misses were caught
  mechanically; nothing wrong ever reached the tree.
- Retry feedback must be evidence + a precise delta. Restating the failed
  assertion produced a near-miss; the character-level diagnosis converged
  in one round. Budget ~2 surgical retries before the conductor takes over.
- Workers follow prose over examples. The docstring example line
  disambiguated the format; the model followed the ambiguous prose twice.
  Spec stubs example-first for local workers.
- Conductor pipelines must be bash, not zsh: zsh `echo` expands the \n
  escapes inside q's JSON envelope and corrupts it (use printf or a
  #!/bin/bash script — see conduct.sh).

## Rerun

```bash
cp -R probe/fixtures/unfinished-v1 /tmp/finish-run && cd /tmp/finish-run
./conduct.sh /tmp/finish-run csvstats/stats.py csvstats/parser.py
# apply candidate, judge with pytest, iterate report.py the same way
```
