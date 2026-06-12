# Local coding + docs-writing models for a 64 GB M5 Pro (mid-2026)

<!-- sessions: research-agent@2026-06-12 -->
Research date: 2026-06-12. Hardware target: MacBook Pro M5 Pro, 64 GB unified RAM
(~48 GB usable GPU budget), 307 GB/s memory bandwidth. Quality baseline: Claude Opus
(Claude Code daily driver). Confidence flags: **[solid]** = multiple sources,
**[single-source]** = one source, **[computed]** = derived from architecture math,
**[hearsay]** = community anecdote.

---

## 0. TL;DR portfolio

```
┌────────────────────────────────────────────────────────────────────────────┐
│ ROLE            MODEL                      QUANT     RAM      EXPECTED t/s │
├────────────────────────────────────────────────────────────────────────────┤
│ Heavy coder     Qwen3-Coder-Next 80B-A3B   UD-Q4_K_XL ~38-42GB ~20-30 dec  │
│ (agentic)       (MoE, 3B active)           GGUF       +tiny KV  on M5 Pro  │
│ Fast-iter coder Qwen3.6-35B-A3B            Q4/MLX-4b  ~20GB    ~30-45      │
│ (default)       (MoE, 3B active)                      +KV                  │
│ Prose/docs +    Gemma 4 26B-A4B-it         Q6/Q8      ~21-27GB ~25-35 (est)│
│ precision       (MoE, 4B active)                      +KV                  │
│ Alt dense coder Qwen3.6-27B dense          Q6         ~22GB    ~12-22      │
│ (quality/token) or Devstral Small 2 24B    Q8         ~25GB    ~15-20 (est)│
└────────────────────────────────────────────────────────────────────────────┘
Runner: LM Studio (MLX engine) or mlx_lm.server for the heavy tier;
Ollama ≥0.19 (MLX backend preview) acceptable if you want to keep one stack.
```

---

## 1. Current best open coding models that fit ≤48 GB

The landscape moved a lot between late 2025 and mid-2026. Key arrivals: Qwen3-Coder-Next
(Feb 2026), Gemma 4 (Apr 2, 2026), Qwen3.6 family (Apr 16, 2026), Devstral 2 (late 2025/2026),
GLM-4.7/4.7-Flash, GLM-5, MiniMax-M2.x, Kimi K2.x. The last four flagship-class models do
NOT fit 48 GB; details below so you know what you're not missing locally.

### 1.1 Qwen3-Coder-Next (80B total / 3B active MoE) — the 48 GB-class agentic flagship

