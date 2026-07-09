# Inference-side augmentations for the local-models stack (2026)

Scope: techniques and tools that make the existing local stack faster, more
capable, or more reliable — not new base models. Stack assumed: Apple Silicon
Mac (M5 Pro, 64GB unified memory), Ollama server routing between llama.cpp
(GGUF) and MLX formats, hard zero-idle policy, tiers gemma4-e4b (warm
companion) / gemma4:26b (big) / qwen3.6:35b-a3b (code) / minicpm-v (vision),
plus existing constrained decoding via Ollama JSON schemas, judged batch
fan-out, local embeddings + sqlite-vec, local code review, and vision reads.

Ranked roughly by fit (biggest lever for this stack first).

## 1. MLX-native MTP speculative decoding (MTPLX / DFlash-style tools)

What it is: uses a model's own built-in multi-token-prediction (MTP) heads to
draft several tokens per step, verified in the same MLX compute graph — no
separate draft model, no extra resident weights.

Why it fits: zero-idle friendly (nothing new to keep warm), and it's an
MLX-only win — the same trick on llama.cpp's Metal backend actually goes
*slower* because each draft-verify step is a separate kernel dispatch. Real
numbers: one Qwen3.6 27B-class model went from 10.5 tok/s (llama.cpp) to 18.3
tok/s (MLX + MTP), a 74% gain from software alone. Directly benefits the
qwen3.6:35b-a3b and gemma4:26b tiers if they're served over the MLX path.

Maturity/effort: community tooling, early but working (2026). Requires running
outside Ollama's stock MLX backend (mlx_lm / vllm-mlx / a dedicated MLX
server) since Ollama hasn't exposed MTP flags yet — moderate integration
effort.

Source: https://vinoth12940.github.io/blog/articles/genai-20260519-local-mtp-speculative-decoding/

## 2. MLX-LM continuous batching (mlx_lm.server / vllm-mlx / oMLX)

What it is: batches concurrent requests to the same model dynamically instead
of serializing them one-at-a-time.

Why it fits: this is the single best match for "judged batch fan-out" — every
parallel judge/worker call to the same local model currently queues; with
continuous batching those calls run together. Benchmarks show up to 4.14x
generation throughput at 8x concurrency on an M2 Ultra-class machine.
vllm-mlx specifically also ships MCP tool calling and an OpenAI/Anthropic
compatible surface, so it's a plausible Ollama alternative for
batch-heavy workloads without giving up the existing tool-call contracts.

Maturity/effort: mature as of the mid-2026 mlx-lm release; moderate effort —
either swap the batch-fan-out path to point at mlx_lm.server/vllm-mlx, or wait
for Ollama's MLX backend to pick it up.

Source: https://github.com/waybarrios/vllm-mlx · https://github.com/jundot/omlx

## 3. KV-cache quantization (Q4/Q8) in MLX

What it is: quantizes the attention KV cache itself (not just weights), cutting
its memory footprint 2-4x with near-lossless quality (TurboQuant-class results
show PPL 6.20 vs. 6.19 baseline on a 35B-A3B model).

Why it fits: on 64GB unified memory this is literally the difference between
16K and 32K+ usable context for the 26B/35B tiers, at effectively zero cost —
it's a flag, not new infrastructure (MLX 0.21 ships it natively).

Maturity/effort: mature, trivial to turn on. TurboQuant's more extreme 3-4 bit
variant is newer/less battle-tested — treat that one as experimental.

Source: https://contracollective.com/blog/kv-cache-quantization-q8-vs-q4-m5-max-mlx-2026

## 4. Cross-encoder reranker (BAAI/bge-reranker-v2-m3) for hybrid retrieval

What it is: a small reranking model that re-scores the top-K candidates from a
first-pass BM25 + vector retrieval before they're used.

Why it fits: directly upgrades the existing sqlite-vec archival search from
pure cosine similarity to a real retrieve-then-rerank pipeline. It's a small
model that loads on demand for a search call and unloads after — fits the
zero-idle policy cleanly, and the "retrieve top-1000, rerank top-100" pattern
is well inside interactive latency budgets even on CPU.

Maturity/effort: mature, widely deployed, low integration effort (one more
step in the retrieval pipeline).

