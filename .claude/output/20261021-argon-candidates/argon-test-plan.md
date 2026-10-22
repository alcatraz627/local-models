# Argon ideator output (raw, unverified)

Citations checked: 20 of 25 exact. Candidate names not yet verified against Hugging Face.

## 1. `BIG_MODEL` (`gemma4:26b`) Verdict

**Verdict: Prune `gemma4:26b` (−17 GB) after re-pointing its remaining fallback/vision hooks.**

### Why it should go
- **Zero organic text demand:** Text usage after the July benchmark burst (772 calls) collapsed to **1 in Aug, 6 in Sep, and 0 in Oct**. Claude Sonnet, Codex, and `lm gemini` (`gemini-3.8-flash`) completely cover heavy reasoning and synthesis.
- **Vision role already superseded:** `see --ui` moved to `mlx-community/Qwen3-VL-8B-Instruct-4bit` (`UI_DEFAULT_MLX=1`) in September, dropping Ollama vision calls on `gemma4:26b` to **5/month** (Sep 5, Oct 5).
- **Memory & disk reclaim:** Removing `gemma4:26b` reclaims **17 GB** on disk (dropping footprint from 114 GB to ~97 GB, or ~89 GB with the 8 GB prune pair `qwen2.5-coder:3b` + `gemma4:e4b-it-qat`) and eliminates the #1 OOM hazard (co-loading 17 GB `gemma4:26b` in Ollama alongside 6 GB `Qwen3-VL-8B` in MLX).

### What breaks if deleted without config/script updates

1. **`config.sh`:**
   - **Line 10:** `BIG_MODEL="${BIG_MODEL:-gemma4:26b}"` — points the `big` tier at a missing tag.
   - **Line 41:** `UI_VISION_MODEL="${UI_VISION_MODEL:-$BIG_MODEL}"` — inherits `gemma4:26b` for Ollama structure reads.
2. **`bin/_lib.sh` & `bin/q`:**
   - **`bin/_lib.sh:55`:** `resolve_tier big` echoes `${BIG_MODEL:-gemma4:26b}`.
   - **`bin/q:157, 235, 634`:** `q --big`, `q -m big`, and `q --diy` plans that route to `tier: "big"` (`intents/diy-plan.toml:17`, `intents/diy-plan.schema.json:10`) fail with `model_missing`.
3. **`bin/see`:**
   - **`bin/see:26`:** Fallback default `MODEL="${VISION_MODEL:-gemma4:26b}"` if `VISION_MODEL` is unset.
   - **`bin/see:436` (`see diff`):** `see diff` (without `--no-read`) sets `MODEL="${UI_VISION_MODEL:-$MODEL}"` and runs through Ollama, not the MLX block (`bin/see:203` gates MLX on `$UI`). Deleting `gemma4:26b` breaks `see diff A B` unless `UI_VISION_MODEL` is repointed to `minicpm-v4.6` or `see diff` is wired to MLX.
   - **`bin/see:469` (`UI_DEFAULT_MLX=0 see --ui`):** The non-MLX fallback for `see --ui` uses `UI_VISION_MODEL`.
4. **`bin/imagine`:**
   - **`bin/imagine:288` (`imagine critique <id>`):** Hardcodes `local model="${IMAGINE_CRITIC_MODEL:-gemma4:26b}"` instead of `VISION_MODEL`.
5. **`lib/ui-verify`:**
   - **`lib/ui-verify:66, 152, 159` (`lm ui-verify`):** Both explicit `lm ui-verify --big` and the **automatic escalation retry** (when the warm tier returns fewer verdicts than claims on line 158: `run_judge --big`) call `q --big`.Note: re-pointing `BIG_MODEL` to `CODE_MODEL` (`qwen3.6:35b-a3b`) would break `ui-verify`'s retry because the 35B code tier ignores Ollama's `--format` schema constraint; re-point `BIG_MODEL` to `WARM_MODEL` (or retire the retry) instead.
6. **`lib/gemini`:**
   - **`lib/gemini:293, 296` (`lm gemini --fallback-local`):** Pipes to `q -m big --raw` and hardcodes `model:"gemma4:26b"` in the JSON envelope.
