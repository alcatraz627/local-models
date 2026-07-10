# MLX on Ollama — measured verdict (2026-07-07)

**TL;DR: MLX is now native in Ollama 0.30.10 — no parallel runtime to build. It loads the
model 3.2× faster and decodes ~7% faster, but prefills 28% slower, and the NVFP4 quant
regressed judgment terseness. `CODE_MODEL` stays on Q4_K_M.**

Machine: M5 Pro, 64 GB unified memory. Model under test: `qwen3.6:35b-a3b` (35B MoE, ~3B
active) as Q4_K_M GGUF (24 GB, llama.cpp/Metal) vs NVFP4 safetensors (21 GB, MLX runner).

## How MLX actually engages (the discovery)

- **It is format-routed, not a toggle.** Ollama ≥0.19 ships an in-process MLX runner;
  safetensors-format library tags (`-nvfp4`, `-mxfp8`, `-mlx-bf16`) route to it, GGUF blobs
  always go to the `llama-server` subprocess. Source: `llm/server.go` ("All GGML models are
  served via the upstream llama-server subprocess") + our server log.
- **`OLLAMA_USE_MLX` never existed** — the old `bin/lm-serve` human NOTE was right to call
  it cargo-cult. There is no env var today either.
- **Proof of engagement** comes from the server log, never the tag name:
  `starting mlx runner subprocess model=qwen3.6:35b-a3b-nvfp4` · `MLX engine initialized
  (0.31.2) device=gpu`.

## The numbers

Benchmark: cold-load run, then two warm runs (1,254-token prompt, 400-token generation,
temperature 0). Prefill measured on the first warm run only — repeating an identical prompt
hits Ollama's KV cache and inflates prefill ~30×.

| metric | Q4_K_M · llama.cpp/Metal | NVFP4 · MLX | delta |
|---|---|---|---|
| cold load | 15.4 s | 4.9 s | **3.2× faster** |
| cold call, end-to-end (short) | 15.8 s | 12.7 s | ~20% faster |
| prefill (1,254 tok) | 1,291 tok/s | 931 tok/s | **28% slower** |
| decode | 64–68 tok/s | ~70 tok/s | +5–9% |
| disk | 24 GB | 21 GB | −3 GB |

The blog's headline (~2× decode, 58→112 tok/s) did not reproduce here — this machine's
llama.cpp/Metal baseline already decodes at 64–68 tok/s. MLX's first request after load also
pays a visible warmup (shader JIT), folded into the cold numbers above.

## The judgment gate (why speed didn't win)

Re-ran the 9-item probe suite on the NVFP4 variant
(`probe/runs/qwen3.6_35b-a3b-nvfp4-20260707-131716.md`) against the Q4_K_M baseline run:

- **7 of 9 items: identical flags** — abstention (both), ask-vs-assume, 5/5 command
  consistency, multi-turn constraint, multifile edit, scope-trap all hold.
- **2 of 9 items: terseness regression.** On `tool-decision`, Q4_K_M answered in 3 clean
  sentences; NVFP4 reached the same answer through ~35 lines of leaked deliberation
  ("Wait… Actually…"), tripping pass AND fail markers. On `invariant-aware-edit`, NVFP4
  produced a ~180-line second-guessing loop around a correct conclusion.
- **Lesson: re-quantized weights need re-gating.** Same model, same conclusions, different
  *behavior*. A tok/s benchmark alone would have shipped the regression.

## Decision

**Keep `CODE_MODEL = qwen3.6:35b-a3b` (Q4_K_M).** The workloads that matter (fleet runs,
reviews) are prefill-heavy and lease-amortized — cold-load speed barely counts there, and
prefill is where MLX loses. The judgment regression is the tie-breaker. The 21 GB NVFP4
variant was reclaimed; one command re-pulls it if the calculus changes:

```
ollama pull qwen3.6:35b-a3b-nvfp4
```

## Unmeasured follow-ups

- **MTP tags** (`-mtp-q4_K_M` etc.) + `OLLAMA_MLX_MTP_*` draft-token vars — multi-token
  prediction as speculative decoding; could stack on either backend.
- **MXFP8** (38 GB, MLX) — the 8-bit variant might not carry NVFP4's behavior regression,
  at the cost of RAM headroom for the two-model fleet.
- Re-test on future Ollama releases: the MLX runner is in preview and prefill is its known
  weak edge.

---

*Sources: `docs/05-perf-levers-and-usage-audit.md` §1 (verdict) · benchmark script
`scratchpad/baseline-qwen36.sh` · server log `logs/ollama-serve.err.log` · probe runs in
`probe/runs/`. Ollama MLX announcement: ollama.com/blog/mlx.*
