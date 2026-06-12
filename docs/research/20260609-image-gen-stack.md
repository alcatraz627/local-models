# Local Image Generation Stack Research
<!-- sessions: local-models-imggen@2026-06-09 -->

> **Goal:** A reusable, version-controllable image generation subsystem on
> Apple Silicon — iterating on tone/style via prompts/presets/workflows, zero
> idle footprint, swappable models, no model fine-tuning.

---

## 1. Hardware Context

| Machine | Chip | GPU cores | Unified RAM | Role |
|---------|------|-----------|-------------|------|
| A (primary) | M5 Pro | 20 | 64 GB | Dev workstation — protect from idle overhead |
| B (LAN, idle) | M4 Pro | — | 24 GB | Candidate offload target |

---

## 2. Tool Comparison

### 2.1 Draw Things (native Mac app)

**What it is:** Free App Store app (SwiftUI + Metal FlashAttention) — the most
Apple-native image generation surface that exists. Everything is Metal-optimized;
no Python stack, no server process.

**Performance (2026):**

| Hardware | Model | Resolution | Time |
|----------|-------|------------|------|
| M4 Pro 24GB | Flux.1 [schnell] | 1024×1024 | ~50s |
| M4 Pro 24GB | Flux.1 [dev] 25 steps | 704×704 | ~6 min |
| M5 Max | Flux.2 [klein] / Z-Image Turbo | 1024×1024 | <1 s (Lightning Draft) |
| M5 Pro (est.) | Flux.1 [dev] 4-bit | 1024×1024 | ~25–35s (3.8× M4 speedup via MLX) |

