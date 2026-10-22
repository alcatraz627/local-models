# Fixes for the lm-discover validation

Branch `lm-discover` in /Users/alcatraz627/Code/local-models-disc, HEAD 2c3d77d. Not pushed, not merged. Finding numbers (F1 ...) are the ones in /Users/alcatraz627/Code/local-models/.claude/output/20261022-lm-discover/validator.md. Scratch work is under /private/tmp/claude-501/-Users-alcatraz627-Code-local-models/a48a6eeb-34f8-4fed-9269-015afa95b460/scratchpad/disc-fix and `disc-fix-mut`.

Final state: drift fixture 648/648, `scripts/verify.sh` 41 passed, 3 FAILED (only the three known ones). Nothing resident (`warm off all` run last).

## Commits

| sha | subject | letters |
|---|---|---|
| a7ccd1e | lm how: registry commands only, safe --go, cloud needs its word | A B C E, F12 F13 F14 |
| 643b380 | json errors on every path, -h on subcommands, warm checks model first | D, F10 F11, F15 (-h), first fixture growth |
| 6ab52dd | completion offers screenshot names via _wanted; how line fits one row | F13 |
| 7e81c94 | drift fixture: retry the clipboard probe check on a busy machine | F |
| 90ce8d6 | lm how: fewer weak alternatives | C |
| a1dafeb | drift fixture: cloud jobs mark every example cloud | F |
| 2c3d77d | server_down with a custom OLLAMA_HOST has no next command | E |

Splitting a7ccd1e per letter was not practical: A, B, C, E and the generator fixes all edit the same two files (lib/verbs.py, lib/verbs.toml) and the files generated from them. The shas above say which commit carries which letter.

## A. `lm how --go` (F1, F3, F4, F6), a7ccd1e

- Model fallback: `ask_small` asks `q --json -m small --format` with `{"job": {"enum": [<non-cloud job names>]}}`. Only a job name is read back, and the command shown is the registry's first eligible example. The code that validated or ran model-written commands is gone (`how_model` in /Users/alcatraz627/Code/local-models-disc/lib/verbs.py).
- Registry field `go` on 10 jobs: read (`lm read latest`, `lm read paste`), help (`lm help`, `lm --capabilities`), more, examples, status, models, doctor, last, timeline, failed (`lm timeline 10 --errors`). Every other job refuses `--go` with exit 2. A job-level `fill` says what the person supplies, and an example-level `fill` list marks the exact parts to highlight.
- `--go` runs `shlex.split(command)` as an argv list (`run_go`), never `shell=True`. The hand-written placeholder filename regex is deleted.
- `--go` with `--json` is a usage error with the envelope on stdout. `--json` answers gain `go` (would `--go` run it) and `fill` (what to supply, or null).

Proof:
```
$ lm how "summarize this pdf" --go --no-model          (on a pty the report.pdf part is bold yellow)
lm doc report.pdf
why: ask about, or summarize, a file (matched "summarize a file")
or:  lm doc report.pdf "what is the decision?"  an answer grounded in the file
lm how: fill in the file path and run it (--go only runs commands that need nothing from you)      rc 2

$ lm how "summarize this pdf" --go --json
{"ok": false, "code": "invalid_args", "message": "--go cannot be combined with --json: read .command from the answer and run it yourself", ...}   rc 2

$ lm how "build a search by meaning index of my docs" --go --no-model      rc 2 (lm rag index is never run)
$ lm how "what is using memory" --go --no-model                            prints lm status, then runs it
$ lm how "my laptop fan is loud and things feel sluggish" --json           (real small-tier call, 1 of them)
{"command": "lm status", "job": "status", "why": "what is loaded and what is free (chosen by the small model)", "alternatives": [], "matched_by": "model", "go": true, "fill": null}
```
Fixture rows that guard it: go commands are plain suite commands and are listed examples; `--go` calls `subprocess.run` with a list and no shell; for every job without `go` that `lm how` can reach by its first keyword, `--go` exits 2 and makes no call (at least 10 jobs); model path rejects a shell string, a cloud job nobody asked for, a missing job, a non-job tool, a reply with no data; a model reply carrying `"command": "evil-command --now"` still shows `lm status`; the enum sent to the model holds no cloud job.

