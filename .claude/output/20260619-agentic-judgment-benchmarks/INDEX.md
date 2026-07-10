# Benchmarks for agentic judgment — not speed, not math (2026-06-19)

Live-web scan of the benchmarks that measure what the user cares about:
**reliability · smart assumptions · knowing when to ask / research / delegate / scan**.
Detail files: [agentic-reliability-tooluse](agentic-reliability-tooluse.md) ·
[metacognition (master)](metacognition-clarification-calibration.md) +
[clarification](clarification-proactivity.md) · [abstention](abstention.md) ·
[calibration-hallucination](calibration-hallucination.md) ·
[instruction-following](instruction-following.md) · [smart-defaults](smart-defaults-humanpref.md)

## What the PRIOR (open-model) scan actually used — and why it's the wrong lens for you
Grep of those 8 files: **SWE-bench, MMMU, OCRBench, MTEB, Open ASR, EQ-Bench, GPQA, MMLU-Pro, math, HumanEval/GSM8K** — capability/accuracy boards. Exactly **one** judgment-relevant mention (IFEval, once). So your instinct is correct: that scan ranked models on getting answers *right*, not on *behaving reliably and knowing its limits*.

## The benchmarks that DO measure your axes

| Your axis | Trust these | Metric / why | Ignore |
|---|---|---|---|
| **Reliability (no flaking)** | **τ²-bench (pass^k)**, IFBench, Multi-IF | `pass^k` = succeeds k times in a row (decays exponentially) | pass@1 headlines, plain IFEval (saturated/gamed) |
| **Smart assumptions / when to ASK** | InteractComp, ClarifyMT-Bench, BFCL **irrelevance-detection**, ACEBench "Special" | scores correctly *refraining* / asking under ambiguity | LMArena/Arena-Hard (reward confident over-answering) |
| **When to research / delegate / scan** | GAIA, AssistantBench, BrowseComp, **Agent Arena** (retries/steerability) | tool/search-decision under real tasks | GAIA *headline* (ensembles, gameable) |
| **Knowing what it doesn't know** | **AbstentionBench**, Refusal Index | abstains on unanswerable/underspecified | TruthfulQA (saturated, small models top it) |
| **Calibration / hallucination** | AA-Omniscience, SimpleQA-Verified, **Vectara HHEM** (live) | confidence matches correctness; grounded-ness | — |
| **Long-horizon coherence** | **Vending-Bench 2** | does it derail over a long run | context-window size (uncorrelated) |

## The four cross-cutting findings that actually change a model pick

1. **`pass^k` is THE reliability number.** 90% pass@1 → ~57% pass^8. Headline scores overstate real reliability by ~20 pts. Only **τ²-bench (Sierra)** reports it.
2. **Reasoning fine-tuning HURTS judgment.** AbstentionBench: reasoning-distilled models (R1-Distill, QwQ, s1.1) are **~24% worse at abstaining** and drop on strict IFEval. Picking by reasoning-leaderboard rank *systematically selects the worst abstainers.* → prefer **non-"thinking" instruct** variants.
3. **Human-preference arenas measure the wrong thing for you** — they reward confident, complete answers, i.e. the opposite of "ask/abstain when unsure."
4. **Many famous agent benchmarks are gameable** — a 2026 Berkeley RDI study showed 8 major ones reachable to near-perfect without solving the task. Trust *reliability-metric* boards (τ²/BFCL-irrelevance/AbstentionBench), not execution-headline boards.

## Open-weight reality (you run local on 64GB)
Judgment axes are **not** closed-model strongholds. On τ-bench, **GLM-4.7 (#2, 87.4%) beats Claude Opus 4.5/GPT-5.2**; GLM-4.7-Flash hits 79.5%. **Qwen (2.5/3/3.5, 7B–32B) is the recurring winner across all five metacognition families** and fits a 64GB Mac quantized. But: **open models are largely unbenchmarked on long-horizon (Vending-Bench)** — the biggest evidence gap.

## Honest caveats
No model (open or closed) is well-calibrated in absolute terms (ECE 0.1–0.4). "ClariQ-2" appears not to exist (hearsay). IN3/ProactiveAgent headline numbers come from models fine-tuned on their own benchmark. Newest τ²/Agent-Arena/GLM-4.7 figures are `[single-source]`; orderings consistent, decimals approximate.
