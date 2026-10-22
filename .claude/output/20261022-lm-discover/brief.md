# Build brief: make lm discoverable without docs, code or trial and error

Owner ask (2026-10-22, verbatim): "please ideate on how can I or an agent use this without every looking up the full docs / code / trial and error" then, approving the plan: "Yes please all of this is fine, ensure that for my own use I still get to see proper structured text and colors so I don't have to parse through blobs of plain text, also do we have docs for tealdeer or manpages, go ahead with all".

Repo: /Users/alcatraz627/Code/local-models. Work in a NEW git worktree at /Users/alcatraz627/Code/local-models-disc on a new branch `lm-discover` cut from `main` (`git -C /Users/alcatraz627/Code/local-models worktree add /Users/alcatraz627/Code/local-models-disc -b lm-discover`). Create a symlink `.venv` in the worktree pointing to /Users/alcatraz627/Code/local-models/.venv. Read /Users/alcatraz627/Code/local-models/CLAUDE.md first, then bin/lm (how the current front-door screen, `lm help <job>`, `lm more` and verb_help are built) and bin/_lib.sh (colour palette, TTY gating).

## The design (decided, build it)

One job registry is the single source of truth. Everything a person or an agent reads about lm is generated from it, and a fixture fails when anything drifts.

```
 lib/verbs.toml (one entry per job)
     ├─► lm / lm help <job> / lm more     generated screens, coloured on a terminal
     ├─► lm --capabilities [--json]       the agent menu
     ├─► lm how "<what I want>"           find the command, print it, --go runs it
     ├─► zsh completion                   verbs, flags, intents, recent screenshots
     ├─► man pages (lm.1, q.1, see.1, warm.1)
     ├─► tealdeer custom pages (lm, q, see, warm)
     ├─► docs/CAPABILITIES.md §0          generated block between markers
     └─► probe/fixtures/verbs-drift.py    every example parses, every -h exits 0, outputs in sync
```

### 1. Registry: lib/verbs.toml
One entry per job currently on the `lm` screen and in `lm help <job>` (ask, cmd, read, diff, doc, again, find, review, status, fast, count, web, failed, more, plus `lm more` items: gemini, fleet, rag, index, imagine, probe, bench, ui-verify, timeline, last, models, doctor, examples). Enumerate the real list from bin/lm before writing; do not invent jobs. Fields per job: `name`, `summary` (one line, written to a person), `usage` (command template), `examples` (list of {cmd, says}), `inputs`, `output` (text shape and the --json shape if any), `exit_codes`, `cost` (no model / small / big / code / vision / mlx, typical seconds), `leaves_mac` (bool), `side_effects` (e.g. loads a model, writes history, reads clipboard), `keywords` (for lm how matching), `see_also`, and `next` hints (see 6). Parse with the stdlib tomllib from `.venv/bin/python` or python3 (3.11+); keep bash readers going through one small python helper rather than parsing TOML in bash.

### 2. Generated human screens (colour is a requirement, not a nice-to-have)
`lm`, `lm help <job>` and `lm more` render from the registry. On a terminal they must look at least as good as today: coloured headings, aligned columns, examples visually distinct from descriptions, the cloud marker. Reuse the palette and TTY gating already in bin/_lib.sh (colour only when the output is a terminal and NO_COLOR is unset). Keep today's screen layout as the baseline: capture `lm`, `lm help read` and `lm more` output BEFORE you change anything (with colours, via `script -q /dev/null`) into the output dir, and compare after. Nothing that works today is removed or renamed.

### 3. Agent menu: `lm --capabilities` and `lm --capabilities --json`
JSON: `{version, jobs:[...registry fields...], conventions:{json_flag, exit_codes, history_scope, no_tty_behaviour}}`. Fast (<300 ms, no model, no network). Plain-text form is the human-coloured overview. Also `lm --capabilities <job>` for one job.

### 4. `lm how "<what I want>"`
Finds the job and prints the concrete command, without running it. Match model-free first (keyword and token overlap against summary, keywords, examples); only if the best score is below a threshold, ask the small tier with the registry as context, constrained with `q --format` and `-m small`. Output: the command (coloured, copyable), one line on why, and up to two alternatives. `--go` runs the top command after printing it. `--json` returns `{command, job, why, alternatives, matched_by: "keywords"|"model"}`. It never runs anything without `--go`, and never picks a cloud lane unless the words ask for web or gemini.

