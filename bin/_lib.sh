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

LM_ROOT_DIR="${BASH_SOURCE[0]%/*}/.."; export LM_ROOT_DIR

# Run lib/verbs.py (the registry reader) with the project python when there is one.
lm_verbs() {
  local py="$LM_ROOT_DIR/.venv/bin/python"
  [ -x "$py" ] || py=python3
  "$py" "$LM_ROOT_DIR/lib/verbs.py" "$@"
}

# A --json error envelope that carries the fix: {ok:false, code, message, remedy, next}.
# remedy is one sentence, next is a runnable command or null. Unknown codes get a generic remedy.
lm_err_json() { # CODE MESSAGE
  local fix; fix="$(lm_verbs remedy "$1" 2>/dev/null)" || fix=""
  [ -n "$fix" ] || fix='{"remedy":"see the message; -h lists the flags and examples","next":null}'
  jq -cn --arg c "$1" --arg m "$2" --argjson f "$fix" '{ok:false, code:$c, message:$m} + $f'
}

# On a terminal only, one gray line under a text-mode error saying what to do about it.
lm_fix_line() { # CODE
  [ -t 2 ] || return 0
  [ -z "${NO_COLOR:-}" ] && [ "${TERM:-}" != dumb ] && local dm=$'\033[2m' rs=$'\033[0m' || local dm="" rs=""
  local fix r n; fix="$(lm_verbs remedy "$1" 2>/dev/null)" || return 0
  r="$(printf '%s' "$fix" | jq -r '.remedy // empty' 2>/dev/null)" || return 0
  n="$(printf '%s' "$fix" | jq -r '.next // empty' 2>/dev/null)" || n=""
  [ -n "$r" ] || return 0
  printf '%s  → %s%s%s\n' "$dm" "$r" "${n:+ (try: $n)}" "$rs" >&2
}

# ── Terminal colors (TTY / NO_COLOR / TERM=dumb aware) ──
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-}" != dumb ]; then
  Y=$'\033[1;33m'; C=$'\033[36m'; G=$'\033[32m'; Dm=$'\033[2m'; Rs=$'\033[0m'; Bd=$'\033[1m'
else Y= C= G= Dm= Rs= Bd= ; fi
# The same palette for text written to STDERR, decided by stderr's own TTY: the set above
# follows stdout, so using it on a stderr line leaked escape codes into redirected logs.
if [ -t 2 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-}" != dumb ]; then
  eY=$'\033[1;33m'; eC=$'\033[36m'; eDm=$'\033[2m'; eRs=$'\033[0m'; eRed=$'\033[31m'; eG=$'\033[32m'; eBd=$'\033[1m'
else eY= eC= eDm= eRs= eRed= eG= eBd= ; fi

