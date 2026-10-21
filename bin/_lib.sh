# _lib.sh — shared helpers for the local-models CLI suite. Source it, never run it.
#
# Everything here earned its place with >=2 real callsites (docs/GOALS.md item 7).
# If a new helper would have one caller, inline it at that callsite instead.

OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
LM_LAUNCHD_LABEL="com.alcatraz.local-models-ollama"

# launchd hands scheduled jobs a bare PATH (/usr/bin:/bin:/usr/sbin:/sbin), so a
# bare `ollama`/`hf` dies with exit 127 there. Sourcing this file is the fix:
# every bin/* script sources _lib.sh before its first tool call.
case ":$PATH:" in *:/opt/homebrew/bin:*) ;; *) PATH="/opt/homebrew/bin:$PATH" ;; esac

# ── Terminal colors (TTY / NO_COLOR / TERM=dumb aware) ──
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-}" != dumb ]; then
  Y=$'\033[1;33m'; C=$'\033[36m'; G=$'\033[32m'; Dm=$'\033[2m'; Rs=$'\033[0m'; Bd=$'\033[1m'
else Y= C= G= Dm= Rs= Bd= ; fi
# The same palette for text written to STDERR, decided by stderr's own TTY: the set above
# follows stdout, so using it on a stderr line leaked escape codes into redirected logs.
if [ -t 2 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-}" != dumb ]; then
  eY=$'\033[1;33m'; eC=$'\033[36m'; eDm=$'\033[2m'; eRs=$'\033[0m'; eRed=$'\033[31m'
else eY= eC= eDm= eRs= eRed= ; fi

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
jsonl_entry() { # LOG N ENTRY_JQ ($i bound to N in jq). N>0 = stable line no; N<0 counts from the end (-1 = latest)
  local log="$1" i="$2" fmt="$3"
  [ -f "$log" ] || { echo "no history yet"; return 1; }
  local total; total=$(wc -l < "$log" | tr -d ' ')
  [[ "$i" =~ ^-[0-9]+$ ]] && i=$(( total + i + 1 ))   # -1 -> latest, -2 -> second-latest
  [[ "$i" =~ ^[0-9]+$ ]] && (( i >= 1 )) || { echo "usage: show <N>   (N from 'history', or -1 for the latest)"; return 1; }
  local line; line=$(sed -n "${i}p" "$log")
  [ -n "$line" ] || { echo "no entry #$i"; return 1; }
  printf '%s' "$line" | jq -r --arg i "$i" "$fmt"
}

# ── Shared arg-parse helpers: same messages and exit code (2) in every tool ──
# A flag that takes a value must have one; without this `shift 2` fails under
# set -e and the tool exits 1 with no message at all.
need_arg() { # TOOL FLAG [VALUE]
  [ "$#" -ge 3 ] && [ -n "${3:-}" ] || {
    printf '%s: %s needs a value\n' "$1" "$2" >&2
    exit 2
  }
}

# Call from the parser's catch-all branch. Only a flag-shaped word (-x, --xyz)
# is refused; "-", "-1" and prompts with spaces ("- fix this") stay positionals.
reject_unknown_flag() { # TOOL ARG
  if [[ "$2" =~ ^--?[A-Za-z][A-Za-z0-9_-]*$ ]]; then
    printf "%s: unknown flag '%s' (run %s -h to list flags); use -- before a prompt that starts with -\n" "$1" "$2" "$1" >&2
    exit 2
  fi
}

# Closest candidate to WORD by edit distance, printed only when it is a plausible
# typo (1 edit for short words, 2 for words of 7+ letters). Prints nothing otherwise.
did_you_mean() { # WORD CANDIDATE...
  local w="$1"; shift
  printf '%s\n' "$@" | awk -v w="$w" '
    function lev(a, b,   i, j, la, lb, d, c, m) {
      la = length(a); lb = length(b)
      for (i = 0; i <= la; i++) d[i, 0] = i
      for (j = 0; j <= lb; j++) d[0, j] = j
      for (i = 1; i <= la; i++) for (j = 1; j <= lb; j++) {
        c = (substr(a, i, 1) == substr(b, j, 1)) ? 0 : 1
        m = d[i-1, j] + 1
        if (d[i, j-1] + 1 < m) m = d[i, j-1] + 1
        if (d[i-1, j-1] + c < m) m = d[i-1, j-1] + c
        d[i, j] = m
      }
      return d[la, lb]
    }
    BEGIN { lim = (length(w) >= 7) ? 2 : 1; best = lim + 1 }
    { n = lev(w, $0); if (n < best) { best = n; pick = $0 } }
    END { if (best <= lim) print pick }'
}

