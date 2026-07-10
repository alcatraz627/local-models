# Agentic Judgment & Reliability Benchmarks — Survey

**Date:** 2026-06-19
**Question:** Which benchmarks measure what actually matters for an agentic local model — **reliability** (consistent, non-flaky behavior), **tool-decision judgment** (when to call / not call a tool, when to search/delegate), and **long-horizon coherence** (not degrading over many steps)? Explicitly NOT raw speed or math/accuracy.

**Reader context:** runs open-weight models locally on a 64GB Mac. Open-weight standings are flagged throughout.

---

## TL;DR — the four benchmarks that actually map to the user's axes

| Benchmark | Axis it measures | The metric that matters | Open-weight at top? | Confidence |
|---|---|---|---|---|
| **τ²-bench (tau2)** | Reliability + tool-decision | **pass^k** (succeed k times *in a row*) | YES — **GLM-4.7 #2 @ 87.4%**, Qwen3.5 top-8 | [solid] |
| **BFCL v4** | Tool-decision (incl. *irrelevance detection* = when NOT to call) | Irrelevance accuracy + multi-turn + agentic | Partial — open RL models (Qwen-based FunRL/GRPO) competitive | [solid] |
| **Vending-Bench 2** | Long-horizon coherence | Final balance over a *simulated year*; derail/meltdown rate | Not yet — Claude Opus 4.6 leads; open models largely untested | [solid] |
| **MCPMark / MCP-Atlas** | Real MCP tool-use under depth | pass@1 / **pass@4** | Mid-pack — Kimi K2.6 best OSS (~0.56), DeepSeek v3.2 #8 | [solid] |

**The single most important concept for the user: `pass^k`.** See first section.

---

## 1. τ-bench / τ²-bench (Sierra Research) — THE reliability benchmark

**What it measures:** Conversational tool-agent behavior in realistic customer-service domains (retail, airline; τ² adds telecom, voice, knowledge-retrieval). The agent must follow domain-specific rules, use tools against a database, and interact with a (simulated) user. τ² adds a **dual-control** framework where *both* agent and user have tools to observe/modify state — closer to real collaboration.

**Maps to:** **Reliability** (primary) + **tool-decision** + some long-horizon (multi-turn dialogues).

### Why `pass^k` is exactly the signal the user wants

- **pass@k** = "succeeded at least once in k tries" — rewards lucky one-offs. This is the *wrong* metric for someone who cares about not flaking.
- **pass^k** = "succeeded in **all** k independent tries" — penalizes intermittent correctness. This is the **reliability** metric.
- Math: pass^k = p^k decays exponentially. A model at **90% pass@1 drops to ~57% at pass^8**. A headline "90% benchmark" can mean **~70% real-world reliability** when the same task is retried by different sessions. [solid]
- Per the meta-analysis: "agent variance per run is large — pass^4 scores often run 15–25 points below pass^1." **Almost no other benchmark reports pass^k** — this is τ-bench's distinguishing contribution. [solid]

> **Practical takeaway for local use:** when comparing two local models, a higher pass^1 with a steep pass^k cliff is *worse* than a slightly lower pass^1 that holds steady across k. Reliability = the *flatness* of the pass^k curve, not the headline.

### Leaderboard (taubench.com / Sierra, mirrored on Steel.dev + llm-stats, captured Jun 19 2026 / Apr 16 2026)

| Rank | Model | Score | Open-weight? |
|---|---|---|---|
| 1 | Step-3.5-Flash (StepFun) | 88.2% | (weights status unclear) |
| 2 | **GLM-4.7 (Z.ai/Zhipu)** | **87.4%** | **YES — open weight** |
| 3 | MiMo-V2-Flash (Xiaomi) | 80.3% | (likely open) |
| 4 | **GLM-4.7-Flash** | 79.5% | **YES** |
| 5 | MiniMax M2 | 77.2% | YES (open) |
| 6 | Claude Opus 4.5 | 70.2% | no |
| 7 | GPT-5.2 | 69.9% | no |
| 8 | **Qwen3.5-397B-A17B** | 68.4% | **YES** (MoE, 17B active — too big for 64GB though) |

