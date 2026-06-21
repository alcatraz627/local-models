# Open-Weight Reranker / Cross-Encoder Landscape — mid-2026

> Research date: 2026-06-19. Focus: open-weight reranker / cross-encoder / late-interaction
> models for RAG and search, runnable locally on a 64 GB Apple-Silicon Mac (CPU/MPS).
> Context: user runs a local-models project on Apple Silicon and wants cheap/fast local reranking.

## TL;DR recommendations

- **Best small/fast local reranker (Mac):** **BAAI/bge-reranker-v2-m3** (568M, Apache-2.0,
  FlagEmbedding/sentence-transformers, runs fast on MPS/CPU) — the de-facto default. Runner-up
  for a touch more accuracy at similar size: **Qwen3-Reranker-0.6B** (Apache-2.0, 32k context).
- **Best accuracy among truly-small (0.6B) open weights:** **jina-reranker-v3** (0.6B,
  BEIR 61.94, beats Qwen3-Reranker-4B) — BUT **license is CC-BY-NC-4.0 (non-commercial)**.
- **Best accuracy with a clean commercial license:** **mxbai-rerank-large-v2** (1.5B, Apache-2.0,
  BEIR 57.49) or **Qwen3-Reranker-4B/8B** (Apache-2.0) if you can spare the RAM/time.
- **Cleanest license + small + multilingual:** bge-reranker-v2-m3, Qwen3-Reranker-*, mxbai-rerank-* —
  all **Apache-2.0**. Avoid Jina rerankers if the use is commercial (non-commercial license).
- **API-only (NOT open weights, flagged):** **Cohere Rerank 3.5** and **Nvidia NeMo Retriever
  rerankers** (gated NIM / weights behind license terms) — not suitable for free local use.

---

## Curated shortlist (4–6) for local RAG on Apple Silicon

| Rank | Model | Size | License | Why pick it |
|---|---|---|---|---|
| 1 | **bge-reranker-v2-m3** | 568M | Apache-2.0 | Default small/fast. Mature, FlagEmbedding + ST support, multilingual, trivial on MPS/CPU. 512-token cap is the main limit. |
| 2 | **Qwen3-Reranker-0.6B** | 0.6B | Apache-2.0 | Same size class, newer (2025), 32k context, instruction-aware, 100+ langs. Strong small-model accuracy. |
| 3 | **mxbai-rerank-base-v2** | 0.5B | Apache-2.0 | RL-trained on Qwen2.5, 100+ langs, 8k ctx. Great speed/accuracy balance, clean license. |
| 4 | **mxbai-rerank-large-v2** | 1.5B | Apache-2.0 | Best Apache-licensed accuracy without going to 4B. BEIR 57.49; beats Cohere 3.5 on their bench. |
| 5 | **Qwen3-Reranker-4B** | 4B | Apache-2.0 | Top open accuracy with clean license; heavier, slower on Mac but fits 64 GB easily. |
| 6 | **jina-reranker-v3** | 0.6B | **CC-BY-NC-4.0** | Best raw accuracy at 0.6B (BEIR 61.94, beats Qwen3-4B) — **non-commercial only**, use for research/personal. |

*ColBERT late-interaction alternative:* **answerai-colbert-small-v1** (33M, Apache-2.0) — tiny,
fast, multi-vector retriever usable as a reranker when RAM is tight.

---

## Full per-model detail

### BAAI / FlagEmbedding family

| Field | bge-reranker-v2-m3 | bge-reranker-v2-gemma | bge-reranker-v2.5-gemma2-lightweight |
|---|---|---|---|
| Params | 568M (~0.6B) | ~2.5B (gemma-2b base) | gemma-2-based, layerwise/compressible |
| License | Apache-2.0 | Apache-2.0 (verify; gemma terms may apply) | Apache-2.0 (verify) |
| HF repo | `BAAI/bge-reranker-v2-m3` | `BAAI/bge-reranker-v2-gemma` | `BAAI/bge-reranker-v2.5-gemma2-lightweight` |
| Framework | FlagEmbedding, sentence-transformers, transformers | FlagEmbedding | FlagEmbedding |
| Mac 64 GB | Yes — fast on MPS/CPU, small | Yes — heavier (~5 GB fp16), slower | Yes — but heaviest |
| Best at | Multilingual + speed, default small reranker | Higher accuracy EN+multiling | Long-context, token-compression |
| Context | 512 tokens (main limitation) | longer | long |
| Headline metric | BEIR ~53.94 nDCG@10 (per mxbai bench); strong MIRACL | higher than m3 | — |
| Source | https://huggingface.co/BAAI/bge-reranker-v2-m3 | https://huggingface.co/BAAI/bge-reranker-v2-gemma | bge-model.com BGE-Reranker-v2 docs |
| Date | card current 2024–2025 | 2024 | 2024 |
| Confidence | [solid] | [solid] | [single-source] |

