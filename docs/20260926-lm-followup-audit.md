# LM follow-up: behavior audit, integration, and trial gates

This report records the audit before implementation. The owner later authorized the CLI ergonomics, model trials, and Codex integration. Current outcomes are in [the implementation and trial report](20260926-lm-implementation-trials.md).

## Recommendations before ergonomic work

1. Make `lm help <job>` show the shortest working path for a human task: describe a table, answer from a document, inspect a screenshot, compare two images, or sweep files. Keep `lm examples` as the single complete showcase. Measure whether a new user gets a usable first result without a retry before adding command aliases.
2. Add an input preflight to `q` that reports extracted format, row/sheet selection, characters, estimated tokens, and the active context limit. The immediate table guard below prevents false success; a preflight would explain what to narrow before spending a model call. Do not quietly chunk tables because row totals and extrema would then change meaning.
3. Make `fleet` report separate envelope, content judge, and sampled human verdicts. Preserve judge command and version in the run record, plus the sampled source rows. The default envelope pass is a transport result, never a quality result. A judge need not be costly: exact row count or source citation containment can reject many false claims.
4. Offer a task-level `describe-data` result with deterministic CSV/XLSX profiling for row count, null count, numeric extrema, and sheet names, followed by optional model prose. This is the largest correctness gain. The tiny model got a minimum wrong on three rows today. Make exact numbers come from a parser rather than prompt wording.
5. Add `lm bench <fixture-set>` only after accepting a fixed workload. Track cold/warm wall time, peak memory, output correctness, and disk delta. Historical mixed-workload latency alone cannot justify replacing models.

These were recommendations at audit time. See the implementation report for what was exercised and what remains a trial.

## Behavior correctness audit

I exercised the installed small model through `q`, the current XLSX converter, both `fleet` gate modes, and one actual screenshot gate. A passing envelope only means a response was produced. The tests were chosen from the advertised jobs in `intents/*.toml` and `docs/CAPABILITIES.md`.

| Intent or path | User job and adversarial input | Observed result | Action |
|---|---|---|---|
| `ask`, `cmd`, `title` | Ask a direct question, request one command for port 3001, and title a short exchange | Direct answer, valid `lsof -i :3001`, four-word title | No observed failure in this small sample. Commands still need caller judgment before execution. |
| `commit` | Request a commit message with no diff | Before: fabricated an infinite-loop fix. After: `ctx_required`, exit 2 | `intents/commit.toml` now requires context. Piped diff still produced a relevant message in the initial battery. |
| `qa` | Ask for a value absent from a provided note, then ask for one present | Abstained on absence, answered present value | Retain source checking for consequential answers. |
| `summarize` | Short release note | Kept the key change | No observed failure; long documents can be truncated, with the truncation marker now visible to the model in every mode. |
| `explain-code` | A snippet containing `curl | sh` and destructive removal | Flagged both risky operations | No observed failure in this sample. |
| `review` | Source with a denominator that can be zero | Identified the zero-division at the supplied line | Lead only; check every finding in source. |
| `complete` | Small function stub with an explicit behavior contract | Filled the stub | No claim about multi-file quality. |
| `code-dispatch` | Ask for code with no judge | Before: produced code. After: `judge_required`, exit 2 | Requires an explicit `=== JUDGE ===` section and named source in the prompt. The orchestrator still owns running that judge. |
| `diy-plan` and `--diy` | Ask for the installed Ollama version | Before: selected unrelated `/usr/bin/What`, swallowed probe failure. After: traced `ollama --version` and answered from its output | Lowercased stopword matching and propagated probe exit status. The planner can still choose an odd intent; keep its trace visible. |
| `describe-data` | Three-row XLSX with one missing price, a price outlier, and quantities 2, 4, 1 | Extraction succeeded. First answer falsely called 2 the minimum; revised prompt avoided that in one retest | `q` rejects a 3,000-row table that exceeds its 16,000-character context with `ctx_truncated`, exit 12. Exact numeric claims remain untrusted until deterministic profiling is built. |
| `fleet` | One `summarize` item without and with `--judge` | Index reported `gate_level=envelope, judge=not_run`, then `gate_level=judge, judge=pass` | Docs, help, examples, and smoke label now state the distinction. |
| `ui-verify` | Blue play image, one true and one contradicted claim | True claim passed; false red-pause claim exited 1 | Parsed inventory now has a structural check. MLX JSON remains best effort and visual judgment still needs the image. |

The current `q` spreadsheet converter supports `.xlsx`. `zconvert` advertises CSV, TSV, XLSX, and JSON, so `q` now rejects `.xls` and `.xlsm` with a specific export suggestion instead of pretending they work. A multi-sheet workbook still defaults to the first sheet; the proposed preflight should expose that selection.

## What changed in this slice

