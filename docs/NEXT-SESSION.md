# NEXT SESSION — local-agent work (agenda)

Resume point for the local-models work, paused 2026-07-05. A gcc-schedule reminder
(`local-agent-resume`) fires **Thu 2026-07-09 09:33** pointing here.

## How to start

```bash
cd ~/Code/local-models
claude          # then run: /catchup   (finds the 2026-07-05 checkpoint automatically)
```
Or just read this file + `docs/09-local-fleet.md` (the design) + `docs/07-implementation.md` (the plan).

## State at pause (so you don't re-derive it)

- **Shipped + committed** (branch `feat/intents-as-data`, HEAD `7331834`, NOT pushed): `see` (vision,
  MiniCPM-V default), `review` + `review --full`/`--repo` + `review-pr`, `probe` + `lm probe`, history QoL.
- **Decided:** `CODE_MODEL=qwen3.6` (won the Task #8 gate 9/9), `VISION_MODEL=minicpm-v`, local models
  don't drive tools (`docs/03`), conversational large-PR review → use Claude (won't build).
- **Task #8 gate = GREEN** → the orchestration spine (`docs/07` Phase 1) is justified to build.

## The work, in priority order

### 1. #5 — MLX perf measurement (small, gated on finding a path)
- Baseline `qwen3.6` tok/s on Ollama (read `eval_count`/`eval_duration` from `/api/generate`).
- Get a REAL MLX path — `OLLAMA_USE_MLX` is inert on 0.30.6 (human NOTE in `bin/lm-serve`, do NOT re-add);
  need newer Ollama or `mlx_lm.server` / `mlx-vlm`. Measure before/after; decide if a parallel MLX
  runtime earns its keep.

### 2. #9 — the fan-out fleet (the big lever; `docs/09`)
- Build the batch fan-out runner (`bin/procedure` / `lm fleet`): a rubric + N items → concurrency-capped
  local-model tasks (2–3 moderate models on 64 GB) → a Judge gate → structured results.
- It turns Claude's cloud sub-agent fan-outs (269 in 14 days, mostly audit/reconcile/verify) into free,
  always-available local ones. Primarily Claude-called; direct for quick tasks.

### 3. NEW — local-agent work (bigger, agentic)
- **"Finishing an unfinished codebase":** a Claude-conducted Procedure with local workers + a Judge that
  completes a partial codebase across files. This is `docs/07` Phase 1 made real (Procedure runner +
  Judge + the winning local coder). Start scoped (one module), gate each step.
- The `docs/09` fleet use-cases at volume: audit / reconcile / homework-check across many files.

## Optional polish (pick up if touching the area)
- `review --json` structured findings (for Claude to consume the review).
- `review-pr` worktree variant when the model needs surrounding (unchanged) context, not just the diff.
- Push `feat/intents-as-data` when ready (never to main without approval).

## Pointers
- `docs/09-local-fleet.md` — the fleet design (use-cases, harness, ratio).
- `docs/07-implementation.md` — the phased orchestration plan (Phase 1 is now unblocked).
- `docs/03-tool-orchestration-decision.md` — why local models don't drive their own tools.
- `_20260705-local-models.claude.md` — the full checkpoint (or `/catchup`).
