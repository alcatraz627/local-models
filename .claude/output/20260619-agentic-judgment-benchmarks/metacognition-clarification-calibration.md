# Metacognition, Clarification & Calibration Benchmarks — Master Synthesis

**Research date:** 2026-06-19
**The user's question:** which benchmarks actually measure a model's *judgment* — making smart assumptions, knowing when to **ask** vs answer, knowing what it **doesn't** know (abstention/calibration), not hallucinating, and following instructions reliably?
**User constraint:** runs open-weight models locally on a 64GB Mac. Open-weight standings are flagged throughout.
**Method:** five parallel research sweeps over live arXiv / GitHub / official leaderboards (June 2026). Per-family detail lives in sibling files in this directory (see "Detailed family files" at the end). Confidence flags: **[solid]** (official page / multiple sources) · **[single-source]** · **[hearsay]**.

---

## 0. The 60-second answer

Five user axes → the benchmark that best measures each → can a local model do well:

| User axis | Best benchmark to trust | Saturated? | Open-weight competitive locally? |
|---|---|---|---|
| **Ask vs assume** (proactivity) | **InteractComp** + **ClarifyMT-Bench** | No — wide open (top model 13.7% on InteractComp) | Yes at single-turn (Qwen-2.5-7B, DeepSeek-R1); degrades multi-turn |
| **Abstention** (knows what it doesn't know) | **AbstentionBench** + **Refusal Index (RI)** | No — unsolved, *scaling doesn't help* | **Yes — Qwen 2.5-32B ties GPT-4o** |
| **Calibration** (confidence matches accuracy) | **AA-Omniscience** + SimpleQA-Verified (+ ECE as the metric) | No — *everyone* is miscalibrated | Partially — Qwen3 strong on factual recall; calibration poor for all |
| **Hallucination** (doesn't make up facts) | **Vectara HHEM** leaderboard (live) | No | **Yes — Llama-3.3-70B, Gemma-3, Qwen3 within ~1pt of frontier** |
| **Instruction-following reliability** | **IFBench / Multi-IF / IFEval++** (NOT plain IFEval) | **IFEval YES (saturated+gamed)**; successors no | Yes — Qwen3.5 + IF-RLVR; multi-turn is the weak spot |
| **Smart defaults** (commonsense judgment) | AbstentionBench/QuestBench cluster — **NOT the arenas** | Arenas measure wrong thing | Yes (Qwen2.5/3-32B class) |

**Three findings that should change how the user picks a local model:**

1. **Reasoning fine-tuning HURTS judgment.** AbstentionBench: reasoning-distilled models (DeepSeek-R1-Distill, s1.1, QwQ) are **~24% WORSE** at abstaining — they confabulate missing context instead of flagging it. Reasoning models also drop on strict IFEval (lose formatting constraints mid-thought). **Selecting a local model by its reasoning-leaderboard score systematically picks the worst abstainers and shakiest instruction-followers.** This is the single most important takeaway.
2. **Open weights are genuinely competitive on the judgment axes** (abstention, hallucination, instruction-following) — these are NOT axes where closed frontier models pull away. Qwen is the recurring open-weight winner across all five families.
3. **The popular leaderboards measure the wrong thing for this user.** LMArena/Arena-Hard reward confident, well-formatted, *thorough* answers — structurally the opposite of "ask when ambiguous / abstain when unsure." A model can top the arena by *never* clarifying. Plain IFEval and TruthfulQA are saturated/gamed. Trust the targeted benchmarks below, not the vibes boards.

---

## 1. Ask-vs-assume / clarification / proactivity

**Verdict: a genuinely UNSOLVED, NOT-saturated capability** — which makes it a real differentiator. The dominant failure is *under*-clarification (over-assuming); an inverse trap (*over*-asking on false-premise/unanswerable inputs) also appears, so the best benchmarks score ask-rate **together with** accuracy (calibration), not ask-rate alone.

| Benchmark | Measures | Metric | Date | Open-weight signal | Conf. |
|---|---|---|---|---|---|
| **InteractComp** ⭐ | Search agents: ask to disambiguate vs assume an interpretation | Accuracy + **interaction-rate** (true calibration) | 2025-10 ([2510.24668](https://arxiv.org/abs/2510.24668)) | Brutal: top model (GPT-5) **13.7%**. **DeepSeek-R1 best-calibrated open** (13.1% @ 44.7% ask-rate). All open models (Qwen2.5/3, GLM-4.5, Kimi-K2) over-assume | [solid] |
| **ClarifyMT-Bench** ⭐ | Multi-turn ask-vs-answer, 12 ambiguity subtypes × 6 personas | Clarification accuracy over 6,120 dialogues | 2025-12 ([2512.21120](https://arxiv.org/pdf/2512.21120)) | **Open beats closed at turn 1:** Qwen-2.5-7B **87.4%**, DeepSeek-R1 84.6% > GPT-4.1 (77.7%), o3 (71.8%). But Llama-3.1-8B collapses (53%) and ALL degrade sharply by turn 3 | [solid] |
| **AskBench** | When+what to ask: intent-deficient + false-premise queries | Accuracy, coverage, redundant-ask rate | 2026-04 ([2602.11199](https://arxiv.org/pdf/2602.11199)) | Stock Qwen-2.5-7B weak (0.33); authors' RLVR-tuned jumps to 0.62 | [solid] |
| **ClarEval** | Code agents under ambiguous specs | Key-Q coverage, missing-premise recall, avg-turns-to-clarify | 2026-02 ([2603.00187](https://arxiv.org/html/2603.00187v1)) | Qwen3-Coder competitive on coverage but needs ~60% more turns than GPT-5-Coder | [solid] |
| **ClarQ-LLM** | Identify uncertainty, resolve via clarifying Qs in task dialog | Success rate, query length | 2024-09 ([2409.06097](https://arxiv.org/html/2409.06097v1)) | **Llama-3.1-405B leads everyone (60.5%)** > GPT-4o (50.8%), but verbose | [solid] |
| **IN3 / Mistral-Interact** | Detect vague instructions, query missing details | Vagueness-judgment acc | 2024-02 ([2402.09205](https://arxiv.org/pdf/2402.09205)) | ⚠️ 85% is from a model **fine-tuned on IN3's own data** — NOT off-the-shelf behavior | [solid] |
| **ProactiveAgent** | Suggest tasks proactively from context | F1 | ICLR'25 | ⚠️ Same gaming: Qwen2-7B-Proactive 66.5% F1 is **tuned on the benchmark** | [solid] |
| **CLAMBER / Abg-CoQA / ClariQ** | Older clarification-question generation | BLEU/F1/detection | 2020–24 | Pre-LLM lineage; superseded. **"ClariQ-2" does not appear to exist** | [solid]/[hearsay] |

**Flags:** IN3/Mistral-Interact and ProactiveAgent report headline open-weight numbers from models **fine-tuned on the benchmark's own training split** — don't read them as base-model evidence. "ProactiveBench" name collides across ≥3 unrelated benchmarks (LLM-agent / Video-LLM / MLLM). **Ask-Now-Use-Later** (2026-05) shows a **62–77pt proactivity gap** vs oracle but is proprietary-models-only.

**Local pick:** Qwen-2.5-7B-Instruct (single-turn decision), DeepSeek-R1 distill (best-calibrated under agentic ambiguity), Qwen3-Coder (code-agent). **Mitigation:** an explicit system rule — *"if the request is ambiguous or missing detail needed to act correctly, ask ONE clarifying question before proceeding"* — directly targets the behavior models skip by default.

---

## 2. Abstention — knowing what you don't know

**Verdict: UNSOLVED, and scaling does not help** (Llama-8B ≈ Llama-405B on AbstentionBench). Good news for local users: **this is the open-weight sweet spot.**

| Benchmark | Measures | Metric | Open-weight signal | Date | Conf. |
|---|---|---|---|---|---|
| **AbstentionBench** ⭐ | Holistic abstention: unanswerable, underspecified, false-premise, stale, subjective (20 datasets / 35K Q) | Abstention recall/precision/F1 (LLM-judge) | **Qwen 2.5-32B ties GPT-4o for #1.** Scale doesn't help. ⚠️ **Reasoning FT degrades it ~24%** | 2025-06 ([2506.09038](https://arxiv.org/abs/2506.09038)) | [solid] |
| **Refusal Index (RI)** ⭐ | Knowledge-aware refusal, **decoupled from accuracy** | Spearman corr(refusal prob, error prob) | 16 models; refusal behavior found unreliable/fragile. Cleanest metric on this axis | 2025-10 ([2510.01782](https://arxiv.org/abs/2510.01782)) | [solid] |
| **SelfAware** | Recognize unanswerable/unknowable Qs | F1 of unanswerable detection | Canonical 2023 self-knowledge set; GPT-4 75.5% | 2023-05 | [solid] |
| **R-Tuning** | *Method*+eval: tune to say "I don't know" | Refusal rate on unanswerable sets | Refusal shown to be a generalizable meta-skill (open models) | NAACL'24 | [solid] |
| **FactGuard-Bench** | Unanswerable detection in **long-context** (4K–128K) | Answerable/unanswerable accuracy | Best of 9 LLMs only 67.7%; training → 81% | 2025-04 | [solid] |
| **FaithEval / HalluLens-Nonsense** | Abstain when evidence removed / refuse fake entities | Faithfulness / false-acceptance | Qwen2.5 low false-refusal; **Llama-3.1-8B over-refuses (83%)** | 2024–25 | [solid] |
| **AbstentionTemporalQA** ("When Silence Is Golden") | Abstention in temporal QA, framed as teachable via CoT+RL | Abstention-aware reward | Freshest successor, ICLR'26 | 2026-02 | [solid] |
| **SQuAD 2.0** | Reading-comprehension abstention | EM/F1 no-answer | ⚠️ **SATURATED** for modern LLMs | 2018 | [solid] |

**Flags:** (1) **SQuAD 2.0 saturated** — floor only. (2) **Reasoning models game the wrong objective** — high accuracy but worse abstention. (3) **Over-abstention ≠ good abstention** — raw refusal rate is gameable (refuse-everything scores high; Llama-3.1-8B's 83% refusal is a *failure*). Prefer **RI** (corr) and **precision/F1**, not recall alone. (4) **Parametric** ("does it know the fact at all" — AbstentionBench/RI) vs **contextual** ("is it in the provided text" — FactGuard/FaithEval) are different "don't-know"s; don't conflate.

**Local pick:** **Qwen 2.5-32B / Qwen3** (ties GPT-4o, runnable quantized in 64GB). **Avoid reasoning-distilled variants for this axis.**

---

## 3. Calibration & hallucination

**Verdict: hallucination is measurable and open weights are competitive; calibration in absolute terms is poor for EVERY model** (ECE 0.1–0.4 across the board, ~12pt confidence-accuracy gap even for the best frontier model).

| Benchmark | Measures | Metric | Open-weight signal | Date | Conf. |
|---|---|---|---|---|---|
| **AA-Omniscience** ⭐ | Knowledge reliability: rewards correct, **penalizes confident-wrong, rewards "I don't know"** | Omniscience Index + Hallucination Rate | Best single calibration map. Cohere Command A+ (open) lowest hallu (14.1%); Qwen3 competitive. "All but 3 models more likely to hallucinate than be correct" | 2025-11 ([2511.13029](https://arxiv.org/html/2511.13029v1)) | [solid] |
| **Vectara HHEM** ⭐ | Intrinsic hallucination in summarization/RAG (live board, FaithJudge) | Hallucination Rate % + Answer Rate % | **Llama-3.3-70B 4.1%, Gemma-3-12B 4.4%, Mistral-Large 4.5%, Qwen3-8B 4.8%** — all within ~1pt of frontier | updated 2026-05-11 ([repo](https://github.com/vectara/hallucination-leaderboard)) | [solid] |
| **SimpleQA-Verified** | Short-form parametric factuality + **stated-confidence calibration** | F1 (correct/incorrect/not-attempted); confidence probes | Gemini 2.5 Pro F1 55.6 leads; **Qwen3 family ranks #2–#5** (235B 50.6%, Next-80B 40.1% — 64GB-feasible). All models overstate confidence | 2025-09 ([2509.07968](https://arxiv.org/html/2509.07968v1)) | [solid] |
| **FACTS Grounding** | Faithful answers using only a long source doc | Factuality % (3 LLM judges) | ⚠️ Closed-model-dominated (Gemini/Claude/GPT); no open-weight in top 5. v2 hard (no model >70%) | v2 2025-12 ([Kaggle](https://www.kaggle.com/benchmarks/google/facts-grounding)) | [solid] |
| **HalluLens** | Extrinsic vs intrinsic hallucination + fake-entity refusal | False-acceptance rate | Llama-3.1-405B best at refusing fake entities (6.9%); some Mistral >80% (bad) | ACL'25 | [solid] |
| **MASK / BeHonest** | **Honesty ≠ accuracy** — does it *lie under pressure* | Honesty score (lower=more honest) | Larger/more-accurate models do NOT lie less. Distinct axis from calibration | 2024–25 | [solid] |
| **ConFiQA** | Context-faithfulness under knowledge conflict (RAG) | Faithfulness accuracy | Used inside method papers (Llama/Qwen); no standalone board | 2025 | [single-source] |
| **ECE** (the metric) | Confidence-accuracy gap | Σ binned \|acc−conf\| | Everyone miscalibrated (0.108–0.427); format choice dominates | metric, per-paper | [solid] |
| **TruthfulQA** | ✕ Imitation of human falsehoods | MC/gen accuracy | ⚠️ **SATURATED, in training data, mislabeled gold, gameable.** Small models (Phi, Granite) top it — red flag | 2021 | [solid] |

**Flags:** **TruthfulQA — do not use as a primary signal** (contaminated, mislabeled, gameable, measures imitation not hallucination; small models top it). HHEM's low-hallucination can be **gamed by high refusal** → always read the Answer Rate column (the board exposes it, which is why it stays trustworthy). "Safetywashing" caution: many honesty/safety benchmarks just track general capability — MASK and AA-Omniscience are explicitly designed to resist this.

**Local pick:** Llama-3.3-70B / Gemma-3 / Qwen3-8B for low hallucination in RAG; Qwen3-Next-80B for factual recall. No model (open or closed) has trustworthy calibration in absolute terms.

---

## 4. Instruction-following reliability

**Verdict: plain IFEval is SATURATED AND PARTIALLY GAMED — stop using it to rank good models.** The discriminating successors (built *because* IFEval saturated) put everyone at 50–70%. Multi-turn is the universal weak spot.

| Benchmark | Measures | Metric | Leader / open-weight | Date | Conf. |
|---|---|---|---|---|---|
| **IFEval** | ~500 programmatically-verifiable constraints | Strict/loose × prompt/instruction-level | ⚠️ **SATURATED:** Qwen3.5-27B 0.950 (open) tops; Llama-3.3-70B 0.921, Gemma-3-27B 0.904, DeepSeek-V3 0.861 | 2023 | [solid] |
| **IFBench** ⭐ | Generalization to **held-out** constraints | Prompt-level loose acc, single+multi-turn | Built because IFEval saturated. o3 69.3; **open: Qwen2.5+IF-RLVR 53.7**, Llama-3.1+IF-RLVR 52.7, DeepSeek-R1 38.0 | 2025-07 ([2507.02833](https://arxiv.org/abs/2507.02833)) | [solid] |
| **Multi-IF** ⭐ | Multi-turn (3 turns) + multilingual; "Instruction Forgetting Rate" | Per-turn acc + final | **Llama-3.1-405B ties o1-preview at top (0.707)**; ALL degrade monotonically turn 1→3 | 2024-10 ([2410.15553](https://arxiv.org/abs/2410.15553)) | [solid] |
| **IFEval++ / reliable@k** ⭐ | **Same instruction under 9 rephrasings** — reliability proper | reliable@k (success across all variants) | Drops up to **61.8%** under rephrasing; **IFEval rankings invert** (a #17 model rises to #7). Most on-axis for "reliability" | 2025-12 ([2512.14754](https://arxiv.org/html/2512.14754v1)) | [solid] |
| **AdvancedIF** | Human-written prompts+rubrics; brand voice, competing system priorities | Human-graded | Built because IFEval is gameable (syntactic constraints satisfiable by incoherent text) | 2026-02 ([2511.10507](https://arxiv.org/abs/2511.10507)) | [solid] |
| **FollowBench / InfoBench / ComplexBench** | Multi-level / decomposed / composed constraints | HSR-SSR / DRFR / composition-aware | GPT-4-class led at release; open models lag on style/composition | 2024 | [solid]/[single-source] |
| **SysBench / RuleBench / CFBench** | System-msg following / inferential rules / Chinese constraints | CSR / rule-acc / multi-dim | Distinct sub-axes (system prompt, if-then rules) | 2024–25 | [single-source] |

**Flags:** **IFEval saturated + gamed** — (1) >80% on IFEval → <50% on held-out constraints (overfitting); (2) syntactic constraints satisfiable by incoherent text (rewards rule-gaming). **Reasoning/CoT models can do *worse* on strict IFEval** (lose formatting mid-thought). **Multi-turn degradation is universal**, not a single-benchmark artifact.

**Local pick:** Qwen3.5 9B–27B or Llama-3.3-70B-Instruct (general single-turn); + IF-RLVR training closes most of the gap to o3 on hard OOD constraints; expect degradation past turn 2 on chained instructions.

---

## 5. Smart defaults / commonsense judgment

**Verdict: the popular human-preference arenas DO NOT map to this axis** — they reward confident, thorough, well-formatted answers (the opposite of "ask when you should / abstain when unsure"). The axis is actually measured by the abstention/clarification/pragmatics cluster.

| Benchmark | Maps to "smart defaults"? | Why | Conf. |
|---|---|---|---|
| **AbstentionBench** ⭐ | **YES — strongest direct map** | "Don't make a wrong confident default" side; Qwen2.5-32B ties GPT-4o | [solid] |
| **QuestBench** | **YES — "ask a good question" side** | Identify the one missing fact to ask for | [single-source] |
| **CLAMBER / ConfuseBench** | YES — ask-vs-assume calibration | Recognize uncertainty vs over/under-ask (EVPI-scored) | [single-source] |
| **PUB / PragmEval** | YES — commonsense default *inference* | Infer the intended (sensible-default) reading | [solid] body / [hearsay] rankings |
| **Social IQa** | PARTIAL — dated, saturated | Commonsense MC, pre-LLM; floor only | [solid] |
| **LMArena** | ✕ **NO — general vibes** | Conflates correctness/tone/length; rewards never-clarifying | [single-source] numbers |
| **Arena-Hard v2** | ✕ NO, but **least length-biased** | Ships explicit **Style Control** (`--control-features markdown length`); open: Qwen3-235B 58.4%, Qwen3-32B 44.5% | [solid] |
| **WildBench / MixEval-Hard** | ✕ NO | Realistic but still answer-quality; MixEval built to *reproduce* Arena Elo (0.96 corr) cheaply | [solid] |

**Flags:** (1) **Arenas measure the wrong thing** — a model can top them by never clarifying. (2) **Length/markdown/style bias pervasive** — only Arena-Hard v2 Style-Control factors it out; always prefer the style-controlled number. (3) **Reasoning↑ ≠ judgment↑** — the AbstentionBench −24% finding means math/reasoning leaders can be *worse* at sensible defaults; the user's axis and the reasoning boards point opposite directions. (4) **The directly-relevant cluster has NO unified live leaderboard** — individual 2024–2025 papers; AbstentionBench is the only one with a clean open-vs-closed comparison.

**Local pick:** **Qwen2.5/Qwen3-32B class** — ties GPT-4o on AbstentionBench *and* scores well on Arena-Hard v2, while runnable. June-2026 open names to watch at this size: MiMo-V2-Flash, Nemotron-3 Nano (30B-A3B), Qwen3-Next-30B-A3B. Avoid pure reasoning-distilled variants if sensible-default-under-ambiguity is the priority.

---

## 6. Cross-cutting curation — what to trust, what to ignore

### Trust these (on-axis, not saturated, expose calibration honestly)
- **InteractComp** — ask-vs-assume *with* interaction-rate (real calibration), brutally hard
- **AbstentionBench** + **Refusal Index** — abstention, scale-resistant, RI is accuracy-decoupled
- **AA-Omniscience** — the cleanest calibration map (penalizes confident-wrong, rewards IDK)
- **Vectara HHEM** — live hallucination board, open weights competitive, exposes refusal-gaming
- **IFBench / Multi-IF / IFEval++** — the discriminating instruction-following frontier

### Ignore / heavily discount these
- **TruthfulQA** — saturated, contaminated, mislabeled, gameable; small models top it
- **Plain IFEval** — saturated + gamed; floor check only, never a ranker for strong models
- **SQuAD 2.0** — saturated abstention floor
- **Social IQa** — dated, solved
- **LMArena / Arena-Hard / WildBench / MixEval** as a *smart-defaults* proxy — they reward the opposite behavior. Fine as weak general-quality signals; for this user's axis, wrong thing.
- **IN3/Mistral-Interact, ProactiveAgent** headline numbers — tuned on their own benchmark; not base-model evidence

### The meta-trap (most actionable)
**Do not pick a local model for judgment by its reasoning/math leaderboard rank.** Reasoning fine-tuning measurably *degrades* abstention (~24%) and can degrade strict instruction-following. For ask/abstain/calibrate/instruction-follow, the reasoning-distilled variants (DeepSeek-R1-Distill, s1.1, QwQ) are often the *worst* choices despite topping the reasoning boards.

### One model family keeps winning the open-weight slot
**Qwen (2.5 / 3 / 3.5, 7B–32B class)** is the recurring open-weight leader across *all five* judgment axes and fits a 64GB Mac quantized — strongest single local bet. Llama-3.3-70B is the runner-up for hallucination + instruction-following; Gemma-3 for low hallucination. The non-distilled (non-"thinking") instruct variants are preferable for judgment.

---

## Detailed family files (in this directory)
- `clarification-proactivity.md` — ask-vs-assume (9 core + 6 proactivity benchmarks)
- `abstention.md` — knowing-what-you-don't-know (9 + 2 adjacent)
- `calibration-hallucination.md` — calibration + hallucination (8 benchmarks + ECE + TruthfulQA teardown)
- `instruction-following.md` — IF reliability (9 core + 6 successors)
- `smart-defaults-humanpref.md` — arenas (wrong-thing) + the cluster that actually maps
