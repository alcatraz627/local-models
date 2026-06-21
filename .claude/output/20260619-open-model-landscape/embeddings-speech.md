# Open-Model Landscape: Embeddings / Rerankers / ASR / TTS (mid-2026)

> Research date: **2026-06-19**. Live sources (WebSearch/WebFetch, HF model cards, MTEB / Open ASR / TTS Arena leaderboards, vendor blogs). Target host: **64 GB Apple-Silicon Mac**. Companion deep-dive files in this same folder: `asr-findings.md`, `tts-findings.md`, `reranker-findings.md`.
>
> Confidence legend: **[solid]** = ≥2 live sources or an official model card · **[single-source]** = one source / cross-vendor benchmark not head-to-head · **[hearsay]** = mentioned but unverified. Leaderboard ELO/WER numbers drift week-to-week — treat ordering as indicative, not gospel.

---

## TL;DR — the local Apple-Silicon picks

```
┌─ Recommended default stack for a local RAG + voice setup on a 64GB Mac ─┐
│                                                                          │
│  EMBED (RAG)   →  EmbeddingGemma-300M  (on-device default, Apache-ish*)  │
│                   or Qwen3-Embedding-0.6B (stronger, 32k ctx, Apache-2)  │
│  RERANK        →  bge-reranker-v2-m3 (568M) OR Qwen3-Reranker-0.6B       │
│  ASR (file)    →  Parakeet-TDT-0.6b-v3 via parakeet-mlx (fast+accurate)  │
│  ASR (stream)  →  Kyutai stt-1b-mlx  OR  Moonshine v2 (tiny, low-latency)│
│  ASR (fallback)→  Whisper large-v3-turbo via mlx-whisper / whisper.cpp   │
│  TTS (presets) →  Kokoro-82M  (Apache-2.0, real-time on CPU/MLX)         │
│  TTS (cloning) →  Chatterbox (MIT, zero-shot clone) — cleanest license   │
│                                                                          │
│  * EmbeddingGemma ships under the Gemma Terms (use-restrictions, not OSI │
│    Apache); fine for personal/local. Qwen3 is true Apache-2.0.           │
└──────────────────────────────────────────────────────────────────────────┘
```

