# Fleet-over-real-code-task — the routing experiment (STATE §PENDING item)

<!-- sessions: vis-ab-3c@2026-07-13 -->

**Question** (from project memory + docs/07 Task #8 framing): can the local tier do
Claude-Code-class code work well enough to route real units to it — "dedicate
resources iff efficacy is ballpark of cloud"?

## Design

The strongest available ground truth: the E1 numeric-position-deltas task this repo
shipped on 2026-07-11 (commit `29dd60d`) — a real multi-function change with a
correctness contract, a known-good reference implementation, and a mechanical judge
(battery F9/F9b, red-first proven).

- Worktree at the pre-E1 commit (`3c38c1a`), current battery + lib deps copied in;
  judge confirmed RED (30/33 — exactly the three capability checks).
- Dispatch prompt (preserved: scratchpad `e1-task-prompt.txt`, 100 lines): task spec
  (including the malformed-geometry skip rule, SPEC-STATED ONLY — not shown as a
  test), the F9 contract verbatim, the two current functions. This mirrors a real
  fixture-first /bloop dispatch.
- Subject: `qwen3.6:35b-a3b` (the on-disk code tier, 23GB) via `q --ctx -m code`.
  Patch applied mechanically (no human/cloud edits to the model's code).

## Result

| metric | value |
|---|---|
| judge after apply | **33/33 GREEN, round 1** — zero retries |
| wall time | 35.2s (model resident; cold-load would add minutes) |
| tokens out | 1,383 |
| spec-only requirement (F9b skip-malformed) | implemented correctly unprompted-by-test |
| defects | redundant imports copied from test context (diff noise, harmless) |

## Decision (scoped to this data — n=1)

1. **The scoped-worker-under-a-judge seat is CLEARED** by the on-disk 35b coder:
   fixture-first implementation units with a mechanical judge can route to the local
   lane. This is the seat docs/09's fleet design describes; docs/03's boundary holds
   (the local model drove no tools — dispatch, apply, and judge stayed with the
   orchestrator).
2. **NOT evidenced: the autonomous tier.** Task decomposition, schema/design
   judgment, fixture authorship, and repo navigation were all supplied by the cloud
   orchestrator in the prompt. No claim is made about un-scaffolded work.
3. **Open: the 80B candidate** (Qwen3-Coder-Next 80B-A3B, per project memory) is not
   on disk (~50GB pull = user decision). The harness here is repeatable — same
   worktree recipe, prompt, and judge — for a like-for-like comparison when pulled.
4. `lm probe` (the 9-item judgment harness) remains the complementary breadth gate;
   this experiment is depth on one real task.

## Routing rule (proposed for docs/STATE)

Route to the local code tier when ALL of: the unit is scoped to named functions/files
· a mechanical judge exists BEFORE dispatch (failing test, schema check, battery) ·
the orchestrator applies + judges. Otherwise stay cloud-side. Escalate one step on a
failed judge round, per model-tier doctrine.
