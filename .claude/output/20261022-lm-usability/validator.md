# Adversarial validation: lm-usability (worktree /Users/alcatraz627/Code/local-models-ux)

Validator run 2026-10-22. Nothing was edited, committed or pushed in either checkout. Model calls: 7 small-tier `q` calls, no big/code/imagine/fleet/review. `warm off all` run at the end (nothing resident). Clipboard text restored and verified with `osascript -e 'clipboard info'`. Scratch work is in /private/tmp/claude-501/-Users-alcatraz627-Code-local-models/a48a6eeb-34f8-4fed-9269-015afa95b460/scratchpad/v/.

## CONFIRMED (reproduced)

### 1. HIGH: cmdcheck marks valid subcommand flags as invented, and tells the user to go to the web
- Commands: `python3 lib/cmdcheck.py "git log --oneline --graph"`, `"git commit --amend --no-edit"`, `"docker run --rm -it ubuntu"`
- Observed: `· checked: git ✓ · --oneline ✗ not in git --help · --graph ✗ not in git --help → q again --web` (same shape for --amend, --no-edit, --rm). Exit 0, `ok:false`.
- Expected: flags of a subcommand (git log, git commit, docker run, npm install, brew install, kubectl get ...) are not in the top-level `--help`/man page, so they should come back as unknown ("?"), not as a failure. Today every common multi-level tool gives a false negative, and the line pushes the user off this Mac.
- Same class: flags that belong to another program on the line are charged to the first one. `find . -name x -exec canary --x {} \;` charges `--x` to find; `echo "--hello" | grep -- --hello` charges `--hello` to grep; quoted arguments starting with `--` count as flags.
- Where: lib/cmdcheck.py:93-96 (all `--word` tokens after the program are treated as its flags) and :155-164 (only the top-level man/--help text is searched).

### 2. HIGH-ish (medium probability, severe impact): cmdcheck reads unbounded `--help` output into memory
- Command: `/usr/bin/time -l python3 lib/cmdcheck.py "yes --foo"`
- Observed: `maximum resident set size 10228121600` (10.2 GB peak footprint) in 1.66 s. `yes` prints its arguments forever, and `capture_output=True` buffers all of it until the 1 s timeout.
- Expected: output capped (read at most some KB, then kill). On a 64 GB Mac running an MLX benchmark this can push the machine into swap from a gray status line.
- Where: lib/cmdcheck.py:117-119 (`subprocess.run(..., capture_output=True, timeout=...)`). Also reachable from every `q cmd` answer on a terminal and from `--json`.

### 3. MEDIUM: cmdcheck's "--help only" still has side effects for programs not on the deny list
- Command: `python3 lib/cmdcheck.py "pbcopy --nope"` then `pbpaste`
- Observed: clipboard was emptied (pbpaste printed nothing; I restored it). `pbcopy --help` reads stdin (DEVNULL) and writes an empty clipboard.
- Expected: the claim is "never runs the command"; that holds, but running `<prog> --help` for an arbitrary program is not safe either. Other programs that treat `--help` as an operand or ignore it (pbcopy, anything user-written in PATH) act. The canary script in PATH confirmed that only `canary --help` is ever run, never the command line itself (18 `canary ran: --help` lines, zero with other args), so the narrow claim holds; the broad safety implication does not.
- Where: lib/cmdcheck.py:29-32 (deny list is a short opt-out list, not an allow list), :157-158.

