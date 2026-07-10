# Metacognition / Judgment Benchmark Matrix — Local Agentic Models

**Date:** 2026-06-19
**Scope:** Locally-runnable open models on a 64 GB Apple-Silicon Mac, scored ONLY on
metacognition/judgment axes — smart assumptions, ask-vs-answer, abstention,
calibration/hallucination, strict instruction-following. **Speed and math are deliberately ignored.**

> **Bottom line up front:** The judgment axes the user cares about are *barely measured per-model*.
> AbstentionBench, InteractComp, ClarifyMT-Bench, and Vectara HHEM publish almost **no scores for any of
> these nine candidates**. The only judgment-adjacent numbers that exist per-candidate are IFEval (saturated),
> Multi-IF/IFBench (partial), and SimpleQA (one model). The strongest *evidence-backed* judgment signal is the
> AbstentionBench research finding itself — **reasoning fine-tuning degrades abstention ~24%** — which acts as a
> structural prior penalizing the thinking-default candidates. **Net: this is a "hands-on probe required" situation,
> not a "pick by leaderboard" one.**

---

## 0. The governing finding (apply to every row)

From **AbstentionBench** (Meta/FAIR, arXiv 2506.09038, Jun 2025; [paper](https://arxiv.org/abs/2506.09038)):

- **Reasoning fine-tuning degrades abstention by ~24% on average** vs the non-reasoning counterpart — *even on
  math/science domains the reasoning model was trained on*. Reasoning models "respond over-confidently and
  rarely abstain."
- Model **scale has almost no effect** on abstention. Bigger ≠ better judgment here.
- Best open model in their eval was **Qwen 2.5 32B Instruct** (a *non-reasoning* instruct model); GPT-4o best closed.
- Concretely degraded: **s1.1 32B** and **DeepSeek-R1-Distill-Llama-70B** (both reasoning distills).

**Direct consequence for this shortlist:** any candidate that **defaults to thinking mode** carries an
*abstention/calibration penalty prior*. Where a non-thinking instruct sibling exists, **prefer it for judgment axes.**

---

## 1. Thinking-mode classification (the load-bearing column)

| # | Model | HF tag (current) | Thinking default? | Non-think sibling for judgment? |
|---|-------|------------------|-------------------|--------------------------------|
| 1 | Qwen3-Coder-Next 80B-A3B | **⚠ name mismatch** — no "Coder-Next". Closest: `Qwen/Qwen3-Next-80B-A3B-Instruct` (non-think) or `Qwen/Qwen3-Next-80B-A3B-Thinking` | Instruct=NO / Thinking=YES | **Instruct IS the non-think variant** — use it |
| 2 | Qwen3-Coder-30B-A3B | `Qwen/Qwen3-Coder-30B-A3B-Instruct` | NO (instruct) | itself |
| 3 | Qwen3.6-35B-A3B | `Qwen/Qwen3.6-35B-A3B` | **YES** (`enable_thinking:false` to disable) | same weights, non-think mode |
| 4 | Qwen3.6-27B (dense) | `Qwen/Qwen3.6-27B` | **YES** (`enable_thinking:false` to disable) | same weights, non-think mode |
| 5 | Devstral-Small-2 24B | `mistralai/Devstral-Small-2-24B-Instruct-2512` | **NO** — plain instruct | itself (no think mode at all) |
| 6 | GLM-4.7-Flash (30B-A3B MoE) | `zai-org/GLM-4.7-Flash` | Optional ("Preserved Thinking" off by default) | default non-think mode |
| 7 | GLM-4.5-Air (106B-A12B) | `zai-org/GLM-4.5-Air` | Hybrid (think + non-think modes) | non-think mode |
| 8 | Gemma 4 (26B-A4B / 31B) | `google/gemma-4-26b-a4b` , `google/gemma-4-31b` | NO (instruct-style) | itself |
| 9 | OLMo 3-Think 32B | `allenai/Olmo-3.1-32B-Think` | **YES — reasoning model by design** | **`allenai/Olmo-3.1-32B-Instruct` exists → prefer for abstention** |

> **⚠ Model-existence flags**
> - **"Qwen3-Coder-Next 80B-A3B" does not exist as named.** There is `Qwen3-Next-80B-A3B` (Instruct/Thinking,
>   general-purpose, *no Coder sub-brand*) and a separate `Qwen3-Coder-30B-A3B`. Matrix below uses
>   **Qwen3-Next-80B-A3B-Instruct** as the intended model.
> - **"Gemma 4 27B" does not exist.** Gemma 4 ships E2B / E4B / **26B-A4B (MoE)** / **31B (dense)**. The "27B" is
>   likely a carry-over from Gemma 3 27B. Matrix uses 26B-A4B + 31B.
> - **OLMo 3-Think is explicitly a reasoning model** → the AbstentionBench penalty applies most strongly here;
>   the non-think `Olmo-3.1-32B-Instruct` sibling is the judgment-preferred build.

---

## 2. The score matrix

Legend: **number** = real reported value; **no data** = not published; confidence
[solid] multi-source / official card · [single-source] one source · [hearsay] indirect/derived.

### 2a. Abstention & ask-vs-assume

| Model | AbstentionBench | InteractComp | ClarifyMT-Bench | Conf |
|-------|-----------------|--------------|-----------------|------|
| Qwen3-Next-80B-A3B-Instruct | no data | no data | no data | — |
| Qwen3-Coder-30B-A3B | no data | no data | no data | — |
| Qwen3.6-35B-A3B | no data | no data | no data | — |
| Qwen3.6-27B | no data | no data | no data | — |
| Devstral-Small-2 24B | no data | no data | no data | — |
| GLM-4.7-Flash | no data | no data | no data | — |
| GLM-4.5-Air | no data | no data | no data | — |
| Gemma 4 26B-A4B / 31B | no data | no data | no data | — |
| OLMo 3-Think 32B | no data (but reasoning ⇒ penalty prior) | no data | no data | — |
| **LEADER (calibration)** | **Qwen2.5-32B-Instruct** (best open) / GPT-4o (best closed) | **forced-ask doubles acc; GPT-5 only 13.7% self-decide** | under-clarification bias universal | [solid] |

**Reading:** *None* of the nine candidates has a published AbstentionBench / InteractComp / ClarifyMT-Bench score.
These three benchmarks evaluate "10–20 representative models" and the candidate set is too new / too niche to appear.
The leader column exists only as the benchmark's own reference points. **This entire judgment cluster is UNMEASURED
for the shortlist → hands-on probe is mandatory.**

### 2b. Strict instruction-following (NOT saturated IFEval)

| Model | IFEval (sat.) | Multi-IF | IFBench (strict) | Conf |
|-------|---------------|----------|------------------|------|
| Qwen3-Next-80B-A3B-Instruct | **87.6** | **75.8** | no data | [solid] (HF card) |
| Qwen3-Coder-30B-A3B | no data | no data | no data | — |
| Qwen3.6-35B-A3B | no data (card omits) | no data | no data | — |
| Qwen3.6-27B | no data (card omits) | no data | no data | — |
| Devstral-Small-2 24B | no data (coding-only card) | no data | no data | — |
| GLM-4.7-Flash | no data (card omits IFEval) | no data | no data | — |
| GLM-4.5-Air | **86.3** | no data | no data | [solid] (GLM-4.5 paper Table 6) |
| Gemma 4 31B | no data | no data | **~76** | [single-source] |
| Gemma 4 26B-A4B | no data | no data | no data | — |
| OLMo 3-Think 32B | **89.0** | no data | **47.6** | [solid] (Ai2 blog) |
| OLMo 3.1-32B-**Instruct** | **88.8** | no data | **39.7** | [solid] (HF card) |
| **LEADER (strict IF)** | Kimi-K2.5 94.0 / Qwen3.5 92.6 | Qwen3-235B-Thinking 80.6 | Nemotron-3-Ultra 81.7 / Hermes-3-70B 81.2 / Qwen3.7-Max 79.1 | [solid] |

**Reading:**
- IFEval is **saturated** (top open ≈ 89–92; candidates cluster 86–89) — *low discriminating power*, as the user warned.
- **IFBench** (the strict one that matters): the public leaderboard (llm-stats, 26 models, Jun 2026) **contains none
  of the candidates** except indirect Qwen3.5/3.6-Plus family — *not* the exact shortlist models.
- The only IFBench numbers for actual candidates come from model docs: **OLMo 3-Think 47.6**, **OLMo 3.1-Instruct 39.7**,
  **Gemma 4 31B ~76** (single-source — treat with caution; if accurate it would make Gemma 4 31B the *strongest
  candidate on strict IF by a wide margin*).
- ⚠ **Counter-intuitive:** OLMo's *Think* (47.6) beats its *Instruct* (39.7) on IFBench — strict-IF benefits from
  the RL reasoning run. This does **NOT** contradict the abstention finding: IFBench measures *constraint compliance*,
  while AbstentionBench measures *knowing when to refuse*. **Reasoning can help strict-IF while hurting abstention** —
  these are different judgment sub-skills. Keep them separate.

### 2c. Calibration & hallucination

| Model | AA-Omniscience Index | SimpleQA(-Verified) | Vectara HHEM | Conf |
|-------|----------------------|---------------------|--------------|------|
| Qwen3-Next-80B-A3B-Instruct | no data | no data (card omits) | no data | — |
| Qwen3-Coder-30B-A3B | no data | no data | no data | — |
| Qwen3.6-35B-A3B | no data | no data | no data | — |
| Qwen3.6-27B | no data | no data | no data | — |
| Devstral-Small-2 24B | no data | no data | no data | — |
| GLM-4.7-Flash | no data | no data | no data | — |
| GLM-4.5-Air | no data | **14.5** | no data | [solid] (GLM-4.5 paper) |
| GLM-4.5 (full, ref) | no data | 26.4 | no data | [solid] |
| Gemma 4 26B-A4B / 31B | no data | no data | no data | — |
| OLMo 3-Think 32B | no data | no data | no data | — |
| **LEADER** | **Claude Fable 5 = 40**, Gemini 3.1 Pro = 33, Claude Opus 4.8 | Qwen3-235B family ~50.6 (top open) | **finix_s1_32b (Ant) 1.8%**; Gemini-2.0-Flash 0.7% (older set) | [solid] |

**Reading:**
- **AA-Omniscience** (Artificial Analysis, 6000 Q, rewards correct / penalizes hallucination / **no penalty for
  abstaining** — i.e. a *direct* calibration-vs-guessing benchmark): top is closed (Claude Fable 5 = 40). The public
  writeups surface **no per-candidate open-model index** — the interactive leaderboard has more but wasn't machine-
  extractable here. **This is the single most relevant calibration benchmark and the candidates are effectively
  unscored in public summaries → probe target.**
- **SimpleQA**: only **GLM-4.5-Air (14.5)** among candidates has a number. Low absolute (these are hard factoid Qs);
  the *calibration* read (abstention rate vs error) is not broken out per-candidate.
- **Vectara HHEM** (grounded-summary hallucination): current top = **finix_s1_32b 1.8%** (Ant Group; obscure).
  **None of the nine candidates appear on the public HHEM board.**

---

## 3. Per-candidate judgment verdict

| Model | Reasoning? | Judgment data we have | Judgment-axis read |
|-------|-----------|------------------------|---------------------|
| **Qwen3-Next-80B-A3B-Instruct** | **No (instruct-only, no `<think>`)** | IFEval 87.6, Multi-IF 75.8 | **Best-positioned on the prior:** explicitly non-thinking ⇒ no abstention penalty, *and* strong Multi-IF (75.8, multi-turn IF). The structurally-safest pick despite missing abstention data. |
| Qwen3-Coder-30B-A3B | No (coder instruct) | none judgment-specific | Coder-tuned ⇒ likely over-eager to *act* (coders rarely abstain). Unmeasured; suspect weak ask-vs-assume. |
| Qwen3.6-35B-A3B | **Yes (default)** | none (card omits IF) | Thinking-default ⇒ abstention-penalty prior. Run with `enable_thinking:false` for judgment work. Unmeasured. |
| Qwen3.6-27B (dense) | **Yes (default)** | none (card omits IF) | Same as 35B. Dense ⇒ slightly steadier IF anecdotally, but no data. Disable thinking for judgment. |
| Devstral-Small-2 24B | No (plain instruct) | coding-only (SWE 68.0) | Narrow SWE agent. *Zero* general-IF/abstention data. High act-bias risk (agentic-coder design). Unmeasured + suspect. |
| GLM-4.7-Flash | Optional think (off default) | none (card omits IFEval) | Agentic/coding-tuned (τ²-Bench 79.5). No IF/calibration data at all. Unmeasured. |
| GLM-4.5-Air | Hybrid | IFEval 86.3, SimpleQA 14.5 | Only candidate with *both* an IF and a factoid-calibration number. SimpleQA 14.5 is low (small factual store) → run RAG, don't trust closed-book. Decent IF. |
| Gemma 4 31B (dense) | No | **IFBench ~76** (single-source) | **If the ~76 IFBench holds, this is the strongest candidate on strict-IF by far** (candidate field is 40s–70s). Non-thinking, Google-tuned for instruction-following. **High-priority probe.** |
| Gemma 4 26B-A4B (MoE) | No | none (rank withheld) | Docs say "best for instruction-following/content, not complex reasoning" — *fits the judgment use-case profile* but unranked. Probe. |
| **OLMo 3-Think 32B** | **Yes — reasoning model by design** | IFEval 89.0, **IFBench 47.6** | Strong strict-IF (best constraint-compliance among candidates with data), **but the reasoning design triggers the AbstentionBench ~24% penalty prior** → expect *worse* abstention/ask-vs-assume. **Prefer `Olmo-3.1-32B-Instruct` (IFBench 39.7) if abstention matters more than constraint-following.** |

---

## 4. Strongest candidate on judgment — FROM DATA

**Caveat: "from data" is thin.** Ranking only by what's *published*:

1. **Qwen3-Next-80B-A3B-Instruct** — *best-positioned overall.* It is the one candidate that is **(a) explicitly
   non-thinking** (so it escapes the AbstentionBench reasoning penalty by construction) **and (b) has the strongest
   *multi-turn* IF number (Multi-IF 75.8)** plus solid IFEval 87.6. Multi-turn IF is the closest public proxy to
   "follows the user reliably over an agentic session." Fits 64 GB at 4-bit (~45 GB).
2. **Gemma 4 31B** — *highest strict-IF if the single-source IFBench ~76 is real*, non-thinking, Google IF-tuning.
   Demote to "promising but single-sourced" until confirmed.
3. **GLM-4.5-Air** — *only candidate with a calibration datapoint* (SimpleQA 14.5) plus IFEval 86.3. The 14.5 warns:
   weak closed-book factual store → pair with retrieval. 106B-A12B at 4-bit is ~55–60 GB — **tight on 64 GB**.
4. **OLMo 3.1-32B-Instruct** (NOT -Think) — strong IFEval/IFBench, non-thinking, *fully open*. Pick the **Instruct**
   build over **Think** for abstention-sensitive work despite Think's higher IFBench.

**Avoid for judgment work (act-bias risk, zero data):** Devstral-Small-2 24B, Qwen3-Coder-30B-A3B, GLM-4.7-Flash —
all coder/agent-tuned with no IF/abstention/calibration numbers; coder tuning correlates with *acting instead of asking*.

**Thinking-default penalty applies to:** Qwen3.6-35B-A3B, Qwen3.6-27B, OLMo 3-Think 32B. Run the Qwen3.6 pair with
`enable_thinking:false` and substitute OLMo's Instruct sibling when abstention/ask-vs-assume is the priority.

---

## 5. What is UNMEASURED → hands-on probe needed

**Effectively everything the user actually cares about is unmeasured per-candidate.** No public source scores ANY of
the nine on AbstentionBench, InteractComp, ClarifyMT-Bench, or Vectara HHEM, and only one (GLM-4.5-Air) on SimpleQA.
A local probe harness is the only way to rank them on judgment. Suggested probe set, in priority order:

1. **Ask-vs-assume (InteractComp-style):** feed 15–20 deliberately under-specified agentic tasks; score
   *clarify-rate* and *correctness-when-clarified*. Directly tests the user's #1 concern.
2. **Abstention (AbstentionBench-style):** mix answerable + unanswerable/false-premise prompts; score
   correct-abstention vs over-confident-answer. **Run thinking-default models in BOTH modes** to measure the penalty live.
3. **Closed-book calibration (SimpleQA / AA-Omniscience-style):** hard factoids; score
   abstention-rate vs error-rate (reward "I don't know" over a wrong guess).
4. **Strict multi-turn IF (IFBench / Multi-IF-style):** stacked constraints across turns; the one axis where some
   public data exists (Qwen3-Next 75.8 Multi-IF, OLMo 47.6 IFBench, Gemma 4 31B ~76) — confirm locally.

**Priority probe targets** (best data-backed position, but key axes still blank): **Qwen3-Next-80B-A3B-Instruct**,
**Gemma 4 31B**, **GLM-4.5-Air**, **OLMo 3.1-32B-Instruct**.

---

## Sources

- AbstentionBench — https://arxiv.org/abs/2506.09038 · https://arxiv.org/html/2506.09038v1 · https://github.com/facebookresearch/AbstentionBench
- InteractComp — https://arxiv.org/html/2510.24668 · https://huggingface.co/papers/2510.24668
- ClarifyMT-Bench — https://arxiv.org/abs/2512.21120
- IFBench leaderboard — https://llm-stats.com/benchmarks/ifbench · https://artificialanalysis.ai/evaluations/ifbench
- Multi-IF leaderboard — https://llm-stats.com/benchmarks/multi-if
- AA-Omniscience — https://artificialanalysis.ai/evaluations/omniscience · https://artificialanalysis.ai/articles/aa-omniscience-knowledge-hallucination-benchmark
- SimpleQA Verified — https://epoch.ai/benchmarks/simple-qa-verified
- Vectara HHEM — https://www.vectara.com/blog/introducing-the-next-generation-of-vectaras-hallucination-leaderboard · https://awesomeagents.ai/leaderboards/hallucination-benchmarks-leaderboard/
- Qwen3-Next-80B-A3B-Instruct — https://huggingface.co/Qwen/Qwen3-Next-80B-A3B-Instruct
- Qwen3.6-27B — https://huggingface.co/Qwen/Qwen3.6-27B · Qwen3.6-35B-A3B — https://huggingface.co/Qwen/Qwen3.6-35B-A3B
- Devstral-Small-2 — https://huggingface.co/mistralai/Devstral-Small-2-24B-Instruct-2512
- GLM-4.7-Flash — https://huggingface.co/zai-org/GLM-4.7-Flash
- GLM-4.5 paper (Air SimpleQA/IFEval Table 6) — https://arxiv.org/pdf/2508.06471
- Gemma 4 — https://artificialanalysis.ai/articles/gemma-4-everything-you-need-to-know · https://codersera.com/blog/gemma-4-complete-guide-2026/
- OLMo 3 — https://allenai.org/blog/olmo3 · https://huggingface.co/allenai/Olmo-3.1-32B-Instruct · https://huggingface.co/allenai/Olmo-3.1-32B-Think
