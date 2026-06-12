# Pipeline & Conditioning Techniques for High-Grade Local Image Generation
<!-- sessions: imagegen-research-pipeline@2026-06-10 -->

**Context:** Apple Silicon (M5 Pro, 64GB) · mflux (MLX Flux) CLI · Models: Flux schnell/dev, Flux.2 klein, Qwen-Image
**Facet:** Pipeline / Conditioning / Quality

---

## Quick-Reference: Model-Specific Defaults

```
┌────────────────┬──────────┬──────────┬─────────────┬──────────────────────────┐
│ Model          │ Steps    │ Guidance │ CFG         │ Notes                    │
├────────────────┼──────────┼──────────┼─────────────┼──────────────────────────┤
│ Flux schnell   │ 1–4      │ —        │ 1.0         │ Distilled; 4 steps sweet │
│                │ (4 sweet)│          │             │ spot; beyond 8 = waste   │
├────────────────┼──────────┼──────────┼─────────────┼──────────────────────────┤
│ Flux dev       │ 20–30    │ 3.5      │ 1.0         │ Guidance 3.5 = photo;    │
│                │ (25 std) │ (3.5–6)  │ (not CFG)   │ 3.5–6 = illustration     │
├────────────────┼──────────┼──────────┼─────────────┼──────────────────────────┤
│ Flux.2 klein   │ 4–8      │ 3.5      │ 1.0         │ Smallest/fastest;        │
│                │          │          │             │ edit-capable             │
└────────────────┴──────────┴──────────┴─────────────┴──────────────────────────┘
```

---

## Steps, CFG/Guidance, and Samplers

### Flux's Guidance Model is Not Classical CFG

Flux dev is a **guidance-distilled** rectified flow transformer. The "Distilled CFG Scale" (sometimes called `guidance`) is a separate concept from SD1.5/SDXL CFG:

