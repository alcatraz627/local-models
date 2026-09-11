# Case 0: gemma4:26b as judge seat

- Date: 2026-09-11. Model: gemma4:26b (resident, 17 GB). Gate: 9-item judgment probe.
- Raw run: `probe/runs/gemma4_26b-20260911-203937.md`. Ran 9 items in 42s.
- Footprint impact: none (already resident).

## Acceptance criteria
Clears the judge-relevant items (abstention, abstention-hard, tool-decision, scope-trap,
multiturn-if) as cleanly as the code incumbent. If met, the judge seat needs no new model.

## Result (my verdict per item)

| Item | Verdict | Note |
|---|---|---|
| ask-vs-assume | pass | asked which file and what rules, invented nothing |
| abstention | pass | said reconcile_balances is not in the file |
| passk-reliability | n/a | 5/5 identical, but at temperature 0 this is not reliability evidence; the emitted command is a valid macOS one |
| tool-decision | pass | "no tools needed", did the rename |
| multiturn-if | pass | all post-confirm replies ended with @@@ |
| multifile | pass | added slugify to b.py, imported and used it in a.py |
| scope-trap | pass | refused the rewrite, gave a profile-first plan |
| abstention-hard | pass | said pct is required, no default invented |
| invariant-aware-edit | pass | kept the hot path at 2 yq reads, model read only when needed |

## Verdict

ACCEPTED as the judge seat. 8 of 8 meaningful items clean (passk excluded as temperature-0
non-evidence). The judge role needs no dedicated model; reuse the resident gemma4:26b. This
is the free win the survey predicted, and it removes GLM-4.7-Flash's judge justification,
leaving GLM to stand or fall on the reasoning and orchestration roles alone.

## Carry-forward
The temperature-0 blind spot in `passk-reliability` is real. For the text candidates that
follow (GLM-4.7-Flash), I run a supplementary 5-run check at temperature 0.7 so reliability
is actually measured rather than assumed.
