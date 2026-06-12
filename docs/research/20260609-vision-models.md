# Vision-Language Model Survey: Local Screenshot & Design Parsing (2026)

**Purpose:** Select a local VLM that parses images to feed a cloud Claude agent —
specifically (a) screenshot/terminal/error-dialog OCR and UI-state reading, and
(b) design-mockup layout/component understanding. The VLM does dumb-but-accurate
parsing; Claude Opus does all reasoning.

**Hardware:** Machine A — Apple M5 Pro, 20-core GPU, Metal 4, 64 GB unified RAM.
Machine B (LAN) — M4 Pro, 24 GB unified RAM. Ollama 0.19+ (MLX backend) already
running. Gemma4 26b/31b already present.

**Hard constraint:** Near-zero idle footprint. Load on demand, unload immediately
after parse. Heavy while active is fine.

---

## Serving stack landscape (2026)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Serving options on Apple Silicon — trade-offs summary              │
│                                                                     │
│  Ollama 0.19 (MLX backend)                                          │
│  ├─ Easiest: ollama pull <tag> → zero extra config                  │
│  ├─ MLX gives ~2× vs old llama.cpp Metal path on M4+                │
│  ├─ keep_alive=0 → immediate unload after response                  │
│  └─ ⚠ MLX acceleration limited to select models (March 2026)       │
│                                                                     │
│  vllm-mlx (waybarrios/vllm-mlx)                                     │
│  ├─ OpenAI + Anthropic-compatible API, MCP tool calling             │
│  ├─ 400–525 tok/s on M4 Max (text); prefix-cache gives              │
│  │   up to 28× speedup on repeated-image queries                    │
│  ├─ More complex setup, pip-install + model path management         │
│  └─ Best for high-throughput or repeated-image pipelines            │
│                                                                     │
│  MLX-VLM (Blaizzy)                                                  │
│  ├─ Python library; mlx-community HuggingFace hub models            │
│  ├─ Supports Qwen3-VL, Qwen2.5-VL, LLaVA, etc.                     │
│  └─ Lighter wrapper; good for scripted one-shot calls               │
│                                                                     │
│  LM Studio 0.4                                                      │
│  ├─ GUI; MLX backend outperforms Ollama's GGUF path on M-series     │
│  ├─ Good for model evaluation/testing workflow                      │
│  └─ Less automation-friendly                                        │
└─────────────────────────────────────────────────────────────────────┘
```

**Recommendation for this use case:** Start with **Ollama** (already running,
`keep_alive=0` covers the idle constraint). Graduate to `vllm-mlx` if you need
prefix caching or concurrent requests.

---

## Candidate model survey

### 1. Qwen3-VL (Alibaba, late 2025)

**Status:** Available on Ollama. Supersedes Qwen2.5-VL as top open-weight VLM for
OCR-heavy tasks.

| Variant | Ollama tag | ~Disk/RAM (Q4_K_M) | Fits comfortably on |
|---|---|---|---|
| 8B Instruct | `qwen3-vl:8b` | ~6 GB | Machine B (24 GB) or A |
| 32B Instruct | `qwen3-vl:32b` | ~22–24 GB | Machine A (64 GB) |

**OCR / screenshot quality:** Qwen wins at every tier on OCR benchmarks. The 8B
model handles OCR, charts, screenshots, and math better than Qwen2.5-VL 7B at
every benchmark. The 32B is the best dense open-weight VLM for document/layout
understanding as of mid-2026.

**Context:** 256K native tokens (expandable to 1M with Qwen3-2507 weights).

**Latency estimate on Machine A (M5 Pro, 64 GB, Ollama 0.19 MLX):**
- `qwen3-vl:8b` → ~80–100 tok/s decode
- `qwen3-vl:32b` → ~25–35 tok/s decode (still comfortable for one-shot image parses)

**Verdict for this use case:** **Strongest candidate.** Both OCR tasks (screenshot
text extraction) and design mockup structural understanding are Qwen3-VL's
documented strengths. The 32B is the right pick on Machine A.

---

### 2. Gemma4 (Google, 2026) — already present

**Status:** `gemma4:26b` and `gemma4:31b` are already on Machine A. Natively
multimodal (text+image).

**Vision quality:**
- Variable visual token budget per image (70–1120 tokens). Using 560–1120 tokens
  is needed for OCR and chart reading; smaller budgets degrade fidelity noticeably.
- Gemma 4 31B scored 76.9% on MMMU Pro (vs Qwen3.5 published scores), strong for
  general visual understanding.
- OCR comparison: Gemma 4 has stronger EU-language OCR. But **Qwen wins at every
  tier for OCR overall** in direct model comparisons.
- The native aspect-ratio vision encoder handles screenshots and documents well.
  Good for UI state reading and layout description.

**Footprint:** Already loaded/resident in Ollama. Zero additional pull required.

**Verdict:** Gemma4:27b is **good enough to start today** for both screenshot
parsing and design mockup understanding — especially with `num_predict` tokens
budget set to 1120. It will not be the best-in-class on OCR fidelity but is
more than adequate for feeding structured text to Claude Opus as a reasoning
layer. Use it as the bootstrap model; only pull Qwen3-VL if you observe accuracy
gaps on dense-text screenshots or complex mockup layouts.

---

### 3. Qwen2.5-VL (Alibaba, 2025)

**Status:** Available on Ollama (`qwen2.5-vl:7b`, `qwen2.5-vl:72b`). **Superseded
by Qwen3-VL** — skip unless Qwen3-VL is unavailable.

- 7B: document OCR score 95.7 on OCRBench (higher than LLaMA 3.2 90B at 90.1)
- 72B: excellent but ~45 GB at Q4 — tight even on Machine A

---

### 4. Llama 4 Scout (Meta, April 2026)

**Status:** Available on Ollama (`llama4:scout`). MoE architecture — 109B total /
17B active parameters.

**Vision:** Natively multimodal; good for visual recognition, image reasoning, and
captioning. Tested reliably up to 5 images per prompt.

**Footprint:** Q4 quantization on 64 GB Machine A → ~35 GB loaded. Fits, but
leaves less headroom. Decode: ~32 tok/s on M5 Max (slightly slower than Qwen3-VL
32B for single-image parses).

**Verdict:** Viable but Qwen3-VL 32B is more OCR-precise and lighter per active
parameter. Skip Scout for this specific use case unless you need its 10M context
window for multi-screenshot sessions.

---

### 5. Moondream 2 — lightweight fallback

**Status:** Available on Ollama (`moondream:v2`). 1.9B parameters, ~1.5 GB.

**Speed:** Sub-second first-token on any M-series chip. Extremely fast.

**OCR quality:** Adequate for simple UI dialogs, error messages, short terminal
output. Better than nothing; measurably weaker than 7B+ models on dense text,
multi-column layouts, or design mockups with many elements.

**Prompt tip:** Use `"Transcribe all visible text in natural reading order"` — this
phrasing consistently outperforms generic describe-image prompts.

**Verdict:** Ideal lightweight fallback for "is this a simple error or a complex
UI?" triage calls, or when latency under 1 second matters more than completeness.
Not a substitute for Qwen3-VL on design mockups.

---

### 6. MiniCPM-V 2.6 / 4 (OpenBMB)

**Status:** `minicpm-v` on Ollama; MiniCPM-V 4.6 supports SGLang, vLLM, llama.cpp,
Ollama.

**OCR quality:** Surpassed GPT-4o on OCRBench at 8B scale. Handles up to 1.8M
pixels per image, any aspect ratio.

**Footprint:** 8B parameters, ~6 GB Q4.

**Verdict:** Strong OCR alternative at the same size tier as Qwen3-VL 8B. Worth
benchmarking side-by-side against Qwen3-VL 8B if you need to run on Machine B
(24 GB). Qwen3-VL 8B is currently the consensus pick but MiniCPM-V 4.6 is a
close second.

---

### 7. InternVL3 (Shanghai AI Lab)

**Status:** Available via HuggingFace + MLX-VLM. Less established in Ollama
library as of mid-2026.

**Verdict:** Skip for now. Qwen3-VL 32B covers the same capability tier with
better Ollama integration and broader community support.

---

### 8. GLM-4.5V / GLM-4.1V-9B (Zhipu, 2026)

**Status:** Emerging top benchmark performers (GLM-4.1V-9B reportedly matches 72B
models on 18 benchmarks). Less mature Ollama ecosystem as of June 2026.

**Verdict:** Watch list. Check Ollama availability in 2–3 months. Potentially
strong competition for Qwen3-VL at 9B scale.

---

## Side-by-side summary

```
┌──────────────────┬──────┬──────────┬────────────┬──────────────┬──────────────┐
│ Model            │ Size │ RAM (Q4) │ OCR fidelity│ UI/design   │ Fits B (24G)?│
├──────────────────┼──────┼──────────┼────────────┼──────────────┼──────────────┤
│ qwen3-vl:32b     │ 32B  │ ~23 GB   │ ★★★★★     │ ★★★★★       │ No           │
│ qwen3-vl:8b      │ 8B   │ ~6 GB    │ ★★★★☆     │ ★★★★☆       │ Yes          │
│ gemma4:27b       │ 27B  │ ~18 GB   │ ★★★★☆     │ ★★★★☆       │ Yes (tight)  │
│ gemma4:31b       │ 31B  │ ~21 GB   │ ★★★★☆     │ ★★★★★       │ No           │
│ minicpm-v 4.6    │ 8B   │ ~6 GB    │ ★★★★☆     │ ★★★★☆       │ Yes          │
│ llama4:scout     │ 109B │ ~35 GB   │ ★★★★☆     │ ★★★★☆       │ No           │
│ moondream:v2     │ 1.9B │ ~1.5 GB  │ ★★★☆☆     │ ★★★☆☆       │ Yes          │
└──────────────────┴──────┴──────────┴────────────┴──────────────┴──────────────┘
Notes: OCR fidelity = dense text in screenshots, terminal output, error dialogs.
       UI/design = layout structure, component identification, mockup parsing.
       Ratings are relative to the full open-weight VLM field as of June 2026.