- `bin/q`, `intents/commit.toml`, `intents/code-dispatch.toml`, `intents/describe-data.toml`: require real input for commit/code dispatch, fail large-table description before the model call, surface truncation to JSON-mode prompts, propagate failed DIY probes, correct XLS support, and tighten numeric wording.
- `lib/fleet`, `bin/lm`, `scripts/verify.sh`, `docs/CAPABILITIES.md`, `docs/STATE.md`: distinguish envelope checks from caller content judges, correct offline/connected examples, and date the handoff doc. `lib/ui-verify` checks the inventory's basic shape and stops calling the MLX output schema-constrained ground truth.
- Claude source skills `ui`, `ui-gripe`, and `vis-compare`, plus Codex `ui-gripe` and `vis-compare` adapters: resolve images already visible in conversation before asking for paths or dispatching. Claude's `context: fork` was removed from the two image-dependent skills. A pathless attached image can be judged natively with an explicit missing-machine-pack limit; a missing image produces a concrete request rather than an empty run. No live conversation-image dispatch was available to reproduce the exact prior failure.
- Claude `model-tier-routing` and `local-models` guidance, plus the Codex `local-models` adapter: local models and Gemini are generally authorized. Gemini is favored for broad, low-judgment, context-heavy sweeps with a scoped prompt, explicit output contract, and targeted source checks. Main-agent judgment and final claims stay with Claude/Codex. A direct sub-agent is preferable where checking Gemini would repeat most of the work. The `pyramid-sweep` record is a caution: its warm local classifier had κ=0.35 on a stratified sample, despite clean planted controls.

## Speech, retrieval, and Pi 4GB: efficacy gates

The combined Ollama and Hugging Face caches are about 110 GB today (52 GB plus 58 GB). The repository's steady target is under 150 GB and hard stop is 200 GB (`CLAUDE.md:15-31`). There is room for bounded candidates, but not an unlimited model collection. Before pulling, record expected download and dependency cache size, run a small trial, and keep only a model that wins a job. Do not equate model-card benchmark claims with local efficacy.

