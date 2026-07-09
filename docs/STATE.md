# local-models — STATE (agent handoff / index)

Single source of truth for where this project is. Read this first. Last updated 2026-07-09.

**What it is:** a local-model toolkit on an Apple-Silicon Mac (M5 Pro, 64 GB), running alongside
cloud Claude. Hard rule: **no idle performance penalty** — nothing heavy resident unless invoked.
**The full command menu with examples: `docs/CAPABILITIES.md`.**

## Entrypoint

`lm` (on PATH) is the front door — `lm` for the overview, `lm status` for server/warm/models.
All commands are also directly on PATH (exec-wrappers in `~/.local/bin/` → `bin/`).

| Command | What | Help |
|---|---|---|
| `q "..."` | quick local LLM — answers, macOS commands (`q cmd`), titles; `--json`/`--format SCHEMA` (constrained decoding → `.data`), `--glow`; `q history`/`show N` | `q -h` |
| `imagine "..."` | local image gen (Flux/Qwen on GPU); `--enhance --from --style --neg --seed`; `history`/`show`/`critique` | `imagine -h` |
| `see <img> [q]` | local vision — structural read or grounded answer; **good-but-verify text**; `--ui` = sectioned UI inventory (elements/hierarchy/icons/patterns, big-tier routed, lease-aware) · `--ui --json` = schema-constrained `.data` · `--ocr` = EXACT text via Apple Vision (no model, ~300ms) · `--menubar` = capture+read the live top strip · `--crop WxH+X+Y`/`--region top…center` = crop-then-read (small crops read near-perfectly) · `see more "q"` = drill into the last image; every read lands `outputs/see/<ts>-…/` (source copy + read.md + meta.json; `see open N` · `see note "…"`) | `see -h` |
| `lm ui-verify <img> "claim"…` | the $0 UI verification gate — enumerable claims judged strictly (pass/fail/unsure; unsure never passes; exit 0 only when all pass) against either a `see --ui --json` inventory (screenshots) or `--app <Name>` = the LIVE accessibility tree via `ax` (native apps, exact); `--region/--crop` for focused reads, `--json` for agents | `lm ui-verify -h` |
| `review <pr#\|file\|dir>` | local code review — PR/files/folders/stdin; `--full` (whole files via API, no checkout), `--findings` (schema-constrained objects), `--glow` | `review -h` |
| `lm probe <model>` | judgment eval — the gate that decides if a model earns a tier | `lm probe` |
| `lm fleet <intent> <files…>` | batch fan-out: N files × one intent, concurrency-capped, Judge-gated, run record | `lm fleet -h` |
| `lm index [find X]` | repo symbol map — "where is X" with live staleness | `lm index -h` |
| `lm opencode [args]` | opencode on the local code tier — auto lease/release around the session | — |
| `lm gemini "..."` | the gemini lane (pinned gemini-3.5-flash, wrapper-only, read-only posture); `ingest`/`ask` per-project sessions (UUID create/resume); structured `gemini_unavailable` fallback. **VERIFIED end-to-end 2026-07-07** — auth = API key in `~/.gemini/.env` (600, wrapper-loaded; settings selectedType=gemini-api-key). Note: plan-mode gemini can READ the workspace it runs in — don't point it at dirs holding secrets | `lm gemini -h` |
| `warm on\|off [tier\|model] [ttl]` | companion pin (forever) or **bounded lease** for big tiers; `warm off all` sweeps | `warm -h` |
| `lm status` / `models` / `doctor` / `timeline` | server + resident + on-disk · tiers · smoke-check · merged history (q/imagine/see/fleet) | `lm` |

## Architecture

- **Server:** self-hosted `ollama serve` via LaunchAgent `com.alcatraz.local-models-ollama`
  (`bin/lm-serve`). Policy baked in: `MAX_LOADED_MODELS=2`, `KEEP_ALIVE=0`, flash-attn + q8 KV.
  Port 127.0.0.1:11434. **MLX is format-routed inside Ollama** (safetensors tags → MLX runner,
  GGUF → llama-server); measured verdict in `docs/05` §1 — Q4_K_M/llama.cpp kept for the code tier.
- **Two-tier model lifecycle:** one small **warm** companion (`gemma4-e4b-warm`, ~5.6 GB,
  `warm on` = forever-pin) + on-demand big models. **Leases** (`warm on code [ttl]`) pin a big
  model with a bounded TTL that self-heals — used by `lm fleet` and `lm opencode` automatically.
  Scheduled warmth: `warm-morning` (weekdays 09:30) + `warm-evening-off` (daily 19:00 `off all`,
  the shutdown backstop) via gcc-schedule + calendar companions.
- **Tiers (config.sh):** small=`gemma4-e4b-warm` · big=`gemma4:26b` · code=`qwen3.6:35b-a3b`
  (probe-gated 9/9) · vision=`minicpm-v`. MoE-first on this 307 GB/s machine.
