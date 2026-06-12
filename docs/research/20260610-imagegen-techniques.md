# High-grade local image generation — techniques (consolidated)

Synthesis of three research sweeps (2026-06-10) into one practical reference for generating
versatile, high-grade images locally on Apple Silicon with `imagine` (mflux). Source docs:
`20260610-imagegen-prompting.md`, `-pipeline.md`, `-local-workflows.md` (sources listed at bottom).

## TL;DR — the decision guide

- **Pick the model by the result, not by habit.** Fast draft → Z-Image turbo / schnell. Photoreal
  final → Flux.1 dev. **Legible text → Ideogram 4.0 or Qwen-Image.** Edit an existing image → Flux
  Kontext. Balanced/faster-than-dev → Flux.2 klein.
- **Prompt in prose for Flux/Qwen** (natural language, T5). Comma-keyword style is an SDXL habit —
  it degrades Flux.
- **Negative prompts are ignored by Flux** (CFG-distilled) — use *positive* framing instead.
- **Iterate with discipline:** fix the seed while tuning the prompt; change one variable per batch;
  save winners as presets.
- **The quality ladder is a pipeline,** not one render: cheap draft → lock seed → tune on a better
  model → upscale/detail.

## 1. Model selection (2026 open-weight landscape)

| Model (`imagine -m`) | Best for | Steps | Guidance | Notes |
|---|---|---|---|---|
| `z-image-turbo`* | fast drafts | 2–4 | — | 6B turbo, great for seed-sweeps |
| `schnell` | fast general | 4 | n/a | great light, weak text/coherence |
| `flux2` (klein-4b) | balanced | ~8 | — | newer, faster than dev |
| `dev`* | photoreal finals | 20–30 | 3.5 | gated; photoreal king; 3.5=photoreal, 4–6=illustration |
| `qwen` | legible text + strong overall | 35–45 | 4–5 | quote text; disable built-in enhancer for layouts |
| `ideogram4`* | **best text (0.97 OCR)** | — | — | released Jun 2026; top open text model |
| `kontext`* | instruction editing of an image | — | — | `mflux-generate-kontext` |

*not yet in our registry — add a `resolve_model` case line (see §8). SD3.5 is a dead end in 2026 — skip.

## 2. Prompting

- **Anatomy (Flux/Qwen, prose):** subject → composition → lighting → lens/camera → style → mood →
  detail boosters. Front-load subject+style in the first ~70 tokens (CLIP gestalt); scene/atmosphere
  after (T5 handles up to 512 tokens; **schnell only 256**).
- **Flux = prose, SDXL = tags.** Don't mix; mixing degrades both.
- **Negative prompts:** effective on SDXL; **silently ignored by CFG-distilled Flux** (schnell/dev).
  For Flux, replace "bad hands" with "five fingers clearly visible." `--neg` only helps on qwen/dev.
- **Text in images:** quote all text in `"double quotes"`; 1–3 words per line for >60% accuracy;
  ask for "high contrast" + "dark overlay under text"; raise guidance (4–5) + steps (35–45). Use
  **qwen** or **ideogram4** — schnell/dev cannot render legible text at any setting.
- **gemma4 expansion (our `--enhance`) works when constrained:** the system prompt must fix target
  style (prose), length (40–70 words for Flux), forbid quality boilerplate + `--ar` flags + concept
  redirection. Build a fragment library (portrait/scene/product) for it to draw from.
- **Failure-mode mitigations:** extra limbs → positive anatomy framing + fewer subjects; duplicate
  subjects → name a single subject explicitly; garbled text → switch to qwen/ideogram + quote it.

## 3. Generation settings

- **Steps:** schnell 4 (distilled; >8 wasteful), dev 20–30, qwen 35–45, z-image 2–4.
- **Guidance vs CFG:** Flux "guidance" (3.5 photoreal → 6 illustration) is *not* classical CFG (which
  stays 1.0 for Flux). Our registry already sets model-aware guidance (dev 3.5, qwen 4).
- **Samplers/schedulers:** Euler+Simple = safe baseline; DEIS+Beta = sharper/higher-contrast; the
  Karras scheduler improves quality at lower step counts.
- **Quantization on 64 GB:** FP16 for archival hero renders, **Q8 for daily high-quality** (~14 GB,
  <1% loss), Q6 for fast iteration, Q4 for concept sketching only (8–12% loss). `imagine -q`.

