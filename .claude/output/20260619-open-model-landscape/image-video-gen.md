# Open-Weight Image & Video Generation Landscape — June 2026

Survey of open-weight diffusion/flow image + video models, curated for a user running
`imagine` = **mflux (MLX FLUX) on an M5 Pro, 64GB unified memory**, who also uses ComfyUI
and cares about FLUX / Qwen / SD-class local generation.

- **Date of survey:** 2026-06-19
- **Confidence tags:** `[solid]` = multiple independent sources · `[single-source]` = one source · `[hearsay]` = community/forum claim, unverified
- **Hardware lens:** A 64GB Apple-Silicon Mac is *excellent* for open **image** gen (every flagship fits, often unquantized or at 8-bit) and *marginal-to-painful* for **video** gen (most need 14–80GB VRAM-equivalent and run minutes-per-clip on MPS/MLX). Flags throughout.

---

## TL;DR cheat sheet

| Need | Top pick for a 64GB Mac | Why |
|---|---|---|
| Best quality T2I (commercial-OK) | **Qwen-Image 2.0** (Apache 2.0, 20B) | Leads open compositional benchmarks, native 2K, commercial license |
| Best quality T2I (max fidelity, NC license OK) | **FLUX.2 [dev]** (32B, non-commercial) | Frontier photorealism; heavy on 32B |
| Fast / few-step on MLX | **Z-Image-Turbo** (6B, Apache, ~8 steps) | Sub-second-class on Apple Silicon, mflux-native, #1 open on AA arena |
| Best text-in-image | **Qwen-Image 2.0** / **Qwen-Image-Edit** | Long paragraphs, tables, EN+ZH; beats FLUX on typography |
| Image editing / instruction | **Qwen-Image-Edit (2511/Plus)** + **FLUX.2 Klein** | Joint text+image encode; ControlNet-Union available |
| Video (feasible-ish on 64GB Mac) | **LTX-2.3 distilled** or **HunyuanVideo-1.5 8B** | Smallest footprints + active MLX ports; still minutes/clip |

---

## Subclass 1 — Flagship open text-to-image (quality)

| Model + version | Arch / params | License | Where to get | 64GB Mac feasibility | Best at | Source (date) | Conf |
|---|---|---|---|---|---|---|---|
| **Qwen-Image 2.0** (Feb 2026) | MMDiT, ~20B (2.0 markets a unified 7B gen+edit core; orig Qwen-Image is 20B MMDiT) | **Apache 2.0** | HF `QwenLM/Qwen-Image`; **mflux** (20B base); **ComfyUI native** (incl GGUF/Nunchaku) | Feasible; 20B wants 8-bit quant on 64GB, slower but runs. ComfyUI GGUF eases it | Compositional accuracy, native 2K, EN+ZH **text rendering**, infographics/posters from 1k-token prompts | qwenlm/Qwen-Image GitHub; comfyui-wiki qwen-image-2512; wavespeed 2026 | [solid] |
| **FLUX.2 [dev]** (Nov 2025) | Rectified-flow DiT, **32B** | **Non-commercial** (dev); commercial needs BFL license/API | HF `black-forest-labs/FLUX.2-dev`; **mflux** (FLUX.2 4B/9B variants); **ComfyUI** (NVIDIA fp8) | 32B is heavy — runnable at low-bit (mflux "Bonsai" low-bit FLUX.2) but slow; the 9B/4B Klein tiers are the practical local path | Frontier photorealism, multi-reference editing, lighting/texture | bfl.ai/blog/flux-2; github black-forest-labs/flux2; venturebeat (Nov 2025) | [solid] |
| **HunyuanImage 3.0** (Sep 2025) | **MoE, 80B total / 13B active**, 64 experts, unified autoregressive | Permissive (Tencent), **commercial-OK** per cards | HF `tencent/HunyuanImage-3.0` (+ `-Instruct`); ComfyUI community | **Not practical on 64GB** — 80B MoE; even active-param routing + KV makes this a multi-GPU/cloud model. Skip locally | Largest open model; rich prompt comprehension, native multimodal | arxiv 2509.23951; HF tencent/HunyuanImage-3.0; wavespeed 2026 | [solid] |
| **FLUX.1 [dev]** (2024, still strong) | DiT, **12B** | Non-commercial (dev); schnell is Apache | HF; **mflux native**; **ComfyUI** (huge ecosystem, GGUF via city96) | **Very feasible** — the proven mflux default. 12B runs 8-bit on 64GB comfortably; ControlNet + LoRA in mflux | Mature ecosystem, LoRAs, ControlNet, the safe daily-driver | en.wikipedia Flux; thundercompute Flux ComfyUI (Jun 2026) | [solid] |
| **HiDream-O1-Image-1.5** | (not fully disclosed here) — ranks Elo 1263 on AA arena, **3rd overall** incl closed | Open-ish (verify card) | HF (HiDream) | Unverified locally; treat as cloud-first until card checked | Top-tier arena quality among open-leaning models | artificialanalysis.ai text-to-image leaderboard (2026) | [single-source] |
| **Ideogram 4** (in mflux as 9B) | DiT, 9B, JSON-caption native | Verify (Ideogram historically closed; mflux lists a 9B base) | **mflux** lists Ideogram 4 9B | Feasible at 9B if weights are genuinely open — **confirm license before commercial use** | Typography / JSON-caption prompting | mflux README (2026) | [single-source] |

