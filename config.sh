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
IMAGINE_MODEL="${IMAGINE_MODEL:-schnell}"
