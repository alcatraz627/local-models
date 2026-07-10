# Open-Weight General-Purpose / Reasoning / Instruction-Following LLM Landscape

**Survey date:** 2026-06-19 · **Researcher:** general-purpose agent (live web sources)
**Target deployment frame:** 64 GB Apple-Silicon Mac (~48 GB usable for weights+KV at 4-bit)

---

## TL;DR — what changed since early-2026 memory

- **Chinese labs own the open-weight frontier.** DeepSeek (V3.2 / V4 Pro), Moonshot
  (Kimi K2.6), Zhipu (GLM-5.x), Alibaba (Qwen3.5/3.6) hold ~4 of the top 5 open
  slots on Artificial Analysis + BenchLM. **Gemma 4 (Google) is the lone Western
  entry in the top tier.**
- **Kimi K2.6** is the single highest-scoring open-weight model on the Artificial
  Analysis Intelligence Index (**54**, ties GPT-5.5 on SWE-bench Pro) — but it's a
  1T-param MoE, **API-tier, not local on a Mac**.
- **Fast naming churn — verify the exact tag before pulling.** Qwen shipped
  3.5 (Feb 2026) → 3.6 (Apr 2026) → 3.7 (Jun 2026, multimodal). Zhipu shipped
  GLM-5 → 5.1 (Apr 7) → 5.2 open weights (Jun 16). Treat any specific version
  number below as "latest as of survey date," not stable.
- **The sweet spot for a 64 GB Mac is the ~30–35B MoE / 27–31B dense tier**
  (Qwen3.6-35B-A3B, Qwen3.6-27B, Gemma 4 31B, OLMo 3 32B, GLM-5 "Air"-class).
  The flagship 200B–1T MoEs do **not** fit at 4-bit.

---

## Confidence legend

`[solid]` corroborated across 2+ independent sources · `[single-source]` one
source only · `[hearsay]` rumor / unreleased / aggregator-only. Note: much of the
2026 data here comes from **aggregator/blog sources** (BenchLM, codersera,
llm-stats, Will-It-Run) rather than primary vendor pages I could fetch directly —
treat headline benchmark numbers as directional, not gospel.

---

## (1) Frontier-class open reasoning models — mostly API-tier / too big for a Mac

These define the open-weight ceiling. **None fit a 64 GB Mac at 4-bit** — listed
so you know what you're trading away by going local, and which you'd hit via API
or a multi-GPU box.

