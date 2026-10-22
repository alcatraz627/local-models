# lm-usability: fixes for the validator findings

Worktree /Users/alcatraz627/Code/local-models-ux, branch `lm-usability`, nothing pushed. Five commits on top of 7a4f6a7. Where one commit covers several findings the shared sha is repeated. Model use: 4 small `q` calls (the F5 pair, the F7 no-terminal prompt, the F10 non-ASCII word), plus one 5.6 GB `warm on small 1h30m` load for F8. `warm off all` was run afterwards and shows nothing resident. The clipboard was not touched (it held text; only reads).

## Commits

| sha | subject | findings |
|---|---|---|
| c4df03a | cmdcheck: subcommand flags, capped help output, shell grammar, exit code | F1 F2 F3 F4, fixture, verify.sh wiring |
| f093abf | q: real file refs only, history as typed, --check and --again | F5 F6 F7, and the writer half of F10 |
| 4090383 | warm: read Go-style durations (1h30m) and validate before loading | F8 |
| f406db9 | see: answer -h and --json before touching clipboard or disk; guard rg under pipefail | F9 F11 |
| 7d93edf | lm: find prefilter, LM_ALL, ask help, history scope, terminal identity | F10 prefilter, F12, F13 |

## Fixture: red then green

`/Users/alcatraz627/Code/local-models-ux/.venv/bin/python probe/fixtures/cmdcheck-route.py`, 48 checks, model-free (fake programs in a temp PATH; the denied-program stubs write a marker if ever run). Wired into scripts/verify.sh right after the measure-check block.

Red, on the code before any fix: `9/48 passed`, 39 FAIL lines. Samples:

```
FAIL F1 git log --oneline --graph: no flag marked invented, no web nudge  [· checked: git ✓ · --oneline ✗ not in git --help · --graph ✗ not in git --help → q again --web]
FAIL F1 flag after -exec is not charged to find  [{'--bogus': False}]
FAIL F4 'if ftool --global; then echo hi; fi': nothing reported as not installed  [· checked: if ✗ not installed · then ✗ not installed · fi ✗ not installed → q again --web]
FAIL F4 'sudo -u root ftool --global': ...  [· checked: root ✗ not installed → q again --web]
FAIL F4 CLI exits 1 when a token is x
FAIL F2 `yes --foo` stays under 200 MB peak  [peak 10662 MB]
FAIL F3 pbcopy: not run, flag not marked invented  [· checked: pbcopy ✓ · --nope ✗ not in pbcopy --help → q again --web]
FAIL F5 /etc/hosts counts as a file reference  [rc 127]   (lm_file_ref did not exist yet)
```

Green, after: `48/48 passed`. In verify.sh: `ok   cmdcheck and routing words (q check / q cmd / prompt routing): 48/48 passed`.

## Per finding

**F1 (c4df03a).** A bare word after the program is treated as a subcommand. Flags are looked up in the top-level man and help first, then in `man <prog>-<sub>` and `<prog> <sub> --help`. Still not found: "?" (`--bogus ? not found in ftool sub help; unverified`), never x, and no web nudge for "?" alone. Flags are only charged to the program they follow: collection stops at a pipe, `;`, `&&`, `||`, after `--`, and after `-exec/-execdir/-ok/-okdir`. Quoted tokens are not flags (the tokenizer now keeps quotes).
Repro: `python3 lib/cmdcheck.py "git log --oneline --graph"` now prints `· checked: git log ✓ · --oneline ✓ · --graph ✓`. `"docker run --rm -it ubuntu"` prints `· checked: docker run ✓ · --rm ✓`. Control, still caught: `ls --all` prints `· checked: ls ✓ · --all ✗ not in ls --help → q again --web`, exit 1.

**F2 (c4df03a).** Help and man output is read through Popen in a new session, at most 256 KB, then the process group is killed.
Repro: `/usr/bin/time -l python3 lib/cmdcheck.py "yes --foo"` now shows 0.11 s real, `19873792 maximum resident set size`, `11764216 peak memory footprint` (was 10.2 GB). Output: `· checked: yes ✓ · --foo ✗ not in yes --help → q again --web`.

**F3 (c4df03a).** DENY_HELP extended with pbcopy, pbpaste, open, say, osascript, defaults, security, networksetup, afplay, screencapture, hdiutil, dscl, softwareupdate, scutil, spctl, mdutil, pfctl, passwd, login, su (plus the existing kill/launchctl/diskutil/tmutil/shutdown/halt/reboot/killall/pkill). A denied program's `--help` is never run; only its man page is read, and a flag the man page does not show comes back `? cannot be checked (pbcopy is never run)`, not a pass. The fixture proves the stubs for pbcopy, open, say and osascript are never executed.