**simonw/llm plugin pick (the project's noted future RAG path):** use **`llm-sentence-transformers`** and register **`Qwen3-Embedding-0.6B`** (best quality-for-size, Apache-2.0, 32k ctx) — or **`EmbeddingGemma-300M`** for the lightest on-device footprint. For a pure-GGUF route use **`llm-gguf`** with **`nomic-embed-text-v1.5`** or **`mxbai-embed-xsmall`**. Details in the embeddings section below.

---

## 1) Text Embedding models (RAG / local semantic search)

Curated shortlist. "Dim" = native embedding dimension (most support Matryoshka truncation to 128/256/512). All listed run on a 64 GB Mac comfortably; the small ones (≤600M) are the ones worth using locally for latency.

| Model | Params | Dim (MRL) | Ctx | License | MTEB / note | Runs on Mac via | Best at | Conf |
|---|---|---|---|---|---|---|---|---|
| **EmbeddingGemma-300M** | 300M | 768 → 512/256/128 | 2,048 | Gemma Terms (use-restricted, free) | #1 open multilingual **<500M** on MTEB; ~22ms/embed on EdgeTPU, <200MB RAM quantized | sentence-transformers, **MLX**, llama.cpp, Ollama, LM Studio | **On-device** default; lowest RAM; mobile/laptop | [solid] |
| **Qwen3-Embedding-0.6B** | 0.6B | 1024 → down to 128 | **32k** | **Apache-2.0** | Strong for size; instruction-aware; 100+ langs | sentence-transformers, Ollama, TEI, transformers.js | Best **quality-per-size** small model; long ctx | [solid] |
| **Qwen3-Embedding-8B** | 8B | 4096 (MRL) | 32k | **Apache-2.0** | **#1 MTEB multilingual** 70.58 (Jun 2025); MTEB-Code 80.68 | MLX / transformers (heavy but fits 64GB) | Top **accuracy** + code search if you want max quality | [solid] |
| **BGE-M3** | 568M | 1024 | **8,192** | **MIT** | Dense + sparse + multi-vector (ColBERT) in one; 100+ langs | sentence-transformers, FlagEmbedding | **Hybrid retrieval** workhorse; MIT clean | [solid] |
| **gte-multilingual-base** | 305M | 768 (elastic) | 8,192 | Apache-2.0 | ~10× faster inference (encoder-only); 70+ langs | sentence-transformers | Fast multilingual base | [single-source] |
| **Nomic-embed-text-v1.5** | 137M | 768 → 256 | **8,192** | Apache-2.0 | English-focused, MRL; tiny (274MB) | **llm-gguf** / sentence-transformers / Ollama | Lightest **English** edge model; GGUF for llm | [solid] |
| **Nomic-embed-text-v2-moe** | 475M (305M active) | 768 → 256 | 512 | Apache-2.0 | First **MoE** text embedder; multilingual | sentence-transformers (`--trust-remote-code`) | Multilingual MoE efficiency | [single-source] |
| **Snowflake Arctic-Embed-L-v2.0** | 303M | 1024 (MRL) | 8,192 | Apache-2.0 | Balanced EN + 74-lang multilingual | sentence-transformers | Balanced multilingual+English retrieval | [single-source] |

**Notes & caveats**
- **Gemini Embedding 001** tops the *English* MTEB (~68.3) but is **API-only / closed** — not a local option; included only as the ceiling reference. **[solid]**
- **Jina-embeddings-v4** (3B, 2048-dim, multimodal) is strong but **CC-BY-NC-4.0 (non-commercial)** — fine for personal local use, flag for anything commercial. **[solid]**
- **NVIDIA llama-embed-nemotron-8B** was reported #1 multilingual across 250+ langs (open weight) — heavy; verify license (NVIDIA/NeMo terms) before relying. **[single-source]**
- **mxbai-embed-large-v1 / mxbai-embed-xsmall** (Apache-2.0): the xsmall is a **30.8 MB GGUF** — ideal for `llm-gguf`. **[solid]**
- Matryoshka truncation: for a local vector DB, 256-dim is usually the sweet spot (¼ the storage, ~1-2 pt MTEB drop).

### The simonw/llm angle (project's noted future RAG path)
The `llm` CLI does embeddings via plugins (`llm embed`, `llm embed-multi`, `llm similar`, stored in SQLite):
- **`llm-sentence-transformers`** — register any HF ST model: `llm sentence-transformers register Qwen/Qwen3-Embedding-0.6B`. **Best local pick: Qwen3-Embedding-0.6B** (Apache-2.0, 32k ctx, strongest small model) or **EmbeddingGemma-300M** (lightest). **[solid]**
- **`llm-gguf`** — pure-llama.cpp route: `llm gguf register-embed-model` with **nomic-embed-text-v1.5-GGUF** or **mxbai-embed-xsmall** (30.8MB). No Python ML deps, fast on Apple Silicon Metal. **[solid]**
- **`llm-ollama`** — if Ollama is already the project's backend, `nomic-embed-text` / `embeddinggemma` / `qwen3-embedding` are all pullable and exposed to `llm` directly. **[solid]**

---

## 2) Rerankers (cross-encoders for RAG)

Full detail in `reranker-findings.md`. Curated shortlist:

| Model | Params | Ctx | License | Metric / note | Runs on Mac | Best at | Conf |
|---|---|---|---|---|---|---|---|
| **bge-reranker-v2-m3** | 568M | 512 | **Apache-2.0** | Mature default; 100+ langs; GGUF quants exist | sentence-transformers / FlagEmbedding / llama.cpp | **Small fast local default** | [solid] |
| **Qwen3-Reranker-0.6B** | 0.6B | **32k** | **Apache-2.0** | Instruction-aware, 100+ langs; longer ctx drop-in | sentence-transformers / GGUF | Best **small + long-context** | [solid] |
| **mxbai-rerank-base-v2** | 0.5B | — | **Apache-2.0** | RL-trained on Qwen2.5; great balance | sentence-transformers | Balanced clean-license small | [single-source] |
| **mxbai-rerank-large-v2** | 1.5B | — | **Apache-2.0** | BEIR ~57.5; beats Cohere 3.5 on their bench | sentence-transformers | **Best accuracy, clean license** | [single-source] |
| **Qwen3-Reranker-4B / 8B** | 4B / 8B | 32k | **Apache-2.0** | Top open accuracy; heavier | MLX / transformers | Max accuracy if you have headroom | [solid] |
| **jina-reranker-v3** | 0.6B | **131k** | **CC-BY-NC-4.0** | BEIR 61.94 — beats Qwen3-4B at 6× smaller | sentence-transformers | Best accuracy/size **(non-commercial!)** | [single-source] |
| **answerai-colbert-small-v1** | 33M | — | Apache-2.0 | Tiny ColBERT late-interaction | sentence-transformers / RAGatouille | Ultra-light late-interaction | [single-source] |

**Picks:** local default **bge-reranker-v2-m3** or **Qwen3-Reranker-0.6B** (both Apache-2.0, fast on MPS/CPU, GGUF-able). Max clean-license accuracy: **mxbai-rerank-large-v2** or **Qwen3-Reranker-4B**. **Avoid for commercial:** all Jina rerankers (CC-BY-NC). **Not open weights:** Cohere Rerank 3.5 (API-only), NVIDIA NeMo rerankers (gated). **[solid]**

---

## 3) ASR / Speech-to-Text

Full detail in `asr-findings.md`. On a Mac the practical choice collapses to **parakeet-mlx vs whisper (MLX/cpp)** — the absolute accuracy leaders are LLM-hybrids with no first-class MLX path.

| Model | Params | License | WER (Open ASR) | Runs on Mac via | Best at | Conf |
|---|---|---|---|---|---|---|
| **Parakeet-TDT-0.6b-v3** | 600M | **CC-BY-4.0** | ~6.34% | **parakeet-mlx** (native MLX) | **Best Mac default**: fast + accurate, punctuation + word timestamps, EN + 24 EU langs w/ auto-detect | [solid] |
| **Whisper large-v3-turbo** | 809M | **MIT** | ~ large-v3 −0.4pt @ ~5× speed | **mlx-whisper**, lightning-whisper-mlx, **whisper.cpp** (GGUF) | Ecosystem fallback; **99 languages**, translation, srt/vtt tooling | [solid] |
| **Whisper large-v3** | 1.55B | MIT | baseline (~7-8%) | mlx-whisper / whisper.cpp | Max Whisper accuracy / multilingual | [solid] |
| **Kyutai stt-1b (en_fr)** | 1B | CC-BY-4.0 | streaming-grade | official **MLX** checkpoint | **Low-latency streaming** (~0.5s delay, semantic VAD) | [solid] |
| **Moonshine v2** | 27M (tiny) | **MIT** | competitive at size | ONNX / candle / transformers | **Lowest latency** (50–258ms); live captions, edge | [solid] |
| **Canary-Qwen-2.5B** | 2.5B | CC-BY-4.0 | **5.63% (#1)** | NeMo / transformers (no clean MLX) | Top accuracy — but heavy/awkward on Mac | [solid] |
| **Voxtral (Mistral)** | 3B/24B | Apache-2.0 | strong | transformers / vLLM | Open multilingual speech-LLM (ASR+understanding) | [single-source] |

**Picks:** primary **Parakeet-TDT-0.6b-v3 via parakeet-mlx**; **Whisper large-v3-turbo** when you need 99-language coverage or translation; **Kyutai stt-1b-mlx** or **Moonshine v2** for real-time streaming/captions. **License note:** NVIDIA NeMo + Kyutai = CC-BY-4.0 (attribution, commercial OK); Whisper/Distil/Moonshine = MIT. **Parakeet v2 is English-only; v3 is the 25-language multilingual one** — use v3 for multilingual on Mac. **[solid]**

---

## 4) TTS / Voice

Full detail in `tts-findings.md`. No open-weight model is in the **TTS Arena V2 top 10** (top is all proprietary: Vocu, Inworld, CastleFlow, Papla). Best **open** entry is Fish Audio S2 Pro (ELO ~1129, rank 11) but with a non-clean license.

| Model | Params | License | Voice cloning | Runs on Mac via | Best at | Conf |
|---|---|---|---|---|---|---|
| **Kokoro-82M v1.0** | 82M | **Apache-2.0** | No (preset voices) | **mlx-audio** / ONNX / CPU | **Cleanest local default**: real-time on CPU, tiny | [solid] |
| **Chatterbox (Resemble)** | 350M | **MIT** | **Yes (zero-shot, ~5s)** | **mlx-audio** / PyTorch | **Best clean-license cloning**; emotion control; Turbo ~75ms | [solid] |
| **Higgs Audio v2** | 3B | **Apache-2.0** | Yes (zero-shot) | PyTorch (MPS) | **Most expressive** open cloner | [single-source] |
| **Fish-Speech / OpenAudio S1** | ~0.5B | Fish Research Lic. (⚠) | Yes (zero-shot) | PyTorch | Highest open quality — **license caveat** | [solid] |
| **Orpheus TTS** | 3B | **Apache-2.0** | Yes (tag-driven) | PyTorch (MPS) | Expressive, emotion tags, LLM-based | [single-source] |
| **Dia (Nari Labs)** | 1.6B | Apache-2.0 | Yes | **mlx-audio** / PyTorch | Dialogue / multi-speaker | [single-source] |
| **Kyutai Pocket TTS** | 100M | CC-BY-4.0 | Yes | CPU | Tiny CPU cloner | [single-source] |
| **MeloTTS** | small | **MIT** | No | PyTorch (CPU) | Fast multilingual presets, no GPU | [solid] |

**Picks:** presets/fastest → **Kokoro-82M** (Apache-2.0, real-time CPU). Voice cloning, cleanest license → **Chatterbox (MIT)**. Most expressive cloning → **Higgs Audio v2** (Apache-2.0, 3B). **Flag licenses:** Fish-Speech (research license), Coqui XTTS-v2 (restrictive Coqui CPML), some F5-TTS forks (CC-BY-NC). The unifying Apple-Silicon runtime is **`mlx-audio`** (Blaizzy) — one MLX library hosting Kokoro/Chatterbox/Dia/Whisper with an OpenAI-compatible server. **[solid]**

---

## 5) All-in-one speech / audio LLMs (note)

- **Canary-Qwen-2.5B**, **IBM Granite-Speech-3.3-8B**, **Microsoft Phi-4-multimodal**, **Voxtral (Mistral 3B/24B)**, **Kyutai Moshi** — Conformer/encoder + LLM-decoder hybrids that top ASR accuracy and add understanding/translation. All are **NeMo/transformers-only** (no first-class MLX) so they're heavy on Apple Silicon; use them on a GPU box, not as the local Mac default. Orpheus / Higgs / Fish on the TTS side are similarly LLM-based audio models. **[single-source]**

---

## Sources (selected, fetched 2026-06-19)

- MTEB leaderboard & embedding roundups: bentoml.com/blog/a-guide-to-open-source-embedding-models · milvus.io/blog/choose-embedding-model-rag-2026 · awesomeagents.ai (MTEB Mar 2026)
- EmbeddingGemma: developers.googleblog.com/en/introducing-embeddinggemma · huggingface.co/google/embeddinggemma-300m · arxiv.org/abs/2509.20354
- Qwen3-Embedding: huggingface.co/Qwen/Qwen3-Embedding-0.6B · qwen.ai/blog?id=qwen3-embedding · arxiv.org/pdf/2506.05176 · simonwillison.net/2025/Jun/8/qwen3-embedding
- BGE-M3 / Arctic / Nomic / Jina: snowflake.com/en/engineering-blog/snowflake-arctic-embed-2-multilingual · huggingface.co/Snowflake/snowflake-arctic-embed-l-v2.0
- simonw/llm plugins: llm.datasette.io/en/stable/plugins/directory.html · github.com/simonw/llm-sentence-transformers · github.com/simonw/llm-gguf
- Open ASR Leaderboard: huggingface.co/spaces/hf-audio/open_asr_leaderboard · huggingface.co/blog/open-asr-leaderboard · arxiv.org/abs/2510.06961 · northflank.com/blog/best-open-source-speech-to-text-stt-model-in-2026-benchmarks
- TTS Arena V2: huggingface.co/spaces/TTS-AGI/TTS-Arena-V2 (+ vendor GitHub for Kokoro/Chatterbox/mlx-audio)
- Companion deep-dives (this folder): asr-findings.md · tts-findings.md · reranker-findings.md
