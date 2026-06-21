# Open-Weight / Local-Runnable TTS & Voice Models — Landscape (mid-2026)

**Research date:** 2026-06-19
**Scope:** open-weight text-to-speech & voice models runnable locally, with emphasis on 64 GB Apple-Silicon Mac (MPS/MLX), zero-shot voice cloning, CPU real-time speed, and license cleanliness for a personal local project.
**Method:** live WebSearch + WebFetch (June 2026). Confidence tags: `[solid]` = multiple independent sources or primary model card; `[single-source]` = one source; `[hearsay]` = vendor self-claim / forum.

---

## TL;DR — the local Apple-Silicon picture

- **Best out-of-the-box on Apple Silicon, fastest, cleanest license:** **Kokoro-82M v1.0** (Apache-2.0, MLX + ONNX, runs real-time on CPU). No voice cloning, preset voices only.
- **Best zero-shot voice cloning + expressiveness, MIT license, MLX-supported:** **Chatterbox / Chatterbox Multilingual / Turbo** (Resemble AI). Clone from ~5 s of audio; emotion-exaggeration control; watermarked.
- **Best large-scale expressive foundation model, Apache-2.0:** **Higgs Audio v2 (3B)** — voice cloning + multi-speaker + prosody, but heavier (~3B, GPU-class; runs on 64 GB Mac but slower).
- **Best for two-speaker dialogue / podcasts:** **Dia-1.6B** (Nari Labs, Apache-2.0, MLX-supported).
- **Highest-quality open zero-shot cloning (research-license caveat):** **Fish-Speech / OpenAudio S1** — top-ranked open model on TTS Arena, but **non-clean license** (Fish Audio Research License on flagship weights).
- **Note on rankings:** As of mid-2026, **no open-weight model is in the TTS Arena V2 top 10** — those are all proprietary (Vocu V3.0, Inworld, CastleFlow, Papla). The gap to open has narrowed to ~81 ELO (from 223 in 2023). Treat the open cluster as roughly tied.

---

## TTS Arena V2 leaderboard — open-weight subset (early/mid-2026)

ELO is from the blind-preference TTS Arena V2 (fresh start vs V1). Top of overall board is proprietary; below is the **open-weight** subset.

| Overall rank | Model | Creator | ELO | License | Source date |
|---|---|---|---|---|---|
| 11 | Fish Audio S2 Pro | Fish Audio | 1128.7 | Research-license (non-clean) | Mar 2026 |
| 16 | Step Audio EditX | StepFun | 1104.9 | open | 2026 |
| 26 | Magpie-Multilingual 357M | NVIDIA | 1064.2 | open | 2026 |
| 32 | Kokoro 82M v1.0 | hexgrad | 1056.2 | **Apache-2.0** | 2026 |
| 33 | Voxtral TTS | Mistral | 1055.9 | open (Apache-ish) | 2026 |
| 35 | Maya1 | Maya Research | 1050.6 | open | 2026 |
| 51 | Fish Speech 1.5 | Fish Audio | 1011.9 | research-license | 2026 |

> Proprietary top 5 (for context): Vocu V3.0 (1581), Inworld TTS MAX (1579), CastleFlow v1.0 (1574), Inworld TTS (1571), Papla P1 (1562) — all closed, no Western API for the top two. `[solid]`

