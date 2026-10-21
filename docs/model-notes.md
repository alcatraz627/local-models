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
| 2026-10-21 | PR review, speedway #110 (56 files, +5962), offline pack over the direct API | each finding read against the code at head (shallow) | 5 findings: 2 held, 1 plausible, 2 false (one shared with Codex). 670K tokens in, 115s, first token at 82s | Via gemini-cli the same pack hung for 16+ min without sending; large inputs must go to the API directly. Comparison: `.claude/output/20261021-pr110-review/COMPARISON.md` |
| 2026-10-21 | Adversarial review of i-dream, from a compressed repo pack (i-dream session) | each finding verified against the tree | 15 findings: 6 held, 2 partial, 2 false (one invented function name each), 5 stale, 1 invented figure. 199s, about 5k words, no truncation | The stale ones leaned on a 2-day-old audit over newer commits; give it the current state, not old reports. Report: `/Users/alcatraz627/Code/Claude/i-dream/.claude/output/20261021-1948-adversarial-review/indictment.md` |
| 2026-10-21 | PR review of speedway #110 by URL, through `lm gemini` | none, it failed | No answer after 451s: it tried to read `.git` (blocked), then "Invalid stream" | The wrapper ran it read-only, with no GitHub access. Pipe `gh pr diff` in instead of passing a URL |
| 2026-10-21 | Ideate the local-model candidate test plan (70K-char context pack) | citations scripted against the tree; fixture paths checked | 20 of 25 file:line citations exact, 2 near, 3 wrong; every fixture path real; candidates real but 2024-25 vintage | Missed the September releases. Plan: `.claude/output/20261021-argon-candidates/argon-test-plan.md` |
| 2026-10-21 | 170K-token sweep of this repo (needle, absent-fact trap, 5 config facts) | exact-answer key | 7/7, 8.4s, about $0.68 | Same score as gemini-3.8-flash at several times the cost |

## gemini-3.8-flash (requested) / gemini-3.6-flash (served)

| Date | Task | Checked how | Result | Note |
|---|---|---|---|---|
| 2026-10-22 | 290 KB needle question, auto-routed to the direct API | exact answer | right, 3 s, served by 3.8-flash | gemini-cli 0.64 (upgraded from 0.46) now also serves 3.8-flash as requested |
| 2026-10-21 | Same 170K sweep, called by the direct API | exact-answer key | 7/7, 11.1s | Through gemini-cli 0.46, requests for 3.8-flash are answered by 3.6-flash (`served` field in gem-history) |

## Codex gpt-6-luna

| Date | Task | Checked how | Result | Note |
|---|---|---|---|---|
| 2026-10-22 | Build the vision harness and fix 23 CLI review findings, two runs at once | the drafts were finished and tested by Claude sonnet seats | Both runs hit the account usage limit midway: full drafts of the harness files, none run; partial edits to `_lib.sh` and `q` | Quota resets 2026-11-20. Its harness drafts were sound enough to finish, with one crash (a missing baseline) |
| 2026-10-21 | PR review, speedway #110, exploring the exported tree read-only, effort high | each finding read against the code at head (shallow) | 2 findings: 1 held (the most product-relevant of either review), 1 false (shared with Argon) | gpt-6-astra and gpt-6-sol are refused on this ChatGPT login; luna is the heaviest accepted |

## Local vision (minicpm-v4.6, Qwen3-VL-8B MLX)

| Date | Task | Checked how | Result | Note |
|---|---|---|---|---|
| 2026-10-22 | 42-case vision harness, 3 seeds, 7 models | generated truths, meaning-based scorers, every failing cell read | Qwen3-VL-8B 101/112, Qwen3.5-9B 100, qwen3.6:35b 98, gemma4:26b 97, Qwen3-VL-4B 85, gemma4-e4b 78, minicpm-v4.6 74 | `docs/20261022-model-comparison.md` |
| 2026-10-21 | Name the odd motif of 12 on the Affinity rug-border fixture | case.json truth (motif 9) | minicpm said 3, Qwen3-VL said 6: both wrong | Counting and comparing many small shapes is a measuring job; a pixel script found motif 9 |
