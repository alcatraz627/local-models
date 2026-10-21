# Adversarial review of the lm CLI suite (2026-10-22)

Scope: `bin/lm`, `bin/_lib.sh`, `bin/q`, `bin/see`, `bin/warm`, `bin/review`, `bin/imagine`,
`lib/gemini`, `lib/gemini-stream.py`, `lib/gemini-direct.py`, `config.sh`, `docs/CAPABILITIES.md`,
`docs/STATE.md` (first 80 lines). No source file was edited.

Method: every finding below was either run (command and observed output quoted) or read
(file:line quoted). Model calls used: 2 on the small tier. One was deliberate (`q --json "say ok"`).
The other was accidental, and it is finding D2: `q --bogus-flag` was sent to the model as a prompt.
No imagine, review, fleet, bench, image `see`, gemini prompt, pull, delete or warm on/off was run.

Ranking is by owner impact: what bites daily use first, cosmetic last.

---

## Defects

### D1. `lm timeline` takes about 43 seconds, even for one row

```
$ /usr/bin/time -p lm timeline 1
2026-10-21T21:15:38Z  q        ask  say ok
real 42.68   user 40.39
```

Cause: `bin/lm:316` runs `gsub("\\s+"; " ")` over every **whole** prompt in the 12 MB
`logs/q-history.jsonl` (3,542 entries, many with full documents inlined) and only then slices
`[0:56]` and `tail`s. Measured on the same file (scratch script, same jq expression):

| variant | wall time |
|---|---|
| current (gsub the whole prompt) | 44 s |
| slice first: `(.prompt[0:200] \| gsub(...))[0:56]` | 1 s |
| `tail -n N` the file first, then jq | 0 s |

Fix (`bin/lm:316-324`): slice before gsub in all five jq lines (`(.prompt[0:200] | gsub(...))`).
Also `tail -n "$n"` each file before jq: the newest N rows overall are always inside the newest
N of each file. Both changes are one-liners. The view the owner opens to see what happened is
currently the slowest command in the suite.

### D2. Unknown flags silently become the prompt and fire a model call (paid on gemini)

```
$ q --bogus-flag
This is not a valid command or flag. Please provide a complete command or specify what you are trying to achieve.
$ q history 3
3541  21:15:28  ask  3034ms  --bogus-flag
```

The same pattern exists in the history from real use: `see history` entry 489 has the prompt
`--quiet`, because `see` does not know `--quiet` (only `lm gemini` does). It became the diff
"focus" text. Parsers that fall through to positionals: `bin/q:174`, `bin/see:195`,
`bin/imagine:355`, `lib/gemini:134`. In `lm gemini` the typo goes to the **paid API**
(for example `lm gemini --quite "…"`). I did not run that, per scope, but the code path is the same `*)` branch.

Fix: in each parser, before the `*)` branch, add
`-?*) emit_error invalid_args "unknown flag '$1' (see <tool> -h); use -- before a prompt that starts with -" 2 ;;`
and a `--) shift; positionals+=("$@"); break ;;` case. One shared helper in `_lib.sh` would keep the
message identical across tools.

### D3. A flag with a missing value exits 1 with no message at all

```
$ q -m            → exit 1, no output
$ q --ctx         → exit 1, no output
$ see --crop      → exit 1, no output
$ lm gemini -m    → exit 1, no output
$ imagine critique → exit 1, no output
```

Cause: `shift 2` fails under `set -e` (`bin/q:159-172`, `bin/see:188-193`, `lib/gemini:128-133`,
`bin/imagine:339-351`). For `imagine critique`, `bin/imagine:286` runs `shift` with no args.
Fix: add `need_arg() { [ $# -ge 2 ] || { echo "$TOOL: $1 needs a value" >&2; exit 2; }; }` to
`_lib.sh` and call `need_arg "$@"` before each `shift 2`. In `critique_image`, check
`[ -n "${1:-}" ] || { echo "usage: imagine critique IMG [\"goal\"]" >&2; return 2; }`.

### D4. `lm status` silently hides the big tier

```
$ lm status
models   on disk
  qwen3-embedding:0.6b ... (8 rows)
  gemma4:e4b-it-qat ...
```

