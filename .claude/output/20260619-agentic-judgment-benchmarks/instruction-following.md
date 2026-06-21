# Instruction-Following / Constraint-Following Benchmarks

**User axis:** instruction-following reliability — how dependably a model obeys explicit
constraints (format, length, content, system-prompt rules) across single- and multi-turn use.

**Research date:** 2026-06-19 · all sources fetched live (not from memory).
**Local context:** user runs open-weight models on a 64GB Mac, so open-weight scores are flagged.

---

## TL;DR for the local-models use case

- **IFEval is saturated** for frontier and strong open-weight models (top scores ~0.92–0.95);
  it no longer differentiates the good models and is partly *gamed* (syntactic constraints
  reward gaming the rule, not coherence). Use it only as a floor check, not a discriminator.
- **Qwen dominates open-weight instruction-following** on IFEval (Qwen3.5 family tops the
  llm-stats board at 0.95) and is competitive on the harder benchmarks. For a 64GB Mac, a
  Qwen3.5 9B–27B-class or Llama-3.3-70B-Instruct model is the strongest local IF bet.
- The **discriminating benchmarks now are IFBench, Multi-IF, IFEval++ and AdvancedIF** — all
  built specifically because IFEval saturated. On these, *everyone* (including frontier) drops
  to 50–70%, so they actually rank models.
- **Multi-turn is the real weak spot**: every model degrades monotonically across turns
  (Multi-IF: o1-preview 0.877 → 0.707 from turn 1→3). Relevant if the user chains instructions.

---

## Benchmark-by-benchmark

| Benchmark | What it measures | Metric | Leader / open-weight standing | Date | Confidence |
|---|---|---|---|---|---|
| **IFEval** | ~500 prompts with programmatically *verifiable* constraints (word count, format, keyword inclusion/exclusion, casing) | Strict & loose accuracy, at prompt-level and instruction-level | Qwen3.5-27B **0.950** (open) tops llm-stats; Llama-3.3-70B **0.921**, Gemma-3-27B 0.904, Kimi-K2 0.898, DeepSeek-V3 0.861. Avg across 65 models 0.846 | Google, late 2023 (arXiv 2311.07911) | [solid] |
| **IFBench** | Generalization to **new, held-out** verifiable constraints (58 OOD constraints on WildChat prompts) — built *because IFEval saturated* | Prompt-level loose accuracy; single-turn (~300) + multi-turn (~1,300) | OpenAI o3 **69.3**; open: Qwen2.5+IF-RLVR **53.7**, Llama-3.1+IF-RLVR 52.7, OLMo2+IF-RLVR 47.3, DeepSeek-R1 38.0. Gemini-2.5-Pro 52.3, Claude-4-Sonnet ~50. AA board: Grok-4.3 83.3, MiniMax-M3 82.9 (open) | AI2 + UW, arXiv 2507.02833, posted 2025-07-03, NeurIPS 2025 D&B | [solid] |
| **Multi-IF** | Multi-turn (3 turns) + multilingual (8 languages) instruction following; introduces "Instruction Forgetting Rate" (IFR) | Per-turn accuracy + final-turn FinalMetric | o1-preview **0.707** & Llama-3.1-405B **0.707** (open) tie top; o1-mini 0.681; Llama-3.1-70B 0.668; GPT-4o / Claude-3.5-Sonnet / Qwen-2.5-72B all >0.6. **All degrade across turns** | Meta (facebookresearch/Multi-IF), arXiv 2410.15553, Oct 2024 | [solid] |
| **FollowBench** | Multi-level fine-grained constraints across 5 types (Content, Situation, Style, Format, Example); adds one constraint per level | Hard Satisfaction Rate (HSR) / Soft Satisfaction Rate (SSR) per level | GPT-4-class led at release; 13 open+closed models evaluated. Open models lag on Style/Situation | ACL 2024, arXiv 2310.20410 | [solid] |
| **InfoBench** | Decomposes complex instructions into individual simple requirements and checks each | **DRFR** (Decomposed Requirements Following Ratio) | GPT-4 led at release; finer-grained than IFEval. Open models trail on decomposed sub-requirements | 2024 (arXiv 2401.03601) | [single-source] |
| **ComplexBench** | Complex instructions = multiple constraints *composed* (And/Chain/Selection/Nested); 4 types, 19 dims, 4 composition modes | Rule-augmented LLM-as-judge, composition-aware scoring | GPT-4-class led; composition (esp. nested/selection) is where models fail | NeurIPS 2024, arXiv 2407.03978 | [solid] |
| **CFBench** | Comprehensive **Chinese** constraints-following; 1,000 samples, 200+ scenarios, 50+ NLP tasks, 10 constraint categories / 25+ subcats | Multi-dim assessment w/ requirement prioritization (CSR/ISR/PSR-style); "substantial room for improvement" reported | Leading LLMs still leave large gap to ceiling; specific per-model scores in full PDF only | ACL 2025 (2025.acl-long.1581) | [single-source] |
| **SysBench** | **System-message** following specifically: constraint violation, instruction misjudgement, multi-turn instability. 500 system msgs, 6 constraint types (action/content/background/role/format/style) | Constraint Satisfaction Rate + Instruction-following across multi-turn | Evaluates how models honor *system prompts* vs user turns — distinct axis. Per-model scores in paper | 2024 (arXiv 2408.10943) | [single-source] |
| **RuleBench** | **Inferential rule following** — if-then rules embedded in instructions (differs from affirmatively-stated constraints) | Rule-application accuracy | Tests reasoning-under-rules, not just surface constraint matching | 2024 | [single-source] |

