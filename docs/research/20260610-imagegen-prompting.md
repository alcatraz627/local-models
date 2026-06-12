# Image Generation Prompting: Best Practices for Flux, SDXL, and Qwen-Image

<!-- sessions: imagegen-prompting@2026-06-10 -->

> **Scope:** Local generation on Apple Silicon via mflux. Models: Flux schnell, Flux.2 klein,
> Flux dev, Qwen-Image. LLM-assisted prompt expansion via gemma4.
> **Companion research:** `20260609-image-gen-stack.md`, `20260609-runtime-orchestration.md`

---

## 1. Prompt Anatomy: The Universal Structure

Regardless of model, a well-formed image prompt answers these questions in order:

```
┌────────────────────────────────────────────────────────────────────┐
│  1. SUBJECT      — who/what, with specific distinguishing details  │
│  2. ACTION/STATE — what they're doing, or how they exist           │
│  3. ENVIRONMENT  — setting, context, world around the subject      │
│  4. LIGHTING     — source, direction, quality, color temperature   │
│  5. LENS/CAMERA  — device, focal length, aperture, framing         │
│  6. STYLE/MEDIUM — artistic movement, film stock, reference        │
│  7. MOOD         — atmosphere, emotional tone                      │
│  8. QUALITY TAGS — model-specific detail boosters (if needed)      │
└────────────────────────────────────────────────────────────────────┘
```

**Front-load the subject.** Both CLIP and T5 encode earlier tokens with more weight. If your
subject is buried after stylistic preamble, prompt adherence degrades.

### Concrete slot vocabulary

| Slot | High-impact terms |
|------|-------------------|
| **Lighting** | golden hour, Rembrandt lighting, rim light, soft diffused overcast, hard directional sunlight, neon underlight, three-point studio, chiaroscuro |
| **Camera** | shot on Sony A7IV 35mm f/1.4, Hasselblad X2D 45mm, Canon EOS R5, 85mm portrait lens, wide-angle 16mm, anamorphic, macro |
| **Film stock** | Kodak Portra 400 (warm skin), Fuji Velvia 50 (vivid landscape), Ilford HP5 (B&W), CineStill 800T (tungsten night) |
| **Composition** | rule of thirds, centered symmetrical, Dutch angle, extreme low angle, bird's-eye view, foreground bokeh, layered depth |
| **Style** | photorealism, impressionist oil painting, ukiyo-e woodblock, brutalist architecture render, product photography, editorial fashion |

---

## 2. Model-Specific Prompting Differences

### 2a. Flux (dev / schnell / klein) — Natural Language Prose

Flux uses a **T5-XXL encoder** that processes language like reading a description, not like
parsing a tag list. This means:

- **Write in sentences.** "A weathered fisherman mending nets on a fog-shrouded Norwegian dock"
  outperforms "fisherman, dock, fog, nets, weathered, Norway."
- **No parenthetical weights.** `(beautiful:1.4)` is ignored entirely. Use language: "with
  particular attention to the texture of her hair" or simply place the element earlier.
- **No `--ar`, `--v` flags.** Midjourney parameters appear as literal text artifacts.
- **Detail boosters are usually counterproductive.** Skip "masterpiece, best quality, 4k,
  intricate details" — Flux doesn't need them and they can dilute specificity.
- **Talk to it like you'd describe a photo to a friend.** That's the mental model that works.

**Optimal length:** 30–80 words for most images. Flux supports up to 512 T5 tokens (≈ 32k
chars for Flux 2 Pro), but 80+ words rarely helps and can cause competing directives.

**Guidance scale (CFG):**
- **Flux dev:** 3.0–3.5 is the photorealistic sweet spot; 3.5–6 for stylized/painted work.
- **Flux schnell:** Distilled model; operates best with CFG ≈ 1 and Distilled CFG Scale ≈ 3.5
  for photorealism, 3.5–6 for illustration.
- Higher guidance improves prompt adherence; lower guidance yields more natural textures at the
  cost of precision.

**Steps:**
- schnell: 2–4 steps (use for rapid iteration; production-quality at step 4)
- dev: 24–32 steps for quality (start at 28 if unsure)

### 2b. SDXL — Tag/Keyword Style