7. **`lib/rag` & `bin/warm` & `bin/lm`:**
   - **`lib/rag:64, 110`:** `lm rag ask --big` forwards `--big` to `q`.
   - **`bin/warm:48, 66`:** `warm on big` / `warm off big` resolves `big` and fails with HTTP 404.
   - **`bin/lm:275, 289, 305`:** `lm models` displays `big=gemma4:26b` as unpulled.

---

## 2. Eight Additional Vision & Image Candidates

All candidates below are distinct from those already in `config.sh` or `.claude/output/20261021-argon-candidates/report.md`:

| # | Exact Model Name | Disk Size | Apple Silicon Runtime | Toolkit Job | Existence Confidence |
|---|---|---|---|---|---|
| 1 | `mlx-community/Qwen2.5-VL-7B-Instruct-4bit` (or `qwen2.5vl:7b`) | ~4.8 GB (MLX 4-bit) / ~6.0 GB (Ollama) | `mlx-vlm` or `ollama` | **Vector-art & geometry critic (Affinity Designer bridge) + `see diff` judge:** Strong bounding-box/point grounding and fine-detail inspection for sharp tips, gaps, and curve symmetry; runs cleanly in Ollama without Qwen3-VL's `#16264` deepstack crash. | **High** |
| 2 | `mlx-community/Pixtral-12B-4bit` | ~7.1 GB | `mlx-vlm` | **High-resolution UI & vector-art critique:** Native variable-resolution / aspect-ratio patch encoding (no square resize distortion), preserving thin vector strokes, sharp corners, and wide menubar/BFB layouts. | **High** |
| 3 | `ibm-granite/granite-docling-258M-mlx` (or `ds4sd/SmolDocling-256M-preview-mlx-bf16`) | ~0.5 GB | `mlx-vlm` | **Structured document parsing (`q` / `bfb` PDF & layout lane):** Converts pages/screenshots to DocTags (tables, code blocks, hierarchy, reading order) in sub-second passes where flat OCR loses structure. | **High** |
| 4 | `black-forest-labs/FLUX.1-Kontext-dev` (4-bit via `mflux-generate-kontext`) | ~6.8 GB (4-bit) | `mflux` | **Instruction-guided image & mockup editing (`imagine edit`):** Edits localized regions, typography, or layout elements from an existing image (`--from`) without re-rolling composition. | **High** |
| 5 | `black-forest-labs/FLUX.1-Fill-dev` (4-bit via `mflux-generate-in-context` / Fill) | ~6.8 GB (4-bit) | `mflux` | **Masked inpainting (`imagine inpaint`):** Fixes isolated region divergences flagged by `see diff` E5/E6 hot cells while holding 100% of unmasked pixels byte-identical. | **High** |
| 6 | `apple/coreml-fastvit-ma36-f16` (or `apple/mobileclip_s2` via CoreML/MLX) | ~0.15–0.4 GB | `coreml` | **Fast perceptual region embeddings for `lib/vis-compare.py`:** Sub-50ms Neural Engine feature extraction to distinguish semantic shape changes from anti-aliasing jitter on sharp vector tips. | **Medium** |
| 7 | `briaai/RMBG-2.0` (ONNX / CoreML FP16) | ~0.5 GB | `coreml` / `other` (`onnxruntime-silicon`) | **Deterministic alpha-matte & background removal (`imagine --cutout` / asset pipeline):** Cleanly isolates generated icons, sprites, and Affinity vector exports before `lib/asset-verify.py`. | **High** |
| 8 | `xinntao/Real-ESRGAN` (`realesrgan-x4plus` / `realesr-general-x4v3` via `realesrgan-ncnn-vulkan` or CoreML) | ~0.07 GB | `coreml` / `other` (Metal `ncnn`) | **Fast 2x/4x deterministic upscaler (`imagine upscale` / crop zoom):** Sharpens `schnell` loop drafts or magnifies sub-pixel vector tips/corners before feeding crops to `see`. | **High** |

---

## 3. Test Plan for Top 5 Candidates

### Memory-Safety & Disk-Budget Rules
1. **Single-heavy-model rule:** Before every run, execute `./bin/warm off all` and verify `ollama ps` is empty. Never run an `mlx-vlm` or `mflux` candidate while a >7 GB Ollama model is resident.
2. **Watchdog active:** Ensure `scripts/mem-guard.py` is running (`--once` check before each stage).
3. **Pull-probe-prune budget:** Baseline is **114 GB** (target ≤150 GB, 36 GB headroom). Prune `gemma4:26b` (−17 GB), `qwen2.5-coder:3b` (−1.9 GB), and `gemma4:e4b-it-qat` (−6.1 GB) first to drop baseline to **89 GB**, then test sequentially and delete any candidate that fails its gate.

