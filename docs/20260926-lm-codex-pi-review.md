# Local model toolkit, Codex integration, and Pi: review for owner decisions

This report reviews the current `lm` toolkit and proposes bounded changes. It is a decision document. No model, package, skill, or harness configuration was installed or changed during the review.

## Recommendation

Keep `lm` as a set of specialist tools. Give Codex three clear reasons to call it: exact local OCR, deterministic visual comparison, and large batches with an explicit task judge. Let Codex inspect the screenshot or code and own the final decision. Verify the repaired spreadsheet path and tighten evidence claims before making local calls more eager. Trial Pi only as a restricted local or Gemini workbench for workflows that the current `lm` CLI and OpenCode cannot already cover.

## What is here and how it works

The front door is `/Users/alcatraz627/Code/local-models/bin/lm:249`. It dispatches to scripts in `bin/` and `lib/`; `/Users/alcatraz627/Code/local-models/config.sh:9` chooses the small, big, code, vision, sweep, embedding, image, and Gemini models. Ollama serves the local chat models; `see --ui` defaults to a separate `mlx-vlm` process (`config.sh:41-54`, `bin/see:536-560`). The Gemini wrapper invokes an external service in plan mode (`lib/gemini:2-23`). Its prompts and history are therefore a different privacy and cost class from local calls.

| Human or agent job | Existing entry point | Useful result | Current boundary |
|---|---|---|---|
| Quick answer, command, structured extraction, document Q&A | `q`, intents in `intents/*.toml` | Text or JSON envelope; PDF, Word, HTML, and spreadsheet extraction | The small model is fast for narrow tasks. A factual or code conclusion needs source checking (`bin/q:175-183`, `bin/q:390-456`). |
| Exact screenshot text | `see --ocr` | Apple Vision words and positions | Model free and measured fast; inspect source pixels for ambiguous text (`bin/see:343-377`). |
| Screenshot structure and visual state | `see`, `see --ui`, crop/region, `see more` | Saved read and optional structured inventory | MLX UI read is a costly second opinion; `--ui --json` on MLX is best effort rather than schema enforced (`bin/see:199-213`, `bin/see:553`). |
| Reference fidelity | `see diff`, `--no-read`, `--only` | Text, color, hash, grid, and edge evidence plus optional VLM read | Deterministic pack supports repeated UI rounds; Codex still decides which differences matter (`lib/vis-compare.py:386-453`, `bin/see:257-280`). |
| Enumerable UI claim | `lm ui-verify` | Strict pass/fail/unsure for screenshot or live accessibility tree | Two model reads in the screenshot path; only claims supported by its input may pass (`lib/ui-verify:125-170`). |
| Code review lead | `review --findings`, `lib/findings-gate.py` | Candidate file and line findings | Leads require Codex source inspection and runtime checks. |
| Repeated question over files | `lm fleet` | Per-item result files and index | The default gate checks a successful nonempty envelope; semantic judgment requires `--judge` (`lib/fleet:157-177`). |
| Model selection | `lm probe` and fixtures | Repeatable judgment exercises | Existing scores are task-specific and do not prove universal superiority. |
| Retrieval and repo location | `lm rag`, `lm index` | Local cited chunks or symbol map | Prefer `rg` for exact names; test retrieval quality before promoting the embedding model. |
| Large corpus or external research | `lm gemini` | Project session or one-shot result | External data transfer, auth, and model availability; wrapper currently defaults to `gemini-3.5-flash` (`config.sh:64-71`). |
| Image generation | `imagine` | Local image file and history | Useful for a requested bitmap; Codex's image generation tool may already serve this use. |
| Operations | `warm`, `status`, `models`, `doctor`, `timeline` | Residency and diagnostics | `warm` pins a small model or leases a larger one; `lm status --json` degrades to a down state (`bin/lm:125-151`). |

`/Users/alcatraz627/Code/local-models/docs/CAPABILITIES.md` is the full command catalog; `lm examples` prints pasteable examples. Histories in `logs/` and run records under `outputs/` make past calls inspectable. The fixed sequence is caller selects task and inputs, wrapper selects a model, model returns an envelope, and a task-specific check decides whether the result is usable. `lm fleet` adds a bounded pool and per-item files (`lib/fleet:101-195`).

## Findings worth acting on

