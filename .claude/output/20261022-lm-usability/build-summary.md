# lm usability build summary

Branch lm-usability in /Users/alcatraz627/Code/local-models-ux, 6 commits on top of main (8325275). Evidence with before and after output:
/Users/alcatraz627/Code/local-models/.claude/output/20261022-lm-usability/evidence.md

Verify: `scripts/verify.sh` 40 passed, 2 failed. Failures: guard-model-tier block path (known, outside this repo) and the launchd check on
com.alcatraz.local-models-ollama (job shows "not running, last exit code 1", log says "address already in use" after an idle shutdown; a restart race
in lm-serve, not touched here). `probe/vision/selftest.py` green, `probe/fixtures/measure-check.py` 32/32, `bash -n` and `ast.parse` clean.

| # | Finding | Status | Notes |
|---|---|---|---|
| 1 | q does not route plain requests | built | On a terminal with no flags: image path goes to see, file path becomes --ctx, near-miss intent is called out and runs as ask, leading gemini or web is pointed at q --web and lm gemini. One gray line each. Flags, --json, --stream-json, --diy and `--` keep old behaviour; `--route` forces, `--no-route` stops. File, typo, gemini and missing-file routes run live; the image-path hop was checked through see, not re-run through q (model budget). |
| 2 | No next move after a bad answer | built | `q again [--big\|--code\|--web]` (no flag = one local step up, never off the machine on its own; `--dry-run`), `q -c` continues your own last exchange, same-prompt-in-5-minutes hint. `again --big` and `--code` not run live (would load 17 and 23 GB while the MLX benchmark runs). |
| 3 | Own calls buried under agent traffic | built | Every row from q, see, imagine, lm gemini, fleet and describe-data records `tty` and `session` (null without a terminal). timeline, last, find, see more, see open -1, q show -1 and q -c default to mine; `--all` or `LM_ALL=1` shows everyone, other rows dimmed. Schema change is additive. |
| 4 | Nothing checks q cmd answers | built | `lib/cmdcheck.py`: `command -v` plus each long flag against man then `--help` (2 s budget, never runs the command; deny list keeps even `--help` off reboot, kill, rm and similar). Gray line, `checked` in --json, history, and `q check "<cmd>"` to use it alone. npx-style launchers whose package is not installed come back as "cannot be checked", not as a pass. |
| 5 | Long documents cut silently | built | Gray line with chars read, percent and what to do. Default --max-ctx left at 16000 (see "not built"). |
| 6 | Cannot find a past answer | built | `lm find "words"` (q, see, gemini, imagine; yours first, others dimmed; searches your words and the answer, not pasted documents). Timeline rows now show `-> first line of the answer`, and document rows show your words plus the file name. `q history port` still ignores its argument; not touched. |
| 7 | Exact tools sit behind slow guesses | built | Text mode only: "what text" answers from OCR with no model; ID or number questions print the exact text first, then the model picks the field; "how many" runs the pixel counter and skips the model unless it reports ambiguity. Names the verb in gray. `--no-measure` skips it. --json callers get the read they always got. |
| 8 | Clipboard images unsupported | built | `see paste ["q"]` (osascript PNG, clear error when the clipboard holds no image, tested both ways with the clipboard text restored) and `see latest ["q"]` (screencapture location, ~/Desktop fallback, `SEE_SCREENSHOT_DIR` override). `lm read paste\|latest` aliases. |
| 9 | Help written for an agent, too long | built | `lm help` is now jobs (ask, cmd, doc, read, diff, count, again, find, web, fast, status, failed, plus the old ones), worded to a person. Each tool's -h is 13 to 23 lines with `--all` for the rest, wrapped at 100 columns. `lm examples` stays long (98 lines) on purpose; it is the showcase. |
| 10 | -h breaks or has side effects | built | timeline, status, models, doctor, last, find, probe, opencode and every new verb answer -h without running. `lm opencode -h` no longer leases the 23 GB model first. |
| 11 | see diff text mode empty | built | Three plain lines (where, text, colours) plus the ASCII heatmap, built from the measured pack. Default judge is the MLX Qwen3-VL-8B with the plain-read fallback (minicpm, then evidence only). `model` is null when no model ran. A real MLX diff read was not run (model budget), only `--no-read`. |
| 12 | lm status hides MLX and memory | built | `memory` line from mem-guard and an `mlx` section from the process table (showed the 16.3 GB benchmark process). `lm status --json` left alone (150 ms contract). |
| 13 | warm vocabulary | built | `warm on 1h` = small model for an hour and prints `q stays fast until 12:51 (warm off to free 5.6 GB)`. Help rewritten without Tier W or lease. `lm fast 1h` and `lm fast off`. The three entry points (warm, lm warm, q on) still exist. |
| 14 | Failure rows lack reason and remedy | built | Timeline error rows print `code - remedy`, `q show` and `see show` add a WHAT TO DO line, new mlx failures keep the cause line instead of the first 200 characters, the gemini steps hint carries an absolute path. Old rows in history are not rewritten. |
| 15 | Front-door prominence | built | The default `lm` screen no longer leads with imagine, probe, bench and the rest; they sit under `lm more`. `lm ask` added. |
| 16 | Stale text | partly | Fixed `lm examples` (see default) and the imagine header (qwen default). The `--diy` narration labelling an image read `intent=describe-data` is unchanged. |
| 17 | Inconsistent input flags | partly | `lm gemini --file F "q"` for one-shot prompts. `--format` still wants a schema file (no inline shorthand), and see stays positional. |
| - | Front door | built | `lm "question"`, `lm cmd`, `lm read`, `lm diff`, `lm doc`, `lm again`, `lm find`, `lm review`, `lm status`, `lm fast`, `lm more`, each a thin alias; `lm more` is the old overview. Nothing removed or renamed. Colours kept. |

## Behaviour changes to know about

- A call with no terminal (agents, hooks, cron) has no "mine". For those callers `lm timeline`, `lm last`, `q -c`, `q show -1`, `see more` and `see open -1` now report
  "none of your calls from this terminal" unless `--all` or `LM_ALL=1` is given. This is what the brief asks for, and it is the change most likely to surprise an agent script.
  scripts/verify.sh was updated to pass `--all` where it relied on the global newest row.
- `q show N` on a missing entry exits 12. (Correction from the validator: it already did on main; `set -e` fired inside `show_entry`. Nothing changed there. The new part is the message, which now says how many of your calls exist.)
- Bare `q "..."` on a terminal can now route; every scripted form (flags, --json, no tty on stdin) behaves as before.

## Judged not worth building

- Routing in machine modes without --diy: agents would be surprised, so it stays off (`--route` opts in).
- Raising the default --max-ctx: the small model's window is about 8k tokens; the printed line and `--max-ctx` are the honest fix.
- An inline `--format` shorthand and a search argument for `q history`: separate features, not needed for the jobs in the audit.
- Going off this Mac on its own: `q again` with no lane never picks --web, and the q routing only names the web lanes.

## Not done

- Docs (docs/CAPABILITIES.md, docs/STATE.md) were not updated.
- No live runs of `q again --big|--code`, a real MLX `see diff` judge, or `q --json cmd`; the paths are wired but only the pieces around them ran.
- A hook nudge asked to settle an env-access convention for this repo (lib/cmdcheck.py reads os.environ for the man call). Left as is; the repo already reads env directly in python and bash.