Notes: bge-reranker-v2-m3 is the community default small reranker — widely integrated
(LlamaIndex, LangChain, Haystack). The 512-token max is the practical ceiling; for longer
passages use the gemma or lightweight variants, or Qwen3/mxbai (8k–32k).

### Qwen3-Reranker (Alibaba)

| Field | Qwen3-Reranker-0.6B | Qwen3-Reranker-4B | Qwen3-Reranker-8B |
|---|---|---|---|
| Params | 0.6B | 4B | 8B |
| License | Apache-2.0 | Apache-2.0 | Apache-2.0 |
| HF repo | `Qwen/Qwen3-Reranker-0.6B` | `Qwen/Qwen3-Reranker-4B` | `Qwen/Qwen3-Reranker-8B` |
| Framework | sentence-transformers (CrossEncoder), transformers ≥4.51, vLLM ≥0.8.5 | same | same |
| Mac 64 GB | Yes — fast, small | Yes — fits, moderate speed (GGUF avail.) | Yes — fits in 64 GB, slower |
| Best at | small + instruction-aware + 32k ctx + 100+ langs | high accuracy, clean license | top-tier accuracy |
| Context | 32k tokens | 32k | 32k |
| Headline metric | MTEB-R 65.80, MMTEB-R 66.36, MTEB-Code 73.42 | BEIR 61.16 (per Jina bench) | highest of series |
| Source | https://huggingface.co/Qwen/Qwen3-Reranker-0.6B ; https://qwenlm.github.io/blog/qwen3-embedding/ | https://huggingface.co/Qwen/Qwen3-Reranker-4B | https://huggingface.co/Qwen/Qwen3-Reranker-8B |
| Date | 2025-06 | 2025-06 | 2025-06 |
| Confidence | [solid] | [solid] | [solid] |

Notes: Released June 2025 alongside Qwen3-Embedding. Instruction-aware (custom task
instructions give +1–5%). GGUF quants exist (QuantFactory, Mungert) — handy for
llama.cpp / Ollama-style local serving on Mac. 0.6B is a direct, slightly-stronger,
longer-context alternative to bge-reranker-v2-m3.

### mixedbread mxbai-rerank v2

| Field | mxbai-rerank-base-v2 | mxbai-rerank-large-v2 |
|---|---|---|
| Params | 0.5B | 1.5B |
| License | Apache-2.0 | Apache-2.0 |
| HF repo | `mixedbread-ai/mxbai-rerank-base-v2` | `mixedbread-ai/mxbai-rerank-large-v2` |
| Framework | sentence-transformers + `mxbai-rerank` lib (Qwen-2.5 base) | same |
| Mac 64 GB | Yes — fast, small | Yes — moderate; ~8× faster than bge-reranker-v2-gemma |
| Best at | balanced size/speed/accuracy | best-in-class Apache accuracy; multilingual + reasoning |
| Context | 8k (32k-compatible) | 8k (32k-compatible) |
| Headline metric | BEIR 55.57 nDCG@10 | BEIR 57.49 nDCG@10 (beats Cohere 3.5 @55.39, Jina v2 @54.35, bge-m3 @53.94) |
| Source | https://huggingface.co/mixedbread-ai/mxbai-rerank-base-v2 ; https://www.mixedbread.com/blog/mxbai-rerank-v2 | https://huggingface.co/mixedbread-ai/mxbai-rerank-large-v2 |
| Date | 2025-03-13 | 2025-03-13 |
| Confidence | [solid] | [solid] |

Notes: Trained with a 3-stage RL pipeline (GRPO + contrastive + preference). Strong on
Chinese (84.16), code search (32.05), tool retrieval. Cleanest "accuracy + Apache license"
option below 4B. Their own benchmark (self-reported) shows large-v2 topping Cohere/Jina/Voyage.

### Jina AI rerankers — NON-COMMERCIAL LICENSE (flag)

