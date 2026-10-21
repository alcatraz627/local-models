# Candidate model suite

Build inputs first, then dry-run or run one stage at a time. The commands below
use `python3` because this worktree has no `.venv/`; the suite scripts and image
fixture generator use only the standard library. No command here pulls a model.

```sh
python3 probe/candidates/build_fixtures.py
python3 probe/candidates/run.py see-diff --dry-run
python3 probe/candidates/run.py see-read --dry-run
python3 probe/candidates/run.py image-tools --dry-run
python3 probe/candidates/run.py text-small --dry-run
python3 probe/candidates/run.py embed --dry-run
python3 probe/candidates/score.py
```

After reviewing each printed disk cost, run a model with `run.py <stage>
--model <id>`. For the current runnable paths, the exact commands are:

```sh
python3 probe/candidates/run.py see-diff --model gemma4:26b
python3 probe/candidates/run.py see-diff --model minicpm-v4.6
python3 probe/candidates/run.py see-read --model minicpm-v4.6
python3 probe/candidates/run.py see-read --model mlx:mlx-community/Qwen3-VL-8B-Instruct-4bit
python3 probe/candidates/run.py text-small --model granite4:tiny-h
python3 probe/candidates/run.py text-small --model gemma4-e4b-warm
```

For Stage 2, run `python3 probe/candidates/run.py image-tools` after adding a
runner for each job. For new Stage 1 and Stage 3 candidates, select the exact
model with `--model` after its runner and local artifact are verified. Until
then, the command exits 3 with `NEEDS RUNNER`. Stage 0's MLX diff command also
exits 3 with `UNRUNNABLE`. Stage 4 skips and exits 0.

`run.py <stage> [--model M]` selects a stage or one model. Before each actual
fixture call it runs `warm off all`. It writes
`results/<stage>/<model-slug>.json`; missing Ollama models print an
`ollama pull ...` command and return 3. It never performs that pull. `--dry-run`
validates that every fixture input and `truth.json` exists, parses every truth
file, and prints the commands it would run without invoking model CLIs.

## Stages and candidates

| Order | Stage | Comparison or job | Candidate disk cost |
|---:|---|---|---|
| 0 | `see-diff` | gemma4:26b (17 GB) vs minicpm-v4.6 and Qwen3-VL-8B MLX | minicpm-v4.6: 1.6 GB; Qwen3-VL-8B 4-bit: about 6 GB |
| 1 | `see-read` | minicpm-v4.6 and Qwen3-VL-8B incumbents vs the candidates | MiMo-V2.6-Distill-Qwen-9B: 18.8 GB; Qwen2.5-VL-7B: 16.6 GB; Pixtral-12B: 25.4 GB; granite-docling-258M: 3.1 GB |
| 2 | `image-tools` | New image jobs | mflux qwen-edit: unconfirmed; FLUX.1-Kontext-dev 4-bit: unconfirmed; RMBG-2.0: unconfirmed, non-commercial license; Real-ESRGAN x4: unconfirmed |
| 3 | `text-small` | granite4:tiny-h / gemma4-e4b-warm vs text challengers | Nemotron 3.5 Bolt 74B-A9B-24GB: 24.1 GB; MiniCPM5-2B: 5.0 GB |
| 4 | `embed` | embeddinggemma-2:740m vs nomic-embed-text | no eval because archived RAG harness/data is absent |

Repository storage sizes below are HF API `usedStorage` values (decimal GB),
not promised download sizes for an eventual quantized runner. The HF IDs and
sizes were checked from API responses on 2026-10-21:

| Candidate | Verified ID | HF API storage |
|---|---|---:|
| MiMo-V2.6-Distill-Qwen-9B | [`XiaomiMiMo/MiMo-V2.6-Distill-Qwen-9B`](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Distill-Qwen-9B) | 18,839,710,173 B (18.8 GB) |
| Qwen2.5-VL-7B-Instruct | [`Qwen/Qwen2.5-VL-7B-Instruct`](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) | 16,584,414,560 B (16.6 GB) |
| Pixtral-12B | [`mistralai/Pixtral-12B-2409`](https://huggingface.co/mistralai/Pixtral-12B-2409) | 25,384,829,919 B (25.4 GB) |
| granite-docling-258M | [`ibm-granite/granite-docling-258M`](https://huggingface.co/ibm-granite/granite-docling-258M) | 3,045,691,426 B (3.1 GB) |
| Nemotron 3.5 Bolt | [`nvidia/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB`](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB) | 24,101,664,038 B (24.1 GB) |
| MiniCPM5-2B | [`openbmb/MiniCPM5-2B`](https://huggingface.co/openbmb/MiniCPM5-2B) | 5,033,557,096 B (5.0 GB) |

All six API requests returned HTTP 200 and a model object naming the ID. No
candidate ID above is UNVERIFIED. Nemotron resolves to a 74B-A9B model, so the
`text-small` placement and a runnable Ollama tag remain gaps. HF repository
storage for the original models is reported; quantized installation costs can
differ.

The `see-read` additions and all Stage 2 candidates are currently **needs a
runner**; see [GAPS.md](GAPS.md). Stage 3 needs exact Ollama tags and an allowed
runner integration. Those gaps cause a dry-run to print `NEEDS RUNNER`; they do
not start another tool. Stage 4 prints its skip reason. A replacement must pass
every fixture the incumbent passes; a model confidence score is never used.

## Fixture checks

Stage 0 checks are based on assertions in `probe/fixtures/vis-battery.py` and
truth descriptions in `make-fixtures.py`: icon color/border changes, the
identical-pair absence guard, theme palette with unchanged text, aspect-ratio
incomparability, and the chart's Q3→Q5 label plus taller bar. The login pair
truth is read from the two copied images (12 open orders becomes 47 and a last
sync line appears). Stage 1 has exact OCR strings, the UI pairs, and copied rug
cases with their original `case.json`; the twelfth-motif case explicitly names
motif 9 as the outlier. Synthetic image-tool inputs include a known RMBG mask,
an edit confined to a marked rectangle, and the rug image for upscale reading.

The Stage 3 source fixture copies `probe/items.toml`. Its existing pass-marker
heuristics are provisional signals and still require human verdicts, as
`bin/probe` specifies. They are not recast as model correctness proof. The
existing fleet gate proves only `ok=true` plus non-empty output; it does not
prove content quality.

Before an eventual MLX run, ensure no Ollama model of 7 GB or more is resident.
Do not load MLX beside one. The runner calls `warm off all` before each fixture
run. Review each listed cost against the disk-budget bands in `CLAUDE.md`
before downloading anything.