- **Intents are data:** `intents/<name>.toml` (ask/cmd/title/commit/summarize/explain-code/
  describe-data/qa/review/complete) — adding a verb is dropping a file.
- **Histories are the API:** `logs/q-history.jsonl` (successes AND failures), `logs/see-history.jsonl`,
  `logs/fleet-history.jsonl`, `outputs/imagine-history.jsonl` — merged by `lm timeline`, mined
  weekly by `scripts/self-audit.sh` (gcc-schedule `lm-self-audit`, Sun 11:00 → digest + proposal
  on recurring failures). Fleet runs leave full records in `outputs/fleet/<ts>-<intent>/`.
- **OpenCode:** `~/.config/opencode/opencode.jsonc` has the `ollama` provider (all local chat
  models, qwen3.6 default). Use `lm opencode` so the lease is handled.
- **Image models** live in the HF cache; `imagine` = mflux (project `.venv`).

## Key files

- `bin/` — `lm q imagine warm see review probe lm-serve` · `_lib.sh` (colors/help/jsonl-history/
  residency/`resolve_tier`) · `config.sh` (tier vars)
- `lib/` — orchestration internals, NOT on PATH: `fleet` (fan-out runner) · `repo-index` ·
  `gemini` (the gemini lane) · `ui-verify` (the UI claim gate)
- `intents/` — the registry + schemas: `review-findings` · `ui-inventory` · `ui-verify`
- `outputs/see/` — the vision artifact store (one folder per read: source copy as read,
  read.md, meta.json, notes.md; newest 150 kept; `see open N`)
- `scripts/self-audit.sh` — the weekly feedback sink
- **`scripts/verify.sh` — the one-command smoke battery (~30s): run after ANY change and at
  session start after a handoff.** 23 checks: syntax, doctor, q envelope+format, fleet+lease,
  index, gemini lane (skips cleanly when unavailable), histories/timeline, sink, gcc hooks
  (pipe-tests), schedules. Its header lists what it deliberately does NOT cover.
- `probe/` — `items.toml` (9-item judgment suite) · `runs/` (verdicts) ·
  `fixtures/unfinished-v1/` (the finish-a-codebase exercise: fixture + conduct.sh + RESULTS.md —
  qwen3.6 completed it 16/16 under a pytest Judge, 2026-07-07)
- `docs/CAPABILITIES.md` — **the exhaustive food menu** (all abilities, grouped, with examples)
- `docs/05-perf-levers-and-usage-audit.md` §1 — **the measured MLX verdict (2026-07-07)**
- `docs/07-implementation.md` — the phased plan (Phase 1 largely built; see PENDING)
- `docs/09-local-fleet.md` — fleet design from 269 real sub-agent dispatches
- `docs/03-tool-orchestration-decision.md` — local models do NOT drive their own tools
- `docs/04` — stay on Ollama · `docs/NEXT-SESSION.md` — last session's agenda state
- Research archives: `.claude/output/20260616-model-tiers/` · `20260619-*` (landscape, judgment
  benchmarks, re-rank) · `20260620-*` (perf levers, usage audit, efficacy architecture) ·
  `20260707-1334-mlx-report/` (the MLX verdict, styled HTML)
- LaunchAgents: `com.alcatraz.local-models-ollama` · `com.alcatraz.warm-morning` ·
  `com.alcatraz.warm-evening-off` · `com.alcatraz.lm-self-audit`

## DONE (chronological, most recent first)

- **2026-07-10 (session local-next-a4, later):** **capability wave A+C** from the augmentation
  research (throughput facets dropped by user call — capability-per-workflow only):
  `see --ocr` (Apple Vision exact text via mac-ocr, composes with crop); `lm ui-verify --app`
  (LIVE accessibility-tree evidence lane via `ax` v0.3.0 — the UI-reading trio is now AX/exact ·
  --ui/structured · --ocr/verbatim); `lm gemini ingest-repo` (repomix-packed, artifact-ignoring);
  Context7 MCP added user-scope. Bug archaeology: the rejected @-token report reproduced on the
  first real pack — TRUE mechanism is plan-mode gemini invoking its read tool on paths inside
  provided content; fixed (no-tools directive + error-strip + digest trim), atoned the
  synthetic-only-repro dismissal, corrected proposal filed. New tools on the box: mac-ocr,
  ax, repomix. User doctrine recorded: images are ephemeral — parse-now over recall.
- **2026-07-10 (session local-next-a4):** **RAG swim test** — built a full local RAG lane
  (nomic-embed-text + sqlite-vec + q-grounded answers, conductor-drives-retrieval per docs/03),
  ingested 88 gcc doc files (865 chunks, 17s, $0), and ran a 13-question grader-authored eval:
  12/13 correct, 0 fabrications, 2/2 negative probes refused; the one miss root-caused to
  heading-dominated chunk embeddings (fact under an unrelated heading). Kept as ARCHIVAL only.
  Also: env-access convention recorded (config.sh = single definition point).