---

## Newer successors / 2025–2026 (the discriminating frontier)

| Benchmark | What it measures | Why it matters | Date | Confidence |
|---|---|---|---|---|
| **IFEval++ / reliable@k** ("Revisiting the Reliability of LMs in Instruction-Following") | **Nuance-oriented reliability**: 541 IFEval cases × 9 "cousin" prompts (rephrase / distractor / constraint reconfig). Does the model obey the *same* instruction under varied phrasing? | Directly the user's "reliability" axis. Performance drops **up to 61.8%** under nuance; even GPT-5 drops 18.3%. **Ranking inversions** vs IFEval (a #17 model rises to #7) — proves IFEval accuracy ≠ reliability. `reliable@k` = success across all k related prompts | arXiv 2512.14754, Dec 2025 | [solid] |
| **AdvancedIF** | Human-written prompts + rubrics (no synthetic). Real intent: brand voice under pressure, multi-turn memory, competing system-prompt priorities | Built by Meta Superintelligence Labs + Surge **because IFEval is gameable** (syntactic constraints reward nonsense that still passes). Human-graded, not programmatic. Verifier hits 0.728 F1 w/ humans; Llama-4-Maverick +6.7% abs after training on it | arXiv 2511.10507, blog 2026-02-05 | [solid] |
| **StructFlowBench** | Structured multi-turn instruction following with inter-turn dependency flow | Multi-turn structure that Multi-IF doesn't model | arXiv 2502.14494, Feb 2025 | [single-source] |
| **EIFBench** | "Extremely complex" instruction following — many simultaneous constraints | Stress-tests constraint density | arXiv 2506.08375, Jun 2025 | [single-source] |
| **IF-RewardBench** | Benchmarks **judge models** for IF evaluation (meta-eval of LLM-as-judge for instruction following) | Relevant if user uses an LLM judge to score local outputs | arXiv 2603.04738, 2026 | [single-source] |
| **FireBench** | Instruction following in enterprise / API-driven app settings | Production-shaped IF | arXiv 2603.04857, 2026 | [single-source] |

---

## Saturation / gaming flags (explicit)

- **IFEval — SATURATED and partially GAMED.** [solid] Top open + frontier models cluster at
  0.90–0.95. Two independent critiques: (1) AI2/IFBench — models scoring >80% on IFEval drop
  **below 50%** on held-out constraints, i.e. high IFEval = overfitting, not general IF;
  (2) Surge/AdvancedIF — IFEval's syntactically-verifiable constraints ("avoid the letter C")
  can be satisfied by **incoherent** text, so the score rewards rule-gaming over real
  instruction satisfaction. **Do not use IFEval to rank strong models.**
- **Reasoning/CoT models can do *worse* on strict IFEval** [single-source] — extended thinking
  causes them to "lose track" of formatting constraints mid-reasoning. Worth noting for local
  reasoning models (DeepSeek-R1-distills, QwQ).
- **Multi-turn degradation is universal** [solid] — not a single-benchmark artifact; every
  model in Multi-IF drops monotonically turn 1→3.

---

## Practical guidance for a 64GB Mac (open-weight)

| Need | Best local pick (per these benchmarks) | Evidence |
|---|---|---|
| General single-turn IF | **Qwen3.5 9B–27B** (IFEval 0.90–0.95) or **Llama-3.3-70B-Instruct** (0.921) | llm-stats IFEval board [solid] |
| Harder / OOD constraints | Qwen2.5 or Llama-3.1 base **+ IF-RLVR** training closes most of the gap to o3 on IFBench (52–54 vs 69) | IFBench paper [solid] |
| Multi-turn chains | Llama-3.1-70B (0.668) is the strongest sub-405B open option; expect degradation past turn 2 | Multi-IF [solid] |
| Reliability under rephrasing | No open-weight number published yet on IFEval++; treat as an **open risk** — rejection sampling (k attempts + select) materially helps weaker models | reliability paper [solid] |

**Caveat:** Benchmark leaderboards (esp. llm-stats / Artificial Analysis) list future-dated model
names (Qwen3.5, Grok 4.3, MiniMax-M3, GPT-5) — these reflect the live boards as of 2026-06-19 and
are reproduced as found. Verify a specific model's score on the live board before committing.

---

## Sources

- IFEval leaderboard — https://llm-stats.com/benchmarks/ifeval
- IFBench (AI2) repo — https://github.com/allenai/IFBench · paper arXiv 2507.02833
- IFBench leaderboard — https://artificialanalysis.ai/evaluations/ifbench
- Multi-IF (Meta) — https://github.com/facebookresearch/Multi-IF · arXiv 2410.15553 · leaderboard https://llm-stats.com/benchmarks/multi-if
- FollowBench — https://arxiv.org/abs/2310.20410 · https://github.com/YJiangcm/FollowBench
- ComplexBench — https://arxiv.org/pdf/2407.03978 · https://openreview.net/forum?id=U2aVNDrZGx
- CFBench — https://aclanthology.org/2025.acl-long.1581/
- AdvancedIF (Meta + Surge) — https://surgehq.ai/blog/advancedif-and-the-evolution-of-instruction-following-benchmarks · arXiv 2511.10507
- IFEval++ / reliability — https://arxiv.org/html/2512.14754v1
- StructFlowBench — https://arxiv.org/pdf/2502.14494 · EIFBench — https://arxiv.org/pdf/2506.08375
- IF-RewardBench — https://arxiv.org/html/2603.04738 · FireBench — https://arxiv.org/pdf/2603.04857
