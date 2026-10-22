# Build brief: make lm usable (implement the usability audit)

Spec: `/Users/alcatraz627/Code/local-models/.claude/output/20261022-lm-usability/audit.md`.
Read it in full. Every finding has evidence and a concrete "what the person would see after"; build
to that. The owner's words: "the colors and examples and explicit flags and helpers are good but so
much else is still lacking for me to be able to use it."

## Build, in this order (each a commit or two)

1. **Help that works (findings 10, 16, 9).** `-h` on every `lm` verb prints help and never runs
   anything (`lm timeline -h`, `lm status -h`, `lm probe -h`, which currently fires a probe against a
   model named "-h"). Fix the stale text (`lm examples` see default, `imagine -h` "Flux"). Rewrite
   `lm help <job>` around the owner's jobs (audit walkthrough rows 1-17), worded to a person, not to an
   agent: no "inspect the image yourself". Cap each tool's `-h` at about 25 lines with `--all` for the
   rest, and wrap at 100 columns.
2. **History knows whose call it was (finding 3).** Every history line written by q, see, imagine,
   lm gemini and fleet records `tty` (the controlling terminal, or null) and `session`
   (`$TERM_SESSION_ID` or similar, else null). "Mine" means same tty/session as the caller, or, in a
   non-terminal call, nothing. `lm timeline`, `lm last`, `see more`, `see open -1`, `q show -1` and
   `q -c` default to the caller's own rows, and `--all` shows everything, with agent rows dimmed.
   Old rows with no tty field count as "not mine" except in `--all`. Keep the JSON history schema
   additive (new fields only).
3. **A next move after a bad answer (finding 2).** `q again [--big|--code|--web]` re-asks the
   caller's last question on a stronger lane. `q -c` continues the caller's own last exchange (item 2).
   When the same prompt repeats within 5 minutes, print the gray hint the audit gives.
4. **q routes plain requests (finding 1).** In text mode, before any model call, run cheap
   deterministic checks: an existing image path in the prompt goes to `see` (exact OCR first for text
   asks, per item 7); an existing non-image file path goes to `--ctx`; a near-miss intent word gets the
   did-you-mean line and runs as ask; a leading "gemini"/"web" word suggests `--web` / `lm gemini`. Narrate
   each route in one gray stderr line. Flags and `--json` callers keep today's exact behaviour (no
   routing in machine modes unless `--diy`), so agents are not surprised.
5. **Check q cmd answers (finding 4).** After a `cmd` answer: `command -v` the binary and look up each
   long flag in `<bin> --help` / `man` output (never execute the command itself; time-box the lookup
   at 2s). One gray line: `· checked: <bin> ✓ · --flag ✗ not in <bin> --help → q again --web`.
   Include the check result in `--json` as `checked`.
6. **Say what was read (finding 5).** When context is truncated, print the gray line from the audit
   and keep `truncated` in JSON.
7. **Exact first in see (finding 7).** When a `see` question asks for text, an ID, a number or
   "how many", run `--ocr` or `see count` first and print that as the measured answer, then the model
   read (or skip it when the measured answer is unambiguous). One gray line names the exact verb.
8. **Clipboard and latest screenshot (finding 8).** `see paste ["q"]` and `see latest ["q"]` as the
   audit describes (osascript for PNG from the clipboard, `defaults read com.apple.screencapture
   location` with a ~/Desktop fallback). Clear error when the clipboard holds no image.
9. **Find past answers (finding 6).** `lm find "words"` searches prompt and response across the
   histories, own rows first, and prints `tool#N  time  question  → first line of answer`. Timeline rows
   show the first line of the answer, and doc-intent rows show the user's words plus the file name.
10. **see diff text mode (finding 11).** Text mode prints a 3-line plain summary from the evidence pack
    (where, in words; whether text changed; whether colours changed) plus the ASCII heatmap; the default
    judge becomes the MLX Qwen3-VL-8B (same fallback rules as plain see reads: minicpm, then evidence only);
    `model` is null in the envelope when no model ran.
11. **lm status shows memory and MLX (finding 12)**; **warm takes a duration first (finding 13)**:
    `warm on 1h` means the small model for 1h, and it prints when it will unload; **failure rows say
    why and what to do (finding 14)**; **one input flag (finding 17)**: `--file` accepted by `lm gemini`.
12. **The front door (proposed section).** `lm` with no arguments shows jobs, not tools, exactly in the
    spirit of the audit's sketch: `lm "question"`, `lm cmd`, `lm read`, `lm diff`, `lm doc`, `lm again`,
    `lm find`, `lm review`, `lm status`, `lm fast`, `lm more`. Each is a thin alias over existing tools.
    `lm more` prints today's overview. Nothing existing is removed or renamed; `q`, `see`, `imagine`,
    `review`, `warm` and every existing `lm` verb keep working exactly as before. Keep the colours.

## Verify (required)

- `bash -n` every shell file you touch. Python: `.venv/bin/python -m py_compile`.
- For each item, run the audit's own evidence commands again and paste before and after into
  `.claude/output/20261022-lm-usability/evidence.md` (in the main repo path below).
- Model calls: at most 12 small ones (q small tier, see on probe/vision/fixtures images). No imagine
  generation, no review runs, no fleet runs, no lm gemini prompts, no pulls/deletes.
- A Qwen3.6-27B MLX benchmark may be running in parallel. Do not run `warm on` big tiers, do not stop
  ollama, do not touch `probe/vision/results/` or `~/.cache/huggingface`.
- Run `bash scripts/verify.sh` at the end (in your worktree) and record pass/fail. One failure
  (guard-model-tier block path) is known and outside this repo; anything else new is yours to fix.
- Run `.venv/bin/python probe/vision/selftest.py` and `probe/fixtures/measure-check.py`; both must stay green.

## Constraints

- Work only in the git worktree /Users/alcatraz627/Code/local-models-ux (branch lm-usability). Use
  /Users/alcatraz627/Code/local-models/.venv/bin/python. Write the evidence and summary files to
  /Users/alcatraz627/Code/local-models/.claude/output/20261022-lm-usability/.
- Follow the repo's comment style: short, human, say why; no em dashes in prose; no "Phase N" notes.
- Shared helpers go in bin/_lib.sh; read the sibling code before adding a pattern.
- Commit in small commits, plain imperative subjects, no AI attribution trailers.
- Finish with `.claude/output/20261022-lm-usability/build-summary.md`: a table of the 17 findings plus the
  front door, each built / partly / not, with the reason, and anything you judged should not be built.