SDXL was trained on shorter, comma-separated keyword prompts and responds accordingly:

- Use **comma-delimited tag lists** rather than full sentences.
- Quality tags **do** help: `masterpiece, best quality, highly detailed, 8k, ultra realistic`
- Negative prompts are **highly effective** (unlike Flux). Use them aggressively (see §5).
- Guidance range: 6–12 (vs Flux's 3–5).
- Steps: ~30 for the base; add refiner pass for detail.
- Weighting syntax works: `(subject:1.3)` boosts, `[element:0.8]` de-emphasizes.
- SDXL dual-encoder (base + refiner) architecture rewards style-layered prompting.

**SDXL weakness vs Flux:** Notorious for "spaghetti fingers" and anatomical errors. Flux's 12B
params handle hands far better by default; on SDXL, use the negative prompt and anatomy helpers.

### 2c. Flux schnell (guidance-distilled) — specific notes

schnell is distilled from dev: the model "bakes in" guidance at training time, so:

- Standard CFG does almost nothing. Set to 1.
- Negative prompts at CFG=1 are silently ignored.
- Use **Distilled CFG Scale** (step-level guidance in mflux: `--guidance` flag) for control.
- At 2–4 steps, schnell is suitable for rapid ideation. For a final asset, switch to dev.
- Prompt at schnell = still prose, still no tags, but keep it shorter (≤50 words) since each
  step does heavier lifting and long prompts cause drift.

### 2d. Qwen-Image — Text Rendering Specialist

Qwen-Image's primary edge is **legible text in generated images** (posters, infographics, signs,
UI mockups). Prompting strategy differs from pure Flux:

- **Quote all text content in double quotes** inside the prompt. Each text block gets its own
  quoted segment: `a poster with "GRAND OPENING" in large bold letters at the top and "Saturday
  June 14" in smaller text below`
- **Specify font style, weight, and hierarchy explicitly:**
  - Use "clean geometric sans" or "neutral grotesk" — avoid serif for body text, avoid
    script/handwriting for anything beyond a single word
  - Say "header very large, subheader medium, body small" (weight language beats point sizes)
  - Request "ample line spacing" and "generous tracking"
- **Structure prompt spatially:** Name each block's position — "large centered header at top,"
  "two-line body at bottom." Structure matters more than flowery language.
- **High contrast is mandatory for legibility:** Ask for "high contrast," "dark overlay under
  text," or "light text on dark solid background."
- **Keep lines short:** 1–3 words succeed ~70%; full sentences drop below ~40% accuracy.
- **Guidance scale:** 4.0–5.0 (lean toward 5 for text-heavy work). More steps (35–45) also
  improve letter formation.
- **Disable built-in prompt enhancer** when you've already carefully structured the layout — the
  enhancer reintroduces decorative flourishes that hurt text clarity.
- CJK text: use "bold sans CJK" with "thick strokes," keep at header size only.

---

## 3. Negative Prompts: When They Help vs When They're Ignored

```
┌──────────────────────────────────────────────────────────────────┐
│  Model          │ Negative Prompts │ Why                         │
├──────────────────────────────────────────────────────────────────┤
│  SDXL           │  EFFECTIVE       │ Full CFG, trained with them │
│  Flux dev       │  IGNORED (stock) │ CFG-distilled architecture  │
│  Flux schnell   │  IGNORED         │ Distilled, CFG=1            │
│  Flux dev+DT    │  PARTIAL         │ Dynamic Thresholding hack   │
│  Qwen-Image     │  Limited         │ Use positive framing        │
└──────────────────────────────────────────────────────────────────┘
```

### For SDXL — the standard negative template

```
deformed, distorted, disfigured, poorly drawn, bad anatomy, wrong anatomy,
extra limb, missing limb, floating limbs, mutated hands, extra fingers,
fused fingers, long neck, watermark, text, signature, blurry, low quality,
jpeg artifacts, oversaturated, ugly, ugly face
```

Keep it targeted: a 30-word focused negative beats a 100-word kitchen sink. For hands
specifically: `extra fingers, fused fingers, malformed hands` is the minimal effective set.

### For Flux — use positive framing instead

Instead of negative prompts, describe what you want:

| Avoid | Use instead |
|-------|-------------|
| `blurry background` | `sharp subject, clean background` |
| `bad hands, extra fingers` | `five fingers clearly visible, natural hand proportions` |
| `text, watermarks` | `no visible text` (works in positive) |
| `low quality` | `crisp detail, high resolution` |
| `white background` (Flux dev) | `neutral backdrop, soft light, high contrast` |

### Dynamic Thresholding workaround (ComfyUI / A1111 only)

Community tool: install `sd-dynamic-thresholding`, add `DynamicThresholdingFull` node, connect
FLUX model → node → KSampler. Settings: CFG 3–7, Interpolate Phi 0.7–0.9, Mode "Half Cosine Up."
Not applicable to mflux CLI directly, but relevant if switching to ComfyUI for a specific task.

---

## 4. Token Budgets and Encoder Architecture

### Flux dual-encoder system

Flux dev and dev-derived models use two text encoders with different roles:

```
┌─────────────────────────────────────────────────────────────────────┐
│  CLIP L/14         │ 77 tokens max  │ Visual-semantic composition   │
│                    │                │ Overall framing, gestalt feel │
├─────────────────────────────────────────────────────────────────────┤
│  T5-v1.1-XXL       │ 512 tokens max │ Rich semantic context         │
│                    │ (256 schnell)  │ Spatial relationships, detail │
└─────────────────────────────────────────────────────────────────────┘
```

**Practical implication:** Keep your primary visual subject and style in the first ~70 tokens
(fits CLIP). Extended scene description, stylistic nuance, and context go after. If mflux warns
about CLIP truncation, it's safe to ignore — T5 still processes the full prompt.

To use T5's full capacity in diffusers/ComfyUI: set `max_sequence_length=512`.

**For schnell:** T5 max is 256 tokens. Prompts over ~180 words may be truncated.

### SDXL dual-encoder (CLIP-G + CLIP-L)

Both encoders are CLIP-based with 77-token limits. This is why SDXL benefits from tag prompts:
tags are information-dense within a tight token budget. Long prose wastes tokens on connective
tissue that doesn't survive the clip.

### Prompt weighting and BREAK

- **SDXL / SD1.5:** `(word:1.3)` to boost, `[word:0.8]` to de-emphasize. Keep weights in
  0.7–1.4 range; values beyond 1.5 cause saturation artifacts.
- **BREAK keyword:** Inserts a zero-padding sequence between sections, forcing the model to
  treat them as independent attention chunks. Use to separate distinct scene elements.
  Example: `a cat sitting on a table, warm light BREAK background: marble kitchen, neutral tones`
- **Flux:** No weighting syntax — use natural language emphasis ("particularly focusing on,"
  "with careful attention to") or structural position (earlier = more weight).

---

## 5. LLM-Assisted Prompt Expansion with gemma4

### What makes a good expansion (vs a bad one)

**Good expansions:**
- Add sensory specificity: hair color, clothing texture, light direction, time of day
- Fill compositional slots that the user left vague (lighting, camera angle)
- Preserve the user's core intent and subject exactly
- Stay within the target length (30–80 words for Flux, 40–60 for SDXL tag chains)
- Match the target model's style: prose for Flux, tags for SDXL

**Bad expansions:**
- Redirect the concept ("a dog in a field" → "a wolf in a mystical forest")
- Over-describe until competing directives appear
- Add Midjourney-style flags (`--ar 16:9`) to a Flux target
- Pad with generic quality boilerplate that doesn't survive CLIP tokenization

### System prompt template for gemma4 (Flux target)

```
You are an expert AI image prompt writer. The user provides a short description.
Expand it into a detailed, natural-language prompt suitable for Flux image generation.

Rules:
- Write in flowing descriptive prose (sentences, not comma tags)
- Add: specific lighting, camera/lens details, mood/atmosphere, environmental context
- Do NOT add parenthetical weights like (word:1.4) — Flux ignores them
- Do NOT add negative prompt content or quality tags like "masterpiece"
- Do NOT redirect the subject or concept
- Target 40–70 words
- Return only the prompt text, no explanation

User description: {input}
```

### System prompt template for SDXL target

