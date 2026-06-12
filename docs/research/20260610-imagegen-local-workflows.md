# Local Image Generation on Apple Silicon: 2026 Tooling, Models & Workflows

> Research date: 2026-06-10 | Hardware context: Apple M5 Pro, 64 GB unified memory

---

## Table of Contents

1. [Apple Silicon Runner Comparison](#apple-silicon-runner-comparison)
2. [Quantization & Memory Strategy for Mac](#quantization--memory-strategy-for-mac)
3. [The 2026 Open Model Landscape](#the-2026-open-model-landscape)
4. [Reproducible / Versionable Workflows](#reproducible--versionable-workflows)
5. [Versatile Pipelines by Use Case](#versatile-pipelines-by-use-case)
6. [LLM-in-the-Loop: Prompt Expansion + Vision Critique](#llm-in-the-loop-prompt-expansion--vision-critique)
7. [Source Index](#source-index)

---

## Apple Silicon Runner Comparison

Four tools dominate the Mac image-gen landscape in 2026. They are not interchangeable — each has a primary niche.

```
┌──────────────────────────────────────────────────────────────┐
│  RUNNER          BACKEND     SPEED     MEM EFF   BEST FOR    │
├──────────────────────────────────────────────────────────────┤
│  Draw Things     Metal/CoreML  ●●●●●   ●●●●●    GUI/daily   │
│  mflux           MLX (Python)  ●●●●○   ●●●●○    CLI/script  │
│  ComfyUI         PyTorch MPS   ●●○○○   ●●●○○    Pipelines   │
│  DiffusionKit    CoreML (Swift) ●●●○○  ●●●●○    Embedding   │
└──────────────────────────────────────────────────────────────┘
```

### Draw Things

- **What it is**: Native SwiftUI Mac App Store app (free) with Metal FlashAttention 2.0 and on-demand weight loading.
- **Speed**: ~25% faster than mflux on M2 Ultra for Flux models; ~163% faster than DiffusionKit for SD3.5 Large. On M4 Pro 24 GB, Flux.1 Dev Q6_K takes ~50 s at 1024×1024/20 steps.
- **Memory**: On-demand weight loading cuts peak usage by ~50% vs naive loaders. At 8 GB you can run SD 1.5 8-bit; at 16 GB SDXL and Flux Schnell; at 24 GB everything.
- **Automation**: Has an HTTP API (port 7860) and a JavaScript scripting system. The `mcp-drawthings` bridge lets Claude Code call it directly. See: `npx -y mcp-drawthings`.
- **Limitations**: GUI-first; batch scripting is clunkier than mflux. No native LoRA training.
- **Best for**: GUI exploration, daily creation, blog/asset generation, users who want zero Python overhead.
- **Source**: [InsiderLLM SD Mac MLX guide](https://insiderllm.com/guides/stable-diffusion-mac-mlx/) · [Draw Things Metal FlashAttention post](https://medium.com/engineering-draw-things/metal-flashattention-2-0-pushing-forward-on-device-inference-training-on-apple-silicon-fe8aac1ab23c)

### mflux

- **What it is**: Line-by-line MLX port of Hugging Face Diffusers models; pure-Python CLI, install with `uv tool install mflux`.
- **Speed**: Slightly behind Draw Things (~25%), but more than 3× faster on M5 vs M4 for Flux-dev-4bit thanks to M5 Neural Accelerators.
- **Current version**: 0.18.0 (2026-06-07); 55 total releases.
- **Supported models** (as of v0.18): FLUX.1, FLUX.2 (4B/9B), Z-Image (6B), Ideogram 4 (9B), ERNIE-Image (8B), Qwen Image (20B), FIBO (8B), SeedVR2, Depth Pro.
- **Key features**: multi-LoRA with scales, ControlNet (Canny), depth conditioning, inpainting/fill, Redux, in-context editing, SeedVR2 upscaling, FIBO prompt tooling, metadata export, `--low-ram` flag.
- **Commands**: `mflux-generate`, `mflux-generate-controlnet`, `mflux-generate-z-image-turbo`, etc.
- **Best for**: CLI workflows, scripted batch pipelines, automation, precise seed/param control, the `imagine` wrapper in this project.
- **Source**: [filipstrand/mflux GitHub](https://github.com/filipstrand/mflux) · [mflux PyPI](https://pypi.org/project/mflux/)

### ComfyUI (+ MLX Nodes)

- **What it is**: Node-graph editor running PyTorch with MPS backend on Mac; MLX node extensions (`ComfyUI-MLX`, `Flux-MLX-ComfyUI`) accelerate specific ops.
- **Speed**: Slowest of the four in pure throughput — Flux Dev Q6_K: 50–90 s on M4 Pro 24 GB vs 50 s in Draw Things. ComfyUI-MLX extension claims 70% faster model loads and 35% faster post-load generation, plus 30% memory reduction.
- **Workflow superpower**: JSON workflow files embedded in output PNGs; drag-and-drop reproducibility; the most mature LoRA/ControlNet/custom-node ecosystem.
- **GGUF quantization**: Q6_K is the community sweet spot on Mac (10 GB, best quality/speed tradeoff).
- **Best for**: Complex multi-stage pipelines, inpainting, ControlNet compositing, reproducible workflows that need to be shared or version-controlled.
- **Source**: [ComfyUI MLX Nodes guide](https://www.runcomfy.com/comfyui-nodes/ComfyUI-MLX) · [Mac Mini M4 benchmark](https://www.heyuan110.com/posts/ai/2026-02-15-mac-mini-local-image-generation/)

### DiffusionKit (Argmax)

- **What it is**: Swift/Core ML inference framework from Argmax, designed for embedding into macOS/iOS apps. Not a user-facing tool.
- **Speed**: Slower than Draw Things by 20–163% depending on model; its value is the Swift API, not raw throughput.
- **Best for**: Developers embedding image gen into a native macOS app; not recommended for personal workflows.
- **Source**: [argmaxinc/DiffusionKit GitHub](https://github.com/argmaxinc/DiffusionKit)

### M5 Pro (64 GB) — Reality Check

With 64 GB unified memory and the M5 Neural Accelerators (GPU-embedded, M5-exclusive), this machine sits at the top of the consumer hierarchy:
- Flux.1 Dev 4-bit: 3.8× faster than M4 for the same task.
- Memory bandwidth: ~153 GB/s — no memory pressure concern at any quantization tier for models ≤ 20B.
- All models in the mflux registry run at full 16-bit or best quantization without `--low-ram`.
- FP16 Flux.1 Dev (full precision, 23 GB) fits comfortably alongside system overhead.

---

## Quantization & Memory Strategy for Mac

| Precision | Disk | Peak RAM | Speed | Recommended when |
|-----------|------|----------|-------|------------------|
| FP16 (full) | ~23 GB | ~24–26 GB | Baseline | 64 GB: always viable |
| 8-bit (`-q 8`) | ~12 GB | ~14 GB | ~15% faster | 24–32 GB |
| 4-bit (`-q 4`) | ~7 GB | ~9 GB | ~40% faster | 16 GB, or speed priority |
| GGUF Q6_K | ~10 GB | ~11 GB | ~35% faster | ComfyUI on 24 GB |

**For 64 GB M5 Pro**: Run FP16 or 8-bit for quality-sensitive work; 4-bit when batch-generating drafts at speed. Save a 4-bit quantized copy locally with `mflux-save --quantize 4 --path ./cache/flux-dev-4bit` — subsequent loads skip the download and quantization step, saving 60–90 s per session.

**`--low-ram` flag** (mflux): Releases model components after use; useful when running concurrent processes. Not needed at 64 GB.

---

## The 2026 Open Model Landscape

### FLUX.1 [dev] and [schnell] — Still the Foundation

- **Architecture**: 12B parameter rectified flow transformer (Black Forest Labs).
- **Dev**: Best photorealism, text rendering, compositional fidelity from open weights. Non-commercial license. 20–25 steps. The quality benchmark.
- **Schnell**: Apache 2.0 (commercial OK). 1–4 steps. Nearly dev-quality for most prompts. The default for iteration.
- **FLUX.1 [Kontext-dev]**: Image editing via text instruction — 12B, open weights under FLUX.1 Non-Commercial License. Handles multi-step iterative edits with "minimal visual drift". Runs locally via diffusers or ComfyUI native workflow. Requires ~24 GB full-precision; quantized down to ~7 GB.
- **Sources**: [HF FLUX.1-dev](https://huggingface.co/black-forest-labs/FLUX.1-dev) · [HF Flux.1-Kontext-dev](https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev) · [ComfyUI Kontext tutorial](https://docs.comfy.org/tutorials/flux/flux-1-kontext-dev)

### FLUX.2 (klein / 4B and 9B)

- Released January 2026 by Black Forest Labs.
- 4B distilled and 9B base variants. Faster than FLUX.1 with comparable output quality on photorealism.
- Supported natively in mflux 0.18. Runs well at 8-bit on 16 GB machines.
- **Best for**: Speed-priority workflows, draft generation, or when FLUX.1's 12B footprint is too large.

### Z-Image (6B, Nov 2025)

- 6B distilled model; substantially faster than Flux Schnell at equivalent output quality.
- Available in mflux as `mflux-generate-z-image-turbo` — 2–4 step generation.
- Commercial license (verify on HF model card before production use).
- **Best for**: Fast draft iteration on 16 GB machines; very low latency previewing.
- **Source**: [ComfyUI-Realtime-Lora supports Z-Image](https://github.com/shootthesound/comfyUI-Realtime-Lora)

### Ideogram 4.0 (9.3B, June 2026)

- **Released**: June 3, 2026 — first open-weights release from Ideogram AI.
- **Architecture**: 9.3B single-stream Diffusion Transformer.
- **Text rendering**: OCR accuracy of 0.97 on X-Omni English benchmark — highest among all open-weight models at this scale. Top-ranked open-weight model on Design Arena Elo leaderboard (behind only proprietary GPT/Gemini).
- **Features**: Native 2K output, bounding-box layout control, structured JSON prompting, transparency support, fine-tuning support.
- **License**: Open-weight but proprietary (not Apache 2.0; verify commercial use terms).
- **Now in mflux**: Supported as of v0.18.0.
- **Best for**: Any design involving readable text in the image, logo mockups, product labels, infographics, typography-heavy scenes.
- **Source**: [Ideogram 4.0 open-weight ranking](https://alternativeto.net/news/2026/6/ideogram-4-0-launches-with-2k-resolution-and-top-open-weight-ranking/) · [MindStudio Ideogram 4 analysis](https://www.mindstudio.ai/blog/ideogram-4-open-weight-image-model-fine-tune)

### Qwen Image (20B, Aug 2025+)

- Multimodal LLM from Alibaba, fine-tuned for text-to-image. Accepts very long, detailed natural-language prompts — up to thousands of tokens.
- **Dual-path**: Qwen2.5-VL handles semantic conditioning (~384 px tokens); VAE/ref path handles pixel fidelity.
- 20B: the largest standard model in mflux's registry. At 8-bit: ~21 GB; runs comfortably on 64 GB.
- **Best for**: Scenes requiring deep compositional understanding from long prose descriptions; art direction prompts that read like paragraphs.
- **Source**: Search results + mflux model table

### Stable Diffusion 3.5 Large

- **Verdict for 2026**: Awkward middle ground. More VRAM than SDXL, less quality than Flux. Community consensus: skip SD3.5 in favor of Flux Schnell unless you have a specific reason.
- **Exception**: SD3.5 Medium (2.5B) is a viable fast option on 8 GB machines where Flux is unrunnable.
- **Source**: [willitrunai Stable Diffusion vs Flux 2026](https://willitrunai.com/blog/stable-diffusion-vs-flux-2026) · [aiphotolabs comparison](https://aiphotolabs.com/compare/flux-vs-stable-diffusion-35-complete-2025-performance-comparison/)

### ERNIE-Image (8B, Apr 2026)

- From Baidu. 8B, distilled and base variants. In mflux 0.18.
- Competitive on photorealistic portraits and East-Asian aesthetic styles.
- License: verify before commercial use.

### Model Selection Quick Reference

```
┌────────────────────────────────────────────────────────────────────┐
│  USE CASE                FIRST PICK       FALLBACK                 │
├────────────────────────────────────────────────────────────────────┤
│  Photorealism            FLUX.1 dev       FLUX.2 9B               │
│  Fast drafts             Z-Image turbo    FLUX.2 4B (Schnell)     │
│  Text in image           Ideogram 4.0     FLUX.1 dev              │
│  Image editing           FLUX.1 Kontext   img2img any Flux        │
│  Illustration / art      FLUX.1 dev+LoRA  SD3.5 Medium            │
│  Long prose prompts      Qwen Image 20B   FLUX.1 dev              │
│  Commercial (open)       FLUX.1 schnell   FLUX.2 (verify)         │
│  Product/design layout   Ideogram 4.0     FLUX.1 dev+ControlNet   │
└────────────────────────────────────────────────────────────────────┘
```

---

## Reproducible / Versionable Workflows

### ComfyUI PNG Metadata Standard

Every ComfyUI output PNG embeds two complete JSON blobs in PNG `tEXt`/`zTXt` chunks:

1. **`workflow`** key: Visual node graph — node positions, widget values, connections, groups. This is what you drag back into ComfyUI to restore the UI.
2. **`prompt`** key: The execution plan — resolved inputs, seed values, sampler settings, model references, CFG, steps, dimensions. This is what the engine actually ran.

Key reproducibility parameters locked in the `prompt` JSON:
- `KSampler` node: `seed`, `steps`, `cfg`, `sampler_name`, `scheduler`
- `EmptyLatentImage`: `width`, `height`
- `CheckpointLoaderSimple`: model filename (the single biggest reproducibility risk — if you replace a model file with the same name, the JSON will silently point at a different model)
- `CLIPTextEncode`: positive and negative prompts

**Best practice**: After locking a good output, export the workflow JSON separately (`Workflow → Save As`), commit it to git alongside the output image. File-hash the model weights and record in a `models.lock.json` in the workflow directory.

**Source**: [Numonic ComfyUI PNG metadata guide](https://www.numonic.ai/blog/comfyui-png-metadata-chunks-workflow-parameters)

### mflux Metadata Export

mflux supports `--metadata` flag to write generation params to a sidecar JSON. Combine with `--seed` for hard reproducibility:

```bash
mflux-generate \
  --model dev \
  --prompt "your prompt" \
  --seed 42 \
  --steps 25 \
  --width 1024 --height 1024 \
  -q 8 \
  --metadata \
  --output ./output/run-001.png
```

The `--metadata` output includes the full resolved config. Commit the `.json` sidecar alongside the PNG for versionable records.

### LoRA & Style Library Management

- **ComfyUI-Lora-Manager** extension: central gallery with preview images, metadata, recipe management, one-click workflow injection. The closest thing to a LoRA "package manager".
- **Chaining LoRAs**: `Load LoRA` nodes chain in series; each with its own scale (0.0–1.5). Community convention: primary style LoRA at 1.0, accent LoRA at 0.4–0.6.
- **Realtime LoRA training** (`ComfyUI-Realtime-Lora`): train a concept LoRA from a few images without leaving ComfyUI. Supports FLUX.1, Z-Image, FLUX Klein, SDXL, WAN 2.2.
- **Style preset libraries**: Save a "style template" workflow JSON (empty content nodes, fixed sampler/LoRA/model nodes). Parameterize only the prompt. Drag-and-drop into any generation session.

### Seed & Prompt Version Control Pattern

```
project/
  workflows/
    portrait-base.json        # ComfyUI workflow template
    product-shoot.json
  seeds/
    good-seeds.jsonl          # {seed, prompt_hash, output_path, notes}
  loras/
    models.lock.json          # {name, sha256, hf_repo, hf_revision}
  outputs/
    YYYYMMDD-HHMMSS-{seed}/
      image.png               # PNG with embedded workflow
      params.json             # mflux sidecar or ComfyUI prompt JSON
```

---

## Versatile Pipelines by Use Case

### Pipeline 1: Photorealistic Output (Hero Images, Portraits)

```
Prompt (prose) → LLM expand → mflux FLUX.1 dev (8-bit, 25 steps)
                               → if text needed: Ideogram 4.0 instead
                               → ControlNet Canny for composition lock
                               → SeedVR2 upscale to 2K
```

- Tool: mflux CLI or Draw Things
- Model: FLUX.1 dev (8-bit on 64 GB gives FP16-quality results at 15% better speed)
- Steps: 20–25; CFG 3.5–5.0
- ControlNet: use Canny edge from a composition sketch or reference photo
- Upscale: `mflux-generate` with SeedVR2 or Draw Things' built-in upscaler

### Pipeline 2: Fast Iteration / Draft Loop

```
Terse prompt → Z-Image turbo (2–4 steps) → pick winner → refine with Flux dev
```

- Tool: mflux `mflux-generate-z-image-turbo`
- Generate 4–6 variations in <30 s total on M5 Pro
- Move winner seed to Flux.1 dev for final render

### Pipeline 3: Text-Heavy Design (Posters, Labels, UI Mockups)

```
Layout description (JSON structured) → Ideogram 4.0 (mflux or ComfyUI)
  → bounding box control for text placement
  → 2K native output
```

- Ideogram 4.0's structured JSON prompting: pass `{layout: [{text: "...", region: [x,y,w,h]}]}` for precise text placement.
- No post-processing compositing needed for most text scenarios.

### Pipeline 4: Iterative Image Editing (Concept Refinement)

```
Base image → FLUX.1 Kontext dev → edit instruction → evaluate → repeat
```

- ComfyUI native workflow: [docs.comfy.org Kontext tutorial](https://docs.comfy.org/tutorials/flux/flux-1-kontext-dev)
- Multi-step edits with minimal drift: change lighting → adjust outfit → swap background, all without re-prompting from scratch.
- Character consistency: Kontext handles subject identity better than img2img for iterative character work.

### Pipeline 5: Illustration / Artistic Style

```
Base prompt → FLUX.1 dev + style LoRA (scale 0.8–1.2) → optional ControlNet pose/depth
```

- CivitAI and Hugging Face both host FLUX.1 LoRA libraries for illustration styles.
- Multi-LoRA: chain a "line art" LoRA + a "color palette" LoRA at independent scales.
- ComfyUI is strongest here due to LoRA ecosystem maturity.

### Pipeline 6: Product Photography

```
Product photo → Kontext edit (background swap, lighting adjust) 
OR
Product render → FLUX.1 dev + ControlNet (Canny from product outline) → lifestyle background
```

- Combine with Depth Pro (in mflux) for depth-aware compositing.

---

## LLM-in-the-Loop: Prompt Expansion + Vision Critique

### Why This Works on Apple Silicon

At 64 GB, you can run a 20B+ LLM (Qwen2.5-72B-Q4, Llama-3.1-70B-Q4) concurrently with a running image generation pipeline without memory contention. The LLM occupies 36–40 GB; Flux 4-bit occupies ~9 GB — they coexist.

### Prompt Expansion Loop

The pattern: terse creative intent → LLM expands to a 150–250 word generation prompt → pass to image model.

**With Ollama + any OpenAI-compatible API** (Qwen Image, HunyuanImage-3.0 native long-prompt support, or any LLM):

```bash
# Expand a terse prompt with a local LLM
EXPANDED=$(ollama run qwen2.5:32b "You are a generative art prompt writer.
Expand this terse image description into a 200-word Flux-optimized prompt.
Include: lighting, materials, composition, color palette, mood, technical camera params.
Description: $TERSE_PROMPT")

# Feed to mflux
mflux-generate --prompt "$EXPANDED" --seed 42 --model dev -q 8
```

**In the `imagine` wrapper** (this project): the `--enhance` flag already calls a local LLM. Hook it to Qwen2.5 via Ollama for best results on long compositional prompts.

### Vision Critique Loop

Use Qwen2.5-VL (7B via Ollama, runs in ~8 GB) as an automatic critic:

```
Generate image → qwen2.5vl: "What is wrong with this image? List 3 specific issues." 
→ LLM: convert critique to prompt corrections → regenerate
```

```bash
# Run Qwen2.5-VL on a generated image
CRITIQUE=$(ollama run qwen2.5vl:7b "
Analyze this image and identify: 
1. Composition issues
2. Lighting/shadow inconsistencies  
3. Anatomical or structural errors
4. What one prompt change would most improve it?
" --image ./output/run-001.png)

# Feed critique back to expansion LLM
REVISED_PROMPT=$(ollama run qwen2.5:32b "
Original prompt: $ORIGINAL_PROMPT
Critic feedback: $CRITIQUE
Produce a revised prompt that addresses the critique.")

mflux-generate --prompt "$REVISED_PROMPT" --seed 43 --model dev -q 8
```

**Qwen2.5-VL on macOS**: Officially available via Ollama (`ollama pull qwen2.5vl:7b`). The 7B model fits in 8 GB; fully tested on macOS by the community.

**Source**: [Qwen2.5-VL on Ollama](https://ollama.com/library/qwen2.5vl) · [Testing Qwen2.5vl on macOS](https://medium.com/@gabi.preda/testing-qwen2-5vl-7b-for-visual-understanding-with-ollama-on-macos-bd6d997597f4)

### Claude Code + Draw Things (MCP Bridge)

For an agent-driven loop where Claude Code orchestrates generation:

```bash
# Add Draw Things as an MCP server
claude mcp add drawthings -- npx -y mcp-drawthings
```

Claude Code gains four tools: `check_status`, `get_config`, `generate_image`, `transform_image`. The agent can:
1. Expand prompts using its own language capabilities
2. Call `generate_image` via MCP
3. Analyze the result via vision capabilities
4. Iterate

**Source**: [Claude Code + Draw Things guide](https://www.heyuan110.com/posts/ai/2026-02-16-claude-code-draw-things-workflow/)

### Multi-Persona Art Direction

The pattern for the `/art-director` persona (task #12 in this project): a Claude persona with deep knowledge of compositional styles, art history, and generation parameters acts as the human-facing layer — interpreting intent, expanding prompts, critiquing outputs, and refining across turns. The critic-loop above is the mechanical backbone; the art director persona provides the aesthetic judgment layer.

---

## Source Index

| # | Source | URL |
|---|--------|-----|
| 1 | filipstrand/mflux GitHub (official repo, v0.18.0) | https://github.com/filipstrand/mflux |
| 2 | HF FLUX.1-dev model card | https://huggingface.co/black-forest-labs/FLUX.1-dev |
| 3 | HF FLUX.1-Kontext-dev model card | https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev |
| 4 | ComfyUI FLUX.1 Kontext native workflow tutorial | https://docs.comfy.org/tutorials/flux/flux-1-kontext-dev |
| 5 | Draw Things Metal FlashAttention 2.0 (engineering blog) | https://medium.com/engineering-draw-things/metal-flashattention-2-0-pushing-forward-on-device-inference-training-on-apple-silicon-fe8aac1ab23c |
| 6 | InsiderLLM: Stable Diffusion on Mac with MLX | https://insiderllm.com/guides/stable-diffusion-mac-mlx/ |
| 7 | Mac Mini M4: ComfyUI vs Draw Things benchmark | https://www.heyuan110.com/posts/ai/2026-02-15-mac-mini-local-image-generation/ |
| 8 | Claude Code + Draw Things MCP workflow | https://www.heyuan110.com/posts/ai/2026-02-16-claude-code-draw-things-workflow/ |
| 9 | argmaxinc/DiffusionKit GitHub | https://github.com/argmaxinc/DiffusionKit |
| 10 | Numonic: ComfyUI PNG metadata chunks explained | https://www.numonic.ai/blog/comfyui-png-metadata-chunks-workflow-parameters |
| 11 | Ideogram 4.0 open-weight launch (AlternativeTo) | https://alternativeto.net/news/2026/6/ideogram-4-0-launches-with-2k-resolution-and-top-open-weight-ranking/ |
| 12 | MindStudio: Ideogram 4.0 analysis | https://www.mindstudio.ai/blog/ideogram-4-open-weight-image-model-fine-tune |
| 13 | WillItRunAI: Stable Diffusion vs Flux 2026 | https://willitrunai.com/blog/stable-diffusion-vs-flux-2026 |
| 14 | AiPhotoLabs: Flux vs SD3.5 performance comparison | https://aiphotolabs.com/compare/flux-vs-stable-diffusion-35-complete-2025-performance-comparison/ |
| 15 | RunComfy: ComfyUI-MLX nodes guide | https://www.runcomfy.com/comfyui-nodes/ComfyUI-MLX |
| 16 | Qwen2.5-VL on Ollama | https://ollama.com/library/qwen2.5vl |
| 17 | Testing Qwen2.5vl on macOS (Medium) | https://medium.com/@gabi.preda/testing-qwen2-5vl-7b-for-visual-understanding-with-ollama-on-macos-bd6d997597f4 |
| 18 | Apple ML Research: LLMs with MLX and M5 Neural Accelerators | https://machinelearning.apple.com/research/exploring-llms-mlx-m5 |
| 19 | mflux PyPI page | https://pypi.org/project/mflux/ |
| 20 | ComfyUI-Lora-Manager GitHub | https://github.com/willmiao/ComfyUI-Lora-Manager |
