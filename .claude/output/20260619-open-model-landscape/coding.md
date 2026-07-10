# Open-Weight Models for CODING — Landscape Survey

**Compiled:** 2026-06-19 · **Method:** live WebSearch/WebFetch across HF model cards, vendor blogs, Aider-polyglot / SWE-bench / LiveBench leaderboards, Artificial-Analysis-style roundups, r/LocalLLaMA-adjacent aggregators. Knowledge-cutoff memory was explicitly distrusted; every model below was re-confirmed against a 2026 source.

> **Hardware framing used throughout:** target box is a **64GB Apple-Silicon Mac**, with **~48GB usable** as the realistic model+context budget (the OS, app, and KV-cache eat the rest). "Fits 64GB?" answers assume a **4-bit quant (MLX or GGUF Q4)** and leave headroom for context. A model whose 4-bit weights alone exceed ~45GB is marked **API-tier / too big**.

---

## TL;DR — what to actually run vs. call

| Need | Run locally on 64GB | Reach for API |
|---|---|---|
| **Agentic coding (best local)** | Qwen3-Coder-Next 80B-A3B (4-bit, ~42GB) · GLM-4.5-Air 106B-A12B (4-bit ~40GB, tight) | GLM-5.2 · DeepSeek-V4-Pro · Kimi K2.7-Code |
| **Dense single-shot quality** | Qwen3.6-27B (4-bit ~17GB, roomy) · Devstral-Small-2 24B | — |
| **Fast iteration / tab-speed agent** | Qwen3-Coder-30B-A3B (4-bit ~18GB, 60+ tok/s) | DeepSeek-V4-Flash |
| **FIM / IDE autocomplete** | Codestral 2 22B · Qwen2.5-Coder 1.5B/7B · Seed-Coder 8B | — |
| **Frontier / too-big-to-run** | — | DeepSeek-V4-Pro · GLM-5.2 · Kimi K2.7-Code · Qwen3-Coder-480B |

---

## A. Agentic coders (tool-use, long-horizon, SWE-bench-shaped)

These are the "drive a coding agent / CLI" models. The local-runnable ones are MoE with low active-param counts (cheap to run despite large total size *if* it fits in unified RAM).

