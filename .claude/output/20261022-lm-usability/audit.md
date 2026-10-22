# lm suite usability audit (2026-10-22)

Scope: can someone who does not remember the flags get a real job done with `lm`, quickly, and trust
the result? Bugs already in `.claude/output/20261022-lm-adversarial/review.md` are not repeated here.
No source file was edited. Model calls used: 7 of the 8 allowed (6 small-tier `q`, counting one
`--diy` planner call, plus 2 `see` reads on fixtures, one of them routed by `--diy`). A Qwen3.6-27B
benchmark was writing to `see-history` and `q-history` while I worked. That traffic shows up in some
of the evidence below, and it turned out to be evidence in its own right (finding 3).

## Verdict

1. You type the job in plain words and `q` answers the wrong question. Give it an image path, a "gemini ..." prefix or a typo, and it chats back instead of sending you to the right tool. The router that fixes this exists (`--diy`), but it is opt-in and has been used 3 times.
2. When an answer is wrong there is no good next move. Answers are deterministic, so retyping gets the same answer (you did this about 22 times). `q -c` continues whatever anyone ran last, and 41% of recent rows are tab-title hook calls. Nothing offers "same question, bigger model or the web".
3. You can't trust what comes back, and nothing tells you how far to trust it. `q cmd` has handed you invented flags and a broken `pkill` with no check. `q summarize` silently read 65% of the file. `lm status` said nothing was loaded while a 2.1 GB vision process was resident.
4. Your own work is buried. About 97% of history comes from agents, hooks and benchmarks, and `lm last`, `see more`, `q -c` and "-1 = latest" all point at that traffic. You can't search past answers at all.
5. The way in is a 20-verb list plus 6 help surfaces (38 to 77 lines each, up to 212 columns wide). Those surfaces are written for an agent ("Inspect the image yourself") and organised around tools, not around the daily jobs your history shows: command, quick question, image text, retry, find it again.

## How owner calls were separated from agent traffic

The histories carry no TTY or session marker, so I classified each row by its own fields
(scratch scripts in the session scratchpad, `mine.py` and `mine2.py`):

| class | rule | q rows |
|---|---|---|
| automated intents | intent in title, diy-plan, describe-data, review, complete, code-dispatch (`title` alone is 1,803 rows, fired by `~/.claude/scripts/tab-title/hooks/auto-base.sh`) | 1,719 |
| long documents | prompt over 600 chars (inlined context from agents) | 1,222 |
| tests | caller under `/private/tmp` or `~/.codex/` worktrees | 327 |
| scripted phrasing | "Reply with", "ANSWER:", "exactly", "json", `<input` | 304 |
| **probably the owner** | everything else, mostly short `ask`/`cmd` prompts | **116** |

So the owner made about 3% of 3,688 `q` calls, mostly in June and July. Only about 17 came after
September 1. In `see`, 897 of 1,408 rows are probe fixtures and most of the rest come from agent
sessions (caller `local-models`, 1,003 rows). There is no row where the owner clearly used `see`
directly. The owner's two attempts to read an image went through `q` instead (rows #303, #309, #319).
`imagine` has 18 lifetime rows, the last on 2026-07-13.

Struggle signals in the 116 owner rows (52 near-duplicate pairs within 180 s):

