# local-models — STATE (agent handoff / index)

Single source of truth for where this project is. Read this first. Last updated 2026-06-11.

**What it is:** a local-model toolkit on an Apple-Silicon Mac (M5 Pro, 64 GB), running alongside
cloud Claude. Hard rule: **no idle performance penalty** — nothing heavy resident unless invoked.

## Entrypoint

`lm` (on PATH) is the front door — `lm` for the overview, `lm status` for server/warm/models.
All commands are also directly on PATH (exec-wrappers in `~/.local/bin/` → `bin/`).

| Command | What | Help |
|---|---|---|
| `q "..."` | quick local LLM — answers, macOS commands (`q cmd`), titles (`q title`); `q history`/`q show N` | `q -h` |
| `imagine "..."` | local image gen (Flux/Qwen on GPU); `--enhance --from --style --neg --seed --stepwise -m`; `imagine history`/`show`/`critique` | `imagine -h` |
| `see <img> [q]` | local vision — structural read of an image/screenshot (type + layout + text + anomalies), or a grounded answer; **good-but-verify text** (don't trust exact strings/values blindly); `--json`; `-m minicpm-v` (default) or `gemma4:26b` | `see -h` |
| `review <pr#\|file\|dir>` | local code review — PR (`gh pr diff N \| review`), files, folders, or stdin; the `review` intent on the code tier; `--json` | `review -h` |
| `warm on\|off\|status` | Tier W toggle — pin a small model resident (snappy) vs zero-idle | `warm -h` |
| `lm status` | server + resident + on-disk models | `lm` |

## Architecture

- **Server:** self-hosted `ollama serve` via LaunchAgent `com.alcatraz.local-models-ollama`
  (`bin/lm-serve`) — the GUI Ollama.app ignored env, so we own it. Policy baked in:
  `MAX_LOADED_MODELS=2`, `KEEP_ALIVE=0`, flash-attn + q8 KV. Port 127.0.0.1:11434.
- **Two-tier model lifecycle:** one small **warm** model (`gemma4-e4b-warm`, num_ctx 8192, ~5.6 GB)
  for the snappy path; everything big loads on-demand and unloads immediately. Resolves the
  snappy-vs-no-idle tension.
- **`q`** drives lifecycle per-request (`keep_alive`, warm-aware); never starts/stops the server.
- **`imagine`** = mflux (MLX Flux) wrapper. Model registry (`resolve_model`) maps a name → mflux
  binary + variant + default steps. `--enhance` uses gemma4 as a prompt engineer; `imagine critique`
  uses gemma4:26b vision to diagnose a result (the generate→critique→refine loop, all local).
- **Image models** live in the HF cache (`~/.cache/huggingface`), not Ollama. First use downloads.

## Key files

- `bin/` — `lm` `q` `imagine` `warm` `lm-serve` · `_lib.sh` (shared: colors/help/jsonl-history/`ollama_up`/`ollama_resident`) · `config.sh` (WARM_MODEL, IMAGINE_MODEL)
- `modelfiles/gemma4-e4b-warm.Modelfile` · `presets/skybound-isles.{json,png}` (a locked wallpaper)
- `docs/00-plan.md` (plan + build log + V1 line) · `docs/q-spec.md` · `docs/STATE.md` (this)
- `docs/GOALS.md` — **goals + audit per command** (guiding goal points, implementation notes, ranked improvements; 2026-06-12)
- `docs/03-tool-orchestration-decision.md` — **DECISION (2026-06-16, MAGI 5/5):** local model does NOT orchestrate its own tools; deterministic `q --ctx/--file` extraction + Claude-Code-as-orchestrator instead. Read before re-opening "let the model read files itself."
- `.claude/output/20260616-model-tiers/research.md` — **model-tier verdict (2026-06-17):** small=gemma4-e4b (keep), big=gemma4:26b (MoE, on disk), code=qwen3.6:35b-a3b (pulled); **dropped gemma4:31b** (dense → bandwidth-bound, ~8× slower than the 26B MoE for +2-4 pts). MoE wins on this 307GB/s machine.
- `.claude/output/20260612-lm-research/` — 4 research reports (consolidation · claude-integration · coding-models · assets-sessions; 2026-06-12)
- `.claude/output/20260619-open-model-landscape/` — **open-model landscape shortlist by task class (2026-06-19):** coding · general/reasoning · vision/VLM · image/video gen · embeddings/RAG + speech. Live-web, 5-agent fan-out, 64GB-fit vs API-tier flagged. Start at `INDEX.md`
- `.claude/output/20260619-agentic-judgment-benchmarks/` — **benchmarks for agentic judgment (2026-06-19):** reliability (τ²-bench pass^k), ask-vs-assume, abstention/calibration, hallucination, long-horizon. Key finding: **reasoning fine-tuning hurts judgment**; prefer non-thinking instruct variants. Start at `INDEX.md`
- `.claude/output/20260619-local-judgment-rerank/` — **local candidate re-rank by judgment axes (2026-06-19):** judgment data too sparse to pick by leaderboard → probe locally. Top-3: Qwen3-Coder-Next (coding) / Qwen3-Next-80B-Instruct (judgment) / GLM-4.5-Air (measured τ-bench).
- `docs/04-ollama-vs-llamacpp-decision.md` — **DECISION (2026-06-20):** stay on Ollama (its engine IS llama.cpp; real perf lever is MLX). Don't migrate.
- `docs/05-perf-levers-and-usage-audit.md` + `.claude/output/20260620-claude-usage-audit/` — **perf levers (MLX-first) + 3-day usage audit** → ~45-50% of work offloadable to lean/moderate local tiers; multi-file coding (~28%) stays cloud for now.
- `.claude/output/20260620-efficacy-architecture/` — **software levers to raise EFFICACY without bigger hardware (2026-06-20):** scaffold > size (4B recovers ~90% of frontier via context-control); prioritized ladder (system-prompt → AGENTS.md → constrained-decode → verify-loop → repo-map → routing → LoRA). Start at `INDEX.md`
- `docs/07-implementation.md` — **IMPLEMENTATION (2026-06-21): behaviour + product spec, professional-but-lean.** Reuses existing substrate (q --json Bus, q-history.jsonl outcome log, config.sh policy, lm status signal); additive coordination not a rebuild. Design principles, behaviour/UX/churn-resistance specs, phased build with concrete artifacts + done-criteria, and the explicit do-NOT-build line. Build from this.
- `docs/06-local-orchestration-design.md` — **DESIGN (2026-06-20): the disciplined local-model collective** ("army of fools under strict procedures, conducted by Claude"). Units (Worker/Procedure/Conductor/Judge/Index/Governor/Feedback-Sink/Bus), the adaptive Governor (no knob-fiddling), 6 phases, cross-interactions, gcc integration (hooks/i-dream/atone/personas). **PENDING `/magi --mode full` adversarial review** (§9 open decisions) — was blocked by API throttle. Fable = the shut-down Claude Fable 5 (whole-repo structural comprehension → replicate via the Index).
- `docs/research/` — runtime, vision, image-gen, **imagegen-techniques** (consolidated reference),
  **art-direction-brief** (the art-director persona's playbook)
- Personas (global): `~/.claude/personas/` — `art-director` (image gen), `closer`/`platform-builder`/`pragmatist` (strategy triad)
- LaunchAgent: `~/Library/LaunchAgents/com.alcatraz.local-models-ollama.plist`

## DONE

- **q** — built, standardized (cli-help-design help, `history`/`show`, deterministic temp 0,
  history log, on PATH), macOS/BSD smart defaults, `think:false`, intents (ask/cmd/title/commit),
  warm-aware, **stdin piping** (`git diff | q commit`), friendly server-down error (2026-06-12).
- **_lib.sh consolidation** (2026-06-12) — colors/help/history/residency-guard/health-check shared
  across q/imagine/lm; closed the duplicated-guard class that caused the enhance un-pin bug.
- **Tab-title auto-base** (2026-06-12) — UserPromptSubmit hook
  (`~/.claude/scripts/tab-title/hooks/auto-base.sh`) titles sessions from the first prompt via
  `q title`; warm-gated, fire-and-forget, manual base wins.
- **Iteration + asset layer** (2026-06-12) — imagine logs the FULL reproducible config (+
  `parent`/`kind` lineage); `redo/vary/refine N` verbs; `star N` / `prune [-y]` / `gallery`
  (self-contained `outputs/index.html`, dark/light); `q -c [N]` conversation continuation
  (cid chains); `lm doctor` (11-check smoke) + `lm timeline`; `history --json` on both tools.
- **Skeptical-review hardening** (2026-06-12) — 18-finding adversarial review + fix round
  (JSONL-corruption, numbering-drift, resident-match, prune keep-set, config decoupling).
  Report: `.claude/output/20260612-skeptical-review/review.md`.
- **gcc discovery** (2026-06-12) — `~/.claude/features/local-models.md` + CLAUDE.md Tier-2
  pointer: other Claude instances can now find the suite.
- **Programmatic API v1** (2026-06-12) — for better-file-browser's native-messaging host (spec:
  `~/Code/better-file-browser/.claude/output/20260612-2014-lm-q-extension-api/spec.md`):
  `lm status --json` (<150ms), `q --json`/`--stream-json` + `--ctx/-name/-max-ctx/--timeout`,
  structured error codes w/ stable exits (10-13, 130), SIGTERM abort (q execs python), 4
  document intents (summarize/explain-code/describe-data/qa). Warmth is READ-ONLY for
  machine consumers (status reports warm/latency_class/available_models; no programmatic
  warm-up — user decision 2026-06-12). Contract: `docs/q-spec.md` §API.
- **Server + warm** — LaunchAgent, `num_ctx`/q8-KV governance, `warm` toggle, verified no-idle.
- **llm-mini** — watchdog neutralized (`idle_timeout_min=0`) so it can't pkill our server; full
  fold-in deliberately **deferred** (over-engineering; serves a future Claude→local goal).
- **imagine** — mflux wrapper; model registry (schnell/flux2/qwen/dev), model-aware steps/guidance,
  `--enhance`/`--from`/`--style`/`--neg`/`--guidance`/`--stepwise`/`--seed`, `history`/`show`,
  observability (pre/post summary, `--metadata`, auto-open), **`critique`** vision-loop.
- **lm** entrypoint + full help/examples across all commands.
- **Personas** — art-director (TUI-wizard creative-direction) + the strategy triad.
- **Research** — runtime / vision / image-gen sweeps + two consolidated guides.
- **Vision probe PASSED** — gemma4:26b vision gives accurate image critiques (→ built `imagine critique`).
- **Scheduled** — local review **Tue Jun 24, 3 PM IST** (Google Calendar) to prioritize the pending below.

## PENDING

- **`--web` for q** (Task 6) — deferred per MAGI (needs a search-backend decision; no proven pull yet).
- **Imagegen §8 upgrades** (Task 13) — 1 of 5 done (`critique`). Still: add `ideogram4` + `z-image-turbo`
  to the registry (best-text + fast-draft); a `--good` quality alias; a refine/upscale step
  (`mflux-upscale-seedvr2`); a Qwen text helper (auto-quote). **→ the June 24 review decides order.**
- **Proper dev-based ControlNet** — the minecraft-style "you" test washed out on schnell+dev-ControlNet;
  the real fix needs the gated FLUX.1-dev base (license + ~24 GB) + a voxel LoRA + a photo of the user.
- **Structured-local agentic tier (NEW use-case, 2026-06-19)** — a heavy on-demand local coder
  for Claude-Code-like multi-file feature work (the *structured* lane, not one-offs). Candidate:
  **Qwen3-Coder-Next 80B-A3B** (UD-Q4_K_XL, ~38–42 GB) via llama.cpp/GGUF (MLX KV-branch bug in
  agent loops). Gated on the **efficacy bar** — ballpark of the cloud agent, else route to cloud.
  Plugging into Claude systems = deferred follow-up audit. See `docs/GOALS.md` § Work-routing lanes
  + project memory `local_agentic_tier_use_case.md`.
- **Deferred-with-triggers (V2):** llm-mini/MCP fold (Claude calls local), LAN M4-Pro offload.
- **If `lm`/`q` quality or ergonomics stall** — evaluate **`simonw/llm`** as a richer base
  (`brew install llm` + `llm install llm-ollama`, which talks to *this* Ollama). Edge over
  `lm`/`q` is the ecosystem, not core chat (already solved here): templates, SQLite prompt
  logging, `-f github:user/repo` fragments, and **embeddings/RAG** plugins for local semantic
  search. Adopt-the-ecosystem, not gap-fill. (suggested 2026-06-18)

## Key lessons (load-bearing)

- For small local models, **the prompt is a bigger quality lever than the model** (4B + good
  system prompt beat a code model + generic prompt).
- `think:false` must be the **API flag** — prompt-level "no thinking" is ignored.
- The accuracy ceiling for `cmd` is **macOS-vs-Linux**, not size → BSD-aware system prompt.
- A tool isn't delivered until it's **on PATH and invoked as a bare command** (atone S3 this session).
- gemma4 **can't generate images** (it's the prompt-engineer/critic); diffusion does the pixels.
