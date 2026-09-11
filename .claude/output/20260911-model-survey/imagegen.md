# Local text-to-image models on Apple Silicon, Sept 2026 survey

Scope: models runnable $0/offline on an M5 Pro 64GB via mflux (MLX Flux) or
MLX-diffusers, benchmarked against the suite's current default, Qwen-Image
(20B, via mflux), for UI-mockup/concept-art/text-rendering use. Quality over
speed is the suite's stated priority (schnell-class fast variants already
rejected).

## Candidates found

### Qwen-Image-2.0 (7B), released 2026-02-10, Alibaba
- **Size/footprint:** 7B params, down from 20B in the original Qwen-Image.
  A lighter architecture, not heavier. Native 2048x2048 output, 1000-token
  prompt support.
- **Apple Silicon runtime:** no mflux/MLX port found in this search. MLX
  community quantizations exist for **Qwen-Image-2512** (a separate,
  differently-numbered release: `mlx-community/Qwen-Image-2512-4bit` and
  `-8bit` on Hugging Face, described as a ~57B-parameter Flux-style MMDiT
  model), plus `mlx-gen` (an mflux fork) with "Qwen Image Edit 2509/2511
  routing and parity fixes." Search results did not confirm whether
  "Qwen-Image-2.0" (7B, Feb 2026) and "Qwen-Image-2512" (57B, MLX-ported) are
  the same lineage under different names, or two distinct Alibaba releases.
  This needs a direct check against the mlx-community / Qwen repos before
  acting on it.
- **Text rendering vs current Qwen-Image:** if 2.0 is confirmed, vendor
  claims cite a DPG-Bench score of 88.32 vs FLUX.1's 83.84, "professional
  typography," and native 2K. That is a plausible upgrade on the exact
  dimension the suite cares about most, but unconfirmed by independent
  benchmark.
- **UI-mockup fidelity:** the same typography strength should transfer
  (infographics, PPT-style slides, posters are cited explicitly by the
  vendor).
- **Verdict:** interesting but underverified. The MLX runtime path is the
  open question, not the model quality.

### Qwen-Image-2512 (~57B), MLX-community quantized
- **Size/footprint:** ~57B, MMDiT (Flux-style) architecture. 4-bit and 8-bit
  MLX quantizations are published (`mlx-community/Qwen-Image-2512-{4,8}bit`).
- **Apple Silicon runtime:** confirmed MLX-native (mlx-community official
  quant). `mlx-gen` (mflux fork) explicitly supports Qwen Image Edit
  2509/2511 routing.
- **Footprint on 64GB:** at ~57B params, even 4-bit lands in the 25-30GB+
  range for weights alone. Large but plausible on 64GB unified memory,
  similar order to Flux.dev/Flux2 already registered.
- **Text/UI verdict:** larger than the current 20B Qwen-Image. If it is a
  genuine successor rather than a differently-licensed rebrand, the extra
  capacity plus the same typography-first design plausibly beats the
  incumbent. The runtime path is through `mlx-gen`, a fork of mflux, not
  mflux itself, so this is an integration change, not a drop-in swap.

### FLUX.2 (Black Forest Labs), dev/pro/Klein family
- **FLUX.2-dev:** ~32.2B params. FP16 needs ~70GB; MLX 4-bit quant fits
  ~17GB. mflux 0.17.5 officially supports the FLUX.2 Klein family; separate
  from-scratch MLX ports exist (`mlx-flux2`, `flux-2-swift-mlx`) for the
  broader FLUX.2 line. On an M5, MLX Flux-dev-4bit generation is reported
  as more than 3.8x faster than on M4.
- **FLUX.2 Klein (4B/9B):** a distilled, fast sub-family. Klein-4B does
  512px in about 5 to 6 seconds on an M3 Max 36GB; Klein-9B needs about
  29GB. This is speed-optimized, the opposite of what the suite wants
  (schnell was already rejected on the same grounds), so Klein is not a
  contender. Only FLUX.2-dev (32B, quality tier) is comparable to
  Qwen-Image.
- **Text rendering vs Qwen-Image:** three independent 2026 comparison posts
  (BentoML, LocalAIMaster, Botmonster) agree, and this matches the suite's
  own stated reasoning for picking Qwen-Image: Qwen-Image wins on in-image
  text rendering; FLUX wins on photorealism and prompt adherence.
  FLUX.2-dev is a strict upgrade over the FLUX.dev/Flux2 already registered
  in the suite, but not a text-rendering win over Qwen-Image.