**Notes:** Closed leaders for reference only (not open): GPT Image 2 (Elo 1339), GPT Image 1.5, Nano Banana 2 / Gemini 3.1 Flash Image, Riverflow 2.0. Among **open** weights, the live consensus is **Qwen-Image 2.0** (commercial) and **FLUX.2 dev** (max fidelity, NC) at the top.

---

## Subclass 2 — Fast / turbo / distilled (few-step, Apple-Silicon / MLX)

| Model + version | Params / steps | License | Where to get | 64GB Mac speed | Best at | Source (date) | Conf |
|---|---|---|---|---|---|---|---|
| **Z-Image-Turbo** (Nov 26 2025) | **6B** DiT, distilled, **~8–9 steps** | **Apache 2.0** | HF `Tongyi-MAI/Z-Image`; **mflux** (Z-Image distilled+base, `-q` quant, LoRA); multiple MLX ports (z-image-turbo-mlx); ComfyUI | **Best fast option for MLX.** 6B → sub-second-class / few-seconds at 1024px on M-series; "3× faster than FLUX" framing; LeMiCa accel +~30% on M1–M4 | Speed + quality balance, strong EN+ZH text, **#1 open-source on AA arena (8th overall)** | github Tongyi-MAI/Z-Image; lovegen.ai; smartart.live (2026); AA leaderboard | [solid] |
| **FLUX.2 [klein] 4B (distilled)** (Jan 15 2026) | **4B**, distilled, ~sub-1s on capable HW | **Apache 2.0** (4B) | HF; **mflux** (FLUX.2 4B); **ComfyUI** (docs.comfy.org flux-2-klein) | **Very feasible & fast** on 64GB; 4B distilled is the lightest flagship-lineage model. Apache → commercial-OK output | Fast T2I **and** editing in one compact model; real-time interactivity | docs.comfy.org/tutorials/flux/flux-2-klein; flux2klein.ai; nextdiffusion (2026) | [solid] |
| **FLUX.2 [klein] 9B (distilled)** | **9B**, distilled | **FLUX Non-Commercial** (9B) | HF; **mflux**; ComfyUI | Feasible at 9B 8-bit; higher quality than 4B but NC license | Higher-fidelity fast editing/gen (non-commercial) | dev.to gary_yan; neurocanvas (2026) | [solid] |
| **FLUX.1 [schnell]** (2024) | **12B**, ~1–4 steps | **Apache 2.0** | HF; **mflux native**; ComfyUI | Feasible; classic Apache turbo, eclipsed on quality by Z-Image/Klein but battle-tested | Commercial-safe legacy turbo, huge tooling | mflux; en.wikipedia Flux | [solid] |
| **ERNIE-Image Turbo** | **8B**, single-stream DiT, distilled | Verify (Baidu) | **mflux** (ERNIE-Image distilled+base); mlx-gen fork enables it | Feasible at 8B; newer, smaller community | Alt fast DiT; check license before commercial | mflux README; mlx-gen (2026) | [single-source] |
| **FIBO** (Oct 2025+) | **8B**, JSON-prompt native, distilled | Verify card | **mflux** (FIBO distilled+base, editing, LoRA) | Feasible at 8B | Structured/JSON-prompt generation + editing | mflux README (2026) | [single-source] |

**MLX reality:** `mflux` (filipstrand) is the canonical MLX-native runtime and as of 2026 supports **Z-Image, FLUX.2 (4B/9B), Ideogram 4, ERNIE-Image, FIBO, SeedVR2, Qwen-Image (20B), Depth Pro, FLUX.1** — with `-q 8` 8-bit quant and multi-LoRA. The **mlx-gen** fork (lpalbou) ships fast compat fixes (Qwen edit, ERNIE, Bonsai low-bit FLUX.2, FLUX.2 editing). For the user's `imagine` workflow, **Z-Image-Turbo and FLUX.2 Klein 4B are the two best new few-step adds**; both are Apache → commercial output is clean.