There are 9 models on disk (`lm status --json` lists `gemma4:26b`), but `bin/lm:237` pipes
through `head -8` with no "+N more" marker. The 9th row is `gemma4:26b`, the **big** tier. The
glance view therefore suggests the big tier is not installed. Fix: drop `head -8`, or print
`… +N more (lm models)` when truncating. Also consider tier labels here, as `lm models` has them.

### D5. `review show -1` shows the latest q call, not the latest review, and its own footer promises otherwise

```
$ review history 3
  ...
  → review show N   (or q show N) for the full review · -1 = latest
$ review show -1
#3542  2026-10-21T21:15:38Z  [ask]  1730ms  gemma4-e4b-warm
PROMPT:
say ok
```

Cause: `bin/review:76` `exec q show "${args[@]:1}"` resolves `-1` against all of q-history.
`bin/review:73` and `docs/CAPABILITIES.md:179` both claim "-1 = latest". Fix: when N is
negative, map it through the review-filtered line numbers already computed at `bin/review:69`
(take the |N|-th from the end of that list), then `exec q show <line>`.

### D6. You cannot see which model answered a `q` call

The text-mode stats line (`bin/q:766`) prints tokens, tok/s, seconds and `q show N`, but not
the model and not whether it was a cold load. `q history` (`bin/q:101`) also omits the model:

```
$ q history 3
3541  21:15:28  ask  3034ms  --bogus-flag
```

`see` (`bin/see:746`) and `lm gemini` (`lib/gemini:419`) both print the model on that line, so
q is the odd one out. With `--diy`, `-c` (which inherits the model) and tier aliases, the model
is exactly the thing that varies. Fix: `q:766` should print `"· %s · %s in / %s out · ..." % (model, ...)` and add
`cold` when `keep == "0"`. `q:101` should add `\(.model)` after the intent.

### D7. Failed `see` reads are logged as successful reads, and other `see` failures are not logged at all

```
$ see history 6
 488  21:14:41  mlx:/nonexistent/model  1866ms  .../f3/a.png  describe
$ see show 488
(visual read failed — the deterministic evidence pack below is complete)
```

The raw entry has `"mode":"diff"`, but the history line says `describe`. It also shows a model
that never answered, with a duration, and carries no error field. The soft-fail path
(`bin/see:609-613`) writes history through the normal tail (`bin/see:694-702`) with no failure
marker. `see`'s own `emit_error` (`bin/see:95-101`) never writes history, unlike q's
(`bin/q:664-671`), which logs failures as `"error": code`. So `lm timeline` can show ✗ for q
and gemini but never for see. Fix: add `error:(if $vf then "vlm_unavailable" else null end)`
to the history jq at `see:694`, and a `log_fail` call inside `emit_error`. Render `\(.mode)` and a
✗ in `see:106` and in the timeline's see line (`lm:320`).

### D8. A gemini failure's history keeps the code but drops the reason and the duration

```
$ lm gemini history 3
 648  15:06:04  error  0ms  The entire review pack is provided inline on stdin
$ lm gemini show 648
# lm gemini error  ·  2026-10-21T15:06:04Z  ·  gemini-4-argon  ·  session: local-models
gemini_error
```

`lib/gemini:79` calls `log_line "error" "$1" ""`, so the response is just the code. The message
(`$2`, which holds the actual stderr tail or the timeout cause) and the elapsed time are lost.
A paid call that ran for minutes shows `0ms`. Separately, every success has whole-second
precision dressed as ms (`3000ms` in rows 646 and 647), from `lib/gemini:300,326` using
`date +%s`. Fix: `log_line "error" "$1: $2" "$(( ($(date +%s) - ${t0:-$(date +%s)}) * 1000 ))"`,
use `python3 -c 'import time;print(int(time.time()*1000))'`, as `see` does, for t0/ms, and
print `.stream` in `show` so the step log is one copy-paste away.

### D9. History times are UTC with no marker

My call at 02:45 local time (IST) shows as `21:15:38` in `q history`, `see history` and
`lm gemini history` (`bin/q:101`, `bin/see:106`, `lib/gemini:142` all slice `.ts[11:19]` of a
`...Z` timestamp). There is no date and no `Z`, so last night's call reads as this evening's.
Fix: in those three jq formats, replace `.ts[11:19]` with
`(.ts | fromdateiso8601 | strflocaltime("%m-%d %H:%M"))`.
`lm timeline` (`lm:316-324`) prints the full UTC ISO time, which is at least labeled, but it
should use the same local format.

