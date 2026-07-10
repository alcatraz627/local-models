# Open-Weight / Local ASR Landscape — mid-2026

Research date: 2026-06-19. Focus: open-weight speech-to-text that runs **fast and local on a 64GB Apple-Silicon Mac** via MLX or whisper.cpp. All figures pulled from live sources (HF model cards, Open ASR Leaderboard blog/paper, vendor blogs, parakeet-mlx/mlx-whisper repos, 2026 benchmark roundups).

> **WER = Word Error Rate** (lower is better). **RTFx** = throughput multiple over real-time (higher is faster; an RTFx of 2000 means 2000s of audio transcribed per second of compute, on the leaderboard's reference GPU — Mac numbers will be far lower but the *ranking* holds).

---

## TL;DR recommendations (Apple-Silicon, 64GB)

| Need | Pick | Why |
|---|---|---|
| **Best accuracy that runs local on Mac** | **parakeet-tdt-0.6b-v3 via parakeet-mlx** (multilingual) OR **whisper-large-v3 / large-v3-turbo via mlx-whisper** | Canary-Qwen-2.5B / Granite-8B win the leaderboard but have NO mature MLX path; parakeet-mlx is first-class native MLX and only ~6.3% WER. |
| **Fastest real-time / streaming on Mac** | **parakeet-mlx** (`transcribe_stream`) for batch+streaming; **Kyutai stt-1b-en_fr-mlx** or **Moonshine** for true low-latency streaming | parakeet RTFx is the highest of any accurate model; Kyutai ships an official MLX checkpoint built for 0.5s-delay streaming; Moonshine is the lowest-latency tiny option. |
| **Best multilingual local** | **parakeet-tdt-0.6b-v3** (25 EU langs, MLX) or **canary-1b-v2** (25 langs + translation, NeMo only) | parakeet v3 is the multilingual model that *also* has an MLX path. Whisper-large-v3 still wins on raw language count (99). |
| **Practical default** | **parakeet-mlx with parakeet-tdt-0.6b-v3** | Native MLX, top-tier speed, near-SOTA WER, punctuation + word timestamps, CC-BY-4.0, English+24 EU langs, auto language detect. Fall back to **mlx-whisper large-v3-turbo** when you need 99-language coverage or the Whisper ecosystem (srt/vtt tooling). |

**The core tradeoff:** the absolute accuracy leaders (Canary-Qwen-2.5B, Granite-Speech-3.3-8B, Phi-4-multimodal) are LLM-hybrid models with NeMo/transformers-only runtimes and no first-class MLX implementation — heavy and awkward on a Mac. The models that are genuinely *fast + native-MLX* are **Parakeet** (NVIDIA, via senstella/parakeet-mlx) and **Whisper** (via mlx-whisper / whisper.cpp). So on a Mac the real choice collapses to **parakeet-mlx vs whisper (MLX or cpp)**.

---

## Curated shortlist (5–8 models)

### 1. NVIDIA Parakeet-TDT-0.6B-v3 ⭐ (top Mac pick)
- **Params/size:** 600M · **License:** CC-BY-4.0 (commercial OK) · **HF:** `nvidia/parakeet-tdt-0.6b-v3` ; MLX: `mlx-community/parakeet-tdt-0.6b-v3`
- **Framework:** NeMo (original) → **native MLX via `senstella/parakeet-mlx`** (`pip install parakeet-mlx`, Apache-2.0 wrapper). Also Swift (`FluidInference/swift-parakeet-mlx`), NPU/ANE ports (NexaAI).
- **Apple Silicon:** YES — best-in-class native MLX. CLI + `transcribe_stream()` for real-time. ffmpeg required.
- **Architecture:** FastConformer-TDT (Token-and-Duration Transducer).
- **WER / speed:** **6.34% avg** on Open ASR Leaderboard; **RTFx 3,332** (reference GPU) — among the highest-throughput models of any accuracy class.
- **Languages:** English + 24 European (25 total), auto language detection, no prompting.
- **Best at:** speed+accuracy balance, long audio (up to 24 min full attention), word- & segment-level timestamps, punctuation + capitalization.
- **Source:** https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3 ; https://github.com/senstella/parakeet-mlx (2025-09) · **[solid]**

### 2. NVIDIA Parakeet-TDT-1.1B / Parakeet-RNNT-1.1B (English, max-throughput)
- **Params:** 1.1B · **License:** CC-BY-4.0 · **HF:** `nvidia/parakeet-tdt-1.1b`, `nvidia/parakeet-rnnt-1.1b`
- **Framework:** NeMo → parakeet-mlx supports `ParakeetTDT/RNNT/CTC/TDTCTC`.
- **Apple Silicon:** YES via parakeet-mlx.
- **WER / speed:** ~8.0% WER (ranks ~23rd on accuracy) but **RTFx >2,000**; Parakeet CTC 1.1B hits **RTFx 2,793 on the long-form track** vs Whisper-large-v3's 68.56 — ~40× faster with comparable long-form WER (6.68 vs 6.43).
- **Best at:** raw English throughput / long-form batch transcription. **English-only** — this is the key caveat vs the multilingual v3.
- **Source:** https://huggingface.co/blog/open-asr-leaderboard ; Northflank 2026 benchmark · **[solid]**

### 3. OpenAI Whisper large-v3 / large-v3-turbo ⭐ (the ecosystem default)
- **Params:** large-v3 1.55B · **turbo 809M** · **License:** MIT · **HF:** `openai/whisper-large-v3`, `openai/whisper-large-v3-turbo`; MLX: `mlx-community/whisper-large-v3-turbo`
- **Framework:** transformers / **whisper.cpp (GGUF/GGML)** / **MLX (`mlx-whisper`, `lightning-whisper-mlx`)** / faster-whisper (CTranslate2).
- **Apple Silicon:** YES — the most-supported. whisper.cpp Metal hits **10–12× real-time on large-v3**; `mlx-whisper` large-v3-turbo ~1.0s avg on the speedtest benchmark; `lightning-whisper-mlx` claims **10× faster than whisper.cpp, 4× faster than plain MLX-whisper** (batched).
- **WER / speed:** large-v3 ~7.4% / turbo ~7.75% avg (leaderboard); turbo within ~0.4 pts of v3 across benchmarks at ~5× the speed.
- **Languages:** **99 languages** — still the multilingual breadth champion. Translation built-in.
- **Best at:** widest language coverage, richest tooling (srt/vtt/timestamps), most mature Mac runtimes. **turbo** is the real-time sweet spot.
- **Source:** https://github.com/mustafaaljadery/lightning-whisper-mlx ; https://huggingface.co/mlx-community/whisper-large-v3-turbo ; promptquorum/whispernotes benchmarks · **[solid]**

### 4. Distil-Whisper distil-large-v3.5 (English, lean)
- **Params:** 756M · **License:** MIT · **HF:** `distil-whisper/distil-large-v3.5` (+ `-openai`, `-ONNX` variants)
- **Framework:** transformers / faster-whisper / whisper.cpp-compatible / MLX-portable.
- **Apple Silicon:** YES (transformers/faster-whisper; MLX via conversion).
- **WER / speed:** ~7.4% short-form, **~1.5× faster than large-v3-turbo**; trained on 98k hrs, ~1% behind v3 on long-form. RTFx ~1.46× relative.
- **Best at:** English-only, lower-memory Whisper-quality transcription; good middle ground if you're staying in the Whisper ecosystem but want more speed than turbo.
- **Source:** https://huggingface.co/distil-whisper/distil-large-v3.5 · **[solid]**

### 5. Moonshine v2 (Useful Sensors) — lowest-latency tiny/streaming
- **Params:** tiny 27M, base/small/medium variants · **License:** MIT · **HF:** `UsefulSensors/moonshine`, `-tiny`, `-base`, `-streaming-medium`
- **Framework:** Keras / ONNX (designed for edge runtimes). No official MLX, but tiny enough to run anywhere on Mac.
- **Apple Silicon:** YES (ONNX/CoreML, CPU — already real-time-trivial at this size).
- **WER / speed:** v2 **Tiny ~50ms latency (5.8× faster than Whisper-tiny)**, Medium 258ms (**43.7× faster than Whisper-large-v3**); error rates ~48% lower than Whisper-tiny, matches/beats Whisper-small/medium at 6–28× fewer params. 107ms on MacBook Pro.
- **Best at:** ultra-low-latency streaming on constrained/edge hardware, wake-word-adjacent live captioning. **English-focused** (Flavors-of-Moonshine adds specialized small langs).
- **Source:** https://arxiv.org/html/2602.12241v1 (Moonshine v2) ; https://huggingface.co/UsefulSensors/moonshine · **[solid]**

### 6. Kyutai STT (stt-1b-en_fr / stt-2.6b-en) — streaming-native, official MLX
- **Params:** 1B (en+fr) / 2.6B (en) · **License:** CC-BY-4.0 · **HF:** `kyutai/stt-1b-en_fr`, **`kyutai/stt-1b-en_fr-mlx`**, `kyutai/stt-2.6b-en`
- **Framework:** Moshi/Mimi-codec delayed-streams-modeling; **official MLX checkpoint shipped** (`-mlx`); also in transformers (added 2025-06-25).
- **Apple Silicon:** YES — one of the few with a vendor-published MLX build, purpose-built for streaming.
- **Speed/latency:** **0.5s delay**, semantic VAD, true streaming token-by-token.
- **Best at:** real-time streaming transcription with built-in voice-activity detection; en/fr (1B) or max-accuracy English (2.6B). Released 2025-06-17.
- **Source:** https://huggingface.co/kyutai/stt-1b-en_fr-mlx ; https://github.com/kyutai-labs/delayed-streams-modeling · **[solid]**

### 7. NVIDIA Canary-Qwen-2.5B — accuracy leader (NOT a great Mac fit)
- **Params:** 2.5B (Canary-1B encoder + Qwen3-1.7B decoder, SALM hybrid) · **License:** CC-BY-4.0 · **HF:** `nvidia/canary-qwen-2.5b`
- **Framework:** NeMo / transformers only. **No first-class MLX path.**
- **Apple Silicon:** Marginal — runs via transformers/PyTorch-MPS but heavy and slow; no optimized Mac runtime as of mid-2026.
- **WER / speed:** **#1 on Open ASR Leaderboard at 5.63% WER**, RTFx 418 (reference GPU). Released 2025-07-17.
- **Best at:** SOTA English accuracy + can also summarize (ASR-LLM hybrid). Use if accuracy is paramount and you have a GPU — **not** the Mac speed pick.
- **Source:** https://huggingface.co/nvidia/canary-qwen-2.5b ; https://www.marktechpost.com/2025/07/17/... · **[solid]**

### 8. Honorable mentions (leaderboard-relevant, weak Mac story)
| Model | Params | License | WER | Mac story | Source |
|---|---|---|---|---|---|
| **IBM Granite-Speech-3.3-8B** | ~9B | Apache-2.0 | **5.85%** (2nd) | transformers only, 8B = heavy on Mac; en/fr/de/es/pt | https://huggingface.co/ibm-granite/granite-speech-3.3-8b · **[solid]** |
| **Microsoft Phi-4-multimodal** | 5.6B | MIT | **6.14%** | transformers; multimodal (text+vision+speech); heavy | https://huggingface.co/microsoft/Phi-4-multimodal-instruct · **[solid]** |
| **NVIDIA Canary-1B-v2** | ~1B (978M) | CC-BY-4.0 | ~8.1% multiling avg / 5.2% common-lang | NeMo only; **25 langs + translation** | https://huggingface.co/nvidia/canary-1b-v2 · **[solid]** |
| **NVIDIA Canary-1B-Flash** | 883M | CC-BY-4.0 | high-acc, **RTFx >1000** | NeMo only; en/de/fr/es + translation | https://huggingface.co/nvidia/canary-1b-flash · **[solid]** |
| **Mistral Voxtral** | Mini/Small (chat); Voxtral-4B-TTS is TTS | Apache-2.0 | — | Voxtral Mini/Small = audio-understanding LLMs (ASR-capable); 2026 TTS release is text→speech, NOT ASR | https://mistral.ai/news/voxtral-tts/ · **[single-source]** — note Voxtral's headline 2026 release is **TTS**, the ASR variants are the earlier Mini/Small |

---

## Decision guide: whisper.cpp vs mlx-whisper vs parakeet-mlx

```
                        ┌─────────────────────────────────────────────┐
                        │  What do you need on the Mac?               │
                        └─────────────────────────────────────────────┘
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        ▼                                 ▼                                 ▼
  99 languages /              Best speed+accuracy             Lowest latency /
  Whisper tooling             (en or 25 EU langs)             true streaming
  (srt, vtt, ecosystem)               │                            │
        │                             ▼                            ▼
        ▼                     ┌──────────────┐            ┌──────────────────┐
 ┌──────────────┐            │ parakeet-mlx │            │ Kyutai stt-*-mlx │
 │ mlx-whisper  │            │ tdt-0.6b-v3  │            │  or Moonshine    │
 │ large-v3-    │            │ (6.34% WER,  │            │  (50–258ms)      │
 │ turbo        │            │  top RTFx)   │            └──────────────────┘
 └──────────────┘            └──────────────┘
        │
        ▼
 whisper.cpp (GGUF) when you want C/C++ embedding, no Python,
 CoreML+Metal, or to ship a binary. ~10–12× RT on large-v3.
```

- **parakeet-mlx** → default for transcription quality+speed on Apple Silicon. Native MLX, CC-BY-4.0, punctuation + word timestamps, en+24 EU langs. Use `mlx-community/parakeet-tdt-0.6b-v3`.
- **mlx-whisper** (or **lightning-whisper-mlx** for batched throughput) → when you need 99-language coverage, Whisper's translation, or the mature srt/vtt tooling. `large-v3-turbo` is the real-time sweet spot.
- **whisper.cpp** → when you want a dependency-free C/C++ binary, CoreML+Metal, embedding into an app, or no Python at all. GGUF quantized models, 10–12× real-time on large-v3.
- **Kyutai stt-*-mlx / Moonshine** → when the job is *live streaming with low latency* rather than batch file transcription.

## License caveats
- **CC-BY-4.0** (Parakeet all variants, Canary all variants, Kyutai): commercial use OK, **attribution required**. NVIDIA NeMo models are CC-BY-4.0 not Apache — fine for products but you must credit.
- **MIT** (Whisper, Distil-Whisper, Moonshine, Phi-4): most permissive.
- **Apache-2.0** (Granite-Speech, parakeet-mlx *wrapper*, Voxtral): permissive. Note the parakeet-mlx *runtime* is Apache but the *weights* are CC-BY-4.0.

## Confidence notes
- All headline WER/RTFx numbers are **[solid]** (HF model cards + Open ASR Leaderboard blog/paper + corroborating 2026 roundups).
- The exact *live* leaderboard ordering could not be scraped (the HF Space renders client-side) — rankings here are reconstructed from the leaderboard blog, the arXiv leaderboard paper (2510.06961), Slator, and Northflank's 2026 benchmark; treat the top-5 *order* as **[solid]** but a specific row's decimal as possibly ±0.2.
- Mac RTFx figures are **relative/qualitative [single-source]** — the leaderboard RTFx is reference-GPU; real Mac speed depends on chip (M1–M4) and quantization.