- **2026-07-09 (session local-next-a4):** **see artifact store** (every read → one
  discoverable folder; fixes the --menubar dead-path defect) + **crop-then-read**
  (`--crop`/`--region`, sips order pinned) + **`see more`/`open`/`note`** drill-down verbs;
  **`lm ui-verify`** — the $0 UI claim gate (strict pass/fail/unsure judge over the --ui
  inventory, live-verified on ground truth); **gemini session self-heal** (vanished chat
  store no longer kills ask/ingest; reset surfaced, never silent) — the @-token report
  (prop-…-63) did NOT reproduce on 0.43.0, closed with evidence; gcc side: `/ui-gripe`
  confusion-forensics skill + designer-reviewer/web-design see-wiring committed;
  `local-models-next` schedule retired; verify.sh now 28 checks.
- **2026-07-07 (session local-agent-9c):** MLX measured + decided (format-routed; Q4_K_M kept;
  NVFP4 judgment-terseness regression caught by the probe — re-quantized weights need re-gating);
  **`lm fleet`** built + exercised (envelope+judge gate, salvage-first, warm-routed lease);
  **finish-a-codebase exercise 16/16** (probe/fixtures/unfinished-v1, evidence+delta retries);
  **`q --format`** constrained decoding + **`review --findings`**; **`--glow`** on q/see/review;
  **warm leases** (`warm on <tier> [ttl]`, `off all`) + **`lm opencode`** wrapper + scheduled
  warmth; **feedback sink** (failures logged, see/fleet histories, unified timeline, weekly
  self-audit); **`lm index`** symbol map; OpenCode wired to local models.
- **2026-07-05:** `see` (MiniCPM-V default after ground-truth bake-off) · `review`/`--full`/
  `--repo`/`review-pr` · `probe` harness + `lm probe` · history QoL (negative indexing, hints).
  **Task #8 gate GREEN:** qwen3.6 9/9 beat qwen3-coder-next 7/9 (51 GB reclaimed) → orchestration
  spine justified.
- **2026-06:** q/imagine/lm core, _lib.sh consolidation, programmatic API v1 (q-spec §API),
  intents-as-data registry, server+warm policy, model-tier research + decisions (docs/03/04/05),
  fleet design (docs/09), implementation plan (docs/07).

## PENDING

- **Fleet at real volume** (parked, actively noted) — first genuine Claude-called sweep over real
  work; measures the cloud-dispatch offset. The runner is ready.
- **Governor policy table** — pair with the gcc **model-tier harness** task (user notes captured
  2026-07-07: Opus daily driver, Fable rare, sub-agents ≤ opus, local + gemini-flash integration,
  hook nudge, pairing tools — see the gcc proposals backlog).
- **Local RAG / embedder** — TESTED AND ARCHIVED 2026-07-10 (not adopted, user call: test-only).
  The swim test scored 12/13 with zero fabrications over the gcc doc corpus; report:
  `.claude/output/20260710-rag-swim-test/report.md`. Scaffolding kept as an archival asset:
  `lib/rag` + `lib/rag.py` (dispatchable via `lm rag`, unadvertised in the menu), embedder
  `nomic-embed-text` on disk, index rebuildable in ~20s. Revisit only on a real need.
- **`procedures/*.toml` + `lm run`** — gated until a 2nd real multi-step recipe exists.
- **MTP speculative decode** — unmeasured (`-mtp-*` tags + `OLLAMA_MLX_MTP_*`).
- **`review-pr` worktree variant** · **`--web` for q** (needs search-backend decision) ·
  **imagegen §8 upgrades** (registry adds, `--good`, upscale) · **dev-ControlNet** (gated FLUX.1-dev).

## Key lessons (load-bearing)

- For small local models, **the prompt is a bigger quality lever than the model**.
- `think:false` must be the **API flag** — prompt-level "no thinking" is ignored.
- **Re-quantized weights need re-gating** — NVFP4 kept conclusions, lost terseness; the probe
  caught what tok/s couldn't. Trust = a passing gate, never a spec sheet.
- **MLX in Ollama is format-routed, not a toggle** — verify engagement from the server log line,
  never the tag name. Benchmark prefill with fresh prompts (KV-cache reuse inflates ~30×).
- **Leases, not pins, for big models** — bounded TTLs self-heal; `keep_alive` is last-writer-wins.
- **Worker retry feedback must ship evidence + a character-precise delta** — restating the spec
  converges never; the delta converged in one round (unfinished-v1 RESULTS.md).
- **Conductor pipelines are bash, never inline zsh** — zsh `echo` expands `\n` inside JSON envelopes.
- A tool isn't delivered until it's **on PATH and invoked as a bare command**.
