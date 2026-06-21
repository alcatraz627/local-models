# τ-bench / τ²-bench Scores — Locally-Runnable Open Models

**Research date:** 2026-06-19
**Researcher note:** All scores verified against primary/official sources where possible. Many candidate
models are **post-cutoff (released 2026)** and were verified to exist via official HF/blog pages. Where a
published τ-bench/τ²-bench score genuinely does not exist, the cell reads **no data** — not estimated.

## ⚠️ Critical methodology caveat (read first)

The benchmark family has **fractured and evolved** through 2026, which makes clean "tau2 retail / tau2 airline"
cells impossible for most of the newer candidates:

- **τ-bench (v1)** — original Sierra benchmark, per-domain retail + airline. Still has a clean leaderboard
  (llm-stats mirror, 23 models). This is where GLM-4.5-Air, Qwen3-Coder-480B, Qwen3-Next sit.
- **τ²-bench** — Sierra's v2. Per-domain leaderboards exist for **airline** (llm-stats, 23 models) and
  **telecom** (Artificial Analysis, 429 models). A clean **retail** τ²-bench per-domain leaderboard was NOT
  found as a primary source; aggregator "combined tau2" pages (pricepertoken) report inflated/suspect numbers
  (e.g. "GLM-4.7-Flash 98.8%") that do **not** reconcile with the per-domain primary leaderboards — treated as
  **hearsay**.
- **τ²-Bench (aggregate)** — several 2026 model cards report a **single aggregate τ²-Bench number** with NO
  retail/airline split (GLM-4.7-Flash 79.5). Recorded in the airline column with a note, since no split exists.
- **τ³-Bench / TAU3-Bench** — the newest (banking + others). What the Qwen3.6 and Gemma 4 cards actually report.
  Captured here for completeness but is **NOT** τ-bench/τ²-bench — flagged distinctly.

So: for the 2026 Qwen3.6 / Gemma 4 generation, **there is no published τ²-bench retail/airline score** — they
report TAU3-Bench instead. That is a real "no data" for the requested metric.

---

## LEADERS (calibration)