### 4. MEDIUM: shell keywords, wrapper options and `!` are reported as "not installed" and trigger the web nudge
- Commands (via `check()`): `'if canary --x; then echo; fi'` gives `if ✗ not installed · then ✗ not installed · fi ✗ not installed`; `'for f in *; do canary --x $f; done'` gives `for/do/done ✗`; `'! canary --x'` gives `! ✗ not installed`; `'cat <<EOF\ncanary --x\nEOF'` gives `EOF ✗ not installed`; `'sudo -u root canary --bogus'` gives `root ✗ not installed`; `'env -u X canary --bogus'` gives `X ✗ not installed`; `'--foo'` gives `--foo ✗ not installed`.
- Expected: keywords and heredoc terminators skipped; wrapper options that take a value (`sudo -u USER`, `env -u NAME`, `xargs -n N` handled only because N is numeric) consumed. A `for`/`if` one-liner is a very common `q cmd` answer; each one currently gets `ok:false` and "→ q again --web".
- Related: a bad verdict still exits 0 (`q check 'ls --all'` prints `ok:false`, rc 0), so scripts cannot branch on it. A markdown fence line carrying a language tag adds a spurious `bash ✓`.
- Where: lib/cmdcheck.py:68-97 (`program_and_flags`), :24-26 (no keyword set), :195-203 (`main` always returns 0).

### 5. MEDIUM: the new routing treats any slash-word or URL in a terminal prompt as a missing file, injects a note into the prompt and corrupts the answer
- Commands: `script -q /dev/null bin/q "reply ok and nothing else, I/O and yes/no"` (pty, so `-t 0` is true) and `bin/q --route "reply ok only; the site is https://example.com/logo.png" </dev/null`
- Observed 1: stderr `· no file at "I/O"; telling the model so`; the logged prompt became `...yes/no\n\n(Note from the runtime: no file exists at "I/O"; say so plainly.)` (history row 3725).
- Observed 2: stderr `· no file at "https://example.com/logo.png"; telling the model so`; the model replied `File not found at "https://example.com/logo.png".` instead of `ok`.
- Expected: only words that look like a path (start with `/`, `~`, `./`, `../`) or end in a known file extension and are not URLs should count; "I/O", "TCP/IP", "yes/no", "km/h", URLs must pass through untouched. The mutated prompt is also what gets written to history, which then feeds `q again` (finding 6) and `lm find`.
- Where: bin/q route block, the `case "$_wc" in */*|*.[A-Za-z]*)` filter and the `*/*|*.png|...` missing-file branch (diff hunk after "ROUTE: send a plain request").

### 6. MEDIUM-LOW: `q again` replays the injected runtime note as the user's question, and prints a multi-line "again" line
- Command: `script -q /dev/null bin/q again --dry-run` after finding 5's row
- Observed: `· again: "reply ok and nothing else, I/O and yes/no\n\n(Note f" (was small) → big` (narration spans three lines; the real run would resend the note).
- Expected: strip the runtime note before storing or before replaying; flatten newlines in the narration.
- Where: bin/q again_run (`nice="${ask:0:50}"`, `ask` taken from stored prompt) and the route block that mutates `QUERY` before it is logged.

### 7. MEDIUM: new `q check` and `q again` subcommands hijack ordinary prompts that begin with those words
- Commands: `bin/q check why is my disk full </dev/null` printed `· checked: why ✗ not installed → q again --web`; `bin/q again and again </dev/null` exited 2 with "none of your calls from this terminal to repeat".
- Expected on main: both are plain prompts (main has no `check` or `again` case in the subcommand dispatch; see the diff). Breaks the claim that scripted forms behave as before.
- Where: bin/q subcommand `case` (`again) ...; check) exec python3 ...`).

### 8. MEDIUM: `warm on <tier> <ttl>` aborts after loading the model for any compound duration (regression)
- Command: `bin/warm on small 1h30m`, then `warm off all`
- Observed: `loading gemma4-e4b-warm for 1h30m ...` then `warm: line 52: 1h30: value too great for base (error token is "1h30")`, exit 1, model left loaded. Ollama accepts Go durations such as `1h30m`; main did too.
- Expected: unknown shapes should print no "until" time (or parse h and m), never abort after the side effect.
- Where: bin/warm:48-56 (`ka_seconds`: `*[0-9]m)` matches "1h30m" and does `$(( ${1%m} * 60 ))`). A value that matches no arm (for example `1.5h`) returns empty, and `fast_until_line` then claims "until you run warm off", which is wrong (bin/warm:61).

