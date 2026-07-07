#!/bin/bash
# Conductor helper for the finish-a-codebase exercise: assemble deterministic
# context for ONE file, call the local coder via q, strip any markdown fences,
# and save the candidate. The Judge (pytest) runs separately — gate each step.
# Usage: [FEEDBACK=<file>] conduct-complete.sh <workdir> <file-to-complete> <sibling>...
# FEEDBACK: optional file of Judge output appended to the context (retry round).
set -euo pipefail
WORK="$1"; TARGET="$2"; shift 2

CTX="$(
  echo "=== FILE TO COMPLETE: $TARGET ==="
  cat "$WORK/$TARGET"
  if [ -n "${FEEDBACK:-}" ]; then
    echo ""
    echo "=== JUDGE FAILURE on your previous attempt (fix the code so this passes) ==="
    cat "$FEEDBACK"
  fi
  for s in "$@"; do
    echo ""
    echo "=== SIBLING (context only, do not output): $s ==="
    cat "$WORK/$s"
  done
  echo ""
  echo "=== TESTS (the spec): tests/test_csvstats.py ==="
  cat "$WORK/tests/test_csvstats.py"
)"

RESP="$(printf '%s' "$CTX" | q complete --json --ctx - -m code --timeout 420)"
echo "$RESP" | jq -e '.ok == true' >/dev/null || { echo "worker failed:"; echo "$RESP" | jq .; exit 1; }

# Models sometimes fence the output anyway; stripping is the conductor's job.
echo "$RESP" | jq -r .text \
  | sed -e '1{/^```/d;}' -e '${/^```$/d;}' \
  > "$WORK/$TARGET.candidate"

echo "$RESP" | jq -c '{model, ms, tokens_in, tokens_out}' >&2
wc -l "$WORK/$TARGET.candidate" >&2