**Open-weight verdict:** Strongest single benchmark for open models. **GLM-4.7 beats Claude Opus 4.5 and GPT-5.2 here.** GLM-4.7-Flash (smaller) is the more 64GB-relevant entry at 79.5%. Note: the 397B Qwen and full GLM-4.7 exceed 64GB; look at *-Flash / distilled variants.

- Leaderboard: https://leaderboard.steel.dev/leaderboards/tau-bench/ · https://llm-stats.com/benchmarks/tau-bench · official taubench.com
- Repo / release notes: https://github.com/sierra-research/tau2-bench
- Confidence: **[solid]** (multiple corroborating sources, recent dates)

---

## 2. BFCL v4 (Berkeley Function-Calling Leaderboard) — tool-decision, incl. "knowing NOT to call"

**What it measures:** Function/tool-calling correctness via AST-matching and (v4) **holistic agentic + multi-turn** evaluation. Crucially includes **Irrelevance Detection**: scenarios where *no* provided tool is relevant and the model is scored on **NOT** emitting a tool call (it should explain or answer directly instead).

**Maps to:** **Tool-decision judgment** (primary) — this is the clearest measure of "knows when to use a tool vs. answer directly / refrain." The irrelevance category is exactly the "don't over-tool" discipline.

**Metric:** Overall accuracy = unweighted average of sub-categories (simple/parallel/multiple function, multi-turn, irrelevance, agentic). Watch the **irrelevance** sub-score specifically — a model can score high overall but be trigger-happy (low irrelevance accuracy = calls tools when it shouldn't).

**Open-weight standing:** [solid] As of Feb–Mar 2026, RL-tuned open approaches (GRPO, reward-conditioning, **FunRL**, **RC-GRPO**) "match or exceed proprietary systems." These are typically Qwen-based. So open-weight is genuinely competitive on *function-calling correctness* specifically.

- Live leaderboard: https://gorilla.cs.berkeley.edu/leaderboard.html (Last updated **2026-04-12**)
- Overview: https://www.emergentmind.com/topics/berkeley-function-calling-leaderboard-v4-bfclv4
- Dataset: https://huggingface.co/datasets/gorilla-llm/Berkeley-Function-Calling-Leaderboard
- Confidence: **[solid]** for structure/dates; **[single-source]** for the specific open-model-parity claim (couldn't render the numeric table — recommend the user open the live page to read per-model irrelevance scores)

---

## 3. MCPMark & MCP-Atlas — realistic MCP tool-use (deep, multi-step)

**MCPMark** (OpenReview `uobROwBsJm`): 127 tasks across **Notion, GitHub, Filesystem, PostgreSQL, Playwright** — deliberately write-heavy and interaction-deep, unlike older read-only MCP benchmarks.

**Maps to:** **Tool-decision + reliability** (reports pass@4) + multi-step execution.

**Leaderboard (mcpmark.ai, updated 2025-12-15):**

| Rank | Model | pass@1 | pass@4 | Open? |
|---|---|---|---|---|
| 1 | gpt-5.2 | 57.5% | 66.9% | no |
| 2 | gemini-3-pro | 53.9% | 66.9% | no |
| 3 | gpt-5 (medium) | 52.6% | 68.5% | no |
| 8 | **DeepSeek v3.2** | 36.8% | — | **YES** |
| 19 | **Qwen-3-coder-plus** | 24.8% | — | **YES** |
| 21–24 | **Kimi-k2** variants | 19–22% | — | **YES** |
| 30 | **GLM-4.5** | 15.6% | — | **YES** |

**The key finding here is the absolute numbers:** best model ~52% pass@1 → **33.86% pass@4**. Strong models (Claude Sonnet 4, o3) fall **below 30% pass@1 / 15% pass@4**. This benchmark exposes how *unreliable* MCP tool-use still is across the board — and the pass@4 cliff is the reliability signal. Open models lag badly here. [solid]

**MCP-Atlas (Scale Labs, updated Apr 2026):** larger; Gemini 3.5 Flash leads at 0.836 across 25 models; budget changed to 100 tool calls/task. A separate "MCP-Mark" tracker (llm-stats) shows **Kimi K2.6 as best open-source at 0.559** (and cheapest top performer). [solid]

- https://mcpmark.ai/leaderboard · https://labs.scale.com/leaderboard/mcp_atlas · https://llm-stats.com/benchmarks/mcp-mark
- Confidence: **[solid]**

---

## 4. Vending-Bench / Vending-Bench 2 (Andon Labs) — THE long-horizon coherence benchmark

**What it measures:** Run a simulated vending-machine business over a **very long horizon** (original: >20M tokens/run; VB2: a simulated **year**, starting with $500). Each sub-task is trivial (order stock, set prices, pay daily fees) but coherence over thousands of steps is the challenge.

**Maps to:** **Long-horizon coherence** (primary) — directly the "doesn't do dumb things over many steps" axis the user named.

**Key findings (the most useful insight in this whole survey):** [solid]
- Models that *eventually* derail do so via **misreading delivery schedules, forgetting past orders, or descending into tangential "meltdown" loops** they rarely recover from.
- **Failures do NOT correlate with context-window fill** — i.e. this is a *reasoning-coherence* failure, not a memory-capacity one. Bigger context won't fix it.
- VB2 leaderboard: **Claude Opus 4.6 leads at ~$8,017 final balance**; Gemini 3 Pro ~$5,500. (Original paper: Claude 3.5 Sonnet & o3-mini were the steady performers.)
- Caveat: a "maximize profit at all costs" variant produced **emergent collusion/price-fixing** between agents — a *safety/alignment* signal worth knowing.

**Open-weight verdict:** Open models are largely **untested / not on the public VB2 board** — this is a gap. If long-horizon coherence is the user's top concern for local models, **there is no good open-weight number to lean on yet** — they'd have to run VB-Arena themselves.

- https://andonlabs.com/evals/vending-bench-2 · https://andonlabs.com/evals/vending-bench-arena · paper https://arxiv.org/abs/2502.15840 · https://llm-stats.com/benchmarks/vending-bench-2
- Confidence: **[solid]** for findings; **[single-source]** for the exact VB2 dollar figures (one tracker)

---

## 5. GAIA / BrowseComp / AssistantBench — "knowing when to search/research"

**GAIA:** real-world assistant tasks that are easy for humans but need multi-step reasoning + web browsing + tool use. **Maps to:** tool/search-decision + multi-step.

> **Important caveat — mostly IGNORE GAIA's top of leaderboard for model comparison.** [solid] The top GAIA entries (92.36% OPS-Agentic-Search, openJiuwen-deepagent, Lemon Agent) are **orchestrated multi-model ensembles / scaffolds**, NOT raw model calls. The board "rewards tool selection, search depth, verification, answer formatting" — you **cannot attribute the score to one base model**, let alone an open-weight one you'd run locally. Raw single-model GAIA (e.g. GPT-5 Mini ~44.8%, Claude 3.7 Sonnet ~43.9%) is the number to compare, not the 90%+ ensembles.

**BrowseComp (OpenAI):** 1,266 short-answer questions where the answer is *easy to verify once found but hard to locate* — tests **persistent, deep web research**. Maps to "when to keep searching." Current leader: GPT-5.5 Pro. Open-weight standing: not prominent. [single-source]

**AssistantBench:** realistic time-consuming web tasks; less live-leaderboard signal in 2026 sources — **lower priority**, largely superseded by GAIA/BrowseComp in attention. [hearsay]

- https://leaderboard.steel.dev/leaderboards/gaia/ (updated Apr 16 2026) · https://huggingface.co/spaces/gaia-benchmark/leaderboard
- Confidence: GAIA **[solid]**, BrowseComp **[single-source]**, AssistantBench **[hearsay]**

---

## 6. Multi-step execution boards (Terminal-Bench, WebArena, AgentBench) — useful but read with care

| Benchmark | What / maps to | 2026 standing | Open-weight |
|---|---|---|---|
| **Terminal-Bench** | Shell agents on containerized Linux; **89 tasks × 5 attempts each** (the ×5 gives a reliability read). Maps to multi-step execution + reliability. | 101 agents / 23 scaffolds | mixed (scaffold-dependent) |
| **WebArena / VisualWebArena** | Web-navigation agents, 812 tasks. Maps to multi-step + tool-decision. | Claude Mythos Preview 68.7%, GPT-5.4 Pro 65.8%; human ~78% | **A3-Qwen3.5-9B = 42.1%** — best open-weight, +20.4pt jump; **9B fits 64GB easily** [solid] |
| **AgentBench (THUDM)** | 8 environments. Maps to broad agentic. | aggregate scores **hide per-environment failures** — read sub-scores | open models present |

> **Critical reliability caveat on this whole family** [solid]: A **2026 Berkeley RDI study** found that **eight major agent benchmarks — incl. SWE-bench Verified, Terminal-Bench, WebArena, OSWorld, GAIA, FieldWorkArena — could be gamed to near-perfect scores WITHOUT solving any tasks**, via leaked reference answers, unsanitized `eval()`, prompt-injectable LLM judges, and scoring functions that skip correctness checks. **Treat any single headline number on these boards with suspicion; prefer benchmarks with adversarial/verified scoring (τ², BFCL AST-matching).**

- https://benchmarkingagents.com/agent-benchmarks/ · https://leaderboard.steel.dev/
- Confidence: **[solid]** (incl. the exploitation study)

---

## 7. Function-call / tool boards: ACEBench, NexusBench, ToolSandbox

| Benchmark | What it adds | Maps to | Open-weight | Confidence |
|---|---|---|---|---|
| **ACEBench** | 4,538 APIs, 8 domains, EN+CN. **"Special" category = ambiguous/incomplete instructions** (tests asking-vs-guessing); "Agent" = multi-agent dialogue. | tool-decision + *calibration* (handling ambiguity) | **Qwen2.5-Coder-32B = 80%** vs GPT-4 86% — strong, and **32B fits 64GB** | [solid] |
| **NexusBench** (Nexusflow) | function-call / tool-use / agent suite | tool-decision | open suite | [single-source] |
| **ToolSandbox** | stateful, conversational, multi-turn tool use w/ implicit state dependencies | tool-decision + reliability | — | [hearsay] (no fresh 2026 leaderboard surfaced) |

ACEBench's **"Special" (ambiguous-instruction) category** is the underrated one for the user's "knowing when to ask vs. act" concern — it's the closest thing to a *calibration* metric in the tool-use family. [solid]

- https://github.com/ACEBench/ACEBench · https://llm-stats.com/benchmarks/acebench · https://github.com/nexusflowai/NexusBench

---

## 8. Agent Arena & GDPval — newest signals

**Agent Arena (LMArena, launched Jun 4 2026):** [solid] Ranks models on **real-world agentic evals at scale**, measuring **behavioral signals — file downloads, disapproval events, retries, steerability** — not static benchmark scores or preference votes. This is conceptually the closest to "does it behave well as an agent, reliably." Actively adding models (Kimi K2.7 Code, MiniMax M3, GLM 5.2 Max, Claude Opus 4.8, GPT-5.5 as of mid-Jun 2026).
- **Key open-weight insight:** open-weight models **retry 30–40% more often on agentic workloads** — a direct *reliability/efficiency* gap that Elo scores hide. Seven open-weight models now sit in LMArena top-25 (GLM-4.7 first into top-10 on Text+WebDev), Elo gap to Claude Opus 4.6 narrowed to 25–42 pts. [solid]
- https://arena.ai/blog/leaderboard-changelog/

**GDPval (OpenAI, Oct 2025; GDPval-AA v2 on Artificial Analysis):** 1,320 tasks (220 open gold subset) across 44 occupations producing real deliverables (docs, slides, spreadsheets). **Maps to:** real-economic-value output quality, *not* reliability/tool-decision per se — frontier models approaching expert quality, ~100× faster/cheaper. Useful as an "is the output actually good" check, less so for the user's three axes. [solid]
- https://artificialanalysis.ai/evaluations/gdpval-aa · https://arxiv.org/abs/2510.04374

---

## What to IGNORE (so the user doesn't chase the wrong numbers)

- **GAIA/SWE-bench/Terminal-Bench/WebArena *headline* top scores** — gameable (Berkeley RDI 2026) and/or ensemble-scaffold scores not attributable to a runnable single model. Use them only via verified sub-scores or single-model rows.
- **Pure pass@1 / pass@k (lowercase) leaderboards** for reliability claims — they reward lucky one-offs. **Insist on pass^k (caret) or pass@4-with-the-cliff-shown.**
- **GDPval / math / accuracy boards** for the user's question — they measure output quality and knowledge, not judgment/coherence/reliability.
- **LMArena Elo (chat)** for agentic reliability — Elo hides the 30–40% extra-retry gap. Use **Agent Arena**, not chat Elo, for agent behavior.

---

## Bottom line for a 64GB-Mac open-weight operator

1. **Reliability:** lean on **τ²-bench pass^k**. Best runnable-ish open option signaled: **GLM-4.7-Flash** (79.5%, beats GPT-5.2's full-size 69.9% on the headline; verify the Flash variant fits 64GB). Qwen3.5/full-GLM are too big.
2. **Knowing when NOT to tool:** **BFCL v4 irrelevance sub-score** + **ACEBench "Special."** Open Qwen-based RL models competitive.
3. **Long-horizon coherence:** **Vending-Bench 2** is the right test but **open models are largely unbenchmarked** — biggest evidence gap; consider self-running VB-Arena.
4. **MCP tool-use:** sobering — even best models ~33% pass@4. Best OSS: **Kimi K2.6 (~0.56 MCP-Atlas)**, DeepSeek v3.2.
5. **Web/research-decision:** **A3-Qwen3.5-9B (42% WebArena)** is the standout *small* open model that genuinely fits 64GB.
6. **Treat any single headline with the Berkeley-RDI gameability caveat** — prefer benchmarks with adversarial/AST/verified scoring.

---

## Source index

- τ-bench/τ²: https://github.com/sierra-research/tau2-bench · https://leaderboard.steel.dev/leaderboards/tau-bench/ · https://llm-stats.com/benchmarks/tau-bench
- pass^k analysis: https://medium.com/alan/benchmarking-ai-agents-stop-trusting-headline-scores-start-measuring-trade-offs-0fdae3a418cf
- BFCL v4: https://gorilla.cs.berkeley.edu/leaderboard.html · https://www.emergentmind.com/topics/berkeley-function-calling-leaderboard-v4-bfclv4
- MCPMark: https://mcpmark.ai/leaderboard · https://openreview.net/forum?id=uobROwBsJm · MCP-Atlas https://labs.scale.com/leaderboard/mcp_atlas
- Vending-Bench: https://andonlabs.com/evals/vending-bench-2 · https://arxiv.org/abs/2502.15840
- GAIA: https://leaderboard.steel.dev/leaderboards/gaia/ · BrowseComp (OpenAI)
- Terminal-Bench/WebArena/AgentBench + gameability study: https://benchmarkingagents.com/agent-benchmarks/ · https://leaderboard.steel.dev/
- ACEBench: https://github.com/ACEBench/ACEBench · https://llm-stats.com/benchmarks/acebench
- NexusBench: https://github.com/nexusflowai/NexusBench
- Agent Arena: https://arena.ai/blog/leaderboard-changelog/
- GDPval: https://artificialanalysis.ai/evaluations/gdpval-aa · https://arxiv.org/abs/2510.04374