## B. Cloud lanes (F2), a7ccd1e

`cloud_state` in lib/verbs.py: a cloud word (`web`, `internet`, `google`, `gemini`, the pair `online search`) counts unless one of `not no dont without never avoid` sits within four words before it, or the same clause (split on punctuation, `but`, `however`, `then`) holds `keep it local`, `local only`, `offline` or `stay local`. The generic triggers `current online research news browse` are gone from the registry (`[how]` now has cloud_words, negators, local_phrases, fresh_words). Fresh-fact words (`current latest newest news weather price`, no cloud word, no negation) keep the top answer local (`ask`) and add `q --web ...` as an alternative marked with a cloud sign and "(leaves this Mac)".

```
$ lm how "do not use the web, tell me what 2+2 is" --no-model      -> lm "how do I see ..." (ask), no cloud
$ lm how "without gemini, summarize this big folder" --no-model    -> q --preflight --ctx report.pdf (doc)
$ lm how "whats the newest node version" --no-model --json         -> ask, alternatives [{"command": "q --web ...", "leaves_mac": true, ...}]
```
Fixture: the 4 negated phrasings, positive controls (web, gemini), the fresh-facts case, and every cloud job's own keywords with the cloud word removed.

## C. Matching (F5), a7ccd1e (alternatives tidy-up in 90ce8d6)

Fixed through keywords and examples in lib/verbs.toml plus three matcher changes: typo repair toward the registry's own words (one edit, five letters or more), a stem fix for doubled consonants (stopping to stop), and "not/no/without/never/avoid" as stop words. `review my git diff` now gives `lm review`; `commit message from my diff` gives `git diff | q commit`; `unload all models` gives `warm off all` and `free up memory by stopping models` gives `lm fast off` (new `warm off all` example under the fast job); `what did the last call say` gives `lm last`; `run many prompts in parallel` gives fleet; `generate an image of a cat` gives `imagine "a cozy reading nook"` (a first draw, not refine). Alternatives are deduped, need two shared words, and never offer how, help, more or examples.

The fixture now holds all 70 phrasings from the validator's item-1 table, each with its correct job (or `no_match` where nothing should match) and, where it matters, the exact command; the 4 negation phrasings expect a non-cloud job. All run with `--no-model`.
```
harness over the table: 0 misses of 70      (was 26 mismatches against these expectations at the start)
fixture:                648/648
```
Judgment calls: `tell me a joke` and `sumarize my clipbord` now expect `ask` (the small model can do both); `weather today` expects `ask` with the web as a marked alternative; `explain this error` accepts ask or failed; `what is installed and what is running and is it healthy` accepts status, doctor or models.

## D. JSON envelopes (F7), 643b380

`bin/lm` sets `MODE=json` when `--json` is anywhere in the arguments, so `usage_fail` also prints the envelope. `json_only` now sets `JSON_ONLY` instead of echoing (the old `$(...)` swallowed the envelope). Covered: `lm models|status|timeline --bogus --json`, `lm last --json` with no history (exit 12), `lm how --json` with no request, `lm rag --json`, `lm fleet --json`, `lm gemini --json` (exit 2 in JSON mode only; text mode keeps its help screen and exit 0), `lm models --json` with the server down (exit 10). `lm last --json` is new and prints the history row as one object. `warm on <missing model>` checks `/api/tags` first: `warm on zzz` prints "failed to load 'zzz': it is not installed" and exits 11 without printing "loading". `imagine` has no JSON mode and was skipped as agreed.
```
$ lm rag --json
{"ok":false,"code":"invalid_args","message":"say what to do: index, search, ask or status (lm rag -h)","remedy":"...","next":null}      rc 2
$ OLLAMA_HOST=127.0.0.1:1 lm models --json
{"ok":false,"code":"server_down","message":"server down: nothing answered at 127.0.0.1:1","remedy":"nothing answers at 127.0.0.1:1 (OLLAMA_HOST points there); ...","next":null}      rc 10
$ warm on zzz        rc 11, nothing printed before the error
```

## E. `next` values (F8), a7ccd1e and 2c3d77d

