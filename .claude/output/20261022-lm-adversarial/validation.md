# Validation of the lm CLI fixes (merged tree, branch vision-suite)

Target: /Users/alcatraz627/Code/local-models (HEAD e885429). Claims: /Users/alcatraz627/Code/local-models/.claude/output/lm-fixes-summary.md.
No source file was edited. Model calls used: 3 of 5 (`q --json -m small "say ok"`, `q "say ok"`, and the same call under `script` to see the stats line on a pty). No imagine, review, fleet, bench, see-with-model, gemini prompt or warm on/off was run. Malformed-history and empty-history cases ran on a copy of the tree in the scratchpad (`.../scratchpad/sb`), not on the real logs.

Side effect to disclose: my probe `see --json --ocr --no-read --model=foo` (finding F1) was parsed as an image path and appended one junk error row to the real `/Users/alcatraz627/Code/local-models/logs/see-history.jsonl` (line 1242, img `--model=foo`, error `img_unreadable`). It is the last line; the vision benchmark's own rows are untouched, but a reader of that file will see it.

Regression check, flags: every flag in the `-h` text of q, see, imagine, review, warm and lm gemini is still accepted by its case statement (enumerated by reading each parser). `see` accepts every flag probe/vision/run.py and probe/candidates/run.py pass (`--json -m --crop --region --ui`, plus `diff A B prompt`), verified with `see --json -m x --crop a --region b --only E5 --grid 8 --glow --ui --no-read` reaching "no image given" (exit 2), not "unknown flag". Callers in lib/ (fleet, rag, ui-verify, gemini) and scripts/verify.sh pass only known flags. No documented flag is rejected. The regressions below are about undocumented-but-natural input.

## Confirmed broken

### F1. `--flag=value` bypasses the unknown-flag guard everywhere (D2 not fully fixed) - MED (paid path on gemini)
```
$ q --preflight --json --bogus=1
{"ok":false,"code":"ctx_required","message":"preflight needs --ctx FILE or piped input"}   (exit 2, but from the preflight check: --bogus=1 was swallowed as the prompt)
$ lm gemini digest --foo=bar      (sandbox copy)
lm gemini: no such file: --foo=bar   (exit 12; parsed as a positional)
$ lm gemini digest --foo
lm gemini: unknown flag '--foo' ...  (exit 2)
$ see --json --ocr --no-read --model=foo
{"ok":false,"code":"img_unreadable","message":"no such file: --model=foo"}  (exit 12, and logged)
```
Expected: exit 2 "unknown flag". `--model=x`, `--timeout=60`, `-m=small` are the natural way to mistype; on `lm gemini "..."` and `q "..."` the whole string, flag included, is sent to the model (paid on gemini); on `imagine` it starts a GPU generation.
Fix: `/Users/alcatraz627/Code/local-models/bin/_lib.sh:65`, regex to `^--?[A-Za-z][A-Za-z0-9_-]*(=.*)?$`.

### F2. `review show -N` dies silently for N of about 10 or more, and out-of-range returns the oldest or nothing (D5 half-fixed) - MED
```
$ review show -20 --json     -> exit 141, no output
$ review show -66 --json     -> exit 141, no output   (65 reviews exist; expected "review: no such review", exit 12)
$ review show -6             -> prints #2774, the oldest-but-one; -1..-6 work
```
Cause: `review_rows | tail -n N | head -n 1` under `set -o pipefail`; `head` exits early, `tail` gets SIGPIPE when rows exceed the pipe buffer (review rows are large). For N above the row count, `tail` returns everything and `head` returns the oldest instead of erroring.
Fix: `/Users/alcatraz627/Code/local-models/bin/review:87`, use `review_rows | jq -rs --argjson k "${want#-}" 'if length >= $k then .[-$k].n else empty end'`.

### F3. `lm gemini show <missing or bad>` exits 1 with no message (the D3 class, survives in show) - MED
```
$ lm gemini show 9999999   -> exit 1, empty output
$ lm gemini show           -> exit 1, empty output
```
Expected: "no entry #9999999" (exit 12) or the usage line (exit 2). `/Users/alcatraz627/Code/local-models/lib/gemini:161` captures `jsonl_entry` output into `SHOWN` and `|| exit $?` discards the message. Same root as F9: `jsonl_entry` prints its errors to stdout.
Fix: `lib/gemini:161`, on failure print `$SHOWN` to stderr; and move the echo lines in `_lib.sh:43,46,48` to stderr (F9).

