# DECISION (2026-06-20): Ollama vs llama.cpp for the local-models runtime

**Verdict: STAY ON OLLAMA. Do not migrate to raw llama.cpp.**
Read this before re-opening the question — the "no" is reasoned, not reflexive.

## TL;DR

Migrating the suite from self-hosted Ollama to raw llama.cpp gains **~nothing** on the
four axes that prompted the question (performance, tuning, control, privacy) and costs a
**foundation-level rewrite** of `q`/`imagine`/`warm`/`lm`. The real performance lever on
this M5 Pro is **MLX** — a different axis than llama.cpp. Keep Ollama as the base; add
llama.cpp GGUF only as a narrow escape hatch.

## The premise that flips it

**Ollama's inference engine *is* llama.cpp** (ggml + Metal kernels). Verified install:
`ollama 0.30.6`, no MLX runner present (matches the prior STATE note "MLX unavailable in
0.30.6"). So right now you are **already running llama.cpp**, just wrapped in a CLI +
registry + lifecycle. "llama.cpp vs Ollama" is therefore mostly "raw llama.cpp vs
llama.cpp-with-ergonomics" → ~zero compute delta.

```
PERFORMANCE on this M5 Pro:
   MLX  >  llama.cpp (Metal)  ≈  Ollama (= llama.cpp under the hood)
   └ the real 30–60% lever      └─────── you are here ───────┘
   Raw llama.cpp = a SIDEWAYS move, not up.
```

## Per-axis grade

| Axis | Gain from raw llama.cpp | Why |
|---|---|---|
| **Performance** | ~none | Ollama already runs llama.cpp's Metal engine. The 30–60% win on M5 is **MLX**, which raw llama.cpp *also* lacks. |
| **Tuning** | marginal | llama.cpp exposes more flags (speculative decoding, GBNF grammars, per-K/V quant, `--n-cpu-moe`) — but mostly features unused here; MoE-A3B gains little from spec-decode. |
| **Control / ecosystem** | ~none | Control is already achieved: self-hosted `ollama serve`, owned wrappers, env (flash-attn, q8 KV, keep_alive). Swapping engines adds maintenance, not control. |
| **Data privacy** | ~none | Ollama collects no telemetry by default; prompts never leave the machine (independently verified zero network traffic post-pull). Only outbound = registry pulls (ollama.com) + update checks. llama.cpp just swaps that for HF pulls. **Ollama is NOT a Meta product** — independent YC-backed co. (Morgan/Chiang). |

## The effort wall

Six `bin/` files are bound to the Ollama API/CLI: `_lib.sh`, `q`, `warm`, `lm`, `lm-serve`,
`imagine`. Migration = rebuild the foundation: model management (llama.cpp has no
registry — manual GGUF paths), multi-model serving (`llama-server` is one model → need
llama-swap), the warm/no-idle 2-tier lifecycle (`keep_alive=-1/0`), and the API shape
(`/api/chat` → OpenAI `/v1`). High effort, marginal-to-nil gains → a bad efficacy trade.

## Recommendation

1. **Performance itch → pursue MLX, not llama.cpp.** Investigate enabling Ollama's MLX
   backend on a newer build, or add `mlx_lm.server` for hot models. (The image side is
   already MLX via mflux.)
2. **llama.cpp = a targeted `bin/` escape hatch**, not a replacement — for KV-cache
   consistency in long agent loops (the MLX KV-branch bug flagged for Qwen3-Coder-Next) and
   GBNF grammar-constrained structured output.

## Corroboration

The repo's own runner research already reached this conclusion:
`.claude/output/20260612-lm-research/coding-models.md` §4 ("stay on Ollama + MLX as the
integration point; keep llama.cpp GGUF as the escape hatch").

## Sources
- Ollama ownership: crunchbase.com/organization/ollama (independent, YC-backed)
- Ollama privacy/telemetry: no default telemetry, prompts local (qwe.edu.pl ollama privacy guide)
- MLX vs llama.cpp on Apple Silicon / why Ollama adopted MLX: yage.ai/share/mlx-apple-silicon-en-20260331.html
