# Build report: lm discoverability

Branch `lm-discover` in the worktree /Users/alcatraz627/Code/local-models-disc (cut from main at f3e5fea). Not pushed, not merged. The `.venv` symlink in the worktree is untracked on purpose.

Commits (no trailers):

| sha | subject |
|---|---|
| b2c1501 | verbs-drift fixture: registry, screens, menu, how and generated files agree (red until built) |
| c1295ee | lm: render screens, agent menu and how from lib/verbs.toml |
| 45ad592 | json errors carry remedy and next; gray next: hint after answers |
| 5dca307 | generate zsh completion, man pages, tldr pages and the docs block |
| 67eaabc | completion and man fixes, warm fix lines, fixture covers the screenshot suggestion |

## Per brief item

| # | Item | Status | Proof |
|---|---|---|---|
| 12 | Drift fixture first | built | b2c1501. Red: `fixture-red.txt` (13/59 passed, exit 1) before any registry existed. Green: `fixture-green.txt` (400/400 at the final commit). Wired into scripts/verify.sh beside the cmdcheck-route line. |
| 1 | Registry lib/verbs.toml | built | 35 entries: 27 jobs (including `how` and everything on `lm more`), 3 tools (q, see, warm), 5 help topics (count, web, failed, json, table). Read by one python helper, lib/verbs.py (stdlib tomllib). |
| 2 | Generated screens, colour kept | built | `lm`, `lm help <job>`, `lm more` render from the registry through the _lib.sh palette (colour only when stdout is a terminal and NO_COLOR is unset). Captured with `script -q` in before/ and after/. `diff before/help-read.ansi after/help-read.ansi` is empty. `lm` differs by one added line (`lm how`). `lm more` differs by the added `lm how` line, and the EXAMPLES column is now aligned to one width (before it was hand-padded). Fixture checks the screens are coloured on a pty and plain when piped. |
| 3 | `lm --capabilities [job] [--json]` | built | `bin/lm --capabilities --json` runs in 52 ms (no model, no network). JSON is `{version, jobs, conventions{json_flag, exit_codes, history_scope, no_tty_behaviour}}`. |
| 4 | `lm how` | built | Words first, small tier only below threshold 3.0, `--go`, `--json`, `--no-model`. Model fallback proven once: `lm how "my laptop fan is loud and things feel sluggish" --json` returned `{"command":"lm status","job":"status",...,"matched_by":"model"}`. Cloud jobs and `--web` examples are only eligible when the words contain web, gemini, internet, online, news and the like. `--go` refuses a command that still holds a placeholder such as shot.png. |
| 5 | Errors carry the fix | built | `lm_err_json` in bin/_lib.sh is the one emitter, used by q, see, lm (usage_fail), fleet, rag, gemini and ui-verify, plus q's embedded python and see reshoot. `bin/see /nonexistent/zz.png --json` prints `{"ok":false,"code":"img_unreadable","message":"...","remedy":"the image could not be found; check the path","next":"lm read latest"}`. The timeline's remedy texts are now checked equal to the registry by the fixture. Text mode gets one gray `→ remedy (try: next)` line on a terminal only. warm has no JSON error envelope (its `status --json` always succeeds), so it only got the terminal fix line on its two failure messages. |
| 6 | `next:` hint | built | Words live in the registry `[hints]`. q: repeat, truncated and small-tier answer. see: unsure or fallback read. Only on a terminal in text mode, off with `LM_HINTS=0`. Proven on a pty: `bin/q "what is 2 plus 2, one word"` printed `next: lm again --big  (not right? the bigger model)`. UNCONFIRMED on a live run: the see hint (needs a vision model load) and the truncated and repeat hints. The registry text for all four is checked by `verbs.py hint`. |
| 7 | Context-aware bare `lm` | built | Pty test with a fresh png in SEE_SCREENSHOT_DIR prints `suggest: you took a screenshot a moment ago, lm read latest` above the screen. Costs about 85 ms (156 ms vs 71 ms with `LM_HINTS=0`, both through `script`). Clipboard check is `osascript -e 'clipboard info'` capped at about 120 ms and killed after that. UNCONFIRMED: the clipboard-image branch (no image on the clipboard to test with). Fixture covers the screenshot branch, `LM_HINTS=0`, and piped silence. |
| 8 | zsh completion | built | share/zsh/_lm _q _see _warm. `zsh -n` clean. Driven in a zpty: `warm sta<TAB>` gives `warm status`, `see lat<TAB>` gives `see latest`, `lm again --b<TAB>` gives `lm again --big`, `q --js<TAB>` gives `q --json`, `lm hel<TAB>` gives `lm help`. Installed as symlinks in /opt/homebrew/share/zsh/site-functions (already on fpath) pointing at /Users/alcatraz627/Code/local-models/share/zsh. A new completion may need `rm ~/.zcompdump*` once. |
| 9 | Man pages | built | share/man/man1/lm.1 q.1 see.1 warm.1, symlinked into /opt/homebrew/share/man/man1 (on manpath) pointing at the main checkout. Proof while the lm link pointed at the worktree: `man -P cat lm` shows NAME, SYNOPSIS, COMMANDS, EXAMPLES, EXIT STATUS. I then re-pointed it at main, so `man lm` fails until the merge lands (expected). `man -P cat /Users/alcatraz627/Code/local-models-disc/share/man/man1/warm.1` renders. |
| 10 | tealdeer pages | built | `tldr --show-paths` custom dir is /Users/alcatraz627/Library/Application Support/tealdeer/pages, so no tealdeer config edit was needed. share/tldr/{lm,q,see,warm}.page.md, 6 to 8 entries each. `tldr lm`, `tldr q`, `tldr see`, `tldr warm` all rendered while linked to the worktree; now linked to main (dangling until merge). Three old 120-byte stub pages (lm, q, warm: "Local-model chat / inference CLI") were replaced: copies are in `replaced-tldr-stubs/`, the originals went to the Trash. |
| 11 | Generated doc block + one command | built | `scripts/gen-verbs.sh` regenerates completion, man, tldr and the block between `<!-- verbs:begin -->` and `<!-- verbs:end -->` in docs/CAPABILITIES.md section 0 (front screen plus a table of every entry). The screens themselves render live. |