| Benchmark / domain | Leader | Score | Source | Confidence |
|---|---|---|---|---|
| **τ-bench airline** | Claude Sonnet 4.5 (Anthropic) | 0.700 | [llm-stats](https://llm-stats.com/benchmarks/tau-bench-airline) | [solid] |
| **τ-bench retail** (combined v1 mirror, current snapshot) | Step-3.5-Flash (StepFun) | 0.882 | [llm-stats](https://llm-stats.com/benchmarks/tau-bench) | [single-source] |
| **τ²-bench airline** | LongCat-Flash-Thinking-2601 (Meituan) | 0.765 | [llm-stats](https://llm-stats.com/benchmarks/tau2-airline) | [solid] |
| **τ²-bench telecom** | JT-35B-Flash / GLM-5.2(max) (tie) | 99.1% | [Artificial Analysis](https://artificialanalysis.ai/evaluations/tau2-bench) | [single-source] |

Best **locally-runnable open** model on τ-bench airline: **GLM-4.5-Air 0.608** (#3 overall, behind only
Claude Sonnet 4.5 and MiniMax M1). On τ²-bench airline: **Qwen3-Next-80B-A3B-Thinking 0.605** (#12).

> **Note on aggregator claims:** pricepertoken's "Tau2 leaderboard" claiming GLM-4.7-Flash 98.8% as overall
> tau2 leader does NOT match the per-domain primary leaderboards (airline leader is 0.765; telecom leader 99.1%
> is telecom-only). Likely conflates the telecom-domain number with "tau2 overall." **Hearsay — not used as a leader.**

---

## CANDIDATE MODELS

| # | Model | τ-bench retail | τ-bench airline | τ²-bench retail | τ²-bench airline | pass^k | Source | Date | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Qwen3-Coder-Next 80B-A3B** | no data | no data | no data | no data | no data | [qwen.ai blog](https://qwen.ai/blog?id=qwen3-coder-next) (no tau scores; reports SWE-bench 70.6% only) | 2026 | [solid] (absence confirmed on official card) |
| 2 | **Qwen3-Coder-30B-A3B-Instruct** | no data | no data | **25.4** | **42.0** | no data | [arXiv 2511.01824](https://arxiv.org/pdf/2511.01824) "Simulating Environments with Reasoning Models" | Nov 2025 | [single-source] (3rd-party paper, NOT Qwen's own card — Qwen HF card has no tau scores) |
| 3 | **Qwen3.6-35B-A3B** | no data | no data | no data | no data | no data | [HF card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B) reports **TAU3-Bench 67.2** (aggregate, not τ²) | Apr 2026 | [solid] (τ² absence confirmed; τ³=67.2 recorded as note) |
| 4 | **Qwen3.6-27B (dense)** | no data | no data | no data | no data | no data | [HF card](https://huggingface.co/Qwen/Qwen3.6-27B) (no τ/τ² scores; general benchmarks only) | Apr 2026 | [solid] (absence confirmed) |
| 5 | **Devstral-Small-2 24B (2512)** | no data | no data | no data | no data | no data | [HF card](https://huggingface.co/mistralai/Devstral-Small-2-24B-Instruct-2512) (reports SWE-bench 68.0%, Terminal-Bench 2 22.5% — no tau) | Dec 2025 | [solid] (absence confirmed) |
| 6 | **GLM-4.7-Flash (30B-A3B MoE)** | no data | no data | no data | **79.5 (aggregate τ²-Bench, no domain split)** | no data | [Unsloth docs](https://unsloth.ai/docs/models/tutorials/glm-4.7-flash) (official benchmark table) | 2026 | [single-source] (aggregate only; no retail/airline split published) |
| 7 | **GLM-4.5-Air (106B-A12B)** | **77.9** | **0.608 (60.8)** | no data | no data | no data | [llm-stats τ-airline](https://llm-stats.com/benchmarks/tau-bench-airline) (#3); retail 77.9 from llm-stats mirror via search | 2025 | airline [solid]; retail [single-source] |
| 8 | **Gemma 4 (31B / 26B-A4B)** | no data | no data | no data | no data | no data | [Artificial Analysis](https://artificialanalysis.ai/models/gemma-4-31b) reports **τ³-Banking** (agentic tool use), NOT τ²; no per-domain τ² score | Apr 2026 | [solid] (τ² absence confirmed; blog claim "τ² 86.4%" is [hearsay], unconfirmed by official) |
| 9 | **OLMo 3-Think 32B** | no data | no data | no data | no data | no data | [Ai2 blog](https://allenai.org/blog/olmo3) (math/code/reasoning only; explicitly no tau-bench) | Nov 2025 | [solid] (absence confirmed) |

---

## Per-cell notes & provenance

**1. Qwen3-Coder-Next 80B-A3B** — Real model (built on Qwen3-Next-80B-A3B-Base, 3B active). Official blog reports
SWE-bench Verified 70.6%, SWE-bench Pro 74.2% — **no τ-bench / τ²-bench reported anywhere**. Genuine no-data.

**2. Qwen3-Coder-30B-A3B-Instruct** — The only candidate with a real per-domain τ²-bench number, but it comes from
a **third-party arXiv paper** (2511.01824, "Simulating Environments with Reasoning Models for Agent Training"),
NOT Qwen's own model card (which has no tau scores). Numbers: **τ²-bench retail 25.4, airline 42.0**. Same paper
context also cites Qwen3-30B-A3B variants on τ²-Telecom ~10–26%. [single-source] — one paper, downstream evaluation.

**3. Qwen3.6-35B-A3B** — Official HF card reports **"TAU3-Bench 67.2"** (vs Qwen3.5-27B 68.4, Gemma4-31B 67.5,
Qwen3.5-35B-A3B 68.9, Gemma4-26B-A4B 59.0). This is **τ³, a single aggregate**, NOT τ²/retail/airline. No τ²
retail/airline published → no data for the requested metric.

**4. Qwen3.6-27B (dense)** — Released Apr 2026, real. Card has general + vision benchmarks, **no τ-family scores**.

**5. Devstral-Small-2 24B** — "Devstral Small 2" = the 24B-Instruct-2512. Coding-agent focused. Card reports
SWE-bench Verified 68.0%, SWE-bench Multilingual 55.7%, Terminal-Bench 2 22.5%. **No τ-bench / τ²-bench.**
(There is also a larger "Devstral 2 123B" — out of local-runnable scope; also no tau scores seen.)

**6. GLM-4.7-Flash** — 30B-A3B MoE (≈3B active). Official benchmark table (Unsloth, mirrors Z.ai): SWE-bench
Verified 59.2, **τ²-Bench 79.5 (single aggregate, NO retail/airline/telecom split disclosed)**, GPQA 75.2,
AIME25 91.6. Recorded the 79.5 in the τ²-airline column with explicit "aggregate" caveat — do not read as
airline-specific. The AA telecom leaderboard separately lists "GLM-4.7-Flash (Reasoning) 98.8%" for **telecom only**.

**7. GLM-4.5-Air** — 106B total / 12B active. Strongest local model on the original **τ-bench (v1)** leaderboard:
**airline 0.608 (#3 of 23)**, **retail 77.9**. Companion GLM-4.5 (full): airline 0.604, retail 79.7. These are
τ-bench v1, not τ². No τ²-bench per-domain score for Air was found in primary sources.

**8. Gemma 4** — Released Apr 2 2026. Comes in 26B-A4B and 31B (and E2B/E4B). Official AA page reports
**"τ³-Banking"** for agentic tool use (no score surfaced on the fetched page), **not τ²**. A Medium aggregator
blog claims "Gemma 4 31B τ²-bench 86.4%" — **could not confirm against any official/primary source → [hearsay],
excluded from the table**. Qwen3.6 card cross-lists Gemma4-31B at TAU3-Bench 67.5 / Gemma4-26B-A4B 59.0 (τ³, not τ²).

**9. OLMo 3-Think 32B** — Released Nov 2025 (Ai2), "best fully-open reasoning model." Evaluated on math (AIME,
MATH), code (HumanEval, MBPP), reasoning (ZebraLogic, BBH), IFEval/IFBench. **No τ-bench / τ²-bench** in the
official blog or model card. Genuine no-data.

---

## pass^k reliability

**No pass^k reliability figure was found for ANY of the 9 candidate models.** pass^k (the τ²-bench reliability
metric — probability all k independent trials succeed) is reported in the Sierra τ²-bench paper for frontier
models (GPT/Claude), but none of the locally-runnable candidates here have a published pass^k number on a
primary source. Genuine no-data across the board.

---

## Source reliability ranking used

1. **[solid]** — official model card (HF / vendor blog) or primary Sierra/HAL leaderboard.
2. **[single-source]** — one credible mirror (llm-stats, Artificial Analysis) or one third-party paper.
3. **[hearsay]** — aggregator/SEO blog (Medium, pricepertoken, benchlm, designforonline) with numbers that
   don't reconcile to primary sources. **Explicitly excluded from score cells.**

Aggregator pages that were checked and **rejected as unreliable**: pricepertoken ("GLM-4.7-Flash 98.8% tau2
overall" — conflates telecom), various Medium/DEV.to Gemma 4 "τ² 86.4%" posts (no primary confirmation).
