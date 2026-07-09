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
VISION_MODEL="${VISION_MODEL:-minicpm-v}"

# `see --ui` (the UI-inventory read) routes to the big tier by default: on the
# i-dream dashboard ground-truth test (2026-07-08) gemma4:26b read structure
# minicpm-v kept getting wrong — the actually-selected nav item, region
# proportions, per-element states — while matching its verbatim recall.
# `see -m <model>` still overrides.
UI_VISION_MODEL="${UI_VISION_MODEL:-$BIG_MODEL}"

# Embedder for `lm rag` (local vector index; 274MB, 768-dim, on-demand load).
RAG_EMBED_MODEL="${RAG_EMBED_MODEL:-nomic-embed-text}"
