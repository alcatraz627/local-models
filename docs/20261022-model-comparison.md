---
reader: the owner, deciding which local model each `see` and `q` job should use
---

# Local model comparison, 2026-10-22

<!-- sessions: vislm-4c@2026-10-22 -->

## What to take from it

- **The plain `see` default is the weakest vision model tested.** minicpm-v4.6 passed 74 of 112 vision checks and fell for false-premise questions on every seed. Qwen3-VL-8B on MLX, which already runs `see --ui`, passed 101. It was worse than minicpm on one case only (one seed of counting red squares), so it does not strictly meet your rule of matching the incumbent everywhere. Switching the default is your call (see "Open decision" below).
- **`see diff` should keep gemma4:26b for now.** qwen3.6:35b-a3b (already on disk as the code tier) and Qwen3-VL-8B each beat it on three cases and lost on three or four. Neither is a clean upgrade.
- **Some jobs belong to scripts, not models.** On counting 23 small dots, finding the odd colour out, and locating a changed grid cell, the deterministic baselines hit every seed and most models missed. That supports building the odd-one-out lane as a measuring tool.
- **Text tiers are fine as they are.** On 14 exact-answer questions, code (qwen3.6) scored 12, big, small and sweep scored 11, and qwen2.5-coder:3b scored 3. sweep (granite) answers about twice as fast as small at the same score.

## Vision: 42 cases, 3 seeds each, 112 checks per model

Every image is generated with a known truth, and every answer is scored by meaning (numbers, colours, cells and negation-aware traps), not by keywords. Each failing cell in the summary below was read before it was counted.

| Model | Runs as | Pass | Median time | Notes |
|---|---|---:|---:|---|
| Qwen3-VL-8B 4-bit | MLX, `see --ui` default | 101 | 3.5 s | best at counting (92%) and reading; no hallucination-trap failures |
| Qwen3.5-9B 4-bit | MLX, pulled for this test | 100 | 5.5 s | ties the 8B, slower, and reasons in circles without answering on one case. Pruned |
| qwen3.6:35b-a3b | Ollama, code tier | 98 | 2.0 s | best at diff localisation (78%) and the real rug odd-one-out; 28 GB resident |
| gemma4:26b | Ollama, big tier, `see diff` default | 97 | 1.5 s | misreads digits in made-up words (4117 for 4417) |
| Qwen3-VL-4B 4-bit | MLX, pulled for this test | 85 | 3.4 s | dominated by the 8B. Pruned |
| gemma4-e4b | Ollama, small tier | 78 | 2.2 s | overcounts by one on every count |
| minicpm-v4.6 | Ollama, plain `see` default | 74 | 1.8 s | falls for false-premise and absent-series questions |

Qwen3.6-27B (16 GB) was planned but not run: Hugging Face downloads were stalling at about 170 KB/s, so its partial download was removed.

Full matrix, capability rollup and crop lift: `probe/vision/REPORT.md`. Per-case winners and losers: `python3 probe/vision/dominance.py <incumbent> <challenger>`.

## Text: 14 exact-answer questions through `q`

| Tier | Model | Pass | Median time |
|---|---|---:|---:|
| code | qwen3.6:35b-a3b | 12 | 0.8 s |
| big | gemma4:26b | 11 | 0.7 s |
| sweep | granite4:tiny-h | 11 | 1.4 s |
| small | gemma4-e4b-warm | 11 | 2.5 s |
| (unused) | qwen2.5-coder:3b | 3 | 1.1 s |

Every model failed the letter count, and most missed that `^a.c$` matches the literal `a.c`. Details: `probe/textcmp/results/`.

## What the run itself fixed

- The memory guard killed big Ollama loads at warn-level pressure for an hour after any MLX call, even with no MLX process alive. It now needs one alive before warn-level pressure counts.
- `see --ui --json` on MLX returned no `.data` when a model wrapped its JSON in a code fence. It now finds the JSON inside.
- Two scorer bugs that failed correct answers on format alone (a mid-line `ANSWER:`, and a toggle given as its own element) were found by reading answers and fixed. `probe/vision/rescore.py` re-judges saved replies without re-running models.

## Open decision

Switch plain `see` reads from minicpm-v4.6 to Qwen3-VL-8B on MLX? It gains 16 cases and loses one seed of one case, and it costs about 2 s more per call plus a fresh model load each time. The default lives in `config.sh` (`VISION_MODEL`).

## How to re-run

```bash
.venv/bin/python probe/vision/gen.py                     # build the fixtures (deterministic)
.venv/bin/python probe/vision/run.py --model <model>     # one model, all cases, seeds 0-2
.venv/bin/python probe/vision/report.py                  # REPORT.md + report.json
python3 probe/textcmp/run.py small sweep big code        # text comparison
```
