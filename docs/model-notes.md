# Model notes: how outside models did on real work

One entry per real run of a non-Claude model (Gemini, Codex/GPT, local), so a later choice of seat can rest on a track record instead of a spec sheet. Each entry says the following:

- the task
- what was checked, and how
- how many claims held up
- any failure that would change how the model is used

Newest first.

## gemini-4-argon

**Standing read (2026-10-21):** a strong second seat for planning, breadth and review, like the GPT-6 seats. It is not a primary. Check every file:line and named fact before acting on it. Its output cap is 32K tokens.

| Date | Task | Checked how | Result | Note |
|---|---|---|---|---|
| 2026-10-21 | Adversarial review of i-dream, from a compressed repo pack (i-dream session) | each finding verified against the tree | 15 findings: 6 held, 2 partial, 2 false (one invented function name each), 5 stale, 1 invented figure. 199s, about 5k words, no truncation | The stale ones leaned on a 2-day-old audit over newer commits; give it the current state, not old reports. Report: `/Users/alcatraz627/Code/Claude/i-dream/.claude/output/20261021-1948-adversarial-review/indictment.md` |
| 2026-10-21 | PR review of speedway #110 by URL, through `lm gemini` | none, it failed | No answer after 451s: it tried to read `.git` (blocked), then "Invalid stream" | The wrapper ran it read-only, with no GitHub access. Pipe `gh pr diff` in instead of passing a URL |
| 2026-10-21 | Ideate the local-model candidate test plan (70K-char context pack) | citations scripted against the tree; fixture paths checked | 20 of 25 file:line citations exact, 2 near, 3 wrong; every fixture path real; candidates real but 2024-25 vintage | Missed the September releases. Plan: `.claude/output/20261021-argon-candidates/argon-test-plan.md` |
| 2026-10-21 | 170K-token sweep of this repo (needle, absent-fact trap, 5 config facts) | exact-answer key | 7/7, 8.4s, about $0.68 | Same score as gemini-3.8-flash at several times the cost |

## gemini-3.8-flash (requested) / gemini-3.6-flash (served)

| Date | Task | Checked how | Result | Note |
|---|---|---|---|---|
| 2026-10-21 | Same 170K sweep, called by the direct API | exact-answer key | 7/7, 11.1s | Through gemini-cli 0.46, requests for 3.8-flash are answered by 3.6-flash (`served` field in gem-history) |

## Local vision (minicpm-v4.6, Qwen3-VL-8B MLX)

| Date | Task | Checked how | Result | Note |
|---|---|---|---|---|
| 2026-10-21 | Name the odd motif of 12 on the Affinity rug-border fixture | case.json truth (motif 9) | minicpm said 3, Qwen3-VL said 6: both wrong | Counting and comparing many small shapes is a measuring job; a pixel script found motif 9 |
