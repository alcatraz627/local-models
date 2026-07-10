# BFCL Scores — Candidate Open Models (research 2026-06-19)

Goal: BFCL **overall accuracy** + the **irrelevance-detection** sub-score (knowing when NOT to
call a tool) for nine candidate local-runnable open models.

> **Critical caveat — version incomparability.** BFCL v1/v2/v3/v4 are NOT comparable. v4 added
> agentic/web-search categories and lowered absolute numbers vs v3. Each cell below tags its version.
> A v3 0.76 and a v4 0.67 are different scales. Do not cross-compare.

> **Naming caveat.** The candidate list has several names that do NOT match what's published.
> The live BFCL-v4 leaderboard (llm-stats.com) shows the **Qwen3.5** family (Qwen3.5-35B-A3B,
> Qwen3.5-27B) — there is **no "Qwen3.6-35B-A3B" or "Qwen3.6-27B"** on any BFCL leaderboard found
> (Qwen3.6 exists as a model family per vendor blogs, but is not BFCL-listed). I report the
> closest published match (Qwen3.5-*) and flag the name mismatch explicitly. Treat these as
> *probable intended targets*, not confirmed matches.

## Findings table

| # | Model (as requested) | BFCL overall | Version | Irrelevance sub-score | Source URL | Date | Confidence |
|---|---|---|---|---|---|---|---|
| 1 | Qwen3-Coder-Next 80B-A3B | **no data** | — | no data | (Qwen3-Coder-Next tech report exists, arxiv 2603.00729, but reports coding benches, not BFCL) | 2026-06-19 | — |
| 1b | *(closest: Qwen3-Next-80B-A3B-Instruct)* | 0.703 | **v3** | no data | https://llm-stats.com/benchmarks/bfcl-v3 | 2026-06-19 | [single-source] |
| 1c | *(closest: Qwen3-Next-80B-A3B-Thinking)* | 0.720 | **v3** | no data | https://llm-stats.com/benchmarks/bfcl-v3 | 2026-06-19 | [single-source] |
| 2 | Qwen3-Coder-30B-A3B(-Instruct) | 0.7663 (76.63%) | **v2** | no data | https://openrouter.ai/qwen/qwen3-coder-30b-a3b-instruct (via Mify-Coder arxiv 2512.23747) | 2026-06-19 | [single-source] |
| 2b | *(related: Qwen3-Coder-Plus, BFCL-v3 run)* | 0.7199 | **v3** | **0.8458** (live irrel 0.8343) | https://evalscope.readthedocs.io/en/latest/best_practice/qwen3_coder.html | 2026-06-19 | [single-source] |
| 3 | Qwen3.6-35B-A3B | **no data** (name not on any BFCL board) | — | no data | — | 2026-06-19 | — |
| 3b | *(closest published: Qwen3.5-35B-A3B)* | 0.673 | **v4** | no data | https://llm-stats.com/benchmarks/bfcl-v4 | 2026-06-19 | [single-source] |
| 4 | Qwen3.6-27B (dense) | **no data** (name not on any BFCL board) | — | no data | — | 2026-06-19 | — |
| 4b | *(closest published: Qwen3.5-27B)* | 0.685 | **v4** | no data | https://llm-stats.com/benchmarks/bfcl-v4 | 2026-06-19 | [single-source] |
| 5 | Devstral-Small-2 24B | **no data** | — | no data | model card has SWE-Bench/Terminal-Bench, NO BFCL: https://huggingface.co/mistralai/Devstral-Small-2-24B-Instruct-2512 | 2026-06-19 | — |
| 6 | GLM-4.7-Flash (30B MoE) | **no data** (best-30B claim, no BFCL number) | — | no data | https://unsloth.ai/docs/models/glm-4.7-flash / https://llm-stats.com/models/glm-4.7-flash | 2026-06-19 | — |
| 7 | GLM-4.5-Air (106B-A12B) | 0.764 (76.4%) | **v3** | no data (overall published; sub-score not broken out in sources found) | https://llm-stats.com/benchmarks/bfcl-v3 | 2026-06-19 | [solid] |
| 8 | Gemma 4 (26B-A4B / 31B) | **no data** | — | no data | not on any BFCL board found | 2026-06-19 | — |
| 9 | OLMo 3-Think 32B | **no data** (32B Think) | — | no data | Olmo-3.1-32B-Think card/blog report math/reasoning, not BFCL. OLMo-3-7B-Instruct = 12.03% BFCL-v2 (single hearsay) | 2026-06-19 | — |

## LEADER lines

- **BFCL-v4 OVERALL LEADER (live, llm-stats):** **Qwen3.7 Max** — 0.750 (v4). Source:
  https://llm-stats.com/benchmarks/bfcl-v4 — 2026-06-19. [solid for that board]
- **BFCL-v3 OVERALL LEADER (live, llm-stats):** **GLM-4.5** — 0.778 (v3). Source:
  https://llm-stats.com/benchmarks/bfcl-v3 — 2026-06-19. [solid]
- **IRRELEVANCE-DETECTION LEADER (for calibration):** **No clean modern leader found.** The only
  per-model irrelevance numbers surfaced come from the **historical BFCL v2/v3 academic landscape**
  (emergentmind survey), NOT the current live v4 board:
  - xLAM-7B-fc-r — **79.76%** IrrelAcc (historical, v2-era). [single-source]
  - Granite-20B-FunctionCalling — 87.08% IrrelAcc; ToolACE-8B ≈89%; GPT-4-0125 61.35%; Llama-3-70B 50.47%.
  - Source: https://www.emergentmind.com/topics/berkeley-function-calling-leaderboard-v4-bfclv4 — 2026-06-19. [hearsay — survey-aggregated, mixes versions]
  - For a *current* candidate, the only modern irrelevance number found is **Qwen3-Coder-Plus =
    0.8458 (v3)** via EvalScope — the best concrete modern irrelevance datapoint among related models. [single-source]

## Notes / honesty flags

- The emergentmind "v4" page's headline numbers (ToolACE-8B ≈91.5 overall, xLAM 79.76 irrel) are
  **older v2/v3-era academic figures**, not the live v4 leaderboard — do not treat as current v4.
- The live llm-stats v4 board carries **no irrelevance sub-column** in the scraped view; only overall.
- None of the requested models report a **BFCL irrelevance sub-score on their own model card / vendor
  blog** — the sub-score is only obtainable from the official gorilla per-category CSV (not parseable
  via WebFetch here) or third-party eval runs (EvalScope for Qwen3-Coder-Plus).
- **5 of 9 candidates have NO BFCL data at all** (Qwen3-Coder-Next 80B, Devstral-Small-2, GLM-4.7-Flash,
  Gemma 4, OLMo 3-Think). Two more (Qwen3.6-35B-A3B, Qwen3.6-27B) have **name mismatches** — only the
  Qwen3.5 analogs are published.
- Only **GLM-4.5-Air (0.764 v3)** and **Qwen3-Coder-30B-A3B (0.7663 v2)** have solid/single-source
  overall numbers directly matching a requested model name.