| Field | jina-reranker-v3 | jina-reranker-v2-base-multilingual | jina-colbert-v2 |
|---|---|---|---|
| Params | 0.6B (0.44B non-embed) | ~278M | ColBERT/multi-vector |
| License | **CC-BY-NC-4.0** | **CC-BY-NC-4.0** | **CC-BY-NC-4.0** (Apache code, NC weights) |
| HF repo | `jinaai/jina-reranker-v3` | `jinaai/jina-reranker-v2-base-multilingual` | `jinaai/jina-colbert-v2` |
| Framework | transformers (Qwen3-0.6B backbone) | transformers / sentence-transformers | RAGatouille / PyLate / ColBERT |
| Mac 64 GB | Yes — small, fast | Yes — very fast | Yes — multi-vector, more storage |
| Best at | SOTA accuracy at 0.6B; multilingual; long ctx | fast multilingual cross-encoder | multilingual late-interaction retrieve+rerank |
| Context | 131,072 tokens | 1k | — |
| Headline metric | BEIR 61.94 nDCG@10; MIRACL 66.83; MKQA 67.92; CoIR 70.64 | BEIR ~54.35 | +6.5% vs ColBERT-v2; +4.8% vs answerai-colbert-small |
| Source | https://jina.ai/news/jina-reranker-v3-0-6b-listwise-reranker-for-sota-multilingual-retrieval/ ; https://huggingface.co/jinaai/jina-reranker-v3 | https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual | https://huggingface.co/jinaai/jina-colbert-v2 ; arxiv 2408.16672 |
| Date | 2025-10-03 | 2024 | 2024-08 |
| Confidence | [solid] | [solid] | [solid] |

Notes: jina-reranker-v3 is the **accuracy leader among 0.6B open weights** — beats
Qwen3-Reranker-4B (61.16) at 6× smaller, via "last but not late interaction" (listwise causal
attention over query + all candidates in one window, 256-dim space). **But CC-BY-NC-4.0 blocks
commercial use** — for the user's local/personal RAG it's usable; for any product it's out.
This is the single biggest license caveat in the shortlist.

### ColBERT-style late-interaction rerankers

| Field | answerai-colbert-small-v1 | jina-colbert-v2 |
|---|---|---|
| Params | 33M | larger, multilingual |
| License | Apache-2.0 | CC-BY-NC-4.0 |
| HF repo | `answerdotai/answerai-colbert-small-v1` | `jinaai/jina-colbert-v2` |
| Framework | RAGatouille, Stanford ColBERT, `rerankers` lib | RAGatouille / PyLate |
| Mac 64 GB | Yes — tiny, very fast | Yes — multi-vector storage cost |
| Best at | tiny footprint, passage retrieval/rerank when RAM-limited | multilingual late-interaction, dynamic dims |
| Headline metric | BEIR 53.79 avg (FEVER 90.96, HotpotQA 76.11) | +6.5% vs ColBERT-v2 |
| Source | https://huggingface.co/answerdotai/answerai-colbert-small-v1 | https://jina.ai/news/jina-colbert-v2-multilingual-late-interaction-retriever-for-embedding-and-reranking/ |
| Date | 2024 | 2024-08 |
| Confidence | [solid] | [solid] |

Notes: Late-interaction (ColBERT) models score query/doc token-vectors separately, then
MaxSim. They double as retriever + reranker but need vector storage per token. For a simple
"rerank top-k" RAG step, a cross-encoder (bge/Qwen3/mxbai) is simpler; ColBERT shines when
you want one model for both stages, or on very tight compute (answerai-colbert-small at 33M).

### API-ONLY — NOT open weights (flagged)

| Model | Status | License | Notes |
|---|---|---|---|
| **Cohere Rerank 3.5** | **API-only** (Cohere API, Azure AI Foundry, AWS Bedrock) | proprietary, no weights | Released Dec 2024. 4096 ctx, SOTA multilingual + reasoning. **Cannot run locally.** Source: https://docs.cohere.com/changelog/rerank-v3.5 |
| **Nvidia llama-3.2-nv-rerankqa-1b-v2** | NIM microservice; weights gated on HF under NVIDIA license | NVIDIA Open Model / community (non-Apache) | 1B, 8192 ctx, 26 langs. Weights exist on HF but behind NVIDIA terms + NIM packaging — not a clean free-local option. Source: https://huggingface.co/nvidia/llama-3.2-nv-rerankqa-1b-v2 |
| **Nvidia llama-3.2-nemoretriever-500m-rerank-v2** | NIM microservice | NVIDIA license | 500M, smaller NeMo reranker. Source: NGC catalog |

---

## License cleanliness summary (most important axis for the user)