| Model | Params / arch | License | Get it | Runs on 64GB Mac (4-bit)? | Best at | Headline number | Source (date) | Conf |
|---|---|---|---|---|---|---|---|---|
| **Qwen3-Coder-Next** (80B-A3B) | 80B total / **3B active**, hybrid (Gated-DeltaNet + attn) MoE | Apache-2.0 | `Qwen/Qwen3-Coder-Next` · `unsloth/Qwen3-Coder-Next-GGUF` · Ollama | **Yes (tight-ish)** — 4-bit needs ~42GB SSD + ~48GB unified RAM; 64GB recommended. ~20+ tok/s | Best *local* agentic coder; 3B active = cheap inference for an 80B-class brain | "comparable to models with 10–20× more active params" | [unsloth.ai](https://unsloth.ai/docs/models/qwen3-coder-next), [dev.to guide](https://dev.to/sienna/qwen3-coder-next-the-complete-2026-guide-to-running-powerful-ai-coding-agents-locally-1k95) (2026) | [solid] |
| **GLM-4.5-Air** (106B-A12B) | 106B total / **12B active** MoE | MIT | `zai-org/GLM-4.5-Air` · `cyankiwi/GLM-4.5-Air-AWQ-4bit` | **Borderline** — 4-bit ~40GB, fits 64GB but thin context headroom | Long-horizon agentic engineering, step-down from full GLM | 57.6% SWE-bench Verified | [HF zai-org/GLM-4.5-Air](https://huggingface.co/zai-org/GLM-4.5-Air), [ssojet roundup](https://ssojet.com/blog/best-local-llms-coding) (2026) | [solid] |
| **Devstral 2** (123B dense) | 123B **dense** | Modified MIT | `mistralai/` on HF · Mistral API | **No** — 123B dense at 4-bit ≈ 62GB+, exceeds budget → effectively API/server | Agentic SWE (built w/ All Hands AI), OpenHands/Vibe CLI | 72.2% SWE-bench Verified; 66.79 LiveBench Coding | [mistral.ai/news/devstral-2-vibe-cli](https://mistral.ai/news/devstral-2-vibe-cli/), [VentureBeat](https://venturebeat.com/ai/mistral-launches-powerful-devstral-2-coding-model-including-open-source) (2026) | [solid] |
| **Qwen3-Coder-480B-A35B** | 480B / 35B active MoE | Apache-2.0 | `Qwen/Qwen3-Coder-480B-A35B-Instruct(-FP8)` | **No** — even 2-bit dynamic GGUF is server-class | Frontier agentic + browser-use, ~Claude-Sonnet class | "comparable to Claude Sonnet on agentic coding" | [HF Qwen3-Coder-480B](https://huggingface.co/Qwen/Qwen3-Coder-480B-A35B-Instruct) (2026) | [solid] |
| **GLM-5.2** (754B-class MoE) | ~754B total MoE | MIT | `zai-org/GLM-5` family · Z.ai API | **No** — server-class; Unsloth 2-bit GGUF still ~241GB | SOTA *open* long-horizon coding; sustains multi-hour autonomous runs | **62.1 SWE-bench Pro** (beats GPT-5.5's 58.6) | [VentureBeat GLM-5.2](https://venturebeat.com/technology/z-ais-open-weights-glm-5-2-beats-gpt-5-5-on-multiple-long-horizon-coding-benchmarks-for-1-6th-the-cost) (2026-06) | [single-source] |
| **DeepSeek-V4-Pro** (1.6T-A49B) | 1.6T total / 49B active MoE, 1M ctx | MIT | `deepseek-ai/DeepSeek-V4-Pro` · DeepSeek API | **No** — frontier, server-class | Highest open-weights SWE-bench; speaks OpenAI + Anthropic API (drops into Claude Code/OpenCode) | **80.6% SWE-bench Verified** (DeepSeek-V4-Pro-Max), tied w/ Gemini 3.1 Pro | [HF blog deepseekv4](https://huggingface.co/blog/deepseekv4), [nxcode](https://www.nxcode.io/resources/news/deepseek-v4-release-specs-benchmarks-2026) (2026) | [solid] |
| **Kimi K2.7-Code** (1T-A32B) | 1T total / 32B active MoE, native INT4 | Modified MIT | `moonshotai/` on HF · Moonshot API | **No** — even native INT4 of a 1T MoE is ~server-class (~250GB+) | Agent-swarm orchestration (up to 300 sub-agents, ~4000 steps), coding-driven UI gen | +21.8% Kimi-Code-Bench-v2 vs K2.6; ~ties GPT-5.5 coding | [explainx K2.7-Code](https://www.explainx.ai/blog/kimi-k2-7-code-open-source-coding-model-2026) (2026-06-12) | [single-source] |

**Notes on the API-tier four (GLM-5.2 / DeepSeek-V4-Pro / Kimi K2.7-Code / Qwen3-Coder-480B):** all are *open-weight* (downloadable, MIT/Apache/Modified-MIT), but their 4-bit footprints run **150–400GB+**, far past a 64GB Mac. They are "open but not local" — run via their own APIs or rented GPUs. DeepSeek-V4 is notable for **dual OpenAI+Anthropic API compatibility**, so it slots into Claude Code without a proxy.

---

## B. Dense quality coders (every param active; predictable, single-shot strength)

Dense models give consistent VRAM/throughput and tend to be the sweet-spot for "one good answer" coding on a single box.

| Model | Params / arch | License | Get it | Runs on 64GB Mac (4-bit)? | Best at | Headline number | Source (date) | Conf |
|---|---|---|---|---|---|---|---|---|
| **Qwen3.6-27B** | 27B **dense** (Gated-DeltaNet + attn hybrid) | Apache-2.0 | `Qwen/Qwen3.6-27B` · GGUF/MLX | **Yes, easily** — Q4_K_M ≈ 16.8GB, tons of headroom; M3 Max/Ultra-class | Best *dense* single-GPU coder; beats the prior 397B MoE flagship | **77.2 SWE-bench Verified** (vs 76.2 for 397B MoE) | [qwen.ai blog](https://qwen.ai/blog?id=qwen3.6-27b), [MarkTechPost](https://www.marktechpost.com/2026/04/22/alibaba-qwen-team-releases-qwen3-6-27b-a-dense-open-weight-model-outperforming-397b-moe-on-agentic-coding-benchmarks/) (2026-04-22) | [solid] |
| **Devstral-Small-2** | 24B **dense**, 128K ctx | Apache-2.0 | `mistralai/Devstral-Small-2` on HF · Ollama | **Yes** — 4-bit ~14–15GB | Laptop-friendly agentic SWE; clean Apache license, redistributable fine-tunes | part of Devstral 2 family (72.2% SWE-V at the 123B tier) | [VentureBeat Devstral 2](https://venturebeat.com/ai/mistral-launches-powerful-devstral-2-coding-model-including-open-source), [Mistral news](https://mistral.ai/news/devstral-2-vibe-cli/) (2026) | [solid] |
| **gpt-oss-20b** | 20.9B total / 3.6B active MoE, MXFP4 | Apache-2.0 | `openai/gpt-oss-20b` · Ollama | **Yes** — designed to fit ~16GB | Reasoning + tool-use coding on a laptop; strong instruction-following | matches/exceeds o4-mini on Codeforces (the 120B); 20b is the laptop tier | [OpenAI gpt-oss model card](https://openai.com/index/gpt-oss-model-card/) (2025-08, still current baseline) | [solid] |
| **Seed-Coder-8B** (Base/Instruct/Reasoning) | 8B **dense**, 32K ctx | MIT | `ByteDance-Seed/Seed-Coder-8B-*` · Ollama | **Yes, trivially** — 4-bit ~5GB | SOTA among ~8B open code models; small, fast, MIT | ~57.1 Aider self-test (beats Qwen3-8B, Qwen2.5-Coder-7B) | [HF ByteDance-Seed/Seed-Coder](https://huggingface.co/ByteDance-Seed/Seed-Coder-8B-Instruct), [GitHub](https://github.com/ByteDance-Seed/Seed-Coder) (2026) | [solid] |

> **Note:** gpt-oss is technically MoE (low active params) but behaves as a "dense-quality" pick at its size class and is grouped here for the laptop-quality use case. `gpt-oss-120b` (116.8B/5.1B) needs a single 80GB GPU — **borderline-too-big** for a 64GB Mac at full precision; an aggressive 4-bit MoE quant (~60GB) is marginal, treat as API/server-leaning.

---

## C. Fast-iteration coders (low active params → high tok/s for agent loops)

For tight agent loops where latency dominates, you want low *active* params and a quant that fully fits in RAM (no offload).

| Model | Params / arch | License | Get it | Runs on 64GB Mac (4-bit)? | Best at | Headline number | Source (date) | Conf |
|---|---|---|---|---|---|---|---|---|
| **Qwen3-Coder-30B-A3B** | 30B / **3B active** MoE | Apache-2.0 | `lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-4bit` · `unsloth/...GGUF` · Ollama | **Yes, comfortably** — 4-bit MLX ~18–20GB, **~68 tok/s on M4 Max** | Best speed/quality local agent driver; fast enough for iterative tool loops | Smaller sibling of the 480B; "10–20× active-param efficiency" lineage | [HF MLX-4bit card](https://huggingface.co/lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-4bit), [unsloth](https://unsloth.ai/docs/models/tutorials/qwen3-coder-how-to-run-locally) (2026) | [solid] |
| **DeepSeek-V4-Flash** (284B-A13B) | 284B total / **13B active** MoE, 1M ctx | MIT | `deepseek-ai/DeepSeek-V4-Flash` · API | **No** — 284B total still ~140GB+ at 4-bit; fast via API, not local | High-throughput agentic coding at API tier, 1M context agents | 69.99 LiveBench Coding-Avg (V4-Pro snapshot; Flash is the fast tier) | [HF DeepSeek-V4-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash), [codersera guide](https://codersera.com/blog/deepseek-v4-complete-guide-2026/) (2026) | [single-source] |
| **gpt-oss-20b** | (see §B) | Apache-2.0 | `openai/gpt-oss-20b` | **Yes** | Laptop-speed reasoning+tools | — | (see §B) | [solid] |
| **Qwen3-Coder-Next** (80B-A3B) | (see §A) | Apache-2.0 | (see §A) | **Yes (tight)** — 3B active keeps it fast despite 80B total | Fast *and* strong if you can spare the ~42GB | — | (see §A) | [solid] |

**Curatorial note:** the genuinely-local fast tier is **Qwen3-Coder-30B-A3B** (the standout: ~68 tok/s, ~18GB) and **gpt-oss-20b**. DeepSeek-V4-Flash is "fast" only as an API offering — its weights don't fit 64GB.

---

## D. FIM / code-completion (IDE autocomplete, fill-in-the-middle)

FIM is a distinct capability — you want a model *trained* for fill-in-the-middle and low latency, not a chat/agent model. Big agentic MoEs are the wrong tool here.

| Model | Params / arch | License | Get it | Runs on 64GB Mac? | Best at | Headline number | Source (date) | Conf |
|---|---|---|---|---|---|---|---|---|
| **Codestral 2** | 22B **dense**, 256K ctx, 80+ langs | **Apache-2.0** (relicensed Apr 2026) | `mistralai/` on HF · Ollama · Mistral API | **Yes** — 4-bit ~13GB | **Class-leading FIM for IDE autocomplete**; predictable VRAM as a dense model | 86.6% HumanEval; "class-leading FIM for open models" | [aitooltier Codestral 2](https://aitooltier.com/tools/codestral), [Mistral news](https://mistral.ai/news/codestral/) (2026-04-08) | [solid] |
| **Qwen2.5-Coder 1.5B / 7B** | 1.5B / 7B dense, FIM-trained | Apache-2.0 (7B; 1.5B Apache) | `Qwen/Qwen2.5-Coder-{1.5B,7B}` · Ollama | **Yes, trivially** | The autocomplete slot: 1.5B for tab-completion latency, 7B for chat | top-rated local coder family 2026 | [dev.to local-coding](https://dev.to/jovan_chan_9500711396d4e6/best-local-coding-llm-in-2026-qwen25-coder-vs-deepseek-coder-v2-vs-codestral-45g8) (2026) | [solid] |
| **Seed-Coder-8B-Base** | 8B dense | MIT | `ByteDance-Seed/Seed-Coder-8B-Base` | **Yes** | Small FIM/completion + base for fine-tuning | (see §B) | [HF Seed-Coder](https://huggingface.co/ByteDance-Seed/Seed-Coder-8B-Base) (2026) | [single-source] |
| **StarCoder2-15B** | 15B dense | OpenRAIL-M | `bigcode/starcoder2-15b` · Ollama | **Yes** — 4-bit ~9GB | Low-latency completion specialist; legacy but still cited | code-completion specialist | [labellerr roundup](https://www.labellerr.com/blog/best-coding-llms/) (2026) | [hearsay] |

**Recommendation for the FIM slot:** **Codestral 2** is the consensus best open FIM model (now Apache-2.0, which unblocks in-product use), with **Qwen2.5-Coder-1.5B** as the low-latency tab-completion companion. StarCoder2 is increasingly superseded.

---

## E. API-tier — open-weight but too big to run on 64GB (notable anyway)

Listed so you know what you're choosing *against* when you run local. All are downloadable open weights; none fit a 64GB Mac at usable quant.

| Model | Why API-tier | License | Headline | Source | Conf |
|---|---|---|---|---|---|
| **DeepSeek-V4-Pro** (1.6T-A49B) | 1.6T MoE; 4-bit ~400GB | MIT | **80.6% SWE-bench Verified** (open-weights leader, ties Gemini 3.1 Pro) | [HF blog](https://huggingface.co/blog/deepseekv4) | [solid] |
| **GLM-5.2** (~754B MoE) | server-class; 2-bit still ~241GB | MIT | **62.1 SWE-bench Pro** (beats GPT-5.5) | [VentureBeat](https://venturebeat.com/technology/z-ais-open-weights-glm-5-2-beats-gpt-5-5-on-multiple-long-horizon-coding-benchmarks-for-1-6th-the-cost) | [single-source] |
| **Kimi K2.7-Code** (1T-A32B) | 1T MoE, native INT4 still ~250GB+ | Modified MIT | +21.8% Kimi-Code-Bench v2 vs K2.6; agent-swarm to 300 sub-agents | [explainx](https://www.explainx.ai/blog/kimi-k2-7-code-open-source-coding-model-2026) | [single-source] |
| **Qwen3-Coder-480B-A35B** | 480B MoE | Apache-2.0 | ~Claude-Sonnet on agentic coding + browser-use | [HF](https://huggingface.co/Qwen/Qwen3-Coder-480B-A35B-Instruct) | [solid] |
| **Devstral 2** (123B dense) | 123B dense ~62GB at 4-bit, no context room | Modified MIT | 72.2% SWE-bench Verified | [VentureBeat](https://venturebeat.com/ai/mistral-launches-powerful-devstral-2-coding-model-including-open-source) | [solid] |
| **GLM-5 / 5.1** (745–754B) | server-class | MIT | GLM-5: 77.8% SWE-V; GLM-5.1: 58.4 SWE-bench Pro (SOTA at release) | [MarkTechPost GLM-5.1](https://www.marktechpost.com/2026/04/08/z-ai-introduces-glm-5-1-an-open-weight-754b-agentic-model-that-achieves-sota-on-swe-bench-pro-and-sustains-8-hour-autonomous-execution/) | [single-source] |

**Data-risk caveat (worth flagging):** GLM API usage has been noted as carrying China-data-handling considerations for some orgs; running the *weights* locally sidesteps that, but the local-runnable GLM tier is only the **Air** variants, not the SOTA full models. ([techtimes](https://www.techtimes.com/articles/318543/20260617/glm-52-open-weights-live-top-coding-benchmark-api-use-carries-china-data-risk.htm)) [single-source]

---

## Benchmark landscape (for grounding the numbers above)

- **SWE-bench Verified** (Python-heavy, real GitHub issues): open-weights leader is **DeepSeek-V4-Pro-Max at 80.6%**, tied with Gemini 3.1 Pro. GPT-5.5 closed-source leads overall (~88.7%). ([marc0.dev leaderboard](https://www.marc0.dev/en/leaderboard))
- **SWE-bench Pro** (harder long-horizon): **GLM-5.2 at 62.1** is the open SOTA, beating GPT-5.5 (58.6). ([VentureBeat](https://venturebeat.com/technology/z-ais-open-weights-glm-5-2-beats-gpt-5-5-on-multiple-long-horizon-coding-benchmarks-for-1-6th-the-cost))
- **Aider-Polyglot** (C++/Go/Java/JS/Python/Rust edit accuracy, 225 exercises): GPT-5 leads at 0.880; **DeepSeek-V3.2-Exp is the top open model at 0.745** (≈74.2%, between Claude Opus 4 and o4-mini) at ~1/100th GPT-5's cost. Note V3.2 is the prior gen — V4 entries are newer. ([llm-stats Aider-Polyglot](https://llm-stats.com/benchmarks/aider-polyglot), [agentmarketcap](https://agentmarketcap.ai/blog/2026/04/06/aider-polyglot-leaderboard-2026-swe-bench-python-bias))
- **LiveBench Coding** (May 2026 snapshot): DeepSeek-V4-Pro 69.99 coding / 56.67 agentic; Qwen3.6-27B 71.78 coding / 50.00 agentic; Devstral 2 66.79 / 43.33. ([pinggy roundup](https://pinggy.io/blog/best_open_source_self_hosted_llms_for_coding/))
- **LiveCodeBench v6:** GLM-4.6 reported 82.8%. ([intuitionlabs](https://intuitionlabs.ai/articles/glm-4-6-open-source-coding-model)) [single-source]

> **Methodology caveat:** several aggregator blogs (codersera, nxcode, miraflow, etc.) are SEO-style secondary sources, not primary leaderboards — hence the `[single-source]` flags on the very newest GLM-5.2 / Kimi-K2.7 / DeepSeek-V4 numbers. The HF model cards and vendor blogs (Qwen, Mistral, OpenAI) are primary and marked `[solid]`. Treat exact benchmark decimals as approximate; the *ordering* (DeepSeek-V4 / GLM-5.2 / Kimi at the open frontier; Qwen3.6-27B & Qwen3-Coder-Next as the local stars) is consistent across sources.

---

## Curated picks for a 64GB Apple-Silicon Mac (the practical answer)

1. **Daily agentic driver (best local):** `Qwen3-Coder-Next 80B-A3B` 4-bit MLX — strongest local agent brain that fits, ~20+ tok/s. If RAM pressure bites, drop to:
2. **Fast agent loops:** `Qwen3-Coder-30B-A3B` 4-bit MLX — ~68 tok/s, ~18GB, leaves huge context headroom. The best speed/quality tradeoff.
3. **Dense single-shot quality:** `Qwen3.6-27B` 4-bit — ~17GB, 77.2 SWE-V, beats a 397B MoE; the "one good answer" pick.
4. **IDE autocomplete (FIM):** `Codestral 2` 22B (Apache-2.0) + `Qwen2.5-Coder-1.5B` for tab latency.
5. **When local isn't enough:** `DeepSeek-V4-Pro` (80.6 SWE-V, OpenAI+Anthropic API compat → drops into Claude Code) or `GLM-5.2` (62.1 SWE-bench Pro).

**Borderline cases to know:** GLM-4.5-Air (106B-A12B, 4-bit ~40GB) *fits* but with thin headroom; gpt-oss-120b needs ~80GB → effectively too big; Devstral 2 (123B dense) and all the 480B+/1T MoEs are server/API-tier.