---

## Subclass 3 — Best at TEXT-in-image

| Model | Why it wins on text | License | MLX / ComfyUI | Source | Conf |
|---|---|---|---|---|---|
| **Qwen-Image 2.0** | Professional typography from 1k-token instructions; infographics, PPT, posters, comics; **long paragraphs, tables, mixed EN+ZH**. Repeatedly cited as best open text rendering | Apache 2.0 | mflux (20B) + ComfyUI native | qwenlm/Qwen-Image; comfyui-wiki; 10b.ai GLM-vs-Flux-vs-Qwen (2026) | [solid] |
| **Qwen-Image-Edit (2511 / Plus)** | Same text engine, applied to edits — change/insert text in an existing image while holding layout | Apache 2.0 | mlx-gen (Qwen edit) + ComfyUI | medium diffusion-doodles model-rundown (2026); mindstudio qwen-image-edit-plus | [solid] |
| **Z-Image-Turbo** | "Excels at accurately rendering complex Chinese and English text" at 6B/8-step speed | Apache 2.0 | mflux + ComfyUI | github Tongyi-MAI/Z-Image; pxz.ai | [solid] |
| **FLUX.2 [dev]** | Strong text but the comparison pieces put **Qwen ahead specifically on text/typography**; FLUX leads on photorealism | NC (dev) | mflux + ComfyUI | 10b.ai GLM-vs-Flux-vs-Qwen (2026) | [solid] |
| **GLM-Image** (Zhipu) | Surfaced in 2026 "best for text in images" comparisons vs Flux/Qwen — verify open-weight status & size before relying | Verify | Check HF | 10b.ai (2026) | [single-source] |

**Bottom line:** for text-in-image, **Qwen-Image 2.0 is the open champion**; Z-Image-Turbo is the fast-and-good-enough option on MLX.

---

## Subclass 4 — Image editing / instruction / ControlNet

| Model | Capability | License | MLX / ComfyUI | Source | Conf |
|---|---|---|---|---|---|
| **Qwen-Image-Edit (2511 / Edit Plus)** | Instruction edit holding identity/lighting; **joint text+image encode** (Text-Encode-Qwen-Image-Edit node) gives strong edit grip; "pwns FLUX Kontext Dev" in community tests; ControlNet pose | Apache 2.0 | **mlx-gen** (Qwen edit) + **ComfyUI** workflows; up to 17MP/60MP via community forks | runflow comfyui-qwen-image-edit; FurkanGozukara wiki; rundiffusion (2026) | [solid] |
| **InstantX/Qwen-Image-ControlNet-Union** | Canny / SoftEdge / Depth / Pose guided gen up to **50MP+** for Qwen-Image | Apache-aligned | ComfyUI | diffusiondoodles Qwen ControlNets (2026) | [solid] |
| **FLUX.2 [klein] (4B/9B)** | Unified T2I **+ single/multi-reference editing** in one compact model | Apache (4B) / NC (9B) | **mflux** (FLUX.2 editing via mlx-gen) + ComfyUI | docs.comfy.org flux-2-klein; mflux README | [solid] |
| **FLUX.2 [dev]** | Single + multi-reference image editing at 32B fidelity | NC | mflux (heavy) + ComfyUI | bfl.ai/blog/flux-2 | [solid] |
| **FLUX.1 Kontext [dev]** | Established instruction-edit baseline; Qwen-Edit now generally beats it on complex edits | NC (dev) | ComfyUI; FLUX.1 in mflux | runflow / FurkanGozukara comparisons (2026) | [solid] |
| **FLUX.1 + ControlNet (Canny/Depth)** | Classic conditioning; **native in mflux** (ControlNet Canny + depth) | Apache (schnell) / NC (dev) | **mflux native** + ComfyUI | mflux README | [solid] |
| **SDXL / SD3.5 ecosystem** | Largest ControlNet + LoRA catalog; speed on consumer HW | SD community / Stability | ComfyUI (massive); MLX support thinner | bentoml guide; willitrunai SD-vs-Flux (2026) | [solid] |

**Bottom line:** **Qwen-Image-Edit** is the current open editing leader (and has the richest ControlNet-Union); **FLUX.2 Klein** is the best *all-in-one fast* gen+edit on MLX; SDXL still wins on sheer breadth of community ControlNets/LoRAs.

---

## Subclass 5 — Open VIDEO generation (hardware reality flagged)