- **Params:** 80B total, ~3B active (10 of 512 experts/token).
  [dev.to guide](https://dev.to/sienna/qwen3-coder-next-the-complete-2026-guide-to-running-powerful-ai-coding-agents-locally-1k95) **[solid]**
- **Released:** Feb 2026 (Alibaba). Apache 2.0.
- **Quant that fits:** UD-Q4_K_XL ≈ 35–40 GB weights — fits the 48 GB budget; Q6_K (~50–55 GB)
  does NOT fit alongside macOS + KV. Unsloth's author recommends UD-Q4_K_XL for most hardware
  ([HN thread](https://news.ycombinator.com/item?id=46872706)). **[solid]**
- **Context:** 256K native, YaRN to 1M.
- **KV cache is its superpower:** hybrid 3:1 Gated-DeltaNet (linear) : full-attention (GQA, 2 KV
  heads) layout means only ~25% of layers hold per-token KV. Real-world report: **~25 GB KV for
  1M tokens** on Apple Silicon — i.e. roughly **0.8 GB @ 32k / 1.6 GB @ 64k / 3.2 GB @ 128k**
  [computed from that ratio]
  ([GitHub QwenLM discussion #139](https://github.com/QwenLM/Qwen3.6/discussions/139),
  [vLLM blog on Qwen3-Next](https://blog.vllm.ai/2025/09/11/qwen3-next.html)). **[solid]**
  This is the one model where 128k coding context is essentially free.
- **Speed:** guide-level numbers: Q4_K_XL "25–40 tok/s" on a 64 GB MacBook Pro (chip unspecified)
  **[single-source]**. M5 Pro at 307 GB/s should land ~20–30 tok/s decode; MoE-A3B is far less
  bandwidth-bound than dense, and M5 Neural Accelerators give 3–4× prefill
  ([Ollama MLX blog](https://ollama.com/blog/mlx)). **[computed/estimate]**
- **Benchmarks:** InsiderLLM cites SWE-bench Pass@5 rebench 64.6% (#1 at release for
  consumer-runnable models) ([InsiderLLM coding guide](https://insiderllm.com/guides/best-local-coding-models-2026/));
  dev.to guide cites SWE-bench Verified 42.8% / SWE-bench Pro 44.3% — note the wide spread
  between marketing and harness numbers. **[conflicting — treat ranking, not absolute, as real]**
- **Agentic:** reliable JSON function calling; needs `--tool-call-parser qwen3_coder` in some
  runners; takes ~150 agent turns where Claude Sonnet 4.5 takes ~120 (more exploratory loops).
  No thinking blocks. **[single-source]**
- **HN reality check** ([HN #46872706](https://news.ycombinator.com/item?id=46872706)) **[hearsay but multiple users]:**
  Q2/Q4 quants felt "more like Haiku level than Sonnet 4.5"; tool-format mismatches (XML-expecting
  CLIs vs JSON-emitting model) caused loops in Codex CLI; one MLX user reported KV-cache
  consistency problems with conversation branching (prefer llama.cpp/GGUF for long agent
  sessions on this model until MLX fix confirmed).

### 1.2 Qwen3.6-35B-A3B (Apr 16, 2026) — the 2026 default for this RAM tier

- **Params:** 35B total / 3B active MoE, multimodal, Apache 2.0
  ([HF model card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B)). **[solid]**
- **Benchmarks:** SWE-bench Verified **73.4%**, SWE-bench Multilingual 67.2, SWE-bench Pro 49.5,
  Terminal-Bench 2.0 51.5, MCPMark (tool use) 37.0 — double Gemma 4-31B's MCPMark
  ([buildfastwithai review](https://www.buildfastwithai.com/blogs/qwen3-6-35b-a3b-review),
  [llm-stats](https://llm-stats.com/models/qwen3.6-35b-a3b)). Official-card numbers —
  independent verification still thin. **[solid for existence, single-source for magnitude]**
- **Context:** 262K native, extensible ~1M.
- **Quant/RAM:** Q8 ≈ 37 GB (fits but tight with big KV); Q4/MLX-4bit ≈ 18–20 GB — the
  comfortable choice, leaves room for a second resident model
  ([InsiderLLM Mac guide](https://insiderllm.com/guides/best-local-llms-mac-2026/)). **[solid]**
- **Speed:** M4 Max: ~45–55 tok/s MLX, ~35–45 Ollama at Q4 (InsiderLLM). M5 Pro has half the
  Max's bandwidth, but A3B active set is small: expect ~30–45 tok/s MLX. **[estimate]**
- **Agentic:** strong tool calling (4/4 in the Tort Mario real-work test below); weaker at
  obeying unusual style rules, and thinking mode makes instruction-following *worse*
  ([Medium real-work test](https://medium.com/@tort_mario/local-llms-in-real-work-gemma-4-qwen-3-6-and-qwen-coder-d43811c7e9b2)). **[single-source]**

### 1.3 Qwen3.6-27B dense — quality-per-token coding pick

- SWE-bench Verified **77.2%**, LiveCodeBench v6 83.9, Terminal-Bench 2.0 59.3 — "matches
  Sonnet 4.6 on SWE-bench Verified" per InsiderLLM
  ([InsiderLLM coding guide](https://insiderllm.com/guides/best-local-coding-models-2026/)). **[single-source, official-card derived]**
- Q4 ≈ 17 GB; Q6/Q8 ≈ 22–30 GB. Simon Willison measured 25.57 tok/s at Q4_K_M (chip:
  M-series, exact model in his post) — "outstanding result for a 16.8 GB local model". **[solid]**
- Dense ⇒ bandwidth-bound: 12–22 tok/s at Q6/Q8 on this class of hardware. Higher single-token
  quality than the A3B MoE on code, but 2–3× slower. Good "deep review" model, sluggish as an
  agent driver.

### 1.4 Gemma 4 (26B-A4B MoE and 31B dense) — Google, Apr 2, 2026

- 26B-A4B: 4B active. Won a 12-task real-work shootout 12/12 (Fast mode) vs Qwen3.6 9/12 and
  Qwen3-Coder-30B 8/12 — only model that consistently wrote correct unit tests, 4/4 on
  AGENTS.md-style rule adherence, perfect tool calling
  ([Medium real-work test](https://medium.com/@tort_mario/local-llms-in-real-work-gemma-4-qwen-3-6-and-qwen-coder-d43811c7e9b2)). **[single-source but detailed]**
- 31B dense: LMArena ~1441, #3 open model on Arena text; but SWE-bench Verified only 52.0 vs
  Qwen3.6's 73.4 ([buildfastwithai](https://www.buildfastwithai.com/blogs/qwen3-6-35b-a3b-review)).
  Gemma = better arena/writing signal, worse harness-agentic signal. **[solid]**
- Multiple 2026 roundups name Gemma 4 26B-A4B "the strong default for local coding" and the
  best general open model on consumer hardware
  ([HF blog roundup](https://huggingface.co/blog/daya-shankar/open-source-llms),
  [Fireworks roundup](https://fireworks.ai/blog/best-open-source-llms)).

### 1.5 Devstral 2 / Devstral Small 2 (Mistral)

- Devstral 2 (123B dense): SWE-bench Verified **72.2%** — "matches Claude Opus ~72%" per
  VentureBeat framing — but Q4 ≈ 65 GB: does NOT fit 48 GB
  ([Mistral announcement](https://mistral.ai/news/devstral-2-vibe-cli/),
  [VentureBeat](https://venturebeat.com/ai/mistral-launches-powerful-devstral-2-coding-model-including-open-source)). **[solid]**
- **Devstral Small 2 (24B dense, Apache 2.0): SWE-bench Verified 68.0%**, ~14 GB at Q4 —
  punches at models 5× its size, purpose-built for agentic coding (SWE-agent-style scaffolds)
  ([aimadetools guide](https://www.aimadetools.com/blog/devstral-small-2-guide/)). Fits easily
  at Q8 (~25 GB). Strong dark-horse for the agent role if Qwen tool-format quirks annoy you. **[solid]**
- Codestral remains the FIM/completion specialist (256K ctx, 80+ langs) — relevant only if you
  want tab-completion, not chat coding.

### 1.6 Doesn't fit 48 GB (so you stop wondering)

| Model | Size | Verdict |
|---|---|---|
| GLM-4.6 / GLM-5 | 355B / 744B MoE | 2-bit GGUF still 135 GB / 241 GB. API-only at this RAM ([Unsloth GLM-4.6](https://unsloth.ai/docs/models/tutorials/glm-4.6-how-to-run-locally), [Unsloth GLM-5](https://unsloth.ai/docs/models/tutorials/glm-5)) |
| GLM-4.5-Air | 106B | borderline; ~Q3 might squeeze but community treats 64 GB as floor-of-pain. GLM-4.7-Flash (30B MoE) DOES fit — fast (60–80 tok/s on M-series) but "competitive with Sonnet 3.5", i.e. below Qwen3.6 tier ([WaveSpeed](https://wavespeed.ai/blog/posts/glm-4-7-flash-local/), [Medium GLM-4.7-Flash](https://medium.com/@zh.milo/glm-4-7-flash-the-ultimate-2026-guide-to-local-ai-coding-assistant-93a43c3f8db3)) **[mixed sources]** |
| MiniMax-M2 / M2.7 | 230B-A10B | "Below 64 GB → not viable"; M2.7 4-bit = 108 GB, wants 128 GB Mac ([Unsloth M2.7](https://unsloth.ai/docs/models/tutorials/minimax-m27), [shareuhack](https://www.shareuhack.com/en/posts/minimax-m27-local-ai-guide-2026)) |
| Kimi K2.x | ~1T MoE | API-only. Best-in-class open writing though (see §2) |
| DeepSeek V4-Flash | 284B-A13B | ~150 GB Q4; "homelab story, not consumer-GPU" ([InsiderLLM](https://insiderllm.com/guides/best-local-coding-models-2026/)) |
| Llama 4 / Llama 3.3 70B | 70B dense Q4 ≈ 40 GB | fits but 8–12 tok/s on M5 Pro and is no longer competitive on coding benchmarks vs Qwen3.6 ([PromptQuorum M5 benchmarks](https://www.promptquorum.com/local-llms/m5-pro-max-llm-benchmarks-2026)) |

### 1.7 Aider-polyglot context

Top of the June 2026 Aider-polyglot board: GPT-5 0.880; best open model is DeepSeek-V3.2-Exp at
0.745 (#5, between Claude Opus 4's 72% and o4-mini) — but that's a full-size DeepSeek, API-tier
([llm-stats Aider-polyglot](https://llm-stats.com/benchmarks/aider-polyglot),
[aider leaderboard](https://aider.chat/docs/leaderboards/)). No ≤48 GB-class model appears near
the top; the local-tier story is told by SWE-bench/LiveCodeBench numbers above. **[solid]**

---

## 2. Docs-writing quality (technical prose)

Benchmarks are scarce; the best proxies are EQ-Bench Creative Writing v3, LMArena, and
community testing.

- **EQ-Bench CW v3 (June 2026):** Claude Opus 4.7 leads (Elo 2206). Best open: Qwen3-235B-A22B
  class (0.875, #3) — too big locally. **Kimi K2** is the famous open "writer's model"
  (~77% of Opus 4.7's creative Elo at 9× cheaper) — API-only at your RAM
  ([eqbench.com](https://eqbench.com/creative_writing.html),
  [llm-stats CW v3](https://llm-stats.com/benchmarks/creative-writing-v3),
  [EVY aggregation](https://evy.so/compare/best-llms-for-writing/)). **[solid]**
- **In the runnable tier, Gemma is the prose pick.** Gemma 4-31B is #3 open on Arena text
  (1441) — arena voting rewards exactly the clean-prose/instruction-following blend docs need
  ([buildfastwithai open-LLM collection](https://www.buildfastwithai.com/blogs/collection/open-source-llms)).
  Gemma-family reputation on r/LocalLLaMA has been "best local writing voice" since Gemma 2/3;
  the Gemma 4 real-work test confirmed best-in-tier instruction adherence (4/4 on style rules
  where Qwen3.6 got 3/4 and 1/4 in thinking mode). **[community consensus + single structured test]**
- **Qwen habits:** strong but noticeably more verbose/list-happy in docs prose; thinking mode
  actively degrades rule-following (second-guesses unusual constraints) — turn it OFF for docs
  ([Medium real-work test](https://medium.com/@tort_mario/local-llms-in-real-work-gemma-4-qwen-3-6-and-qwen-coder-d43811c7e9b2)). **[single-source, matches long-standing community hearsay]**
- **Coder-tuned models write worse prose** than their general siblings (Qwen3-Coder-30B scored
  lowest in the same test, incl. on non-code instruction tasks). Don't use the coder variant
  for README/ADR writing. **[single-source + intuitive]**
- No "technical writing" benchmark exists as of June 2026 — flag: all prose-quality claims here
  are creative-writing-proxy or anecdote. **[explicit gap]**

---

## 3. Honest Opus-baseline calibration

What an Opus-calibrated user should actually expect from the ≤48 GB tier:

- **Benchmark parity is real but narrow.** Qwen3.6-27B's 77.2% SWE-bench Verified nominally
  beats Claude-Sonnet-class numbers, and Devstral 2 (123B) matches Opus ~72% — but these are
  harness-scaffolded, pass@k-flattered numbers from official cards. Hands-on reports are far
  more sober. **[solid pattern across sources]**
- **Where the gap bites hardest (ranked):**
  1. **Multi-file / cross-repo reasoning** — a 2026 benchmark put Claude at a ~60% advantage on
     multi-file context tasks vs the best local model; "local models struggle to understand how
     files relate" ([kunalganglani benchmark](https://www.kunalganglani.com/blog/local-llm-vs-claude-coding-benchmark),
     [dev.to 32GB-vs-Opus](https://dev.to/alanwest/cloud-llms-vs-local-models-can-32gb-of-vram-actually-compete-with-claude-opus-1flj)). **[solid]**
  2. **Sustained agent loops** — HN consensus: nobody has "a local model that fits on my 64GB
     MacBook Pro and can run a coding agent like Codex CLI or Claude Code well enough to be
     useful"; quantized Coder-Next felt "more like Haiku than Sonnet 4.5"; tool-format
     mismatches and thinking-loops break long sessions
     ([HN #46872706](https://news.ycombinator.com/item?id=46872706)). **[hearsay, multiple users]**
  3. **Instruction nuance** — local models obey the letter, miss the spirit; unusual constraints
     get second-guessed (thinking-mode regression above).
  4. **Long-context fidelity** — 256K on the box ≠ 256K usable; effective recall degrades well
     before the limit (community-reported, unquantified). **[hearsay]**
- **Where local is genuinely fine:** single-file edits, bug fixes, test generation, boilerplate,
  code explanation, scoped refactors — "the 80%+ of day-to-day work," with cloud models judged
  "approximately one year ahead" ([BSWEN comparison](https://docs.bswen.com/blog/2026-03-23-local-llm-vs-claude-gpt-coding/),
  [InsiderLLM](https://insiderllm.com/guides/best-local-coding-models-2026/)). **[solid consensus]**
- **Calibration sentence:** expect *good-Sonnet-3.5-to-low-Sonnet-4-class* output on scoped
  tasks, *Haiku-class* behavior in long agentic loops, and don't hand it the cross-repo
  refactors you'd give Opus. The right mental model is "very capable junior pair" not
  "Opus offline."

---

## 4. Runner choice for the heavy tier (Apple Silicon, mid-2026)

Big 2026 development: **Ollama 0.19 (Mar 31, 2026) shipped an MLX backend preview** for
Apple Silicon (32 GB+ Macs): ~1.6× faster prefill, ~2× decode vs its llama.cpp path, and on
M5-family chips it uses the GPU Neural Accelerators for 3–4× prompt processing
([Ollama blog](https://ollama.com/blog/mlx), [9to5Mac](https://9to5mac.com/2026/03/31/ollama-adopts-mlx-for-faster-ai-performance-on-apple-silicon-macs/),
[MacRumors](https://www.macrumors.com/2026/03/31/ollama-now-runs-faster-apple-silicon-macs/)). **[solid]**

| Runner | Speed | Memory | Load/unload (no-idle) | Notes |
|---|---|---|---|---|
| **mlx_lm.server / MLX-LM** | Fastest: MLX beats Ollama-llama.cpp by 15–30% tok/s, ~10% less RAM ([willitrunai](https://willitrunai.com/blog/mlx-vs-ollama-apple-silicon-benchmarks)) | Best | Manual (process start/stop — scriptable, fits on-demand pattern) | You already have an MLX venv. mlx-community has full Qwen3.6 coverage. KV-cache branching bug reported on Coder-Next specifically **[hearsay]** |
| **LM Studio** | ~MLX speed (uses MLX engine on Mac) | Good | GUI + `lms load/unload` CLI; JIT-load + auto-evict on idle TTL | Best ergonomics for a heavy on-demand tier; OpenAI-compatible server |
| **Ollama ≥0.19 (MLX preview)** | ~85% of raw MLX | Good | Best-in-class: `keep_alive`/`OLLAMA_KEEP_ALIVE=0` gives automatic unload — matches your no-idle rule natively | Keeps your existing stack/Modelfiles; MoE + M5 accelerators supported; preview-quality, some model bugs in 0.18.x fixed in 0.19 |
| **llama.cpp direct** | Between Ollama-old and MLX; best flag control (`--n-cpu-moe`, KV quant per K/V, speculative decoding) | Fine | Manual | The fallback when MLX lags a brand-new architecture; recommended over MLX for Coder-Next agent sessions (KV consistency) ([dev.to Coder-Next guide](https://dev.to/sienna/qwen3-coder-next-the-complete-2026-guide-to-running-powerful-ai-coding-agents-locally-1k95)) |

**Recommendation:** stay on **Ollama 0.19+ with MLX backend** as the integration point (your
flash-attn + q8 KV config carries over; `keep_alive 0` preserves no-idle), and keep
**llama.cpp GGUF** as the escape hatch for Qwen3-Coder-Next agent sessions until the MLX KV
issue is confirmed fixed. Use LM Studio only if you want a GUI model browser.
Speculative decoding: supported in llama.cpp/LM Studio; MoE-A3B models gain little from it
(active set already tiny) — skip the complexity. **[reasoned, low-confidence on spec-decode gains]**

---

## 5. Recommended portfolio + KV-cache math

### Roles

1. **Heavy agentic coder — Qwen3-Coder-Next 80B-A3B, UD-Q4_K_XL (Unsloth GGUF, llama.cpp or
   Ollama).** ~38–42 GB weights + near-zero KV growth. Expected ~20–30 tok/s decode on M5 Pro
   **[estimate]**, fast prefill via M5 accelerators (Ollama-MLX path) or llama.cpp. This is the
   "load it, do the big scoped task, unload it" model. On-demand only — it owns the machine
   while loaded.
2. **Fast-iteration default coder — Qwen3.6-35B-A3B, 4-bit MLX (~20 GB) or Q4_K_M GGUF.**
   ~30–45 tok/s. Can stay co-resident with the prose model (20 + 27 GB < 48 GB).
   Disable thinking mode for instruction-heavy work.
3. **Prose/docs specialist — Gemma 4 26B-A4B-it, Q6/Q8 (~21–27 GB).** Best-in-tier instruction
   adherence and writing voice; also a shockingly good precision coder (won the real-work
   shootout) — useful second opinion on reviews.
   - Alt: if you'd rather consolidate, Qwen3.6-35B-A3B does docs acceptably but more verbosely.
4. **Optional dense second-opinion — Qwen3.6-27B Q6 or Devstral Small 2 24B Q8** for
   highest-quality single-shot review/refactor when 15–22 tok/s is acceptable.

### KV-cache cost at coding contexts (the num_ctx caveat)

Your stack pins `num_ctx` + q8 KV. Costs per model (K+V, per-token = 2·layers·kv_heads·head_dim·bytes):

| Model | f16 @32k / 64k / 128k | q8 @32k / 64k / 128k | Basis |
|---|---|---|---|
| Qwen3-Coder-Next 80B (hybrid) | ~0.8 / 1.6 / 3.2 GB | ~half | ~25 GB per 1M tokens reported ([QwenLM discussion #139](https://github.com/QwenLM/Qwen3.6/discussions/139)) **[solid]** |
| Qwen3-Coder-30B-A3B (48L, 4 KV heads, d128) | ~3 / 6 / 12 GB | ~1.5 / 3 / 6 GB | **[computed]**; one user ran 262K in ~5.7 GB with aggressive turbo-quant KV ([llama.cpp discussion](https://github.com/ggml-org/llama.cpp/discussions/20969)) |
| Qwen3.6-35B-A3B | similar order to Coder-30B **[computed, arch unverified — verify layer/head counts on the HF card before pinning]** | ~1.5–3 / 3–6 / 6–12 GB | |
| Devstral Small 2 24B (Mistral-Small arch, est. 40L, 8 KV heads) | ~10 / 20 / 40 GB | ~5 / 10 / 20 GB | **[computed, low-confidence arch]** — dense models are the KV hogs; 128k is NOT practical here |
| Gemma 4 26B-A4B | unknown — Gemma 3 used sliding-window interleave which cut KV ~4×; assume moderate. **[low-confidence]** Verify empirically with `ollama ps` after load. | | |

Practical Modelfile guidance:
- Heavy tier (Coder-Next): `num_ctx 131072` is safe — KV is trivial on this architecture.
  Budget check: 42 GB weights + ~2 GB KV + overhead ≈ 45 GB. Tight but OK; drop to 96k if
  macOS pressure-kills.
- Fast tier (Qwen3.6-35B): `num_ctx 65536` with q8 KV ≈ 20 GB + ~3 GB = 23 GB. 128k pushes
  ~26 GB — still fine standalone, but not co-resident with Gemma at Q8.
- Prose tier (Gemma 4): docs rarely need >32k; pin `num_ctx 32768`.
- Keep flash attention on (`OLLAMA_FLASH_ATTENTION=1`) — required for KV quantization anyway.

### What NOT to do

- Don't chase GLM-5 / MiniMax-M2.7 / Kimi K2.6 locally — 2-bit desperation quants of 200B+
  models on 64 GB are strictly worse than a clean Q4 of the models above.
- Don't run the coder-tuned models for docs writing.
- Don't trust 73–77% SWE-bench numbers as "Opus at home" — see §3 calibration.
- Don't leave the heavy tier resident: 42 GB weights + Opus-driven workflows elsewhere will
  swap-thrash. `keep_alive 0` / explicit unload.

---

## Sources (load-bearing)

- https://insiderllm.com/guides/best-local-coding-models-2026/ — VRAM-tier coding rankings, Apr-May 2026
- https://insiderllm.com/guides/best-local-llms-mac-2026/ — Mac-specific recs + tok/s, runner notes
- https://huggingface.co/Qwen/Qwen3.6-35B-A3B + https://llm-stats.com/models/qwen3.6-35b-a3b — Qwen3.6 specs/benchmarks
- https://www.buildfastwithai.com/blogs/qwen3-6-35b-a3b-review — Qwen3.6 vs Gemma 4 benchmark table
- https://dev.to/sienna/qwen3-coder-next-the-complete-2026-guide-to-running-powerful-ai-coding-agents-locally-1k95 — Coder-Next quants/RAM/speeds/agentic
- https://news.ycombinator.com/item?id=46872706 — Coder-Next community reality check
- https://github.com/QwenLM/Qwen3.6/discussions/139 — hybrid-arch KV: ~25 GB per 1M tokens on Apple Silicon
- https://blog.vllm.ai/2025/09/11/qwen3-next.html — Qwen3-Next hybrid attention architecture
- https://medium.com/@tort_mario/local-llms-in-real-work-gemma-4-qwen-3-6-and-qwen-coder-d43811c7e9b2 — 12-task real-work shootout (Gemma 4 won)
- https://mistral.ai/news/devstral-2-vibe-cli/ + https://venturebeat.com/ai/mistral-launches-powerful-devstral-2-coding-model-including-open-source — Devstral 2 / Small 2
- https://unsloth.ai/docs/models/tutorials/glm-5 + https://unsloth.ai/docs/models/tutorials/minimax-m27 — why GLM-5/MiniMax don't fit
- https://eqbench.com/creative_writing.html + https://evy.so/compare/best-llms-for-writing/ — writing-quality proxies
- https://www.kunalganglani.com/blog/local-llm-vs-claude-coding-benchmark + https://dev.to/alanwest/cloud-llms-vs-local-models-can-32gb-of-vram-actually-compete-with-claude-opus-1flj — Opus-gap head-to-heads
- https://ollama.com/blog/mlx + https://willitrunai.com/blog/mlx-vs-ollama-apple-silicon-benchmarks — runner/MLX backend, M5 accelerators
- https://www.promptquorum.com/local-llms/m5-pro-max-llm-benchmarks-2026 — M5 Pro 307 GB/s + tok/s baselines
- https://aider.chat/docs/leaderboards/ + https://llm-stats.com/benchmarks/aider-polyglot — Aider polyglot standings