`ctx_too_large`, `sheet_missing`, `ocr_missing`, `repomix_missing`, `img_unreadable` now have `next` null, plus `clipboard_empty` and `no_index` (a rag index command with a guessed folder). The useful command lives in the remedy sentence (`ctx_too_large` also says the cloud lane leaves this Mac; the matching text in the timeline table in bin/_lib.sh is updated and the fixture checks they agree). `server_down` names OLLAMA_HOST and has `next` null when it is not the default host. Fixture: every remaining `next` is a complete suite command with no placeholder, no install, nothing that leaves the Mac; the named codes are null; the live `see ... --json` and `lm models --json` envelopes are checked.
```
$ see --json /nonexistent/zz.png
{"ok":false,"code":"img_unreadable",...,"remedy":"the image could not be found; check the path (for your newest screenshot instead: lm read latest)","next":null}
```

## F. Drift fixture (F9, F15), 643b380, 7e81c94, a1dafeb, a7ccd1e

New checks: registry exit codes against behaviour (last 12, help bad job 2, how no_match 12, timeline bad flag 2, read/diff/see missing image 12, `lm models` with `OLLAMA_HOST=127.0.0.1:1` 10, status 0, doctor 1, index 2, probe 2, bench bad set 1, gemini no args 0 and with `--json` 2, find 2, one unknown word 2); bin/lm's dispatch table against the registry in both directions; the cloud filter; colour from `lm how` piped (with and without `CLICOLOR_FORCE`) and on a pty; the hint emitter called directly with stdout and stderr captured, plus a static check that bin/q delegates to it and bin/see redirects to stderr; `--go` guard; model-path stub; `-h` on `warm on`, `q show`, `imagine refine`, `lm warm on`.

Registry claims fixed to match behaviour: bench ("1 failed, a missing fixture set ends in a Python error"), gemini no args ("0 ... or the help screen; 2 with --json"), the exit-2 wording ("a single unknown word; several words are taken as a question"), `lm last` (adds `--json`, exit 2). `warm on -h`, `q show -h` (and `q history -h`) and `imagine refine -h` now print help and exit 0.

### Mutation table (each applied in a scratch copy, never in the worktree)

Run against the tree at 7e81c94 (plus the two later matcher tweaks, which do not touch the guarded paths); baseline in the same harness was 646/646 green.

| # | Mutation | Fixture | First failing check |
|---|---|---|---|
| 1 | `lm last` exits 7, registry says 12 | RED 645/646 | exit code of lm last is 12 [rc=7] |
| 1b | `lm help <bad job>` exits 1, registry says 2 | RED 645/646 | exit code of lm help nosuchjob is 2 [rc=1] |
| 2a | ghost verb `zap` in bin/lm | RED 645/646 | every verb bin/lm dispatches is in the registry [zap] |
| 2b | registry verb `rag` renamed `rag2` in the dispatch | RED 643/646 | dispatched but not in the registry [rag2]; in the registry but not dispatched [rag] |
| 3a | job-level cloud filter removed | GREEN 646/646 | none: an equivalent mutant, because every example of a cloud job is marked cloud and the example filter still excludes them. Fixed by making that a checked invariant (a1dafeb) |
| 3c | job-level and example-level cloud filters removed | RED 633/648 | how 'do not use the web ...' and 'whats the newest node version' pick `q --web` |
| 3b | negation ignored | RED 642/646 | how never picks a cloud lane against the words |
| 4 | `Pal(True)` in `cmd_how` (colour when piped) | RED 644/646 | lm how piped: no escape codes (and the CLICOLOR_FORCE variant) |
| 5a | hint emitter writes to stdout | RED 642/646 | emit_hint small_answer: stderr only |
| 5b | bin/q prints its hint with print() | RED 645/646 | q writes its hint through the emitter, not to stdout |
| 6a | `--go` refusal guard removed | RED 621/646 | --go never runs ask, which has no go field (and more) |
| 6b | every command counts as runnable | RED 621/646 | the same checks |
| 7 | model path accepts a reply that is not a job name | RED 642/646 | model path rejects a shell string instead of a job name [raised KeyError] |

Mutation 3 as the validator ran it (3a) was indeed missed, but only because it was an equivalent mutant; 3c is the real removal of the cloud filter and goes red.

## G. Small items