# ── Help rendering ──
# Rows wrap at HELP_W columns so no line runs off a normal terminal. A help screen
# is the short version by default: everything after `_more` is shown only with
# --all, and `_help_end` says how much was left out.
HELP_W=100
HELP_ALL=false     # set by the tool when --all is among its args
_help_hide=false; _help_hidden=0
_more() { $HELP_ALL || _help_hide=true; }
_help_end() { # COMMAND the user types to see the rest, e.g. "q -h --all"
  local was=$_help_hide n=$_help_hidden
  _help_hide=false; _help_hidden=0
  if $was && [ "$n" -gt 0 ]; then printf '\n  %s%s --all   shows the other %s rows (every flag, the rest of the examples)%s\n' "$Dm" "$1" "$n" "$Rs"; fi
}
# Fill the array _WL with TEXT broken into lines of at most AVAIL characters.
_wrap_lines() { # AVAIL TEXT
  local avail="$1" line="" word; local -a words
  _WL=()
  read -ra words <<<"$2"
  for word in ${words[@]+"${words[@]}"}; do
    if [ -n "$line" ] && [ $(( ${#line} + 1 + ${#word} )) -gt "$avail" ]; then _WL+=("$line"); line="$word"
    else line="${line:+$line }$word"; fi
  done
  _WL+=("$line")
}
_help_row() { # COLOR WIDTH LABEL DESC
  if $_help_hide; then _help_hidden=$((_help_hidden + 1)); return 0; fi
  local col="$1" w="$2" label="$3" avail lead l
  avail=$(( HELP_W - w - 3 )); [ "$avail" -lt 30 ] && avail=30
  _wrap_lines "$avail" "$4"
  lead="$(printf '%*s' $((w + 3)) '')"
  if [ "${#label}" -gt "$w" ]; then
    printf '  %s%s%s\n' "$col" "$label" "$Rs"
    for l in "${_WL[@]}"; do printf '%s%s%s%s\n' "$lead" "$Dm" "$l" "$Rs"; done
  else
    printf '  %s%-*s%s %s%s%s\n' "$col" "$w" "$label" "$Rs" "$Dm" "${_WL[0]}" "$Rs"
    for l in "${_WL[@]:1}"; do printf '%s%s%s%s\n' "$lead" "$Dm" "$l" "$Rs"; done
  fi
}
_sec() { $_help_hide && return 0; printf '\n%s%s%s\n' "$Y" "$1" "$Rs"; }
_cmd() { _help_row "$C" 32 "$1" "$2"; }
_opt() { _help_row "$G" 32 "$1" "$2"; }
_ex()  {
  if $_help_hide; then _help_hidden=$((_help_hidden + 1)); return 0; fi
  local avail=$(( HELP_W - 49 )) l
  _wrap_lines "$avail" "$2"
  if [ "${#1}" -gt 44 ]; then
    printf '  %s$%s %s\n' "$Dm" "$Rs" "$1"
    for l in "${_WL[@]}"; do printf '%*s%s%s%s\n' 5 '' "$Dm" "$l" "$Rs"; done
  else
    printf '  %s$%s %-44s %s%s%s\n' "$Dm" "$Rs" "$1" "$Dm" "${_WL[0]}" "$Rs"
    for l in "${_WL[@]:1}"; do printf '%*s%s%s%s\n' 49 '' "$Dm" "$l" "$Rs"; done
  fi
}
_kv()  { $_help_hide && return 0; printf '  %s%-9s%s %s\n' "$Dm" "$1" "$Rs" "$2"; }
# A gray note line under a help section; wraps like the rows do.
_note() {
  if $_help_hide; then _help_hidden=$((_help_hidden + 1)); return 0; fi
  local l; _wrap_lines $(( HELP_W - 2 )) "$1"
  for l in "${_WL[@]}"; do printf '  %s%s%s\n' "$Dm" "$l" "$Rs"; done
}
# True when any argument asks for help (-h, --help, help). Verbs call it first so
# that asking for help can never run the verb.
wants_help() { local a; for a in "$@"; do case "$a" in -h|--help) return 0 ;; esac; done; return 1; }
wants_all() { local a; for a in "$@"; do [ "$a" = --all ] && return 0; done; return 1; }

# ── JSONL history: numbered list + full entry ──
# Entry numbers are stable JSONL line numbers, so `show N` works forever.
jsonl_history() { # LOG N LINE_JQ
  local log="$1" n="$2" fmt="$3"
  [[ "$n" =~ ^[0-9]+$ ]] || n=15
  [ -f "$log" ] || { echo "no history yet ($log)"; return; }
  local total start; total=$(wc -l < "$log" | tr -d ' ')
  start=$(( total - n + 1 )); (( start < 1 )) && start=1
  # one torn line must not hide every newer row, so unparseable lines become a marker
  tail -n "$n" "$log" | jq -rR "(fromjson? | $fmt) // \"(unreadable history line)\"" | nl -ba -v "$start" -w4 -s'  '
}

# ── Whose call was it ──
# Every history row records the terminal (tty) and terminal session it came from, so
# "my last call" can mean mine and not whatever a hook or agent ran a second ago.
# Both are null for a call with no terminal (agents, hooks, cron). Old rows have no
# such field and count as not mine.
lm_identify() { # sets LM_TTY and LM_SESSION once per process
  [ -n "${_LM_IDENTIFIED:-}" ] && return 0
  _LM_IDENTIFIED=1
  LM_TTY=""; LM_SESSION=""
  # A process with no terminal on stdin or stderr (an agent, a hook, cron) has no identity, even when it
  # inherited the owner's terminal-session variables; otherwise it would count as "mine".
  if [ -t 0 ] || [ -t 2 ]; then
    local t; t="$(ps -o tty= -p "$$" 2>/dev/null)"; t="${t//[[:space:]]/}"
    case "$t" in ''|'?'|'??') t="" ;; esac
    LM_TTY="$t"
    LM_SESSION="${TERM_SESSION_ID:-${ITERM_SESSION_ID:-${WEZTERM_PANE:-${KITTY_WINDOW_ID:-${TMUX_PANE:-}}}}}"
  fi
  export LM_TTY LM_SESSION
}
# jq fragment for a history row's identity: use with --arg tty "$LM_TTY" --arg sess "$LM_SESSION".
JQ_WHO='{tty:(if $tty == "" then null else $tty end), session:(if $sess == "" then null else $sess end)}'
# jq def: what to do about an error code, in words (shown next to failed rows).
JQ_REMEDY='def remedy($c): {
      server_down: "the local server was stopped; it restarts on the next call, or run lm doctor",
      model_missing: "that model is not installed; lm models lists what is",
      timeout: "it took too long; try a smaller input or a longer --timeout",
      ctx_required: "that intent needs a file; add --ctx FILE",
      ctx_unreadable: "the file could not be read; check the path",
      ctx_binary: "the file is binary; extract its text first",
      ctx_too_large: "the file is too big; cut it down, or send it to the cloud lane with lm gemini --file (that leaves this Mac)",
      cancelled: "it was cancelled before it finished",
      mlx_failed: "the MLX read failed; run it again, or add -m minicpm-v4.6",
      model_error: "the vision model failed; run it again, or lm doctor",
      ocr_missing: "install the text reader: npm install -g mac-ocr",
      vlm_unavailable: "the model read was skipped; the measured evidence is still complete",
      gemini_unavailable: "gemini is not available; check the key in ~/.gemini/.env",
      gemini_error: "gemini ended without an answer; lm gemini show -1 has the steps"
    }[$c] // "";'
# jq def: true for a row that came from the caller's own terminal or session.
JQ_MINE='def mine($t; $s): ($t != "" and (.tty // "") == $t) or ($s != "" and (.session // "") == $s);'

# Stable line number of the caller's K-th latest row in LOG (K=1 is the newest), or nothing.
mine_line() { # LOG K
  local log="$1" k="${2:-1}"
  lm_identify
  [ -f "$log" ] || return 1
  [ -n "$LM_TTY$LM_SESSION" ] || return 1
  local hits
  hits="$(rg -n -e "\"tty\": ?\"$LM_TTY\"" ${LM_SESSION:+-e "\"session\": ?\"$LM_SESSION\""} "$log" 2>/dev/null | tail -n "$k" | sed 's/:.*//')" || true
  [ "$(printf '%s\n' "$hits" | grep -c .)" -ge "$k" ] || return 1
  printf '%s' "$hits" | head -n 1
}
# Which rows a -1 / latest lookup may land on: mine (default) or all. LM_ALL=1 or --all in the tool flips it.
# LM_ALL counts as on for 1, yes or true; 0, empty or anything else is off.
lm_all_on() { case "$(printf '%s' "${LM_ALL:-}" | tr 'A-Z' 'a-z')" in 1|yes|true) return 0 ;; esac; return 1; }
LM_ENTRY_SCOPE=mine; ! lm_all_on || LM_ENTRY_SCOPE=all