**F4 (c4df03a).** Skips the shell keywords (`if then else elif fi for while until do done case esac in function select time ! { }`), heredoc bodies and terminators, markdown fence lines (with or without a language tag), redirection targets, and a leading `--foo`. Wrapper options that take a value are consumed: sudo -u/-g, env -u, xargs -n/-I/-P, timeout <duration>, nice -n, watch -n. `q check` and `python3 lib/cmdcheck.py` exit 1 when any token is x (flag not found or program not installed), else 0; "?" is 0. `check()` and `line()` are unchanged in shape, so `q cmd` and its exit code are untouched.
Repro: fixture cases `if/for/while/!/heredoc/sudo -u root/env -u X/timeout 5/nice -n 5/xargs -n 1/--foo/fence` all pass; CLI: `ftool --nope` exit 1, `ftool --global` exit 0, `ftool sub --bogus` exit 0, `zzz-not-a-program --x` exit 1.

**F5 (f093abf).** New `lm_file_ref WORD` in bin/_lib.sh (caller: the route loop in bin/q, and the fixture). Counts a word only if it starts with `/`, `~/`, `./`, `../`, or is a bare name with a known extension that exists on disk; anything containing `://` never counts. The "no file at" note is only for path-start words.
Repro: `bin/q --route "reply ok only; the site is https://example.com/logo.png and I/O" </dev/null` printed `ok` with no "no file" line (before: the model answered "File not found"). `bin/q --route "does ./nonexist-zz.txt exist? answer in four words" </dev/null` still narrates `· no file at "./nonexist-zz.txt"; telling the model so` and the model answered `No, it does not exist.`

**F6 (f093abf).** The runtime note is exported as `Q_RUNTIME_NOTE`; the python appends it to the model's user message only. History keeps what was typed. `q again` also strips a note from rows written before this change. The narration line flattens newlines and tabs.
Repro: after the F5 note call, `bin/q --again --all --dry-run` printed one line: `· again: "does ./nonexist-zz.txt exist? answer in four words" (was small) → big`, and the history row's prompt is exactly the typed words.

**F7 (f093abf).** `q check ...` and `q again ...` dispatch only when stdin is a terminal; otherwise they fall through as plain prompts. `q --check "<cmd>"` and `q --again [--big|--code|--web] [--dry-run]` always dispatch. `lm again` now execs `q --again`. (`lm cmd` is the `cmd` intent, not `check`; nothing else called either.)
Repro: `bin/q check "in four words, why is my disk full" </dev/null` answered `Check disk usage details. Files are taking up space.` (a plain prompt, as on main). `bin/q --check "ls --all" </dev/null` printed the verdict, exit 1. Under a pty, `q check "ls -l"` printed `· checked: ls ✓`.

**F8 (4090383).** `ka_seconds` and `is_duration` parse any run of `<n>[dhms]` (1h30m, 90m, 45s, 2h, 1d) plus bare seconds. `require_ttl` runs before `ollama_ensure`, so an unreadable time exits 2 with a plain message and loads nothing. `fast_until_line` says "until you run warm off" only for `forever`/`-1`. `pin` now sends seconds so every accepted form, including `d`, reaches Ollama the same way.
Repro: `bin/warm on small 1.5h` printed `warm: '1.5h' is not a time. Use a number with units like 90m, 2h, 1h30m or 45s, or 'forever'.` exit 2, nothing loaded. `bin/warm on 1.5h`, same. `bin/lm fast 1h30m` printed `loading gemma4-e4b-warm for 1h30m ...` then `q stays fast until 15:16 (warm off to free 5.6 GB)`. `bin/warm on small 1h30m` printed `small stays fast until 15:16 ...`. Then `warm off all`.

**F9 (f406db9).** `see paste` and `see latest` scan their args first: `-h/--help` prints help and exits 0, `--json` sets the JSON mode, both before any clipboard or filesystem access.
Repro: `bin/see paste -h` (clipboard held text) printed the help screen. `env SEE_SCREENSHOT_DIR=<empty dir> bin/see latest -h` printed help. `bin/see paste --json` printed `{"ok":false,"code":"clipboard_empty",...}`, exit 12. `env SEE_SCREENSHOT_DIR=<empty dir> bin/see latest --json` printed `{"ok":false,"code":"img_unreadable",...}`, exit 12.

**F10 (f093abf writer, 7d93edf prefilter).** q writes both history paths with `ensure_ascii=False`, UTF-8 file. `lm find` skips its quick `rg -F` filter when the first word has a quote, backslash or non-ASCII (it still reads the newest 4000 rows per log).
Repro (pty): `q "reply with exactly this one word: zqxcafé"` then `lm find "zqxcafé"` printed both `q#3735 ... → zqxcafé` (new, raw UTF-8) and `q#3728 ... → zqxcafé` (an old escaped row). `lm find 'say "hi'` ran without error.

