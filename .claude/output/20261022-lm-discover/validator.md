# Adversarial validation: lm-discover (worktree /Users/alcatraz627/Code/local-models-disc)

Validator run 2026-10-22. Nothing fixed. Scratch evidence: /private/tmp/claude-501/-Users-alcatraz627-Code-local-models/a48a6eeb-34f8-4fed-9269-015afa95b460/scratchpad/ (how.py, errs.py, cmp.py, mut.py, disc-mut/).

Verdict: the plumbing holds (JSON valid, colour gating, idempotent generation, scripted output byte-identical to main apart from the new `remedy`/`next` fields, bare `lm` under 300 ms). `lm how` is the weak part: 13 of 69 phrasings got a wrong top answer, negation is ignored (4 cloud picks against the user's words), and `--go` runs the registry's canned example rather than anything built from the user's request. The drift fixture misses 4 of 7 mutations that matter.

Model-budget note (my own overrun): I made about 6 small-tier or vision calls instead of 3. Three were unintended: `q --json nosuchintent hi`, `lm zzzverb --json` and `see latest --json` all treat the input as a prompt or read the real newest screenshot; one was a deliberate `see ocr-fixture.png --json`; two were `lm how` model fallbacks under `--go`. Nothing over 8 GB loaded. `warm off all` run, nothing resident. Clipboard untouched. I created and then trashed `lib/__pycache__/` in the worktree (my import of verbs.py); `git status` is clean except the intentional `.venv` symlink.

## CONFIRMED findings

### F1 (High) `lm how --go` runs the registry example, not a command built from the user's words
- `<scratch>/disc-mut/base/bin/lm how "search the web for rust news" --go --no-model` (with bin/q stubbed to log) printed `q --web "current node LTS version?"` and the stub ran `--web current node LTS version?`. The user asked about rust news; a different query went to the web lane.
- Same shape: "run a shell command for me" runs `lm cmd "list the 5 largest files in ~/Downloads"`; "ask a question" runs `lm "what text is in ~/Desktop/shot.png"`.
- Expected: `--go` runs only a command that carries the user's own arguments, or refuses when the top command is a canned example.
- lib/verbs.py:298-317 (`how_answer` returns `ex["cmd"]`), :384-390 (`--go` runs it with `shell=True`).

### F2 (High) Negation is ignored; cloud lanes picked against the words (4 phrasings)
- `lm how "do not use the web, tell me what 2+2 is" --no-model` -> `q --web "current node LTS version?"`
- `lm how "tell me the latest news but keep it local" --no-model` -> `q --web ...`
- `lm how "how many tokens is this file but not on the web" --no-model` -> `q --web ...`
- `lm how "without gemini, summarize this big folder" --no-model` -> `lm gemini --file big.md "summarize the risks"`
- Expected: a negated or "keep it local" request never selects a cloud job. The trigger test is a bare word match.
- lib/verbs.py:251-252 (`cloud_ok = any(t in raw ...)`), lib/verbs.toml:49 (`cloud_triggers`). Generic triggers `current`, `online`, `research`, `news` also enable the cloud lane.

### F3 (High) Model-fallback command is executed by `--go` with `shell=True` and only its first token is validated
- Patched `subprocess.run` so the model "returned" each command (gotest.py). `how_model` ACCEPTED all of: `lm status; touch /private/tmp/claude-501/pwned3`, `lm status && echo chained`, `q --web "latest news"`, `lm gemini --file big.md "x"`, `warm off all`.
- Consequences: (a) a prompt-injected or confused model reply can chain arbitrary shell after `lm`; (b) the "never picks a cloud lane" promise is not enforced on the model path (`q --web` and `lm gemini` pass; the substring check is for the word `cloud` only); (c) the returned `job` is not checked against the `command`.
- I did not make the real model produce this, so the model-compliance half is SUSPECTED; the validation gap itself is confirmed.
- lib/verbs.py:346-356 (validation), :388-390 (`shell=True`).

### F4 (Medium) `--go` can still run state-changing or long commands with no confirmation
- `lm how "build a search by meaning index of my docs"` -> `lm rag index docs/`. `lm rag index` "rebuilds from scratch" (lib/rag:34, lib/rag.py:10), so `--go` from a directory with a `docs/` folder replaces the user's existing index. I did not execute it (code evidence only).
- Others reachable the same way: `lm review` (23 GB code model, minutes), `lm probe gemma4:26b`, `lm bench quick`, `lm fast 1h` (leaves a model warm), `lm opencode`.
- The placeholder filter (lib/verbs.py:385) is a hand list of filenames; `see dashboard.png --ui` passes it. Expected: a `--go` allow-list of read-only jobs, or a confirm step for jobs whose registry `side_effects` are non-empty.

### F5 (Medium) 13 of 69 phrasings got a wrong top answer
See the table below. Systematic misses: review vs diff (`review my git diff` -> image diff), commit message (`commit message from my diff` -> image diff), stop/unload models -> `lm models` / `lm status` instead of `lm fast off` or `warm off all`, `what did the last call say` -> timeline not `lm last`, `run many prompts in parallel` -> `lm cmd` not fleet, `generate an image of a cat` -> `imagine refine 12 "warmer light"` (a refine-history example, not a first draw).

### F6 (Medium) `lm how --go --json` mixes JSON and command output on stdout
- `lm how "what is installed" --go --json` printed the JSON line, then the `lm models` table, on the same stdout. A `--json` caller cannot parse stdout.
- lib/verbs.py:377-390.

### F7 (Medium) Several `--json` paths still emit plain text instead of the envelope
Exit codes are right, but stdout is empty or a help screen:
- `lm models --bogus --json`, `lm status --bogus --json`, `lm timeline --bogus --json`, `lm last --json`: stderr text, empty stdout, rc 2.
- `lm how --json` (empty query): stderr text only (the `no_match` path does emit an envelope; the empty-query path at lib/verbs.py:367-369 does not).
- `lm rag --json`: stderr text. `lm fleet --json` (no args) and `lm gemini --json` (no args) print a help screen (rc 2 and rc 0).
- `env OLLAMA_HOST=127.0.0.1:1 lm models --json`: `server down - start: launchctl kickstart ...` as text, rc 10.
- `warm on zzz`: `loading zzz for 60m ...` on stdout then error text, rc 11 (the build report says warm has no envelope, so this is a gap against brief item 5, not a regression).
- `imagine --json`: `unknown flag '--json'`.

### F8 (Medium) `next` values that are not runnable or not helpful
From lib/verbs.toml:72-124.
- `ctx_too_large` -> `lm gemini --file FILE` and `sheet_missing` -> `q --preflight --ctx FILE --json` hold a literal placeholder. The first also pushes the user toward the cloud lane from an error envelope.
- `ocr_missing` -> `npm install -g mac-ocr` and `repomix_missing` -> `npm install -g repomix`: an agent that runs `next` mechanically installs a global package.
- `img_unreadable` -> `lm read latest` for every missing-image case, including `see count x.png` and `see diff a.png b.png`. For a wrong path, it starts a vision read of a different image. Observed: `see /nonexistent/zz.png --json`, `see count /nonexistent/a.png --json`, `see diff ...` all return `next:"lm read latest"`.
- Other failure codes got `next:null`, which the brief allows (`invalid_args`, `ctx_unreadable`, `not_an_image`).
- `server_down` remedy "the local server was stopped; it restarts on the next call" is wrong when the cause is a bad `OLLAMA_HOST` (`env OLLAMA_HOST=127.0.0.1:1 q --json hi`; message says unreachable at 127.0.0.1:1, rc 10).

### F9 (Medium) Drift fixture survives 4 of 8 meaningful mutations
Run in scratch copies (scratchpad/disc-mut/m_*), `probe/fixtures/verbs-drift.py`, baseline 400/400.

| Mutation | Fixture | Verdict |
|---|---|---|
| bin/lm `lm last` exits 7 instead of 12 (registry says 12) | 400/400 green | MISSED: exit codes in the registry are never checked against behaviour |
| bin/lm gains a ghost verb `zap` not in registry | 400/400 green | MISSED: dispatch table vs registry is not compared, only the screens |
| lib/verbs.py cloud filter removed (`if False: continue`) | 400/400 green | MISSED: no test that cloud jobs stay out without trigger words |
| lib/verbs.py `Pal(True)` in `cmd_how` (colour when piped) | 400/400 green | MISSED: effect confirmed (`lm how ... --no-model` piped prints escapes); `lm how` plain-when-piped is untested |
| bin/q hint written to stdout instead of stderr | 400/400 green | MISSED: hint placement needs a tty and a model, so untested |
| bin/lm LM_HINTS=0 check removed | 399/400, red on "LM_HINTS=0 silences the suggestion" | caught |
| lib envelope drops remedy/next | 398/400, red on q and see envelope checks | caught |
| (build report, not re-run) typo example, stale `front_says` | red | caught |

### F10 (Low) False screenshot suggestion when `SEE_SCREENSHOT_DIR` is a file
`SEE_SCREENSHOT_DIR=<fresh .png file> script -q /dev/null lm` prints `suggest: you took a screenshot a moment ago, lm read latest`. `find <file> -maxdepth 1 -name '*.png' -mmin -10` matches the file itself. bin/lm:47. A nonexistent dir, empty string and a dir with a quote and space are silent and the screen still renders (rc 0).

### F11 (Low) Bare `lm` cost
Measured with `script -q /dev/null lm`, 3 runs each, vs 44-47 ms with `LM_HINTS=0`: default 158-182 ms; 5000-file screenshot dir 170-267 ms; osascript stubbed to sleep 8 s about 230 ms. All under 300 ms and never failed, but above the brief's 150 ms for the checks themselves in the 5000-file and slow-osascript cases. The clipboard probe is cut after about 120 ms while real `osascript -e 'clipboard info'` takes 75-96 ms, so on a loaded machine the clipboard-image suggestion will intermittently be missed (one of three runs with a fast stub that prints PNGf immediately showed no suggestion: SUSPECTED race).

### F12 (Low) `truncated` hint hard-codes 40000
bin/q (`hint_line(..., n=40000)`): the suggestion `--max-ctx 40000` is a constant, not the file's size, and it can be lower than a limit the user already passed. bin/q already prints an exact "the whole file: --max-ctx N" line at about line 713, so the new hint repeats it with a worse number. Not exercised live (needs a model run); code evidence.

### F13 (Low) Completion descriptions truncated and flag pairs mis-described
share/zsh/_q, _see: many `[...]` descriptions stop mid-sentence (`'--web[search the web first (DDG, no key) and answer from the]'`, `--menubar[... (needs]`, `--crop[... (crop-then-read]`). Pairs share the first flag's text (`--code` described as "use the big (reasoning) / code tier"). `-m`/`--model` take no value in `_see`. `zsh -n` is clean for all four, and `compinit` registers `_comps[lm|q|see|warm]`.

### F14 (Low) Man pages
`mandoc -T lint` on all four: no errors; every page warns `missing date, using "": TH` (the `.TH` line has no date) and has STYLE lines over 80 bytes. groff is not installed on this machine, so `groff -ww` was not run. `man -P cat` on lm.1 shows NAME, SYNOPSIS, COMMANDS, AGENT MENU, EXAMPLES, EXIT STATUS, FILES, SEE ALSO with no stray roff.

### F15 (Low) Smaller items
- `lm help web` differs from main: adds a blank line and `☁ This leaves your Mac.` (cmp.py). The build report only claims `help read` is identical.
- `lm how ... ` alternatives can repeat a command: "show the current models loaded in memory" -> alternatives `lm models` twice.
- `lm how "x" --jsno` silently treats the unknown flag as query words (rc 12/no_match) rather than a usage error. lib/verbs.py:364.
- `-h` is not side-effect free everywhere the registry implies: `warm on -h` tries to load a model named `-h` (rc 11, ollama call; same on main), `imagine refine -h` and `q show -h` exit 2. Fixture only checks job-level `-h`.
- `bench nosuchset` prints a Python traceback, rc 1; registry says "2 bad usage" (scripts/bench.py:93, unchanged code, registry claim wrong).
- `lm gemini --json` with no args prints help and exits 0 (registry says 2 for bad usage).
- `lm "zzzverb" --json` and `q --json nosuchintent hi` run the model (an unknown verb or intent word becomes the prompt). Pre-existing, but the new `-h`/capabilities text implies a usage error exists for unknown verbs ("2 bad usage: ... unknown verb").

## SUSPECTED (not executed or not reproduced)
- `_lm_shots` in the completion files puts `${shots}` inside a `(...)` word list: macOS screenshot names contain spaces ("Screenshot 2026-10-22 at 15.20.46.png"), which would split into several candidates. Reading only; I could not drive TAB completion (zpty and expect both failed to deliver the tab to zle in this environment), so interactive completion is UNCONFIRMED by me.
- `--go` of `lm rag index docs/` replacing an existing index (F4), by code reading.
- Model path accepting an injected shell tail (F3) given a real model reply.

## Claims that held
- `lm --capabilities --json`: valid JSON, keys `version, jobs, conventions`, 35 jobs, no escape bytes, 42-52 ms (5 runs each for `--capabilities`, `how`, `more`, `help read`).
- Exit codes listed vs observed: `lm last` no history 12, `lm help nosuchjob` 2, `lm models` server down 10, `see`/`lm read`/`lm doc`/`lm ui-verify` missing file 12, `lm timeline --bogus` 2, `lm doctor` 1, `warm on banana` 2, `warm on zzz` 11, `lm index find` (no symbol) 2, `lm probe` (no model) 2, `lm how` no_match 12, `q` unreadable ctx 12.
- Every registry usage/example first token pair answers `-h` with rc 0 and writes nothing under logs/ or outputs/ (hcheck.py), excepting the three subcommand cases in F15.
- Success-path output piped is byte-identical to main for: `lm help`, `help read|ask|count`, `status --json`, `models [--json]`, `examples`, `read|ask|cmd|again -h`, `q intents`, `q -h [--all]`, `see -h [--all]`, `warm -h`, `warm status [--json]`, `see ... --ocr`, `q --preflight --json`, `lm find`, `lm index find`. Differences are only the new `lm how` line (bare `lm`, `lm more`), the aligned `lm more` examples column, per-checkout history, artifact paths, and the known `lm doctor` PATH checks. Error envelopes differ only by the added `remedy` and `next`.
- Colour: `lm`, `help`, `more`, `--capabilities [job]`, `how` are coloured on a pty, plain with `NO_COLOR=1`, plain piped, plain with `CLICOLOR_FORCE=1` piped; `--json` forms contain no escape bytes on a pty.
- `lm` bare never fails: nonexistent dir, file-as-dir, empty string, 5000 files, slow osascript all rc 0; piped output has no suggestion. `LM_HINTS=0` removes it (44-47 ms).
- Positive clipboard branch works with a stub osascript that prints PNGf (suggests `lm read paste`).
- `scripts/gen-verbs.sh`: run twice in a scratch copy, second run changes nothing; text above and below the markers survived (`HANDEDIT-TOP/BOTTOM`), text inside the markers is replaced as designed; regenerated share/ files equal the committed ones; missing marker -> exit 2 with a clear message and no write.
- tldr pages: title, `>` description and More-information lines, `- description:` then blank then backticked command, 6-8 entries; `tldr --render` renders q.page.md.
- Metacharacter, leading-dash, empty and 6000-character queries: no crash, no command run, no file created (`$(touch ...)` and backtick payloads did not execute; checked pwned1/pwned2 absent).
- Item 8 (rg/grep no-match under `set -eo pipefail` inside `$(...)`): reviewed every added or changed line in bin/_lib.sh, bin/lm (`suggest_next`), bin/q, bin/see, bin/warm, lib/fleet, gemini, rag, ui-verify, scripts/gen-verbs.sh, scripts/verify.sh. All `$(...)` with a possibly failing command carry `|| true`, `|| return 0` or `|| var=""`; the only `grep` is inside `if`. No instance found. `verify.sh` has no `set -e`, so `VD="$(...)"; vdrc=$?` is safe.

## Item 1 table: `lm how <phrase> --no-model --json` (top answer; R right, W wrong, M no match which falls to the model in normal use)

| # | Phrasing | Top answer | Result |
|---|---|---|---|
| 1 | read the text in my last screenshot | lm read latest | R |
| 2 | whats on my clipbaord image | no_match | M (typo) |
| 3 | ocr this | see shot.png --ocr | R |
| 4 | what is eating my RAM | no_match | M |
| 5 | my mac is slow | no_match | M |
| 6 | redo that with a better model | lm again --big | R |
| 7 | try again but smarter | lm again | R |
| 8 | compare two screenshots | lm diff before.png after.png | R |
| 9 | what changed between these two images | lm diff before.png after.png | R |
| 10 | summarize this pdf | lm doc report.pdf | R |
| 11 | search my files for the invoice | no_match | M |
| 12 | review my git diff | lm diff before.png after.png | W |
| 13 | how many tokens is this file | no_match | M |
| 14 | how many tokens is this file but not on the web | q --web "current node LTS version?" | W (cloud, negated) |
| 15 | explain this error | lm timeline 10 --errors | W (soft) |
| 16 | delete all my files | no_match | R (cannot do) |
| 17 | generate an image of a cat | imagine refine 12 "warmer light" | W (wrong command) |
| 18 | send an email to bob | no_match | R (cannot do) |
| 19 | run a shell command for me | lm cmd "list the 5 largest files in ~/Downloads" | R (canned) |
| 20 | unload all models | lm models | W |
| 21 | free up memory by stopping models | lm status | W |
| 22 | search the web for rust news | q --web "current node LTS version?" | job R, query canned (F1) |
| 23 | do not use the web, tell me what 2+2 is | q --web ... | W (cloud, negated) |
| 24 | without gemini, summarize this big folder | lm gemini --file big.md "summarize the risks" | W (cloud, negated) |
| 25 | sumarize my clipbord | no_match | M |
| 26 | screnshot text | no_match | M (typo) |
| 27 | read screenshot and then redo it bigger | lm read shot.png | R (first intent only) |
| 28 | what did the last call say | lm timeline | W (lm last) |
| 29 | why did my last command fail | lm timeline 10 --errors | R |
| 30 | (empty) | usage error rc 2 | R |
| 31 | --go | usage error rc 2 | R |
| 32 | -rf / | no_match | R |
| 33 | ; rm -rf ~ # | no_match | R |
| 34 | $(touch /private/tmp/claude-501/pwned1) | no_match, file not created | R |
| 35 | `touch /private/tmp/claude-501/pwned2` | no_match, file not created | R |
| 36 | "a " x 3000 (6000 chars) | no_match | R |
| 37 | quote'd "phrase" with \| pipe && chain | no_match | R |
| 38 | how fast is the model | lm fast 1h | W (soft) |
| 39 | benchmark the models | lm bench quick | R |
| 40 | check the ui against the design | lm ui-verify shot.png "the CTA is disabled" | R |
| 41 | timeline of my calls | lm timeline | R |
| 42 | which models are installed | lm models | R |
| 43 | is everything healthy | no_match | M (doctor) |
| 44 | ask a question | lm "what text is in ~/Desktop/shot.png" | R (canned) |
| 45 | make a command line for listing big files | lm cmd "list the 5 largest..." | R |
| 46 | use gemini to read my whole repo | lm gemini ingest-repo . | R (asked for gemini) |
| 47 | run many prompts in parallel | lm cmd "list the 5 largest files in ~/Downloads" | W (fleet) |
| 48 | index my notes for search | no_match | M |
| 49 | ask my notes | no_match | M |
| 50 | tell me a joke | no_match | R (cannot do) |
| 51 | weather today | no_match | R |
| 52 | translate to french | no_match | R |
| 53 | review my uncommitted changes | lm review | R |
| 54 | build a search by meaning index of my docs | lm rag index docs/ | R (F4 under --go) |
| 55 | start opencode | lm opencode | R |
| 56 | what is installed and what is running and is it healthy | no_match | M |
| 57 | commit message from my diff | lm diff before.png after.png | W (q commit) |
| 58 | keep the model warm for an hour | no_match | M |
| 59 | how many red squares are in this image | see count dots.png | R (colour dropped) |
| 60 | the odd one out in this grid | no_match | M |
| 61 | whats the newest node version | no_match | M |
| 62 | tell me the latest news but keep it local | q --web ... | W (cloud, negated) |
| 63 | read this image offline | lm read shot.png | R |
| 64 | internet | no_match | M |
| 65 | online ocr of my screenshot | see shot.png --ocr | R |
| 66 | show errors | lm timeline 10 --errors | R |
| 67 | quick summary of the last thing I ran | lm last | R |
| 68 | why is it so slow today | no_match | M |
| 69 | RM -RF EVERYTHING | no_match | R |
| 70 | find where fleet_worker is defined in the repo | lm index find fleet_worker | R |
| 71 | lm / help | lm help | R |

Totals: 13 W (12, 14, 15, 17, 20, 21, 23, 24, 28, 38, 47, 57, 62), 16 M, rest R. Cloud lane chosen with no cloud word in the request: none. Cloud lane chosen with a cloud word that was negated: 4 (14, 23, 24, 62).
Model calls inside item 1: 2 (`what is installed` and `see dashboard` under `--go`); `what is installed` returned `lm models` (right), `see dashboard` returned `see dashboard` with `why` "reads the content of the image named dashboard" and the `--go` ran it against a nonexistent file (rc 12).