jsonl_entry() { # LOG N ENTRY_JQ ($i bound to N in jq). N>0 = stable line no; N<0 counts from the end (-1 = latest)
  local log="$1" i="$2" fmt="$3"
  # Exit codes follow the table in docs/CAPABILITIES.md: 2 bad usage, 12 missing entry.
  [ -f "$log" ] || { echo "no history yet" >&2; return 12; }
  local total; total=$(wc -l < "$log" | tr -d ' ')
  if [[ "$i" =~ ^-[0-9]+$ ]]; then
    if [ "$LM_ENTRY_SCOPE" = mine ]; then
      # -1 means YOUR latest call from this terminal, not the newest row anyone wrote.
      local want="${i#-}" have=0
      lm_identify
      i="$(mine_line "$log" "$want")" || i=""
      if [ -z "$i" ]; then
        if [ -n "$LM_TTY$LM_SESSION" ]; then
          have="$(rg -c -e "\"tty\": ?\"$LM_TTY\"" ${LM_SESSION:+-e "\"session\": ?\"$LM_SESSION\""} "$log" 2>/dev/null)" || have=0
        fi
        if [ "${have:-0}" -gt 0 ]; then
          echo "you asked for your call number $want back, but only $have of your calls from this terminal are in this history (--all reaches the rest)" >&2
        else
          echo "none of your calls from this terminal are in this history yet (--all, or a number from 'history', reaches the rest)" >&2
        fi
        return 12
      fi
    else
      i=$(( total + i + 1 ))   # -1 -> latest, -2 -> second-latest
    fi
  fi
  [[ "$i" =~ ^[0-9]+$ ]] || { echo "usage: show <N>   (N from 'history', or -1 for the latest)" >&2; return 2; }
  (( i >= 1 )) || { echo "no entry #$2 (there are $total)" >&2; return 12; }
  local line; line=$(sed -n "${i}p" "$log")
  [ -n "$line" ] || { echo "no entry #$i (there are $total)" >&2; return 12; }
  printf '%s' "$line" | jq -r --arg i "$i" "$fmt" 2>/dev/null \
    || { echo "entry #$i is not valid JSON (a torn write?); the raw line: ${line:0:200}" >&2; return 12; }
}