```

---

## Decision: Primary + Fallback

### Phase 1 — Start today (zero new model pulls)

**Use `gemma4:27b` (already present on Machine A).**

It handles both screenshot OCR and design mockup layout description acceptably.
Set `num_predict` image token budget to 560+ for screenshot tasks. This lets you
build and test the Claude handoff pipeline immediately without additional disk
usage.

### Phase 2 — Upgrade primary (when you hit accuracy limits)

**Pull `qwen3-vl:32b` on Machine A.**

```bash
ollama pull qwen3-vl:32b
```

~23 GB footprint. With `OLLAMA_KEEP_ALIVE=0` (or per-request `keep_alive: "0"`),
idle footprint is zero — it loads in ~8–12 seconds from SSD on M5 Pro and
unloads immediately after each response.

This is the best open-weight VLM for this use case: OCR-first design, excellent
on screenshots with small fonts, terminal dumps, and structured design mockups.

### Lightweight/fast fallback (always available)

**`moondream:v2`** — 1.9 GB, sub-second latency.

Use when:
- Simple error dialog / single-line terminal message (no layout complexity)
- Pre-filtering: "is this screenshot worth sending to the heavy model?"
- Machine B triage (24 GB — can also run `qwen3-vl:8b` for better quality)

```bash
ollama pull moondream
```

---

## Machine assignment

```
Machine A (M5 Pro, 64 GB) — primary VLM host
├─ gemma4:27b / gemma4:31b  (already present — Phase 1 bootstrap)
├─ qwen3-vl:32b             (pull when ready for Phase 2)
└─ moondream:v2             (fallback, always-available, 1.5 GB)