## 4. Conditioning & input images (when to use which)

| Technique | mflux | When | Key setting |
|---|---|---|---|
| **img2img** | `imagine --from IMG` | reimagine from a starting image | denoise/strength 0.35–0.55 (>0.7 → use ControlNet) |
| **ControlNet** | `mflux-generate-controlnet` / `-depth` | lock structure/pose/composition | canny 0.4–0.8, depth 0.5–0.7, combined ≤0.9 |
| **Instruction edit** | `mflux-generate-kontext` / `-qwen-edit` | "make the sky sunset" | 3-layer prompt (Action / Context / Preservation), one change per pass |
| **Inpaint/outpaint** | `mflux-generate-fill` | replace/extend a region | denoise 0.9–1.0, guidance 30–50, blur mask edges |
| **Style transfer** | `mflux-generate-redux` | match a reference's style | weight ≤0.5 to keep prompt influence |
| **LoRA** | `--lora-paths` `--lora-scales` | borrowed style/subject (no training) | scale 0.8–1.0 + trigger words mandatory |

## 5. Upscaling & refinement

- **Two-stage upscale:** generate at 512–1024 → Flux.2 klein → 2048 → `mflux-upscale-seedvr2`
  (tiled, 1024 tile, 32–64 px padding) → 4096. Face/detail pass: DDIM, denoise 0.4–0.6.
- **The iterative workflow that wins:** seed-sweep on schnell/Q4 (cheap) → **lock the seed** → tune
  guidance/prompt on dev/Q6 → final render at dev/Q8 or FP16.

## 6. The canonical versatile pipeline

```
 draft            final            text-in-image      edit            hero
 Z-Image/schnell → Flux.1 dev   →  Ideogram4/Qwen  →  Kontext     →   ControlNet(canny)
 (2-4 steps)      (8-bit, 25st)    (quoted text)      (1 change/pass)  + SeedVR2 upscale
```
Pick the leg you need; you rarely run all five. The art-director persona (todo) automates choosing.

## 7. LLM-in-the-loop (uses models you already have)

- **Prompt engineer:** gemma4 expands a terse idea → rich prompt. Already wired as `imagine --enhance`.
- **Vision critic (next):** run a VLM (Qwen2.5-VL 7B ~8 GB, or your gemma4 vision) over the generated
  PNG — "what's wrong, what to change" — feed the fix back into the prompt and regenerate. Both the
  expander and the critic fit concurrently at 64 GB. This is the **generate → critique → refine loop**
  the art-director persona will drive, and it overlaps the deferred vision-probe (Task 7).

## 8. What to apply to OUR `imagine`

Already done: model registry, model-aware steps/guidance, `--enhance`, `--from`, `--style`, `--neg`.
Worth adding (each is a small, bounded change):

- **Registry: add `ideogram4` + `z-image-turbo`** (best-text + fast-draft) — one `resolve_model` line each.
- **A `--good` / quality alias** mapping to dev (or qwen) with the right steps, for one-flag quality.
- **A refine/upscale step** wrapping `mflux-upscale-seedvr2` (the hero-image leg).
- **A vision-critic subcommand** (`imagine critique <img>`) using gemma4/Qwen2.5-VL → suggested reprompt.
- **Qwen text helper:** when `-m qwen`, auto-quote detected text and nudge guidance up.

## Sources (selected; full lists in the three sweep docs)

Prompting: getimg.ai Flux guide · skywork.ai Flux prompting · civitai prompt-crafting · wavespeed.ai
Qwen text rendering · stable-diffusion-art SDXL-vs-Flux · apatero local LLM prompt enhancer.
Pipeline: github.com/filipstrand/mflux · apatero Flux Apple-Silicon / ControlNet / Fill guides ·
hanlab.mit.edu SVDQuant · comfyui-wiki Kontext · docs.comfy.org Flux ControlNet · myaiforce Flux.2 upscale.
Local/landscape: FLUX.1-Kontext-dev (HF) · Ideogram 4.0 launch · numonic ComfyUI PNG metadata ·
Draw Things Metal FlashAttention · ollama Qwen2.5-VL · machinelearning.apple.com LLMs-MLX-M5.