```
You are an expert Stable Diffusion prompt writer. Expand the user's concept into
an SDXL-optimized comma-separated tag prompt.

Rules:
- Use comma-separated keywords, not full sentences
- Include: subject tags, medium, style, lighting, quality tags (masterpiece, best quality, 8k)
- Quality prefix: "masterpiece, best quality, highly detailed, "
- Camera: "shot on Canon 5D, 85mm lens, shallow depth of field"
- Target 50–80 tokens total
- Return only the positive prompt; no negative prompt

User concept: {input}
```

### Fragment presets for gemma4 to inject

Train gemma4 (or hard-wire in the expansion system prompt) to recognize intent categories and
pull from these reusable fragment sets:

| Intent | Fragment |
|--------|----------|
| Portrait / skin | `natural skin texture, subsurface scattering, pores visible, Kodak Portra 400` |
| Product / commercial | `studio softbox lighting from camera-left, clean shadow, commercial grade` |
| Landscape / nature | `golden hour side-lighting, atmospheric haze, foreground detail, Fuji Velvia 50` |
| Architecture | `architectural photography, tilt-shift lens, geometric precision, neutral overcast` |
| Character / fantasy | `dynamic pose, detailed costume, rim light, concept art, ArtStation quality` |
| Night / neon | `CineStill 800T, neon reflections, bokeh background lights, rain-wet streets` |

---

## 6. Common Failure Modes and Prompt-Level Mitigations

### Extra limbs / anatomical distortion

- **Root cause:** Insufficient compositional specificity.
- **Flux mitigation:** Describe the pose explicitly: "standing with both hands visible, fingers
  relaxed, arms at her sides." Mention the count: "five fingers clearly visible."
- **SDXL mitigation:** Add to negative: `extra limbs, extra fingers, fused fingers, malformed
  hands, bad anatomy, wrong anatomy`. Flux handles this natively 95% better than SDXL.
- **Nuclear option:** Generate without hands in frame (tight portrait crop, hands offscreen).

### Garbled / illegible text in the image

- **Root cause:** All standard diffusion models conflate visual texture with text; Flux is worse
  than Qwen-Image at letter formation.
- **Routing fix:** Use Qwen-Image for any prompt requiring readable text (posters, signs, UI
  mocks). Don't fight Flux for this.
- **If you must use Flux:** Generate without text, add overlay in Photoshop/Pixelmator/GIMP.
- **Qwen-Image:** Quote all text in `"double quotes"`, use sans-serif, limit lines to 1–3 words.

### Duplicate subjects / doubled elements

- **Root cause:** Resolution mismatch (generating at 2× native res causes splits) or vague
  subject count.
- **Mitigation:** Use model-native resolution (Flux: 1024×1024 base). For off-aspect, use
  multiples of 32. Specify count explicitly: "a single lighthouse" not "lighthouse."

### Over-smooth / plastic textures

- **Root cause:** High guidance scale with sparse detail descriptors.
- **Mitigation:** Lower CFG (try 2.5 for Flux dev). Add texture-specific terms: "natural grain,
  subtle noise, film grain, slight imperfection." Specify material directly: "weathered
  concrete" not "wall."

### Conflicting aesthetics / muddy output