| Model | Params / arch | License | HF / tag | Run target | Best at | Headline bench | Source (date) | Conf |
|---|---|---|---|---|---|---|---|---|
| **Kimi K2.6** (Moonshot) | 1T MoE, **32B active**, MLA, 384+1 experts, 256K ctx | Modified MIT (free <100M MAU / <$20M/mo) | `moonshotai/Kimi-K2.6` (HF) | Multi-GPU / cloud (~0.5–1 TB) | Agentic coding, tool use, long-horizon agents | **AAII 54** (top open); ties GPT-5.5 on SWE-bench Pro 58.6%; HLE-w/tools 54.0% | [codersera](https://codersera.com/blog/kimi-k2-6-complete-guide-2026/), [llm-stats](https://llm-stats.com/models/kimi-k2.6) (Apr 2026) | [solid] |
| **DeepSeek V4 Pro (Max)** | ~671B+ MoE (V3.2 lineage), DeepSeek Sparse Attention | DeepSeek/MIT-class open weights | `deepseek-ai/*` (HF) | Multi-GPU / cloud | Overall general + coding leader | **BenchLM overall 87** (top open); coding blended 89.8 | [BenchLM](https://benchlm.ai/blog/posts/best-open-source-llm) (2026) | [single-source] |
| **DeepSeek-V3.2 / V3.2-Speciale** | 671B MoE, DSA sparse attn | open weights | `deepseek-ai/DeepSeek-V3.2` | Multi-GPU / cloud | Agentic + high-compute reasoning (IMO/IOI gold under relaxed budget) | comparable to GPT-5 on scalable-RL eval | [arXiv 2512.02556](https://arxiv.org/html/2512.02556v1) (Dec 2025) | [solid] |
| **GLM-5 / 5.1 / 5.2** (Zhipu/Z.ai) | ~745B MoE, **~44B active**, up to 1M ctx (5.2) | **MIT** | `zai-org/GLM-5` (HF; 5.1 open Apr 7, 5.2 Jun 16) | Multi-GPU / cloud (~400 GB) | Frontier reasoning + agentic coding; first open model to AAII ~50 | **AAII ~50** (GLM-5); GLM-5 SWE-bench Verified 77.8% | [HF blog](https://huggingface.co/blog/mlabonne/glm-5), [smartchunks](https://smartchunks.com/artificial-analysis-intelligence-index-april-2026-explained/) (Apr 2026) | [solid] |
| **Qwen3.5 397B-A17B** (Alibaba) | 397B MoE, **17B active** | Apache 2.0 | `Qwen/Qwen3.5-397B-A17B` | Multi-GPU / cloud | Broadest open generalist (reasoning + multilingual) | **BenchLM overall 77**; coding 86.7 | [codersera](https://codersera.com/blog/qwen-3-5-complete-guide-2026/), [BenchLM](https://benchlm.ai/blog/posts/best-open-source-llm) (Feb 2026) | [single-source] |
| **Mistral Large 3** | 675B MoE, **41B active** | open weights (Mistral) | `mistralai/*` (HF) | Multi-GPU / cloud | Western open MoE flagship; strong general/multilingual | flagship-tier 2026 (no single headline number corroborated) | [aiunpacking](https://aiunpacking.com/guides/open-source-ai-models-2026-llama-mistral-deepseek/) (Dec 2025) | [single-source] |
| **Llama 5** (Meta) | frontier open weights (size unconfirmed) | Llama Community (700M MAU cap) | `meta-llama/*` | likely multi-GPU | targeted at GPT-5 / Gemini 3 parity; Meta's open-frontier may be ending (Muse Spark ships closed) | parity claims, not independently benchmarked here | [theplanettools](https://theplanettools.ai/tools/llama-5), [digitalapplied](https://www.digitalapplied.com/blog/open-weight-model-q3-2026-projection-competitive-forecast) (Apr 2026) | [hearsay] |

> **DeepSeek R2** (the rumored consumer-grade 32B dense MIT reasoning model that
> *would* fit a Mac) is **NOT released as of 2026-06-19** — leak/rumor only.
> [decodethefuture](https://decodethefuture.org/en/deepseek-r2-explained/) `[hearsay]`

---

## (2) Mid-size general models that FIT a 64 GB Apple-Silicon Mac at 4-bit

This is the **practical local tier**. Rule of thumb on a 64 GB Mac (~48 GB usable):
dense ≤ ~34B and MoE ≤ ~120B-A10B-class fit at 4-bit with usable context. The
35B-A3B MoEs are the standout — near-instant (3B active) yet broadly capable.

| Model | Params / arch | License | HF / Ollama | Fits 64 GB @ 4-bit? | Best at | Headline bench | Source (date) | Conf |
|---|---|---|---|---|---|---|---|---|
| **Qwen3.6-35B-A3B** | 35B MoE, **3B active**, hybrid think, MM, ~260K ctx | Apache 2.0 | `Qwen/Qwen3.6-35B-A3B`; `ollama run qwen3.6:35b-a3b` | **YES — ~21 GB @ Q4**, big headroom (Q6 fits 64 GB) | Fast agentic coding + general; best speed/quality on a Mac | rivals Gemma4-31B; 27B sibling 77.2 SWE-bench Verified | [Will-It-Run](https://willitrunai.com/blog/qwen-3-5-35b-a3b-vram-requirements), [qwen.ai](https://qwen.ai/blog?id=qwen3.6-35b-a3b) (Apr 2026) | [solid] |
| **Qwen3.6-27B (dense)** | 27B dense, hybrid thinking, MM | Apache 2.0 | `Qwen/Qwen3.6-27B`; `ollama run qwen3.6:27b` | **YES — ~16–18 GB @ Q4** | Best *quality* in the local tier for math/code/reasoning; pick over 35B-A3B when you want depth over speed | ties Sonnet 4.6 on AA Agentic Index; **77.2 SWE-bench Verified** | [localclaw](https://localclaw.io/blog/qwen3-6-27b-deep-dive), [llm-stats](https://llm-stats.com/models/qwen3.6-35b-a3b) (Apr 2026) | [single-source] |
| **Gemma 4 31B (dense)** | 31B dense, multimodal | Apache 2.0 | `google/gemma-4-31b`; `ollama run gemma4:31b` | **YES — ~18–20 GB @ Q4** | Strongest Western open generalist; "31B beats 400B rivals" framing | **MMLU-Pro 85.2**, AIME-2026 89.2, LiveCodeBench-v6 80.0, Arena 1452 | [codersera](https://codersera.com/blog/gemma-4-complete-guide-2026/), [startuphub](https://www.startuphub.ai/ai-news/ai-research/2026/google-gemma-4-review-2026) (Apr 2026) | [solid] |
| **Gemma 4 26B-A4B (MoE)** | 26B MoE, **~3.8B active**, MM | Apache 2.0 | `google/gemma-4-26b-a4b`; `ollama run gemma4:26b` | **YES — ~15 GB @ Q4** | Near-31B quality at MoE speed | AIME-2026 88.3 @ 3.8B active; Arena 1441 | [tech-insider](https://tech-insider.org/google-gemma-4-open-model-benchmarks-2026/) (Apr 2026) | [single-source] |
| **OLMo 3-Think 32B** (Ai2) | 32B dense, reasoning | Apache 2.0 (**fully open**: data+code+logs) | `allenai/OLMo-3-Think-32B`; `ollama run olmo3:32b` | **YES — ~19 GB @ Q4** | Best *fully reproducible* model; auditable pipeline; research / provenance-sensitive use | strongest fully-open thinking model; near Qwen3-32B on AIME/GPQA at ~6× fewer train tokens | [allenai](https://allenai.org/blog/olmo3), [interconnects](https://www.interconnects.ai/p/olmo-3-americas-truly-open) (Nov 2025) | [solid] |
| **Qwen3.5-122B-A10B** | 122B MoE, **10B active** | Apache 2.0 | `Qwen/Qwen3.5-122B-A10B` | **MARGINAL — ~74 GB @ Q4** → needs 96–128 GB; **NOT a 64 GB fit** | Heaviest "almost-local" tier (Mac Studio 128 GB) | strong generalist between 35B and 397B | [Will-It-Run](https://willitrunai.com/blog/qwen-3-5-122b-a10b-vram-requirements) (2026) | [solid] |

> **Do NOT expect Qwen3 235B-A22B or any 200B+ MoE on a 64 GB Mac** — 235B needs
> **~132 GB @ Q4**. The 122B-A10B is the ceiling, and it wants ≥96 GB.
> [Will-It-Run](https://willitrunai.com/blog/qwen-3-gpu-requirements) `[solid]`

---

## (3) Small / edge models (≤8B) — fast local + on-device

For sub-second responses, on-device phones/tablets, and "instant" local agents.
All fit a Mac trivially (a few GB); the interest is phone/edge feasibility.

| Model | Params / arch | License | HF / Ollama | Edge target | Best at | Headline bench | Source (date) | Conf |
|---|---|---|---|---|---|---|---|---|
| **Gemma 4 E4B** | ~4.5B effective, MM (audio+vision), Thinking Mode | Apache 2.0 | `google/gemma-4-e4b`; `ollama run gemma4:e4b` | ~2–3 GB @ Q4; phones/tablets | Best all-round on-device multimodal (audio+vision+function-calling on a phone) | strongest sub-8B multimodal edge model | [mindstudio](https://www.mindstudio.ai/blog/gemma-4-e2b-vs-e4b-edge-models-audio-vision-phone) (Apr 2026) | [solid] |
| **Gemma 4 E2B** | ~2.3B effective | Apache 2.0 | `google/gemma-4-e2b`; `ollama run gemma4:e2b` | ~1–1.5 GB @ Q4; CPU-only, sub-2 GB | Smallest viable; runs CPU-only (no Thinking/MM) | ultra-light edge | [gemma4.dev](https://gemma4.dev/models/gemma-4-e2b) (Apr 2026) | [solid] |
| **Qwen3.5-9B (dense)** | 9B dense (best 8B-class dense) | Apache 2.0 | `Qwen/Qwen3.5-9B`; `ollama run qwen3.5:9b` | ~6 GB @ Q4 | Strongest small dense generalist + code | top-of-class small dense (8B bracket) | [Will-It-Run](https://willitrunai.com/blog/qwen-3-5-9b-vram-requirements) (2026) | [single-source] |
| **Qwen3-8B** (prior gen, mature) | 8B dense | Apache 2.0 | `Qwen/Qwen3-8B`; `ollama run qwen3:8b` | ~5 GB @ Q4 | Battle-tested, widest tooling support | HumanEval ~76 (best <8B for code, Qwen3-7B line) | [bentoml](https://www.bentoml.com/blog/the-best-open-source-small-language-models) (2026) | [solid] |
| **Phi-4-mini (3.8B)** (Microsoft) | 3.8B dense | MIT | `microsoft/Phi-4-mini`; `ollama run phi4-mini` | ~3 GB @ Q4; 8 GB-RAM machines | Best reasoning-per-param at the very low end | GSM8K 88.6, ARC-C 83.7; ~22 tok/s on M4 Air | [localaimaster](https://localaimaster.com/blog/small-language-models-guide-2026), [bentoml](https://www.bentoml.com/blog/the-best-open-source-small-language-models) (2026) | [solid] |
| **OLMo 3-Instruct 7B** (Ai2) | 7B dense, fully open | Apache 2.0 | `allenai/OLMo-3-Instruct-7B`; `ollama run olmo3:7b` | ~5 GB @ Q4 | Fully-open small chat model; matches Qwen2.5/Gemma3/Llama3.1 7-8B | competitive 7B instruct | [allenai](https://allenai.org/blog/olmo3) (Nov 2025) | [solid] |

> **Phi-5 (Microsoft):** no confirmed 2026 release found at survey time. Phi-4-mini
> remains the current Phi edge pick. `[hearsay]` on any Phi-5.

---

## (4) Best open "writer" / prose models

EQ-Bench Creative Writing is the reference. Top of the board is closed (Claude
Fable 5 ~2189, Opus 4.7 ~2184). Among **open weights**, the writers are the same
big Chinese MoEs — so good local prose means the ~30B local tier, not the
chart-toppers.

| Model | Why it writes well | License / runnable locally? | EQ-Bench Creative | Source (date) | Conf |
|---|---|---|---|---|---|
| **Kimi K2.6** (Moonshot) | **Best open-weight prose**; near-frontier voice & coherence | Mod-MIT; **API-tier, not local** | **~1753** (top open) | [eqbench-derived](https://eqbench.com/creative_writing.html), [search synthesis] (Apr 2026) | [single-source] |
| **Kimi K2** (orig) | Strong narrative; cheaper | Mod-MIT; API-tier | ~1691 | same | [single-source] |
| **GLM-5** (Zhipu) | High creative + good instruction-following for style control | MIT; API-tier (745B) | ~1657 creative / ~1533 general | same | [single-source] |
| **Qwen3.6-27B / 35B-A3B** | **Best *locally-runnable* writer** on a 64 GB Mac; strong style range, hybrid thinking for outlining | Apache 2.0; **fits 64 GB** | not separately scored in sources; inherits Qwen prose quality | [intellectualead](https://intellectualead.com/best-llm-writing/) (2026) | [hearsay] |
| **Gemma 4 31B** | Clean, controllable prose; strong IFEval lineage (Gemma has historically been a tidy writer) | Apache 2.0; **fits 64 GB** | not separately scored; inferred from Gemma writing reputation | [evy.so](https://evy.so/compare/best-llms-for-writing/) (2026) | [hearsay] |

> **Local-writer takeaway:** the chart-leading open writers (Kimi/GLM) are too big
> for a Mac. For *local* prose, **Qwen3.6-27B** (depth) or **Gemma 4 31B**
> (clean/controllable) are the realistic picks; treat their writing rank as
> inferred, not benchmarked.

---

## (5) Reasoning-specialist ("thinking" / chain-of-thought) models

Hybrid-thinking is now standard (Qwen/Gemma/GLM toggle think on/off). The dedicated
reasoning specialists:

| Model | Params / arch | License | Fits 64 GB @ 4-bit? | Best at | Headline bench | Source (date) | Conf |
|---|---|---|---|---|---|---|---|
| **DeepSeek-V3.2-Speciale** | 671B MoE, high-compute reasoning variant | open weights | **No** (cloud) | Competition-grade math/proof (IMO/IOI gold under relaxed budget) | gold-medal IMO/IOI 2025 | [arXiv 2512.02556](https://arxiv.org/html/2512.02556v1) (Dec 2025) | [solid] |
| **DeepSeek R1** (mature) | 671B MoE reasoning | MIT | **No** (cloud) | Pure math reasoning | **MATH-500 97.3** | [BenchLM](https://benchlm.ai/blog/posts/best-open-source-llm) (2025) | [solid] |
| **OLMo 3-Think 32B** (Ai2) | 32B dense reasoning | Apache 2.0 (fully open) | **YES — ~19 GB @ Q4** | **Best LOCAL reasoning specialist**; auditable RL pipeline | strongest fully-open thinking model; near Qwen3-32B on AIME/GPQA | [allenai](https://allenai.org/blog/olmo3) (Nov 2025) | [solid] |
| **Qwen3.6-27B (thinking mode)** | 27B dense, hybrid | Apache 2.0 | **YES — ~17 GB @ Q4** | Best *general-purpose* local reasoner; toggle thinking for math/code | 77.2 SWE-bench Verified; benefits from larger think budgets | [localclaw](https://localclaw.io/blog/qwen3-6-27b-deep-dive) (Apr 2026) | [single-source] |
| **GLM-5 (reasoning)** | 745B MoE | MIT | **No** (cloud) | Frontier open reasoning + agentic | BenchLM 79–83 reasoning tier | [BenchLM](https://benchlm.ai/blog/posts/best-open-source-llm) (2026) | [single-source] |
| **DeepSeek R2** (rumored 32B dense, MIT) | 32B dense | MIT (rumored) | would be **YES** | consumer reasoning (if it ships) | rumored 92.7 AIME | [decodethefuture](https://decodethefuture.org/en/deepseek-r2-explained/) | [hearsay — UNRELEASED] |

> **Local reasoning takeaway:** **OLMo 3-Think 32B** and **Qwen3.6-27B (thinking
> on)** are the two reasoning specialists that actually fit a 64 GB Mac. Everything
> frontier-tier (DeepSeek-Speciale, R1, GLM-5) is cloud/API.

---

## Long-context note

- **Context windows have ballooned in 2026.** Qwen3.5/3.6 ship ~260K native;
  **Qwen3.7 Plus and GLM-5.2 advertise 1M-token** windows; Kimi K2.6 is 262K.
  DeepSeek's **Sparse Attention (DSA)** and Kimi's **MLA** are the enabling tricks —
  they cut KV/attention cost so long context is affordable.
  [chatforest](https://chatforest.com/builders-log/zhipu-glm-5-2-1m-context-open-weights-agentic-coding-builder-guide/),
  [arXiv 2512.02556](https://arxiv.org/html/2512.02556v1) `[solid]`
- **On a Mac, context is a memory tax.** The headline 1M windows are a cloud/API
  story. Locally, KV cache eats unified memory fast — running Qwen3.6-27B/35B-A3B
  at 4-bit, budget realistically for **32K–128K** effective context before KV
  cache competes with weights for your ~48 GB. The big windows exist in the
  weights; your RAM caps what you can actually fill. `[single-source / reasoned]`

---

## Practical shortlist for a 64 GB Apple-Silicon Mac

| Need | Pick | Why |
|---|---|---|
| **Default daily driver (speed)** | **Qwen3.6-35B-A3B** @ Q4/Q6 | 3B active = fast; broad capability; huge headroom |
| **Best local quality** | **Qwen3.6-27B** or **Gemma 4 31B** @ Q4 | dense depth for math/code/reasoning/prose |
| **Local reasoning specialist** | **OLMo 3-Think 32B** (fully open) or Qwen3.6-27B (think on) | auditable / general |
| **Fast + on-device / phone** | **Gemma 4 E4B** (MM) · **Phi-4-mini** (reasoning) · **Qwen3.5-9B** (dense quality) | small footprint |
| **Local prose** | **Qwen3.6-27B** / **Gemma 4 31B** | chart-leaders (Kimi/GLM) are too big |
| **Reach for API/cloud (not local)** | **Kimi K2.6** (agentic+writing), **DeepSeek V4 Pro / V3.2**, **GLM-5.x** | frontier open weights, 200B–1T MoE |

---

## Caveats / verification flags

1. **Naming churn is severe.** Qwen 3.5→3.6→3.7 and GLM 5→5.1→5.2 all shipped
   within months. **Confirm the exact HF tag and its size before pulling** — Ollama
   tags above are best-effort and may differ from the published repo name.
2. **Benchmark numbers are aggregator-sourced.** BenchLM/codersera/Will-It-Run/
   llm-stats, not primary vendor evals I could fetch. Directional, not precise.
3. **VRAM figures @ Q4** are weights-only estimates; **add KV cache + macOS overhead**
   (~10–14 GB reserve on a 64 GB machine). The "fits" calls assume that reserve.
4. **EQ-Bench open-weight writer scores** were synthesized from search snippets, not
   read off the live table (couldn't fetch it cleanly) — `[single-source]`/`[hearsay]`.
5. **DeepSeek R2** and **Phi-5** are unconfirmed/unreleased as of 2026-06-19.