### D10. `lm doctor` says "all checks passed" while it skips the dependencies that actually break things

```
$ lm doctor
  ok   on PATH: q -> /Users/alcatraz627/Code/local-models/bin/q
  ...
all checks passed
```

- **`yq` is not checked**, yet every intent reads its TOML through it (`bin/q:33,129-131`).
  Each read is `2>/dev/null`, so without yq every intent silently loses its system prompt
  (`SYS=""`) and `needs_ctx`. The tool keeps answering, just wrongly.
- Only the warm model is checked (`bin/lm:252`). big, code, sweep, `VISION_MODEL`
  (minicpm-v4.6, the `see` default), `RAG_EMBED_MODEL` and the MLX `UI_VISION_MLX` HF cache
  (the `see --ui` default) are not.
- The PATH line claims `q -> …/bin/q`, but the check is only `command -v q` (`bin/lm:256`), so any
  `q` on PATH passes.
- The gemini line checks the binary, not the key (`~/.gemini/.env` or `GEMINI_API_KEY`).
- `docs/CAPABILITIES.md:273` calls it an "11-point smoke check". It prints 13 required plus 5 optional checks.

Fix: add `check "yq installed" command -v yq` and loop `check "tier $t ($(resolve_tier $t))"` over
small/big/code/sweep plus VISION_MODEL and RAG_EMBED_MODEL, using the same `/api/tags` body. Compare
`command -v $c` against `$BIN/$c` (or the `~/.local/bin` wrapper target). Add an `opt`-style line
for the gemini key file. Add `--json` (see D14).

### D11. Errors and usage text go to stdout

- `bin/lm:365`, unknown verb: `echo "lm: unknown …"` with no `>&2`.
- `bin/lm:347`, opencode missing.
- `bin/warm:96`, usage on a bad verb.
- `bin/imagine:268,269,287,361`, usage and "no such image".
- `bin/imagine:295,370`, progress and notes.

Anything piping these (`lm foo | jq`, `imagine critique x.png > notes.md`) gets error text in the
data. Fix: append `>&2` on each line listed above.

### D12. The unknown-verb hint is stale, and `lm help <verb>` does not route to the verb's help

```
$ lm nonexistent-verb
lm: unknown 'nonexistent-verb' — try: lm · lm q · lm imagine · lm warm · lm status · lm models · lm doctor · lm timeline · lm examples
$ lm help see
unknown job: see          (exit 2)
```

The hint (`bin/lm:365`) names 9 of the 20 dispatched verbs. It omits see, review, gemini, fleet,
rag, index, ui-verify, probe, bench, opencode and help. `lm help see` fails, although `see -h`
exists, and the error lists neither the jobs nor the fix. `lm rag` is dispatched (`bin/lm:340`) but
absent from the overview. Fix: at `bin/lm:113`, before the `*)` branch, add
`q|see|imagine|review|warm) exec "$BIN/$1" -h ;; gemini|fleet|rag|index|ui-verify|bench) exec "$BIN/lm" "$1" -h ;;`.
Make the fallback print the job list. Change `bin/lm:365` to `>&2` and point to `lm` (the overview)
rather than a partial list. Add an `lm rag` row to `overview()`.

### D13. Help text that contradicts behaviour

| Claim | Where | Reality |
|---|---|---|
| `schnell  (default)` | `bin/imagine:153` | `config.sh:25` sets `IMAGINE_MODEL=qwen`, and the comment says schnell was dropped |
| `lm models … (★ default · ● resident)` | `bin/lm:32`, `bin/q:51` | `lm models` prints no ★ (the default is labeled `small`) |
| `lm gemini models … (★ = default)` | `bin/lm:174` | the output uses `*` |
| `lm timeline [N]  merged q + imagine history` | `bin/lm:34` | it merges q, imagine, see, fleet and gemini (`lm:315-324`) but not compare-history or opencode-history |
| `-m … small \| big \| code \| <name>` | `bin/q:72` | `sweep` is also a reserved alias (`_lib.sh:57`) |
| `q <intent>` list of 8 intents | `bin/q:45` | the registry has 12 (`q intents`); review, complete and code-dispatch are missing |
| "11-point smoke check" | `CAPABILITIES.md:273` | 18 lines |
| schnell "fast ~25s" | `bin/imagine:153` | `CAPABILITIES.md:192` says ~46s |