- **Root cause:** Too many style references from different domains (e.g., "photorealistic anime
  impressionist oil painting watercolor").
- **Mitigation:** Pick one dominant style and one supporting aesthetic. "Photorealistic, with
  painterly color grading" is coherent. "Photorealistic anime watercolor" is not.

### Prompt drift (output ignores key elements)

- **Root cause:** Key element mentioned too late, or masked by longer early description.
- **Mitigation:** Move the critical element to the very start of the prompt. Fix the seed and
  iterate guidance scale before changing the prompt. For SDXL, use `(element:1.2)`.

### White/flat backgrounds (Flux dev)

- **Root cause:** Flux dev has a known issue with the phrase "white background" producing fuzzy
  outputs.
- **Mitigation:** Use "neutral backdrop, soft light, high contrast" or "off-white seamless
  paper, studio lighting" instead.

---

## 7. Reusable Style Fragments and Preset Library

Save these as named presets in your `imagine` wrapper's registry. Log the model, guidance, and
steps alongside them.

### Portrait presets

```
# Cinematic Portrait
shot on Sony A7IV, 85mm f/1.4, shallow depth of field, warm Rembrandt lighting,
natural skin texture, cinematic color grade, fine detail

# Studio Commercial
neutral seamless backdrop, three-point softbox lighting, crisp shadow,
commercial photography, high contrast, no post-processing artifacts

# Environmental Portrait
subject in natural context, golden hour backlight, environmental storytelling,
Kodak Portra 400, handheld feel
```

### Scene presets

```
# Cinematic Exterior
anamorphic lens, golden hour, atmospheric haze, teal-and-orange grade,
cinematic composition, depth through layers

# Night Urban
CineStill 800T, neon reflections on wet pavement, shallow focus,
bokeh light points, high ISO grain, gritty documentary feel

# Nature/Landscape
Fuji Velvia 50, wide angle 16mm, polarizing filter effect,
foreground interest, layered depth, cloud drama
```

### Quality suffix (Flux — use sparingly)

Only when output is consistently under-detailed:
```
ultra sharp, fine detail, 8K resolution equivalent
```
Do NOT use "masterpiece" or "best quality" with Flux — they're SDXL vocabulary.

---

## 8. Practical Workflow for the imagine CLI

```
┌──────────────────────────────────────────────────────────────────┐
│  Step 1  │ Write a 10-word seed concept                          │
│  Step 2  │ Route: text in image? → Qwen. Otherwise: Flux dev/    │
│          │   schnell based on speed/quality need                 │
│  Step 3  │ LLM expansion (gemma4) → 40-70 word prose prompt      │
│  Step 4  │ Add a preset style fragment if applicable             │
│  Step 5  │ Fix seed, generate 2–4 samples                        │
│  Step 6  │ Iterate ONE variable (guidance, style, or prompt word)│
│  Step 7  │ Document winning prompt + params in preset registry   │
└──────────────────────────────────────────────────────────────────┘
```

**Iteration discipline:** Change one variable per generation batch. Don't simultaneously change
prompt + guidance + steps — you won't know what fixed it.

**Seed management:** Fix seed during prompt refinement. Once satisfied with the prompt, vary the
seed to sample the distribution. A good prompt should produce good images across multiple seeds.

---

## Sources

1. **getimg.ai — FLUX.1 Prompt Guide: Pro Tips and Common Mistakes to Avoid**
   https://getimg.ai/blog/flux-1-prompt-guide-pro-tips-and-common-mistakes-to-avoid

2. **Skywork AI — Flux Prompting Ultimate Guide: FLUX.1 dev & schnell**
   https://skywork.ai/blog/flux-prompting-ultimate-guide-flux1-dev-schnell/

3. **Ambience AI — Flux 2 Pro Prompt Guide (2026)**
   https://www.ambienceai.com/tutorials/flux-prompting-guide

4. **WaveSpeed Blog — Qwen Image 2512 Text Rendering Guide**
   https://wavespeed.ai/blog/posts/qwen-image-2512-text-rendering/

5. **Medium (Amdad H / Towards AGI) — How to Write Negative Prompts in FLUX**
   https://medium.com/towards-agi/how-to-write-negative-prompts-in-flux-e4305c9e7333

6. **Civitai Education — Prompt Crafting Guide Part 1: Basics**
   https://education.civitai.com/civitais-prompt-crafting-guide-part-1-basics/

7. **Medium (Boqiang Liang) — FLUX.1-dev: Encoders and Token Limitations**
   https://medium.com/@lbq999/flux-1-dev-encoders-and-token-limitations-8631c179eaad

8. **Apatero Blog — Best Local LLM Prompt Enhancer for AI Generation 2025**
   https://apatero.com/blog/best-local-llm-prompt-enhancer-ai-generation-2025

9. **Stable Diffusion Art — SDXL vs Flux1.dev Models Comparison**
   https://stable-diffusion-art.com/sdxl-vs-flux/

10. **ZSky AI — Why Your AI Images Look Bad: 15 Fixes**
    https://zsky.ai/blog/why-ai-images-look-bad

11. **HuggingFace — FLUX.1-dev: Discussions on Token Limits**
    https://huggingface.co/black-forest-labs/FLUX.1-dev/discussions/43