Draw Things is **~20% faster than ComfyUI** and **~25% faster than mflux** on
Apple Silicon due to Metal FlashAttention v2.5 (uses M5's Neural Accelerators).

**Preset / workflow system:**
Configurations in Draw Things store: model, LoRA(s), ControlNet(s), steps, CFG,
sampler, seeds, negative prompt, resolution — everything in the settings panel.
Save via ••• → Save As. iCloud-syncs across Mac/iPad/iPhone.

**Limitations for "subsystem" goal:**
- Configurations are stored as opaque app-internal blobs — NOT plain JSON files.
- No git-diff-friendly export of presets.
- Workflows are linear (no node graph), so complex multi-pass pipelines are
  cumbersome.
- No CLI / scripting API for automation.

**Idle footprint:**
As a native macOS app it respects app lifecycle. When Draw Things is not
open, footprint is exactly zero — no background daemon, no server process,
no port held open. When open but idle (no generation), it holds ~150–300 MB
of system RAM (UI only, no model in memory until you run a generation).
Model is loaded on first generate and cached in RAM until next launch or
manual model switch. Quitting the app = full cleanup.

---

### 2.2 ComfyUI (node-graph workflow engine)

**What it is:** Python server with a browser-based node editor. Workflows are
stored as **plain JSON files** — the most version-control-friendly format in
this space. Runs locally; also supports LAN serving (`--listen 0.0.0.0`).

**Performance:**
- Roughly **20% slower than Draw Things** on Apple Silicon (MPS backend vs Metal).
- ComfyUI supports an MLX backend via the `Mflux-ComfyUI` custom node, which
  brings near-mflux speed for Flux models with automatic memory cleanup after
  each generation.
- Typical: M4 Pro 24GB → Flux.1 [schnell] at 1024×1024 in ~60–70s without MLX
  nodes; faster with Mflux-ComfyUI node.

**Preset / workflow system — THE STRONGEST in this class:**

Workflows are JSON (~15–500 KB each). Key practices for a reusable subsystem:
1. **Normalize JSON** before committing (sort node IDs, pretty-print, sort keys)
   via a pre-commit hook → clean `git diff`.
2. Store workflow JSONs in a git repo; track tone/style variants as branches or
   tagged versions.
3. `comfyui-workspace-manager` custom node adds in-app version history.
4. Style presets: reusable "sub-workflows" (groups of nodes) can be copy-pasted
   across workflows; community-shared at Civitai and GitHub.
5. ControlNet + IP-Adapter nodes are first-class in ComfyUI:
   `ControlNetLoader` + `IPAdapterModelLoader` → wire into any workflow.
6. Negative prompts, seeds, sampler parameters → nodes with fixed or
   randomized values; pin seed for reproducibility.

**Idle footprint:**
ComfyUI is a **server process** — it holds its Python runtime and any loaded
model in RAM as long as the process is running. Known macOS issue: memory not
always cleaned between renders without `--cache-none`. Mitigation:
- Use `--cache-none` flag (slower per-run but lower idle RAM).
- Kill the process via a shell alias or launchd on-demand launcher when not in
  use. With nothing loaded and `--cache-none`, idle RAM is ~200–400 MB
  (Python runtime only).
- **Zero-idle guarantee**: wrap launch in a script; quit ComfyUI when done.
  A launchd `on-demand` socket activator or a simple shell wrapper achieves this.

**LAN offload:**
ComfyUI supports `--listen 0.0.0.0 --port 8188` on Machine B, browsed from
Machine A. The `ComfyUI_NetDist` custom node also enables distributing workflow
steps across multiple machines on LAN.

---

### 2.3 mflux / MLX-native Flux

**What it is:** Pure MLX Python port of Flux and other models — CLI + Python
API. As of v0.17.5 (May 2026) covers Flux.1 [dev/schnell], Flux.2 [klein/dev],
Z-Image Turbo, FIBO, HiDream, and more.

**Performance:**
- ~25% slower than Draw Things for Flux models.
- ~3.8× faster on M5 vs M4 for Flux-dev-4bit.
- No persistent server process: `mflux-generate` runs, generates, exits.
  **Natural zero-idle footprint** — it IS a CLI command, not a daemon.

**Preset / workflow system:**
All parameters are CLI flags or Python script arguments. A "preset" is a shell
script or Python wrapper with baked-in values:
```bash
mflux-generate \
  --model flux-dev-4bit \
  --prompt "$(cat prompts/editorial-style.txt)" \
  --steps 20 --guidance 3.5 \
  --seed 42 --width 1024 --height 1024
```
Easy to version-control (shell scripts in git). No GUI, no visual node graph.
No native ControlNet or IP-Adapter support in mflux itself — those require
ComfyUI wrappers.

**Best used as:** CLI/scripting backend for automated pipelines, or as the
backend engine for the `Mflux-ComfyUI` custom node inside ComfyUI.

---

### 2.4 Automatic1111 / Forge

**Status on macOS 2026:**
- A1111 master branch broken as of January 2026; requires `dev` branch.
- Forge is faster than A1111 and has memory-efficient attention — but both run
  on MPS (Metal Performance Shaders), not Metal FlashAttention.
- ComfyUI is faster than A1111 on Apple Silicon in most benchmarks.
- Both have higher idle footprint than Draw Things (Python/Gradio web server).
- SDXL and older SD 1.5/2.x models are their strength. Flux support is
  available but not their primary optimization target.

**Verdict:** Do not use. Worse on every axis (performance, stability, idle
footprint) compared to the alternatives on Apple Silicon in 2026.

---

## 3. Model Survey

| Model | Disk (fp16/bf16) | Disk (4-bit quant) | Comfortable RAM | M4 Pro 24GB speed | M5 Pro 64GB speed (est.) |
|-------|------------------|--------------------|-----------------|-------------------|--------------------------|
| SD 1.5 | ~2 GB | ~1 GB | 8 GB | 5–10 s | 3–5 s |
| SDXL | ~6.5 GB | ~3.5 GB | 10–12 GB | 20–35 s | 12–20 s |
| SD 3.5 Medium | ~5.1 GB (fp16) | — | 8–10 GB | ~40–60 s | ~20–35 s |
| SD 3.5 Large | ~15 GB (fp16) | ~8 GB | 18–24 GB | slow | ~60–90 s |
| Flux.1 [schnell] | ~24 GB (bf16) | ~6.7 GB (Q4) | 12 GB (Q4) | ~50 s (Q5-bit) | ~15–25 s |
| Flux.1 [dev] | ~24 GB (bf16) | ~6.7 GB (Q4) | 16 GB (Q4) | ~6 min (25 steps) | ~90–120 s |
| Flux.2 [klein] 4B | ~4 GB | ~2 GB | 8 GB | ~20–30 s | ~8–15 s |
| Flux.2 [dev] 9B | ~9 GB | ~5 GB | 12 GB | ~60–90 s | ~25–40 s |
| Z-Image Turbo | ~8 GB | ~4 GB | 10 GB | ~40–60 s | ~15–25 s |

**Notes:**
- "Comfortable RAM" = unified RAM needed for smooth generation without heavy
  swapping. On Apple Silicon, unified memory means CPU and GPU share the pool.
- M4 Pro 24GB runs Flux.1 at Q5/Q6 quantization (near-lossless quality).
- M5 Pro 64GB can run Flux.1 at full bf16 if desired; Q4/Q5 is ~2–3× faster.
- Flux.2 [klein] (4B parameters, distilled) is the practical 2026 daily-driver:
  fast, small footprint, strong quality. Supersedes Flux.1 [schnell] in the
  "fast-iteration" slot.
- SD 3.5 Medium is a solid SDXL-class alternative with better prompt adherence;
  5.1 GB on disk.

---

## 4. The "Style / Preset Subsystem"

The goal is analogous to hooks/rules: encode tone, style, procedure once →
reuse without manual nudging each session.

### 4.1 Layers of customization (no fine-tuning required)

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 1: Prompt Templates                                           │
│  Plain text files, git-tracked. Parameterized with placeholders.     │
│  e.g. prompts/editorial-portrait.txt, prompts/technical-diagram.txt │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 2: Negative Prompts                                           │
│  Companion .neg.txt files or a shared negatives/common.txt           │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 3: Workflow JSON (ComfyUI)                                    │
│  Encodes: model, sampler, steps, CFG, resolution, seed, LoRA weight  │
│  git-tracked; diff-friendly after JSON normalization pre-commit hook  │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 4: LoRA conditioning (pre-trained, no training required)      │
│  Community LoRAs from Civitai wired into workflow at a weight.       │
│  e.g. a "cinematic lighting" LoRA at weight 0.7                      │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 5: IP-Adapter / ControlNet (style reference image)            │
│  Feed a reference image → soft style transfer without fine-tuning.   │
│  ControlNet: structure/pose/depth conditioning.                       │
│  IP-Adapter: loose style reference (FLUX.1-dev-IP-Adapter on HF).   │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 LoRA-as-conditioning vs LoRA-training distinction

**Using a pre-trained LoRA (IN SCOPE):**
Download a community-trained `.safetensors` LoRA from Civitai or Hugging Face.
Load it in ComfyUI via `LoraLoader` node at a strength of 0.5–1.0. The LoRA
modifies the model's attention weights at inference time. No GPU training
required. Disk cost: 50 MB – 800 MB per LoRA. This is style conditioning.

**Training a LoRA (OUT OF SCOPE per user constraints):**
Requires 50–200+ reference images, a GPU training run (hours to days), and
hyperparameter tuning. This is fine-tuning-adjacent and explicitly excluded.

The distinction: a pre-trained LoRA is a **read-only conditioning artifact**
that you drop into a workflow node — same mental model as a ControlNet model
or an IP-Adapter checkpoint.

### 4.3 Recommended repository structure

```
image-gen/
├── workflows/               # ComfyUI JSON workflows (git-tracked)
│   ├── editorial-portrait.json
│   ├── technical-flat.json
│   └── _base-flux-schnell.json   # shared base workflow
├── prompts/                 # Prompt templates
│   ├── editorial-portrait.txt
│   ├── technical-flat.txt
│   └── negatives/
│       └── common.neg.txt
├── loras/                   # LoRA .safetensors (gitignored, path-referenced)
│   └── README.md            # links to Civitai/HF sources + weights used
├── controlnets/             # ControlNet models (gitignored, path-referenced)
├── seeds/                   # Pinned seed values for reproducible hero images
│   └── editorial-v3.seed.txt
├── .hooks/
│   └── pre-commit           # JSON normalization for clean workflow diffs
└── README.md
```

Model binary files (LoRAs, ControlNets) are gitignored; only their source URLs
and the weights used in workflows are committed. The workflow JSONs reference
them by filename.

---

## 5. Machine Assignment

### 5.1 Does Flux fit on Machine B (M4 Pro 24 GB)?

Yes. Flux.1 [schnell/dev] at Q5-bit quantization uses ~10–14 GB RAM, comfortably
within 24 GB. Flux.2 [klein] 4B fits at fp16 (~4 GB). Machine B can host Flux
generation with room for the OS.

Generation times on M4 Pro 24GB:
- Flux.1 [schnell] 1024×1024: ~50 s
- Flux.2 [klein] 1024×1024: ~20–30 s

### 5.2 Recommended split

```
┌──────────────────────────────────────────────────────┐
│  Machine A (M5 Pro 64GB) — primary dev workstation   │
│                                                       │
│  Image gen: ON-DEMAND LAUNCH only                     │
│  Use Draw Things (GUI, zero idle) for interactive     │
│  iteration and quick test renders.                    │
│  M5 Pro 64GB means even full bf16 Flux.1 fits easily. │
│  Expected: ~20–35s for Flux.1 schnell at 1024×1024.  │
│                                                       │
│  Zero idle: quit Draw Things when done. Or run mflux  │
│  from CLI (exits naturally after generation).         │
└──────────────────────────────────────────────────────┘
         │  heavy batch / overnight runs
         ▼
┌──────────────────────────────────────────────────────┐
│  Machine B (M4 Pro 24GB) — LAN worker                │
│                                                       │
│  ComfyUI running with --listen 0.0.0.0                │
│  Only launched when actively batching.               │
│  Browse ComfyUI UI from Machine A via LAN IP.        │
│  Machine A's dev performance unaffected.             │
│  Flux.1 at Q5: ~50s/image. Good for batch overnight. │
└──────────────────────────────────────────────────────┘
```

**Recommended day-to-day flow:**
- Interactive iteration → Draw Things on Machine A (on-demand, quit when done).
- Batch generation / complex workflows → ComfyUI on Machine B over LAN.
- Scripted pipelines → mflux CLI on either machine (exits after generation).

---

## 6. Recommendation

### Primary tool: **ComfyUI** (for the subsystem goal)

Rationale: The "reusable subsystem" requirement maps directly to ComfyUI's
JSON workflow model. Every workflow is a plain text file that can be:
- version-controlled in git
- diff'd (with JSON normalization pre-commit hook)
- branched for style variants
- shared, imported, exported
- parameterized with prompt-template node inputs

No other tool in this space gives you git-trackable, diff-friendly, shareable
workflow artifacts. Draw Things' Configuration system is app-internal and opaque.
mflux/CLI has no visual composition layer.

### Idle footprint plan for ComfyUI

ComfyUI is a server — it has footprint when running. The mitigation:

```bash
# ~/.local/bin/comfy-start
#!/bin/zsh
cd ~/path/to/ComfyUI
python main.py --listen 0.0.0.0 --port 8188 \
  --cache-none \          # releases model RAM between jobs
  --fp16-vae              # reduces peak RAM during VAE decode

# ~/.local/bin/comfy-stop
#!/bin/zsh
pkill -f "python main.py"
```

When not generating: launch on-demand, kill when done. No background daemon,
no always-resident service.

On Machine B (LAN), this is even cleaner — it's dedicated/idle anyway.

### Starter model: **Flux.2 [klein] 9B** (or Flux.1 [schnell] Q5)

- **Flux.2 [klein] 9B:** ~5 GB disk (quantized), ~12 GB RAM, ~25–40s/image on
  M5 Pro, strong quality-to-speed ratio. The 2026 daily-driver.
- **Flux.1 [schnell] Q5:** ~8 GB disk, ~10 GB RAM, ~20–35s/image on M5 Pro,
  well-understood by the community, vast LoRA library on Civitai.

Start with Flux.1 [schnell] for LoRA/community-resource availability, migrate to
Flux.2 [klein] when the LoRA ecosystem matures — model swappability is built
into ComfyUI via the `CheckpointLoaderSimple` node.

### Conditioning stack (no fine-tuning)

For style consistency and tone control:
1. **Prompt templates** (git-tracked `.txt` files, slot into ComfyUI text nodes).
2. **Pre-trained style LoRAs** from Civitai at 0.6–0.8 weight in `LoraLoader`.
3. **IP-Adapter** (`InstantX/FLUX.1-dev-IP-Adapter` on Hugging Face) for
   image-reference style transfer — wire in a reference image, tune strength.
4. **ControlNet** for structural conditioning (pose, depth, edge) when
   consistent layout matters.
5. **Seed pinning** in workflow JSON for reproducible hero images.

None of these require GPU training. All are drop-in artifacts with version-pinned
references tracked in the repo README.

---

## 7. Summary Table

| Criterion | Draw Things | ComfyUI | mflux CLI | A1111/Forge |
|-----------|-------------|---------|-----------|-------------|
| Apple Silicon perf | Best (Metal FA) | Good (−20%) | Good (−25%) | Worst |
| Idle footprint | Near-zero (GUI app) | Needs mgmt (server) | Zero (CLI exits) | Bad (Gradio server) |
| Preset/workflow versioning | Opaque (iCloud blob) | **Excellent (JSON+git)** | Script-level | Mediocre |
| LoRA / ControlNet / IP-Adapter | Yes | **Best (node graph)** | LoRA only | Yes |
| Swappable models | Yes | **Best (per-node)** | Yes (CLI flag) | Yes |
| Scripting/automation | No | Good (API) | **Best (CLI/Python)** | Limited |
| Setup friction | **Lowest** | Medium | Low | High |
| Recommended for this goal | Secondary (interactive) | **Primary** | Backend / batch | Skip |

---

## Sources

- [Mac Mini M4 AI Image Generation: ComfyUI vs Draw Things (50s Flux Benchmark)](https://www.heyuan110.com/posts/ai/2026-02-15-mac-mini-local-image-generation/)
- [Draw Things Ultimate Guide: Local AI Image Generation on Mac](https://www.heyuan110.com/posts/ai/2026-02-15-draw-things-ultimate-guide/)
- [Metal FlashAttention v2.5 w/ Neural Accelerators: delivering breakthrough performance on the Apple M5 chip](https://releases.drawthings.ai/p/metal-flashattention-v25-w-neural)
- [Introducing Lightning Draft: interactive image generation on M5 Max](https://releases.drawthings.ai/p/introducing-lightning-draft-interactive)
- [GitHub — filipstrand/mflux: MLX native implementations of state-of-the-art generative image models](https://github.com/filipstrand/mflux)
- [ComfyUI Review 2026: The most powerful node-based Stable Diffusion workflow engine](https://visionstack.visionsparksolutions.com/reviews/comfyui/)
- [ComfyUI Git: Version Control and Repository Management Guide](https://www.alexanderharte.com/comfyui-git-version-control-guide/)
- [Configuration Basics — Draw Things WIKI](https://wiki.drawthings.ai/wiki/Configuration_Basics)
- [GitHub — 11cafe/comfyui-workspace-manager](https://github.com/11cafe/comfyui-workspace-manager)
- [Dynamic VRAM in ComfyUI: Saving Local Models from RAMmageddon](https://blog.comfy.org/p/dynamic-vram-in-comfyui-saving-local)
- [How to Access ComfyUI from Local Network](https://comfyui-wiki.com/en/faq/how-to-access-comfyui-on-lan)
- [GitHub — city96/ComfyUI_NetDist: Run ComfyUI workflows on multiple machines](https://github.com/city96/ComfyUI_NetDist)
- [Run FLUX.1 Locally in 2026: VRAM Needs + 5-Minute Setup](https://localaimaster.com/blog/flux-local-image-generation)
- [GitHub — raysers/Mflux-ComfyUI: Quick Mflux on ComfyUI](https://github.com/raysers/Mflux-ComfyUI)
- [InstantX/FLUX.1-dev-IP-Adapter — Hugging Face](https://huggingface.co/InstantX/FLUX.1-dev-IP-Adapter)
- [Stable Diffusion 3.5 Medium VRAM Requirements — WillItRunAI](https://willitrunai.com/image-models/sd-3-5-medium)
- [Flux + ComfyUI on Apple Silicon Macs — 2024 (Medium)](https://medium.com/@tchpnk/flux-comfyui-on-apple-silicon-with-hardware-acceleration-2024-4d44ed437179)
- [M4M and M3U for image generation speed — MacRumors Forums](https://forums.macrumors.com/threads/m4m-and-m3u-for-image-generation-speed-sd-flux-etc.2454524/)
- [Exploring LLMs with MLX and the Neural Accelerators in the M5 GPU — Apple ML Research](https://machinelearning.apple.com/research/exploring-llms-mlx-m5)
