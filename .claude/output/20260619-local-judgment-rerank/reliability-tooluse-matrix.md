# Model × Benchmark Matrix — Reliability & Tool/Agent-Decision (Local Agentic-Coding)

**Research date:** 2026-06-19
**Scope:** 9 locally-runnable (64 GB Apple-Silicon) open models, scored ONLY on reliability + tool/agent-decision benchmarks. Speed/math deliberately excluded.
**Method:** four parallel research agents, LIVE web sources. Per-cell confidence flags. **"no data" = no published score found; never fabricated or inferred.**

Source files (this directory):
`_model-existence.md` · `_tau-bench.md` · `_bfcl.md` · `_mcpmark-termbench-arena.md`

---

## ⚠️ Read first — three honesty caveats that shape everything below

1. **The data is mostly absent.** Across 9 models × 6 benchmark families, the matrix is dominated by **"no data."** This is the central finding, not a failure of search: these reliability/tool-decision benchmarks are reported by *very few* open-model cards. Most vendors publish SWE-bench / coding / reasoning, not τ-bench / BFCL-irrelevance / MCPMark.

2. **The benchmark families fractured in 2026.** τ-bench (v1) → τ²-bench → τ³/TAU3-Bench; BFCL v2 → v3 → v4 (different scales, NOT cross-comparable); Terminal-Bench 1.0 → 2.0 → 2.1. A 2026 model reporting "TAU3-Bench 67.2" has **not** reported the τ²-retail/airline cell the user asked for — that is a genuine no-data for the requested metric.

3. **Model-existence uncertainty (UNRESOLVED, flagged).** The existence agent reported all 9 names resolve to "real HF repos," but explicitly caveated that #3/#4/#6/#8 (Qwen3.6-35B-A3B, Qwen3.6-27B, GLM-4.7-Flash, Gemma 4) **postdate its cutoff** and the confirmation rests on search-index hits a summarizer *could* have hallucinated. Independently, the **BFCL agent found NO "Qwen3.6" on any BFCL board — only Qwen3.5 analogs.** These two findings conflict. I am NOT asserting these four models are confirmed-real; treat their existence as **[single-source], to be verified by a direct HF card fetch before you rely on it.** The τ-bench and MCPMark/TB agents *did* surface what they read as official cards for Qwen3.6-35B-A3B and Gemma 4 — so the weight of evidence leans "real but tag/version possibly off" — but this is not nailed down.

---

## Canonical HF tags (corrected from the candidate-list spelling)

| # | Candidate (as given) | Corrected HF tag | Exists? |
|---|---|---|---|
| 1 | Qwen3-Coder-Next 80B-A3B | `Qwen/Qwen3-Coder-Next` (no size suffix in tag) | yes [solid] |
| 2 | Qwen3-Coder-30B-A3B | `Qwen/Qwen3-Coder-30B-A3B-Instruct` | yes [solid] |
| 3 | Qwen3.6-35B-A3B | `Qwen/Qwen3.6-35B-A3B` | **[single-source] — postdates cutoff, BFCL board shows only Qwen3.5** |
| 4 | Qwen3.6-27B (dense) | `Qwen/Qwen3.6-27B` | **[single-source] — same caveat** |
| 5 | Devstral-Small-2 24B | `mistralai/Devstral-Small-2-24B-Instruct-2512` | yes [solid] |
| 6 | GLM-4.7-Flash (30B MoE) | `zai-org/GLM-4.7-Flash` (30B-A3B) | **[single-source] — postdates cutoff** |
| 7 | GLM-4.5-Air (106B-A12B) | `zai-org/GLM-4.5-Air` | yes [solid] — best-established (Jul 28 2025, MIT) |
| 8 | Gemma 4 (26B-A4B / 31B) | `google/gemma-4-26B-A4B`, `google/gemma-4-31B` | **[single-source] — postdates cutoff** |
| 9 | OLMo 3-Think 32B | `allenai/Olmo-3.1-32B-Think` (3.1, not 3) | yes [solid] — name slightly off |

---

## THE MATRIX

Columns are the requested reliability / tool-decision benchmarks. Cells are the score for the **exact requested model** (sibling/analog scores are footnoted, not placed in-cell). Version tags matter — do not cross-compare across versions.