- **UI-mockup fidelity:** FLUX's edge is photorealistic composition, not
  legible baked-in labels or text, the opposite of what UI mockups need.
- **Verdict:** worth upgrading the registered Flux2 slot to FLUX.2-dev
  proper (mflux 0.17.5 already supports the Klein family; dev support
  should be checked directly against the mflux changelog), but it does not
  challenge Qwen-Image as default.

### HunyuanImage 3.0 (Tencent), released 2026-01-26
- **Size/footprint:** 80B total, 13B active (MoE, autoregressive unified
  gen/edit/understanding model), described as the world's largest
  open-source image generation model. Third-party benchmarks recommend it
  for 24GB+ VRAM setups, but that is a CUDA/VRAM framing, not Apple Silicon.
- **Apple Silicon runtime:** no MLX or mflux port surfaced in search. Given
  the MoE plus autoregressive architecture, very different from the
  Flux-style diffusion transformer that mflux/MLX-diffusers are built
  around, a port is nontrivial and none appears to exist yet.
- **Verdict:** not currently runnable on this machine. Worth a watch-later,
  not an action item.

### SD 3.5 Large
Described in 2026 roundups as a reliable all-rounder with a large
community, but no specific claim of beating Qwen-Image on text rendering or
UI fidelity surfaced. Treated here as a known incumbent-class model, not a
new contender: nothing found suggests it displaces the current default.

### Krea 2 / Ideogram 4.0 (mentioned in passing)
One roundup names these as the two strongest local image models to arrive
in 2026: Krea 2 for photorealism and speed, Ideogram 4.0 for in-image text
and typography. Both carry real caveats: Ideogram has historically been a
hosted/API product, not an open-weights local release, and no
MLX/mflux/Apple-Silicon runtime evidence turned up for either in this
search. These need a dedicated licensing and weights-availability check
before being treated as real local candidates. They are mentioned here
only because independent sources named them as the current typography
leaders, which is directly relevant to the suite's UI-mockup use case.

### Sana, AuraFlow, SD-next
No 2026-specific update or Apple-Silicon-MLX evidence surfaced for these in
this search pass. Not included as active candidates.

## Ranked shortlist

1. **No swap of the default is warranted yet.** Every model found that
   plausibly beats Qwen-Image on text rendering (Qwen-Image-2.0, Ideogram
   4.0) has an unconfirmed or absent Apple-Silicon runtime path in this
   research pass. The gate is not model quality, it is whether it actually
   runs on this machine via mflux/MLX today.
2. **Qwen-Image-2512 (mlx-community, ~57B, via `mlx-gen`)** is the most
   concrete near-term upgrade candidate: confirmed MLX weights exist today,
   same typography-first lineage as the incumbent, larger capacity. This
   needs a scoped follow-up: confirm licensing and relationship to the
   current registered Qwen-Image, test-run via `mlx-gen` (a fork of mflux,
   an integration change, not config-only), and measure memory and time
   cost on this machine before registering.
3. **FLUX.2-dev (32B)** is a reasonable upgrade to the registered Flux2
   slot (mflux already supports the FLUX.2 family), but should stay a
   photorealism/prompt-adherence option, not challenge Qwen-Image as the
   UI-mockup default. Every independent source agrees text rendering is
   Qwen's strength, not Flux's.
4. **HunyuanImage 3.0, Qwen-Image-2.0 (7B), Ideogram 4.0, Krea 2** are
   watch-later items. Each has a real signal in its favor (SOTA typography
   claims, or "strongest local model" mentions) but no confirmed, evidenced
   MLX/mflux runtime path as of this search. Re-check when mflux/
   mlx-community changelogs mention them directly, rather than acting on
   vendor-blog claims alone.

**Bottom line:** Qwen-Image remains the right quality-first default today.
The one concrete, actionable next step if this suite wants to chase a real
upgrade is verifying and trialing Qwen-Image-2512 via `mlx-gen`, not a
model-family swap.

## Search coverage note

This was a fixed-budget web-search pass (no browsing of primary repos or
changelogs), so figures above are quoted from secondary sources (vendor
blogs, aggregator roundups, HF model cards) and are flagged "unconfirmed"
wherever independent verification would need a direct read of the
mflux/mlx-community source. Treat parameter counts and benchmark scores as
directionally useful, not load-bearing for a purchase or registration
decision without a follow-up direct check.
