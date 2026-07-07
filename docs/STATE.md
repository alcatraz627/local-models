# local-models — STATE (agent handoff / index)

Single source of truth for where this project is. Read this first. Last updated 2026-07-07.

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
| `see <img> [q]` | local vision — structural read or grounded answer; **good-but-verify text**; `--json`, `--glow`; `see history`/`show N` | `see -h` |
| `review <pr#\|file\|dir>` | local code review — PR/files/folders/stdin; `--full` (whole files via API, no checkout), `--findings` (schema-constrained objects), `--glow` | `review -h` |
| `lm probe <model>` | judgment eval — the gate that decides if a model earns a tier | `lm probe` |
| `lm fleet <intent> <files…>` | batch fan-out: N files × one intent, concurrency-capped, Judge-gated, run record | `lm fleet -h` |
| `lm index [find X]` | repo symbol map — "where is X" with live staleness | `lm index -h` |
| `lm opencode [args]` | opencode on the local code tier — auto lease/release around the session | — |
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
- `lib/` — orchestration internals, NOT on PATH: `fleet` (fan-out runner) · `repo-index`
- `intents/` — the registry + `review-findings.schema.json` (constrained-decode schema)
- `scripts/self-audit.sh` — the weekly feedback sink
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
- **Local RAG / embedder** (deferred, noted) — revisit via simonw/llm ecosystem if q ergonomics stall.
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
