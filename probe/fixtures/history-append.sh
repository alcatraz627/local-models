#!/bin/bash
# history-append.sh: parallel writers to one history file must each leave a whole row.
#
# The histories are what agents read back, so a row cut in two by another writer
# breaks every reader. Eight writers each append 25 rows of about 12 KB through
# jsonl_append; the file must then hold 200 rows that all parse. Needs no model.
set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$DIR/bin/_lib.sh"
F="$(mktemp -t history-append)"
BIG="$(head -c 9000 /dev/zero | tr '\0' 'x')"
writer() {
  local i
  for i in $(seq 1 25); do
    jq -cn --argjson w "$1" --argjson i "$i" --arg r "$BIG" '{w:$w, i:$i, response:$r, tail:"end"}' | jsonl_append "$F"
  done
}
for w in 1 2 3 4 5 6 7 8; do writer "$w" & done
wait
python3 - "$F" <<'PY'
import json, sys
rows = bad = 0
for raw in open(sys.argv[1], "rb").read().split(b"\n"):
    if not raw.strip():
        continue
    rows += 1
    try:
        row = json.loads(raw)
        assert row["tail"] == "end" and len(row["response"]) == 9000
    except Exception:
        bad += 1
ok = rows == 200 and bad == 0
print(f"history-append: {rows} rows, {bad} broken ({'ok' if ok else 'FAIL'}: 200 whole rows needed)")
sys.exit(0 if ok else 1)
PY
rc=$?
trash "$F" 2>/dev/null || true
exit $rc
