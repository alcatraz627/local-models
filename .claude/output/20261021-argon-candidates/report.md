# Gemini 4 Argon trial and local candidate revision

2026-10-21. The Argon tests ran from the scratchpad scripts `argon_probe.py` and `argon_sweep.py`.

## Gemini 4 Argon

| Test | gemini-4-argon | gemini-3.8-flash |
|---|---|---|
| Fake-paper trap | refused, named the likely real paper | refused |
| Bat-and-ball variant | $1.20, correct (20.7s) | $1.20, correct (3.6s) |
| Strict JSON | clean | clean |
| 170K-token repo sweep (needle, absent-fact trap, 5 config facts) | 7/7, 8.4s | 7/7, 11.1s |
| Through `lm gemini` (gemini-cli 0.46, plan mode) | works, 16s | in use |

Argon costs $4 in and $20 out per million tokens, so the sweep cost about $0.68, several times Flash's cost for the same score. Independent reporting gives it the lowest hallucination rate among top-scoring models. The key reports a 32K output cap; the docs say 65K. These tests are too easy to separate the two models. A harder test would be a contradiction hunt over about 500K tokens (roughly $2-3).

Pick-list change in `config.sh` and `lib/gemini`: now `gemini-3.8-flash gemini-3.5-flash gemini-4-argon`. `gemini-3.8-pro` and `gemini-3.5-pro` were removed because the key does not list them.

## Local candidates

The footprint is 114 GB (53 GB Ollama, 61 GB HF), so about 36 GB is free under the 150 GB target. The evidence comes from secondary sources, so each candidate still has to pass its real gate on this machine.

| Tier | Current model | Candidate | Note |
|---|---|---|---|
| CODE_MODEL | qwen3.6:35b-a3b | hold | Qwen3.8-27B scores lower on coding (61.7 vs 73.8, directional only); dense runs slower on this bandwidth |
| BIG_MODEL | gemma4:26b | Qwen3.8-27B | strong agentic scores, Apache 2.0; probe at temperature 0 and 0.7 |
| UI_VISION_MLX | Qwen3-VL-8B | MiMo-V2.6-Distill-Qwen-9B | September release, MIT licence; test on harder `--ui` fixtures |
| document OCR | Apple Vision | PaddleOCR-VL-1.6 / GLM-OCR (~1B) | top of OmniDocBench; add only if Apple Vision falls short |
| SWEEP_MODEL | granite4:tiny-h | Nemotron 3.5 Bolt / MiniCPM5-2B | held to the same fleet output checks |
| embedder | nomic, qwen3-embedding:0.6b | embeddinggemma-2:740m | low priority, the RAG lane is archived |
| prune | | gemma4:e4b-it-qat | 6 GB; looks redundant with the warm model. NOT qwen2.5-coder:3b: lm fleet used it 49 times Jul to Oct |

## Suite

`verify.sh` passed 38 checks and failed 4. All gemini checks passed. The 4 failures are outside the pick-list's only two readers:

- vis battery case F6
- the guard-model-tier block path
- the `warm-morning` schedule is missing
- `warm-evening-off` is not loaded in launchd

## Round 2 (same day)

### BIG_MODEL usage, measured from logs/*-history.jsonl

| Month | text calls (q) | vision calls (see --ui, see diff) |
|---|---|---|
| Jul | 772 (probe and bench runs) | 80 |
| Aug | 1 | 15 |
| Sep | 6 | 5 |
| Oct | 0 | 5 |

For text it is idle. Its only live job is `see diff` (UI_VISION_MODEL defaults to BIG_MODEL), which the Affinity vision helper's diff route calls. Retiring it means repointing the following:

- `see diff` and the non-MLX `see --ui`, through UI_VISION_MODEL
- `imagine critique` (bin/imagine:288 hardcodes it)
- the `lm ui-verify` escalation retry (lib/ui-verify:159 calls q --big)
- `lm gemini --fallback-local` (lib/gemini:296)
- `q --big`, the diy planner's big tier, and `lm rag --big`

Argon listed these; 20 of 25 of its file:line citations were exact.

### Argon as ideator

Argon wrote the test plan from a 70K-character context pack in 313s.

- It grounded the plan in real paths: every fixture it named exists.
- Its candidates are real but older (2024-25): Qwen2.5-VL-7B, Pixtral-12B, granite-docling-258M, FLUX.1-Kontext-dev, FLUX.1-Fill-dev, RMBG-2.0 and Real-ESRGAN. It did not know the September releases.
- Its claim that Qwen2.5-VL is better at sharp tips is untested.

Verdict: a useful second seat for planning and breadth, like the GPT-6 seats. Every citation and model claim still needs a check before it drives work.

Worth testing from its list, because they add jobs the toolkit lacks:

- instruction-based image edit (Kontext; mflux already ships qwen-edit, so try that first at zero download)
- background removal (RMBG-2.0, non-commercial licence)
- 4x upscale before a crop read (Real-ESRGAN)
- document layout parsing (granite-docling)

### Affinity: where a local model helps and where it does not

Test: the rug-border-twelve-motifs fixture, where motif 9 of 12 is taller and leans.

- minicpm-v4.6 (the helper's default) answered motif 3.
- Qwen3-VL-8B via MLX answered motif 6.
- Both are wrong.

A model-free column-profile script (scratchpad odd_one_out.py) found motif 9 by measurement: its top edge sits 17 px higher and it is 23 px wider. It also flagged motifs 3 to 5 as unreliable, because the pink band covers them; that occlusion still splits one motif in two, so the script is a prototype.

Recommendation: for "make these uniform" requests, the Affinity guard should measure (scripts) and use the vision model only to describe. That is this repo's rule, "scripts measure, models judge". A see-side odd-one-out lane would serve it. Not built yet.

## Sources

- https://ai.google.dev/gemini-api/docs/models/gemini-4-argon
- https://www.deeplearning.ai/the-batch/argon-a-low-hallucination-model-build-for-knowledge-work
- https://www.eesel.ai/de/blog/gemini-4-argon-test
- https://llmgateway.io/models/gemini-4-argon
- https://benchlm.ai/compare/qwen3-6-35b-a3b-vs-qwen3-8-27b
- https://jacar.es/en/open-models-september-2026/
- https://pasqualepillitteri.it/en/news/24368/best-open-weight-models-october-2026-compared
- https://blog.roboflow.com/best-open-source-ocr-models/
