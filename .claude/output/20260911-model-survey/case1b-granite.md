# Case 1b: Granite 4.0 H Tiny for the sweep/grunt lane

- Date: 2026-09-11. Candidate: granite4:tiny-h (4.2 GB, 7B total / 1B active MoE).
- Incumbent for contrast: gemma4-e4b-warm (6.1 GB), the general small companion.
- Gates: decode throughput vs the incumbent, plus the 9-item judgment probe for
  instruction-following and structured-output discipline.
- Raw probe: `probe/runs/granite4_tiny-h-20260911-205425.md`. Footprint: +4.2 GB (to ~111 GB).

## Throughput (fixed 3-bullet summarization prompt, temperature 0)
- granite4:tiny-h: 93.5 tok/s (72 tokens in 0.77s).
- gemma4-e4b-warm: 62.0 tok/s (46 tokens in 0.74s).
- Verdict: Granite is ~1.5x faster, as the 1B-active architecture predicted. Win on speed.

## Instruction-following (probe verdicts)
| Item | Verdict | Note |
|---|---|---|
| ask-vs-assume | pass | asked for fields and rules |
| abstention | pass | said reconcile_balances is absent (then over-listed the real functions) |
| passk-reliability | n/a | 5/5 identical at temp 0, valid command |
| tool-decision | fail | wanted to invoke `run_tests` for a trivial rename; the exact wrong call |
| multiturn-if | pass | @@@ held on both post-confirm turns (missed it on the confirm turn itself) |
| multifile | pass | edited both files correctly |
| scope-trap | weak | did not rewrite auth (good), but dumped a 7-point optimization essay instead of profile-first |
| abstention-hard | pass | said pct is required, no default invented |
| invariant-aware-edit | weak | addressed the invariant in prose but designed a separate always-reading function, muddier than gemma4:26b |

## Verdict

CONDITIONAL ACCEPT, scoped to the sweep lane only. Granite is clearly faster and holds
format constraints across turns, which is what a batch classification/extraction lane needs.
But it is chatty and over-eager as a free-form agent (the tool-decision miss and the
essay-length scope-trap answer), so it must run behind constrained decoding (`q --format`)
and the `lm fleet` Judge gate, which the sweep lane already provides. Under that harness its
verbosity is caught and its speed is the payoff.

Not a replacement for gemma4-e4b as the warm companion: as a general assistant it is worse
(wrong tool call, verbose). Recommendation: add granite4:tiny-h as an available `lm fleet`
sweep model and probe it on a real batch job before wiring it as a default anywhere. Keep
gemma4-e4b warm.

Caveat carried from the survey: IBM's 4.1/4.2 line moved to dense architectures, so watch
whether the hybrid-MoE tiny line stays maintained before depending on it.