1. **The spreadsheet failure is historical and the repair needs a fleet run.** Two 290-item `describe-data` runs produced 580 `ctx_binary` envelope failures, recorded in `logs/fleet-history.jsonl` and under `outputs/fleet/20260912-171019-describe-data/results/`. Commit `2e8b03a` later added spreadsheet extraction to `q` (`bin/q:390-403`). `--ctx` and `--file` are aliases (`bin/q:154-155`), and `fleet` uses `--ctx` (`lib/fleet:134-142`), so the current code appears to route these files through the repair. The model endpoint was unavailable to this run. Exercise one real spreadsheet through `fleet`, including a multi-sheet case, before calling this fixed. The 580 failures say nothing about the sweep model's judgment quality.
2. **“Judge-gated” is too broad a claim.** Without `--judge`, fleet checks only `.ok` and nonempty `.text` (`lib/fleet:157-173`). A fluent false extraction can pass. The 135 `qa` items and 44 `summarize` items in history passed that envelope; their content quality was not established by it. Rename the default status to transport/envelope pass, and require an explicit judge for a quality claim. Carry judge identity and version in the run record.
3. **The Codex skill carries stale task authority.** `/Users/alcatraz627/.codex/skills/local-models/SKILL.md:20` says the owner authorized Gemini analysis of `~/.claude` “in this task.” That line was written for an older task. A future Codex session can misread it as standing export permission. Replace it with a rule tied to current user authorization and file selection; never use model selection as permission.
4. **The `lm examples` headline is false for part of the menu.** `/Users/alcatraz627/Code/local-models/bin/lm:57` claims all commands are local, free, and offline; lines 73, 77-82, and 103-107 include web and Gemini calls. Split examples by local and external execution, with cost and privacy marked on the external lines. The overview at `bin/lm:15` makes the same broad claim.
5. **The UI path has a verification mismatch.** `see --ui --json` defaults to MLX (`bin/see:199-213`), while the MLX path explicitly says it cannot enforce the JSON schema (`bin/see:553`). `lm ui-verify` consumes that inventory and then runs another model judge (`lib/ui-verify:125-170`). An `unsure` result is handled correctly, but a well-formed invented inventory remains a risk. For exact text use `see --ocr`; for native controls prefer accessibility evidence; for visual claims keep Codex's own screenshot inspection in the loop. Record inventory validity and provenance in the verdict.
6. **Current documentation mixes historic and live state.** `/Users/alcatraz627/Code/local-models/docs/STATE.md:1` says last updated July 9 while later September waves are appended. Its entry at line 25 calls `--ui --json` schema constrained without the MLX caveat. Replace the evergreen “single source of truth” claim with a generated or dated state section. Avoid a second hand-maintained status ledger.

## Performance audit

Historical JSONL timings were aggregated by route; they are mixed workloads, not a controlled benchmark. The local Ollama endpoint was unavailable to this sandboxed run: `lm status --json` returned `server:"down"` and `lm models --json` returned the server-down error. That does not prove the host daemon is stopped. No model throughput, power, OOM, or live workflow result was measured today.

| Recorded route | Samples | Median | 90th percentile | Reading |
|---|---:|---:|---:|---|
| `see --ocr`, Apple Vision | 88 | 332 ms | 696 ms | Strong default for exact screen text. |
| `see` on MiniCPM-V 4.6 | 14 | 2.5 s | 17.9 s | Small sample and mixed cold/warm calls. |
| `see --ui` on MLX Qwen3-VL-8B | 7 | 21.7 s | 34.9 s | Use when structure materially changes a decision. |
| Earlier `see --ui` on Gemma 4 26B | 68 | 26.1 s | 37.4 s | Different dates and workloads; no clean A/B speed verdict. |
| `see diff --no-read` | 10 | 18 ms | 21 ms | Cheap feedback for iterative compare rounds. |
| `q`, warm model | 2,077 | 674 ms | 3.0 s | Mix of prompts and residency states. |
| `q`, code model | 43 | 11.6 s | 59.7 s | Too slow to call reflexively for work Codex can do directly. |

The `see diff` history reports 16 ms median extractor time and 8.1 s median total time across 35 runs, consistent with optional model reads dominating the path. The dedicated July measurement in `/Users/alcatraz627/Code/local-models/docs/05-perf-levers-and-usage-audit.md:9-45` compared Q4_K_M and NVFP4 for the code model; Q4_K_M had faster prefill and passed the local judgment probe more cleanly. Keep that choice until a same-prompt rerun shows a gain. The current 52 GB Ollama plus 58 GB Hugging Face footprint totals about 110 GB, under the 150 GB steady budget in `CLAUDE.md`.