| Model | τ-bench retail | τ-bench airline | τ²-bench retail | τ²-bench airline | BFCL overall | BFCL irrelevance | MCPMark | Terminal-Bench | Agent Arena | pass^k |
|---|---|---|---|---|---|---|---|---|---|---|
| **Qwen3-Coder-Next 80B-A3B** | no data | no data | no data | no data | no data | no data | no data | no data | no data | no data |
| **Qwen3-Coder-30B-A3B-Instruct** | no data | no data | 25.4 ᴬ | 42.0 ᴬ | 0.7663 (v2) ᴮ | no data | no data | no data | no data | no data |
| **Qwen3.6-35B-A3B** | no data | no data | no data | no data | no data ᶜ | no data | 37.0% ᴰ | 0.515 (TB 2.0, #32) | no data | no data |
| **Qwen3.6-27B (dense)** | no data | no data | no data | no data | no data ᶜ | no data | no data | **0.593 (TB 2.0, #20)** | no data | no data |
| **Devstral-Small-2 24B** | no data | no data | no data | no data | no data | no data | no data | 0.225 (TB 2.0, card) ᴱ | no data | no data |
| **GLM-4.7-Flash (30B-A3B)** | no data | no data | no data | 79.5 (τ² aggregate, no split) ᶠ | no data | no data | no data | no data ᴳ | no data | no data |
| **GLM-4.5-Air (106B-A12B)** | 77.9 (v1) | **0.608 (v1, #3 overall)** | no data | no data | **0.764 (v3)** | no data | no data | no data | no data | no data |
| **Gemma 4 (31B / 26B-A4B)** | no data | no data | no data | no data | no data | no data | 18.1% (31B) ᴰ | 0.429 (31B, TB 2.0) ᴰ | **#27 (31B)** | no data |
| **OLMo 3-Think 32B** | no data | no data | no data | no data | no data | no data | no data | no data | no data | no data |

### Cell confidence & footnotes

- ᴬ Qwen3-Coder-30B τ²-retail/airline = **25.4 / 42.0** — from a **third-party arXiv paper (2511.01824)**, NOT Qwen's own card. **[single-source].** These are *weak* scores (frontier ≈ 60–77 retail).
- ᴮ Qwen3-Coder-30B BFCL **0.7663 is v2** (via Mify-Coder arXiv 2512.23747). **[single-source].** Not comparable to v3/v4 numbers.
- ᶜ Qwen3.6-35B/27B BFCL: **name not on any BFCL board.** Closest *published* are the **Qwen3.5** analogs: Qwen3.5-35B-A3B = 0.673 (v4), Qwen3.5-27B = 0.685 (v4). These are **different models** — not placed in-cell.
- ᴰ Qwen3.6-35B MCPMark 37.0% and Gemma 4 31B MCPMark 18.1% / TB 42.9% come from **one secondary blog** (labellerr), not the official mcpmark.ai board (which lists none of the candidates). **[single-source/hearsay].**
- ᴱ Devstral-Small-2 24B Terminal-Bench **22.5% is on the Mistral card** (TB 2). **[solid]** but a *coding-execution* proxy, not a tool-decision metric.
- ᶠ GLM-4.7-Flash τ²-Bench **79.5 is a single aggregate** (Unsloth/Z.ai table) with **NO retail/airline/telecom split** — placed in the airline column only to surface it, with caveat. Do not read as airline-specific. A separate AA telecom-only number ("98.8%") exists but is telecom-domain, not overall.
- ᴳ GLM-4.7-Flash has no *Flash-specific* TB cell; the **parent GLM-4.7 = 41% on TB 2.0** (sibling, not in-cell).
- **τ-bench LEADER values use mixed scales** — GLM-4.5-Air airline 0.608 is on the 0–1 scale; retail 77.9 is the percentage mirror. Same benchmark, different source's reporting convention.

---

## Per-benchmark LEADER (calibration) + candidate ranking

### τ-bench / τ²-bench
- **LEADERS (closed/frontier):** τ-bench airline → **Claude Sonnet 4.5 = 0.700**; τ²-bench airline → **LongCat-Flash-Thinking-2601 = 0.765**; τ²-telecom → JT-35B-Flash / GLM-5.2 tie = 99.1%.
- **Best LOCAL on τ-bench airline:** **GLM-4.5-Air = 0.608** (#3 overall, behind only Sonnet 4.5 and MiniMax M1). This is the single strongest reliability signal in the whole set.
- **Candidate ranking (data only):** 1) GLM-4.5-Air (airline 0.608 / retail 77.9, v1) → 2) GLM-4.7-Flash (τ² aggregate 79.5, no split — not directly comparable) → 3) Qwen3-Coder-30B (τ² retail 25.4 / airline 42.0, weak, single-source). Everyone else: no data.
- **pass^k: no data for ANY of the 9.** pass^k exists only for frontier models in the Sierra τ²-bench paper.

### BFCL (overall + irrelevance)
- **LEADERS:** BFCL-v4 overall → **Qwen3.7 Max = 0.750**; BFCL-v3 overall → **GLM-4.5 = 0.778**. **No clean modern irrelevance-detection leader exists** — the live v4 board has no irrelevance column; the only modern per-model irrelevance datapoint is **Qwen3-Coder-Plus = 0.8458 (v3, EvalScope)**, a sibling of candidate #2.
- **Candidate ranking (data only):** 1) GLM-4.5-Air = 0.764 (v3) **[solid]** → 2) Qwen3-Coder-30B = 0.7663 (v2) **[single-source, different scale]**. Everyone else: no data on overall; **no candidate has a published irrelevance sub-score** (the metric the user most cares about — "knowing when NOT to call a tool"). The closest proxy is the Qwen3-Coder-Plus 0.8458 sibling.

