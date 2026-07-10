# Open-model landscape — shortlist by task class (2026-06-19)

Live-web research (not from memory), 5 parallel agents across HF trending, leaderboards
(LMArena, Aider, SWE-bench, MTEB, Open ASR, image arenas), and vendor blogs. Each row
flags **fit** on the user's **M5 Pro / 64 GB** (~48 GB usable GPU budget): ✅ fits at 4-bit ·
🟡 borderline · ☁️ API/server-tier (too big to run locally).

Detail files: [coding](coding.md) · [general-reasoning](general-reasoning.md) ·
[vision-multimodal](vision-multimodal.md) · [image-video-gen](image-video-gen.md) ·
[embeddings-speech](embeddings-speech.md) (+ [asr](asr-findings.md) · [tts](tts-findings.md) · [reranker](reranker-findings.md))

> Confidence: first-party model cards + vendor blogs are `[solid]`; the newest
> benchmark decimals (GLM-5.2, Kimi-K2.7, DeepSeek-V4) are aggregator-sourced
> `[single-source]` — orderings are consistent, exact numbers approximate. Naming
> churns fast (Qwen 3.5→3.6→3.7, GLM 5→5.2) — confirm the HF tag before pulling.

---

## 1. Coding

| Model | Params/arch | License | Fit | Best at |
|---|---|---|---|---|
| **Qwen3-Coder-Next 80B-A3B** | 80B MoE / 3B act | Apache-2.0 | ✅ ~42 GB Q4 | **Best local agentic coder** (the pick for the heavy tier) |
| Qwen3-Coder-30B-A3B | 30B MoE / 3B act | Apache-2.0 | ✅ ~18 GB | Fast-iteration coder (~68 tok/s) |
| Qwen3.6-27B (dense) | 27B dense | Apache-2.0 | ✅ ~17 GB | Dense quality, 77.2 SWE-V; slower |
| Devstral-Small-2 24B | 24B dense | Apache-2.0 | ✅ ~14–25 GB | Agentic dark-horse, SWE-agent scaffolds |
| Codestral 2 22B | 22B dense | Apache-2.0 | ✅ | **Best open FIM/autocomplete** |
| GLM-4.5-Air 106B-A12B | MoE | MIT | 🟡 ~40 GB | Bigger local reasoner, thin headroom |
| DeepSeek-V4 / GLM-5.2 / Kimi-K2.7 / Qwen3-Coder-480B | 0.5–1.6T MoE | MIT/Apache | ☁️ 150–400 GB+ | Frontier open coders — API-tier (DeepSeek-V4 has OpenAI+Anthropic API compat → drops into Claude Code) |

## 2. General / reasoning / instruction

| Model | Params/arch | License | Fit | Best at |
|---|---|---|---|---|
| **Qwen3.6-35B-A3B** | 35B MoE / 3B act | Apache-2.0 | ✅ ~21 GB | **Default local daily driver** (fast MoE) |
| Qwen3.6-27B (dense) | 27B dense | Apache-2.0 | ✅ ~17 GB | Best local quality; ties Sonnet 4.6 (AA Agentic) |
| Gemma 4 31B (dense) / 26B-A4B | dense / MoE | Gemma | ✅ | Best local prose + general; MMLU-Pro 85.2 |
| OLMo 3-Think 32B | 32B dense | Apache-2.0 | ✅ | Fully-open auditable local reasoning specialist |
| Gemma 4 E4B · Phi-4-mini 3.8B · Qwen3.5-9B | ≤9B | open | ✅ tiny | Edge/on-device, phone/CPU-feasible |
| DeepSeek-V4 · Kimi-K2.6 · GLM-5.x · Qwen3.7 (235B+) | 200B–1T MoE | mixed | ☁️ | Frontier open reasoning/writing — API-tier |

## 3. Vision / multimodal (VLM)

