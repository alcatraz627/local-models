# Calibration & Hallucination Benchmarks for LLMs

**Research date:** 2026-06-19
**User axis:** Does the model's confidence match its accuracy (calibration), and does it make up facts (hallucination)?
**User context:** Runs local/open-weight models on a 64GB Mac — open-weight performance is highlighted throughout.

Confidence flags: **[solid]** = official page or multiple corroborating sources · **[single-source]** = one source · **[hearsay]** = aggregator/secondhand only.

---

## TL;DR — what to actually use

- **For "does it make up facts in RAG/summarization"** → **Vectara HHEM leaderboard** (live, frequently updated, open-weights included). Best open-weight: **Llama-3.3-70B (4.1%)**, Gemma-3-12B (4.4%), Mistral-Large-2411 (4.5%), Qwen3-8B (4.8%). [solid]
- **For "does it know facts AND abstain when it doesn't" (the calibration axis you actually want)** → **AA-Omniscience** (Artificial Analysis, Nov 2025). Explicitly *rewards accuracy, punishes confident wrong guesses, rewards abstention.* This is the single best match for "confidence matches accuracy." [solid]
- **For grounded factuality (long-doc, no hallucination beyond source)** → **FACTS Grounding** (Google DeepMind/Kaggle). Closed models lead; v2 is hard (no model >70%). [solid]
- **For parametric short-form factuality + stated-confidence calibration** → **SimpleQA-Verified** (Google, Sep 2025). [solid]
- **Avoid as a primary signal:** **TruthfulQA** — saturated, in training data, mislabeled gold answers, measures the wrong thing. [solid]

---

## Benchmark-by-benchmark

### 1. AA-Omniscience (Artificial Analysis) — BEST calibration match
| Field | Detail |
|---|---|
| What it measures | Knowledge reliability AND hallucination across 42 topics / 6,000 questions. Critically: rewards correct answers, **penalizes confident wrong guesses, and rewards "I don't know" abstention**. |
| User axis | **Calibration + Hallucination** (the cleanest single mapping to "confidence matches accuracy"). |
| Metric | **Omniscience Index** (accuracy minus penalized hallucination) + a separate **Hallucination Rate**. Negative-scoring for confident errors. |
| Leaders | Index: Gemini 3.x Pro / Claude Opus 4.x lead. **Lowest hallucination rate: Cohere Command A+ (14.1%)**, then Qwen3.x Max (22.9%), MiMo-V2.5-Pro (24.5%). Headline finding: **"all but three models are more likely to hallucinate than give a correct answer."** |
| Open-weight | **Strong showing** — Cohere Command A+ (open-weight) leads hallucination-rate; Qwen variants competitive. Good news for local users. |
| URL / date | https://artificialanalysis.ai/evaluations/omniscience · paper https://arxiv.org/html/2511.13029v1 · Nov 2025, live-updated (113 models as of mid-2026) |
| Flag | **[solid]** — official page + arXiv + announcement |

### 2. Vectara HHEM Hallucination Leaderboard — BEST live hallucination signal
| Field | Detail |
|---|---|
| What it measures | Intrinsic hallucination: feed a document, ask for a summary using *only* facts in the document, detect summaries that introduce false info. RAG/summarization setting. |
| User axis | **Hallucination** (faithfulness/grounding). |
| Metric | **Hallucination Rate %**, Factual Consistency Rate (100 − hallu), and **Answer Rate %** (refusal-adjusted — important: a low hallu rate via high refusal is flagged). Detector evolved HHEM-1.0 → 2.1 → now **FaithJudge** (few-shot LLM-as-judge, human-aligned). |
| Leaders | finix_s1_32b / AntGroup (1.8%), GPT-5.4-nano (3.1%), Gemini-2.5-flash-lite (3.3%), Phi-4 (3.7%). |
| Open-weight | **Llama-3.3-70B-Instruct (4.1%, 99.5% answer rate)**, Gemma-3-12B (4.4%), Mistral-Large-2411 (4.5%, 99.9%), Qwen3-8B (4.8%, 99.9%). All very close to frontier. Note: reasoning models hallucinate **>10%** on the harder late-2025 dataset (7,700 docs, up to 32k tokens). |
| URL / date | https://github.com/vectara/hallucination-leaderboard · HF space https://huggingface.co/spaces/vectara/leaderboard · **last updated 2026-05-11**, continuously refreshed |
| Flag | **[solid]** — official GitHub + HF + corroborating aggregator |