## Fixture red and green

Red (before building): `fixture-red.txt`, last line `13/59 checks passed`, exit 1. Green: `fixture-green.txt`, last line `400/400 checks passed`.

Mutation proof that it guards: editing a `front_says` without regenerating failed `docs/CAPABILITIES.md block equals a fresh generation`; adding the typo example `lm lasst` failed `example verb ok: lm lasst` and the man page check. Both restored.

## verify.sh tail

```
  ok   verbs registry in sync (screens, menu, how, completion, man, tldr, docs): 397/397 checks passed
  ...
  FAIL lm doctor — run it directly to see which check          (worktree PATH checks, known)
  FAIL guard-model-tier block path                             (known)
  FAIL launchd: com.alcatraz.local-models-ollama failing (1)   (known)
40 passed, 3 FAILED
```

That run was before the last fixture additions (now 400 checks). Only the three known failures remain.

## Installed files

| What | Link | Target |
|---|---|---|
| zsh completion | /opt/homebrew/share/zsh/site-functions/_lm _q _see _warm | /Users/alcatraz627/Code/local-models/share/zsh/ |
| man pages | /opt/homebrew/share/man/man1/lm.1 q.1 see.1 warm.1 | /Users/alcatraz627/Code/local-models/share/man/man1/ |
| tldr pages | /Users/alcatraz627/Library/Application Support/tealdeer/pages/lm q see warm .page.md | /Users/alcatraz627/Code/local-models/share/tldr/ |

All of these dangle until the branch is merged. No shell rc file and no tealdeer config were edited.

## Skipped or limited

- `lm <verb> -h` (verb_help for ask, cmd, read and the others) is still hand-written in bin/lm. The registry checks that each answers `-h` with exit 0 and no side effects, but the text is not generated from it. Not in the brief's list of generated outputs.
- `lm examples` (the long showcase) is still hand-written, for the same reason.
- rag.py, data-profile.py, websearch and the other lib python helpers still print their own `{ok:false}` objects; q and the wrappers re-emit through the central path, but a helper run directly does not carry remedy and next.
- The cost line in `lm --capabilities <job>` reads awkwardly where cost_secs has parentheses ("vision, 1 (--ocr) to 30 (cold vision model) s").
- Model use: 2 small-tier calls (one `lm how` fallback, one `q` for the hint check). Nothing larger loaded. `warm off all` run at the end: nothing resident.
- Hook nudges seen while building (env-read note on the fixture and verbs.py, banner-comment note, CAPABILITIES.md prose-quality note) were not acted on beyond removing the fixture's banner comments. The CAPABILITIES.md note says the file already failed before this change.