| License | Models | Commercial-safe? |
|---|---|---|
| **Apache-2.0** | bge-reranker-v2-m3, bge-reranker-v2-gemma, Qwen3-Reranker-0.6B/4B/8B, mxbai-rerank-base-v2, mxbai-rerank-large-v2, answerai-colbert-small-v1 | **Yes — clean** |
| **CC-BY-NC-4.0** | jina-reranker-v3, jina-reranker-v2-base-multilingual, jina-colbert-v2 | **No — non-commercial only** |
| Proprietary / API | Cohere Rerank 3.5 | No (paid API) |
| NVIDIA license / gated | Nvidia NeMo rerankers | Restricted |

The user's safe, clean-license, small, fast local set is: **bge-reranker-v2-m3**,
**Qwen3-Reranker-0.6B**, **mxbai-rerank-base-v2** (all Apache-2.0, all comfortable on a
64 GB Mac via MPS/CPU; GGUF quants exist for Qwen3 and bge for llama.cpp/Ollama serving).

## Accuracy ranking (open weights, BEIR nDCG@10 where comparable)

1. jina-reranker-v3 — 61.94 (0.6B) — *NC license*
2. Qwen3-Reranker-4B — 61.16 (clean license)
3. mxbai-rerank-large-v2 — 57.49 (clean license)
4. mxbai-rerank-base-v2 — 55.57
5. bge-reranker-v2-m3 — ~53.94
6. answerai-colbert-small-v1 — 53.79

> Caveat: BEIR numbers are drawn from different vendor benchmark posts (Jina, mixedbread)
> and are not all measured under identical retrieval pipelines — treat cross-vendor BEIR
> comparisons as **[single-source]** indicative, not head-to-head. Qwen3 numbers above
> (MTEB-R 65.80 etc.) are on MTEB retrieval subsets over Qwen3-Embedding candidates, a
> different setup than the BEIR table. MTEB has a dedicated reranking track on the public
> leaderboard (huggingface.co/spaces/mteb/leaderboard) — confirm live before publishing a
> definitive ordering.

## Confidence notes

- Param counts, licenses, HF repos, frameworks, context lengths: **[solid]** (from HF model
  cards + vendor blogs fetched live 2026-06-19).
- BEIR/MTEB headline scores: **[solid]** per individual vendor source, but **[single-source]**
  for any cross-vendor ranking (different eval pipelines).
- bge-reranker-v2-gemma / v2.5-lightweight license strings: **[single-source]** — verify the
  exact license on each card (gemma-derived weights sometimes carry Gemma terms).
- Nvidia reranker license details: **[single-source]** — gated, verify NVIDIA terms before use.

## Sources

- Qwen3 reranker blog: https://qwenlm.github.io/blog/qwen3-embedding/ (2025-06)
- Qwen3-Reranker-0.6B card: https://huggingface.co/Qwen/Qwen3-Reranker-0.6B
- Qwen3-Reranker-4B card: https://huggingface.co/Qwen/Qwen3-Reranker-4B
- Qwen3-Reranker-8B card: https://huggingface.co/Qwen/Qwen3-Reranker-8B
- mxbai-rerank v2 blog: https://www.mixedbread.com/blog/mxbai-rerank-v2 (2025-03-13)
- mxbai-rerank-large-v2 card: https://huggingface.co/mixedbread-ai/mxbai-rerank-large-v2
- mxbai-rerank-base-v2 card: https://huggingface.co/mixedbread-ai/mxbai-rerank-base-v2
- bge-reranker-v2-m3 card: https://huggingface.co/BAAI/bge-reranker-v2-m3
- bge-reranker-v2-gemma card: https://huggingface.co/BAAI/bge-reranker-v2-gemma
- BGE-Reranker-v2 docs: https://bge-model.com/bge/bge_reranker_v2.html
- jina-reranker-v3 news: https://jina.ai/news/jina-reranker-v3-0-6b-listwise-reranker-for-sota-multilingual-retrieval/ (2025-10-03)
- jina-reranker-v3 card: https://huggingface.co/jinaai/jina-reranker-v3
- jina-reranker-v2 card: https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual
- jina-colbert-v2 news: https://jina.ai/news/jina-colbert-v2-multilingual-late-interaction-retriever-for-embedding-and-reranking/
- answerai-colbert-small-v1 card: https://huggingface.co/answerdotai/answerai-colbert-small-v1
- Cohere Rerank v3.5 changelog: https://docs.cohere.com/changelog/rerank-v3.5
- Nvidia llama-3.2-nv-rerankqa-1b-v2 card: https://huggingface.co/nvidia/llama-3.2-nv-rerankqa-1b-v2
- MTEB leaderboard (verify live): https://huggingface.co/spaces/mteb/leaderboard