Fix: edit each string. The q usage line could be generated from `intents/` the same way
`list_intents` already is.

### D14. `--json` is missing or silently ignored on observability verbs

- `q history 1 --json` prints the text view. `--json` is honoured only directly after `history`
  (`bin/q:113`), and imagine has the same bug (`bin/imagine:309`).
- `see history --json` silently prints text (`bin/see:105`).
- There is no `--json` for `lm doctor`, `lm timeline`, `warm status`, `lm gemini history` or `review history`.
  `lm status` and `lm models` have one.
- `q history --json` emits raw lines without their line number, so a consumer cannot then call `q show N`.

Fix: parse `--json` anywhere in the history args, put a shared `jsonl_history_json` in `_lib.sh` that
emits `{n, …entry}` per line, and add `--json` to doctor (array of `{label, ok, optional}`) and to timeline.

### D15. `lm gemini --fallback-local` reports the wrong model when the big tier changes

`lib/gemini:340` hardcodes `model:"gemma4:26b"` in the JSON. The call itself uses `q -m big`
(`lib/gemini:336`), so if `BIG_MODEL` changes the envelope lies. Fix:
`--arg lm "$(resolve_tier big)"` and `model:$lm`.

### D16. `imagine critique` breaks the residency contract and the host override

`bin/imagine:300` posts to a hardcoded `http://127.0.0.1:11434` (ignoring `OLLAMA_HOST`) with
no `ollama_ensure`. lm-serve stops the server after idle, so this fails with no message. The
request sends no `keep_alive`, so it falls to the server default of 0 and **unloads a leased
`gemma4:26b`**. That violates the `_lib.sh:105-110` "every API caller MUST check" rule that
q and see follow. Critiques are not logged to any history either. Fix: `ollama_ensure || { server_down_msg; return 10; }`,
`$OLLAMA_HOST`, `keep_alive: (if ollama_resident "$model" then -1 else 0)`, and one line
appended to `imagine-history.jsonl` with `kind:"critique"`.

### D17. `lm gemini watch <non-number>` leaks a raw sed error

```
$ lm gemini watch abc
sed: 1: "abcp
": command a expects \ followed by text      (exit 1)
```

`lib/gemini:148`. Fix: `[[ "${positionals[1]:-1}" =~ ^[0-9]+$ ]] || emit_error invalid_args "watch N: N is a number (1 = newest)" 2`.

### D18. `lm models` and `lm status` disagree on sizes, and `lm models` drops two tiers

