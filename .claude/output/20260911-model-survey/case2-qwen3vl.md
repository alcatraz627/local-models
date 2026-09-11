# Case 2: Qwen3-VL-8B (MLX-VLM) vs gemma4:26b for `see --ui`

- Date: 2026-09-11. Candidate: Qwen3-VL-8B-Instruct-4bit via MLX-VLM (~6 GB, new runtime).
  Incumbent: gemma4:26b (17 GB, current UI_VISION_MODEL). Also in frame: minicpm-v4.6 (1.6 GB).
- Runtime: mlx-vlm 0.7.0 installed into the project .venv (via uv; no pip in the venv).
  Qwen3-VL runs standalone, NOT through `see` (which is Ollama-only). Ollama's Qwen3-VL
  path is still blocked on Apple Silicon (#16264), so MLX-VLM is the required path.
- Footprint: +~6 GB to the HF cache. Runs verified one-model-at-a-time under the mem-guard
  daemon after a parallel load OOM-killed the machine earlier (see mem-guard note below).

## Acceptance criterion
Beat gemma4:26b on UI-structure facts (selected item, states, counts) with zero
hallucinated elements. A clear win justifies the new MLX-VLM runtime dependency.

## Results (hand-labeled ground truth)

FX-UI-1 kanban (INBOX 0, BACKLOG 0, ACTIVE 43, BLOCKED 0, DONE 97):
- Qwen3-VL-8B: 5/5 exact, including BLOCKED's 0.
- gemma4:26b: 5/5 exact.
- minicpm-v4.6: 4.5/5 (fumbled BLOCKED's 0 as the body placeholder).

FX-UI-2 settings badges (Jobs 2, Active parts 8, Unlisted parts 6, Error management 12):
- Qwen3-VL-8B: 4/4 exact, zero hallucinations.
- gemma4:26b: 4/4 exact, zero hallucinations.
- minicpm-v4.6: 3/4 (missed Jobs 2), zero hallucinations.

## Verdict

TIE at lower cost, not a clear win on this evidence. Qwen3-VL-8B matched gemma4:26b
perfectly on both fixtures at roughly a third of the memory (6 GB vs 17 GB). It did not
*beat* the incumbent here, because both models scored 100% and my two fixtures were not
hard enough to separate them. The survey's benchmark case (94.4% ScreenSpot for Qwen3-VL
vs no UI-grounding score for gemma4:26b) predicts a gap on harder UI-grounding tasks;
I did not reproduce that gap, so I do not claim it.

Recommendation: Qwen3-VL-8B is a viable lower-memory replacement for gemma4:26b in the
`see --ui` role, worth the MLX-VLM integration IF the goal is to reclaim the 17 GB big
model from the vision role. But the integration is real work (a new backend path in `see`,
which is Ollama-only today), and the win on current evidence is memory, not accuracy. So:
build the integration and re-test on harder fixtures (ambiguous selection states, partial
highlights, dense tables) before swapping. Do not swap on two perfect-score fixtures alone.

Pragmatic near-term: minicpm-v4.6 (already Ollama-native, 1.6 GB) covers most UI reads at
4.5/5 and 3/4 with no integration work. It is the cheap default; Qwen3-VL-8B is the accuracy
ceiling that needs plumbing.

## mem-guard note
The earlier parallel run (mlx-vlm + gemma4:26b at once) exhausted unified memory and the
kernel jetsam killer took down every agent on the machine. Fix: `scripts/mem-guard.py`
daemon (threshold 10 GB available, kills the largest model process before jetsam fires,
never targets agent processes, logs to logs/mem-guard.jsonl), plus a strict one-heavy-model-
at-a-time discipline. All Stage 2 runs after that were sequential and clean.