| Model | Params/arch | License | Fit | Best at |
|---|---|---|---|---|
| **Qwen3-VL-30B-A3B-Instruct** | 31B MoE / 3B act | Apache-2.0 | ✅ | **Best drop-in upgrade** over gemma4 critique (run via MLX/llama.cpp — Ollama vision broken) |
| InternVL3.5-30B-A3B | 30B MoE | open | ✅ | Comparable general VLM alternative |
| MiniCPM-V 4.5 | 8B | Apache-2.0 | ✅ | Small VLM that **works in Ollama vision**, beats gemma4 OCR |
| DeepSeek-OCR 2 · dots.ocr (3B) · PaddleOCR-VL | 3B / spec | Apache-2.0 | ✅ | **Document/OCR/charts** specialists |
| Moondream 3 (9B-A2B) · Moondream 0.5B | tiny MoE | open | ✅ | Fast alt-text/caption/UI-detection (5–20× gemma4) |
| Qwen3-VL-235B · InternVL3.5-241B · Llama4-Maverick 400B | huge MoE | mixed | ☁️ | Frontier multimodal — API-tier |

## 4. Image / video generation

| Model | Type | License | Fit | Best at |
|---|---|---|---|---|
| **Z-Image-Turbo 6B** | few-step T2I | Apache-2.0 | ✅ mflux-native | **Best fast add to `imagine`** (~8 steps, #1 open arena, commercial-clean) |
| FLUX.2 Klein 4B | T2I + edit | Apache-2.0 | ✅ MLX | Sub-second gen+edit in one, commercial-clean |
| Qwen-Image 2.0 (20B) | T2I | Apache-2.0 | ✅/🟡 | Best commercial-OK open quality + **text-in-image champ** |
| Qwen-Image-Edit (2511/Plus) | edit/ControlNet | Apache-2.0 | ✅ | **Best instruction editing**, beats FLUX Kontext |
| FLUX.2 [dev] 32B | T2I | **non-commercial** | 🟡 heavy | Top photorealism (license caution) |
| LTX-2.3 distilled · HunyuanVideo-1.5 8B | video | mixed | 🟡 minutes/clip | Most feasible local video (MLX); Wan 2.5 is API-only |
| HunyuanImage 3.0 80B | T2I | open | ☁️ | Largest open image model — multi-GPU |

## 5. Embeddings / RAG / rerankers + speech

| Model | Task | License | Fit | Best at |
|---|---|---|---|---|
| **Qwen3-Embedding-0.6B** | embedding | Apache-2.0 | ✅ tiny | **Best local RAG pick** (1024-dim, 32k ctx) — wire into `simonw/llm` |
| EmbeddingGemma-300M | embedding | Gemma | ✅ <200MB | Lightest on-device (Matryoshka 768→128) |
| Qwen3-Embedding-8B · BGE-M3 | embedding | Apache/MIT | ✅ | Accuracy ceiling (#1 MTEB ML) / hybrid workhorse |
| bge-reranker-v2-m3 · Qwen3-Reranker-0.6B | rerank | Apache-2.0 | ✅ | Local default reranker (avoid Jina = non-commercial) |
| **Parakeet-TDT-0.6b-v3** (parakeet-mlx) | ASR | open | ✅ MLX | **Best Mac speech-to-text** (~6.3% WER, timestamps) |
| Whisper large-v3-turbo | ASR | MIT | ✅ | 99-language + translation (mlx-whisper/whisper.cpp) |
| Kokoro-82M | TTS | Apache-2.0 | ✅ | Cleanest local default voice (real-time CPU/MLX) |
| Chatterbox | TTS clone | MIT | ✅ | Best clean-license zero-shot voice cloning (~5s) |

---

## Quick reads per your setup

- **Heavy coder you just chose** is the right local pick — nothing open beats Qwen3-Coder-Next 80B-A3B in the 64 GB-fit class; everything better is API-tier.
- **One-line upgrades** to the existing suite: VLM critique → **Qwen3-VL-30B-A3B** (via MLX); image gen → add **Z-Image-Turbo** to `imagine`; future RAG → **Qwen3-Embedding-0.6B** via `llm-sentence-transformers`.
- **License landmines** flagged in detail files: FLUX.2 dev (non-commercial), Jina rerankers (CC-BY-NC), Fish-Speech/XTTS (restricted), HunyuanVideo (disputed). Clean-commercial sets are noted per cluster.