### 9. MEDIUM: `see paste -h` and `see latest -h` are not side-effect-free help; `--json` errors are not JSON
- `bin/see paste -h` printed "the clipboard holds no image..." and exited 12 (clipboard held text).
- `SEE_SCREENSHOT_DIR=<empty dir> bin/see latest -h` exited 12 with "no screenshots found" instead of help.
- `bin/see paste --json` (text clipboard) and `SEE_SCREENSHOT_DIR=<empty> bin/see latest --json` print plain text on stderr, not `{"ok":false,"code":...}` on stdout; `$MODE` is still `text` when `emit_error` runs because the args are parsed later.
- Expected: -h/--help answered before touching the clipboard or filesystem; `--json` honoured for the error.
- Where: bin/see:193-201 (`paste`) and :205-209 (`latest`), `emit_error` at bin/see:128.
- Note: the help screen itself is only reachable as `see -h`. `see latest -h` worked only because Desktop held a PNG.

### 10. MEDIUM-LOW: `lm find` misses q rows whenever its first word is non-ASCII
- Commands: `bin/q "reply with exactly this one word: zqxcafé"`, then `bin/lm find "zqxcafé"` gives "nothing matches"; `bin/lm find "zqxcaf"` finds the row.
- Cause: q writes history with `json.dumps` default (`café` on disk) while the prefilter is a raw `rg -F` of the first term against the file. see and gemini rows are written by jq as raw UTF-8, so `lm find "×"` found see and gemini rows but no q rows. Any first term with a quote or backslash fails the same way.
- Where: bin/lm `find_src` (`rg -n -i -F -e "$first"`); writer at bin/q (python log write, no `ensure_ascii=False`).

### 11. MEDIUM-LOW (regression of the already-fixed bug class): bare assignment with an rg pipeline in `see`
- Code: `_mlx_cause="$(rg -i -N 'error' "$SEE_TMP/mlx.err" 2>/dev/null | tail -n 1 | head -c 160)"` at bin/see:~780, under `set -eo pipefail`. When mlx.err has no line containing "error" (an OOM kill prints "Killed: 9", or an empty stderr with empty TEXT), rg exits 1 and the assignment aborts `see` silently with exit 1: no `emit_error`, no history row, no "mlx-vlm read failed" message.
- Reproduced the exact line in isolation: scratchpad/v/repro.sh prints nothing and exits 1 (the `echo "after assignment"` line never runs). I did not trigger it end to end because I cannot force an MLX failure without loading a model. On main the same pipeline sat inside `$(...)` used as an argument, where a non-zero status was harmless, so this is a regression.
- Where: bin/see:779-781 (path: `if [ "$rc" -ne 0 ] || [ -z "$TEXT" ]`).

### 12. LOW: smaller defects
- `LM_ALL=0` still means "all" (`LM_ALL=0 bin/q show -1` printed the newest row from anyone; test is `[ -n "${LM_ALL:-}" ]`). bin/_lib.sh:`LM_ENTRY_SCOPE=mine; [ -n "${LM_ALL:-}" ] && ...`.
- `lm ask` with no arguments prints the `lm cmd` help and exits 2 (bin/lm:804, `verb_help cmd`). `lm ask -h` prints q's full help.
- `lm find ""` succeeds and lists the newest rows from everyone (empty term passes the "at least one term" check).
- `lm timeline --json` with no terminal prints `[]` and exits 0 with no hint (the text hint is skipped for `--json`), so an agent cannot tell "no history" from "history exists but is not yours".
- `q show -5` when you have 3 rows says "none of your calls from this terminal are in this history yet", which is false; it should say there are only 3.
- Build-summary claim "`q show N` on a missing entry now exits 12 (it exited 0 before)" is wrong: `/Users/alcatraz627/Code/local-models/bin/q show 999999 </dev/null` already exits 12 (`set -e` fires inside `show_entry`). Documentation inaccuracy only.
- `q history` is not filtered to "mine" although its new help line says `--all` applies to history; `q history --all` just returns the same 15 rows.
- `lm cmd ""` prints the full q help with exit 0 (same as main for `q ""`).