The next measurement should use a fixed task set: ten exact OCR images, ten UI state questions, ten visual comparison pairs, one spreadsheet batch, and one judged file batch. Record cold and warm load, wall time, tokens per second where available, peak memory, disk delta, false assertions, and Codex time saved. Compare the whole workflow, including review of local output, against Codex alone. A model earns a default only if it improves the target task with acceptable latency and memory use. Avoid a general “offload percentage” target; the 2026-06 usage estimate in `docs/05` predates current Codex capabilities and mixes tool calls with useful outcomes.

## Model and capability search, 26 September 2026

Primary model catalogs and project releases show options, not winners on this machine.

| Candidate | Why test it | Decision today |
|---|---|---|
| [Qwen3.6 27B Coding](https://ollama.com/library/qwen3.6%3A27b-coding) | An 18 GB dense coding variant may be useful for Pi's short autonomous tool loops; the suite already uses Qwen3.6 35B A3B. | Trial against the existing code probe and a real bounded coding task. Do not replace the default from the model card. |
| [Gemma 4 MLX tags](https://ollama.com/library/gemma4/tags) | MLX variants exist for the current big model. | Revisit only with a workload where cold load is material; July's analogous code-tier test favored Q4_K_M for prefill and output discipline. |
| [MiniCPM-V 4.6](https://github.com/OpenBMB/MiniCPM-V) | Already adopted as the small vision route. The project also offers video support. | Keep. Test video only if there is a concrete frame-analysis workflow; local UI review already has screenshots. |
| [Qwen3 Embedding 0.6B](https://ollama.com/library/qwen3-embedding) | Possible retrieval upgrade from `nomic-embed-text`, with longer context and multilingual/code retrieval claims. | Build a held-out query set with exact citation scoring before switching the RAG index; re-embedding has a real cost. |
| [Qwen3-ASR 0.6B](https://huggingface.co/collections/Qwen/qwen3-asr) | Local speech transcription is a new possible lane. | Park until the owner has recurring audio input; there is no observed workflow gap in this repo yet. |

No evidence found that a newly released model should replace the current small, big, code, vision, or sweep defaults outright. The most valuable new work is correctness at the tool boundary and task-specific measurement. A model popularity chart cannot establish that a screenshot state, code fix, or retrieval answer got better.

## Codex integration proposal

The integration already exists in part: Codex discovers a `local-models` skill, the UI skill family is installed, and the gcc adapter documents shared rules, hooks, IPC, and the i-dream Codex domain (`/Users/alcatraz627/.claude/features/codex-adapter.md:51-94`). The UI router delegates to source skill guidance; `ui-gripe` and `vis-compare` already name `see` as an evidence source. The missing piece is a small decision rule and an exercise of the installed Codex route, not a duplicate orchestration system.

Proposed Codex call policy:

1. For screenshots, Codex views the whole frame. Call `see --ocr` when an exact label, count, or position matters. Call `see diff --no-read --json` during a repeated reference-fidelity loop; inspect its contact sheet and source images before a verdict. Call `see --ui` only when UI structure remains unclear after direct inspection. Use `lm ui-verify` for a narrow enumerable claim, with `unsure` treated as unresolved.
2. For code, Codex reads files and runs the result. Use `review --findings` only as a cheap independent lead, then validate each cited trigger. Use `fleet` when there are many independent files, an explicit question, and a judge that can reject wrong output. Do not route planning, architecture, or multi-file autonomous edits to a local model by default.
3. For large private guidance, prefer exact search, then local RAG if it beats search on a held-out set. Use Gemini only for a question that genuinely exceeds local/Codex context and whose selected material is authorized for external transfer. Remove the stale task-specific authorization from the skill.
4. Keep the Codex skill short. Put command contracts in the repo; generate or link a small usage card to the maintained skill, and run a Codex UI review and batch task as acceptance. Record `lm` invocation, runtime, accepted evidence, rejected evidence, and Codex rework. If calls do not change a decision or save measurable effort, stop the nudge.

Acceptance: on one UI task and one judged batch task, Codex chooses the route at the right time, cites the source image or file, corrects one injected bad local result, and reaches the same or better user-visible answer than Codex alone within an agreed time budget. No global automatic model call until that holds.

## Pi harness plan and value test

Pi is absent here (`command -v pi` returned nothing and `~/.pi` is absent). Current official Pi docs use [`@earendil-works/pi-coding-agent`](https://pi.dev/docs/latest/quickstart), Node 22.19+, and a built-in Google Gemini API-key provider. This machine has Node 26.9.0. [Pi models documentation](https://pi.dev/docs/latest/models) supports Ollama through a local OpenAI-compatible endpoint in `models.json`. [Pi security documentation](https://pi.dev/docs/latest/security) says tools run with the process's OS permissions and project trust is not a sandbox. Do not copy Codex/Claude credentials into Pi or install third-party extensions to get started.

Pi has a plausible purpose only as an **explicitly bounded workbench**: run the local code model or Gemini on a scratch checkout for a contained edit or corpus question, keep a session, inspect the diff, and compare its total cost and usefulness with `lm fleet`, `lm gemini`, and the existing OpenCode local-code launcher. The TUI, model switching, and extensions are features, not benefits until that comparison finds one. Pi's [extension API](https://pi.dev/docs/latest/extensions) could later add a project-specific judge or tool gate; the first trial needs no extension.

After owner review: pin the official package version; install in an isolated prefix or managed location; configure only the existing Ollama endpoint and a separate Gemini credential path; set a global instruction file limiting writes to a scratch workspace; run `pi --version` and one read-only prompt; run a two-file local task and a Gemini corpus task; inspect changes, timing, memory, and external data sent; then decide whether to retain it. Use an OS sandbox or disposable worktree for write trials. A Pi session is worth keeping only if it handles a bounded multi-turn local/Gemini workflow better than the existing `lm` wrappers and OpenCode with no hidden credential or idle-memory cost.

## Other gcc skills and subsystems

The source skills catalog under `/Users/alcatraz627/.claude/skills/` has many more entries than Codex's curated list in `/Users/alcatraz627/.claude/adapters/codex/skills.list:1-27`. The cap is deliberate: the list says Codex shortens skill descriptions after a small context budget. Select by observed task gap.

| Candidate | Proposal | Reason |
|---|---|---|
| `gated-plan` | Adapt for Codex after one real owner decision bundle | Its investigate, alternative, and decision contract fits this kind of gated work; Claude-specific UI and logging need translation. |
| `build-change` | Consider after a non-UI implementation where Codex loses behavior and runtime acceptance | Can complement the UI family; do not import before a concrete failure. |
| `tag` | Add a Codex adapter, not a raw symlink, if the owner wants Codex to file guidance | It writes many protected gcc indexes and asks for confirmation; preserve one canonical store and route writes through a trusted bridge. |
| `atone`, `affirm`, `gcc-proposal`, `pin-for-dream` | Keep existing gcc verbs; inspect task-specific adapters before more imports | `/Users/alcatraz627/.claude/features/codex-adapter.md:64-67` already documents tagged Codex events, queueing, and i-dream ingestion. Add missing UX only after a failed real filing. |
| `i-dream` | Audit Codex event quality and attribution before adding a new feed | A `codex-sessions` domain is already registered; duplicate ingestion would make trends less trustworthy. |
| `catchup` | Keep a Codex-specific resume workflow if needed | The Claude source assumes WAL, Task tools, wake/deadline, and direct IPC commands. This run could read the checkpoint through the adapter, but a raw skill import would promise unavailable mechanics. |

The existing `ui` skill family is the right scope, but its adapters need one real Codex task traced through route, image evidence, optional `lm` call, Codex judgment, and rendered result. Reading the skill files proves discoverability, not successful use. The highest-priority cross-system fix is the stale Gemini permission sentence in the Codex `local-models` skill.

## Decision requested

I recommend approving the first implementation slice: exercise the repaired spreadsheet batch path, narrow the fleet and `lm examples` claims, remove the stale Codex Gemini authorization, and run the fixed workload tests. Then run a measured Codex UI and batch pilot. Decide on model replacements and Pi installation from those results. Pi and any new gcc skill imports remain proposals until you review this report.

## Evidence and limits

Reviewed source, installed skill list, current configuration, historical JSONL aggregates, sample failed batch envelopes, and official model/Pi documentation. `git status --short` was empty before this report. `lm status --json` returned the down envelope in this sandbox; `lm models --json` returned `server down`. No model call, live Pi session, installation, or controlled performance benchmark was run. Historical logs include mixed prompts, dates, and cold/warm states, so timings rank workflow costs but do not establish a model winner.