# ── Shared arg-parse helpers: same messages and exit code (2) in every tool ──
# A flag that takes a value must have one; without this `shift 2` fails under
# set -e and the tool exits 1 with no message at all.
need_arg() { # TOOL FLAG [VALUE]
  [ "$#" -ge 3 ] && [ -n "${3:-}" ] || usage_fail "$1" "$2 needs a value"
}

# For flags where an empty value is meaningful (--neg ""): only a missing word
# fails. Pass the parser's remaining argument count.
need_arg_present() { # TOOL FLAG ARGC
  [ "$3" -ge 2 ] || usage_fail "$1" "$2 needs a value"
}

# A usage error, exit 2. Machine callers (MODE=json in the calling tool) also get
# the {ok:false, code} envelope on stdout, as every other error in that mode does.
usage_fail() { # TOOL MESSAGE
  printf '%s: %s\n' "$1" "$2" >&2
  case "${MODE:-}" in
    json)   lm_err_json invalid_args "$2" ;;
    stream) jq -cn --arg m "$2" '{t:"error", code:"invalid_args", message:$m}' ;;
  esac
  exit 2
}

# For verbs whose only option is --json, in any position: sets JSON_ONLY to --json when given and
# refuses anything else (usage error, exit 2). Call it directly, never inside $( ), or the JSON
# error envelope is swallowed by the substitution.
json_only() { # TOOL ARG...
  local tool="$1" a; shift
  JSON_ONLY=""
  for a in "$@"; do
    case "$a" in --json) JSON_ONLY=--json ;; *) usage_fail "$tool" "unexpected '$a' (the only option is --json)" ;; esac
  done
}

# Call from the parser's catch-all branch. Only a flag-shaped word (-x, --xyz,
# --xyz=value) is refused; "-", "-1" and prompts with spaces ("- fix this") stay
# positionals.
reject_unknown_flag() { # TOOL ARG
  if [[ "$2" =~ ^--?[A-Za-z][A-Za-z0-9_-]*(=.*)?$ ]]; then
    usage_fail "$1" "unknown flag '$2' (run $1 -h to list flags). If it is part of your prompt, quote the prompt, or put -- before it"
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
        # a swapped pair of letters ("statsu") is one typo, not two
        if (i > 1 && j > 1 && substr(a, i, 1) == substr(b, j-1, 1) && substr(a, i-1, 1) == substr(b, j, 1) && d[i-2, j-2] + 1 < m) m = d[i-2, j-2] + 1
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

# True if a word in a typed prompt names a file: it starts with /, ~, ./ or ../, or it is a bare
# name with a known file extension that exists here. "I/O", "TCP/IP", "yes/no" and URLs are not files.
lm_file_ref() { # WORD
  local w="$1"
  case "$w" in *://*) return 1 ;; esac
  case "$w" in
    /?*|"~/"*|./?*|../?*) return 0 ;;
  esac
  case "$(printf '%s' "${w##*.}" | tr 'A-Z' 'a-z')" in
    png|jpg|jpeg|webp|gif|heic|pdf|md|txt|csv|tsv|json|yaml|yml|toml|xlsx|docx|doc|rtf|odt|html|htm|log|py|sh|js|ts|swift|rs|go)
      case "$w" in *.*) [ -e "${w/#\~/$HOME}" ] ;; *) return 1 ;; esac ;;
    *) return 1 ;;
  esac
}
