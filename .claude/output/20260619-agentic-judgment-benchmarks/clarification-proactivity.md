# Clarification / Proactivity Benchmarks — Ask-vs-Assume Axis

**Research date:** 2026-06-19
**User axis:** ask-vs-assume / proactivity — does the model know *when to ask a clarifying question* vs just answering?
**User constraint:** runs local/open-weight models on a 64GB Mac (Qwen, Llama, Mistral, DeepSeek, Gemma).
**Sourcing:** live WebSearch + WebFetch against arXiv / GitHub / alphaXiv (June 2026). Confidence flags per row.

---

## TL;DR for a local-model user

- **The field is NOT saturated** — it is the opposite. The newest benchmarks (InteractComp, AskBench, ClarEval, Ask-Now-Use-Later) all show frontier *and* open models scoring badly (often single-digit to ~60%), with large human gaps. This is a genuine, unsolved capability — good for picking a model that's differentiated here.
- **The dominant failure mode is UNDER-clarification (over-assuming).** Models barrel ahead with assumptions instead of asking. A second, opposite failure (over-clarification on refusal-style/unanswerable inputs) shows up in AskBench/ClarifyMT.
- **Open-weight models CAN be competitive on the *single-turn* ask/answer decision** — Qwen-2.5-7B and DeepSeek-R1 actually beat several closed models on ClarifyMT-Bench turn-1. But they **degrade fast in multi-turn**, ask *inefficiently* (more turns for same result — ClarEval), and **over-assume** in agentic search (InteractComp).
- **Best open-weight signal for a 64GB-Mac user:** **Qwen-2.5-7B-Instruct** and **DeepSeek-R1** for the ask/answer decision; **Qwen3-Coder** if the use case is code-agent clarification. None are "solved" — treat clarification as a known weak spot to prompt around (explicitly instruct the model to ask before assuming).
- **Caveat — fine-tuned specialist models inflate numbers.** IN3/Mistral-Interact and ProactiveBench numbers come from models *trained on the benchmark's own data*. Those scores measure "can a small model be tuned for this," not "does the off-the-shelf model do it." Don't read Mistral-Interact's 85% as "Mistral-7B asks well out of the box."

---

## Core benchmarks (ask-vs-assume / clarification)

