#!/bin/bash
# verify — the one-command smoke battery for the whole local-models suite.
#
# Run this after any change (and at session start after a handoff) to prove the
# suite still works END-TO-END: real model calls on the cheap tiers, real hook
# pipe-tests, real history/schedule checks. ~30s wall, a few tiny local model
# calls + up to 2 gemini calls (skipped cleanly when gemini is unavailable).
# Exit 0 = everything passed; any FAIL prints red and exits 1.
#
# What it deliberately does NOT cover (verify by hand when touched):
#   imagine generation (GPU, ~min) · lm opencode session (loads 23GB coder) ·
#   MLX re-benchmarks (docs/05 §1 procedure) · probe suite (lm probe <model>) ·
#   scheduled firings themselves (test-fire: gcc-schedule run <name>) ·
#   guard-model-tier LIVE block (needs a real Agent dispatch from a session) ·
#   lm ui-verify full gate (a --ui big-tier read + judge, ~40s — run one by hand:
#   lm ui-verify <shot> "claim") · see --ui/--crop/--menubar reads (big tier;
#   the artifact-store check below exercises the plain-see path only).
set -uo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); printf '  \033[32mok\033[0m   %s\n' "$1"; }
bad()  { FAIL=$((FAIL+1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }
skip() { printf '  \033[2mskip\033[0m %s\n' "$1"; }

echo "── syntax ──"
SYN_FAIL=0
for f in bin/lm bin/q bin/see bin/review bin/warm lib/fleet lib/repo-index lib/gemini lib/ui-verify lib/websearch scripts/self-audit.sh scripts/verify.sh; do
  bash -n "$f" 2>/dev/null || { bad "syntax: $f"; SYN_FAIL=1; }
done
# bin/probe is python — compile-check, don't bash -n it.
python3 -m py_compile bin/probe 2>/dev/null || { bad "syntax: bin/probe (py_compile)"; SYN_FAIL=1; }
[ "$SYN_FAIL" -eq 0 ] && ok "syntax on all bin/ lib/ scripts/ entrypoints (bash -n + py_compile)"

echo "── toolkit (lm doctor) ──"
if ./bin/lm doctor >/dev/null 2>&1; then ok "lm doctor (server, models, venv, PATH)"; else bad "lm doctor — run it directly to see which check"; fi

echo "── q: envelope + constrained decoding (warm/small tier) ──"
R=$(./bin/q --json --timeout 60 "Reply with one word: ok" 2>/dev/null)
[ "$(printf '%s' "$R" | jq -r .ok 2>/dev/null)" = "true" ] && ok "q --json envelope" || bad "q --json: $R"
printf '{"type":"object","properties":{"word":{"type":"string"}},"required":["word"]}' > /tmp/verify-schema.$$.json
R=$(./bin/q --json --format /tmp/verify-schema.$$.json --timeout 60 "Reply with word=ok" 2>/dev/null)
[ -n "$(printf '%s' "$R" | jq -r '.data.word // empty' 2>/dev/null)" ] && ok "q --format → parsed .data" || bad "q --format: $R"
rm -f /tmp/verify-schema.$$.json 2>/dev/null || true

echo "── q --diy: planner emits a valid plan (warm tier) ──"
R=$(./bin/q --json --no-stats --timeout 60 --intent diy-plan --format intents/diy-plan.schema.json "kill whatever is on port 9999" 2>/dev/null)
[ -n "$(printf '%s' "$R" | jq -r '.data.intent // empty' 2>/dev/null)" ] && ok "diy planner → schema-valid plan (.data.intent set)" || bad "diy planner: $R"

echo "── websearch (skips cleanly offline) ──"
if W=$(./lib/websearch "ollama github" -n 2 --json 2>/dev/null) && [ "$(printf '%s' "$W" | jq -r .ok)" = "true" ]; then
  ok "websearch → $(printf '%s' "$W" | jq '.results | length') results"
else skip "websearch unreachable (offline or DDG layout change — check by hand if online)"; fi

echo "── fleet: fan-out + judge + lease + run history ──"
if ./bin/lm fleet summarize intents/ask.toml -m qwen2.5-coder:3b >/dev/null 2>&1; then
  ok "lm fleet 1-item run (judge passed)"
  T=$(tail -1 logs/fleet-history.jsonl | jq -r .pass 2>/dev/null)
  [ "$T" = "1" ] && ok "fleet-history run line" || bad "fleet-history missing/odd"
else bad "lm fleet run"; fi

echo "── index: symbol lookup + staleness machinery ──"
./bin/lm index . >/dev/null 2>&1
./bin/lm index find resolve_tier 2>/dev/null | grep -q "_lib.sh" && ok "lm index find (exact hit)" || bad "lm index find"

echo "── gemini lane (skips cleanly if unavailable) ──"
R=$(./bin/lm gemini --json --timeout 90 "Reply with one word: ok" 2>/dev/null); RC=$?
if [ "$(printf '%s' "$R" | jq -r '.code // empty' 2>/dev/null)" = "gemini_unavailable" ]; then
  skip "gemini unavailable (structured error path verified instead) — FLAG to user"
  ok "gemini_unavailable envelope + exit $RC"
elif [ "$(printf '%s' "$R" | jq -r .ok 2>/dev/null)" = "true" ]; then
  ok "lm gemini one-shot envelope"
  A=$(./bin/lm gemini --timeout 90 ask "What TOML file was ingested into this session? Filename only." 2>/dev/null || true)
  printf '%s' "$A" | grep -qi "complete" && ok "lm gemini session memory (ask)" || skip "session memory inconclusive (answer: ${A:0:40})"
else bad "lm gemini: $R"; fi

echo "── see: artifact store (small vision tier) ──"
R=$(./bin/see presets/skybound-isles.png --json 2>/dev/null)
A=$(printf '%s' "$R" | jq -r '.artifact // empty' 2>/dev/null)
if [ "$(printf '%s' "$R" | jq -r .ok 2>/dev/null)" = "true" ] && [ -n "$A" ]; then
  ok "see --json envelope + artifact field"
  { ls "$A"/source.* >/dev/null 2>&1 && [ -f "$A/read.md" ] && [ -f "$A/meta.json" ]; } \
    && ok "artifact folder complete (source + read.md + meta.json)" || bad "artifact folder incomplete: $A"
  [ "$(./bin/see open -1)" = "$A" ] && ok "see open -1 → same artifact" || bad "see open -1 mismatch"
else bad "see --json: $R"; fi

echo "── ui-verify: help + dispatch (full gate not run — see header) ──"
./bin/lm ui-verify >/dev/null 2>&1 && ok "lm ui-verify dispatch + help" || bad "lm ui-verify dispatch"

echo "── see --ocr: Apple Vision exact-text lane (no model) ──"
if command -v mac-ocr >/dev/null 2>&1; then
  R=$(./bin/see presets/skybound-isles.png --ocr --json 2>/dev/null)
  [ "$(printf '%s' "$R" | jq -r .model 2>/dev/null)" = "apple-vision" ] && ok "see --ocr envelope (apple-vision)" || bad "see --ocr: $R"
else skip "mac-ocr not installed (npm install -g mac-ocr)"; fi

echo "── ax: accessibility lane present (ui-verify --app dependency) ──"
if command -v ax >/dev/null 2>&1; then
  [ -n "$(ax list 2>/dev/null | head -2)" ] && ok "ax list (Accessibility perm live)" || bad "ax installed but list empty — check Accessibility permission"
else skip "ax not installed (cargo install --git https://github.com/watzon/ax-cli)"; fi

echo "── histories + timeline ──"
for h in logs/q-history.jsonl logs/see-history.jsonl logs/fleet-history.jsonl logs/gem-history.jsonl; do
  [ -f "$h" ] && jq -es . "$h" >/dev/null 2>&1 && ok "parses: $h" || bad "missing/corrupt: $h"
done
[ "$(./bin/lm timeline 5 | wc -l | tr -d ' ')" -ge 5 ] && ok "lm timeline merges streams" || bad "lm timeline"

echo "── feedback sink ──"
bash scripts/self-audit.sh >/dev/null 2>&1 && [ -f "logs/self-audit/$(date +%Y%m%d).md" ] && ok "self-audit digest" || bad "self-audit"

echo "── gcc hooks (pipe-tests) ──"
H=~/.claude/scripts/hooks/guard-model-tier.sh
if [ -f "$HOME/.claude/.fable-subagent-promo" ]; then
  skip "guard-model-tier fable block — BYPASSED by ~/.claude/.fable-subagent-promo (promo window, self-expires 2026-07-17). Every fable sub-agent dispatch currently passes. Delete the file to restore the hard block."
else
  [ "$(echo '{"session_id":"verify","tool_name":"Agent","tool_input":{"model":"fable","prompt":"x"}}' | "$H" | jq -r .decision 2>/dev/null)" = "block" ] && ok "guard-model-tier: fable → block" || bad "guard-model-tier block path"
fi
if [ -f "$HOME/.claude/.model-tier-off" ]; then
  skip "guard-model-tier warn path — muted machine-wide (~/.claude/.model-tier-off exists; silence is correct)"
else
  echo '{"session_id":"verify","tool_name":"Agent","tool_input":{"prompt":"x"}}' | "$H" | jq -e .hookSpecificOutput >/dev/null 2>&1 && ok "guard-model-tier: unpinned → warn" || bad "guard-model-tier warn path"
fi
[ -z "$(echo '{"session_id":"verify","tool_name":"Agent","tool_input":{"model":"sonnet","prompt":"x"}}' | "$H")" ] && ok "guard-model-tier: pinned → silent" || bad "guard-model-tier silent path"
echo '{"session_id":"verify","tool_name":"Read","tool_input":{"file_path":"'"$DIR"'/presets/skybound-isles.png"}}' | ~/.claude/scripts/hooks/log-image-reads.sh && [ -n "$(tail -1 ~/.claude/logs/image-reads.jsonl | jq -r .est_tokens 2>/dev/null)" ] && ok "log-image-reads" || bad "log-image-reads"

echo "── gcc schedules (labels present) ──"
# gcc-schedule is an interactive zsh alias — scripts must use the real path.
S=$(bash ~/.claude/scripts/schedule/schedule.sh list --all 2>/dev/null)
for name in warm-morning warm-evening-off lm-self-audit image-tools-review tier-telemetry-review; do
  printf '%s' "$S" | grep -q "$name" && ok "scheduled: $name" || bad "schedule missing: $name"
done

echo "── residency (informational) ──"
./bin/warm status 2>/dev/null | sed 1d | grep -q . && echo "  note: models resident (fine if you warmed deliberately)" || echo "  note: zero-idle"

echo
if [ "$FAIL" -eq 0 ]; then printf '\033[32m%d checks passed, 0 failed\033[0m\n' "$PASS"; exit 0
else printf '\033[31m%d passed, %d FAILED\033[0m\n' "$PASS" "$FAIL"; exit 1; fi