**F11 (f406db9).** `bin/see` `_mlx_cause=` now ends `|| true`. Isolated proof: with an empty mlx.err under `set -eo pipefail`, the line now continues (`after assignment: []`). Other assignments in the diff `main...lm-usability` whose pipeline starts with or ends in rg/grep and can find nothing, found by searching the added lines:
1. bin/see ~780, `_mlx_cause="$(rg ... | tail | head -c 160)"`: guarded.
2. bin/_lib.sh `mine_line`, `hits="$(rg -n ... | tail | sed)"`: guarded with `|| true`.
3. bin/lm `lm_timeline` `tl_src`, the `$all` branch pipeline (`tail | jq`, no rg but the same sibling gap the validator noted): guarded with `|| true`.
Already safe, left alone: `lm_find` `find_src` (`|| true`), `lm_timeline` non-`$all` branch (`|| true`), `again_row` in bin/q (`|| true`), the `ps | rg ... | while ... done || true` in lm status, and `[ "$(... | grep -c .)" -ge ... ]` in mine_line (inside a test).

**F12 (7d93edf).**
- `LM_ALL`: new `lm_all_on` in bin/_lib.sh; only 1/yes/true (any case) means all. `env LM_ALL=0 bin/q show -1 </dev/null` now exits 12 `none of your calls from this terminal...`; `env LM_ALL=1 ...` shows the newest row from anyone. `lm timeline` uses the same helper.
- `lm ask` with no args: ask help, exit 2. `lm ask -h`: `lm ask — a quick answer from the small local model` plus one usage row (a new `ask` entry in `verb_help`), exit 0.
- `lm find ""`: `lm find: give at least one word to look for`, exit 2.
- `lm timeline --json </dev/null`: stderr `this call has no terminal, so none of the history is 'yours'. lm timeline --all shows everything.` then `[]`. `lm last` suppresses this hint (it prints its own).
- `q show -5` with 3 of your rows: `you asked for your call number 5 back, but only 3 of your calls from this terminal are in this history (--all reaches the rest)`, exit 12.
- `q history`: chose the filter, like timeline. It lists your rows only (numbers are still the log's line numbers, so `q show N` works) and `--all` returns everyone's; `--json` follows the same rule; the help line now says "your recent queries". Under a pty `q history 3` printed rows 3725, 3729, 3735 (mine); `q history --all 3` printed 3733, 3734, 3735. With no terminal it prints a stderr hint and nothing (JSON: `[]`), matching `lm timeline`.
- build-summary.md line 36 corrected in the main checkout (the only file touched there).
- Not changed: `lm cmd ""` printing q help (same as main for `q ""`; the validator listed it as parity).

**F13 (7d93edf).** `lm_identify` sets `LM_TTY`/`LM_SESSION` only when stdin or stderr is a terminal; otherwise both are empty (and exported empty, so a parent's value is not inherited). Evidence: the `lm timeline --json </dev/null` run above reports no terminal even though this shell has the session variables; under a pty the same commands identify as `ttys002`.

## verify.sh

`bash scripts/verify.sh`: `40 passed, 3 FAILED`. The three are the known ones:
```
  FAIL lm doctor — run it directly to see which check     (six "on PATH" rows: the PATH points at the main checkout)
  FAIL guard-model-tier block path
  FAIL launchd: com.alcatraz.local-models-ollama failing (1)
```
and `ok   cmdcheck and routing words (q check / q cmd / prompt routing): 48/48 passed`.

## Not fixed or left as-is

- Commits are grouped by file, not strictly one per finding: F5/F6/F7 and the F10 writer share bin/q, and F10's prefilter, F12 and F13 share bin/lm and bin/_lib.sh (the repo has no non-interactive hunk staging here). The shas above say which.
- The remaining SUSPECTED item that `mine_line` ORs tty and session so a reused tty name can claim an old row: not in the decisions, not changed. In this session a validator pty row and a new pty row both carried `ttys002`, which shows the reuse is real.
- `cmdcheck` still checks the `tool` found in PATH for `/opt/x/tool --flag` (benign, not in scope).
- A bare word argument after a program (`ls somedir --bogus`) is read as a possible subcommand, so its unknown flag is "?" rather than x. That follows decision 1; the cost is a missed catch for programs that take a positional first.
- Hook nudge to surface: the env-access hook asked the owner how env reads should be done in this repo (cmdcheck.py and the fixture read `os.environ` for PATH and the man pager). Nothing was changed for it; the reads are not new patterns.