Sources: [TTS Arena V2 leaderboard](https://tts-agi-tts-arena-v2.hf.space/leaderboard) · [OfflineTTS leaderboard breakdown 2026](https://www.offlinetts.com/blog/tts-arena-leaderboard-2026/) · [SiliconFlow TTS leaderboard](https://www.siliconflow.com/articles/benchmark/text-to-speech-models). Confidence: `[solid]` (cross-confirmed across OfflineTTS + SiliconFlow; the live HF Space did not render a table to WebFetch).

---

## Per-model detail

### 1. Kokoro-82M (v1.0) — **top pick for clean, fast local Apple Silicon**
- **Params/size:** 82M (tiny). **License:** **Apache-2.0** (weights + ONNX). `[solid]`
- **HF repo:** `hexgrad/Kokoro-82M`; ONNX: `onnx-community/Kokoro-82M-v1.0-ONNX`; NVIDIA opt: `nvidia/kokoro-82M-onnx-opt`. MLX: `gabrimatic/kokoro-mlx`.
- **Frameworks:** PyTorch, **ONNX**, **MLX** (mlx-audio), candle-friendly. Runs **real-time on CPU**; trivially on MPS/MLX on a 64 GB Mac.
- **Best at:** speed + low memory + clean license. 54 voice presets, multilingual. **No voice cloning** (preset voices only).
- **Headline:** Hit **#1 on TTS Arena (legacy V1) in Jan 2026** beating 10–100× larger models; ELO ~1056 (V2, rank 32). MOS comparable to much larger models.
- **Sources:** [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) · [Kokoro review 2026](https://texttolab.com/blog/kokoro-tts-review) · [kokoro-mlx](https://github.com/gabrimatic/kokoro-mlx). `[solid]`

### 2. Chatterbox / Chatterbox Multilingual / Turbo (Resemble AI) — **top pick for voice cloning on Apple Silicon**
- **Params/size:** base ~0.5B; **Turbo 350M**; Multilingual V3 ~0.5B. **License:** **MIT**. `[solid]`
- **HF repo:** `ResembleAI/chatterbox`; GitHub `resemble-ai/chatterbox`.
- **Frameworks:** PyTorch + **MLX (mlx-audio supports Chatterbox)**. Runs on MPS/MLX on a 64 GB Mac. Turbo: **75 ms latency, ~6× real-time**.
- **Best at:** **zero-shot voice cloning from ~5 s of audio**; first open model with **emotion-exaggeration control** (single param); expressiveness; real-time. Multilingual V3 = **25 languages**, cross-lingual cloning.
- **Watermarking:** PerTh watermark **on by default** (first open TTS to ship auth-on-by-default) — note for provenance, not a blocker.
- **Headline:** vendor claims **~65% preference over ElevenLabs** in own blind test `[hearsay]`; on TTS Arena it's a competitive open option `[single-source]`.
- **Sources:** [ResembleAI/chatterbox](https://huggingface.co/ResembleAI/chatterbox) · [Chatterbox Multilingual](https://www.resemble.ai/learn/models/chatterbox-multilingual) · [Chatterbox Turbo](https://www.resemble.ai/chatterbox-turbo/) · [GitHub](https://github.com/resemble-ai/chatterbox). `[solid]` on license/clone; `[hearsay]` on the ElevenLabs win-rate.

### 3. Higgs Audio v2 (Boson AI) — **largest clean-license expressive foundation model**
- **Params/size:** 3B (`higgs-audio-v2-generation-3B-base`). **License:** **Apache-2.0** (most permissive large-scale TTS to date). `[solid]` — note one HF mirror lists `license: other`; the official Boson release states Apache-2.0.
- **HF repo:** `bosonai/higgs-audio-v2-generation-3B-base`; GitHub `boson-ai/higgs-audio`.
- **Frameworks:** PyTorch (Transformers). No first-class MLX port confirmed; runs on a 64 GB Mac via **MPS** but slower than the small models (3B + audio codec).
- **Best at:** expressiveness + emotion, **zero-shot voice cloning**, **multi-speaker dialogue**, prosody adaptation, even humming/background-music generation. Pretrained on 10M+ hours.
- **Headline:** **75.7%** win-rate over gpt-4o-mini-tts on EmergentTTS-Eval "Emotions"; 55.7% on "Questions". `[solid]`
- **Sources:** [bosonai/higgs-audio-v2](https://huggingface.co/bosonai/higgs-audio-v2-generation-3B-base) · [Boson blog](https://www.boson.ai/blog/higgs-audio-v2) · [BrightCoding writeup](https://www.blog.brightcoding.dev/2025/09/17/higgs-audio-v2-the-first-open-source-foundation-model-for-expressive-speech-and-voice-cloning/). `[solid]`

### 4. Dia-1.6B (Nari Labs) — **best for two-speaker dialogue / podcasts**
- **Params/size:** 1.6B. **License:** **Apache-2.0**. `[solid]`
- **HF repo:** `nari-labs/dia` (GitHub `nari-labs/dia`).
- **Frameworks:** PyTorch + **MLX (mlx-audio + mlx-tts-studio support Dia)**. Runs on consumer device; on a 64 GB Mac via MPS/MLX comfortably.
- **Best at:** ultra-realistic **multi-speaker dialogue in one pass**, audio-conditioned emotion/tone, nonverbals (laughter, cough, throat-clear). Voice-clone-able via audio conditioning.
- **Headline:** positioned as open ElevenLabs/NotebookLM-podcast alternative; strong expressiveness `[single-source]`.
- **Sources:** [nari-labs/dia GitHub](https://github.com/nari-labs/dia) · [MarkTechPost release](https://www.marktechpost.com/2025/04/22/open-source-tts-reaches-new-heights-nari-labs-releases-dia-a-1-6b-parameter-model-for-real-time-voice-cloning-and-expressive-speech-synthesis-on-consumer-device/). `[solid]` on license/size.

### 5. Kyutai TTS / Pocket TTS / Moshi — **lowest-latency streaming + tiny CPU model**
- **Params/size:** Kyutai TTS **1.6B** (server/streaming); **Pocket TTS 100M** (Jan 2026, CPU real-time); Moshi (speech-text foundation, full-duplex). **License:** open (CC-BY / permissive — verify per-repo). `[single-source]`
- **HF repo:** `kyutai/*` (e.g. `kyutai/moshiko-pytorch-bf16`); GitHub `kyutai-labs/delayed-streams-modeling`, `kyutai-labs/moshi`.
- **Frameworks:** PyTorch, candle/Rust, MLX variants exist (Moshi has MLX ports). Pocket TTS **runs real-time on CPU**.
- **Best at:** **streaming low-latency** (Moshi ~160–200 ms), full-duplex dialogue; **Pocket TTS** matches 10× larger models at 100M and supports **voice cloning** on CPU.
- **Headline:** Moshi theoretical 160 ms latency; Pocket TTS = best tiny-CPU cloning option of 2026. `[single-source]`
- **Sources:** [kyutai.org/tts](https://kyutai.org/tts) · [delayed-streams-modeling](https://github.com/kyutai-labs/delayed-streams-modeling) · [moshi GitHub](https://github.com/kyutai-labs/moshi). `[single-source]` (verify exact license + MLX support before relying).

### 6. Fish-Speech / OpenAudio S1 / S2 Pro (Fish Audio) — **highest-quality open, but license caveat**
- **Params/size:** S1 / S1-mini / S2 Pro family. **License:** **mixed** — MIT for self-hosting per some sources, **but flagship weights under FISH AUDIO RESEARCH LICENSE (non-clean for commercial)**. `[solid]` on the caveat → **flag for a personal-but-careful local project**.
- **HF repo:** `fishaudio/fish-speech-1` (+ OpenAudio S1 via playground/HF); GitHub `fishaudio/fish-speech`.
- **Frameworks:** PyTorch; runs locally (Docker image available). No first-class MLX; MPS works.
- **Best at:** **zero-shot voice cloning from 10–30 s**, 13 languages, high naturalness. **S2 Pro = highest-ranked open model on TTS Arena (ELO 1128.7, rank 11)**; Fish Speech 1.5 historically scored very high.
- **Headline:** S2 Pro #1 open in blind preference; ELO 1128.7. `[solid]`
- **Sources:** [fishaudio/fish-speech](https://github.com/fishaudio/fish-speech) · [OpenAudio S1](https://openaudios1.com/) · [HF model](https://huggingface.co/fishaudio/fish-speech-1). License caveat `[solid]` — **double-check the exact license on the specific weight you pull.**

### 7. Sesame CSM-1B — **conversational base model (clone needs fine-tune)**
- **Params/size:** ~1B (card lists ~2B in F32 tensors). **License:** **Apache-2.0**. `[solid]`
- **HF repo:** `sesame/csm-1b`; **MLX port: `senstella/csm-1b-mlx`** (Apple Silicon native). In Transformers since 2025-05.
- **Frameworks:** PyTorch (CUDA examples) + **MLX (senstella port)**. Runs on 64 GB Mac via MLX.
- **Best at:** **contextual conversational** speech (LLaMA-style dual decoder + Mimi codec). **NOT cloning out of the box** — base generation model, "not fine-tuned on any specific voice"; cloning requires separate fine-tune.
- **Headline:** first open contextual TTS from Sesame; quality good in-context. `[solid]`
- **Sources:** [sesame/csm-1b](https://huggingface.co/sesame/csm-1b) · [csm-1b-mlx](https://huggingface.co/senstella/csm-1b-mlx) · [Transformers CSM docs](https://huggingface.co/docs/transformers/model_doc/csm). `[solid]`

### 8. Orpheus TTS (Canopy Labs) — **LLM-native, emotion tags, voice cloning**
- **Params/size:** family of **3B / 1B / 400M / 150M** (Llama-3 backbone). **License:** **Apache-2.0**. `[solid]`
- **HF repo:** `canopylabs/orpheus-3b-0.1-pretrained` (+ -ft); GitHub `canopyai/Orpheus-TTS`.
- **Frameworks:** PyTorch (vLLM/llama-style serving); the smaller sizes are MPS-friendly. No confirmed first-class MLX.
- **Best at:** **zero-shot voice cloning**, **guided emotion/intonation via tags**, low latency (~200 ms, ~100 ms with input streaming). The 150M/400M tiers are attractive for fast local use.
- **Headline:** emergent LLM-for-speech quality; ~200 ms latency. `[single-source]`
- **Sources:** [canopyai/Orpheus-TTS](https://github.com/canopyai/Orpheus-TTS) · [orpheus-3b HF](https://huggingface.co/canopylabs/orpheus-3b-0.1-pretrained). `[solid]` on license/sizes.

---

## Secondary / supporting models (worth knowing, not shortlisted)

| Model | Size | License | Best at | Apple Silicon | Notes | Source |
|---|---|---|---|---|---|---|
| **F5-TTS** | ~0.3–0.5B | open (check repo; CC-BY-NC dataset caveat in some forks) | flow-matching zero-shot cloning, fast inference | PyTorch/MPS; community MLX | newer alt to XTTS, competitive quality, faster | [F5-TTS local guide](https://builderai.tools/blog/running-f5-tts-locally-for-voice-cloning) `[single-source]` |
| **IndexTTS** | GPT-style | open | **most robust/stable open zero-shot cloning**; beats XTTS on naturalness | PyTorch/MPS | industrial-grade, controllable, fast | [IndexTTS paper](https://arxiv.org/html/2502.05512v1) `[solid]` |
| **Coqui XTTS-v2** | ~0.5B | **Coqui Public Model License (non-commercial-ish — CPML)** | 17-lang cloning from 6 s; mature ecosystem | needs 4–6 GB VRAM; MPS works | Coqui defunct but model widely used; **license not fully clean** | [XTTS-v2 overview](https://www.aimodels.fyi/models/huggingFace/xtts-v2-coqui) `[solid]` |
| **MaskGCT** (Amphion) | large NAR | open (Amphion) | non-AR TTS, voice conversion; 100K hrs multilingual | PyTorch | upgraded to **Metis** (Feb 2025, unified speech tasks) | [Amphion MaskGCT](https://github.com/open-mmlab/Amphion/tree/main/models/tts/maskgct) `[solid]` |
| **MeloTTS** (MyShell) | small | **MIT** | **real-time on CPU**, multilingual, many English dialects | CPU/MPS | no cloning; great for fast clean local | [MeloTTS](https://tts.ai/text-to-speech/?model=melotts) `[solid]` |
| **Parler-TTS** | ~0.6–1B | **Apache-2.0** | **describe-the-voice via text prompt** (no reference clip) | PyTorch/MPS | great for prototyping voices by description | [inferless TTS compare](https://www.inferless.com/learn/comparing-different-text-to-speech---tts--models-part-2) `[solid]` |
| **NVIDIA Magpie-Multilingual 357M** | 357M | open (NVIDIA) | multilingual, ELO 1064 (rank 26) | PyTorch | strong small multilingual entry on Arena | [OfflineTTS leaderboard](https://www.offlinetts.com/blog/tts-arena-leaderboard-2026/) `[single-source]` |

---

## Decision guidance for the local project

### Best for LOCAL Apple-Silicon (64 GB Mac) use
1. **Kokoro-82M v1.0** — MLX/ONNX, real-time CPU, Apache-2.0, trivial to run. *Default if you don't need cloning.*
2. **Chatterbox (Turbo / Multilingual)** — MLX-supported via `mlx-audio`, MIT, cloning + expressiveness. *Default if you DO need cloning.*
3. **Dia-1.6B** — MLX (`mlx-audio` / `mlx-tts-studio`), Apache-2.0, dialogue.
4. **Sesame CSM-1B** — native MLX port `senstella/csm-1b-mlx`, Apache-2.0 (but cloning needs fine-tune).
> Runtime: **`mlx-audio`** (Blaizzy) is the unifying lib — Kokoro, Chatterbox, Dia, Whisper under one MLX library with an **OpenAI-compatible API server**. Strongly recommended host. [mlx-audio](https://github.com/Blaizzy/mlx-audio)

### Zero-shot VOICE CLONING (no fine-tune)
- **Chatterbox** (~5 s ref, MIT, MLX) — cleanest + easiest.
- **Fish-Speech / OpenAudio S1** (10–30 s ref, highest quality) — **license caveat**.
- **Higgs Audio v2** (Apache-2.0, heavier, best expressiveness).
- **IndexTTS** (most robust/stable), **F5-TTS** (fast flow-matching), **XTTS-v2** (mature, **non-clean license**), **Orpheus** (tag-driven), **Kyutai Pocket TTS** (100M, CPU).
- **NOT cloning out-of-box:** Kokoro, MeloTTS, Parler-TTS (describe-only), Sesame CSM (needs fine-tune).

### Fastest / real-time on CPU
- **Kokoro-82M** and **MeloTTS** — real-time on CPU, no GPU.
- **Kyutai Pocket TTS (100M)** — CPU real-time + cloning.
- **Chatterbox Turbo (350M)** — 75 ms latency, 6× real-time (MPS).

### License cleanliness (best → flag) for a personal local project
- **Cleanest (Apache-2.0 / MIT):** Kokoro, Chatterbox (MIT), Higgs Audio v2, Dia, Sesame CSM, Orpheus, Parler-TTS, MeloTTS (MIT).
- **Flag / verify before commercial or redistribution:** **Fish-Speech/OpenAudio** (Fish Audio Research License on flagship weights), **Coqui XTTS-v2** (Coqui Public Model License, restrictive), **F5-TTS** (some dataset/fork CC-BY-NC caveats — check the specific weight), **Kyutai** (verify per-repo).

---

## Caveats & confidence notes
- The live HF **TTS Arena V2 Space did not render its leaderboard table** to the fetcher; ELO figures are cross-confirmed via OfflineTTS + SiliconFlow secondary sources (`[solid]`) but exact week-to-week ELO drifts — top open cluster is within ~13–80 ELO, treat as tied.
- **No open-weight model is in the Arena V2 top 10** as of mid-2026; the leader open model is **Fish Audio S2 Pro (ELO 1128.7, rank 11, Mar 2026)**.
- MLX support claims for Kokoro/Chatterbox/Dia/CSM are confirmed via `mlx-audio` + dedicated ports; for Higgs/Fish/Orpheus, assume **MPS (PyTorch)** unless a port is verified.
- Verify the **exact license on the specific HF weight** you download — several models have permissive code but restrictive flagship weights (Fish), or a non-standard model license (Coqui CPML).

## Key source URLs
- TTS Arena V2 leaderboard: https://tts-agi-tts-arena-v2.hf.space/leaderboard
- OfflineTTS 2026 leaderboard breakdown: https://www.offlinetts.com/blog/tts-arena-leaderboard-2026/
- mlx-audio (Apple Silicon host): https://github.com/Blaizzy/mlx-audio
- Kokoro: https://huggingface.co/hexgrad/Kokoro-82M
- Chatterbox: https://huggingface.co/ResembleAI/chatterbox
- Higgs Audio v2: https://huggingface.co/bosonai/higgs-audio-v2-generation-3B-base
- Dia: https://github.com/nari-labs/dia
- Kyutai TTS: https://kyutai.org/tts
- Fish-Speech: https://github.com/fishaudio/fish-speech
- Sesame CSM-1B: https://huggingface.co/sesame/csm-1b
- Orpheus: https://github.com/canopyai/Orpheus-TTS
