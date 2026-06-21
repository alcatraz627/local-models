# Abstention Benchmarks — "Knowing What You Don't Know"

**User axis:** abstention / knowing-what-you-don't-know (refusing to answer when it shouldn't; unanswerable, underspecified, false-premise, stale-data queries).
**Research date:** 2026-06-19. All findings from live web sources (arXiv, OpenReview, HuggingFace, GitHub, MIT Press TACL).
**Local-model angle:** user runs open-weight models on a 64GB Mac, so open-weight results are flagged throughout.

---

## TL;DR for a local-model user

- **Abstention is an UNSOLVED problem** across the board, and **scaling does not help** (Llama 8B ≈ Llama 405B on AbstentionBench). This is the single most important finding.
- **Good news for local models:** open-weight **Qwen 2.5 32B ties GPT-4o for the top spot** on AbstentionBench. Qwen3 family dominates 2026 hallucination leaderboards. Open weights are genuinely competitive here — this is NOT an axis where closed frontier models pull ahead.
- **Bad news / trap:** **reasoning fine-tuning DEGRADES abstention by ~24%** (AbstentionBench). So a "reasoning" distill (DeepSeek-R1-Distill, s1.1) is *worse* at knowing its limits than its base model. Picking a thinking model for this axis is counterproductive.
- **Best benchmark to track:** **AbstentionBench** (Meta FAIR, holistic, 35K queries, open code) for breadth; **Refusal Index / RI** (Oct 2025) for a clean, accuracy-independent metric.

---

## Benchmark table