`lm status` shows `granite4:tiny-h  4.2 GB` (ollama's decimal GB). `lm models` shows `3.9GB`
for the same model (`bin/lm:299` divides by 1073741824, which is GiB, but labels it GB). `lm models`
also does not label the sweep tier (granite4:tiny-h) or the vision model (minicpm-v4.6), and its
`tiers` footer (`lm:305`) omits sweep and vision, though `--json` includes sweep. Fix: divide by 1e9
(matching ollama and the disk-budget doctrine's `du`). Add `sweep` and `vision` to the
`$tier` map and the footer.

### D19. `warm status` with nothing resident prints a bare header

```
$ warm
NAME    ID    SIZE    PROCESSOR    CONTEXT    UNTIL
```

`lm status` says `none (idle, ~0 RAM)` for the same state. Fix at `bin/warm:73`: reuse
the `lm_status` "none" branch, or `ollama_cli ps | awk 'NR>1' | grep -q . || echo "nothing resident (idle, ~0 RAM)"`.

### D20. NO_COLOR is honoured only on stdout help

`_lib.sh:15` gates colours on stdout TTY and NO_COLOR. The stderr channels ignore NO_COLOR:
`bin/q:212,542,573` (diy and web narration), `bin/q:709` (python stats, thinking dim),
`lib/gemini-stream.py:169,176` and `lib/gemini-direct.py:34`. gemini-direct.py always emits ANSI,
even when stderr is a file. `lm_step` (`_lib.sh:81`) prints `$Dm` to stderr but `$Dm` was decided
from **stdout**'s TTY, so `LM_PROGRESS=1 see … 2>log` writes escape codes into the log when stdout
is a terminal. Fix: export a `_lib.sh` helper `use_color_fd N` and gate each stderr colour on
`[ -t 2 ] && [ -z "$NO_COLOR" ]`. In python, use `sys.stderr.isatty() and not os.environ.get("NO_COLOR")`.

### D21. `lib/gemini-direct.py` sits outside the suite's own contracts

It was added in 5d48e27 and is the documented route for large packs, but:

- It is not reachable from `lm gemini` (rg finds no caller in bin/ or lib/).
- It writes no history, which breaks "histories are the API".
- Its docstring usage names `argon_direct.py`.
- It crashes with a bare `StopIteration` if the key line is missing (`:10`).
- It skips the GEMINI_MODELS pick-list validation.

Fix: expose it as `lm gemini --direct` (or a `direct` verb), have it append to `gem-history.jsonl`
with `kind:"direct"`, and fix the docstring.

### D22. Stale docs

- `docs/STATE.md:3` says "Reviewed 2026-09-27", but the latest commits are from 2026-10-21.
- `STATE.md:36` says timeline merges "q/imagine/see/fleet"; it also merges gemini.
- `STATE.md:58-59` lists histories without `gem-history`, `compare-history` or `opencode-history`.
- `STATE.md:68` omits `review-pr`.
- `STATE.md:70-71` lib list omits `rag`, `websearch`, `gemini-stream.py`, `gemini-direct.py` and `vis-*`.
- `bin/lm:48` "per-command help" names only q, imagine and warm.

### D23. Cosmetic: overview misalignment

`bin/lm:25,29` pad `'lm fleet <intent> …'` and `'lm ui-verify <img> …'` with `%-20s`, which
counts bytes. The 3-byte `…` makes those two rows one column short, and you can see it in the `lm` output.
Use `...` or pad by hand.

---

## Improvement ideas (not defects)

1. **One cross-tool "what just happened".** Add `lm last [tool]` and make `lm timeline` print the
   per-tool entry number (`q#3542`, `see#489`, `gem#648`), so a timeline row leads directly to `<tool> show N`.
   Add `lm timeline --errors` and `--tool see` filters, with a `--json` form.
2. **Add `intent`, `entry` and `cold_load` to the q `--json` envelope** (`bin/q:772`). Today a
   machine caller cannot tell a cold load from a warm one or find the history line it produced.
3. **Rotate or compact history.** `q-history.jsonl` is 12 MB because full documents are stored in
   `prompt`. Store the user's own words plus a `ctx_name` and `ctx_chars`, and keep the full
   prompt only for the last N entries. Every `q -c` slurps the whole file (`bin/q:604`) and every q
   call counts its lines (`bin/q:751`).
4. **Keep internal calls out of the owner's history.** `diy-plan` planner sub-calls show up as
   their own entries (`q history` row 3539). Tag them `internal:true` and hide them by default.
5. **Did-you-mean for `lm` verbs and q intents.** The verb list is closed and small, so an edit-distance
   suggestion is a few lines.
6. **`lm --version`** prints `LM_VERSION` (already in `config.sh:21`). Today it is "unknown".
7. **tok/s from `eval_duration`.** The q stats line divides output tokens by total wall time,
   including the cold load (`bin/q:765`), so a cold call reports a misleadingly low tok/s.
8. **One shared arg-parse helper** in `_lib.sh` (need_arg, unknown-flag rejection, `--`). That
   would fix D2 and D3 in one place and keep error text identical across tools.
9. **`lm status` should show the lease TTL and the tier mapping** (the `UNTIL` column from `ollama ps`
   is already there in `warm status`), so one command answers what is warm, for how long, and as which tier.
10. **A consistent exit-code table.** q and see use 2, 10, 11, 12 and 13 deliberately, while warm,
    imagine and lm use 1 for everything and review uses 1, 2 and 3. Document one table in
    `CAPABILITIES.md` and adopt it in warm, imagine and lm.

---

## UNCONFIRMED

- Server-down behaviour of `lm status`, `lm models`, `warm` and `imagine critique` was read, not
  induced. Stopping the server was out of scope.
- D2 on `lm gemini` (a typo'd flag sent as a paid prompt) is from code reading at `lib/gemini:134`.
  It was not run because it would make a paid call.
- D16's "unloads a leased gemma4:26b" follows from the server's `KEEP_ALIVE=0` (STATE.md:41) and
  the missing `keep_alive` field. It was not exercised.
- D20's escape codes in a redirected log were inferred from `_lib.sh:15,81`, not captured.
