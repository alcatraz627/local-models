# NEXT SESSION — local-agent work (agenda)

**Status: the 2026-07-05 agenda is DONE (session local-agent-9c, 2026-07-07).** The
gcc-schedule reminder (`local-agent-resume`, Thu 2026-07-09 09:33) points here — if it
fires and you're reading this, the work it was guarding already happened; retire it
(`gcc-schedule rm local-agent-resume`) or repoint it at the follow-ups below.

## What landed 2026-07-07 (branch `feat/intents-as-data`, NOT pushed)

- **#5 MLX** — measured, decided, documented in `docs/05` §1. MLX is native in Ollama
  0.30.10 (format-routed: safetensors tags → MLX runner, GGUF → llama-server; no env
  var, no parallel runtime to build). NVFP4 variant: 3.2× cold load, −28% prefill,
  +5–9% decode, and a judgment-terseness regression caught by the probe →
  **CODE_MODEL stays Q4_K_M**; the 21 GB variant was reclaimed.
- **#9 fleet** — `lm fleet <intent> <files…>`: concurrency-capped fan-out, envelope +
  `--judge` gate, salvage-first results, bounded warmth lease with warm-pin restore.
  Exercised end-to-end (`lib/fleet`).
- **Local-agent exercise** — finish-a-codebase proven: qwen3.6 completed the
  `probe/fixtures/unfinished-v1` package 16/16 under a pytest Judge (2 surgical
  retries). Findings in the fixture's `RESULTS.md`.
- **Polish** — `q --format` (schema-constrained decoding, `.data` in the envelope) +
  `review --findings`; q-spec updated.

## Open items (pick up next)

**Triaged by the user 2026-07-07 (day-2 wave shipped same day):** pushed ✓ · warm leases +
`lm opencode` + scheduled warmth ✓ · feedback sink (all histories + weekly self-audit) ✓ ·
`lm index` ✓ · CAPABILITIES.md + STATE refresh ✓ · lm-serve NOTE resolved ✓ · Thursday
reminder retired ✓ · `--glow` everywhere ✓ · OpenCode wired ✓.

**The live pending list is `docs/STATE.md` § PENDING** (single source; don't duplicate here).
Headliners: fleet-at-real-volume (parked, actively noted) · Governor table + the gcc
**model-tier harness** (user notes in the gcc proposals backlog + this session's Task #18) ·
RAG deferred · procedures/MTP/review-pr-worktree deferred.

## Pointers

- `docs/05-perf-levers-and-usage-audit.md` §1 — the measured MLX verdict.
- `docs/09-local-fleet.md` — fleet design · `lib/fleet` — the runner.
- `probe/fixtures/unfinished-v1/RESULTS.md` — the codebase-finisher exercise record.
