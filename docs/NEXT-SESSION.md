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

1. **Push `feat/intents-as-data`** — awaiting the human's go (never main).
2. **Fleet at volume** — first real Claude-called fleet run on actual work (an audit
   or reconcile sweep across a real doc/code set); measure the cloud-dispatch offset.
3. **Procedure manifests** (`procedures/*.toml` + `lm run`) — only when a 2nd real
   multi-step recipe exists; the fleet + conduct.sh loop is the seam until then.
4. **MTP speculative decode** — unmeasured: `-mtp-*` tags + `OLLAMA_MLX_MTP_*` vars.
5. **`bin/lm-serve` NOTE** — the OLLAMA_USE_MLX note is now resolved history (docs/05
   has the ground truth); human may want to update or keep it.
6. **docs/STATE.md** — dated 2026-06-11, missing see/review/probe/fleet; due a refresh.

## Pointers

- `docs/05-perf-levers-and-usage-audit.md` §1 — the measured MLX verdict.
- `docs/09-local-fleet.md` — fleet design · `lib/fleet` — the runner.
- `probe/fixtures/unfinished-v1/RESULTS.md` — the codebase-finisher exercise record.