### MCPMark / Terminal-Bench / Agent Arena
- **LEADERS:** MCPMark → **gpt-5-2-high = 57.5% Pass@1** (top open absent from board); Terminal-Bench 2.0 → **GPT-5.5 = 82.7%** (top open = GLM-5.1 = 69.0%); Agent Arena → **Claude Fable 5 = #1** (top open = Gemma 4 31B at #27).
- **Candidate ranking, Terminal-Bench 2.0 (the only well-populated column):** 1) **Qwen3.6-27B = 0.593 (#20)** [solid] → 2) **Qwen3.6-35B-A3B = 0.515 (#32)** [solid] → 3) Gemma 4 31B = 0.429 [single-source] → 4) Devstral-Small-2 = 0.225 [solid, card]. (All TB 2.0; none appear on the TB 2.1 split.)
- **MCPMark:** official board has **none** of the candidates; only secondary-blog numbers exist (Qwen3.6-35B 37.0%, Gemma 4 31B 18.1%) — **[single-source/hearsay].**
- **Agent Arena:** only **Gemma 4 31B (#27)** appears. ("Qwen 3.6 Plus" at #21 is a *different, larger* variant — not a candidate.)

---

## Bottom line

### Strongest on reliability + tool-decision FROM DATA
**GLM-4.5-Air (106B-A12B)** is the clear evidence-backed leader for this use case, and it's also the most solidly-confirmed-real model in the set:
- Best local model on **τ-bench airline (0.608, #3 overall)** — the closest thing to a published *reliability* number any candidate has.
- Strong **BFCL overall (0.764, v3)** — second-best is a v2 number on a different scale.
- MIT-licensed, established since Jul 2025.
- **Caveat:** at 106B-A12B it's the heaviest candidate; runnable on 64 GB only at aggressive quant (≈3-4 bit). Its tool-*decision* (irrelevance) sub-score is still **no data** — its lead is on overall + retail/airline reliability, not specifically on "when to skip a tool."

**Runner-up on the tool-decision axis specifically:** the **Qwen3-Coder** line is the only family with *any* irrelevance-flavored signal (sibling Qwen3-Coder-Plus = 0.8458 irrelevance v3), and Qwen3-Coder-30B is the only candidate with a real (if weak, single-source) τ²-bench retail/airline split. But these are sibling/third-party numbers, not the exact candidate on a primary card.

**For agentic terminal execution (proxy):** Qwen3.6-27B (TB 2.0 0.593) leads the candidates — *if* the model is confirmed real (see caveat 3).

### Essentially UNMEASURED → need a hands-on probe
These have **near-zero or zero** published reliability/tool-decision data and cannot be ranked from the literature — a hands-on local probe (τ²-bench-style multi-turn tool tasks with irrelevant-tool traps + long-horizon coherence) is the only way to judge them:

1. **Qwen3-Coder-Next 80B-A3B** — real model, *zero* presence on all 6 benchmark families. Completely unmeasured on judgment.
2. **OLMo 3-Think 32B** — reasoning/math benchmarks only; no τ / BFCL / MCPMark / TB / Arena. Fully unmeasured on tool-decision.
3. **Devstral-Small-2 24B** — only an execution proxy (TB 22.5%, SWE-bench 68%); **no** tool-*decision* / irrelevance / multi-turn-reliability data.
4. **Gemma 4 26B-A4B** — the MoE variant has essentially nothing (the 31B dense has the few scattered single-source numbers); also existence-uncertain.
5. **GLM-4.7-Flash** — one un-split τ² aggregate (79.5) and existence-uncertain; no irrelevance, no MCPMark, no Flash-specific TB.
6. **Qwen3.6-35B-A3B / Qwen3.6-27B** — existence itself is [single-source] (BFCL board shows only Qwen3.5); the only solid numbers are TB 2.0 — and **nothing** on the tool-decision (irrelevance / τ²-reliability) axis the user cares most about.

**Net:** Data can rank GLM-4.5-Air first and tell you Qwen3-Coder / Qwen3.6 have *some* signal, but **the specific axis the user prioritizes — knowing when NOT to call a tool (BFCL irrelevance) + pass^k reliability — is "no data" for literally all 9 candidates.** That axis is unmeasured across the board and is the single best target for a hands-on probe.
