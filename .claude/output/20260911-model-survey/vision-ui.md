# Local VLM survey, September 2026

Scope: candidates to beat the suite's current vision defaults (`minicpm-v` for
general/OCR reads, `gemma4:26b` for `see --ui` structure) on an M5 Pro, 64 GB,
~307 GB/s Mac, via self-hosted Ollama v0.33.0 or MLX-VLM.

## The Ollama-on-Apple-Silicon trap, still live

**`ollama/ollama` issue #16264 is still OPEN** (checked 2026-09-11, `gh issue
view 16264 --repo ollama/ollama` returned state `OPEN`). A Qwen3-VL-8B GGUF
plus mmproj imported into Ollama registers as vision-capable, then crashes the
runner on the first real image request on Apple Silicon/Metal: HTTP 500,
"llama runner terminated, exit status 2". The latest comment (still
unresolved) traces it to a mismatch between `llama_model_n_embd` and
`llama_model_n_embd_inp` in Ollama's Go runner when Qwen3-VL's "deepstack"
image features are present. This is an Ollama-side bug, not a model defect.

This affects **manually-imported Qwen3-VL GGUF** via Ollama's llama.cpp path.
Whether the official `ollama.com/library/qwen3-vl` tags (4b/8b/30b/32b/235b,
all 256K ctx, requiring Ollama 0.12.7+) hit the same code path was not
confirmed by search. Every related thread found describes the same crash
signature regardless of import method, so treat the official tags as
**unverified on Apple Silicon until probe-tested**, not as a safe bypass.

**The clean workaround is MLX-VLM.** Qwen3-VL (dense and MoE) landed in
`Blaizzy/mlx-vlm` recently (Qwen's own account confirmed it), and
`mlx-community` publishes ready quantized checkpoints, for example
`Qwen3-VL-4B-Instruct-3bit` and `Qwen3-VL-32B-Thinking-4bit`. Ollama 0.30+
also grew its own native MLX engine for some models, but Qwen3-VL vision
specifically should route through **MLX-VLM directly**, not through Ollama,
until #16264 closes. This matches the brief's own fallback rule: MLX-VLM
covers VLMs Ollama does not serve cleanly, and Qwen3-VL is now squarely that
case.

## Role 1: general vision reading (describe/answer about an arbitrary image)

| Model | Size (q4/q8) | Runtime | Case vs. incumbent (`minicpm-v`) | Known failure modes |
|---|---|---|---|---|
| **Qwen3-VL-8B-Instruct** | ~6.1 GB Ollama tag, smaller as 3-bit MLX | MLX-VLM (Ollama path unverified, see trap above) | Beats minicpm-v on general reasoning and scene understanding, not just text. Strong on spatial relationships and long-context (256K) multi-image tasks | Larger footprint than minicpm-v for equivalent quality. MLX-VLM tooling is younger and rougher than Ollama's `see` integration |
| **MiniCPM-V 4.6** | ~1.6 GB (Ollama `minicpm-v4.6`, also a 1b tag) | Ollama-native | Same lineage as the incumbent but cuts vision-encoder FLOPs by more than 50% and gets 2.4x token throughput vs. its own baseline. A strict efficiency upgrade over `minicpm-v` at similar or smaller footprint | Newer and less battle-tested than the incumbent. Verify OCR-fidelity parity before swapping the default |
| **InternVL3.5-8B** | ~8B, GGUF or an `mlx-community/InternVL3-8B-MLX-4bit`-style build | MLX-VLM (no Ollama library tag found) | MIT-licensed, competitive general and document scores (840 OCRBench) | No first-class Ollama tag. Adds an MLX-VLM dependency for a role the incumbent already covers reasonably |
| **Gemma4:26b** (already in suite, used for `see --ui`) | ~26B, Ollama-native | Ollama | Already proven as the suite's structure-reading model, not a new candidate here | Heavier than needed for plain image description |

**Read:** the low-risk upgrade for minicpm-v is **MiniCPM-V 4.6**. Same family,
smaller, faster, Ollama-native, no runtime change. Qwen3-VL-8B is the
higher-ceiling option if MLX-VLM plumbing is worth adding for this role too,
but its edge over MiniCPM-V 4.6 on plain "describe this image" is smaller than
its edge on OCR and UI, below.

## Role 2: OCR / verbatim text extraction

The suite already has Apple Vision OCR (`see --ocr`, no model, ~300ms) for
pure verbatim text. A VLM only earns its place here by adding scene context
around the text (what the text is labeling, its role in the layout), not by
out-OCR'ing a dedicated OCR engine on raw string accuracy.

| Model | Size | Runtime | Case for scene-aware OCR | Failure modes |
|---|---|---|---|---|
| **Qwen3-VL-4B / 8B** | 3.3 GB / 6.1 GB Ollama tags, smaller as an MLX quant | MLX-VLM | Clears every Gemma3 size including 27B on DocVQA: 4B scores 95.3, 8B scores 96.1. The strongest documented OCR-plus-context combination found for this class | Same Apple-Silicon-via-Ollama crash risk (#16264); use MLX-VLM |
| **MiniCPM-V 4.5/4.6** | 8.7 GB (4.5) / 1.6 GB (4.6) | Ollama-native | Purpose-built for OCR, high-res documents, and video. 4.6 keeps the OCR lineage while cutting compute | Weaker than Qwen3-VL on structured document benchmarks per public scores, though still solid |
| **InternVL3.5-8B** | ~8B | MLX-VLM | 840/1000 OCRBench, a decent scene-plus-text combination | No Ollama tag. Marginal gain over Qwen3-VL for the extra runtime dependency |

**Read:** for text-plus-context (the actual gap Apple Vision OCR does not
fill), **Qwen3-VL-4B or 8B via MLX-VLM** is the best-evidenced pick. The
DocVQA margin over Gemma3-27B is large enough to justify the new runtime path.
If adding MLX-VLM is unwelcome scope right now, MiniCPM-V 4.6 is the
Ollama-native fallback and a strict upgrade over the current `minicpm-v`.

## Role 3: UI inventory and structure discrimination (the suite's weakest spot)

This is the highest-value gap: which control is selected or active, region
proportions, element states, hierarchy. Exactly what `see --ui` currently
routes to `gemma4:26b` for, because `minicpm-v` gets it wrong.

| Model | Size | Runtime | Case for improving UI-structure discrimination | Failure modes |
|---|---|---|---|---|
| **Qwen3-VL-8B-Instruct** | 6.1 GB Ollama, smaller as MLX quant | MLX-VLM | **94.4% ScreenSpot**, 54.6% ScreenSpot-Pro, 58.2% OSWorld-G (Qwen3-VL technical report). Purpose-evaluated on GUI element grounding, not just general VQA. Qwen explicitly trains this line to recognize UI elements, understand functions, and operate GUIs. The strongest documented UI-grounding score found for any locally-runnable model in this class | Not yet probe-tested against the suite's own ground-truth fixtures. Apple-Silicon-via-Ollama crash risk applies |
| **Moondream 3 (preview)** | 9B MoE, 2B active | Ollama tag exists (`moondream`) for the older generation; Moondream 3 weights auto-download via the Python API, and an MLX-VLM path is documented (sub-2s inference on Apple Silicon per vendor) | **80.4 ScreenSpot**, up from 60.3 in the prior release. Purpose-built for pointing, grounding, and structured output rather than long conversations. Native bounding-box/coordinate output is a good fit for an inventory tool that wants structured facts, not prose | Meaningfully behind Qwen3-VL-8B on the same benchmark, 80.4 vs 94.4. "Preview" tag suggests the API or format may still shift. Verify the Ollama tag actually serves v3, not the older Moondream2 |
| **Gemma4:26b** (current `--ui` router target) | ~26B | Ollama-native | Already proven on the suite's own dashboard ground-truth test. The bar to beat | Much larger than either candidate above for a worse documented grounding score than Qwen3-VL-8B |
| **InternVL3.5** | 8B to 38B range | MLX-VLM | General MMMU/OCRBench strength suggests reasonable structure reading, but no UI-specific grounding benchmark was found in this search | Unproven on this specific task. Lower priority than the two above |

**Read: Qwen3-VL-8B is the standout for this role.** Its ScreenSpot score,
94.4, is far ahead of Moondream 3's 80.4, and the general-purpose incumbent
gemma4:26b was never benchmarked on UI-grounding specifically. It won the
current role by default, not by a documented UI score. Given the suite's own
ruling that this is the highest-value gap, Qwen3-VL-8B via MLX-VLM is the
single most important pull-and-probe candidate in this whole survey.

Moondream 3 is the interesting second axis: far smaller (2B active) and
outputs structured coordinates natively, which may suit a checklist-style
inventory tool better than prose-then-parse, even though its raw ScreenSpot
number trails Qwen3-VL. Inference cost and output shape both matter for a
$0/offline suite that runs many probes, so it is worth testing anyway.

## Ranked shortlist: pull and probe-test against existing ground-truth fixtures

1. **Qwen3-VL-8B-Instruct**, role: UI inventory (primary target) plus
   OCR/general secondary. ~6.1 GB q4 Ollama tag size, smaller as an MLX quant.
   Runtime: **MLX-VLM** (Ollama path blocked by open issue #16264 on Apple
   Silicon). Highest-value single pull in this survey: it directly attacks the
   UI-structure gap with a documented benchmark margin.
2. **Qwen3-VL-4B-Instruct**, role: OCR / scene-aware text extraction, a
   lighter footprint if the 8B proves too slow for routine probes. ~3.3 GB.
   Runtime: **MLX-VLM**.
3. **MiniCPM-V 4.6**, role: general vision reading / OCR, a low-risk drop-in
   upgrade for the current `minicpm-v` default. ~1.6 GB. Runtime:
   **Ollama-native** (`ollama pull minicpm-v4.6`), no new dependency, smallest
   footprint of the whole list.
4. **Moondream 3 (preview)**, role: UI grounding, secondary to Qwen3-VL-8B.
   Worth testing for its structured-coordinate output shape and much smaller
   active-parameter cost (2B active in a 9B MoE). Runtime: **MLX-VLM**
   (Moondream's Python path also auto-downloads; confirm an MLX build exists
   before committing).
5. **InternVL3.5-8B**, role: general/OCR fallback, MIT-licensed. ~8B. Runtime:
   **MLX-VLM** (an `mlx-community/InternVL3-8B-MLX-4bit`-style build; no
   Ollama tag). Lowest priority of the five: no UI-specific benchmark was
   found, and its general/OCR scores do not clearly beat Qwen3-VL or MiniCPM-V
   4.6 enough to justify a third new dependency path unless the first four
   disappoint.

## Open items for the probe pass, not answered by this search

- Whether the official `ollama.com/library/qwen3-vl` tags hit the same Metal
  crash as the manually-imported GGUF in #16264. Test directly rather than
  assume either way.
- Moondream 3's exact weight size and whether a ready `mlx-community` quant
  exists yet, versus needing a local conversion.
- Real MLX-VLM throughput on this specific M5 Pro for Qwen3-VL-8B. The
  benchmark scores above are accuracy, not latency; latency needs measuring
  in-suite.

## Sources

Consulted via web search on 2026-09-11: `ollama/ollama` issue #16264 (state
confirmed OPEN via `gh issue view`); Ollama library pages for qwen3-vl,
minicpm-v4.5, minicpm-v4.6; the Qwen3-VL Technical Report (arxiv 2511.21631);
the Moondream blog post "moondream-3-preview" and moondream.ai/models;
mlx-community InternVL3/InternVL3_5 Hugging Face repos; the Blaizzy/mlx-vlm
GitHub repo; and several 2026-vintage vendor and aggregator posts (mixpeek,
bentoml, tinyweights.dev, promptquorum), each cross-checked against the
primary sources above rather than taken alone.
