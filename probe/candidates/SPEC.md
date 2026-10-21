# Candidate model suite: build spec

This suite decides which new local models earn a place in the toolkit. It runs each candidate against fixtures whose right answer is known in advance, so a pass means the model got a checkable answer right. A model's own confidence never counts.

Owner rulings (2026-10-21):

- Try every candidate below.
- `see` quality must not drop. A model replaces an incumbent only if it scores at least as well on every fixture the incumbent passes.
- Keep Claude usage to a minimum: Codex builds the harness, and runs go through one script.

## What to build

Build everything under `probe/candidates/`:

| File | Purpose |
|---|---|
| `run.py` | Runs a stage: `run.py <stage> [--model M]`. Writes `results/<stage>/<model-slug>.json` and prints a one-line pass/fail summary per fixture. Never pulls a model; if the model is missing, it prints the exact pull or download command and exits 3. |
| `fixtures/` | Copied or generated fixtures, each with a `truth.json` holding the expected answer and how to check it. |
| `score.py` | Reads `results/` and prints a table per stage: candidate against incumbent, per fixture. Exit 0 always. |
| `README.md` | How to run each stage, the order, and the disk cost of each candidate. |

Use `.venv/bin/python` for anything needing PIL. Use the existing CLIs as the model runner (`see`, `see diff`, `see --mlx`, `q -m`, `imagine`) and do not call Ollama or mlx directly, except for model families `see` cannot run yet. List those in the README as "needs a runner".

## Checks must be mechanical

Every fixture's check is a script comparison against `truth.json`:

- an exact or normalised string match
- a number within a tolerance
- an item named in the answer at the right position (for example "motif 9")
- an absence check, for example "names no difference" on an identical pair

No model judges another model.

## Stages, in run order

### Stage 0: `see-diff`, installed models only, no download

The question: can `see diff` drop gemma4:26b (17 GB)?

- Incumbent: gemma4:26b, which is the current `UI_VISION_MODEL`.
- Challengers: minicpm-v4.6 and `mlx:mlx-community/Qwen3-VL-8B-Instruct-4bit`.
- Fixtures: the pairs in `probe/fixtures/` that `probe/fixtures/vis-battery.py` already knows the truth for. These are f2 to f6 (`f3` is the identical pair, so any claimed difference fails it) and `diff-a.png`/`diff-b.png`. Derive each truth from the battery's assertions and `probe/fixtures/make-fixtures.py`, not from a model.
- Run `see diff A B --json -m <model>`. Check whether `see diff` accepts `-m mlx:<repo>`. If it does not, note it as a gap: MLX for `see diff` would need wiring in `bin/see`, and you must not change `bin/see`.

### Stage 1: `see-read`, single-image reads

- Incumbents: minicpm-v4.6 (plain `see`) and Qwen3-VL-8B (`see --mlx`, `see --ui`).
- Challengers: MiMo-V2.6-Distill-Qwen-9B, Qwen2.5-VL-7B-Instruct, Pixtral-12B and granite-docling-258M.
  - Before writing any of these into a command, confirm the exact Hugging Face repo or Ollama tag exists, with `curl -s https://huggingface.co/api/models/<repo>` (a 200 reply that names the model). Record the verified id and size in the README.
  - A candidate that cannot be verified is listed as UNVERIFIED and gets no stage.
- Fixtures:
  - `probe/fixtures/ocr-fixture.png`: exact strings; truth from `see --ocr --json`, which is Apple Vision and not an LLM.
  - The vis-battery UI fixtures.
  - The Affinity rug cases. Copy them read-only from `/Users/alcatraz627/Code/Claude/Affinity/AffinityWork/guard/test/cases/*/fixture.png`; their `case.json` gives the truth. Example: rug-border-twelve-motifs, where the odd motif is 9. Never write into the Affinity repo.

### Stage 2: `image-tools`, new jobs (no incumbent; pass means the job works)

| Candidate | Job and check |
|---|---|
| mflux qwen-edit (check whether the installed mflux ships it; no download if so) | Edit one region. Check: `see diff ref edited --no-read --json` shows change only in the target grid cells. |
| FLUX.1-Kontext-dev, 4-bit via mflux | Same check as qwen-edit. |
| RMBG-2.0 | Background removal. Check: the alpha matte is within 2 percent of a synthetic fixture with a known mask. Generate the fixture: a shape on a noisy background. Note the licence (non-commercial). |
| Real-ESRGAN x4 | Upscale. Check: running PSNR on a downscale-then-upscale round trip beats Lanczos. Then a crop read: the Affinity tip fixture read by `see` after upscaling beats the raw crop. |

### Stage 3: `text-small`, sweep and warm lanes

- Incumbents: granite4:tiny-h (sweep) and gemma4-e4b-warm (small).
- Challengers: Nemotron 3.5 Bolt and MiniCPM5-2B. Verify the exact tags first, as in stage 1.
- Fixtures: the existing `lm fleet` envelope check plus `probe/items.toml`. Read `lib/fleet` and `bin/probe` for how they score, and reuse that scoring instead of inventing a new one.

### Stage 4: `embed`, low priority

embeddinggemma-2:740m against nomic-embed-text on the archived RAG eval, if its harness still runs. Otherwise mark it skipped and say why.

## Memory and disk rules

These are hard rules:

- Before each model run, call `warm off all`.
- Never load an MLX model while an Ollama model of 7 GB or more is resident. That combination crashed the machine once (see `scripts/mem-guard.py`).
- `run.py` prints each candidate's disk cost before running. The owner's disk budget is in `CLAUDE.md` hard rule 3. The runner never pulls; a person or the orchestrating agent runs the pull after reading the cost.

## Out of scope

- Do not edit `bin/`, `lib/` or `config.sh`. If a stage needs a runner change, write it up in `probe/candidates/GAPS.md`.
- Do not push.
- Commit to a new branch `candidates-suite`.
