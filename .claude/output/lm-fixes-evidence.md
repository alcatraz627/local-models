# lm CLI fixes: before and after evidence

Worktree: `/Users/alcatraz627/Code/local-models-lm` (branch `lm-ergonomics`).
Before = the unfixed main checkout `/Users/alcatraz627/Code/local-models` (or the review's quoted output where the call costs money). After = this worktree.
Every command below was run from absolute paths into the worktree's `bin/`. Real 12 MB histories were copied into the worktree's gitignored `logs/` and `outputs/` first.

Exit codes are shown as `[exit N]`. Raw runs: scratchpad `pairs.txt`, `verify1.txt`, `verify2.txt`.

## Shared helpers (D2, D3, idea 8)

`bin/_lib.sh` now holds `need_arg`, `reject_unknown_flag` (flag-shaped words only, so `-`, `-1` and prompts with spaces stay positionals; `--` ends flags), `jsonl_history_json`, `did_you_mean`, `use_color_fd`, `JQ_LOCAL_TS` and a stderr palette. Wired into q, see, imagine, review, lib/gemini (and `lm timeline`).
Codex's uncommitted helpers were reviewed: `need_arg` and `jsonl_history_json` kept as written. `reject_unknown_flag` rejected any `-*` word including `-` and prompts like "- fix this", so it was narrowed. The q stats line had lost its colour reset (`rs`), restored. The q history local time had no `try`, so a malformed ts would abort jq; replaced by the shared `lts` def.

## D1 timeline speed

Before (`lm timeline 1`, real histories): `real 0m39.231s` (review measured 42.68 s).
After:
```
$ time lm timeline 20            real 0m0.061s
$ time lm timeline 20 --errors   real 0m0.760s   (scans newest 5000 entries per log)
```
Fix: tail each log first, slice the prompt to 200 chars before `gsub`.

## D2 unknown flags become the prompt

Before: `q --bogus-flag` answered "This is not a valid command or flag..." (a model call, entry 3541); `see history` entry 489 stored `--quiet` as the prompt.
After:
```
$ q --bogus-flag      q: unknown flag '--bogus-flag' (run q -h to list flags); use -- before a prompt that starts with -   [exit 2]
$ see --quiet         see: unknown flag '--quiet' (run see -h to list flags); ...   [exit 2]
$ lm gemini --quite hi  lm gemini: unknown flag '--quite' (run lm gemini -h to list flags); ...   [exit 2]   (no API call)
$ imagine --bogus "a cat"  imagine: unknown flag '--bogus' ...  [exit 2]
$ review --bogus      review: unknown flag '--bogus' ...  [exit 2]
```
Still working: `q show -1` (history index), `review show -1`, `review --staged` (explicitly allowed in the review parser), and `--` to send a dash prompt.

## D3 missing flag value

Before: `q -m`, `q --ctx`, `see --crop`, `lm gemini -m`, `imagine critique` all `[exit 1]` with no output.
After:
```
q -m                 q: -m needs a value                       [exit 2]
q --ctx              q: --ctx needs a value                    [exit 2]
see --crop           see: --crop needs a value                 [exit 2]
lm gemini -m         lm gemini: -m needs a value               [exit 2]
imagine critique     usage: imagine critique IMG ["goal"]      [exit 2]
```

## D4 lm status hid the big tier

Before: 8 model rows, `gemma4:26b` cut by `head -8`. After: all 9 rows, with tier labels (`tier sweep|vision|embed|code|small|big`), and the last row is `gemma4:26b ... tier big`.

## D5 review show -1

Before: `review show -1` printed `#3640 ... [ask]` (a q call). After: `#3107 ... [review] ...` (latest review). `review history` is numbered by q-history line and shows local time.

## D6 model not visible

After (pty run, the stats line only prints on a terminal):
```
$ script -q /dev/null q "say ok"
Ok.
· gemma4-e4b-warm · cold · 78 in / 3 out · 93 tok/s · 1.5s · q show 3544
$ q history 2
3552  10-22 03:07  diy-plan  gemma4-e4b-warm  2580ms  kill whatever is on port 9999
```

## D7 failed see reads logged as successes

Before: `see history 6` row 488 said `describe` with a model that never answered, no failure marker, and `see` runtime errors wrote no history.
After:
```
$ see /nonexistent2.png          see: no such file: /nonexistent2.png   [exit 12]
$ see history 1                  494  10-22 03:13  read ✗  minicpm-v4.6  0ms  /nonexistent2.png  describe
$ see diff a b -m mlx:/nonexistent/model --json     (mlx load fails, pack still ships)
$ see history 3
 492  10-22 03:12  diff ✗ ...
 493  10-22 03:12  diff ✗  mlx:/nonexistent/model  7208ms  .../f3/a.png  describe
$ lm timeline 4 --tool see       see#492 diff ✗ ... / see#493 diff ✗ ...
```
Rows now carry `error` (`vlm_unavailable` for a soft-failed diff, the emit_error code otherwise). Old rows without the field are recognised by their "(visual read failed" response, so entries 488 and 489 also show the mark. Usage errors (exit 2) are not logged.
Not done: `describe` is still the last column for diff rows in `see history` because that column is the prompt placeholder; the mode is now the second column (`diff`).

## D8 gemini failure history

Before (`lm gemini history 3`): `648  15:06:04  error  0ms  The entire review pack...`, response = the bare code `gemini_error`.
After: error rows hold `code: message` and the real duration. A real failed call from the verify run:
```
657  10-22 03:09  error  95834ms  What TOML file was ingested into this session? Fil
$ lm gemini show 657
gemini_error: Error starting session: Session ID "614d5979-..." already exists. Use --resume ...
steps: python3 lib/gemini-stream.py render .../logs/gemini-live/20261021T213911Z-28331.jsonl
```
Success rows have millisecond precision (`7126ms` for verify's one-shot, not `3000ms` steps).
Side finding, not fixed (out of scope): that failure is an existing bug where the one auto-retry after a timeout reuses `--session-id` for a brand-new session, which gemini-cli rejects with "already exists".

## D9 UTC times

Before: `21:15:28` (UTC, no date). After, local `MM-DD HH:MM` in `q history`, `see history`, `lm gemini history`, `review history`, `imagine history` and `lm timeline`:
```
3541  10-22 02:45  ask  gemma4-e4b-warm  3034ms  --bogus-flag     (same entry, 21:15:28Z)
```

## D10 lm doctor

After, with a deliberately broken config (the guard's opposite proof):
```
$ BIG_MODEL=nonexistent:1b VISION_MODEL=nonexistent-vision lm doctor
  FAIL tier big on disk (nonexistent:1b)
  FAIL vision model on disk (nonexistent-vision)
2 check(s) failed   [exit 1]
```
Clean run: yq, jq, ollama, server, LaunchAgent, tiers small/big/code/sweep, vision, embed, MLX vision cache, mflux venv, PATH wrappers that reach THIS checkout, logs dir, optional extras plus the gemini API key. From the worktree with the real `~/.local/bin` wrappers the six PATH lines FAIL (they point at the main checkout), which is the intended behaviour; with worktree wrappers on PATH all pass. `lm doctor --json` returns `{"ok":true,"failed":0,"checks":[{label,ok,optional},...]}`. CAPABILITIES no longer says "11-point".

## D11 errors to stdout

Before: `lm foo 2>/dev/null` and `warm bogus 2>/dev/null` still printed the error. After both print nothing on stdout (`done` only). Also moved: opencode-missing, imagine usage, "no such image", imagine notes and progress.

## D12 verb hints

Before: `lm nonexistent-verb` listed 9 of 20 verbs on stdout, exit 1; `lm help see` was `unknown job: see`.
After:
```
lm nonexistent-verb   lm: unknown verb 'nonexistent-verb'; run lm for the full list   [exit 2]
lm timline            lm: unknown verb 'timline' (did you mean 'timeline'?); ...       [exit 2]
lm help see           prints see's help   (also q imagine review warm probe ui-verify index bench opencode)
lm help sse           lm help: unknown job 'sse' (did you mean 'see'?) + job and tool lists   [exit 2]
```
`lm` overview gained `lm rag` and `lm last`, per-command help names every tool.

## D13 help text

- `imagine -h`: `qwen  (default)` now follows `IMAGINE_MODEL`; schnell says `~46s`.
- `lm models` / `q models` help: star removed. `lm examples`: `(* = default)`. timeline description lists q/imagine/see/fleet/gemini. `q -m` lists `sweep`.
- q usage line lists the 12 intents, generated from `intents/*.toml`.

## D14 --json

```
q history 1 --json            {"ts":...,"intent":"summarize",...,"n":3553}
see history 1 --json          {...,"mode":"ocr",...,"n":491}
review history 1 --json       {...,"intent":"review",...,"n":3107}
lm gemini history 3 --json    (same row shape with n)
imagine history 2 --json      (same)
warm status --json            {"server":"up","resident":[{"name":"gemma4-e4b-warm:latest","size":5551916317,"expires_at":"..."}]}
lm doctor --json, lm timeline --json   (above and below)
```
`--json` works in any position after `history`.

## D15 fallback-local model name

`lib/gemini` now uses `resolve_tier big` for the JSON `model` and calls `$DIR/bin/q`. Read-verified; the fallback path was not run (needs an unavailable gemini).

## D16 imagine critique

After (small tier as critic to keep it cheap):
```
$ IMAGINE_CRITIC_MODEL=gemma4-e4b-warm imagine critique probe/fixtures/ocr-fixture.png "a plain fixture"
  (critiquing ... with gemma4-e4b-warm — loads on demand)      <- on stderr
(1) WHAT IT IS: A white, blank canvas with minimal text ("VERIFY FIXURE" ...
$ imagine history 2
  19    10-22 03:11  critique  3924ms  .../ocr-fixture.png
$ lm timeline 3 --tool imagine
10-22 03:11  imagine#19   critique  a plain fixture
```
It now runs `ollama_ensure`, honours `OLLAMA_HOST`, sends `keep_alive` -1 when the model is already resident else 0, and logs a `kind: critique` row (image path in `.image`, never `.output`, so `prune` ignores it). `imagine redo 19` refuses cleanly (`entry #19 is a critique`, exit 12), `prune` and `gallery` still run. UNCONFIRMED: the server-down path (`return 10`) was read, not induced.

## D17 watch abc

Before: `sed: 1: "abcp ... command a expects \ followed by text [exit 1]`. After: `lm gemini: watch N: N is a number (1 = newest) [exit 2]`.

## D18 lm models vs lm status

Before: `granite4:tiny-h 3.9GB`, `gemma4:26b 16.7GB`, no sweep or vision labels, footer without them. After: sizes written the way ollama writes them (`4.2 GB`, `17 GB`, `639 MB`), `sweep` and `vision` labels, footer `... sweep=granite4:tiny-h · vision=minicpm-v4.6`.

## D19 warm with nothing resident

Before: bare header `NAME ID SIZE PROCESSOR CONTEXT UNTIL`. After: `nothing resident (idle, ~0 RAM)`.

## D20 NO_COLOR and stderr colour

Before (stdout a terminal, stderr to a file): `od -c` of the `lm_step` line began `033 [ 2 m [ 0 3 : 1 3 : 1 8 ...`. After: no escape bytes (`[03:13:13 q] cold load`). Stderr lines in q, review, imagine, lib/gemini now use stderr's own palette and honour NO_COLOR; `gemini-stream.py` and the q python path check `NO_COLOR`. `gemini-direct.py` emits only JSON and no ANSI (the review's claim about it does not hold in the current file).

## D21 gemini-direct

Checked, nothing still true: `--direct` and auto-routing exist in `lib/gemini`, history is written by the wrapper, the docstring no longer names `argon_direct.py`, the key lookup is a function (no `StopIteration`), and the pick-list validation runs before the backend. Not rebuilt.

## D22 stale docs

`docs/STATE.md`: review date, timeline sources, all six history files, `review-pr`, the missing lib files. `bin/lm` per-command help names every tool.

## D23 overview alignment

Overview rows use `...` and a 22-column pad, so `lm fleet <intent> ...` and `lm ui-verify <img> ...` line up with the rest (checked in the `lm` output above).

## Ideas

| # | Evidence |
|---|---|
| 1 | `lm timeline 3 --tool imagine` rows lead `imagine#19`; `--errors`, `--tool T` (with did-you-mean, e.g. `sea` -> `see`), `--json` rows `{ts,time,tool,n,kind,err,text}`; `lm last see` printed `see#493` then `see show 493`. |
| 2 | `q --json "say ok"` -> `..."intent": "ask", "entry": 3543, "cold_load": true}` |
| 5 | `q commt` -> `q: 'commt' is not an intent. Did you mean 'commit'? ...` [exit 2], no model call; `lm timline` and `lm help sse` as above. |
| 6 | `lm --version` -> `lm 1.1` (was "unknown ... try:"). Also `-V` and `version`. |
| 7 | stats line tok/s now `tok_out / eval_duration` (93 tok/s on a cold 3-token call; the old wall-time divisor would have read about 2). |
| 9 | After `warm on small 5m`: `gemma4-e4b-warm:latest  5.6 GB  until 4 minutes from now  tier small` in `lm status`; released with `warm off`. |
| 10 | Exit-code table added to `docs/CAPABILITIES.md` section 11; warm uses 10/11/2, imagine 2/10/12, lm 2/10/12. |
| 3, 4 | Skipped as instructed. |

## Verification

- `bash -n` on `bin/_lib.sh bin/lm bin/q bin/see bin/review bin/warm bin/imagine lib/gemini` all clean; `py_compile` on `lib/gemini-stream.py` clean.
- `scripts/verify.sh` (PATH wrappers pointing at the worktree, `.venv` symlinked from the main checkout):
  - first run 37 passed, 3 FAILED; final run **38 passed, 3 FAILED**.
  - The 3 failures are the known pre-existing ones: `guard-model-tier block path`, `schedule missing: warm-morning`, `launchd: com.alcatraz.warm-evening-off not loaded`. The vis battery now passes (53/53).
- Model calls used by me: q `--json "say ok"` and a pty `q "say ok"` (2 of 5), one `imagine critique` on the small tier, plus whatever `verify.sh` itself runs (its gemini one-shot and ask, a fleet item, a minicpm `see`). No imagine generation, review, bench, or gemini prompt of my own.