> **Hard truth for the M5 Pro 64GB:** video gen is VRAM-bound and slow on Apple Silicon. MLX ports exist (Wan2.2-mlx, mlx-video, ltx-2-mlx) and **work**, but expect **minutes per short clip** and high memory pressure. Unified-memory helps fit models others can't, but compute (no CUDA, MPS/MLX) is the bottleneck. **Feasible to experiment; not a production video station.** For real throughput, rent a 4090/A6000.

| Model + version | Params / arch | License | Where to get | 64GB Mac feasibility | Best at | Source (date) | Conf |
|---|---|---|---|---|---|---|---|
| **LTX-2.3** (distilled, 8-step) | ~22B DiT (distilled runs 8 steps); video **+ audio** | Open (Lightricks; verify commercial tier) | HF (Lightricks); **MLX port `dgrauet/ltx-2-mlx`**; `james-see/ltx-video-mac` (MPS); ComfyUI | **Most feasible video on Mac.** Distilled 8-step = lowest footprint; MPS ~4–6 min/10s @1080p on M3 Max; native MLX port exists | Fast-ish local video, smallest practical footprint, has audio | crepal what-is-ltx-2-3; github dgrauet/ltx-2-mlx; james-see/ltx-video-mac (2026) | [solid] |
| **HunyuanVideo-1.5** (Nov 2025) | **8.3B** diffusion; T2V + I2V | Reports conflict: **Apache 2.0** vs **Tencent Hunyuan Community License** — *verify before commercial* | HF `tencent/HunyuanVideo-1.5`; ComfyUI low-VRAM workflows; GGUF 8GB community builds | Feasible — 8.3B is the **smallest quality T2V/I2V**; ~14GB VRAM-class (GGUF down to 8GB). On 64GB Mac runs but slow on MPS | Best quality-per-VRAM; I2V; consumer-grade | HF tencent/HunyuanVideo-1.5; willitrunai vram (2026); apatero guide | [solid] (license [single-source]) |
| **Wan 2.2** (14B / smaller variants) | 14B (+1.3B small); MoE-ish T2V/I2V; LoRA support | Open (Apache-family; verify) | HF `Wan-AI/...`; **`osama-ata/Wan2.2-mlx`** pure MLX port; `Blaizzy/mlx-video`; ComfyUI (huge) | Feasible with pain: FP8/GGUF brings 14B → ~6GB@480p; **but** MPS attempts cited **~180GB unified for 1s@16f** full-res, and 1.3B ~3s clip on M2 Ultra 125GB. Use small variant / heavy quant | Most mature open video ecosystem, LoRAs, I2V | spheron gpu-cloud (2026); github osama-ata/Wan2.2-mlx; localaimaster (2026) | [solid] |
| **Wan 3.0** (early 2026) | Improved temporal coherence over 2.x | Open-weight (per Flowith) — verify HF release | HF Wan-AI (verify); ComfyUI | Same constraints as Wan2.2, likely heavier — confirm weights actually posted | Longer-sequence identity coherence | flowith wan open-weight (2026); forvideo wan-2-7 recap | [single-source] |
| **Wan 2.5 / 2.6 / 2.7** | Audio+video, agentic multi-scene | **Proprietary** (2.5 weights NOT released — API-only; audio licensing blocks open release) | Alibaba Cloud API only | **Not local.** API-only | Synced audio+video, agentic prompts | spheron deploy-wan-2-5; mindstudio (2026) | [solid] |
| **HunyuanVideo (original)** | 13B | Tencent Community License | HF; ComfyUI | Heavy: 60–80GB orig / ~14GB with v1.5 offload. Prefer **1.5** instead | Superseded by 1.5 for local | spheron gpu-cloud (2026) | [solid] |
| **Mochi 1** (Genmo) | 10B AsymmDiT | Apache 2.0 | HF `genmo/mochi-1-preview`; ComfyUI | Painful: FP8 ~20GB, **8+ min/5s clip on a 4090** — slower on Mac. Apache license is the draw | Open Apache T2V baseline | spheron/willitrunai (2026) | [solid] |

**Video pick for this user:** start with **LTX-2.3 distilled** (native MLX port, smallest footprint, audio) or **HunyuanVideo-1.5 8B** (best quality-per-VRAM, I2V). Treat **Wan 2.2 small/quantized** as the "mature ecosystem but heavy" option. Anything Wan 2.5+ is cloud-only.

---

## MLX / mflux & ComfyUI availability matrix (for the `imagine` workflow)