## SUSPECTED (read in code, not reproduced)

- Terminal identity: `LM_SESSION` is taken from `TERM_SESSION_ID`/`ITERM_SESSION_ID`/`TMUX_PANE`, which child processes inherit. An agent or hook started from your terminal session shares the value and its calls will count as "mine", defeating finding 3 of the audit for Terminal.app, iTerm and tmux users. `ps -o tty=` has the same effect when a spawned process keeps the controlling tty, and tty names are reused across tabs over time. In this validator environment both were empty, so I could not show it. bin/_lib.sh `lm_identify`.
- `mine_line` ORs tty and session patterns, so a reused tty name plus an old row can claim an unrelated row as yours.
- cmdcheck `program_and_flags` runs `help_text(name)` with `basename(prog)` through PATH lookup, so `/opt/x/tool --flag` checks the `tool` found in PATH, not the file named. Benign but inaccurate.
- `lm fast 1h30m` falls into the "model name" branch (is_duration only accepts one unit) and fails with "model '1h30m' not found" (seen, clear error, exit 11). Same compound-duration gap as finding 8.
- `lm_timeline`'s `$all` branch lacks the `|| true` its siblings have; a torn log line is handled by `fromjson?`, so only a jq failure would abort.

## Claims I tried to break that held

- Every verb and alias answers -h with exit 0 and no side effects: lm cmd, read, diff, doc, again, find, review, status, fast, more, ask, models, doctor, probe, opencode, timeline, last, count, web, failed, examples; `q again -h`; `q check -h`. Exceptions are only `see paste -h` and `see latest -h` with an empty dir (finding 9).
- No-tty callers match main on every cheap parity check: `q ""`, `q -- -h`, `q --ctx /nonexistent`, `q --preflight --file`, `q --bogus`, `q intents`, `q -c`, `q -c 999999 hi`. A no-tty `q "... see /etc/hosts"` did not route and logged `"tty": null, "session": null`.
- History scope: rows without a terminal store null tty and session; `LM_ALL=1`, `--all` before or after N all reach the newest row from anyone; `q show 999999` exits 12; `q show abc`, `q show` and `q show 1.5` exit 2.
- cmdcheck never runs the checked command: a canary program in PATH logged only `--help` across 38 shapes (pipes, `&&`, `;`, `$(...)`, backticks, subshells, redirects, env prefix, sudo, xargs, timeout, nohup, `bash -c`, `exec`, heredoc, `find -exec`); deny-listed `rm`/`dd`-class programs get no `--help` call; nonexistent binaries come back "not installed"; empty and whitespace input return an empty verdict without error; `q cmd` shows the gray line on a pty and `checked` in `--json`.
- `see paste` with a PNG on the clipboard works (`--ocr` and `--json`), the temp dir is cleaned (no `see-run.*` left), and a text-only clipboard gives exit 12 with a clear message. `see latest` with an empty SEE_SCREENSHOT_DIR exits 12 with a clear message.
- `lm status` exits 0 with no MLX process and under `env -i` with a minimal PATH; `lm status --json` still returns the contract object.
- Edge inputs: `lm "-5 degrees in F"` and `lm -5 degrees in F` both answer; `lm doc ""`, `lm doc /nonexistent.pdf`, `lm read /nonexistent.png`, `lm diff a`, `lm timeline abc|0|-5`, `lm find -n 0|-n` fail with exit 2 or 12 and a plain message; `lm find -- -n` works.
- `lm fast 1h30m` fails cleanly, and `warm on small 1h` form `warm off all` leaves nothing resident.