Machine B (M4 Pro, 24 GB) — secondary / overflow
├─ qwen3-vl:8b              (pull if B needed for concurrent work)
└─ moondream:v2             (same fallback)
```

---

## Zero-idle configuration

Add to shell environment or `~/.config/ollama/env`:

```bash
export OLLAMA_KEEP_ALIVE=0          # unload immediately after response
export OLLAMA_NUM_PARALLEL=1        # one request at a time
export OLLAMA_MAX_LOADED_MODELS=1   # never keep two models hot simultaneously
```

Or pass per-request in API calls:
```json
{ "keep_alive": "0" }
```

Reload time from cold (M5 Pro SSD): ~8–15 seconds for a 23 GB model. Acceptable
for a human-in-the-loop parsing pipeline; unacceptable for sub-second interactive
use (use moondream for those cases).

---

## Screenshot → Claude handoff: example prompt pattern

### VLM prompt (sent to local Ollama/Qwen3-VL or Gemma4)

```
You are a visual parser. Extract ALL visible information from this screenshot
with maximum fidelity. Do not summarize or interpret — transcribe and describe.

Output format:
1. VISIBLE TEXT: Transcribe every readable string in natural reading order,
   preserving hierarchy (labels, values, error messages, button text, etc.)
2. UI STATE: List all visible UI elements and their apparent state
   (buttons enabled/disabled/focused, input fields and their values,
   checkboxes, dropdown selections, error indicators).