- F10, 643b380: bare `lm` only looks in `SEE_SCREENSHOT_DIR` when it is a directory. A file there prints no suggestion (fixture, pty).
- F11, 643b380: the clipboard probe waits up to 7 polls of 20 ms plus process start, measured at about 200 ms. Bare `lm` on a pty, three runs each: slow osascript stub (sleeps 8 s) 0.25 to 0.26 s; same plus a 5000-file screenshot dir 0.25 to 0.26 s; real osascript 0.14 s; `LM_HINTS=0` 0.05 s. All under 300 ms. A stub that answers in 30 ms is seen (fixture, with three tries for a busy machine).
- F12, a7ccd1e: q already prints the exact "the whole file: --max-ctx N" line for every truncation in text mode, so the generic `--max-ctx 40000` hint (and its registry entry and the doc job's `next`) is removed. Verified the other q hint on a pty: `next: lm again --big  (not right? the bigger model)` still prints, on stderr, through `verbs.emit_hint`.
- F13, a7ccd1e and 6ab52dd: flag descriptions are cut at the end of a clause (up to 78 characters), never inside brackets, never on a dangling article. `--big` and `--code`, `--route` and `--no-route` each get their own text. `-m`/`--model` take a value in `_q` (tier list) and `_see` (free text): the old code removed `-m` from inside `--model` while stripping flags, so neither had one. Screenshot names go to `compadd` as an array through `_wanted`, so a name with spaces is one candidate. Verb and intent descriptions use the same shortening.
- F14, a7ccd1e: `.TH` carries `manual_date` from the registry, non-ASCII is written as roff `\[uXXXX]`, and lines are folded under 73 bytes (request lines continue with a backslash). `mandoc -T lint` on all four pages prints nothing.
- F15 leftovers: `lm how` alternatives are deduped; `lm how x --jsno` is a usage error. `lm help web` still adds the blank line and the cloud note compared with main; that is registry-driven and was not touched.

## Screen comparison against /Users/alcatraz627/Code/local-models/.claude/output/20261022-lm-discover/after

Captured with `script -q` on a terminal with `SEE_SCREENSHOT_DIR` at an empty scratch dir; files at /private/tmp/claude-501/-Users-alcatraz627-Code-local-models/a48a6eeb-34f8-4fed-9269-015afa95b460/scratchpad/disc-fix/new-lm.ansi, new-help-read.ansi, new-more.ansi.

- `lm help read`: identical to after/ (empty diff).
- `lm`: one line differs, the how row: `find the command for it, without running anything (--go runs it)` became `find the command for it, run nothing (--go runs read-only ones)`. Same colours, same single-row layout, fits the 65-column cell without wrapping.
- `lm more`: one line differs, the how row: `(--go runs it)` became `(--go runs read-only ones)`.
- Colour is kept everywhere (cyan labels, yellow headings, dim text). Nothing got plainer. `lm how` itself is now coloured with the fill-in parts of a template in bold yellow, which is new.

## Not done, or not confirmed

- UNCONFIRMED: interactive TAB completion of screenshot names with spaces. I tried a zpty harness four times; it could not deliver the tab to zle reliably (same as the validator), so `zsh -n` and the generated text are all that was checked. `_lm_shots` now uses the standard `_wanted ... compadd -- "${shots[@]}"` form.
- UNCONFIRMED: the clipboard branch with a real image on the clipboard (a stub osascript was used; I never touched the real clipboard or the owner's screenshots).
- `imagine --json` stays unsupported (agreed).
- `-m`/`--model` and `-c`/`--continue` keep one shared description for both spellings, because they mean the same thing.
- Model budget: 2 direct small-tier calls (one `lm how` fallback, one `q` hint check). `scripts/verify.sh` was run twice and makes its own small-tier calls (the fleet and q checks), so the total for the session is higher than 3 if those count. Nothing over 8 GB; `warm off all` run after each.
- The worktree edit hook printed an env-access nudge when `os.environ.get("OLLAMA_HOST")` was added to lib/verbs.py (it wants a central env accessor and a `.claude/conventions/env-access.md`). I did not set that up: the repo has no such convention and the build report recorded the same nudge. Owner call.
- The mutation harness (mut.py and the stub scripts) lives in the scratchpad, not in the repo.