### F4. The typo guard from idea 5 blocks real multi-word prompts, and `--` does not bypass it - MED
```
$ q commits since friday       -> exit 2  "q: 'commits' is not an intent. Did you mean 'commit'?"
$ q --json titles for blog posts -> exit 2, plain text, nothing on stdout
$ q -- commits                 -> exit 2  (the code comment says `--` sends it anyway; it does not)
```
The comment at `/Users/alcatraz627/Code/local-models/bin/q:183` says "a lone word", but `bin/q:182` tests only `positionals[0]`, so any unquoted sentence whose first word is one edit from an intent (commits, titles, reviews, tile, task) is refused. Before the fix these ran.
Fix: add `&& [ "${#positionals[@]}" -eq 1 ]` at `bin/q:182`, and skip the check when `--` was seen.

### F5. One malformed history line hides every newer row, silently (timeline) or loudly (others) - MED/LOW
Sandbox q-history with a garbage third line and a valid fourth:
```
$ lm timeline            -> prints "jq: parse error ..." on stderr, shows rows 1-2 only, exit 0. Row 4 (the newest) is gone.
$ q history              -> same truncation, exit 5
$ q show 3               -> raw "jq: parse error", exit 5
$ review show -1         -> raw jq error, exit 5
```
A torn line from two concurrent writers (fleet -j N) is plausible. Fix: `bin/lm:430`, feed `tail` output through `jq -R 'fromjson? // empty'` style tolerance before the row functions; `bin/review:77` the same for `review_rows`.

### F6. Any unquoted flag-shaped word inside a prompt is rejected, and the message misdescribes why - LOW/MED
```
$ q how do I use tar -xvf
q: unknown flag '-xvf' (run q -h to list flags); use -- before a prompt that starts with -
```
The prompt did not start with a dash. Unquoted prompts (`q cmd list files -la`, `imagine a cat -ish`) now fail where they used to work. This is the cost of D2's design; the message should say "or quote the prompt". `/Users/alcatraz627/Code/local-models/bin/_lib.sh:66`.

### F7. In `--json` / `--stream-json` mode, usage errors are plain text and stdout is empty - LOW
```
$ see --json --crop      -> stderr "see: --crop needs a value", stdout empty, exit 2
$ q --json -m            -> same
$ q --json --bogus       -> same
```
q's contract (bin/q comment at `emit_error`) and CAPABILITIES say machine modes carry `{ok:false, code}`. Exit code 2 is right, the envelope is missing. `need_arg` and `reject_unknown_flag` (`_lib.sh:55-69`) run before each tool defines its `emit_error`.

### F8. D20 residual: stdout palette still written to stderr in four places - LOW
```
$ script -q /dev/null bash -c "lm last q 2>err.txt"     (stdout is a TTY, stderr a file)
$ cat -v err.txt
^[[2mq#3643^[[0m
```
Same defect class as D20, in the new `lm last` code (`/Users/alcatraz627/Code/local-models/bin/lm:454`) and in `lib/fleet:170,212` and `lib/ui-verify:180,181` (all use `$Bd/$Dm/$Rs`, decided from stdout). Use the `e*` palette from `_lib.sh:20-22`.

### F9. Exit-code table (idea 10) is not honored by the history-show verbs, and errors go to stdout (D11 residual) - LOW
Table says 2 = bad usage, 12 = missing history entry. Observed:
```
q show 9999999 / see show 9999999 / imagine show 9999999 / review show 99999999 -> exit 1, "no entry #N" on STDOUT
q show abc / see show abc / imagine show abc / review show abc -> exit 1 (table: 2), usage on STDOUT
imagine star 9999999 -> exit 12 (stderr)      <- inconsistent with imagine show -> 1
lm gemini show 9999999 -> exit 1 (and no text, F3)
```
Fix once in `/Users/alcatraz627/Code/local-models/bin/_lib.sh:43,46,48`: `>&2`, return 12 for missing and 2 for non-numeric. Also `imagine prune` "trash not found" echoes to stdout (`bin/imagine:202`).

### F10. `lm timeline 0 --errors` (or `--tool`) prints every row - LOW
```
$ lm timeline 0 --errors --tool see     -> 3 rows;  lm timeline 0 -> nothing
```
jq `.[-0:]` is the whole array; `/Users/alcatraz627/Code/local-models/bin/lm:440`. Reject N=0 or use `.[length-$n:]` with a floor.

