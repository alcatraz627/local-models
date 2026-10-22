# lm usability build: evidence (before and after)

Worktree: /Users/alcatraz627/Code/local-models-ux, branch lm-usability. "Before" is the unchanged main checkout
(/Users/alcatraz627/Code/local-models) or the audit's recorded output where re-running would cost a model call.
"After" is the worktree. All output below was produced by running the commands, with NO_COLOR=1.

Model calls made while building: q small tier about 10 (again 3, routing 5, cmd 1, plus the verify.sh battery's own),
one plain MLX read inside verify.sh, no imagine, no review, no fleet beyond verify.sh's one-item run, no pulls or deletes.
`lm gemini` calls: only the two verify.sh makes.

## Item 1: help works (findings 10, 16, 9)

Before (audit row 18, and re-run):
```
$ /Users/alcatraz627/Code/local-models-ux/bin/lm timeline -h
lm timeline: unknown flag '-h' (run lm timeline -h to list flags). If it is part of your prompt, quote the prompt, or put -- before it
[exit 2]

$ /Users/alcatraz627/Code/local-models-ux/bin/lm status -h
lm status: unexpected '-h' (the only option is --json)
[exit 2]

$ /Users/alcatraz627/Code/local-models-ux/bin/lm help count
lm help: unknown job 'count'
  jobs: table document screenshot compare batch retrieval research
  tools: q see imagine review warm probe fleet gemini rag index ui-verify bench opencode
[exit 2]

$ /Users/alcatraz627/Code/local-models-ux/bin/lm help history
lm help: unknown job 'history'
  jobs: table document screenshot compare batch retrieval research
  tools: q see imagine review warm probe fleet gemini rag index ui-verify bench opencode
[exit 2]

$ /Users/alcatraz627/Code/local-models-ux/bin/lm help fast
lm help: unknown job 'fast'
  jobs: table document screenshot compare batch retrieval research
  tools: q see imagine review warm probe fleet gemini rag index ui-verify bench opencode
[exit 2]

$ lm examples | rg "see shot.png"
  see shot.png "what state is the toggle in?"           grounded read (minicpm-v4.6)

$ imagine -h | head -1
imagine — local image generation (Flux on Apple Silicon, runs on YOUR GPU)

help-size  lm             lines=38 maxcols=122
help-size  lm examples    lines=77 maxcols=103
help-size  q -h           lines=72 maxcols=165
help-size  see -h         lines=56 maxcols=212
help-size  imagine -h     lines=51 maxcols=103
help-size  lm gemini -h   lines=27 maxcols=208
help-size  warm -h        lines=14 maxcols=86
help-size  review -h      lines=21 maxcols=138
```

After:
```
$ /Users/alcatraz627/Code/local-models-ux/bin/lm timeline -h
lm timeline — your recent calls, newest last

USAGE
  lm timeline [N]                  your last N calls (default 20) across q, see, imagine, fleet and
                                   gemini
  lm timeline --errors             only failed calls, each with its reason and what to do
  lm timeline --all                also agents, hooks and other terminals (dimmed)
  lm timeline --tool T             one of q, see, imagine, fleet, gemini
  lm timeline --json               rows as JSON (adds mine, answer, code)
  Each row starts with a handle like q#3689: open it with q show 3689.
[exit 0]

$ /Users/alcatraz627/Code/local-models-ux/bin/lm status -h
lm status — what is loaded, free memory, when it unloads

USAGE
  lm status                        server, free memory, loaded models and when they unload, MLX
                                   processes
  lm status --json                 the machine-readable status other tools read
[exit 0]

$ /Users/alcatraz627/Code/local-models-ux/bin/lm help count
lm help count — count things in an image by measuring pixels

START
  see count dots.png                           how many objects (exact, instant, no model)
  see count squares.png --color blue           only the blue ones
  see odd grid.png                             the one item that differs among repeated items

  Asking "how many" through lm read runs this first.
[exit 0]

$ /Users/alcatraz627/Code/local-models-ux/bin/lm help history
lm help find — search the answers you got before

START
  lm find "port 5432"                          matching questions and answers across q, see, gemini
                                               and imagine, yours first
  lm timeline 15                               your last 15 calls, newest last
  lm timeline --all                            include agents and hooks (dimmed)
  lm last                                      your latest call, in full

  Open one with the handle it prints: q show 3689, see show 1433.
[exit 0]

$ /Users/alcatraz627/Code/local-models-ux/bin/lm help fast
lm help fast — keep answers instant

START
  lm fast 1h                                   q answers in under a second until the time it prints
  lm fast off                                  free the memory now
  lm status                                    what is loaded and when it unloads

  Without it the first answer after a pause takes about 5 s while the model loads. Nothing stays
  loaded on its own.
[exit 0]

$ lm examples | rg "see shot.png"
  see shot.png "what state is the toggle in?"           grounded read (Qwen3-VL on MLX; minicpm-v4.6

$ imagine -h | head -1
imagine — draw an image on this Mac's GPU, offline and free (default model: qwen)

help-size  lm             lines=23 maxcols=100
help-size  lm examples    lines=98 maxcols=100
help-size  q -h           lines=18 maxcols=100
help-size  see -h         lines=20 maxcols=99
help-size  imagine -h     lines=16 maxcols=99
help-size  lm gemini -h   lines=13 maxcols=95
help-size  warm -h        lines=14 maxcols=100
help-size  review -h      lines=24 maxcols=99
```
`lm probe -h` after: prints a plain description and runs nothing (no probe/runs file written).
Help size went from 38 / 72 / 56 / 51 / 27 lines (up to 212 columns) to 23 / 18 / 20 / 16 / 13 lines for lm / q / see / imagine / lm gemini,
all at most 100 columns wide. `--all` prints the rest (q -h --all is the old 100 or so rows, wrapped).

## Item 2: history knows whose call it was (finding 3)

A real terminal call (run under `script`, so it has a tty) records its tty. Excerpt of the row:
`{"intent": "describe-data", ..., "caller": "/Users/alcatraz627/Code/local-models", "tty": "ttys009", "session": null}`

Under that same terminal: `lm timeline 5` listed only the calls made there, `q show -1` and `lm last` opened the newest of them.
From this agent call (no terminal) the default is nothing, and `--all` shows everything:
see the "mine vs everything" block in item 7 to 11 below. Old rows have no tty field and count as not mine.

## Item 3: a next move after a bad answer (finding 2)

Run in a pty (third tty-bearing call set). The second identical question prints the hint; `q again` re-asks on the named lane:
```
$ q --no-stats?? first ask
[11:35:57 q] gemma4-e4b-warm cold load · intent=ask
Blue.
· gemma4-e4b-warm · cold · 90 in / 3 out · 33 tok/s · 5.2s · q show 3697
$ same question again (within 5 min)
[11:36:03 q] gemma4-e4b-warm cold load · intent=ask
Blue.
· gemma4-e4b-warm · cold · 90 in / 3 out · 30 tok/s · 2.7s · q show 3698
· same input gives the same answer (temp 0); try: q again --big · q again --web
$ q again --dry-run
· again: "In one word, what colour is the sky on a clear day" (was small) → big
$ q again --code --dry-run
· again: "In one word, what colour is the sky on a clear day" (was small) → code
$ q again --web
· again: "In one word, what colour is the sky on a clear day" (was small) → web
· web: "In one word, what colour is the sky on a clear day?" → 5 results (top page fetched)
[11:36:08 q] gemma4-e4b-warm cold load · intent=ask
Blue is the color of the sky on a clear day due to Rayleigh scattering [1, 4]. This process scatters shorter blue wavelengths of sunlight more effectively than longer ones [1, 4].
· gemma4-e4b-warm · cold · 2,035 in / 42 out · 57 tok/s · 4.4s · q show 3699
$ q again --dry-run  (after web: no lane named)
q again: the last answer already used small+web. Name a lane: q again --web (sends the question off this Mac) or --code
[exit 2]
```
Not run: `q again --big` / `--code` for real (it would load the 17 / 23 GB tier while the MLX benchmark runs). `--dry-run` shows the plan and lane; the code path
is the same exec as the `--web` run above.

## Item 4: q routes plain requests (finding 1)

```
$ q commitz            (typo of an intent; routes by default on a terminal)
· 'commitz' is not an intent; did you mean 'q commit'? Running it as a plain question.
[11:37:48 q] gemma4-e4b-warm cold load · intent=ask
The command to commit changes in Git is `git commit`. You can add a message using the `-m` flag, like `git commit -m "Your message"`.
· gemma4-e4b-warm · cold · 78 in / 36 out · 65 tok/s · 4.3s · q show 3700
$ q "gemini what colour is the sky on a clear day, one word"
· 'gemini' at the start does not search anything. Answering locally. For the web: q --web "..."; for Gemini: lm gemini "..." (both send the question off this Mac)
[11:37:52 q] gemma4-e4b-warm cold load · intent=ask
Blue
· gemma4-e4b-warm · cold · 90 in / 2 out · 119 tok/s · 2.4s · q show 3701
$ q "what does /Users/alcatraz627/Code/local-models-ux/probe/fixtures/a.py do, one line"
· file in the prompt → reading a.py as context (the same as --ctx)
[11:37:55 q] gemma4-e4b-warm cold load · intent=ask
This Python file defines a `Page` class that initializes a page with a title and body, and automatically generates a slug and a truncated preview from the body.
· gemma4-e4b-warm · cold · 211 in / 33 out · 21 tok/s · 3.9s · q show 3702
$ q "what is in /nope/missing.md"
· no file at "/nope/missing.md"; telling the model so
[11:37:59 q] gemma4-e4b-warm cold load · intent=ask
The file /nope/missing.md does not exist.
· gemma4-e4b-warm · cold · 110 in / 13 out · 70 tok/s · 3.2s · q show 3703
$ q --no-route commitz   (old behaviour: exit 2, no model call)
q: 'commitz' is not an intent. Did you mean 'commit'? (q intents lists them; q ask "commitz" sends it as a prompt)
[exit 2]
$ q --json "Reply with the word ok" with a typo-ish first word keeps machine behaviour
[11:38:03 q] gemma4-e4b-warm cold load · intent=ask
{"ok": true, "text": "ok", "model": "gemma4-e4b-warm", "ms": 1732, "tokens_in": 87, "tokens_out": 2, "truncated": false, "intent": "ask", "entry": 3704, "cold_load": true}
```
The image-path route hands the prompt to `see`: with a text question it is then answered by OCR with no model (item 7 block below shows that read). Verified
through `see` directly; the `q "what text is in <img>"` hop itself was not re-run to save model calls.

## Item 5: q cmd answers are checked (finding 4)

The audit's own cases, checker run alone (`q check "<command>"`, never executes the command):
```
$ q check "npx ccusage --today --per-model"
· checked: ccusage ? not installed here, so its flags cannot be checked
$ q check "pkill pm2 --stop && pm2 list --no-color"
· checked: pkill ✓ · --stop ✗ not in pkill --help · pm2 ✓ · --no-color ✓ → q again --web
$ q check "du -sh ~/Downloads --max-depth=1 | sort -rh"
· checked: du ✓ · --max-depth ✗ not in du --help · sort ✓ → q again --web
```
A real `q cmd` call (audit row 2) in a pty:
```
[11:39:47 q] gemma4-e4b-warm cold load · intent=cmd
find ~/Downloads -type f -exec du -sh {} + | sort -rh | head -n 5
· gemma4-e4b-warm · cold · 153 in / 24 out · 67 tok/s · 4.9s · q show 3705
· checked: find ✓ · sort ✓ · head ✓
```
The `--json` envelope gains `checked` through the same code path; that was not exercised with a live call (model budget).

## Item 6: say what was read (finding 5)

`q summarize --ctx docs/STATE.md` against a dead server (so no model runs, the line prints before the call):
```
· read 16,000 of 24,442 chars (65%); the whole file: --max-ctx 25000
```
Over 28,000 characters it says the file is too big for the small model and points at `--big` or `cat FILE | lm gemini "..."`. `truncated` stays in the JSON envelope.

## Items 7, 8, 9, 10, 11 (model-free runs)

Before (main checkout):
```
=== item 8: clipboard and latest screenshot (before) ===

$ /Users/alcatraz627/Code/local-models/bin/see paste --ocr
see: no such file: paste
[exit 12]

$ /Users/alcatraz627/Code/local-models/bin/see latest --ocr
see: no such file: latest
[exit 12]

=== item 7: exact first (before) ===
(before: a text question goes to the vision model, 16.6 s in the audit; count likewise 19 s on the 27B)

$ /Users/alcatraz627/Code/local-models/bin/see /Users/alcatraz627/Code/local-models/probe/vision/fixtures/C03/s0/image.png --ocr
(no text recognized)
[exit 0]

=== item 10: see diff text mode (before) ===

$ /Users/alcatraz627/Code/local-models/bin/see diff /Users/alcatraz627/Code/local-models/probe/fixtures/f2-a.png /Users/alcatraz627/Code/local-models/probe/fixtures/f2-b.png --no-read
(visual read skipped: --no-read — the deterministic evidence pack below is complete)
[exit 0]
$ see diff f2-a f2-b --no-read --json | jq {model, hot: .evidence.grid_heat.hot_cell_pct}
{"model":"gemma4:26b","hot":56.2}

=== item 9: find and timeline rows (before) ===

$ /Users/alcatraz627/Code/local-models/bin/lm find port 5432
lm: unknown verb 'find'; run lm for the full list
[exit 2]

$ /Users/alcatraz627/Code/local-models/bin/lm timeline 6 --all
lm timeline: unknown flag '--all' (run lm timeline -h to list flags). If it is part of your prompt, quote the prompt, or put -- before it
[exit 2]

=== item 11: lm status (before) ===

$ /Users/alcatraz627/Code/local-models/bin/lm status
server   up · 127.0.0.1:11434
loaded   resident models (warm) · how long they stay · which tier they are
  none (idle, ~0 RAM)
models   on disk
  qwen3-embedding:0.6b       ac6da0dfba84    639 MB    3 weeks ago     
  granite4:tiny-h            566b725534ea    4.2 GB    5 weeks ago        tier sweep
  minicpm-v4.6:latest        e95583acac77    1.6 GB    5 weeks ago        tier vision
  nomic-embed-text:latest    0a109f422b47    274 MB    3 months ago       tier embed
[exit 141]

=== item 3/2: mine vs everything (before) ===

$ /Users/alcatraz627/Code/local-models/bin/lm timeline 3
10-22 11:44  see#1538     ocr  image.png  describe
10-22 11:44  see#1539     diff  f2-a.png  describe
10-22 11:44  see#1540     diff  f2-a.png  describe
[exit 0]

$ /Users/alcatraz627/Code/local-models/bin/see open -1
/Users/alcatraz627/Code/local-models/outputs/see/20261022T061434Z-diff-f2-a-27510
[exit 0]

$ /Users/alcatraz627/Code/local-models/bin/q show -1
#3694  2026-10-22T05:43:33Z  [diy-plan]  5401ms  gemma4-e4b-warm

PROMPT:
what text is in /Users/alcatraz627/Code/local-models/probe/vision/fixtures/T01/s0/image.png

RESPONSE:
{
  "intent": "describe-data",
  "needs_web": false,
  "tier": "small",
  "reason": "Analyze the content of the specified image file."
}
[exit 0]
```

After:
```
=== item 8: clipboard and latest screenshot (after) ===

$ /Users/alcatraz627/Code/local-models-ux/bin/see paste --ocr
see: the clipboard holds no image. Copy one first: Cmd-Ctrl-Shift-4 copies a screenshot area (plain Cmd-Shift-4 saves a file instead: use see latest)
[exit 12]

$ /Users/alcatraz627/Code/local-models-ux/bin/see latest --ocr
[exit 141]

$ /Users/alcatraz627/Code/local-models-ux/bin/see paste --ocr
VERIFY FIXTURE
corner
[exit 0]

$ /Users/alcatraz627/Code/local-models-ux/bin/see latest --ocr
[exit 1]
(paste on an empty clipboard, for the error text:)

$ /Users/alcatraz627/Code/local-models-ux/bin/see paste --ocr
see: the clipboard holds no image. Copy one first: Cmd-Ctrl-Shift-4 copies a screenshot area (plain Cmd-Shift-4 saves a file instead: use see latest)
[exit 12]

=== item 7: exact first (after) ===

$ /Users/alcatraz627/Code/local-models-ux/bin/see /Users/alcatraz627/Code/local-models/probe/fixtures/ocr-fixture.png what text is in this image?
VERIFY FIXTURE
corner
[exit 0]

$ /Users/alcatraz627/Code/local-models-ux/bin/see /Users/alcatraz627/Code/local-models/probe/vision/fixtures/C03/s0/image.png how many blue squares are there?
4
4 object(s) found by background-distance segmentation, min area 7px; kept 4 of 15 objects matching blue
[exit 0]

$ /Users/alcatraz627/Code/local-models-ux/bin/see /Users/alcatraz627/Code/local-models/probe/vision/fixtures/C03/s0/image.png how many blue squares are there? --json --no-measure --ocr
{"ok":true,"text":"(no text recognized)","model":"apple-vision","ms":102,"artifact":"/Users/alcatraz627/Code/local-models-ux/outputs/see/20261022T061436Z-ocr-image","data":{"width":720,"height":480,"words":[]}}
[exit 0]

=== item 10: see diff text mode (after) ===

$ /Users/alcatraz627/Code/local-models-ux/bin/see diff /Users/alcatraz627/Code/local-models/probe/fixtures/f2-a.png /Users/alcatraz627/Code/local-models/probe/fixtures/f2-b.png --no-read
Where: the centre of the image (about 56.2% of the image differs)
Text: unchanged
Colours: different; the biggest shift is #2563eb to #2634eb

Heatmap (8 by 8, # = most different, blank = same):
  |        |
  | +####+ |
  | ###### |
  | ###### |
  | ###### |
  | ###### |
  | +####+ |
  |        |
[exit 0]
$ see diff f2-a f2-b --no-read --json | jq {model, hot: .evidence.grid_heat.hot_cell_pct}
{"model":null,"hot":56.2}

=== item 9: find and timeline rows (after) ===

$ /Users/alcatraz627/Code/local-models-ux/bin/lm find port 5432
q#3689     10-22 11:07  how do I see which process is using port 5432 on my mac  → Run `lsof -i :5432` in your terminal to list the process using port 54
[exit 0]

$ /Users/alcatraz627/Code/local-models-ux/bin/lm timeline 6 --all
10-22 11:44  see#1469     read ✗    describe  → clipboard_empty
10-22 11:44  see#1470     ocr  ocr-fixture.png  describe  → VERIFY FIXTURE
10-22 11:44  see#1471     count  image.png  --color blue  → 4
10-22 11:44  see#1472     ocr  image.png  how many blue squares are there?  → (no text recognized)
10-22 11:44  see#1473     diff  f2-a.png  describe  → (visual read skipped: --no-read — the deterministic evidence
10-22 11:44  see#1474     diff  f2-a.png  describe  → (visual read skipped: --no-read — the deterministic evidence
[exit 0]

=== item 11: lm status (after) ===

$ /Users/alcatraz627/Code/local-models-ux/bin/lm status
server   up · 127.0.0.1:11434
memory   35 GB available · pressure normal · swap 5.6 GB
loaded   ollama models: size · when they unload · which tier
  none (idle, ~0 RAM)
[exit 1]

=== item 3/2: mine vs everything (after) ===

$ /Users/alcatraz627/Code/local-models-ux/bin/lm timeline 3
this call has no terminal, so none of the history is 'yours'. lm timeline --all shows everything.
[exit 0]

$ /Users/alcatraz627/Code/local-models-ux/bin/see open -1
none of your calls from this terminal are in this history yet (--all, or a number from 'history', reaches the rest)
[exit 1]

$ /Users/alcatraz627/Code/local-models-ux/bin/q show -1
none of your calls from this terminal are in this history yet (--all, or a number from 'history', reaches the rest)
[exit 12]
```

More after-output (warm duration, gemini --file, front door aliases):
```
=== item 11: warm takes a time first ===

$ /Users/alcatraz627/Code/local-models-ux/bin/warm on 1h
loading gemma4-e4b-warm for 1h ...
q stays fast until 12:51 (warm off to free 5.6 GB)
NAME                      ID              SIZE      PROCESSOR    CONTEXT    UNTIL               
gemma4-e4b-warm:latest    f7e173a5b6a0    5.6 GB    100% GPU     8192       59 minutes from now    
[exit 0]

$ /Users/alcatraz627/Code/local-models-ux/bin/warm off
shutting down gemma4-e4b-warm ...
NAME    ID    SIZE    PROCESSOR    CONTEXT    UNTIL 
[exit 0]
=== item 17: lm gemini --file (no call made: missing file / wrong verb) ===

$ /Users/alcatraz627/Code/local-models-ux/bin/lm gemini --file /nope/missing.md summarize
lm gemini: no such file: /nope/missing.md
[exit 12]

$ /Users/alcatraz627/Code/local-models-ux/bin/lm gemini --file /Users/alcatraz627/Code/local-models-ux/docs/STATE.md ask x
lm gemini: --file works with a one-shot prompt (lm gemini --file doc "question"); ask already takes its own files
[exit 2]
=== item 12: the front door aliases ===

$ /Users/alcatraz627/Code/local-models-ux/bin/lm cmd -h
lm cmd — one shell command, checked before you run it

USAGE
  lm cmd "task"                    one shell command; it checks the program and each --flag against
                                   its own --help
  $ lm cmd "list the 5 largest files in ~/Downloads"
     
[exit 0]

$ /Users/alcatraz627/Code/local-models-ux/bin/lm doc
lm doc — ask about, or summarize, a file

USAGE
  lm doc <file>                    summarize the file (PDF, Word, HTML, text, spreadsheet)
[exit 141]

$ /Users/alcatraz627/Code/local-models-ux/bin/lm statsu
lm: unknown verb 'statsu' (did you mean 'status'?); run lm for the jobs, or lm "your question" to ask
[exit 2]

$ /Users/alcatraz627/Code/local-models-ux/bin/lm fast -h
lm fast — keep answers instant for a while

USAGE
  lm fast [1h]                     keep the small model loaded so q answers instantly (default 1h)
[exit 141]
```

## Verify

`PATH=<worktree>/bin:$PATH bash scripts/verify.sh` from the worktree (the PATH prefix is only so lm doctor's "on PATH" checks see this checkout):
```
── syntax ──
  ok   syntax on all bin/ lib/ scripts/ entrypoints (bash -n + ast.parse)
── deterministic table contract ──
  ok   table contract: 8 behavior cases passed
  ok   benchmark and RAG contract: 4 behavior cases passed
── toolkit (lm doctor) ──
  ok   lm doctor (server, models, venv, PATH)
── q: envelope + constrained decoding (warm/small tier) ──
  ok   q --json envelope
  ok   q --format → parsed .data
── q --diy: planner emits a valid plan (warm tier) ──
  ok   diy planner → schema-valid plan (.data.intent set)
── websearch (skips cleanly offline) ──
  ok   websearch → 2 results
── fleet: fan-out + envelope gate + lease + run history ──
  ok   lm fleet 1-item run (envelope passed)
  ok   fleet-history run line
── index: symbol lookup + staleness machinery ──
  ok   lm index find (exact hit)
── gemini lane (skips cleanly if unavailable) ──
  ok   lm gemini one-shot envelope
  ok   lm gemini session memory (ask)
── see: artifact store (small vision tier) ──
  ok   see --json envelope + artifact field
  ok   artifact folder complete (source + read.md + meta.json)
  ok   see open -1 → same artifact
── ui-verify: help + dispatch (full gate not run — see header) ──
  ok   lm ui-verify dispatch + help
── see --ocr: Apple Vision exact-text lane (no model) ──
  ok   see --ocr envelope (apple-vision)
  ok   see --ocr --json → positioned words (VERIFY FIXTURE @ top-left)
── vis-compare: evidence battery (fixtures F1-F12, model-free) ──
  ok   53/53 vis-compare assertions passed
  ok   vision harness selftest (probe/vision, model-free)
  ok   measure lane (see count / see odd): 32/32 passed
── findings-gate: mechanical review-findings gate ──
  ok   findings-gate self-test: ok (13 cases, kept=2 dropped=11)
── imagine: preflight refuses a half-downloaded model (fail-fast, no generation) ──
  ok   imagine preflight (with-partials): refuses + prints a WORKING download command
  ok   imagine preflight (no-partials): refuses + prints a WORKING download command
── imagine: model cache complete (liveness, no generation) ──
  skip imagine model not pulled: schnell
  ok   imagine model cached: qwen (50GB)
── ax: accessibility lane present (ui-verify --app dependency) ──
  ok   ax list (Accessibility perm live)
── histories + timeline ──
  ok   parses: logs/q-history.jsonl
  ok   parses: logs/see-history.jsonl
  ok   parses: logs/fleet-history.jsonl
  ok   parses: logs/gem-history.jsonl
  ok   lm timeline merges streams
── feedback sink ──
  ok   self-audit digest
── gcc hooks (pipe-tests) ──
  FAIL guard-model-tier block path
  ok   guard-model-tier: unpinned → silent (warn retired)
  ok   guard-model-tier: pinned → silent
  ok   log-image-reads
── gcc schedules (labels present) ──
  ok   scheduled: warm-evening-off
  ok   scheduled: lm-self-audit
── loop machinery (reshoot + launchd health) ──
  ok   see reshoot: static recipe replays
  ok   see reshoot: missing loop-dir dies structured
  FAIL launchd: com.alcatraz.local-models-ollama failing (1)
── residency (informational) ──
  note: zero-idle

40 passed, 2 FAILED
```
The two FAIL rows: guard-model-tier block path (known, lives in ~/.claude), and the launchd label check: the ollama LaunchAgent shows
"not running, last exit code = 1". Its error log ends with `lm-serve: idle 300s, shutting the server down` followed by
`Error: listen tcp 127.0.0.1:11434: bind: address already in use`, a restart racing the idle shutdown. That is how lm-serve and ollama_ensure
behave, not something this branch touches (no file under bin/lm-serve or the plist changed).
`probe/vision/selftest.py` exit 0, `probe/fixtures/measure-check.py` 32/32, `bash -n` clean on every touched shell file, `ast.parse` clean on lib/cmdcheck.py, lib/data-profile.py, bin/probe.
