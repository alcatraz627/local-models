# Model Existence Verification

Research date: 2026-06-19. Method: HuggingFace search + vendor blog/news. Strongest
signal = the actual HF URLs returned by the search index (real repo hits), which are
more reliable than WebFetch page summaries (small-model summarizer can hallucinate
benchmark numbers / dates). Confidence reflects that distinction.

| # | Candidate (as given) | EXISTS | Exact HF repo tag | Release date | Note | Confidence |
|---|----------------------|--------|-------------------|--------------|------|------------|
| 1 | Qwen3-Coder-Next 80B-A3B | yes | `Qwen/Qwen3-Coder-Next` | ~early 2026 (vendor blog `qwen.ai/blog?id=qwen3-coder-next`) | Real. Repo is **`Qwen/Qwen3-Coder-Next`** (no "80B-A3B" suffix in the tag). Built on Qwen3-Next-80B-A3B-Base; 80B total / 3B active MoE, ~70% SWE-Bench Verified. | [solid] |
| 2 | Qwen3-Coder-30B-A3B | yes | `Qwen/Qwen3-Coder-30B-A3B-Instruct` | mid-2025 (part of Qwen3-Coder family) | Real, widely mirrored (unsloth/Mungert/giladgd GGUFs). Canonical tag carries the **`-Instruct`** suffix; non-thinking mode only, 262K ctx. | [solid] |
| 3 | Qwen3.6-35B-A3B | yes | `Qwen/Qwen3.6-35B-A3B` | April 2026 | Real. First open-weight Qwen3.6 MoE variant (35B total / 3B active). NVIDIA NVFP4 + GGUF/MLX mirrors exist. Name as given is exact. | [solid] |
| 4 | Qwen3.6-27B (dense) | yes | `Qwen/Qwen3.6-27B` | ~Apr 22 2026 (vendor blog `qwen.ai/blog?id=qwen3.6-27b`) | Real. Dense 27B coding model; `QwenLM/Qwen3.6` GitHub + unsloth/ollama/NVFP4 mirrors. Name as given is exact. | [solid] |
| 5 | Devstral-Small-2 24B | yes | `mistralai/Devstral-Small-2-24B-Instruct-2512` | Dec 9 2025 (Simon Willison writeup + Mistral) | Real. Canonical tag is **`Devstral-Small-2-24B-Instruct-2512`** (note the `-2512` date code). Apache-2.0; ships with "Mistral Vibe" CLI. | [solid] |
| 6 | GLM-4.7-Flash (30B MoE) | yes | `zai-org/GLM-4.7-Flash` | early 2026 (with GLM-4.7 family) | Real. 30B-A3B MoE lightweight variant. Sibling `zai-org/GLM-4.7` also exists; NVFP4/GGUF mirrors present. Org is **`zai-org`** (Z.ai/Zhipu). | [solid] |
| 7 | GLM-4.5-Air (106B-A12B) | yes | `zai-org/GLM-4.5-Air` | Jul 28 2025 | Real, well-established. 106B total / 12B active MoE, MIT license, hybrid reasoning. Name + params as given are exact. | [solid] |
| 8 | Gemma 4 (26B-A4B and/or 31B) | yes | `google/gemma-4-26B-A4B` (+ `-it`), `google/gemma-4-31B` (+ `-it`) | 2026 (postdates cutoff) | Real. Both variants present under `google/`: a **26B-A4B MoE** and a **31B dense**, each with `-it` instruct. E2B/E4B small variants also in family. unsloth GGUFs exist. | [single-source] |
| 9 | OLMo 3-Think 32B | partial | `allenai/Olmo-3.1-32B-Think` (current) | Olmo 3: Nov 2025 (`Olmo-3-1125-32B` base); 3.1 Think refresh ~Dec 2025 | Name slightly off. The live canonical Think tag is **`Olmo-3.1-32B-Think`** (extra RL pass), not "Olmo-3-32B-Think" — that exact tag exists only as community GGUF mirrors (`unsloth/Olmo-3-32B-Think-GGUF`). Base model: `allenai/Olmo-3-1125-32B`. | [solid] |

## Summary of name corrections vs. candidate list

- **#1** → drop the "80B-A3B" from the tag: it's just `Qwen/Qwen3-Coder-Next`.
- **#2** → add `-Instruct`: `Qwen/Qwen3-Coder-30B-A3B-Instruct`.
- **#5** → add `-Instruct-2512`: `mistralai/Devstral-Small-2-24B-Instruct-2512`.
- **#9** → the official current tag is `allenai/Olmo-3.1-32B-Think` (3.1, not 3); base is `Olmo-3-1125-32B`.
- **#3, #4, #6, #7, #8** → names map cleanly to real repos.

## Confidence / honesty caveats

- Every candidate resolved to a **real HF repo** in the search index — none appear
  hallucinated or nonexistent. The verification leans on the URL lists returned by
  HF search (real index entries), which I trust over the prose summaries.
- Several models (#3, #4, #6, #8) **postdate the assistant's Jan 2026 training
  cutoff**, so confirmation rests entirely on live search hits + vendor blog URLs.
  The repos clearly exist; specific benchmark numbers quoted by the summarizer were
  NOT independently verified and should not be treated as authoritative.
- Gemma 4 (#8) marked `[single-source]` only because all confirmation came from one
  search pass (HF `google/gemma-4-*` repos + unsloth mirrors); the repos are real but
  I did not fetch the model card directly.