| Model | mflux (MLX) | mlx-gen fork | ComfyUI | License flag |
|---|---|---|---|---|
| FLUX.1 dev/schnell | ✅ native (ControlNet, LoRA, edit) | ✅ | ✅ (largest ecosystem) | schnell Apache / dev NC |
| FLUX.2 dev (32B) | ⚠️ low-bit "Bonsai" only | ✅ editing | ✅ (NVIDIA fp8) | NC (dev) |
| FLUX.2 Klein 4B | ✅ | ✅ | ✅ | **Apache 2.0** |
| FLUX.2 Klein 9B | ✅ | ✅ | ✅ | NC |
| Z-Image-Turbo 6B | ✅ (`-q`, LoRA) | ✅ | ✅ | **Apache 2.0** |
| Qwen-Image 20B | ✅ base | — | ✅ native (GGUF/Nunchaku) | **Apache 2.0** |
| Qwen-Image-Edit | — | ✅ (mlx-gen) | ✅ workflows | **Apache 2.0** |
| ERNIE-Image 8B | ✅ | ✅ | community | verify |
| FIBO 8B | ✅ (edit, LoRA) | — | community | verify |
| Ideogram 4 9B | ✅ (listed) | — | — | **verify open status** |
| SeedVR2 3B/7B (upscale) | ✅ | — | ✅ | verify |
| LTX-2.3 (video) | ✅ `dgrauet/ltx-2-mlx` | — | ✅ | verify commercial |
| Wan 2.2 (video) | ✅ `osama-ata/Wan2.2-mlx`, `Blaizzy/mlx-video` | — | ✅ | Apache-family (verify) |
| HunyuanVideo-1.5 (video) | via mlx-video (check) | — | ✅ low-VRAM | **license conflict — verify** |

---

## Confidence & caveats

- **License conflicts to verify before any commercial use:** HunyuanVideo-1.5 (Apache vs Tencent Community — sources disagree), Ideogram 4 in mflux (Ideogram historically closed), ERNIE-Image, FIBO, Wan license family, LTX commercial tier. `[single-source]` on each.
- **HiDream-O1-Image-1.5** ranks very high on the AA arena (Elo 1263) but its open-weight status/size weren't confirmed in this pass — verify the HF card.
- **GLM-Image** (Zhipu) appears in 2026 text-in-image comparisons; open-weight status unconfirmed here.
- **Param-count nuance:** "Qwen-Image 2.0" is marketed around a unified ~7B gen+edit core in some 2026 coverage while the original `Qwen-Image` is a 20B MMDiT; mflux ships the 20B. Treat the 20B as what runs locally today.
- **Video on Apple Silicon** numbers (180GB/1s full-res Wan; 4–6 min/10s LTX on M3 Max) are `[single-source]`/community — directionally right (slow + memory-bound) but treat exact figures as estimates.

## Key source URLs (with dates)
- Z-Image: https://github.com/Tongyi-MAI/Z-Image · https://lovegen.ai/z-image-turbo (Nov 2025)
- Qwen-Image: https://github.com/QwenLM/Qwen-Image · https://comfyui-wiki.com/en/tutorial/advanced/image/qwen/qwen-image-2512 (2026)
- FLUX.2: https://bfl.ai/blog/flux-2 · https://github.com/black-forest-labs/flux2 · https://docs.comfy.org/tutorials/flux/flux-2-klein (Nov 2025 / Jan 2026)
- HunyuanImage 3.0: https://arxiv.org/abs/2509.23951 · https://huggingface.co/tencent/HunyuanImage-3.0 (Sep 2025)
- mflux: https://github.com/filipstrand/mflux · https://github.com/lpalbou/mlx-gen (2026)
- Qwen-Image-Edit: https://www.runflow.io/blog/comfyui-qwen-image-edit · https://medium.com/diffusion-doodles/model-rundown-z-image-turbo-qwen-image-2512-edit-2511-flux-2-dev-fc787f5e87ad (2026)
- Leaderboards: https://artificialanalysis.ai/image/leaderboard/text-to-image · https://wavespeed.ai/blog/posts/lm-arena-text-to-image-rankings-2026/ (Jun 2026)
- Video: https://huggingface.co/tencent/HunyuanVideo-1.5 · https://github.com/dgrauet/ltx-2-mlx · https://github.com/osama-ata/Wan2.2-mlx · https://www.spheron.network/blog/gpu-cloud-video-ai-2026/ · https://willitrunai.com/blog/hunyuanvideo-1-5-vram-requirements (2025–2026)
- SD/SDXL context: https://www.bentoml.com/blog/a-guide-to-open-source-image-generation-models · https://willitrunai.com/blog/stable-diffusion-vs-flux-2026 (2026)