| Benchmark | What it measures | Metric | Open-weight result | URL | Date | Confidence |
|---|---|---|---|---|---|---|
| **AbstentionBench** | Holistic abstention across 20 datasets / 35K queries: unknown answers, underspecification, false premises, subjective, stale data | Abstention **recall** (primary) + precision + F1; LLM-judge | **Qwen 2.5 32B ties GPT-4o for #1.** Scaling Llama 8B→405B gives ~no gain. Reasoning FT (DeepSeek-R1-Distill-Llama-70B, s1.1) **degrades** abstention | [arxiv 2506.09038](https://arxiv.org/abs/2506.09038) · [code](https://github.com/facebookresearch/AbstentionBench) | Jun 10 2025 | **[solid]** |
| **SelfAware** | Can the model recognize unanswerable/unknowable questions (self-knowledge)? 1,032 unanswerable + 2,337 answerable, 5 categories | F1 of unanswerable detection; "answerable/unanswerable" classification | Original (2023) tested LLaMA among 20 LLMs; GPT-4 75.5%. Predates current open weights — still the canonical "self-knowledge" set, widely reused | [ACL 2023](https://aclanthology.org/2023.findings-acl.551/) · [arxiv 2305.18153](https://arxiv.org/abs/2305.18153) · [code](https://github.com/yinzhangyue/SelfAware) | May 2023 | **[solid]** |
| **R-Tuning** (Refusal-Aware Instruction Tuning) | A *method* + eval: tune LLMs to say "I don't know" on questions beyond parametric knowledge; splits data into certain/uncertain | Refusal rate on unanswerable sets (FalseQA, NEC, SA); accuracy retained on known | Method applied to open models (LLaMA/OpenLLaMA-family). Refusal shown to be a generalizable "meta-skill" | [NAACL 2024](https://aclanthology.org/2024.naacl-long.394/) · [arxiv 2311.09677](https://arxiv.org/abs/2311.09677) | Nov 2023 (NAACL'24) | **[solid]** |
| **SQuAD 2.0** | Reading-comprehension abstention: 50K+ adversarial unanswerable questions; must abstain when no answer in passage | EM / F1 with no-answer handling | Foundational lineage benchmark; **saturated** for modern LLMs (see flags) | [emergentmind](https://www.emergentmind.com/papers/1806.03822) · [arxiv 1806.03822](https://arxiv.org/abs/1806.03822) | 2018 | **[solid]** |
| **QnotA** | Taxonomy of unanswerable Qs (Incomplete Info, Future, Incorrect Info, Ambiguous, Unmeasurable); 400 samples | Abstention accuracy per category | Small (400). Taxonomy-focused, not a leaderboard | (taxonomy paper; see AGent [arxiv 2309.05103](https://arxiv.org/pdf/2309.05103)) | 2023–24 | **[single-source]** |
| **FaithEval (unanswerable task)** | Faithfulness to context: 2.4K unanswerable examples where supporting evidence is removed; must abstain not hallucinate | Accuracy on unanswerable / faithfulness | "Even SOTA models often struggle." Tested open + proprietary; Salesforce dataset public on HF | [github](https://github.com/SalesforceAIResearch/FaithEval) · [HF dataset](https://huggingface.co/datasets/Salesforce/FaithEval-unanswerable-v1.0) | 2024–25 | **[solid]** |
| **FactGuard / FactGuard-Bench** | Detecting unanswerable Qs in **long-context** (4K–128K) texts; 25,220 answerable+unanswerable examples | Overall accuracy (answerable vs unanswerable gap) | 9 LLMs: best **only 67.67%** overall; gap between answerable/unanswerable. Training on it → 81.17%. Multi-agent generated | [OpenReview](https://openreview.net/forum?id=c4nZkkyl6E) · [arxiv 2504.05607](https://arxiv.org/html/2504.05607) | Apr 2025 | **[solid]** |
| **Refusal Index (RI)** — *"Can LLMs Refuse Questions They Do Not Know?"* | Knowledge-aware refusal: how accurately a model refuses Qs it actually doesn't know (decoupled from overall accuracy) | **RI = Spearman rank corr(refusal prob, error prob)** — stable across refusal rates | 16 models, 5 datasets (incl. SimpleQA). Finding: factual accuracy high but **refusal behavior unreliable/fragile**. Metric is the contribution | [arxiv 2510.01782](https://arxiv.org/abs/2510.01782) · [OpenReview](https://openreview.net/forum?id=9gJBhkLRat) | Oct 2 2025 | **[solid]** |
| **AbstentionTemporalQA** — *"When Silence Is Golden"* | Abstention in **temporal** QA (time-sensitive evidence, conflated time-periods) + beyond; frames abstention as teachable via CoT+RL | Abstention-aware reward / abstention accuracy | Method (CoT supervision + RL w/ abstention rewards) applied to open models; ICLR 2026 accepted | [arxiv 2602.04755](https://arxiv.org/abs/2602.04755) · [code](https://github.com/Blackzxy/AbstentionTemporalQA) | Feb 2026 (ICLR'26) | **[solid]** |
| **Know Your Limits** (survey) | TACL survey unifying abstention literature: a map, not a benchmark — useful for taxonomy & metric definitions | n/a (survey) | n/a | [TACL/MIT Press](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00754/131566/) · [arxiv 2407.18418](https://arxiv.org/pdf/2407.18418) | 2024–25 | **[solid]** |

### Adjacent / context (not pure abstention but measure refusal/idk behavior)
- **HalluLens** (ACL 2025, [arxiv 2504.17550](https://arxiv.org/html/2504.17550v1)): hallucination benchmark separating intrinsic/extrinsic + false-refusal-rate. Qwen2.5 7B/14B kept **low false-refusal**; Llama-3.1-8B-Instruct refused 83% (over-abstains). **[solid]**
- **Hallucination Benchmarks Leaderboard, Apr 2026** ([awesomeagents.ai](https://awesomeagents.ai/leaderboards/hallucination-benchmarks-leaderboard/)): **Qwen3 family holds 3 of top-5.** Strong open-weight signal for local users. **[single-source]**

---

## Open-weight verdict (for the 64GB Mac)

| Model class | Abstention signal | Notes |
|---|---|---|
| **Qwen 2.5 32B / Qwen3** | **Strongest open option.** Ties GPT-4o on AbstentionBench; low false-refusal on HalluLens; Qwen3 dominates 2026 hallucination leaderboards | 32B fits comfortably in 64GB (quantized). Best pick for this axis. |
| **Llama 3.1 / 3.3 70B** | Mediocre; **scale doesn't help** (8B≈405B). Llama-3.1-8B-Instruct *over*-refuses on HalluLens (83%) | Over-abstention is its own failure — refusing answerable Qs. |
| **Mistral 7B, OLMo 7B** | Weaker on AbstentionBench | Not recommended for this axis. |
| **DeepSeek-R1-Distill, s1.1 (reasoning)** | **AVOID for abstention** — reasoning FT degrades abstention ~24% | Counterintuitive but well-documented. |

---

## Flags — saturated / gamed / measures-the-wrong-thing

- ⚠️ **SQuAD 2.0 is SATURATED** for modern LLMs. It's extractive RC over a single short passage; the "abstain" decision is narrow (is the answer in *this* paragraph). Useful lineage/historical anchor, NOT a discriminating signal for 2025–26 frontier or open models. Treat as a floor, not a measure.
- ⚠️ **Reasoning models GAME the wrong objective.** A "thinking"/CoT-distilled model looks better on accuracy benchmarks but is **worse** at abstention (–24%, AbstentionBench). If you select a local model by reasoning-benchmark scores, you will systematically pick the *worst* abstainers. This is the biggest trap on this axis.
- ⚠️ **Over-abstention ≠ good abstention.** Raw "refusal rate" is gameable — a model that refuses everything scores high. Llama-3.1-8B-Instruct's 83% HalluLens refusal is a *failure mode*, not a win. Prefer metrics that decouple this: **Refusal Index (Spearman corr of refusal vs. error)** and AbstentionBench's **precision/F1** (not recall alone) are the right lenses.
- ⚠️ **LLM-judge dependence.** AbstentionBench and several others score abstention with an LLM judge — judge bias/leniency is a known confound. Cross-check with the rule-based RI metric where possible.
- ℹ️ **FactGuard/FaithEval are context-grounded** (RAG-style: is the answer in the provided text), distinct from **parametric** abstention (does the model know the fact at all). Don't conflate — they measure different "don't know"s. AbstentionBench + RI cover parametric; FactGuard/FaithEval cover contextual.

---

## Recommendation

Track **AbstentionBench** (breadth, open code, open-weight rankings) + **Refusal Index** (clean accuracy-independent metric). For local use, **Qwen 2.5 32B / Qwen3** is the standout open-weight abstainer; **avoid reasoning-distilled variants** for this specific capability. Watch **AbstentionTemporalQA / "When Silence Is Golden"** (ICLR 2026) as the freshest successor framing abstention as a teachable CoT+RL skill.
