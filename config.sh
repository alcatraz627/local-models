# Local-models V1 config — sourced by bin/* scripts.
# One place to change which model is the warm companion and how it behaves.

# Tier W: the small model kept warm for the snappy companion path.
# A derived model (see modelfiles/) with num_ctx pinned small so its KV-cache
# footprint stays tiny even while resident.
WARM_MODEL="${WARM_MODEL:-gemma4-e4b-warm}"

# -1 = stay resident until `warm off` (never auto-unload). This is the whole
# point of the toggle: residency is a deliberate choice, not a timer.
WARM_KEEP_ALIVE="-1"

OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"

# Default image-gen model for `imagine` (override per call with `imagine -m <name>`).
# Registry names: schnell (fast) · flux2 (balanced) · qwen (best text) · dev · or any HF repo.
IMAGINE_MODEL="${IMAGINE_MODEL:-schnell}"