### 5. Errors carry the fix
Every `--json` error envelope from q, see, lm and warm carries `remedy` (one sentence) and `next` (a runnable command, or null). Find where envelopes are emitted (`emit_error` and friends) and add them centrally; reuse the remedy text that the timeline already prints for error codes. Text-mode errors already print a remedy in many places; make the remaining ones consistent.

### 6. "next:" hint after an answer
On a terminal only (never in --json, never without a tty), after a q/see answer print at most one gray `next:` line chosen from what happened: answer from the small tier → `lm again --big`; file truncated → `--max-ctx N`; see read with low-confidence or model fallback → `see <img> --ocr`; same prompt repeated → `lm again`. Off with `LM_HINTS=0`. Hints come from the registry `next` field, not hard-coded strings.

### 7. Context-aware bare `lm`
On a terminal, bare `lm` adds at most one gray suggestion line at the top when: the clipboard holds an image (`lm read paste`), or a screenshot newer than 10 minutes exists in the screenshot dir (`lm read latest`). These checks must take under 150 ms total and never fail the screen.

### 8. zsh completion
Generate `share/zsh/_lm`, `_q`, `_see`, `_warm` from the registry (verbs, flags, q intents from intents/*.toml, and for image args the newest screenshots). Install by symlinking into a directory ALREADY on the owner's zsh fpath (find one with `zsh -ic 'print -l $fpath'`; prefer /opt/homebrew/share/zsh/site-functions). Do NOT edit ~/.zshrc or any shell rc file; if no writable fpath dir exists, stop and put the exact one line the owner should add in your report.

### 9. Man pages
Generate `share/man/man1/lm.1`, `q.1`, `see.1`, `warm.1` (roff, from the registry plus each tool's `-h --all` rows). Install by symlinking into a directory already on `manpath` (check `manpath`; prefer /opt/homebrew/share/man/man1). Verify `man lm` renders (`man -P cat lm` shows the NAME and EXAMPLES sections). No rc edits.

### 10. tealdeer pages
Find the custom pages dir with `tldr --show-paths` (it reports the custom pages directory, which may need `custom_pages_dir` set in the tealdeer config; if the config must be edited, edit only the tealdeer config file and say so in the report). Generate `lm.page.md`, `q.page.md`, `see.page.md`, `warm.page.md` in tldr format (title, one-line description, 5-8 `- description:` / `` `command` `` pairs from the registry examples) into share/tldr/ in the repo, symlink into the custom dir, and verify `tldr lm` renders them.

### 11. Generated doc block
Replace the hand-written §0 front-door code block in docs/CAPABILITIES.md with a generated block between `<!-- verbs:begin -->` and `<!-- verbs:end -->` markers. One command regenerates every output: `scripts/gen-verbs.sh` (screens are rendered live, so it covers completion, man, tldr and the doc block).

### 12. Drift fixture (write it FIRST, watch it go red)
probe/fixtures/verbs-drift.py, model-free: the registry parses; every job named on the `lm` screen exists in the registry and vice versa; every example's first two tokens are a real verb; every job's `-h` exits 0 with no side effects; generated files on disk equal a fresh generation (so a registry edit without `gen-verbs.sh` fails); `lm --capabilities --json` validates against the registry; `lm how` returns the expected job for at least 12 phrasings taken from the registry keywords and 6 natural phrasings you write (e.g. "text from my last screenshot" → read latest, "redo that on a bigger model" → again --big, "what is using memory" → status) without calling a model. Run it before building and record that it fails; wire it into scripts/verify.sh beside the cmdcheck-route line using that line's pattern.

## Constraints
- Nothing stays warm by default. Model budget: at most 4 small-tier calls (for testing the model fallback of `lm how`); nothing over 8 GB. Run `/Users/alcatraz627/Code/local-models-disc/bin/warm off all` before finishing if you loaded anything.
- Scripted and no-tty behaviour of existing commands must not change except for the added `remedy`/`next` fields in JSON errors.
- Always run worktree binaries by absolute path; PATH points at the main checkout. Man and completion symlinks you install must point at the MAIN checkout paths (/Users/alcatraz627/Code/local-models/share/...) so they keep working after merge; note they will dangle until the merge lands, which is expected.
- Commits on `lm-discover` after each logical unit; short imperative subjects; NO Co-Authored-By or any Claude trailer (a hook rejects them). Never push. Never merge. Do not touch the main checkout except for writing your report into this output dir.
- `bash /Users/alcatraz627/Code/local-models-disc/scripts/verify.sh` must end with only the known failures: guard-model-tier block path, launchd com.alcatraz.local-models-ollama, and the lm doctor PATH checks (worktree-only).
