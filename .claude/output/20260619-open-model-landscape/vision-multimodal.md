# Open-Weight Vision-Language / Multimodal Model Landscape — June 2026

**Compiled:** 2026-06-19 · live web sources (HF model cards, OpenVLM/OmniDocBench leaderboards, vendor blogs, roundups). Confidence tags: `[solid]` = corroborated by official card or ≥2 sources · `[single-source]` = one credible source · `[hearsay]` = roundup/forum only, unverified.

## TL;DR for this user

- **You run `gemma4:26b`** = **Gemma 4 26B MoE** (Google, released **2026-04-02**), a 25.2B-total / 3.8B-active MoE with a ~550M-param SigLIP vision encoder, 256K context, **vision works natively in Ollama** (Q4_K_M = 18GB download). It's a *general* image-understanding model — solid all-rounder for critique, but **not** a benchmark leader on OCR/charts or on hard MMMU reasoning. [solid]
- **The single biggest upgrade for general image critique** is **Qwen3-VL-30B-A3B-Instruct** (Apache-2.0, 31B-total / 3B-active MoE) — same "fits-easily" footprint as gemma4, materially stronger multimodal reasoning, OCR, grounding, and 256K→1M context. **Caveat:** vision is **broken in Ollama today** (mmproj crashes on Apple Silicon) — run it via **llama.cpp `llama-mtmd-cli` / `llama-server`** or **MLX**, not `ollama run`. [solid]
- **For document/screenshot/PDF/table work** (where gemma4 is weak), add a *specialist*: **PaddleOCR-VL 1.6** (OmniDocBench 96.33) or **DeepSeek-OCR 2** (3B, Apache-2.0, 91.09) — both crush general VLMs on layout-faithful Markdown extraction.
- **For fast local image description** (alt-text, scene captions, detection), **Moondream 3** (9B MoE / 2B active) or **Moondream 0.5B** beat gemma4 on latency by a wide margin.
- **Too big to run locally** but worth knowing as the quality ceiling: **Qwen3-VL-235B-A22B**, **InternVL3.5-241B-A28B**, **Llama 4 Maverick 400B**.

---

## (1) General VLMs that fit a 64GB Apple-Silicon Mac at 4-bit

A 64GB Mac realistically allocates ~40–48GB to a model. At 4-bit: a ~30B-total MoE (~16–20GB) is comfortable; a 32B dense (~18–20GB) fits; ~70B dense at 4-bit (~40GB) is the upper ceiling and tight.