| Candidate | Trial job | Efficacy threshold | Decision |
|---|---|---|---|
| [whisper.cpp tiny/base](https://github.com/ggml-org/whisper.cpp/blob/master/README.md) on Pi 4 | Short offline voice commands when Mac unavailable | At least 90% intent success on 30 owner-spoken commands across quiet/noisy/accent cases, with under 5 s perceived delay and no service interference | Plausible small offline command lane. Upstream reports tiny at 75 MiB disk and ~273 MB memory; older Pi 4 demos show feasibility, not current latency on this device. |
| [Qwen3-ASR 0.6B](https://huggingface.co/Qwen/Qwen3-ASR-0.6B) on Mac | Transcribe the owner's 20 real clips, including names, code terms, and noise | Lower word error rate than the existing available path, with fewer damaging proper-noun errors and useful latency | Candidate only. Official examples target CUDA/vLLM; Apple Silicon setup and memory must be measured before adoption. Do not start on Pi. |
| [SmolVLM2 256M](https://huggingface.co/HuggingFaceTB/SmolVLM2-256M-Video-Instruct) on Pi | Ten actual Pi camera questions: object present, simple state, OCR-like labels | At least 8/10 correct with abstention on ambiguous frames and latency acceptable to the camera flow | Experimental. Small enough to test in principle, but no Pi 4 quality/latency proof found. Likely better to route image work to the Mac. |
| [Qwen3 Embedding 0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) on Mac | Held-out personal-doc retrieval, compared with current `lm rag`/`rg` | Improve top-5 answer-bearing chunk recall by at least 10 points without a material false-citation rise; measure re-index time and disk | Candidate only. Retrieval quality is an index and query problem as well as a model problem. |

Use two independent measures for speech: transcription accuracy (word error rate plus proper names) and downstream task completion. A technically good transcript that sends the wrong media command fails. For retrieval, score whether the answer-bearing passage is among returned chunks and whether the cited chunk actually supports the answer. For vision, require abstention and count unsupported confident answers as failures. Include latency and peak memory in every trial; a higher benchmark score that blocks Pi media or makes the UI sluggish is a loss.

### Pi as a client of Mac inference

The csync repo documents a persistent mesh peer on port 8790 and Pi assistant on 8791 (`/Users/alcatraz627/Code/Claude/csync/AGENTS.md:5-21`). The assistant's current `/chat` dispatch rejects non-Gemini providers (`assist/main.go:147-155`). Ollama on the Mac is loopback-bound, so direct Pi access is not currently a service contract. Csync's temporary reverse-SSH target is a different trust model; do not reuse it for always-on inference.

The proposed seamless path is a Mac-side inference service bound to the tailnet, authenticated with csync's mesh token or a scoped derivative, and a `mac-local` provider in the Pi assistant. The Pi sends bounded audio/image payloads with request ID and timeout; the Mac chooses a named `lm` capability and returns model version, evidence, latency, and a structured error. The assistant exposes availability in `/capabilities`, so the phone can choose local/Mac/Gemini without pretending an offline Mac is live. If Mac inference is unavailable, keep the request pending for an explicit fallback choice rather than silently uploading private media to Gemini. Put payload limits, concurrency, media-service isolation, and token redaction in the protocol. Test Tailscale reconnect, Mac sleep, duplicate requests, and Pi undervoltage before calling it seamless. The Pi's most recent handback reported throttling; live state needs rechecking before a performance trial.

A csync Codex peer was contacted by IPC for current Pi hardware, service, and transport details. No reply was available at report time. This architecture is therefore a proposal, not a deployed or peer-ratified plan.

## Pi agent harness as an experiment

[Pi's quickstart](https://pi.dev/docs/latest/quickstart) supports Node 22.19+, and this Mac has Node 26.9.0. [Pi models](https://pi.dev/docs/latest/models) documents Gemini login and an Ollama-compatible endpoint in `models.json`; [Pi extensions](https://pi.dev/docs/latest/extensions) can add tools but run with the process's OS permissions. Do not start with extensions or a copied Claude config. Pi is worth trying as a deliberately small, inspectable workbench for Gemini/local multi-turn tasks, not as the main coding seat.

After review, pin the official package version and install in an isolated prefix. Give it a scratch repo, a minimal `AGENTS.md`, Gemini through its supported login, and Mac Ollama through the compatible endpoint on the Mac. Do not use Claude or Codex models in Pi. Run three comparisons: a broad corpus sweep against `lm gemini`; a bounded local-model edit against `lm fleet`/OpenCode; and a multi-turn exploratory session where Pi's session branching or extension surface might matter. Preserve prompts, outputs, changed-file lists, wall time, model usage, and user-rated usefulness. Keep Pi only if one workflow is easier to start, inspect, and resume than the current tools without adding an always-on daemon or a second opaque instruction stack. A Pi install is not yet authorized by this review.

## Broader gcc adoption

The prior review was too conservative about imports. The decision should depend on the work Codex can actually do with the skill, not on whether Claude already has it.

| Skill/subsystem | Codex fit | Proposed action |
|---|---|---|
| `arch-qa`, `build-change`, `gated-plan` | Good fit for code-path answers and behavior-preserving plans; source skills have Claude-specific dispatch or record steps | Trial Codex adapters on one real architecture question and one non-UI change. Preserve source behavior contracts, replace unavailable mechanics. |
| `deep-research`, `pyramid-sweep` | Valuable when breadth, evidence, and a survivor gate are genuinely needed | Import a short routing adapter, not automatic parallelism. Demand corpus size, expected survivors, sample gate, and stop budget before use. |
| `gcc-map`, `improve-skill` | Directly useful for the current instruction-load and UI-skill misfire problem | Adapt for Codex and exercise on this UI family. A skill body change may not affect an already-running Claude skill invocation; test a fresh invocation. |
| `tag`, `preference-graduation` | Useful for durable owner guidance, but both write or graduate canonical records | Expose candidate drafting in Codex; let `gcc`/owner-reviewed placement perform writes. Avoid a second Codex memory graph. |
| `atone`, `affirm`, `gcc-proposal`, `pin-for-dream` | Already reachable through tagged `gcc` verbs | Improve discovery/examples, then check receipt and later ingestion. Do not create duplicate stores or direct shell calls. |
| `decision-wizard`, `catchup`, `core-dump`, `callouts`, `probe`, `validate` | Already in the Codex skill list | Exercise them on natural triggers; repair concrete adapter gaps. Their presence alone is not integration proof. |
| `retro-dump`, `doctor`, `summarize-changes` | Useful only with past-session or environment authority | Keep discoverable via `gcc-discover`; adapt when a matching job occurs. Do not import Claude's WAL or session-resume assumptions raw. |

The strongest near-term import is `improve-skill`: this exact UI misfire is a concrete trigger. The next is `build-change` for non-UI work where capability parity matters. `tag` can be valuable once Codex can submit a complete, reviewable placement proposal through the trusted `gcc` door. Wider import should make these jobs easier, not swell every prompt with skill descriptions.

## Verification boundary

Live commands and output are in the handback for this run. The q intent battery covered one or two examples per intent, not a statistical qualification. The data prompt correction has one counterexample retest. No new speech, embedding, Pi vision, or Pi harness model was installed. No live Pi endpoint was called. No conversation-attached screenshot was available to replay the original `ui-gripe on these` failure; the skill changes remove its identified fork/path mismatch and need one fresh-session acceptance run.
