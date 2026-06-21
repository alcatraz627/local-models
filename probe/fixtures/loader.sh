# (excerpt from bin/q) — intents are data, loaded per call via yq.
INTENT_DIR="$DIR/intents"
intent_exists()    { [ -f "$INTENT_DIR/$1.toml" ]; }
intent_sys()       { yq -p toml -r '.system_prompt // ""' "$INTENT_DIR/$1.toml" 2>/dev/null; }
intent_needs_ctx() { [ "$(yq -p toml -r '.needs_ctx // false' "$INTENT_DIR/$1.toml" 2>/dev/null)" = true ]; }

# HOT PATH: a plain `q "..."` resolves intent=ask, then runs:
#   intent_needs_ctx "$INTENT"   (1 yq read)
#   intent_sys "$INTENT"         (1 yq read)
# i.e. 2 yq reads per call. The snappy path is a hard project goal — keep it cheap.