| Model | Params / Arch | License | Repo / run path | Fits 64GB Mac @4-bit | Best at | Headline benchmark | Source (date) | Conf |
|---|---|---|---|---|---|---|---|---|
| **Qwen3-VL-30B-A3B-Instruct** | 31B total / ~3B active MoE; Interleaved-MRoPE + DeepStack ViT; 256K→1M ctx | Apache-2.0 | `Qwen/Qwen3-VL-30B-A3B-Instruct` (HF); GGUF exists; **vision via llama.cpp/MLX — NOT Ollama (mmproj crash on Metal)** | Yes, easily (~16–20GB) | All-round upgrade to gemma4: reasoning, OCR, 2D/3D grounding, GUI agent, video, long-ctx | 8B variant matches Qwen2.5-VL-72B on video; flagship rivals Gemini-2.5-Pro | [HF card](https://huggingface.co/Qwen/Qwen3-VL-30B-A3B-Instruct), [Ollama issue #16264](https://github.com/ollama/ollama/issues/16264) (2026) | [solid] |
| **Qwen3-VL-32B-Instruct** | 32B dense | Apache-2.0 | `Qwen/Qwen3-VL-32B-Instruct(-GGUF)`; same Ollama caveat | Yes (~18–20GB), tighter | Highest-quality Qwen3-VL that still fits comfortably; dense = simpler to quantize | (vendor charts, exact numbers not in card text) | [HF card](https://huggingface.co/Qwen/Qwen3-VL-32B-Instruct) (2026) | [solid] |
| **Qwen3-VL-8B-Instruct** | 8B dense | Apache-2.0 | `Qwen/Qwen3-VL-8B-Instruct(-GGUF)`; same caveat | Yes, trivially (~5GB) | Strong small general VLM; 8B punches at old-72B level on video | matches Qwen2.5-VL-72B on video benches | [HF card](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct) (2026) | [solid] |
| **InternVL3.5-30B-A3B** | ~30B total / ~3B active MoE; ViT–MLP–LLM, Qwen3 LM + InternViT-300M | Open weights (MIT-family per InternVL line) | `OpenGVLab/InternVL3_5-30B-A3B(-HF)` (HF); transformers/vLLM/lmdeploy | Yes (~16–20GB) | Reasoning + agentic; strong MMMU/MathVista; single-A100-class = fits Mac at 4-bit | InternVL3-78B set 72.2 MMMU SOTA among open MLLMs; 3.5 improves on it | [InternVL3.5 blog](https://internvl.github.io/blog/2025-08-26-InternVL-3.5/), [HF](https://huggingface.co/OpenGVLab/InternVL3_5-30B-A3B-HF) (2025-08-26) | [solid] |
| **InternVL3.5-38B** | 38B dense | Open weights | `OpenGVLab/InternVL3_5-38B-HF` | Yes but tight (needs 2×A100 in FP16 → fine at 4-bit on 64GB, ~22GB) | Highest InternVL that fits; best open MMMU reasoning class | (38B between 30B and 241B on the family curve) | [HF](https://huggingface.co/OpenGVLab/InternVL3_5-38B-HF) (2025) | [single-source] |
| **MiniCPM-V 4.5** | 8B (Qwen3-8B + SigLIP2-400M); LLaVA-UHD high-res | Apache-2.0 | `openbmb/MiniCPM-V-4_5(-gguf)`; **Ollama `minicpm-v4.5` (vision works)** | Yes, trivially (~6GB) | Best small-model OCR + high-res (1.8MP, any aspect); 4× fewer visual tokens | OpenCompass avg **77.2**; OCRBench surpasses GPT-4o-latest & Gemini-2.5 | [HF card](https://huggingface.co/openbmb/MiniCPM-V-4_5), [paper](https://arxiv.org/pdf/2509.18154) (2025) | [solid] |
| **Gemma 4 26B MoE** *(your current)* | 25.2B total / 3.8B active MoE; ~550M SigLIP vision enc; 256K ctx | Gemma | `gemma4:26b` (Ollama, **vision native**, Q4_K_M=18GB) | Yes (18GB) | Solid general all-rounder, image+video frames, multilingual, **easiest to run (Ollama)** | (no headline MMMU published; mid-pack vs Qwen3-VL/InternVL) | [Ollama](https://ollama.com/library/gemma4:26b), [Gemma 4 card](https://ai.google.dev/gemma/docs/core/model_card_4) (2026-04-02) | [solid] |
| **Llama 4 Scout** | 109B total / 17B active MoE; native early-fusion multimodal; 10M ctx | Llama 4 Community | `meta-llama/Llama-4-Scout-*` (HF) | Borderline — 109B@4-bit ≈ 55–60GB, **too tight for 64GB in practice** | Huge context, native multimodal; really an H100-class model | MMMU ~69.4; OCRBench ~847 | [Meta blog](https://ai.meta.com/blog/llama-4-multimodal-intelligence/), [Presenc](https://presenc.ai/research/best-open-weight-vision-language-models-2026) (2026) | [single-source] |

**Verdict vs gemma4:26b:** Qwen3-VL-30B-A3B and InternVL3.5-30B-A3B are the same "comfortable MoE" footprint with clearly stronger reasoning/OCR/grounding — they **beat** gemma4 on capability. The cost is run-path friction (no working Ollama vision yet → llama.cpp or MLX). gemma4 wins **only** on convenience (one-line Ollama vision). MiniCPM-V 4.5 **complements** gemma4: tiny, Ollama-native vision, far better OCR for its size.

---

## (2) Tiny / edge VLMs — fast local image description

| Model | Params / Arch | License | Repo / run path | Footprint | Best at | Headline benchmark | Source (date) | Conf |
|---|---|---|---|---|---|---|---|---|
| **Moondream 3 (preview)** | 9B MoE / **2B active**; 24 layers (4 dense + MoE 64 experts/8 active); SigLIP enc; 32K ctx; SuperBPE | Open (preview) | `moondream/moondream3-preview` (HF); Moondream SडK/Station | ~4–6GB @4-bit | Frontier-level reasoning at edge speed; detection, pointing, captions, UI grounding | COCO det **51.2** (+20.7 vs prior); OCRBench **61.2**; ScreenSpot UI F1@0.5 **60.3** | [Moondream 3 blog](https://moondream.ai/blog/moondream-3-preview), [HF](https://huggingface.co/moondream/moondream3-preview) (2025) | [solid] |
| **Moondream 2** | 2B dense; SigLIP + Phi-style LM | Apache-2.0 | `vikhyatk/moondream2` (HF); Ollama; MLX | ~1.5–2GB | Captioning, VQA, detection, point — classic tiny VLM | strong for 2B; widely deployed | [Moondream](https://moondream.ai/), [GitHub](https://github.com/m87-labs/moondream) (2025) | [solid] |
| **Moondream 0.5B** | 0.5B; "world's smallest VLM" | Apache-2.0 | `moondream/moondream-0_5b` (HF) | **816MB @4-bit / 996MB @8-bit RAM** | Ultra-low-latency alt-text, scene description on phones/edge; runs anywhere | smallest viable VLM | [Moondream 0.5B blog](https://moondream.ai/blog/introducing-moondream-0-5b) (2025) | [solid] |
| **Gemma 4 E4B** | Effective 4B; multimodal (image+video), native audio in | Gemma | `gemma4:e4b` (Ollama, vision native) | ~3–4GB | On-device multimodal incl. audio; Ollama-native | (on-device tier) | [Ollama](https://ollama.com/library/gemma4:e4b), [Gemma 4 card](https://ai.google.dev/gemma/docs/core/model_card_4) (2026-04-02) | [solid] |
| **Qwen3-VL-2B / 4B-Instruct** | 2B / 4B dense | Apache-2.0 | `Qwen/Qwen3-VL-2B/4B-Instruct(-GGUF)`; llama.cpp/MLX | ~1.5–3GB | Smallest Qwen3-VL; strong OCR/grounding for size; Thinking variants exist | (small tier of Qwen3-VL family) | [HF Qwen3-VL](https://huggingface.co/docs/transformers/model_doc/qwen3_vl) (2026) | [solid] |
| **Florence-2 / Phi-vision class** | 0.23B–0.77B (Florence-2); Phi-4-multimodal 5.6B | MIT | `microsoft/Florence-2-*`, `microsoft/Phi-4-multimodal-instruct` | tiny–6GB | Florence-2: dense detection/caption/OCR primitives; Phi-4-mm: MMMU 57.4 / OCRBench 742 | Phi-4-mm MMMU **57.4** | [Presenc](https://presenc.ai/research/best-open-weight-vision-language-models-2026) (2026) | [single-source] |

**Verdict vs gemma4:26b:** these don't out-reason gemma4 — they out-**speed** it by 5–20×. Moondream 3 (2B active) gives surprisingly strong UI/detection grounding gemma4 lacks. Use a Moondream tier when you want sub-second captions/alt-text/detection rather than a careful critique.

---

## (3) Document / OCR / chart specialists (screenshots, PDFs, tables)

These beat *every* general VLM (incl. gemma4) at layout-faithful extraction. OmniDocBench (1651 PDF pages, 10 doc types) and OCRBench/olmOCR-Bench are the leaderboards.

| Model | Params / Arch | License | Repo / run path | Best at | Headline benchmark | Source (date) | Conf |
|---|---|---|---|---|---|---|---|
| **PaddleOCR-VL 1.6** | VL OCR + layout modules (Baidu) | Apache-2.0 | `PaddlePaddle/PaddleOCR-VL` (HF); PaddleOCR toolkit | Full-document parsing — "the OCR job most teams actually ship" | **OmniDocBench 96.33** (leader) | [CodeSOTA OCR](https://www.codesota.com/ocr) (2026-06-16) | [solid] |
| **MinerU 2.5-Pro** | document-parsing VLM (OpenDataLab) | Apache-2.0 (2.5-Pro) / AGPL-3.0 (2.5) | `opendatalab/MinerU` | PDF→Markdown pipeline, tables, formulae | OmniDocBench **95.69** | [CodeSOTA OCR](https://www.codesota.com/ocr) (2026) | [solid] |
| **DeepSeek-OCR 2** | **3B** VLM; optical context compression / visual causal flow | Apache-2.0 | `deepseek-ai/DeepSeek-OCR-2` (HF); vLLM/Transformers/Unsloth | Grounded Markdown, efficient throughput, tables/charts/math; **small enough to run locally** | OmniDocBench **91.09** (+3.73 vs v1); olmOCR-Bench 76.3 | [HF](https://huggingface.co/deepseek-ai/DeepSeek-OCR-2), [Medium analysis](https://medium.com/@tentenco/deepseek-ocr-2-how-visual-causal-flow-architecture-teaches-ai-to-read-documents-like-humans-54b56ee34a06) (2026-01-27) | [solid] |
| **dots.ocr 1.5 / 3B** | **3B** (RedNote HILab) | Apache-2.0 | `rednote-hilab/dots.ocr` (HF) | Layout-aware extraction; SVG/scene-text track; compact | OmniDocBench **88.41**; olmOCR-Bench 79.1 | [CodeSOTA OCR](https://www.codesota.com/ocr), [OmniDocBench](https://github.com/opendatalab/OmniDocBench) (2026-03) | [solid] |
| **olmOCR (v0.4+)** | OCR pipeline over a VLM (Allen AI) | Apache-2.0 | `allenai/olmOCR-*` | Messy layouts, handwriting, RL-tuned; fully-open data+code | olmOCR-Bench **82.4** | [CodeSOTA OCR](https://www.codesota.com/ocr) (2025-10-21) | [solid] |
| **Qwen3-VL (as OCR)** | see §1 | Apache-2.0 | as §1 | Best *general* model for OCR when you also need reasoning over the doc; OCRBench leader among general VLMs | Qwen3.5-class hit OCRBench 931/1000 (text recog) | [CodeSOTA OCR](https://www.codesota.com/ocr) (2026-05-18) | [single-source] |

**Verdict vs gemma4:26b:** for screenshots/PDFs/tables, **don't use gemma4** — pair a 3B specialist (DeepSeek-OCR 2 or dots.ocr, both Apache-2.0 and locally runnable) for extraction, then optionally hand the extracted Markdown to gemma4/Qwen3-VL for reasoning. PaddleOCR-VL 1.6 is the accuracy ceiling if you can run the Paddle stack.

---

## (4) Video-understanding VLMs

| Model | Params / Arch | License | Run path | Best at | Headline benchmark | Source (date) | Conf |
|---|---|---|---|---|---|---|---|
| **Qwen3-VL** (8B → 235B) | text-timestamp alignment + interleaved MRoPE; 256K ctx | Apache-2.0 | llama.cpp/MLX/vLLM (Ollama vision broken) | Best open video understanding; 8B ≈ Qwen2.5-VL-72B; flagship ≈ Gemini-2.5-Pro on long video | par with Gemini-2.5-Pro / GPT-5-minimal on video; surpasses on long-video @256K | [Qwen3-VL Tech Report](https://arxiv.org/pdf/2511.21631), [bentoml guide](https://www.bentoml.com/blog/multimodal-ai-a-guide-to-open-source-vision-language-models) (2025-11) | [solid] |
| **InternVL3.5** | ViT–MLP–LLM | open weights | vLLM/lmdeploy/MLX | Strong on Video-MME, MVBench, MLVU, LongVideoBench, CG-Bench | clear gains over InternVL3 across 6 video benches | [InternVL3 paper](https://arxiv.org/pdf/2504.10479) (2025) | [solid] |
| **Gemma 4 (all sizes)** | frame-based video | Gemma | Ollama / HF | Video *frames* across all sizes incl. 26B you run; convenient | (no headline video number) | [Gemma 4 card](https://ai.google.dev/gemma/docs/core/model_card_4) (2026-04-02) | [single-source] |
| **LLaVA-Video / SlowFast-LLaVA-1.5** | token-efficient video LLMs | Apache-2.0 | HF | Long-form video on a token budget; research-grade | token-efficient long video | [SlowFast-LLaVA-1.5](https://arxiv.org/pdf/2503.18943) (2025) | [single-source] |

**Verdict:** gemma4 already does frame-based video, but **Qwen3-VL is the clear leader** — its 8B variant rivals the old 72B class, and the design is purpose-built for temporal alignment + 256K long-video context. If video matters, this is the upgrade.

---

## (5) API-tier multimodal too big to run locally (the quality ceiling)

Flag = why it won't run on a 64GB Mac.

| Model | Params | License | Why it's API-tier | Headline | Source (date) | Conf |
|---|---|---|---|---|---|---|
| **Qwen3-VL-235B-A22B-Instruct** | 235B total / 22B active MoE | Apache-2.0 | 235B@4-bit ≈ 120–130GB — won't fit 64GB | rivals Gemini-2.5-Pro / GPT-5 across multimodal | [Presenc](https://presenc.ai/research/best-open-weight-vision-language-models-2026), [bentoml](https://www.bentoml.com/blog/multimodal-ai-a-guide-to-open-source-vision-language-models) (2026) | [solid] |
| **InternVL3.5-241B-A28B** | 241B total / 28B active MoE | open weights | needs 8×A100; ~120GB@4-bit | SOTA among open MLLMs (general/reasoning/agentic) | [HF](https://huggingface.co/OpenGVLab/InternVL3_5-241B-A28B) (2025-08-26) | [solid] |
| **Llama 4 Maverick** | 400B total / 17B active MoE | Llama 4 Community | 400B too large; multi-GPU server | MMMU ~**73.4** (leads), OCRBench ~870 | [Presenc](https://presenc.ai/research/best-open-weight-vision-language-models-2026) (2026) | [single-source] |
| **Pixtral Large** | 124B dense | MRL/open weights | 124B@4-bit ≈ 65GB+, **deprecated** by Mistral | frontier image understanding (now superseded) | [Mistral](https://mistral.ai/news/pixtral-large/) (deprecated 2026) | [solid] |
| **Qwen2.5-VL-72B** | 72B dense | Tongyi Qianwen | 72B@4-bit ≈ 40GB — *technically* fits but tight & superseded by Qwen3-VL | MMMU ~70.2, OCRBench ~888 | [Presenc](https://presenc.ai/research/best-open-weight-vision-language-models-2026) (2026, "as of May 2026") | [single-source] |

---

## Cross-cutting practical notes

- **The Ollama-vision gap is the #1 gotcha (2026).** Many top new VLMs (Qwen3-VL, Qwen3.5-VL) ship as **GGUF main + separate `mmproj.gguf` vision file**, and Ollama's mmproj path is rough — Qwen3-VL-8B GGUF "registers as vision-capable but crashes on first image on Apple Silicon" ([ollama#16264](https://github.com/ollama/ollama/issues/16264)). **Working vision today:** llama.cpp `llama-mtmd-cli`/`llama-server`, **MLX** (best on Apple Silicon), or vLLM. Models that *do* work in Ollama vision now: **gemma4**, **MiniCPM-V 4.5**, **Moondream 2**. [solid]
- **MLX is the Apple-Silicon-native path** — for Qwen3-VL/InternVL on a 64GB Mac, prefer MLX or llama.cpp-Metal over Ollama until the mmproj path stabilizes. [single-source]
- **License watch:** Apache-2.0 (Qwen3-VL, MiniCPM-V 4.5, DeepSeek-OCR 2, dots.ocr, olmOCR, PaddleOCR-VL, Molmo, Pixtral-12B) is the cleanest. Gemma (custom), Llama 4 Community (custom, MAU cap), Tongyi Qianwen (Qwen2.5-VL-72B) carry restrictions. NVLM is CC-BY-NC (non-commercial).
- **Benchmark hygiene:** many OCR scores are vendor self-reported (CodeSOTA flags this); MMMU/OCRBench numbers in roundups are `[single-source]` unless taken from the official card. The 70B-class MMMU/OCRBench figures came from a roundup, not first-party cards.

## Recommended actions for this user

1. **Drop-in capability upgrade for image critique:** add **Qwen3-VL-30B-A3B-Instruct** via **MLX** or **llama.cpp** (Apache-2.0, fits easily) — keeps gemma4 as the Ollama-convenient fallback.
2. **Add an OCR/doc lane:** **DeepSeek-OCR 2** or **dots.ocr** (both 3B, Apache-2.0, locally runnable) for screenshots/PDFs/tables — gemma4 is not competitive here.
3. **Add a speed lane:** **Moondream 3** (or **MiniCPM-V 4.5** for Ollama-native vision + better OCR) for fast captions/alt-text/detection.
4. **Know the ceiling:** Qwen3-VL-235B / InternVL3.5-241B / Llama 4 Maverick are the API-tier quality bar — route to a hosted endpoint when local quality isn't enough.