| Benchmark | What it measures | Metric | Date / venue | Open-weight signal | Paper | Conf. |
|---|---|---|---|---|---|---|
| **IN3 + Mistral-Interact** ("Tell Me More!") | Whether an agent detects vague instructions and proactively queries missing details before acting ("fake success" problem) | Vagueness-judgment accuracy; Missing-detail recovery rate; Summary intention coverage | 2024-02-14, arXiv | **Mistral-Interact (tuned Mistral-7B)**: 85.19% vagueness-judgment acc, ~96% intention coverage — matches/beats GPT-4 on several axes. But it's **fine-tuned on IN3 data**, not off-the-shelf. Base LLaMA-2-7B / Mistral-7B do far worse. | [arXiv 2402.09205](https://arxiv.org/pdf/2402.09205) · [summary](https://ai-scholar.tech/en/articles/chatgpt/IN3) | [solid] |
| **ClarifyMT-Bench** | Multi-turn: whether to ask a clarifying question or answer directly, across 12 ambiguity subtypes & 6 user personas | Clarification Accuracy (correct ask/answer action rate) over 6,120 dialogues, ~2.67 turns avg | 2025-12-24, arXiv preprint | **Open beats closed at turn 1:** Qwen-2.5-7B **87.4%**, DeepSeek-R1 84.6%, Llama-3.1-70B 83.1% — all above GPT-4.1 (77.7%), o3 (71.8%), Claude-Sonnet-4.5 (75.1%). Only Gemini-2.5-Flash (89.4%) higher. **BUT** Llama-3.1-8B collapses (53.4%) and all models degrade sharply turns 2→3 (GPT-4.1: 77.7→56.9→55.9). | [arXiv 2512.21120](https://arxiv.org/pdf/2512.21120) · [overview](https://www.alphaxiv.org/overview/2512.21120v1) | [solid] |
| **AskBench** | When AND what to ask: intent-deficient queries (AskMind) + false-premise queries (AskOverconfidence) | Accuracy; Coverage (rubric checkpoints resolved before answering); Redundant-questioning rate | 2026-04-20 (v2), arXiv | Qwen-2.5-7B **baseline is weak**: 0.332 acc / 0.214 cov on AskMind. Authors' **RLVR-tuned Qwen** ("OursI/OursO") jumps to ~0.62 acc / 0.68–0.81 cov. Gemini strong on overconfidence (0.840). Llama/Mistral/DeepSeek not tested. | [arXiv 2602.11199](https://arxiv.org/pdf/2602.11199) | [solid] |
| **InteractComp** | Search agents with deliberately ambiguous queries: ask for disambiguation vs assume an interpretation | Task accuracy; Interaction rate (% of rounds the agent asks) — calibration of ask vs assume | 2025-10, arXiv | **Brutally hard & exposes over-assuming.** Best model (GPT-5) only **13.73%**. **DeepSeek-R1 best open-weight: 13.08% acc @ 44.72% interaction rate** (best-calibrated). GPT-4o-mini asks most (73.95%) but only 7.14% acc. With-context jumps to 40–71% → *interaction is the bottleneck, not knowledge.* Open models tested: Qwen2.5, Qwen3-235B, DeepSeek-Chat/R1, GLM-4.5, Kimi-K2 — all over-assume. | [arXiv 2510.24668](https://arxiv.org/abs/2510.24668) | [solid] |
| **ClarEval** | Code agents under ambiguous instructions: intent inference, missing-requirement identification, interaction efficiency | KQC (key-question coverage), PIR (premise ID), MPR (missing-premise recall), ATC (avg turns to clarify, lower=better), EAR (efficiency-adjusted recall) | 2026-02-27, arXiv | Open code models competitive on *coverage* but *inefficient*: **Qwen3-Coder** KQC 0.668 / MPR 0.640 / ATC 1.645; Qwen2.5-Coder 0.544 / 0.643 / **ATC 2.396** (60% more turns than GPT-5-Coder for similar intent detection). GPT-5-Coder MPR 0.951; Claude-Opus-4.1 KQC 0.754. | [arXiv 2603.00187](https://arxiv.org/html/2603.00187v1) | [solid] |
| **ClarQ-LLM** | Whether a model identifies uncertainty in task-oriented dialog and resolves it via clarifying questions | Success Rate (all required info gathered); Avg Query Discrepancy; Avg Query Length | 2024-09, arXiv | **Llama-3.1-405B best of all (60.5% success)**, beating GPT-4o (50.8%) and GPT-4 (29.6%) — but verbose ("excessively high" query length). Human ~85%. Shows a large open model *can* lead on asking, at a verbosity cost. | [arXiv 2409.06097](https://arxiv.org/html/2409.06097v1) | [solid] |
| **Abg-CoQA** | Conversational QA: detect ambiguous question, ask clarification instead of answering (entity/time/answer-type/event ambiguity) | BLEU-1 for clarification-Q gen; F1 for post-clarification answer | 2021, AKBC (foundational, predecessor) | Pre-LLM era; best system BLEU-1 12.9% vs human 40.8%; QA-after-clarify F1 40.1% vs human 75.2%. **Large human gap = headroom.** Historical baseline, superseded by CLAMBER/ClarifyMT. | [OpenReview](https://openreview.net/forum?id=SlDZ1o8FsJU) · [code](https://github.com/MeiqiGuo/AKBC2021-Abg-CoQA) | [solid] |
| **CLAMBER** | Identify & clarify ambiguous information needs; taxonomy of ambiguity types | Ambiguity-detection accuracy; clarification quality | 2024-05 (ACL '24), arXiv | LLMs show "false sense of confidence" — fail to recognize ambiguity, **over-assume**. Open models included; finding is the over-assumption bias, not a leaderboard win. | [arXiv 2405.12063](https://arxiv.org/pdf/2405.12063) | [solid] |
| **ClariQ / ConvAI3** | Detect ambiguous query in conversational search, generate a good clarifying question | Clarification-question selection/generation quality (document-relevance based) | 2020, SCAI@EMNLP / ConvAI3 challenge | **Foundational, pre-LLM, effectively superseded.** No modern open-weight leaderboard. **No evidence of a "ClariQ-2"** despite searching — treat that name as not-yet-existing. | [GitHub](https://github.com/aliannejadi/ClariQ) · [arXiv 2009.11352](https://arxiv.org/pdf/2009.11352) | [solid] (ClariQ) / [hearsay] (ClariQ-2 — not found) |

---

## Proactivity benchmarks (broader "act/ask before told" axis)

| Benchmark | What it measures | Metric | Date | Open-weight signal | Paper | Conf. |
|---|---|---|---|---|---|---|
| **ProactiveBench / ProactiveAgent** (Lu et al.) | Predict & suggest tasks proactively from environment/activity context, without explicit request | Recall/Precision/Accuracy/False-Alarm/**F1** | ICLR 2025 (Jan) | **Fine-tuned open models lead:** Qwen2-7B-Proactive **66.47% F1**, LLaMA-3.1-8B-Proactive 66.25% (vs untuned 60.7%/55.1%). Reward model 0.918 F1. Again: *tuned on the benchmark's data.* | [GitHub thunlp/ProactiveAgent](https://github.com/thunlp/ProactiveAgent) | [solid] |
| **Ask Now, Use Later** (Proactivity Gap) | "Ask-to-Remember": ask for *reusable* preferences during a session to apply in *later* offline test sessions | TSAcc (test-session accuracy on tasks bound to hidden standing rules) | 2026-05-27, arXiv | **Proprietary-only** (GPT-5.4, Claude Opus 4.7, Gemini 3, Qwen3.6-Plus API, MiniMax M2.7, DeepSeek V4 — all closed/API). Default agents 15.0–23.7% vs oracle 82.5–96.7% → **62–77 pt proactivity gap.** No local-weight eval. | [arXiv 2605.28108](https://arxiv.org/html/2605.28108v1) | [solid] |
| **PROPER** (knowledge-gap navigation) | Personalized proactive agents navigating user knowledge gaps | proactivity / personalization metrics | 2026 (v4), arXiv | PDF was binary; numbers not extracted. Repo exists (i-kiran/ProPer-Agent). | [arXiv 2601.09926](https://arxiv.org/pdf/2601.09926) | [single-source] |
| **ProactiveEval** | Unified framework decomposing proactive dialogue into target-planning + dialogue-guidance | target-planning / guidance scores across 328 environments | 2025-08, arXiv | Framework, not a single leaderboard; useful as eval harness. | [arXiv 2508.20973](https://arxiv.org/pdf/2508.20973) | [single-source] |
| **AMBIG-SWE** | Interactive coding agents overcoming ambiguous issue specs | task resolution under ambiguity | ICLR 2026 (accepted) | Code-agent flavor of ask-vs-assume; complements ClarEval. Numbers not extracted. | [arXiv 2502.13069](https://arxiv.org/pdf/2502.13069) | [single-source] |
| **ProactiveBench (Video-LLM)** | Multimodal: model decides *when* to respond during video playback | timing/response F1 | 2025-07, arXiv | **Different axis (video timing), not text ask-vs-assume.** Listed to disambiguate the name collision. | [arXiv 2507.09313](https://arxiv.org/html/2507.09313v1) | [solid] |

---

## Flags: saturated / gamed / measures-the-wrong-thing

- **NOT saturated (the opposite):** InteractComp (top model 13.7%), AskBench, ClarEval, Ask-Now-Use-Later (62–77pt gaps), Abg-CoQA all show huge human/oracle gaps. This is a genuinely open capability — *good* for differentiating models.
- **GAMED-by-construction (read carefully):** **IN3/Mistral-Interact** and **ProactiveBench (Lu)** report their headline open-weight numbers from models **fine-tuned on the benchmark's own training split**. Those measure "small model *can be tuned* for asking," not off-the-shelf behavior. **Do not cite Mistral-Interact 85% as evidence stock Mistral asks well.** AskBench's "OursI/OursO" are likewise the authors' tuned models.
- **Name collisions / ghosts:**
  - "ProactiveBench" refers to ≥3 unrelated benchmarks (Lu LLM-agent F1; a Video-LLM one; a multimodal "ProactiveBench: Benchmarking Proactiveness in MLLMs"). Always disambiguate.
  - **"ClariQ-2" does not appear to exist** — searches surface only ClariQ/ClariQ-FKw (2020) and unrelated successors. Treat as [hearsay].
  - "ClarifyBench" in the literature = the POMDP/Value-of-Information tool-calling disambiguation work ([arXiv 2511.08798](https://arxiv.org/html/2511.08798v1), "Structured Uncertainty guided Clarification"), distinct from ClarifyMT-Bench.
- **Measures-an-adjacent-thing (not pure ask-vs-assume):** Abg-CoQA / ClariQ are *clarification-question generation/selection* quality (pre-LLM, document-relevance metrics) rather than the agentic *decision* to ask. Useful as lineage, weak as a 2026 model-selection signal.
- **Over-clarification is the inverse trap:** AskBench (AskOverconfidence), ClarifyMT (Refusal persona), and CLAMBER all note models *over-ask* on unanswerable/false-premise inputs even as they *under-ask* on genuinely ambiguous ones. A benchmark reporting only ask-rate (not calibration) measures the wrong thing — InteractComp's pairing of accuracy *with* interaction-rate is the better design.

---

## Practical recommendation for the 64GB-Mac user

1. **For the ask/answer decision (single-turn): Qwen-2.5-7B-Instruct** is the strongest fits-on-Mac open model (87.4% ClarifyMT turn-1, > most closed models). **DeepSeek-R1 distills** are best-calibrated under agentic ambiguity (InteractComp). Both run locally.
2. **Expect multi-turn degradation and over-assuming.** Mitigate with an explicit system-prompt rule: *"If the request is ambiguous or missing detail needed to act correctly, ask ONE clarifying question before proceeding."* The benchmarks show this is exactly the behavior models skip by default.
3. **For code-agent clarification: Qwen3-Coder** (better turn-efficiency than Qwen2.5-Coder per ClarEval).
4. **Avoid trusting tuned-specialist headline numbers** (Mistral-Interact, ProactiveBench-tuned) as evidence about base-model behavior.
5. **Best single benchmark to watch** for this axis going forward: **InteractComp** (accuracy + interaction-rate together = real calibration) and **ClarifyMT-Bench** (open-vs-closed head-to-head with persona stress-tests).

---

## Sources

- IN3 / Tell Me More: https://arxiv.org/pdf/2402.09205 · https://ai-scholar.tech/en/articles/chatgpt/IN3
- ClarifyMT-Bench: https://arxiv.org/pdf/2512.21120 · https://www.alphaxiv.org/overview/2512.21120v1
- AskBench: https://arxiv.org/pdf/2602.11199
- InteractComp: https://arxiv.org/abs/2510.24668
- ClarEval: https://arxiv.org/html/2603.00187v1
- ClarQ-LLM: https://arxiv.org/html/2409.06097v1
- Abg-CoQA: https://openreview.net/forum?id=SlDZ1o8FsJU
- CLAMBER: https://arxiv.org/pdf/2405.12063
- ClariQ / ConvAI3: https://github.com/aliannejadi/ClariQ · https://arxiv.org/pdf/2009.11352
- ProactiveAgent (ICLR 2025): https://github.com/thunlp/ProactiveAgent
- Ask Now, Use Later: https://arxiv.org/html/2605.28108v1
- PROPER: https://arxiv.org/pdf/2601.09926
- ProactiveEval: https://arxiv.org/pdf/2508.20973
- AMBIG-SWE: https://arxiv.org/pdf/2502.13069
- ClarifyBench (POMDP/VOI): https://arxiv.org/html/2511.08798v1
