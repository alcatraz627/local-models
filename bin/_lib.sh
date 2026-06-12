# _lib.sh — shared helpers for the local-models CLI suite. Source it, never run it.
#
# Everything here earned its place with >=2 real callsites (docs/GOALS.md item 7).
# If a new helper would have one caller, inline it at that callsite instead.

OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
LM_LAUNCHD_LABEL="com.alcatraz.local-models-ollama"

# ── Terminal colors (TTY / NO_COLOR / TERM=dumb aware) ──
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-}" != dumb ]; then
  Y=$'\033[1;33m'; C=$'\033[36m'; G=$'\033[32m'; Dm=$'\033[2m'; Rs=$'\033[0m'; Bd=$'\033[1m'
else Y= C= G= Dm= Rs= Bd= ; fi

# ── Help rendering (conventions/cli-help-design.md) ──
_sec() { printf '\n%s%s%s\n' "$Y" "$1" "$Rs"; }
_cmd() { printf '  %s%-32s%s %s%s%s\n' "$C" "$1" "$Rs" "$Dm" "$2" "$Rs"; }
_opt() { printf '  %s%-32s%s %s%s%s\n' "$G" "$1" "$Rs" "$Dm" "$2" "$Rs"; }
_ex()  { printf '  %s$%s %-44s %s%s%s\n' "$Dm" "$Rs" "$1" "$Dm" "$2" "$Rs"; }
_kv()  { printf '  %s%-9s%s %s\n' "$Dm" "$1" "$Rs" "$2"; }

# ── JSONL history: numbered list + full entry ──
# Entry numbers are stable JSONL line numbers, so `show N` works forever.
jsonl_history() { # LOG N LINE_JQ
  local log="$1" n="$2" fmt="$3"
  [[ "$n" =~ ^[0-9]+$ ]] || n=15
  [ -f "$log" ] || { echo "no history yet ($log)"; return; }
  local total start; total=$(wc -l < "$log" | tr -d ' ')
  start=$(( total - n + 1 )); (( start < 1 )) && start=1
  tail -n "$n" "$log" | jq -r "$fmt" | nl -ba -v "$start" -w4 -s'  '
}
jsonl_entry() { # LOG N ENTRY_JQ ($i is bound to N inside the jq program)
  local log="$1" i="$2" fmt="$3"
  [[ "$i" =~ ^[0-9]+$ ]] || { echo "usage: show <N>   (N from 'history')"; return 1; }
  [ -f "$log" ] || { echo "no history yet"; return 1; }
  local line; line=$(sed -n "${i}p" "$log")
  [ -n "$line" ] || { echo "no entry #$i"; return 1; }
  printf '%s' "$line" | jq -r --arg i "$i" "$fmt"
}

# ── Ollama server + residency ──
ollama_up() { curl -s -m 3 "$OLLAMA_HOST/api/version" >/dev/null 2>&1; }

# True if MODEL is currently resident. keep_alive is last-writer-wins per
# request, so every API caller MUST check this before choosing keep_alive:
# resident -> -1 (preserve the warm pin) · not resident -> 0 (load-and-unload).
# Exact name or name:tag — a bare prefix match would let `q -m gemma4` count the
# resident gemma4-e4b-warm as itself and pin the wrong model forever.
ollama_resident() { ollama ps 2>/dev/null | awk -v m="$1" 'NR>1 && ($1 == m || index($1, m ":") == 1) {f=1} END{exit !f}'; }

server_down_msg() {
  echo "ollama server is DOWN ($OLLAMA_HOST)" >&2
  echo "  start it: launchctl kickstart -k gui/$(id -u)/$LM_LAUNCHD_LABEL" >&2
}