### Staged Execution Order & Gates

#### Stage 1: `ibm-granite/granite-docling-258M-mlx` (+0.5 GB) — Document Structure Parsing
- **Fixtures:** `probe/fixtures/ocr-fixture.png` and rendered images of `probe/fixtures/e8-a.html` / `probe/fixtures/e8-b.html`.
- **Pass/Fail Criteria:** Extracts all ground-truth strings from `ocr-fixture.png` with zero hallucinated tokens and preserves heading/table tags on `e8-a.html` in <1.5s.
- **Trust Check:** Deterministic string/tag diff against `see --ocr --json` (`mac-ocr`) output and the source DOM in `probe/fixtures/e8-capture-a.json`.

#### Stage 2: `realesrgan-x4plus` (+0.07 GB) — Crop Upscaling for Vector/Corner Inspection
- **Fixtures:** Downsampled 64×64 crops of `probe/fixtures/f2-a.png` / `probe/fixtures/f2-b.png` (corner differences) plus a 3-fixture Affinity vector-art micro-set (1: sharp vs blunted cusp tip, 2: 2px hairline gap, 3: asymmetric bezier handle).
- **Pass/Fail Criteria:** Upscaling the crop 4× before `see` increases corner/tip defect detection accuracy vs raw crops without tripping false positives on `probe/fixtures/f3-a.png` / `f3-b.png` (identical pair).
- **Trust Check:** Run `lib/vis-compare.py` (`probe/fixtures/vis-battery.py` F2 and F3 assertions) and `lib/asset-verify.py` against the high-res ground-truth reference.

#### Stage 3: `mlx-community/Qwen2.5-VL-7B-Instruct-4bit` (+4.8 GB) — Vector Critic & `see diff` Seat
- **Fixtures:** `probe/fixtures/f2-a.png` vs `f2-b.png` (4 corner cells), `probe/fixtures/diff-a.png` vs `diff-b.png` (login UI diff), `probe/fixtures/f3-a.png` vs `f3-b.png` (identical), and the 3 Affinity vector-art fixtures above.
- **Pass/Fail Criteria:** Names all 4 corner divergences on `f2-a/b`, correctly classifies 3/3 vector-tip/gap fixtures, emits zero fabricated differences on `f3-a/b`, and replaces `gemma4:26b` in `see diff` (if using Ollama tag `qwen2.5vl:7b`) at ≤6 GB RAM.
- **Trust Check:** Cross-check every reported region against `lib/vis-compare.py` E5/E6 `top_cells` coordinates and `lm ui-verify` schema validation (`intents/ui-inventory.schema.json`).

#### Stage 4: `mlx-community/Pixtral-12B-4bit` (+7.1 GB) — Native Aspect-Ratio Vector & UI Read
- **Fixtures:** Same fixture pack as Stage 3 plus an ultrawide menubar strip (`see --menubar` artifact) and `probe/fixtures/f4-a.png` / `f4-b.png` and `f5-a.png` / `f5-b.png`.
- **Pass/Fail Criteria:** Must beat both `Qwen3-VL-8B-Instruct-4bit` and Stage 3 (`Qwen2.5-VL-7B`) on sharp-tip vector calls and wide-aspect-ratio UI element counts with zero hallucinated controls.
- **Trust Check:** Automated coordinate/count comparison against `lib/vis-compare.py` JSON evidence pack and `see --ocr --json` word positions; prune immediately if it only ties Stage 3.

#### Stage 5: `black-forest-labs/FLUX.1-Kontext-dev` 4-bit (+6.8 GB) — Targeted Image/Mockup Editing
- **Fixtures:** `presets/skybound-isles.png` and `probe/fixtures/diff-a.png`.
- **Pass/Fail Criteria:** Given a single targeted edit prompt (e.g., change one badge/color while keeping layout), converges in 1 round where `imagine refine` took ≥2 rounds, without shifting unedited regions.
- **Trust Check:** Deterministic check via `see diff ref.png edited.png --no-read --json` + `lib/vis-ledger.py`: target hot cell transitions to `fixed` while out-of-target grid cells maintain `grid_delta_pct < 5.0%`.