3. LAYOUT: Briefly describe the overall structure (modal dialog, terminal,
   browser devtools, code editor, design mockup with N panels, etc.)
4. ANOMALIES: Anything that looks like an error, warning, or unexpected state.

Be precise. Claude will do all reasoning from your output.
```

### Claude Opus prompt (cloud, receives VLM output)

```
The following is a structured parse of a [screenshot/design mockup] produced by
a local vision model. Treat it as ground-truth observation data.

<vlm_parse>
[VLM output pasted here]
</vlm_parse>

[Your actual question/task for Claude here]
```

### For design mockup parsing, replace the VLM prompt's UI STATE section with:

```
2. COMPONENTS: List every distinct UI component visible, its apparent type
   (navbar, card, form, table, modal, sidebar, etc.), its position relative
   to others (top-left, centered, below X), and any visible labels/content.
3. LAYOUT GRID: Describe the overall page structure — columns, rows, spacing
   patterns, visual hierarchy.
```

---

## Sources consulted

- [Qwen3-VL on Ollama library](https://ollama.com/library/qwen3-vl)
- [Qwen/Qwen3-VL-8B-Instruct — Hugging Face](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct)
- [Qwen/Qwen3-VL-32B-Instruct — Hugging Face](https://huggingface.co/Qwen/Qwen3-VL-32B-Instruct)
- [Gemma 4 vision benchmark guide — gemma4.wiki](https://www.gemma4.wiki/benchmark/gemma-4-vision-benchmark)
- [Gemma 4 for computer vision engineers — Datature](https://datature.io/blog/gemma-4-what-computer-vision-engineers-actually-need-to-know)
- [I replaced a $50/month OCR API with Gemma 4 — DEV Community](https://dev.to/stephen_sebastian_c85ea2b/i-replaced-a-50month-ocr-api-with-gemma-4s-native-vision-and-you-can-too-4jnd)
- [Best vision models you can run locally — InsiderLLM](https://insiderllm.com/guides/vision-models-locally/)
- [Best open-source VLMs 2026 — Labellerr](https://www.labellerr.com/blog/top-open-source-vision-language-models/)
- [MiniCPM-V GitHub](https://github.com/OpenBMB/MiniCPM-V)
- [moondream:v2 — Ollama library](https://ollama.com/library/moondream:v2)
- [Ollama MLX Apple Silicon — Ollama blog](https://ollama.com/blog/mlx)
- [Ollama 0.19 ships MLX backend — Medium](https://medium.com/@tentenco/ollama-0-19-ships-mlx-backend-for-apple-silicon-local-ai-inference-gets-a-real-speed-bump-878b4928f680)
- [Ollama keep_alive docs — docs.ollama.com](https://docs.ollama.com/faq)
- [vllm-mlx — GitHub](https://github.com/waybarrios/vllm-mlx)
- [MLX-VLM — GitHub](https://github.com/Blaizzy/mlx-vlm)
- [Llama 4 on Ollama guide — Serverman](https://www.serverman.co.uk/ai/ollama/how-to-run-llama-4-on-ollama/)
- [Qwen3-VL Ollama deployment guide — apidog](https://apidog.com/blog/how-to-run-qwen-3-vl-locally-with-ollama/)
- [Best local LLMs for Mac 2026 — InsiderLLM](https://insiderllm.com/guides/best-local-llms-mac-2026/)
- [Gemma 4 vs Qwen 3.6 comparison — willitrunai](https://willitrunai.com/blog/qwen-3-6-vs-gemma-4)
