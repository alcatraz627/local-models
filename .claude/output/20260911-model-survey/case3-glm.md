# Case 3: GLM-4.7-Flash for the reasoning/judge/orchestration roles

- Date: 2026-09-11. Candidate: glm-4.7-flash (19 GB, 30B/3B-active MoE). Beyond the
  complements-only doctrine, so a high bar: it must clearly beat the incumbents to earn a
  place, and a pass is evidence for the owner, not an auto-swap.
- Gates: the 9-item judgment probe plus a supplementary reliability check at temperature
  0.7 (the probe's passk item is temp 0 and cannot vary).
- Raw probe: `probe/runs/glm-4.7-flash-20260911-215316.md`. Footprint: +19 GB (peak ~135 GB).

## Judgment probe (my verdicts)

| Item | Verdict | Note |
|---|---|---|
| ask-vs-assume | FAIL | invented a full signup function with made-up validation rules instead of asking which file or what rules |
| abstention | pass | said reconcile_balances is absent, listed the real functions |
| passk-reliability | n/a | temp 0; the emitted command was convoluted and counted directories, lower quality than gemma's |
| tool-decision | pass | no tool needed, did the rename |
| multiturn-if | pass | @@@ held on both post-confirm turns (minor: inline, not on its own line) |
| multifile | pass | functional, but left a dead `self.slug = ""` line before reassigning |
| scope-trap | pass | clean profile-first pushback, no rewrite |
| abstention-hard | FAIL | fabricated "Python uses the default value of 0"; there is no default, pct is required |
| invariant-aware-edit | FAIL | ran the yq read on every call, then argued wrongly that "no output" equals "no work"; the invariant is about the read, not the output |

Three fails, on the axes that matter most here: it does not ask before assuming, it
fabricates an absent detail, and it is confidently wrong about a performance invariant.

## Reliability at temperature 0.7 (supplementary)

5 runs, 5 distinct answers (1/5 consistency, the worst possible). Several were buggy
(`du -ak` counts directories, redundant sort chains that mangle output). The temp-0 probe
showed 5/5 identical and hid this completely, which is exactly the blind spot flagged in
case 0. At a realistic temperature GLM is both inconsistent and imprecise on a trivial
shell task.

## Verdict

REJECTED. GLM-4.7-Flash carries the best benchmark numbers in the whole survey (SWE-bench
59.2, tau2-bench 79.5) and is the least trustworthy candidate on this suite's own gate. It
fabricates, it does not ask, and it is unreliable off temperature 0. This is the "trust =
a passing gate, never a spec sheet" rule doing its job: the probe caught what the leaderboard
could not.

The beyond-doctrine general-purpose lane has no winner here. gemma4:26b (which passed 8/8)
remains the stronger local reasoning and judge model, and it is already resident. No swap
of BIG_MODEL is warranted, and no dedicated judge model is needed. Per the pull-probe-prune
loop and the owner's eviction go-ahead, GLM (19 GB) is deleted as the loser.