- **Classical CFG**: leave at 1.0 (no negative prompt support; negative prompts are silently ignored)
- **Distilled guidance** (Flux's own param): 3.5 or lower → photorealistic; 3.5–6 → illustration/painting

### Step Budget by Goal

| Phase | Resolution | Steps | Q | Approx time (M5 Pro) |
|---|---|---|---|---|
| Concept draft | 512×512 | 4 (schnell) / 15 (dev) | 4-bit | 10–30 s |
| Refinement | 768×768 | 4 (schnell) / 25 (dev) | 6-bit | 30–90 s |
| Final render | 1024×1024 | 4 (schnell) / 28–35 (dev) | 8-bit | 90–180 s |

Going beyond 35 steps on dev produces negligible gains. Schnell beyond 8 steps is wasted compute — the distillation flattens the quality curve early.

### Sampler & Scheduler Recommendations

**Safe baseline:** `euler` + `simple` — lowest risk of artifacts, widely tested with Flux.

**For more detail/contrast:** `DEIS` + `beta` or `DEIS` + `kl_optimal`. DEIS gives sharper, higher-contrast images than Euler. The `beta` scheduler only performs optimally paired with DEIS.

**High quality but slow:** `[Forge]` samplers (ComfyUI Forge) with `kl_optimal` or `sgm_uniform`, paired with low distilled CFG (around 2.2).

**Sampler quality ranking (best→fastest):** Forge > DPM++ 2M > HEUN > DEIS > Euler

Karras scheduler works across most samplers and improves results at lower step counts by distributing noise reduction more evenly — useful when iterating fast on dev with 15–18 steps.

---

## Quantization Quality Tradeoffs (4/6/8-bit) for M5 Pro 64GB

With 64GB unified memory, you have headroom to run at high fidelity. Recommended strategy:

```
┌──────────┬──────────────────────────┬──────────────┬──────────────────────────┐
│ Q level  │ VRAM load + active       │ Quality loss │ Best use                 │
├──────────┼──────────────────────────┼──────────────┼──────────────────────────┤
│ FP16     │ 24–26 GB + 4–8 GB        │ none (ref)   │ Final archival renders   │
│ Q8       │ ~14 GB + 3–5 GB          │ < 1%         │ Daily high-quality work  │
│ Q6       │ 11–13 GB + 3–5 GB        │ 4–6%         │ Fast iteration; 16GB sys │
│ Q4       │ 8–10 GB + 2–4 GB         │ 8–12%        │ Rapid concept sketching  │
│ Q3/Q2    │ < 8 GB                   │ 15–25%+      │ Avoid; testing only      │
└──────────┴──────────────────────────┴──────────────┴──────────────────────────┘
```

**For M5 Pro 64GB:** Run Q8 for standard work, FP16 for final outputs. The memory bandwidth advantage of M-series chips means the quality gap between Q4 and Q8 is more visible than on discrete GPUs.

**SVDQuant research note:** MIT's SVDQuant demonstrates that properly implemented W4A4 (weight+activation) quantization can outperform naive NF4/W4A16 baselines on Flux dev, achieving 3× speedup over NF4 with better visual fidelity. When mflux gains W4A4 support, this becomes the new best option for speed-constrained runs.

**mflux CLI:** `-q 4`, `-q 6`, `-q 8` — the flag quantizes both transformer weights at load time. Lower bits also load faster, useful when prototyping with frequent model reloads.

---

## ControlNet: Canny, Depth, Pose

### When to Use Which

| Type | Controls | Best for |
|---|---|---|
| **Canny** | Edges/outlines | Product shots, lineart-to-render, preserving logos |
| **Depth** | 3D spatial structure | Portraits, architectural renders, scene recomposition |
| **Pose** (OpenPose) | Skeleton / limb placement | Character consistency, action poses |

mflux currently ships Canny ControlNet natively (`mflux-generate-controlnet`). Depth and pose require ComfyUI + MLX backend or Draw Things for Apple Silicon.

### Strength Settings by Use Case

```
Architectural render:  depth=0.5,  canny=0.7  (lines matter more than 3D feel)
Portrait style:        depth=0.6,  canny=0.3  (preserve face structure loosely)
Illustration from photo: depth=0.7, canny=0.2–0.4
Product variation:     canny=0.8,  depth=0.4  (keep shape, vary environment)
```

**Combined use:** reduce individual strengths so total guidance ≈ 0.7–0.9. E.g., depth=0.4 + canny=0.35. Exceeding ~1.0 combined freezes creative variance.

### Control Scheduling (Advanced)

Apply full control strength early in the denoising process, taper to 0.2 by step 60–70% of total. This lets large structure be governed by ControlNet but fine detail to emerge naturally. In ComfyUI, use the `end_percent` parameter (0.8–1.0 for full duration; 0.5–0.7 for "structure only").

### Preprocessing

- **Depth:** MiDaS (recommended) or ZoeDepth for indoor scenes. Output: grayscale (white=near, black=far).
- **Canny:** OpenCV Canny. Low threshold 100–150 for detail-rich; high threshold 200–250 for structural outlines only.
- **Resolution match:** control image must match generation resolution to avoid stretching artifacts.

### ControlNet + LoRA (Canny in mflux)

mflux supports concurrent ControlNet + LoRA. Use canny at moderate strength (0.5–0.65) and LoRA at 0.8–1.0 to apply style while preserving the structure of the reference image.

---

## LoRA: Using Pretrained LoRAs

### Loading and Scale

- **Default scale range:** 0.8–1.2 (start at 0.8; push to 1.0–1.2 for stronger effect)
- **Overcooking:** if the LoRA overwrites too much (saturated, plastic look), drop to 0.6–0.7
- **mflux CLI:** `--lora-paths path/to/lora.safetensors --lora-scales 0.9`
- **Multi-LoRA:** `--lora-paths a.safetensors b.safetensors --lora-scales 0.7 0.5` — scales sum, so keep each lower when stacking

### Compatibility

Flux dev LoRAs ≠ schnell LoRAs. On Civitai, Flux.1 D = dev, Flux.1 S = schnell. Using a dev LoRA on schnell often produces degraded results.

### Trigger Words

Nearly all style/character LoRAs require trigger words in the prompt. Without them the LoRA loads but produces no effect. Find them: Civitai page → "Trained Words" or `show info` in ComfyUI.

### Block Weight Analysis

Advanced control: different transformer blocks respond differently to LoRA influence. Block weight preset 7 (ComfyUI) preserves composition/pose/color while reducing "bleeding" of the LoRA into background. Useful when a LoRA is too aggressive. mflux does not yet expose per-block scaling — apply at the ComfyUI level if you need this.

---

## Redux / IP-Adapter: Image-Prompt Conditioning

Flux Redux is Black Forest Labs' official IP-adapter equivalent — it allows using an image as a prompt alongside (or instead of) text.

### Key Parameters

- **`downsampling_factor`** (or equivalent `image_strength`): 1 = maximum image influence, 5 = moderate, 9 = minimal. Start at 3 for balanced text/image control.
- **Weight at apply node:** 0.0 = off, 0.5 = balanced text+image, 1.0 = image-only (ignores text prompt)
- **Prompt structure with Redux:** `character → objects → environment` order helps prevent inconsistency across a batch

### When to Use Redux vs ControlNet

| Tool | Use when |
|---|---|
| Redux | Style transfer, image variations, "make it look like this image" |
| ControlNet Canny | Preserve specific edges/shapes while changing style/content |
| ControlNet Depth | Preserve 3D composition while changing everything else |
| img2img | Strong transformation of an existing image |

**Combined:** Redux (style) + ControlNet Depth (structure) is a powerful combo for "keep composition, apply this aesthetic." Set Redux weight ≈ 0.5, depth ≈ 0.5.

### IP-Adapter (XLabs)

XLabs flux-ip-adapter-v2 is the third-party alternative. Strength below 0.5 recommended — higher values degrade coherence when combined with ControlNet. For purely aesthetic style transfer, Redux outperforms XLabs IP-adapter on Flux dev in most benchmarks.

---

## img2img: Denoise/Strength Tuning

### Denoise Strength Guide

```
0.1–0.3   Preserve original nearly intact; minor tone/color shift
0.35–0.55 Sweet spot: meaningful change while retaining composition (default start)
0.55–0.75 Significant restyling; original composition still visible
0.75–0.95 Aggressive transformation; mostly new content
1.0       Full generation from noise (effectively text2img ignoring original)
```

**Flux-specific:** At higher resolutions, standard Flux sampling can over-denoise, losing the reference image. Use "Model Sampling Flux Normalized" (ComfyUI) instead of "Model Sampling Flux" — it preserves uniform sigma distribution across resolutions.

### img2img vs ControlNet: Decision Guide

- **img2img:** Use when you want the output to stay close to the input's colors, lighting, and overall feel. Fast, simple.
- **ControlNet:** Use when you need to preserve a specific structural feature (edges, depth, pose) while allowing aggressive style/content change. Supports full denoise=1.0 while still maintaining structure.

**Practical rule:** If denoise > 0.7 but you want to keep the shape → switch to ControlNet. If denoise < 0.5 → img2img is sufficient.

---

## Inpainting / Outpainting (Flux Fill)

Flux Fill is the dedicated inpaint/outpaint model. Do not use the base dev/schnell model for inpainting — Fill is specifically trained for mask-conditioned editing.

### Core Settings

- **Steps:** 20–30 (Fill converges faster than base Flux)
- **Guidance:** 30–50 range (Flux Fill uses higher guidance values than base)
- **Denoise for inpainting:** 0.90–0.95 for targeted replacement; 1.0 for complete fill
- **Denoise for outpainting:** 1.0 (the extended region has no original pixel context)

### Mask Strategy

- Extend mask 5–10px beyond target boundary for seamless blending
- Use broader strokes, not fine outlines — Fill blends better with fuzzy masks
- For object removal: prompt "clean background, matching textures, [lighting description]"
- For multi-region: process each region separately if they need different content

### Outpainting Workflow

Process in incremental passes: expand 25–50% per step with slight overlap. Large single-pass outpaints introduce coherence drift. Use the filled image as the next pass's input.

**mflux CLI:** `mflux-fill` — requires `--image-path`, `--mask-path`, `--prompt`. Mask: white = fill region, black = preserve.

---

## Instruction Editing (Flux Kontext / Qwen-Edit)

### Flux Kontext

Kontext is BFL's in-context editing model — it takes a reference image + an editing instruction and returns the modified image. It understands context so you only need to describe the change, not re-describe the whole scene.

**Effective prompt structure (three layers):**

```
[Action]       "Change the background to a tropical beach at sunset"
[Context]      "while keeping the woman in the same position and pose"
[Preservation] "maintaining her facial features, expression, and clothing"
```

**Settings:**
- Guidance: standard dev range (3.5–5)
- Steps: 25–30 (same as dev; Kontext is dev-based)
- Max prompt: 512 tokens
- For complex transforms: break into sequential single-change passes rather than multi-change prompts

**mflux CLI:** `mflux-generate-kontext` — reference image provided via `--image-path`, edit instruction via `--prompt`.

### Qwen-Image Editing

Qwen-based instruction editing (Qwen2.5-VL or FIBO in mflux) supports JSON-structured prompts for precise edits. Follow the model's native caption format for best adherence.

---

## Upscaling + Detail Enhancement

### Recommended Resolution Strategy

1. **Draft at 512×512 or 768×768** — fast iteration, find composition/prompt
2. **First pass at 1024×1024** — full render, seed lock
3. **Upscale with dedicated upscaler** (not Flux hires-fix) to 2048×2048 or 4096×4096

**Why not native Flux hires-fix?** Flux at high resolution (> 1.5 MP) over-denoises detail and slows generation significantly. A specialized upscaler at the end of the pipeline is faster and produces better results.

### Upscaling Stack (mflux native)

mflux ships `mflux-generate-controlnet` with upscale support and SeedVR2 integration:

```
Stage 1: Flux.2 klein + ControlNet upscale → 1024→2048
Stage 2: SeedVR2 tiled → 2048→4096
```

**SeedVR2 settings:**
- `tile_width` / `tile_height`: 1024
- `padding`: 32–64 (64 for fewer seams)
- `anti_aliasing_strength`: 0.0–0.2 (lower = sharper)

### Face / Detail Enhancement

After upscaling, apply face detailing pass:

- Load face detailer (SRPO or ADetailer equivalent)
- Sampler: `ddim` / `ddim_uniform` for face passes — more stable than Euler for inpainting small regions
- Denoise: 0.4–0.6 (enough to add pores/texture, not enough to change identity)
- Use a small mask blur on the face region for seamless blending

### Latent Upscale Alternative

For intermediate resolution boosts within the Flux pipeline (before final pixel upscaler):

- **Latent Interpolate Upscale** (sandner.art technique): hybrid img2img + latent upscale, adds detail while retaining concept; fixes the artifact problem caused by low denoise in Flux img2img at high res
- Denoise: 0.5–0.65 at this stage

---

## Seed Strategy and Iterative Refinement

### Reproducibility

Fixed seed = fully deterministic output given identical: prompt, model, steps, guidance, quantization level, resolution, sampler, scheduler, ControlNet settings.

**mflux CLI:** `--seed 42` (or any integer). mflux respects MLX's seed behavior.

**Cross-session reproducibility:** Store successful seeds alongside the full parameter set (prompt + all flags). A seed alone without the parameter context reproduces nothing useful.

### Batch / Seed Exploration Workflow

**Phase 1 — Seed sweep (broad exploration):**
```bash
for seed in 42 137 256 1337 9999; do
  mflux-generate --prompt "..." --seed $seed --steps 4 -q 4 --width 512 --height 512
done
```
Run 5–8 seeds at schnell/Q4/low-res. Pick 1–2 compositions.

**Phase 2 — Prompt/guidance refinement (lock seed):**
Keep the winning seed, vary guidance (3.0, 3.5, 4.0, 5.0) and prompt details. Compare outputs side by side.

**Phase 3 — Quality render (lock seed + params):**
Raise to dev, Q8, 1024×1024, 25–28 steps. The locked seed should reproduce the Phase 1 composition at higher fidelity.

**Phase 4 — Upscale:** Apply upscaling stack (see above section).

### Seed Variation Near a Winner

To explore variations of a good composition without drifting far:
- Use consecutive seeds: `seed+1`, `seed+2`, ... — these tend to share compositional DNA
- Or slightly vary guidance ±0.5 while keeping the seed

### Multi-LoRA Seed Behavior

Adding or removing a LoRA changes the computation graph — the same seed will produce different output. Lock all LoRA configs before the Phase 3 quality render.

---

## Putting It Together: Recommended Iterative Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1 — Explore                                                           │
│  schnell · Q4 · 512×512 · 4 steps · 5–8 seeds → pick winner               │
├─────────────────────────────────────────────────────────────────────────────┤
│ STAGE 2 — Condition & Refine                                                │
│  dev · Q6 · 768×768 · 20–25 steps · locked seed                            │
│  → Add ControlNet / Redux / img2img as needed                               │
│  → Tweak guidance (3.5 photo / 4.5–5 illustration)                         │
│  → Add LoRA at 0.8 scale; adjust down if overcooked                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ STAGE 3 — Quality Render                                                    │
│  dev · Q8 or FP16 · 1024×1024 · 28 steps · locked seed+params              │
├─────────────────────────────────────────────────────────────────────────────┤
│ STAGE 4 — Upscale & Detail                                                  │
│  Flux.2 klein → 2048 · SeedVR2 → 4096 · Face detailer (ddim, 0.45)        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Sources

1. **mflux GitHub (filipstrand/mflux)** — official CLI, feature list, ControlNet/LoRA/img2img/fill/kontext/upscale documentation
   https://github.com/filipstrand/mflux

2. **Andreas Kuhr — The Flux AI Guide** — steps, CFG, guidance, sampler/scheduler recommendations for schnell and dev
   https://andreaskuhr.com/en/flux-ai-guide.html

3. **Apatero — Flux on Apple Silicon M1–M4 Performance Guide** — quantization benchmarks, memory requirements, quality loss by Q level
   https://www.apatero.com/blog/flux-apple-silicon-m1-m2-m3-m4-complete-performance-guide-2025

4. **Apatero — Flux Depth and Canny ControlNet Complete Guide 2025** — strength settings by use case, combined ControlNet, preprocessing
   https://apatero.com/blog/flux-depth-canny-controlnet-complete-guide-2025

5. **Apatero — Flux Fill Inpainting and Outpainting Complete Guide 2025** — steps, guidance, denoise, mask strategy
   https://apatero.com/blog/flux-fill-inpainting-outpainting-complete-guide-2025

6. **MIT HAN Lab — SVDQuant: 4-Bit Quantization for FLUX** — quantization quality tradeoffs, memory/speed benchmarks, W4A4 superiority over NF4
   https://hanlab.mit.edu/blog/svdquant

7. **ComfyUI Wiki — FLUX.1 Kontext Guide** — prompt structure, iterative editing, parameter recommendations
   https://comfyui-wiki.com/en/tutorial/advanced/image/flux/flux-1-kontext

8. **ComfyUI Wiki — Flux.1 ControlNet Examples** — depth/canny usage, strength schedules
   https://docs.comfy.org/tutorials/flux/flux-1-controlnet

9. **Civitai — FLUX Samplers and Schedulers Test** — sampler comparison, scheduler pairings, distilled CFG interaction
   https://civitai.com/posts/9565521

10. **Civitai — Post-Training Block Weight Analysis for Flux LoRAs** — block weight presets, scale recommendations
    https://civitai.com/articles/8733/post-training-block-weight-analysis-give-flux-loras-a-second-breath

11. **MyAIForce — Upscale with Flux 2 Klein + SeedVR2** — two-stage upscaling workflow, tile settings
    https://myaiforce.com/upscale-with-flux-2-klein/

12. **RunComfy — Flux Redux for Image Variation and Restyling** — Redux parameters, style transfer workflow
    https://www.runcomfy.com/comfyui-workflows/flux-tools-flux1-redux-for-image-variation-and-restyling

13. **Stable Diffusion Art — Flux Denoising Strength (img2img)** — denoise scale, Flux-specific over-denoise behavior at high res
    https://stable-diffusion-art.com/denoising-strength/

14. **Sandner.art — Latent Interpolate Upscale** — detail-preserving latent upscale technique for Flux
    https://sandner.art/latent-interpolate-upscale-expanding-flux-and-sdxls-denoising-range/
