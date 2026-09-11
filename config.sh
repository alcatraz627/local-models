# Local-models V1 config — sourced by bin/* scripts.
# One place to change which model is the warm companion and how it behaves.

# Model size tiers — `q -m <alias>` / `q --big` resolve these; any other -m
# value is passed through literally. All on-demand-loaded except the warm small.
#   small = the warm companion (snappy, default)   big = heavier MoE for reasoning
#   code  = coding/tool-use specialist             (chosen for fast MoE shapes, not
# dense — this 307GB/s machine is bandwidth-bound; see docs/03 + the model-tiers research)
WARM_MODEL="${WARM_MODEL:-gemma4-e4b-warm}"   # = small
BIG_MODEL="${BIG_MODEL:-gemma4:26b}"          # MoE (3.8B active): ~30-45 tok/s, best prose + long-ctx
CODE_MODEL="${CODE_MODEL:-qwen3.6:35b-a3b}"   # MoE: strongest local tool-calling + coding

# -1 = stay resident until `warm off` (never auto-unload). This is the whole
# point of the toggle: residency is a deliberate choice, not a timer.
WARM_KEEP_ALIVE="-1"

OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"

# Toolkit version — reported by `lm status --json` (api_version covers the
# machine contract separately; bump that only on breaking changes).
LM_VERSION="1.1"

# Default image-gen model for `imagine` (override per call with `imagine -m <name>`).
# Registry names: schnell (fast) · flux2 (balanced) · qwen (best text) · dev · or any HF repo.
IMAGINE_MODEL="${IMAGINE_MODEL:-qwen}"   # quality-first default; schnell dropped (speed not valued for images) — `imagine -m schnell` re-pulls it

# Local vision model for `see` (read images/screenshots → text).
# minicpm-v (~5.5GB, ollama-native): OCR-strong default. On a 4-screenshot fidelity
# test against native-vision ground truth (claude-instances) it transcribed verbatim
# text/commands/counts that gemma4:26b MISSED ("reads the shape, not the words"), with
# no hallucinated controls. Trade-off: gemma4:26b (17GB) is the stronger general-scene
# reasoner — use `see -m gemma4:26b` for that. (qwen3-vl image path hangs in ollama #16264.)
VISION_MODEL="${VISION_MODEL:-minicpm-v4.6}"   # swapped 2026-09-11: 4.6 beats minicpm-v on UI structure (read ACTIVE 43/DONE 97 the old one missed), hallucinates nothing, at 1.6GB vs 5.5GB. Evidence: .claude/output/20260911-model-survey/case1a-minicpm46.md. Old minicpm-v kept installed as fallback.

# Ollama model for structure-heavy vision. Since 2026-09-12 `see --ui` uses this ONLY
# when UI_DEFAULT_MLX=0; by default --ui routes to the MLX Qwen3-VL model (below).
# `see diff` still uses this for its structure read. gemma4:26b was measured better at
# structure/state than minicpm-v on the 2026-07-08 dashboard test. `see -m` overrides.
UI_VISION_MODEL="${UI_VISION_MODEL:-$BIG_MODEL}"

# MLX-VLM vision model for `see --mlx` / `see -m mlx:<repo>` — a higher-accuracy UI
# path that runs OUTSIDE ollama via mlx-vlm (installed in .venv). Qwen3-VL-8B tied
# gemma4:26b perfectly on UI-structure fixtures at ~6GB vs 17GB (2026-09-11 survey,
# .claude/output/20260911-model-survey/). Ollama's Qwen3-VL path is broken on Apple
# Silicon (#16264), so MLX-VLM is the required runtime. Loads fresh each call (no
# keep_alive); NEVER run it while a big ollama model is resident — that combo OOM'd
# the machine once. scripts/mem-guard.py guards against it.
UI_VISION_MLX="${UI_VISION_MLX:-mlx-community/Qwen3-VL-8B-Instruct-4bit}"

# Route a plain `see --ui` (no explicit -m) through the MLX Qwen3-VL model by default,
# so the common UI-read path does NOT load the 17GB gemma4:26b tier (memory reclaim,
# owner 2026-09-12). `see diff` still uses UI_VISION_MODEL. Set UI_DEFAULT_MLX=0 to
# revert `see --ui` to the ollama UI_VISION_MODEL.
UI_DEFAULT_MLX="${UI_DEFAULT_MLX:-1}"

# Sweep/grunt model for high-throughput batch work (lm fleet). granite4:tiny-h is
# ~1.5x faster than the warm companion (1B active), but chatty as a free agent — only
# trustworthy behind constrained decoding + the fleet Judge gate (2026-09-11 survey).
SWEEP_MODEL="${SWEEP_MODEL:-granite4:tiny-h}"

# Embedder for `lm rag` (local vector index; 274MB, 768-dim, on-demand load).
RAG_EMBED_MODEL="${RAG_EMBED_MODEL:-nomic-embed-text}"