# Local wall-clock time for a history entry's UTC .ts, as MM-DD HH:MM. Use inside jq.
JQ_LOCAL_TS='def lts: (try (fromdateiso8601 | strflocaltime("%m-%d %H:%M")) catch "?");'

jsonl_history_json() { # LOG N
  local log="$1" n="$2"
  [[ "$n" =~ ^[0-9]+$ ]] || n=15
  [ -f "$log" ] || { printf '[]\n'; return; }
  local total start
  total=$(wc -l < "$log" | tr -d ' ')
  start=$(( total - n + 1 )); (( start < 1 )) && start=1
  tail -n "$n" "$log" | jq -c --argjson start "$start" 'input_line_number as $i | . + {n: ($start + $i - 1)}'
}

use_color_fd() { # FD
  [ -z "${NO_COLOR:-}" ] && [ "${TERM:-}" != dumb ] && [ -t "$1" ]
}

# ── Size-tier aliases → real model names ──
# `-m small|big|code|sweep` resolves via config.sh; any other value passes
# through literally, so `-m llama3.2` still works. Those four words are
# reserved — a model literally named one of them needs its full name:tag.
# sweep = the high-throughput grunt tier (granite4:tiny-h), for lm fleet.
resolve_tier() {
  case "$1" in
    small) echo "${WARM_MODEL:-gemma4-e4b-warm}" ;;
    big)   echo "${BIG_MODEL:-gemma4:26b}" ;;
    code)  echo "${CODE_MODEL:-qwen3.6:35b-a3b}" ;;
    sweep) echo "${SWEEP_MODEL:-granite4:tiny-h}" ;;
    *)     echo "$1" ;;
  esac
}

# Expand a leading ~ / ~/ in a path arg. The shell only expands ~ when it is
# UNQUOTED, so a quoted "~/shot.png" reaches the tool literal and fails "no such
# file" — the backslash-escape workaround exists only because quotes suppress the
# expansion. Every path-taking command runs its file args through this.
expand_tilde() {
  case "$1" in
    "~")   printf '%s\n' "$HOME" ;;
    "~/"*) printf '%s\n' "$HOME/${1#\~/}" ;;
    *)     printf '%s\n' "$1" ;;
  esac
}

# Terse tagged progress to stderr: "[HH:MM:SS tag] msg". For a human watching a slow
# call (a cold model load shows nothing for seconds otherwise) and for an agent that
# opts in. On when stderr is a TTY, or LM_PROGRESS=1 for captured callers (Claude);
# LM_QUIET=1 forces off. stderr only, so it never pollutes a --json stdout.
lm_step() {
  { [ -t 2 ] || [ -n "${LM_PROGRESS:-}" ]; } || return 0
  [ -n "${LM_QUIET:-}" ] && return 0
  # Colour follows stderr, not stdout: Dm was decided from stdout's TTY above.
  local dm="" rs=""; use_color_fd 2 && { dm=$'\033[2m'; rs=$'\033[0m'; }
  printf '%s[%s %s]%s %s\n' "$dm" "$(date +%H:%M:%S)" "$1" "$rs" "$2" >&2
}

# ── Ollama server + residency ──
ollama_up() { curl -s -m 3 "$OLLAMA_HOST/api/version" >/dev/null 2>&1; }

# The `ollama` CLI. On macOS a bare `ollama ps` with no server up launches
# Ollama.app, whose own server ignores lm-serve's policy and never goes away, so
# every CLI call goes through here and simply fails while the server is down.
ollama_cli() { ollama_up || return 1; ollama "$@"; }

# Start our server if it is not running, for callers about to use a model. It
# stops itself after a few idle minutes (bin/lm-serve), so this is cheap to call.
ollama_ensure() {
  ollama_up && return 0
  launchctl kickstart "gui/$(id -u)/$LM_LAUNCHD_LABEL" >/dev/null 2>&1 || return 1
  local i
  for i in $(seq 1 40); do
    sleep 0.25
    ollama_up && return 0
  done
  return 1
}

# True if MODEL is currently resident. keep_alive is last-writer-wins per
# request, so every API caller MUST check this before choosing keep_alive:
# resident -> -1 (preserve the warm pin) · not resident -> 0 (load-and-unload).
# Exact name or name:tag — a bare prefix match would let `q -m gemma4` count the
# resident gemma4-e4b-warm as itself and pin the wrong model forever.
ollama_resident() { ollama_cli ps 2>/dev/null | awk -v m="$1" 'NR>1 && ($1 == m || index($1, m ":") == 1) {f=1} END{exit !f}'; }

server_down_msg() {
  echo "ollama server is DOWN ($OLLAMA_HOST)" >&2
  echo "  start it: launchctl kickstart gui/$(id -u)/$LM_LAUNCHD_LABEL" >&2
}
