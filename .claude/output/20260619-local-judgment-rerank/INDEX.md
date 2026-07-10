# Local candidate re-rank by JUDGMENT axes (2026-06-19)

Re-ranking the 64GB-runnable agentic candidates by reliability / ask-vs-assume /
abstention / calibration / instruction-following — NOT speed or SWE-bench. Built from
two live matrices: [reliability-tooluse-matrix](reliability-tooluse-matrix.md) ·
[metacognition-matrix](metacognition-matrix.md).

## Verification first (names were uncertain; now grounded against Hugging Face)

| Model | Real? | HF / source | Note |
|---|---|---|---|
| **Qwen3-Next-80B-A3B-Instruct** | ✅ | `Qwen/Qwen3-Next-80B-A3B-Instruct` | GENERAL model, **non-thinking Instruct** variant exists (Thinking is separate) |
| **Qwen3-Coder-Next** (80B-A3B) | ✅ | qwen.ai/blog `qwen3-coder-next`, GGUF via Unsloth | CODING-specialized, built on Qwen3-Next-Base, ~70.6 SWE-bench. **Distinct from the above.** |
| Gemma 4 31B / 26B-A4B | ✅ | `google/gemma-4-31B-it`, `google/gemma-4-26B-A4B-it` | Apr 2 2026; configurable thinking |
| GLM-4.5-Air 106B-A12B | ✅ | `zai-org` (MIT) | Jul 2025; heavy (~tight on 64GB at 4-bit) |
| GLM-4.7-Flash | ✅ | Z.ai, Jan 19 2026 | the τ-bench small-model star |
| Qwen3.6-35B-A3B / 27B | ⚠️ unverified | board shows Qwen3.5 | confirm exact tag before relying |

## The headline finding: you CAN'T pick by leaderboard here — the data doesn't exist

Across 9 candidates × the judgment benchmarks, **most cells are "no data."** No public
source scores ANY candidate on AbstentionBench, InteractComp, ClarifyMT-Bench, BFCL
irrelevance-detection, or Vectara HHEM. pass^k is unreported for all. Vendors publish
coding/reasoning scores, not judgment scores. **Nothing was fabricated to fill gaps.**

That is the de-risking insight: SWE-bench was the wrong lens, but a judgment *leaderboard*
doesn't exist for these models → the only sound path is a **hands-on local probe**.

## The sparse data that DOES exist (ranked)

| Axis | Best-supported candidate (data) | Number | Source confidence |
|---|---|---|---|
| Tool-use reliability (τ-bench) | **GLM-4.5-Air** 0.608 airline (#3, best local); GLM-4.7-Flash 79.5% (τ-bench) | real | [single-source] |
| Multi-turn instruction-following | **Qwen3-Next-80B-A3B-Instruct** Multi-IF 75.8 / IFEval 87.6 | real | [single-source] |
| Strict IF (IFBench) | Gemma 4 31B ~76; OLMo-3-Think 47.6 > Instruct 39.7 | real | [single-source] |
| Calibration | GLM-4.5-Air (only SimpleQA datapoint, 14.5) | thin | [single-source] |
| Execution proxy (Terminal-Bench 2.0) | Qwen3.6-27B 0.593 > 35B-A3B 0.515 > Gemma4-31B 0.429 > Devstral 0.225 | real | [solid] |
| Abstention / ask-vs-assume / pass^k | **NONE — no data for any candidate** | — | — |

## The two governing principles (apply where data is silent)

1. **Reasoning-tuning HURTS judgment (~24% worse abstention; AbstentionBench).** Penalizes
   thinking-default builds: OLMo-3-**Think**, Qwen3.6 (think-by-default), Gemma-4 thinking-on.
   → Prefer **non-thinking Instruct** builds (`enable_thinking:false`).
2. **Coder/agent-tuned models carry act-bias risk** (trained to *do*, not to *ask/abstain*) and
   have zero abstention data → Devstral, Qwen3-Coder-30B, GLM-4.7-Flash are judgment-unknowns.

## The fork your use-case creates

Your stated workload (agentic multi-file *coding*) and your judgment axis point at
**different models**:
- **Coding lens** → Qwen3-Coder-Next (specialized, 70.6 SWE-bench)
- **Judgment lens** → Qwen3-Next-80B-A3B-**Instruct** (general, non-thinking, best IF data)
- **Measured tool-reliability** → GLM-4.5-Air / GLM-4.7-Flash (only ones with real τ-bench)

Same ~40GB footprint for the two Qwen 80B-A3B variants. No leaderboard resolves this for
*your* work — a probe does.

## Recommendation: a small local judgment-probe harness (the de-risking step)

Pull the **top 3** (Qwen3-Coder-Next, Qwen3-Next-80B-Instruct, GLM-4.5-Air or 4.7-Flash) and
run a ~6-item probe BEFORE the deep workflow integration:
1. **Ask-vs-assume** — underspecified multi-file request; does it ask or barrel ahead?
2. **Abstention** — task referencing a file/API that doesn't exist; does it say "I don't know" or hallucinate?
3. **pass^k reliability** — run the same agentic task 5× cold; count clean successes (not pass@1).
4. **Tool-decision** — give it a tool it shouldn't use; does it refrain (irrelevance)?
5. **Strict multi-turn IF** — a constraint that must hold across 3 turns.
6. **Real multi-file coding task** from one of the user's repos — the actual workload.

This directly serves "be sure before deep investment," and matches the just-baked
**efficacy-over-speed** + **structure-over-one-shotting** preferences (probe, don't gamble).