### 3. FACTS Grounding (Google DeepMind / Kaggle)
| Field | Detail |
|---|---|
| What it measures | Given a long doc (up to 32k tokens) + a request, does the model answer faithfully **using only the document**, without hallucinating? 1,719 examples (finance, tech, medicine, law, retail). |
| User axis | **Hallucination** (grounded factuality). |
| Metric | **Factuality score %** = average of 3 LLM judges (Gemini 1.5 Pro, GPT-4o, Claude 3.5 Sonnet) to reduce single-judge bias. Dec 2025 **FACTS v2 / Leaderboard** splits into 4 dims: Grounding, Parametric, Search, + multi-dimensional. |
| Leaders | Gemini 2.0 Flash Exp (83.6%), Gemini 1.5 Flash (82.9%), Gemini 1.5 Pro (80.0%), Claude 3.5 Sonnet (79.4%), GPT-4o (78.8%). **v2 is hard: no model breaks 70%.** |
| Open-weight | **Weak presence** — top ranks are all closed (Gemini/Claude/GPT). No open-weight in top 5. This benchmark favors frontier closed models. |
| URL / date | https://www.kaggle.com/benchmarks/google/facts-grounding · blog https://deepmind.google/blog/facts-grounding-a-new-benchmark-for-evaluating-the-factuality-of-large-language-models/ · v1 Dec 2024, FACTS Leaderboard (v2) Dec 2025 |
| Flag | **[solid]** — official DeepMind blog + Kaggle + aggregator (Kaggle page itself didn't render for direct fetch) |

### 4. SimpleQA (OpenAI) + SimpleQA-Verified (Google) — calibration aspect
| Field | Detail |
|---|---|
| What it measures | Short-form parametric factuality: 4,326 (SimpleQA) / 1,000 (Verified) adversarial fact-seeking questions with single indisputable answers. **Verified** fixes SimpleQA's noisy/incorrect labels, topical bias, redundancy. |
| User axis | **Hallucination** (parametric factuality) **+ Calibration** (SimpleQA's signature feature). |
| Metric | Ternary grade: correct / incorrect / not-attempted. F1 = harmonic mean of overall-correct and correct-given-attempted. **Calibration probes:** (a) *stated confidence* — "give your confidence %" → measures over/under-confidence; (b) *answer frequency* across repeated samples. Finding: **all models systematically overstate confidence**; accuracy well below the perfect-calibration line. |
| Leaders | SimpleQA-Verified: **Gemini 2.5 Pro F1=55.6** (SOTA, beats GPT-5). SimpleQA (aggregator): Gemini 2.5 Pro 53.0%, then **Qwen3-235B-A22B 50.6%**, **Qwen3-VL-235B 46.7%**, **Qwen3-Next-80B 40.1%**. Field avg ~20.8%. |
| Open-weight | **Excellent on SimpleQA** — Qwen3 family (235B and 80B) ranks #2–#5, beating most closed models. DeepSeek-R1 29.1%. Qwen3-Next-80B (40.1%) is a strong 64GB-feasible pick. |
| URL / date | OpenAI: https://openai.com/index/introducing-simpleqa/ (Oct 2024) · Verified paper: https://arxiv.org/html/2509.07968v1 + https://huggingface.co/papers/2509.07968 (Sep 2025) · Kaggle leaderboard https://www.kaggle.com/benchmarks/openai/simpleqa · Epoch AI https://epoch.ai/benchmarks/simple-qa-verified |
| Flag | **[solid]** — official OpenAI + Google arXiv + Epoch; specific open-weight numbers **[single-source]** (awesomeagents aggregator) |

### 5. ConFiQA — context-faithfulness under knowledge conflict
| Field | Detail |
|---|---|
| What it measures | RAG scenarios with **deliberate knowledge conflicts**: does the model trust retrieved context or fall back to (wrong) parametric memory? Isolates the "fluent but contradicts evidence" failure. |
| User axis | **Hallucination** (context-faithfulness, the RAG flavor). |
| Metric | Faithfulness accuracy (% answers following context vs parametric). Used as the standard benchmark in faithfulness papers (ParamMute +54.63%, ContextFocus, CLEAR, COIECD). |
| Leaders | No public live leaderboard — used as an eval *within* method papers; methods (ParamMute, ContextFocus) report large gains over prompting baselines. |
| Open-weight | Method papers test on open models (Llama, Qwen) since they need weight access — relevant to local-model faithfulness tuning. |
| URL / date | Referenced via ParamMute https://arxiv.org/html/2502.15543 (Jun 2025), ContextFocus https://arxiv.org/pdf/2601.04131v1 (Jan 2026) |
| Flag | **[single-source]** — no standalone leaderboard; appears as a shared eval set across multiple papers |

### 6. HalluLens (Meta FAIR) — extrinsic vs intrinsic taxonomy
| Field | Detail |
|---|---|
| What it measures | First benchmark **solely for extrinsic hallucination** (contradicting training data), formalizing extrinsic vs intrinsic. 3 tasks: **LongWiki** (long-form), **PreciseQA/PreciseWikiQA** (factual queries), **Nonsense** (non-existent entity refusal). Dynamic test-set generation → resists contamination. |
| User axis | **Hallucination** (+ a refusal/abstention element via the Nonsense task, which touches calibration). |
| Metric | False Acceptance Rate (on nonsense entities), accuracy/precision/recall per task. |
| Leaders | **Llama-3.1-405B lowest false-acceptance (6.88%)** on non-existent entities; some Mistral variants **>80%** (very bad). GPT-4o best precision/recall balance, 52.59% on PreciseWikiQA. |
| Open-weight | **Mixed** — Llama-3.1-405B excellent on the abstention task; Mistral variants poor. Useful for testing whether a local model refuses fake entities. |
| URL / date | ACL 2025: https://aclanthology.org/2025.acl-long.1176/ · arXiv https://arxiv.org/pdf/2504.17550 (Apr 2025) |
| Flag | **[solid]** — ACL paper + corroborating aggregator |

### 7. Honesty benchmarks: MASK, BeHonest, HONESET
| Field | Detail |
|---|---|
| What they measure | **MASK** (Center for AI Safety, 2025): **disentangles honesty from accuracy** — does the model *lie when pressured*, independent of whether it knows the truth? "Many honesty benchmarks just measure accuracy in disguise." **BeHonest** (GAIR, 2024): 3 axes — self-knowledge (knowledge-boundary awareness), non-deceptiveness, consistency; 10 scenarios. **HONESET**: referenced but lower-profile. |
| User axis | **Calibration** (BeHonest's self-knowledge axis = "knows what it doesn't know") + a distinct *honesty/deception* axis MASK isolates. |
| Metric | MASK: **honesty score** = propensity to lie under pressure (lower = more honest). BeHonest: per-scenario rates across the 3 axes. |
| Leaders | MASK: **larger/more-accurate models do NOT lie less** — frontier models "readily lie when pressured" (30 models tested). BeHonest: "significant room for improvement" across 9 open+closed models. |
| Open-weight | Both test open + closed families across sizes; BeHonest explicitly spans open-source. No clear open-weight winner — honesty is weakly correlated with scale/capability. |
| URL / date | MASK: https://www.mask-benchmark.ai/ + https://arxiv.org/pdf/2503.03750 (Mar 2025) · BeHonest: https://gair-nlp.github.io/BeHonest/ + https://arxiv.org/abs/2406.13261 (Jun 2024) |
| Flag | **[solid]** for MASK + BeHonest · **[hearsay]** for HONESET (named, not detailed in live sources) |

### 8. Expected Calibration Error (ECE) — the metric, not a leaderboard
| Field | Detail |
|---|---|
| What it is | A **metric**, not a benchmark: ECE = Σ(\|Bₘ\|/n)·\|acc(Bₘ)−conf(Bₘ)\| — bins predictions by confidence, measures gap between confidence and accuracy. Variants: **smECE** (kernel-smoothed, theoretically sounder). |
| User axis | **Calibration** (the canonical metric for it). |
| Key 2025-26 findings | LLMs are **severely miscalibrated**: ECE ranges 0.108–0.427 across formats; even best-calibrated frontier model (Claude Opus 4.5) shows a **~12-point** confidence-accuracy gap. *Float* confidence format calibrates best (ECE 0.128) but is least consistent; *categorical* is consistent but worst-calibrated (0.427). Format choice dominates. |
| Where it shows up | "Benchmarking LLMs via Uncertainty Quantification" (UCL), epistemic-calibration benchmark https://arxiv.org/pdf/2512.16030 (Dec 2025), behaviorally-calibrated RL https://arxiv.org/html/2512.19920v1. No single canonical "ECE leaderboard" — it's reported per-paper. |
| URL / date | https://arxiv.org/pdf/2512.16030 (Dec 2025) · https://discovery.ucl.ac.uk/id/eprint/10217368/ |
| Flag | **[solid]** as a metric; **[single-source]** per individual numbers |

---

## ⚠️ Saturated / gamed / measures-the-wrong-thing

### TruthfulQA — DO NOT rely on as a primary signal
- **Saturated / contaminated:** now in training data; scores inflated. [solid]
- **Mislabeled gold answers:** incorrect "truth" labels; metrics over-penalize. (HalluLens paper, Apr 2025). [solid]
- **Gameable:** simple heuristics + answer-leaking style cues exploit dataset weaknesses; many public scores use few-shot/self-consistency that leak answers — community pushes for strict zero-shot. (turntrout.com analysis). [solid]
- **Measures the wrong thing:** often cited as a *hallucination* benchmark but actually measures *imitation of human falsehoods/factuality* — conceptual mismatch. Counterintuitively, **larger models score *less* truthfully**. [solid]
- **Current "leaders"** (telling): Phi-3.5-MoE (0.775), IBM Granite 3.3 8B (0.669), Phi-4-mini (0.664) — small models top it, a saturation red flag.
- URL: https://github.com/sylinrl/TruthfulQA · criticism https://turntrout.com/original-truthfulqa-weaknesses

### Vectara HHEM — one caveat (not a disqualifier)
Low hallucination rate can be **gamed by high refusal** — always read the **Answer Rate** column alongside. The leaderboard exposes this, which is why it's still trustworthy.

### "Safetywashing" caution (general)
arXiv 2407.21792 ("Safetywashing") warns many safety/honesty benchmarks correlate strongly with general capability — i.e., they measure capability, not safety/calibration progress. Applies most to TruthfulQA-style evals; MASK and AA-Omniscience are explicitly designed to resist this.

---

## Recommendation for a 64GB-Mac local-model user

| Goal | Use this benchmark | Best open-weight pick observed |
|---|---|---|
| Won't make up facts in RAG/summarization | **Vectara HHEM** | Llama-3.3-70B (4.1%), Gemma-3-12B (4.4%), Qwen3-8B (4.8%) |
| Knows facts AND abstains when unsure (calibration) | **AA-Omniscience** | Cohere Command A+, Qwen3 family |
| Short-form factual recall | **SimpleQA-Verified** | Qwen3-Next-80B (40.1%) — fits 64GB quantized |
| Faithful to provided context (RAG) | **ConFiQA** / FACTS Grounding | Llama/Qwen (tunable) |
| Refuses fake/nonexistent entities | **HalluLens** Nonsense task | Llama-3.1 family strong |

**Bottom line:** open-weight models are genuinely competitive on hallucination/faithfulness (Llama-3.3-70B, Qwen3, Gemma-3 within ~1pt of frontier on HHEM), and the **Qwen3** family is a standout on factual recall (SimpleQA #2–5). Calibration in absolute terms is poor *across the board* (ECE 0.1–0.4 for everyone) — no model, open or closed, has confidence that reliably matches accuracy.