- Identical retries that got identical answers: #1/#2/#3 and #4 all returned `sysctl -a`. #2118 and #2119 returned the same broken `pkill pm2 --stop && ...`, and so did #2120 after adding "make sure command is accurate". #3508 and #3509 matched too.
- Refining by retyping instead of following up: the ccusage chain #224 to #226 ("... did not work, check its docs"), the apk unzip chain #3504 to #3509 ("unzip -d is not working"). `-c` was used once in 3,688 rows (2026-06-12).
- Trying to escalate from inside the prompt: "gemini codex how to check usage limits" (#2216, #2217), "gemini pm2 view details..." (#2221). `q --web` exists, but the owner never used it.
- Guessing meta-commands that became prompts: `--title for this lm runner` (#53), `intent title for ...` (#57), `list` (#182, answer "Please specify what you would like me to list."), `intent` (#312), `commitz` (#3644, answered with git trivia).
- Images sent to the text tool: #303 "what text is in ~/.claude/assets/images/region-...png", answered "I cannot access local files". #309 got the same answer.
- Wrong answers with no warning: #224 `npx ccusage --today --per-model` (invented flags), #2118 `pkill pm2 --stop`, #2215 `man codex`, #176 `code_analyzer --scan . ...` (a tool that does not exist).

## Walkthroughs

Each row starts from `lm` or `lm help` with no memory of the flags. Times are wall-clock as measured.
"Not run" rows were walked through help and code only, as the scope required.

| # | job | steps taken | tries | feel | where it broke |
|---|---|---|---|---|---|
| 1 | quick question | `lm` shows `lm q "..."`, then `q "how do I see which process is using port 5432"` gives `lsof -i :5432` | 1 | ok, 5.2 s (cold) | `lm` promises "sub-second" only after `warm on`, and the default is a cold 5 s. Model and timing are hidden when stderr isn't a TTY |
| 2 | shell command | `q cmd "list the 5 largest files under ~/Downloads, with sizes"` gives `Find ~/Downloads -type f -exec du -sh {} + \| sort -rh \| head -n 5` | 1 | ok, 6.4 s | capitalised `Find`, and nothing was checked. History shows invented commands passing silently (see above) |
| 3 | summarize a long file | guessed `q summarize docs/STATE.md`, got `ctx_required` with the exact fix, then `q summarize --ctx docs/STATE.md` | 2 | ok, 15 s | it read only 16,000 of 24,702 chars and never told me (`bin/q:527-542` tells the model, not the human) |
| 4 | pasted screenshot from the clipboard | `lm help screenshot` doesn't mention the clipboard. `see --clipboard` gives "unknown flag". `pngpaste` isn't installed. `rg clipboard bin/ lib/` finds only text `pbpaste` | 3 | failed | no way in. You have to save the file by hand first |
| 5 | exact text from an image | natural first try: `q "what text is in <img>"` gives "I cannot read the text from an image file". Then `see <img> "what is the build id exactly?"` gives `K7Q-48XZ-2093` (correct). Then `see <img> --ocr` gives the exact text | 2-3 | slow, then fast: 16.6 s VLM vs 1.2 s OCR | `q` doesn't route. `--diy` does route to `see`, but picks the 16 s VLM, not the exact OCR (see#1433) |
| 6 | which of two UI shots changed, and where | `lm help compare` gives `see diff A B --no-read --json`. Text mode prints "(visual read skipped: --no-read, the deterministic evidence pack below is complete)" with **nothing below it**. `--json` gives grid cells `[3,5],[4,5],[3,3],[4,3]` | 3 | poor | "where" comes back as grid coordinates I have to interpret. The default (with a read) loads the 17 GB gemma tier. The JSON says `"model":"gemma4:26b"` although no model ran. The help says "Judge which visible differences matter yourself." |
| 7 | count things in an image | `lm help count` gives "unknown job". Found `see count` in `see -h`, then `see count C03/s0/image.png --color blue` gives `4` (truth.json: 4), instant | 2 | good once found | the natural `see img "how many blue squares"` goes to the VLM (benchmark rows: 19 s on 27B) with no pointer to `see count` |
| 8 | JSON answer for a script | `q --json "is 91 a prime number? answer yes or no"` gives an envelope with `text:"No."`, `model`, `entry`, `cold_load` | 1 | good | a typed field needs a schema **file** (`--format FILE`, `bin/q:415-418`). There's no inline shorthand |
| 9 | ask Gemini about a large doc (not run) | `lm gemini -h`, guessed `lm gemini --file doc "..."` and got "unknown flag '--file'". It has to be `cat doc \| lm gemini "..."` | 2 | ok | `q` takes `--file`/`--ctx` but `lm gemini` takes only stdin. Same job, different flag |
| 10 | review uncommitted changes (not run) | `review -h`: bare `review` = git diff | 1 | good | runs on the 23 GB code tier with no time estimate |
| 11 | find an answer from an hour ago | `lm timeline 15` (0.16 s) shows prompts only, interleaved with benchmark rows. Tried `lm timeline --grep port` (rejected) and `q history port` (silently ignored "port", showed 15 rows). Then `q show N` for each candidate | 3+ | poor | no search, no answer text in the rows, owner rows mixed with agent rows. Doc intents show the document's first line, not the question |
| 12 | what's loaded, and free memory | `lm status` says "none (idle, ~0 RAM)". `.venv/bin/python scripts/mem-guard.py --once` (found only in `lm examples`) shows `available~=20.0G` and an `mlx_vlm.generate` process at **2.1 GB** | 2 | misleading | status doesn't see MLX residency and shows no memory |
| 13 | make the next q calls fast for an hour (not run) | `warm -h`: `on` = 2 h lease, `on code [2h]` = 60 m default, plus "Tier W", "companion", "lease" | 1-2 | confusing | the natural `warm on 1h` would try to load a model named "1h" (`bin/warm:56-61`, `resolve_tier "$target"`). It has to be `warm on small 1h`. There are also three entry points: `warm`, `lm warm`, `q on` |
| 14 | generate an image (not run) | `imagine -h` is clear, with refine/vary/star | 1 | ok | the header says "Flux" but the default is qwen, ~1-2 min |
| 15 | understand why a call failed | `lm timeline 8 --errors` shows ✗ rows with no reason. `see show 1401` gives a traceback cut off before the cause. `q show 3612` gives `[error: server_down]` and no remedy. `lm gemini show 656` gives "timeout ..." plus a relative-path `python3 lib/gemini-stream.py render ...` | 3 | poor | no reason or remedy on the list view, and the detail views give raw codes |
| 16 | follow up on the last answer (from history) | `q -c "..."` continues `tail -1` of the global log (`bin/q:606-607`). In the last 300 rows, 123 are `title` calls from the tab-title hook | 1 | unsafe | follow-ups land in a stranger's chain, which is plausibly why the owner retypes instead |
| 17 | ask about something current (from history) | the owner typed "gemini ..." into `q`. The real path is `q --web` or `lm gemini`, and neither appears in `lm help` jobs except "research" | 2-3 | poor | the small model answers unknowable questions confidently (#2215 `man codex`) |
| 18 | read a verb's help | `lm timeline -h` gives "unknown flag '-h' (run lm timeline -h to list flags)". `lm status -h` exits 2. `lm probe -h` **fired 9 HTTP calls and wrote `probe/runs/-h-<ts>.md`** | 1 | broken | help on three verbs is a dead end or has side effects |

Side effect of row 18: my two `lm probe -h` runs created
`/Users/alcatraz627/Code/local-models/probe/runs/-h-20261022-110646.md` and
`/Users/alcatraz627/Code/local-models/probe/runs/-h-20261022-110656.md`. I left them in place.
They are junk and safe to trash.

## Findings, ranked by daily cost to the owner

### 1. `q` doesn't route plain requests to the right tool (M)

Evidence: owner rows #303, #309 (image paths sent to `q`, answered "cannot access local files").
Rerun today on a fixture: `q "what text is in .../T01/s0/image.png"` gave "I cannot read the text from an
image file." Also #2216, #2221 ("gemini ..." prefix), #182 `list`, #312 `intent`, #53 `--title`,
#3644 `commitz`. `q --diy` on the same prompt routed to `see` and returned the text, so the router works,
but history shows 3 `diy` rows ever.

Change: in text mode, bare `q` runs cheap deterministic checks before any model call. An image path
in the prompt goes to `see` (OCR first, see 7). An existing file path goes to `--ctx`. A first word
within edit distance 1 of an intent (`commitz`) gets "did you mean `q commit`? (running as ask)". A
leading `gemini`/`web` word suggests `--web` or `lm gemini`. Only then does the `--diy` planner run, and
it narrates in gray as it does now. What the owner would see:

```
$ q "what text is in ~/Desktop/shot.png"
· image in prompt → see --ocr (exact) ~1s
Release notes / Build ID: K7Q-48XZ-2093 ...
```

### 2. There's no good next move after a bad answer (M)

Evidence: about 22 identical retries in the owner rows (#1 to #3, #6 to #8, #26 to #30, #2118/#2119,
#3508/#3509). `q -h` DEFAULTS says "deterministic (temp 0)", so a retry can't change anything.
`-c` was used once in 3,688 rows. `q -c` targets `tail -1 "$LOG"` (`bin/q:607`), and 41% of the last 300
rows are tab-title calls, so a follow-up usually continues someone else's exchange.

Change: add `q again [--big|--web|--code]`, which re-asks your last question on a stronger lane, and
scope `-c` to the calling terminal (key by `$TERM_SESSION_ID` or the tty plus a `tty:true` history field).
When the same prompt repeats within 5 minutes, print `· same input gives the same answer (temp 0); try:
q again --big · q again --web`.

### 3. Your own calls are buried under agent traffic (M)

Evidence: the separation above (owner about 3% of q, about 0% of see). `lm last` returned `see#1439`, a
benchmark read, while my last call was q#3694 and see#1433. `see more` and `see open -1` resolve
`jsonl_entry "$LOG" -1` (`bin/see:151`), which is global. With the benchmark running, `see open -1`
pointed at a read I did not make.

Change: every history line records `tty` and `session`. `lm timeline`, `lm last`, `see more`, `-1` and
`q -c` default to "mine, this terminal". `--all` shows everything, and agent rows render dimmed.

### 4. Nothing checks `q cmd` answers (M)

Evidence: #224 `npx ccusage --today --per-model` (invented flags; the owner came back with "did not work,
check its docs"), #2118 `pkill pm2 --stop && ...` (invalid, and it would kill pm2), #2215 `man codex`,
#176 `code_analyzer --scan`. Project hard rule 2 asks for a task-appropriate check, and `cmd` has none.

Change: after a `cmd` answer, check that the binary exists (`command -v`) and that each long flag
appears in `<bin> --help` or its man page (no execution). Print one gray line:
`· checked: ccusage ✓ · --per-model ✗ not in ccusage --help → q again --web`.

### 5. Long documents are cut off silently (S)

Evidence: `q summarize --ctx docs/STATE.md` (24,702 chars) answered without any notice. `bin/q:527-529`
truncates at `MAX_CTX=16000` (about 4k tokens) and only appends a note for the model (`bin/q:541-542`).
The JSON envelope has `truncated`, but text mode never prints it.

Change: print on stderr `· read 16,000 of 24,702 chars (65%); whole file: --max-ctx 40000, or
cat file | lm gemini "..."`. Also consider raising the default to what the small tier can actually hold.

### 6. You can't find a past answer (S-M)

Evidence: `lm timeline --grep port` gives "unknown flag". `q history port` silently printed the last 15
rows. Timeline rows show prompts only, and doc-intent rows show `<input name="STATE.md"> # local-models...`
instead of the question.

Change: add `lm find "port 5432"`, which searches prompt and response across all six histories (owner rows
first) and prints `q#3689  11:07  how do I see which process...  → lsof -i :5432`. Timeline rows get the
first line of the answer, and doc rows show the user's words plus the file name.

### 7. The exact tools sit behind slow guesses (M)

Evidence: `see <img> "what is the build id exactly?"` took 16.6 s on the VLM. `see <img> --ocr` took
1.2 s and is exact. `see count --color blue` was instant and matched truth.json (4), while the
natural phrasing goes to a VLM (benchmark see#1417: 19 s on 27B). `--diy` sent "what text is in" to the VLM,
not OCR (see#1433).

Change: when a `see` question asks for text, IDs, numbers or "how many", run `--ocr`/`count` first and
print it as the measured answer. The model reads second, or not at all. One gray line names the exact
verb for next time.

### 8. Clipboard images aren't supported (S)

Evidence: walkthrough 4. `see --clipboard` is rejected, `pngpaste` is missing, and nothing in `bin/` or
`lib/` reads an image from the clipboard. The commonest macOS screenshot flow (Cmd-Ctrl-Shift-4) can't
reach `see`.

Change: `see paste ["q"]` writes the clipboard PNG through `osascript` (`the clipboard as «class PNGf»`,
no extra install) to a temp file and reads it. Add `see latest` for the newest file in
`defaults read com.apple.screencapture location`.

### 9. The help is written for an agent, and it's long (S)

Evidence (NO_COLOR line counts and max width): `lm` 38 lines / 122 cols, `lm examples` 77 / 103,
`q -h` 72 / 165, `see -h` 56 / 212, `imagine -h` 51, `lm gemini -h` 27 / 208. `lm help` jobs are table,
document, screenshot, compare, batch, retrieval, research. `lm help count|history|fast` all give
"unknown job". The job text says "Inspect the image yourself for visual judgment" and "Judge which
visible differences matter yourself".

Change: rebuild the `lm help` job list from walkthrough rows 1-17, worded to the owner, and cap each
`-h` at about 25 lines with `--all` for the rest. Wrap at 100 columns.

### 10. Help verbs that break or have side effects (S)

Evidence: walkthrough 18. `lm timeline -h` gives an error pointing at itself, `lm status -h` exits 2, and
`lm probe -h` ran a 9-test probe against a model named `-h` and wrote a report file.

Change: route `-h` before parsing in all three.

### 11. `see diff` text mode is empty without the model (M)

Evidence: walkthrough 6. "evidence pack below is complete" is followed by nothing, in both the live
output and `see show 1416`. The `--no-read --json` envelope claims `"model":"gemma4:26b"`.

Change: text mode prints a 3-line plain summary built from the evidence: where (the hot grid region in
words, e.g. "middle band, left and right of centre: something shifted sideways"), whether text changed,
and whether colours changed, plus the ASCII heatmap the JSON already carries. The default judge should be
the MLX 8B, not the 17 GB tier. `model` should be null when no model ran.

### 12. `lm status` hides MLX and memory (S)

Evidence: walkthrough 12. Status said idle while `mlx_vlm.generate` held 2.1 GB. Free memory is only
reachable as `.venv/bin/python scripts/mem-guard.py --once`.

Change: `lm status` gains `memory  20 GB available · pressure normal · swap 5.7 GB` and an `mlx` line from
mem-guard's process scan.

### 13. The `warm` vocabulary works against the job (S)

Evidence: walkthrough 13. There are two different default lengths (2 h and 60 m), jargon ("Tier W",
"companion", "lease"), and `warm on 1h` would load a model named "1h" (`bin/warm:56-61`).

Change: accept a duration in the first slot (`warm on 1h` means small for 1 h) and print
`q stays fast until 12:15 (warm off to free 6 GB)`.

### 14. Failure rows have no reason or remedy (S)

Evidence: walkthrough 15. Change: timeline error rows print `code · remedy`, for example
`server_down · server was stopped; it restarts on the next call, or run lm doctor`. `see show` should keep
the last traceback line (the cause), not the first 300 chars. The gemini step-log hint should use an
absolute path or `lm gemini watch N`.

### 15. Front-door prominence doesn't match use (S)

Evidence: `imagine` is the second row of `lm` with 18 lifetime runs (last 2026-07-13), and it is frozen per
project memory. `probe`, `bench`, `opencode`, `index` and `rag` sit in the owner's front door. `lm ask` is an
unknown verb, although `ask` is q's default intent.

### 16. Stale or contradictory text (S)

`lm examples` says the `see` default is "minicpm-v4.6", while `see -h` says Qwen3-VL on MLX, and history
confirms MLX (see#1415). The `imagine -h` header says Flux while the default is qwen. The `--diy` narration
labelled an image read `intent=describe-data`.

### 17. Inconsistent input flags across tools (S)

`q --file/--ctx`, `lm gemini` stdin only (`--file` rejected), `see` positional, `--format` file-only.
Accept `--file` everywhere it makes sense.

## Proposed front door

The walkthrough supports one: 14 of 18 jobs started from a guess the current surfaces didn't answer.
The idea is that `lm` with no arguments shows jobs, not tools, and each job's command already does the
routing:

```
lm — local models on this Mac (nothing leaves the machine unless marked ☁)

  lm "question"              answer; an image path, file or "how many" routes itself
  lm cmd "task"              one shell command, checked against its --help
  lm read <img|paste|latest> ["q"]   text or an answer from an image (exact OCR first)
  lm diff A B                what changed between two images, and where
  lm doc <file> "q"          ask or summarize a file (says how much it read)
  lm again [--big|--web ☁]   redo your last question, stronger
  lm find "words"            search your past answers
  lm review                  review uncommitted changes

  lm status   loaded · memory · fast-until · last errors
  lm fast 1h  keep answers instant for an hour
  lm more     everything else: gemini ☁, fleet, rag, index, imagine, probe, bench, ui-verify
```

Each verb is a thin alias over what already exists:

- `lm "..."` is `q` with routing on.
- `read` is `see` with OCR/count first.
- `doc` is `q --ctx`.
- `again` reuses `-c` scoped to the terminal.
- `fast` is `warm on small`.
- `find` is new and reads the histories.

`q`, `see`, `imagine` and `review` stay as they are for power use and agents. Nothing is deleted;
`lm more` shows today's `lm` overview.

## What not to change

- **The error-with-fix messages.** `q summarize <file>` names the exact fix, and unknown flags are now refused with a `--` hint. That is the best moment in the walkthrough.
- **The `--json` envelopes.** `q --json` carries `entry`, `cold_load` and `truncated`. Agents depend on them, so keep them stable.
- **The exact tools.** `see --ocr` (1.2 s, verbatim) and `see count` (instant, matched truth) are the most trustworthy things in the suite. Promote them; don't change them.
- **Bare `review` reviews uncommitted changes.** It is the right default.
- **The current speed of `lm timeline`** (0.16 s for 15 rows) and the `tool#N` handles in it.
- **`lm doctor`'s checklist,** which now covers yq, every tier, the MLX cache, PATH targets and the gemini key.
- **Colours, examples and explicit flags.** The owner called these good. The redesign adds a layer on top and replaces nothing.
- **`lm gemini models` validation and `did_you_mean` on `lm` verbs.**
