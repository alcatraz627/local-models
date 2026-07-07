#!/bin/bash
# Weekly self-audit — the feedback sink for the local-model suite (docs/07 §2.4).
#
# Mines the last 7 days of every history stream (q, see, fleet, imagine) into a
# small digest a human can skim: volume, failure codes by model, latency, fleet
# pass rates. If one failure code recurs enough to look structural (>=5 hits),
# it files ONE proposal into the gcc backlog for human triage — it never fixes,
# tunes, or retries anything itself (propose, never seize).
#
# Scheduled weekly via gcc-schedule (lm-self-audit, Sun 11:00); run by hand any time.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS="$DIR/logs"
OUT_DIR="$LOGS/self-audit"
mkdir -p "$OUT_DIR"
CUTOFF="$(date -u -v-7d +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ)"
TODAY="$(date +%Y%m%d)"
DIGEST="$OUT_DIR/$TODAY.md"

# Recent slice of a JSONL (ts >= cutoff); missing file = empty stream.
recent() { [ -f "$1" ] && jq -c --arg c "$CUTOFF" 'select(.ts >= $c)' "$1" 2>/dev/null || true; }

Q=$(recent "$LOGS/q-history.jsonl")
SEE=$(recent "$LOGS/see-history.jsonl")
FLEET=$(recent "$LOGS/fleet-history.jsonl")
IMAGINE=$(recent "$DIR/outputs/imagine-history.jsonl")

count() { [ -n "$1" ] && printf '%s\n' "$1" | wc -l | tr -d ' ' || echo 0; }

{
  echo "# lm self-audit — $(date +%Y-%m-%d) (last 7 days)"
  echo
  echo "| stream | calls | failures |"
  echo "|---|---|---|"
  echo "| q | $(count "$Q") | $(printf '%s\n' "$Q" | jq -s '[.[] | select(.error)] | length') |"
  echo "| see | $(count "$SEE") | — |"
  echo "| fleet runs | $(count "$FLEET") | $(printf '%s\n' "$FLEET" | jq -s '[.[] | select(.fail > 0)] | length') runs w/ fails |"
  echo "| imagine | $(count "$IMAGINE") | — |"
  echo
  echo "## q failures by code × model"
  printf '%s\n' "$Q" | jq -rs '[.[] | select(.error)] | group_by(.error + "|" + .model)
    | map("- \(.[0].error) × \(length)  (\(.[0].model))") | .[]' 2>/dev/null || echo "- none"
  echo
  echo "## q latency by model (avg ms, successful calls)"
  printf '%s\n' "$Q" | jq -rs '[.[] | select(.error | not)] | group_by(.model)
    | map("- \(.[0].model): \((map(.ms) | add / length) | round)ms × \(length)") | .[]' 2>/dev/null || echo "- none"
  echo
  echo "## fleet pass rates"
  printf '%s\n' "$FLEET" | jq -rs 'map("- \(.ts[0:10]) \(.intent) ×\(.items) → \(.pass)✓/\(.fail)✗ (\(.model), \(.wall_s)s)") | .[]' 2>/dev/null || echo "- none"
  echo
  echo "_Streams: logs/q-history.jsonl · logs/see-history.jsonl · logs/fleet-history.jsonl · outputs/imagine-history.jsonl_"
} > "$DIGEST"

echo "digest: $DIGEST"

# Structural-failure gate: one recurring code (>=5 hits in a week) is a pattern,
# not noise — hand it to the human via the gcc proposals backlog, once.
TOP=$(printf '%s\n' "$Q" | jq -rs '[.[] | select(.error)] | group_by(.error + "|" + .model)
  | map({k: (.[0].error + " on " + .[0].model), n: length}) | sort_by(-.n) | .[0] // empty
  | select(.n >= 5) | "\(.k) × \(.n)"' 2>/dev/null || true)
if [ -n "$TOP" ]; then
  bash ~/.claude/scripts/propose.sh add \
    --title "lm self-audit: recurring failure — $TOP (last 7d)" \
    --body "Weekly lm self-audit found a structural failure pattern: $TOP. Digest: $DIGEST. Consider a probe re-run, timeout tuning, or model swap — human call." \
    --category other --effort small \
    --tags "src:lm-self-audit" >/dev/null 2>&1 || true
  echo "proposal filed: $TOP"
fi
