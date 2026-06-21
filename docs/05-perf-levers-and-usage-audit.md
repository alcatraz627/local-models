# Performance levers + 3-day usage audit (2026-06-20)

Reference report. Companion to `04-ollama-vs-llamacpp-decision.md` and the raw audit at
`.claude/output/20260620-claude-usage-audit/audit.md`. Hardware: M5 Pro / 64 GB.

## The lever stack (ROI-ordered)

```
PERFORMANCE on this M5 Pro:
   MLX  >  llama.cpp (Metal)  ≈  Ollama (= llama.cpp under the hood, current)
   └ the lever ──────────────────────────────────┘
```

1. **MLX backend — the big perf lever, but NOT a flag on this Ollama.** MLX is Apple's
   unified-memory-native framework; on M5 it drives the GPU Neural Accelerators (3–4×
   prefill, 30–60% decode). **Ground truth (tested — see the `bin/lm-serve` NOTE):
   `OLLAMA_USE_MLX` is absent from Ollama 0.30.6's config dump, so the flag is inert here.**
   MLX therefore needs a newer Ollama build that actually exposes it, or the `mlx_lm.server`
   path (lever 3) — it is NOT a 5-minute flag on 0.30.6. Don't cargo-cult the env var.
2. **Quant + KV tuning — ~90% done.** 4-bit sweet spot; q8 KV cache (have it) ~doubles
   usable context; keep `num_ctx` no larger than the task needs (KV grows linearly).
3. **Full MLX serving (when Ollama-MLX coverage disappoints):** `mlx_lm.server` (spec-decode
   in mlx-lm 0.21+), `vllm-mlx` (400+ tok/s, Anthropic-API compatible, "works with Claude
   Code"), `mlx-serve`/Rapid-MLX. Cost: suite speaks Ollama `/api/chat`, these speak OpenAI
   `/v1` → needs an adapter in `_lib.sh` or run alongside. Also the path to the Claude-integration goal.
4. **Speculative decoding — skip for A3B.** Draft-model verify gains little when only ~3B
   active; pays off only for DENSE models (Qwen3.6-27B, Gemma 31B).
5. **Exotic — SSD expert-streaming** (`SwiftLM`): run >64 GB MoE by streaming inactive
   experts from SSD. Slow; know it exists.
6. **llama.cpp escape hatch** (not speed): GBNF grammar-constrained output + KV consistency
   in long agent loops. `llama-server` + `llama-swap`, as a `bin/` helper, never a replacement.

## 3-day usage audit → local-fit tiers

```
26 sessions · 12,646 tool calls · ~31M output tokens
Bash 32% + Edit 24% + Read 21%  =  77% of all calls

  WORK BUCKET           SHARE   → LOCAL TIER              STATUS
  ────────────────────────────────────────────────────────────────
  read-only recon        ~22%   → lean→moderate           offload now
  multi-file coding      ~28%   → BEEFY (aspirational)     cloud for now
  config/doc edits       ~15%   → moderate                offload now
  research & synthesis   ~12%   → hybrid (RAG + cloud)     partial
  debugging / planning   ~12%   → cloud (judgment)         stays cloud
  shell composition      ~8%    → lean — q cmd EXISTS      offload now
  git commit msgs        ~3%    → lean — q commit EXISTS   offload now
  ────────────────────────────────────────────────────────────────
  Offloadable today ≈ 45–50%   ·   Must stay cloud ≈ 40%   (±5pp)
```

**Key read:** ~half the tool-call volume is lean/moderate work the local stack can already
do; for shell + commits the tooling already exists (`q cmd`, `q commit`) — the bottleneck is
habit, not capability. The aspirational beefy (multi-file) slice overlaps heavily with the
~40% that should stay cloud anyway. Immediate win = lean+moderate tiers, gated only on MLX
making them fast enough to reach for.

## Week plan (Tasks #22–24)

1. **MLX:** the `OLLAMA_USE_MLX` flag is inert on 0.30.6 (tested) — check whether a newer Ollama exposes a real MLX toggle, else use `mlx_lm.server`; then measure tok/s.
2. Build the `q` habit for shell + commits (optional: a nudge hinter).
3. Wire local embedder + RAG (`simonw/llm` + Qwen3-Embedding-0.6B) to kill the research re-fetch tax.

Beefy probe + MLX-server/Anthropic path = later (Task #8).