Source: https://www.digitalapplied.com/blog/hybrid-search-bm25-vector-reranking-reference-2026

## 5. EmbeddingGemma on the Apple Neural Engine

What it is: a 768-dim embedding model that runs on the ANE via Core ML instead
of the GPU.

Why it fits: this is the concrete win for zero-idle + Apple Silicon —
indexing/archival embedding work stops competing with whatever chat/code model
is currently resident on the GPU, because it runs on hardware that's otherwise
sitting unused. Meaningful if the sqlite-vec archival pipeline ever runs
concurrently with an active chat session.

Maturity/effort: mature (Google model with existing MLX/CoreML ports), low
effort to swap in as the embedding tier.

Source: https://contracollective.com/blog/local-embeddings-apple-silicon-nomic-bge-qwen3-m5-max-2026

## 6. Prefix/prompt caching (llama.cpp host-memory cache, Ollama auto KV reuse)

What it is: reuses already-computed KV state for a repeated prompt prefix
instead of recomputing it — Ollama does this automatically when the model
stays loaded and the prefix is byte-identical; llama.cpp's newer server build
adds host-memory (RAM, not just VRAM) prefix caching so it survives past what
fits on GPU.

Why it fits: the judged batch fan-out pattern typically shares a stable system
prompt/rubric across many calls — this is a pure win with zero new
infrastructure, just a config/discipline point (keep the prefix byte-identical,
keep_alive set so the model doesn't unload between calls).

Maturity/effort: mature, essentially free. The only cost is discipline around
prompt construction (no dynamic timestamps etc. in the shared prefix).

Source: https://github.com/ggml-org/llama.cpp/discussions/20574 · https://docs.ollama.com

## 7. llguidance grammar backend (vs. Ollama's default XGrammar)

What it is: an alternative constrained-decoding backend — computes token masks
on the fly with ~50us/token average and near-zero startup cost, and
benchmarks ahead of XGrammar on some grammar classes; supports full
context-free grammars, not just JSON Schema.

Why it fits: marginal on top of what's already there — Ollama's default
XGrammar is already fast for JSON-schema constrained decoding, which is most
of what "judged batch fan-out" needs. The actual reason to reach for this is
if a use case needs a real CFG (a code grammar, a DSL, not just JSON) that
Ollama's schema mode doesn't express.

Maturity/effort: mature but requires a custom llama.cpp build
(`-DLLAMA_LLGUIDANCE=ON`) or SGLang — non-trivial to slot into an
Ollama-centric setup.

Source: https://github.com/guidance-ai/llguidance

## 8. BAML (schema-aware typed LLM function calling)

What it is: a small typed DSL where you define input/output schema and prompt
together; it coerces any model's raw output into your types via a parsing
algorithm (Schema-Aligned Parsing) rather than requiring the model to have
native function-calling/response_format support.

Why it fits: complements the existing Ollama JSON-schema constrained decoding
— BAML's pitch is it works "day 1" on any newly-pulled local model, even one
whose chat template doesn't yet support structured tool calls cleanly. Useful
if a future model tier lands before Ollama's schema support catches up to it.

Maturity/effort: production-ready project, but it's a new DSL/toolchain to
adopt, not a drop-in library — moderate effort, worth it mainly if
model-specific schema quirks become a recurring pain point.

Source: https://deepwiki.com/BoundaryML/baml

## 9. PaddleOCR-VL (0.9B) or olmOCR for document OCR

What it is: a dedicated sub-1B-parameter OCR/document-structure model
(text, tables, formulas, 109 languages), quantized to ~300MB.

Why it fits: far cheaper than routing pure document/table/formula extraction
through the general-purpose minicpm-v vision tier — this loads fast, does one
job well, and is small enough to fit the zero-idle load/unload-per-call
pattern trivially. Good complement, not a replacement, for minicpm-v (keep
minicpm-v for open-ended "what's in this image" reads, use OCR model for
structured document extraction).

Maturity/effort: PaddleOCR-VL is new in 2026 but already benchmarks at the top
of OmniDocBench for its size class; olmOCR-2 is the more battle-tested
alternative (82.4 accuracy, 1.78 pages/sec). Low effort, it's just another
Ollama/GGUF or MLX pull.

Source: https://insiderllm.com/guides/paddleocr-vl-local-document-ocr/

## 10. whisper.cpp with Core ML / ANE encoder offload

What it is: local speech-to-text with the encoder running on the Apple Neural
Engine via Core ML instead of CPU/GPU.

Why it fits: adds a voice-input modality essentially for free — the ANE is
otherwise idle on this machine, so this doesn't contend with the GPU tiers at
all (3x+ speedup over CPU-only, real-time-capable even on a MacBook-class
chip). Fully in line with zero-idle since it's invoked per-utterance, nothing
stays resident.

Maturity/effort: very mature (ggml-org/whisper.cpp), low effort.

Source: https://github.com/ggml-org/whisper.cpp

## 11. mlx-audio for local TTS (Kokoro 82M / Chatterbox-Turbo 350M)

What it is: an MLX-native audio library covering TTS/STT/STS; Kokoro is an
82M-param Apache-2.0 TTS model, Chatterbox-Turbo a 350M-param distilled
single-step model with sub-200ms latency.

Why it fits: pairs with whisper.cpp for a full local voice loop; both models
are small enough to load per-request and unload after, matching the zero-idle
posture, and both are MLX-native so they use the same execution path as the
rest of the stack rather than requiring a separate PyTorch/CUDA runtime.

Maturity/effort: mature project, small models, low effort.

Source: https://github.com/Blaizzy/mlx-audio

## 12. GEPA (reflective prompt evolution)

What it is: a prompt-optimization framework that iteratively evolves prompts
against a metric using reflective text critique, positioned as lighter-weight
than DSPy (which bundles prompt optimization inside a larger
module-compilation framework).

Why it fits: if there's a desire to auto-tune prompts for the fixed local
tiers (e.g., squeeze more judge-agreement out of gemma4:26b as a judge) without
adopting DSPy's full "compile a program" mental model, GEPA is a narrower,
cheaper tool for exactly that slice.

Maturity/effort: newer (2026), smaller footprint than DSPy, but less battle
tested — treat as worth a pilot, not a default.

Source: https://github.com/gepa-ai/gepa

## 13. A lightweight local model router (vLLM Semantic Router / RouteLLM-style)

What it is: a small classifier that scores an incoming query (difficulty,
domain, required capability) and picks which backend/tier should handle it.

Why it fits: this would formalize the manual routing already happening between
the local lane, gemini-flash, and cloud Claude — replacing "the owner decides"
with a fast, cheap, local pre-classification step. Genuinely useful only if
routing decisions are frequent enough and repetitive enough to be worth
automating; otherwise it's overhead for a decision a human already makes well.

Maturity/effort: early open-source project (2026); meaningful integration
effort since it assumes an OpenAI-compatible multi-backend proxy setup.

Source: https://vllm-semantic-router.com/

---

## Skip these — sound good, don't fit this stack

**exo (distributed inference cluster over Thunderbolt/RDMA).** exo's entire
value proposition is pooling multiple Macs' unified memory to run models too
big for any one machine (e.g., a 671B model across eight Mac minis). This is a
single-Mac stack (one M5 Pro, 64GB) — there's no second machine to cluster
with, so none of exo's actual mechanism (RDMA, memory pooling, cross-node
scheduling) applies. Revisit only if a second Apple Silicon box enters the
picture.

**Stock vLLM (non-MLX).** vLLM's kernels are CUDA-first; it doesn't run
natively on Apple Silicon in any way that beats the MLX-native options above.
The real 2026 story here is community MLX ports (vllm-mlx, oMLX) wrapping
vLLM's API surface around an MLX backend — those are covered above (#2).
Reaching for upstream vLLM itself on this hardware is a dead end.

**llama.cpp Metal speculative decoding (classic draft-model approach).** The
technique that gives 2-4x on CUDA goes *backward* on Apple Silicon specifically
through llama.cpp's Metal path, because each draft-verify step launches a
separate GPU kernel and that dispatch overhead outweighs the tokens saved.
Since part of this stack already routes GGUF models through llama.cpp via
Ollama, it's worth flagging explicitly: don't turn on speculative decoding for
the llama.cpp-routed models — the win only exists on the MLX path (item #1).