### F11. Flag handling inconsistent on the small verbs - LOW
- `warm --json` -> "unknown verb '--json'" exit 2 while `warm status --json` works.
- `lm doctor --bogus`, `lm status --bogus`, `lm models --bogus` run normally (exit 0); `--json` is honored only as the first word (`lm doctor --bogus --json` prints text). `bin/lm:496-498`.
- `lm last --errors` answers "unknown tool '--errors'" (the timeline's error leaking through); `imagine critique -h` answers "no such image: -h" (`bin/imagine:291`).
- `need_arg` rejects a legitimately empty value: `imagine --neg ""`, `q --ctx-name ""` now exit 2 (`_lib.sh:56`, requires non-empty `$3`).

### F12. `see` logs a typo'd path or non-image as a failed read - LOW
`see` now writes an error row for exit-12 input mistakes (`img_unreadable`, `not_an_image`; `bin/see:105-107`). My F1 probe created see#1242 this way, and `lm timeline --errors --tool see` now lists it. Only runtime failures should be rows; exit 2 is already excluded, 12 should arguably be too.

### F13. `q` JSON `entry` and the stats-line `q show N` can point at another call's row - LOW (UNCONFIRMED by run)
`/Users/alcatraz627/Code/local-models/bin/q:764` computes the entry number as `line count + 1` before the history append at `bin/q:795`. Two q processes finishing close together (`lm fleet -j 4`, the running benchmark) get the same number. Read, not induced (a concurrent run needs several model calls).

### F14. `lm doctor` cascades one outage into six misleading failures - LOW
With the server unreachable (`env OLLAMA_HOST=http://127.0.0.1:1 lm doctor`): `FAIL server up`, then FAIL for every tier, vision and embed "on disk". Only the first is true. `bin/lm:291-320`: skip the disk checks (or mark them "unknown") when `/api/tags` is empty. Exit code 1 and the count (7) are right.

## Held under attack

| Item | Attack | Result |
|---|---|---|
| D1 timeline speed | `lm timeline 3` | 0.06 s. `lm timeline 50 --errors --json` 0.83 s. `lm timeline 100000 --json` returns 5,620 rows = 63+654+18+3643+1242, the exact sum of the five logs, no "?" times, no null kinds |
| D3 missing value | `q -m`, `q --ctx`, `see --crop`, `lm gemini -m`, `imagine -m`, `review -m/--repo`, `lm timeline --tool`, `imagine critique` | all exit 2 with a one-line message (text only in --json mode, see F7) |
| D4 status | `lm status` | all 9 models, tier labels, no head -8 |
| D5 | `review show -1..-6` | newest-review semantics correct, matches `review history` (fails only at larger N, F2) |
| D6 | pty run of `q "say ok"` | stats line shows model, `cold`, tokens, tok/s, `q show N`; `q history` shows model |
| D7 | `lm timeline --tool see --errors --json` | old rows 488 and 489 flagged by text, new error rows flagged |
| D8 | read `lib/gemini:81-88,329,363` | reason kept, real ms from a python clock; old rows 653/654 show 4000ms but predate the fix |
| D9 | timeline, q/see/imagine/gemini history | local `MM-DD HH:MM`; sandbox 09:00Z shows 14:30 |
| D10 | `lm doctor`, `--json`, injected outage | yq, all tiers, vision, embed, mlx, PATH target, gemini key present; exit 1 and failure count correct |
| D11 | unknown verb, warm usage, imagine usage | on stderr (residuals in F9) |
| D12 | `lm help` for every job and tool (25 inputs), `lm <tool> -h` for 11 tools | every one routes, exit 0; unknown job exit 2 with did-you-mean; `lm statsu` suggests status |
| D13 | rg for the old strings | gone |
| D14 | `q history 1 --json`, `q history --json 1`, `imagine history 1 --json`, `lm gemini history 3 --json`, `review history --json` | all emit NDJSON with `n` |
| D15, D16 | read; sandbox with a critique row | `imagine history/show/lm last imagine/lm timeline` all render the critique row, `imagine redo 2` refuses it with exit 12 |
| D17 | `lm gemini watch abc` / `watch 0` | exit 2 clean message / exit 12 clean message |
| D18, D19 | `lm models` vs `lm status`; `warm status` | sizes agree; "nothing resident (idle, ~0 RAM)" |
| D21 to D23 | read | direct route reachable via `--direct`, docs and alignment fixed |
| D20 | `NO_COLOR` code paths read | `use_color_fd`, python `isatty and not NO_COLOR` in q:720 and gemini-stream, lm_step all correct (residuals in F8) |
| Idea 1 | `lm last see/q/fleet/gemini/imagine`, `lm last nonexistent` | open the right entry with correct line numbers (checked against `wc -l`), exit 2 / 12 as designed |
| Idea 2 | `q --json` | `intent`, `entry`, `cold_load` present and correct for a serial call |
| Idea 5/6 | `lm statsu`, `lm --version/-V/version` | suggestion and `lm 1.1` |
| Empty history | sandbox `lm last see`, `lm timeline --tool fleet --json` | "no history yet" exit 12; `[]` |
| `-1`/`-2` indexes | `q show -1`, `review show -2` | correct; `q show -2` on a malformed line is F5 |
| Syntax | `bash -n` on lm, q, see, lib/gemini | clean |

Not exercised (outside the allowed calls): `scripts/verify.sh`, any generation, `lm gemini` prompts, `warm on/off`, server-down branches of imagine critique, a concurrent q run for F13.
