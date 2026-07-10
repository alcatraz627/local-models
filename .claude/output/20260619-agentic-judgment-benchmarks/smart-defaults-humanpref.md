# Benchmarks & human-preference signals for "smart defaults / sensible commonsense judgment"

Research date: 2026-06-19. Sources are LIVE web (WebSearch/WebFetch), not memory.
User context: runs local models on a 64 GB Mac → open-weight standings called out throughout.

## TL;DR — which benchmarks actually map to the axis

The user axis is **"the model made the sensible default / smart assumption / good commonsense
judgment"** — and, by extension, the metacognition pair: *asking a good question when it should*
vs *making a sensible default when it shouldn't ask*.

- **General human-preference arenas (LMArena, Arena-Hard, WildBench, MixEval-Hard) do NOT
  cleanly map to this axis.** They measure aggregate "which answer is better," which conflates
  smart-defaults with verbosity, formatting, and tone. They are **"vibes + style" preference**,
  heavily length/markdown-biased, and reward *over-answering* (the opposite of "ask when
  ambiguous"). Use them as a weak general-quality proxy only. **FLAGGED as WRONG-thing for
  smart-defaults.**
- **The benchmarks that DO map are the abstention / clarification / pragmatics cluster**:
  **AbstentionBench, QuestBench, CLAMBER, ConfuseBench** (ask-vs-assume), and **PUB / PragmEval /
  Social IQa** (commonsense + pragmatic default inference). These directly test "don't confidently
  answer a false-premise / underspecified question" and "infer the intended meaning." This is the
  real proxy for the user's axis.
- **Key, counterintuitive finding** (AbstentionBench, Jun 2025): *reasoning fine-tuning makes
  models WORSE at abstaining (−24% avg)* — they hallucinate the missing context instead of flagging
  it. So a higher score on the math/reasoning leaderboards can **anti-correlate** with "sensible
  default under ambiguity." This is the single most important takeaway for the user.

---

## Part A — Human-preference arenas (general "vibes", weak map to the axis)

| Benchmark | What it measures | Maps to smart-defaults? | Metric |
|---|---|---|---|
| **LMArena** (ex-Chatbot Arena) | Aggregate human pairwise preference over real chats; "which of two anonymous answers is better" | **NO — general vibes.** Conflates correctness, tone, formatting, length. "Hard Prompts" / "Arena Expert" sub-categories filter to harder prompts but still measure overall-better, not assumption quality | Elo (Bradley-Terry) |
| **Arena-Hard-Auto / v2** | Automatic offline proxy for the Arena: 500 hard prompts + 250 creative, judged by GPT-4.1 / Gemini-2.5 | **NO — general quality.** Closest to "handles a hard real prompt well", but a single answer judged better ≠ made a smart assumption | Win-rate vs baseline (%) |
| **WildBench** | 1,024 challenging real user queries from 1M+ chat logs; per-category checklists | **WEAK/PARTIAL.** Real-user-query realism is good, but WB-Score/WB-Reward still measure answer quality, not ask-vs-assume | WB-Score, WB-Reward, Elo |
| **MixEval / MixEval-Hard** | Web-mined real queries matched to ground-truth benchmark items; cheap + high Arena correlation | **NO.** Ground-truth-graded; explicitly built to *correlate with Arena Elo* (0.96), so it inherits the same vibes signal — just cheaper | Ground-truth accuracy (%) |

### A1. LMArena (formerly Chatbot Arena) — [single-source on numbers / solid on existence]
- **What:** Live blind A/B human-vote arena. Categories: Overall, Hard Prompts, Expert (launched
  Nov 2025, top ~5.5% of prompts by reasoning depth), Coding, Math, Creative, Instruction-Following,
  Multi-Turn, etc. ~327 models as of Mar 2026.
- **Metric:** Elo. **Style Control** is available (controls for length + markdown) — without it the
  board is strongly length/format-biased.
- **June 2026 standings (from SEO-aggregator sites, NOT the official page — treat as approximate):**
  - Overall text top tier: **Claude Opus 4.8 (#1, ~1510)**, Gemini 3.1 Pro, Claude Opus 4.7,
    GPT-5.5 Pro (all ~1500). *(Note: a second aggregator listed GPT-5.6 Pro / "Claude Mythos 5" /
    Opus 4.7 / Gemini 3.2 Pro as the leaders — the aggregators disagree on exact model names and
    Elo, so trust only the shape: frontier closed models lead.)*
  - **Top OPEN-WEIGHT:** **DeepSeek V4 Pro** and **Qwen 3.7 Max** (~1450, just below the frontier
    tier). Llama 4.5 Maverick, GLM-6 (Zhipu), Kimi K2.6 (Moonshot) cited lower.
- **For a 64 GB Mac:** the arena-leading open models (DeepSeek V4 Pro, Qwen 3.7 Max) are
  far too large to run locally; their *smaller siblings* (Qwen3-30B/32B class) are what's relevant.
- **Style/gaming flag:** **HIGH.** Documented length + markdown bias; models are known to be tuned
  for arena preference. Use the Style-Controlled view if relying on it at all.
- **URLs:** official `https://arena.ai/leaderboard` (could not fetch live in this run);
  aggregators `https://presenc.ai/research/chatbot-arena-elo-leaderboard-june-2026`,
  `https://www.swfte.com/lmarena`. Changelog: `https://arena.ai/blog/leaderboard-changelog/`.

### A2. Arena-Hard-Auto / Arena-Hard v2.0 — [solid] (official GitHub fetched)
- **What:** Offline automatic proxy for the Arena. v2.0 = 500 fresh hard prompts + 250 creative-
  writing queries (software-eng, math, creative). LLM-as-judge.
- **Metric:** **Win-rate** pairwise vs a baseline; judges GPT-4.1 and Gemini-2.5. ~98.6% claimed
  correlation with human Arena rankings.
- **Style bias — EXPLICITLY ADDRESSED:** v2.0 ships **Style Control** (`--control-features markdown
  length`) to factor out markdown density + token length. This is the one arena-style board that
  lets you strip the length-bias — a point in its favor.
- **Open-model standings (v2.0, Hard prompts, Gemini-2.5 judge):** Qwen3-235B-A22B **58.4%**,
  Qwen3-32B **44.5%**, QwQ-32B **43.5%**; older Llama-3.1-Nemotron-70B **10.3%**, Qwen2.5-72B
  **10.1%**. June-2026 aggregator board (llm-stats) shows **MiMo-V2-Flash (Xiaomi) #1 at 0.862**,
  then Qwen3-Next-80B-A3B 0.827, Qwen3-235B variants ~0.79, NVIDIA Nemotron-3 ~0.74.
- **64 GB Mac relevance:** **Qwen3-32B / QwQ-32B / Qwen3-Next-30B-A3B** class scores well and is
  runnable quantized. **MiMo-V2-Flash** and **Nemotron-3 Nano (30B-A3B)** are the new June-2026
  open names worth watching at this size.
- **Released:** v2.0 on **2025-04-23**. **URL:** `https://github.com/lmarena/arena-hard-auto`,
  board `https://llm-stats.com/benchmarks/arena-hard-v2`.
- **Maps to axis?** NO — general answer-quality, but the *style-controlled* number is the least
  length-biased general signal available.

### A3. WildBench — [solid] (ICLR 2025 paper)
- **What:** 1,024 hard real-user queries from >1M chat logs; 12 fine-grained task classes
  (info-seeking, reasoning, planning, editing, coding, math, role-play, data-analysis, creative,
  advice-seeking, brainstorming, misc) → 5 groups. Task-specific checklists guide the judge.
- **Metric:** WB-Score & WB-Reward (per-category), plus Elo. Pearson **0.98** with Chatbot Arena.
- **Standings:** Leaderboard is from the **2024–2025 era** (GPT-4o-2024-05-13 ~1256 Elo,
  Claude-3.5-Sonnet ~1239) — **STALE, no live June-2026 update found.** Treat as historical.
- **URL:** `https://allenai.github.io/WildBench/`, paper `https://arxiv.org/html/2406.04770`.
- **Maps to axis?** WEAK — realism is good (real messy queries), but still answer-quality grading,
  not assumption-quality. Its "advice-seeking" + "info-seeking" categories *touch* the axis but
  don't isolate it.

### A4. MixEval / MixEval-Hard — [solid] (NeurIPS 2024)
- **What:** Mines real web queries, matches them to ground-truth benchmark items; "wisdom of the
  crowd" mixture. Cheap (≈6% the cost of MMLU), low variance (0.36 std).
- **Metric:** ground-truth accuracy. **0.96 ranking correlation with Chatbot Arena Elo** —
  MixEval-Hard ranks #1 among benchmarks on Arena-correlation.
- **Maps to axis?** NO. By design it *reproduces* the Arena's general-preference signal cheaply, so
  it carries the same not-about-smart-defaults limitation. Useful only as a cheap general proxy.
- **URL:** `https://mixeval.github.io/`, paper `https://arxiv.org/pdf/2406.06565`.
- **Gaming flag:** ground-truth-based → less style-gameable than Elo, but it's a *proxy of a
  vibes metric*, so it inherits the wrong-thing problem for this axis.

---

## Part B — The cluster that ACTUALLY maps: abstention / clarification / pragmatics

This is where "made the sensible default vs over-asking vs under-asking" is directly measured.

| Benchmark | What it measures | Maps to axis? | Metric |
|---|---|---|---|
| **AbstentionBench** | Should the model *refuse/flag* instead of confidently answering an unanswerable / false-premise / underspecified question | **YES — strongest direct map** (the "don't make a dumb confident default" side) | Abstention recall / precision / F1 |
| **QuestBench** | Can the model *ask the right question* to acquire the one missing fact in an underspecified reasoning task | **YES — the "ask a good question" side** | Accuracy at identifying the needed question |
| **CLAMBER** | Identify + clarify ambiguous information needs; quality of clarifying questions | **YES — ask-vs-assume** | Ambiguity-detection + clarify-quality |
| **ConfuseBench** | Recognize & resolve sources of uncertainty (vs answering through it) | **YES (partial)** | Uncertainty recognition/resolution |
| **PUB / PragmEval** | Pragmatic/implicature understanding — infer the *intended* meaning (the sensible default reading) | **YES — commonsense default inference** | Multi-task accuracy |
| **Social IQa** | Commonsense reasoning about social situations / intentions | **PARTIAL — commonsense, dated** | MC accuracy |

### B1. AbstentionBench — [solid] (arxiv HTML fetched) ⭐ best single proxy
- **What:** 20 datasets / 6 scenarios — **unknown answers, false premises, stale info, subjective
  questions, underspecified context, unclear intent.** Tests whether the model *abstains / flags*
  instead of confidently confabulating. This is exactly "don't make a wrong smart-sounding default."
- **Metric:** **Abstention recall** (fraction of unanswerable Qs correctly not-answered), + precision
  + F1. Most models have high precision but low recall (they under-abstain = over-confident default).
- **Standings & open-weight:**
  - Best: **GPT-4o** and **Qwen 2.5 32B** (top overall) — *an open 32B ties the frontier here*,
    a strong signal for the 64 GB Mac user.
  - Worst: **OLMo-7B-Instruct**; near-zero recall on medical (MediQ) across the board.
  - Open models evaluated: Llama-3.1 (8B/70B/405B), Llama-3.3-70B, **Qwen-2.5-32B**, Mistral-7B,
    OLMo-7B, DeepSeek-R1-Distill-Llama-70B.
  - ⚠️ **Reasoning fine-tuning DEGRADES abstention by ~24%** (DeepSeek-R1-Distill, s1.1
    hallucinate missing context). → high reasoning-benchmark scores can ANTI-correlate with sensible
    behavior under ambiguity.
- **Published:** 2025-06-10. **URL:** `https://arxiv.org/html/2506.09038v1`.
- **64 GB Mac takeaway:** **Qwen2.5-32B** (and successors like Qwen3-32B) is the sweet-spot open
  model that's both runnable and good at *not* over-asserting. Avoid pure reasoning-distilled
  variants if "sensible default under ambiguity" is what you want.

### B2. QuestBench — [single-source] (cited via AbstentionBench/search; direct page not fetched)
- **What:** "Can LLMs ask the *right* question to acquire info in reasoning tasks?" Underspecified
  reasoning problems where exactly one fact is missing; model must identify the question to ask.
- **Metric:** accuracy at selecting/identifying the needed clarifying question.
- **Standings:** specific live numbers not retrieved this run; Gemini/GPT-class lead, models
  generally weak at this. **Maps to the "asks a good question" axis directly.**
- **URL:** search-surfaced (Li et al., 2025); confirm at the arXiv listing before citing numbers.
- **Confidence:** [single-source] — existence solid, leaderboard numbers unverified.

### B3. CLAMBER — [single-source] (arxiv abstract via search)
- **What:** Benchmark of *identifying and clarifying ambiguous information needs*. Finding: current
  LLMs **fail to ask high-quality clarifying questions** because they can't assess their own
  knowledge boundaries → they default-answer instead of clarifying.
- **Metric:** ambiguity classification + clarify-question quality.
- **URL:** `https://arxiv.org/pdf/2405.12063` (2024). **Maps to axis:** YES (ask-vs-assume).
- **Confidence:** [single-source].

### B4. ConfuseBench / "Do not Abstain!" / Structured-Uncertainty — [single-source]
- **What:** Family of 2025 papers on recognizing & resolving uncertainty rather than abstaining
  blindly OR over-answering — i.e. the *calibrated* middle the user wants (don't over-ask, don't
  under-ask). Uses EVPI (Expected Value of Perfect Information) to score which clarifying question
  is worth asking.
- **URLs:** `https://arxiv.org/pdf/2506.00780`, `https://openreview.net/forum?id=dc8ebScygC`,
  `https://arxiv.org/pdf/2502.04485` (Active Task Disambiguation).
- **Maps to axis:** YES — this is literally the over-ask/under-ask calibration the user named.
- **Confidence:** [single-source] each; no consolidated leaderboard.

### B5. PUB / PragmEval / "On the Same Wavelength" — [solid as a body, no live board]
- **What:** Pragmatics understanding — implicature, presupposition, figurative language, intention
  recognition. I.e. inferring the **sensible default reading** of an utterance. PUB (ACL 2024
  Findings) + PragmEval (11 datasets) + 2025 work (Sravanthi et al., "learning to think for
  pragmatic understanding", ACL 2025; "On the Same Wavelength", 2025).
- **Maps to axis:** YES — this is the *commonsense-default-inference* half of the user's axis.
- **Metric:** multi-task accuracy. No single live leaderboard / open-vs-closed standings found.
- **URLs:** `https://aclanthology.org/2024.findings-acl.719.pdf` (PUB),
  `https://arxiv.org/pdf/2509.06952`, `https://arxiv.org/pdf/2502.12378` (survey).
- **Confidence:** [solid] as research area; [hearsay] on any specific model ranking.

### B6. Social IQa — [solid, but dated]
- **What:** Commonsense reasoning about social interactions & intentions (the classic 2019 AllenAI
  benchmark). Touches "commonsense judgment" but is saturated by frontier models and pre-LLM-era.
- **Maps to axis:** PARTIAL — commonsense, but multiple-choice and largely solved; not discriminating
  for 2026 frontier/open models. Use only as a floor check.
- **Confidence:** [solid] existence, low current value.

---

## Cross-cutting flags (read before trusting any of these)

1. **The arenas measure the WRONG thing for "smart defaults."** LMArena/Arena-Hard/WildBench/MixEval
   all score "is this answer better," which rewards thorough, well-formatted, *confident* answers —
   structurally the opposite of "ask when you should / don't over-assert." A model can top the arena
   by *never* clarifying. **Do not use arena rank as a smart-defaults proxy.**
2. **Length/markdown/style bias is pervasive** in the Elo/win-rate boards. Only **Arena-Hard v2 with
   Style Control** explicitly factors it out. Always prefer the style-controlled number.
3. **Reasoning ↑ ≠ judgment ↑.** AbstentionBench's −24% finding means the math/reasoning leaderboard
   leaders (incl. reasoning-distilled open models) can be *worse* at sensible defaults under
   ambiguity. The user's axis and the reasoning leaderboards can point in opposite directions.
4. **The directly-relevant cluster (AbstentionBench/QuestBench/CLAMBER/ConfuseBench/PUB) has no
   unified live leaderboard.** They're individual papers, mostly 2024–2025, with per-paper model
   lists. AbstentionBench is the only one with a clean open-vs-closed comparison fetched live.
5. **Open-weight, on a 64 GB Mac:** the standout is **Qwen2.5/Qwen3-32B class** — ties GPT-4o on
   AbstentionBench (good defaults / abstention) AND scores well on Arena-Hard v2 (general quality),
   while being runnable. Avoid pure reasoning-distilled variants (DeepSeek-R1-Distill, s1.1) if
   sensible-default-under-ambiguity is the priority. June-2026 open names to watch at this size:
   **MiMo-V2-Flash, Nemotron-3 Nano (30B-A3B), Qwen3-Next-30B-A3B.**

## Source confidence ledger
- [solid]: Arena-Hard-Auto (official GitHub), AbstentionBench (arXiv), WildBench (ICLR'25 paper),
  MixEval (NeurIPS'24), PUB/PragmEval (ACL).
- [single-source]: LMArena June-2026 *numbers* (SEO aggregators, names disagree — Opus 4.8 vs
  4.7, GPT-5.5 vs 5.6), Arena-Hard-v2 June-2026 board (llm-stats), QuestBench/CLAMBER/ConfuseBench
  leaderboard numbers.
- [hearsay]: any specific open-vs-closed ranking on PUB/PragmEval/Social IQa.

## Key URLs
- AbstentionBench: https://arxiv.org/html/2506.09038v1 (2025-06-10) ⭐
- Arena-Hard-Auto: https://github.com/lmarena/arena-hard-auto · board https://llm-stats.com/benchmarks/arena-hard-v2
- LMArena official: https://arena.ai/leaderboard · changelog https://arena.ai/blog/leaderboard-changelog/
- WildBench: https://allenai.github.io/WildBench/ · https://arxiv.org/html/2406.04770
- MixEval: https://mixeval.github.io/ · https://arxiv.org/pdf/2406.06565
- CLAMBER: https://arxiv.org/pdf/2405.12063 · QuestBench (Li et al. 2025, search-surfaced)
- ConfuseBench/uncertainty: https://arxiv.org/pdf/2506.00780 · https://arxiv.org/pdf/2502.04485
- PUB: https://aclanthology.org/2024.findings-acl.719.pdf · Pragmatics survey https://arxiv.org/pdf/2502.12378
