# Local text-LLM tier survey, September 2026

Scope: candidates for the `local-models` suite (Apple Silicon M5 Pro, 64 GB, ~307 GB/s
bandwidth, Ollama 0.33.0 host, MLX format-routed for safetensors). This machine is
bandwidth-bound, so a MoE model with a low active-param count beats a dense model of
equal quality. Resident budget target: about 40 GB per big model.

Incumbents being benchmarked against:
- **small/warm**: `gemma4:e4b` (about 6 GB, always resident)
- **big/reasoning**: `gemma4:26b`, MoE with about 3.8B active params (17 GB)
- **code/tool-calling**: `qwen3.6:35b-a3b`, MoE with about 3B active params (23 GB),
  cleared 9/9 on the suite's judgment probe

All sizes below are approximate q4/q8 on-disk figures reported by Ollama's library
pages or vendor docs at search time (2026-09-11). Verify the actual pull size before
committing disk or bandwidth budget. Library pages showed internally inconsistent
numbers for the same model across different write-ups this session, so treat every
figure as unconfirmed until `ollama pull` + `ollama show` say otherwise.

---

## 1. Close-to-frontier reasoning

The best single local model this machine can plausibly run.

| Candidate | Params (active) | Disk (q4/q8) | Ollama/MLX | Case | Failure mode |
|---|---|---|---|---|---|
| **GLM-4.7-Flash** (Zhipu, local sibling of the Jan 2026 flagship) | 30B total, 3B active MoE | 19 GB q4_K_M, 32 GB q8_0, 60 GB bf16 | `ollama pull glm-4.7-flash` (needs Ollama 0.14.3+; this host runs 0.33.0, should clear it) | Reported SWE-bench Verified 59.2 (about 3x Qwen3-30B-A3B) and τ²-Bench 79.5 vs Qwen3's 49.0. AIME25 91.6, GPQA 75.2. If these numbers hold under the suite's own probe, this beats gemma4:26b's reasoning tier at roughly the same footprint. Needs the mechanical gate before any of it is trusted. | New enough that tag stability on this host's 0.33.0 is unconfirmed. One write-up flagged a pre-release Ollama requirement. Pull and `ollama show` before relying on it. |
| **Qwen3.8:27b** (dense, mid-Aug 2026) | 27B dense | 18 GB q4_K_M | `ollama pull qwen3.8:27b` | Dense, not MoE, so it works against the bandwidth-bound preference. Qwen states "substantial gains across coding, professional work, research, and long-horizon agentic tasks" over Qwen3.6. Worth a bake-off against GLM-4.7-Flash at near-identical disk size, since dense models sometimes hold more consistent judgment per token. | Dense at 27B will be visibly slower tok/sec than either incumbent MoE at this bandwidth. Only worth it if the quality delta is large. |
| **Mistral Small 4** (Mar 2026) | 119B total, about 6B active MoE | Not confirmed at q4; likely 60-70 GB even quantized | MLX/Ollama availability unconfirmed | Unifies instruct, reasoning (ex-Magistral), coding (ex-Devstral), and multimodal into one model. Attractive breadth. | Exceeds the 40 GB resident budget even at q4 (119B params is around 60+ GB q4). Excluded unless the budget relaxes or a much lower quant turns up. Listed for completeness only. |
| **Qwen3.8-Flash-Next** (Qwen4 architecture preview) | 125B total, 6B active MoE | 105 GB MLX, 120 GB Q4_K_M GGUF | `ollama pull qwen3.8-flash-next` | Genuinely frontier-adjacent locally, the first open Qwen4-architecture weight, but far outside budget. Even q4 is 3x the target footprint. Excluded. | Not runnable within constraints. |

**Verdict:** GLM-4.7-Flash is the only candidate in this role that both plausibly beats
gemma4:26b and fits the budget at a similar footprint (19 GB vs 17 GB). Qwen3.8:27b is
a reasonable dense bake-off partner if GLM's benchmarks don't hold up under the local
probe.

---

## 2. Reliable grunt work (cheap, fast, high-throughput)

Classification, summarization, and extraction at volume. This role trades peak
reasoning for tokens/sec and a small footprint that can sit alongside a bigger model.

| Candidate | Params (active) | Disk | Ollama/MLX | Case | Failure mode |
|---|---|---|---|---|---|
| **Granite 4.0 H Tiny** (IBM, hybrid Mamba-2/transformer MoE) | 7B total, 1B active | About 3.5 GB q4 (6.7 GB q8 reported) | `ollama pull ibm/granite4.0-preview:tiny` or `granite4:tiny-h` | 1B active is the lowest active-param count of any candidate surveyed. Should be the fastest tok/sec on this bandwidth by a wide margin. IBM's hybrid architecture claims over 70% RAM reduction on long or batched inputs, useful for a high-volume extraction lane. Supports tool calling and structured output. | Still tagged "preview" at search time. Verify it isn't marked preview/unstable on this Ollama version. IBM's 4.1/4.2 successors moved to dense architectures (8B/30B, no MoE), which suggests IBM itself deprioritized the hybrid-MoE line. Check whether Tiny is still maintained before depending on it. |
| **gemma4:e4b** (incumbent, restated for contrast) | About 4B effective | About 6 GB | already resident | Baseline this role competes against. Already fast, already warm, zero migration cost. | N/A |
| **Qwen3.6:27b-coding / 27b** (dense) | 27B dense | 18 GB | `ollama pull qwen3.6:27b` | Too large for a "grunt work" lane at this machine's bandwidth. Dense 27B will not out-throughput a 1-4B-active MoE. Listed only to rule out. | Wrong shape for this role. Dense penalizes exactly the axis this role optimizes. |

**Verdict:** Granite 4.0 H Tiny stands out purely on the active-param axis: 1B active
is 3-8x lower than every other model surveyed. Worth a probe run specifically to check
whether the "preview" stability concern is founded, before it displaces gemma4-e4b as
the always-warm companion, or gets added as a third lane.

---

## 3. Sustained answers on limited context

Coherent multi-turn or longer generations without needing a huge context window. This
favors architectures that stay stable over long single-session generations, over raw
context-length numbers.

| Candidate | Params (active) | Disk | Ollama/MLX | Case | Failure mode |
|---|---|---|---|---|---|
| **gemma4:12b** (dense, unified variant added June 2026) | 12B dense | About 8 GB est. | `ollama pull gemma4:12b` | Sits between the warm e4b and the big 26B MoE. Dense at this size keeps bandwidth cost modest, and Gemma's family is already validated on this suite for prose quality. A natural mid-tier for sustained-generation tasks that don't need the 26B's full reasoning budget. | Size and quality aren't independently confirmed this session. Treat as a plausible slot, not a benchmarked pick, until probed. |
| **Qwen3.6:27b** (dense) | 27B dense | 18 GB | `ollama pull qwen3.6:27b` | Same family as the incumbent coding model but dense. Dense models are reported to hold consistency better over long generations than MoE routing, which can drift expert selection over a long single response. Worth testing specifically for degradation over long outputs. | Dense cost at this size cuts into the "keep footprint modest" goal of this role. Only wins if the consistency claim holds under test. |
| **Granite 4.0 H Tiny** (see role 2) | 7B, 1B active | 3.5 GB | as above | IBM markets the hybrid Mamba-2 design specifically for long-input RAM efficiency. If that extends to long-output coherence, unconfirmed, it's an extremely cheap slot for this role. | Long-context RAM efficiency and long-output coherence are different claims. Don't assume one implies the other without testing. |

**Verdict:** Weakest-evidenced role in this survey. No vendor is specifically marketing
a "long sustained generation on a small context window" model in 2026; every family
above is a plausible but unconfirmed fit. gemma4:12b is the safest bet given the
family's existing track record on this suite.

---

## 4. Judgement calls (LLM-as-judge / grading / verdict seat)

Needs strong instruction-following and calibration more than raw reasoning power.

| Candidate | Params (active) | Disk | Ollama/MLX | Case | Failure mode |
|---|---|---|---|---|---|
| **GLM-4.7-Flash** (see role 1) | 30B, 3B active | 19 GB | as above | High GPQA (75.2) and τ²-Bench (79.5, an agent/tool-use benchmark that stresses following exact instructions) suggest good calibration. If it clears the suite's judgment probe as well as qwen3.6:35b-a3b did (9/9), it's a strong dual-purpose reasoning-and-judge model, cutting the number of resident models needed. | Same new-tag caution as role 1. Also carries the standard self-preference-bias risk if it ever judges its own outputs, a generic LLM-judge caveat, not architecture-specific. |
| **Qwen3.8:27b** (dense) | 27B dense | 18 GB | as above | Dense models are the 2026 industry default for judge seats specifically because MoE routing can introduce inconsistency across similar-but-not-identical prompts, a real risk for a grader that needs to score near-duplicate outputs consistently. Worth testing head-to-head against GLM-4.7-Flash on the suite's calibration probe. | Slower than MoE at this size. The calibration benefit is a hypothesis to test, not a settled fact. |
| **Llama 3.3 70B** (still cited as the 2026 production default for self-hosted judges) | 70B dense | About 40 GB q4, right at the budget ceiling | widely available | Multiple 2026 sources cite this as "the standard self-hosted judge," with a small human-correlation gap to frontier judges: real-world calibration track record. | Fully consumes the resident budget (about 40 GB), leaving no headroom for the warm companion. Would require evicting everything else while loaded. Dense, so also the worst bandwidth fit of any candidate here. Include only as a stretch/occasional-use option, not a default judge. |
| **gemma4:26b** (incumbent, restated) | MoE, 3.8B active | 17 GB | already in suite | Already used for structural vision reads. Reusing it as the judge seat costs zero new disk or bandwidth budget if its judgment calibration is adequate: the cheapest possible answer to this role. | Whether its judgment calibration specifically (vs. general reasoning) has been probed is unknown. The incumbent's 9/9 judgment-probe result belongs to qwen3.6, not gemma4. |

**Verdict:** The cheapest real improvement path is probing gemma4:26b (already
resident, zero new cost) against the suite's judgment gate before pulling anything
new. If a dedicated judge model is wanted, GLM-4.7-Flash is the best-fitting new
candidate. Llama 3.3 70B has the strongest track record but is a budget-buster, not a
default.

---

## 5. Orchestration and tool-calling (agentic multi-step)

Reliable structured or function calling. The incumbent (`qwen3.6:35b-a3b`) already
cleared 9/9 on this suite's own probe, so the bar for replacement is high.

| Candidate | Params (active) | Disk | Ollama/MLX | Case | Failure mode |
|---|---|---|---|---|---|
| **qwen3.6:35b-a3b-coding** (coding-tuned sibling of the incumbent) | 35B, 3B active MoE | 23 GB | `ollama pull qwen3.6:35b-a3b-coding` | Same base architecture as the already-validated incumbent, with a coding-specific tune. Near-zero-risk swap-in to test whether the coding tune improves tool-calling without touching architecture or size. Cheapest possible experiment in this whole survey. | May be narrower than the general a3b tune if it over-indexes on code generation at the expense of general tool-orchestration prompts. Needs the same 9-probe re-run, not an assumption of improvement. |
| **GLM-4.7-Flash** (see role 1) | 30B, 3B active | 19 GB | as above | τ²-Bench (an explicit tool-use/agent benchmark) score of 79.5, vs a cited 49.0 for "Qwen3" (unclear whether that is the exact incumbent variant), is the single most directly relevant number in this whole survey for this role. Worth prioritizing the probe run. | Same new-tag caution as elsewhere. τ²-Bench numbers are self-reported by the vendor ecosystem, not independently reproduced here. |
| **MiniMax M2** (256 experts, agent-native post-training) | 229.9B total, 9.8B active MoE | Not confirmed; likely 130 GB+ even at q4 | Unconfirmed Ollama tag | Purpose-built as agent-native, explicitly iterated M2 to M2.5 to M2.7 for agentic use: a strong directional signal for this role specifically. | Far outside the 40 GB budget even accounting for the lower active-param fraction, because resident memory for MoE is dominated by total params, not active params, on this machine's architecture. Excluded. |
| **Kimi K2.6** (Moonshot, Agent Swarm) | 1T total, 32B active MoE | About 630 GB int4 | Unconfirmed | Frontier agentic capability (100+ sub-agent orchestration) is interesting for what "orchestration" means at scale, but the total footprint is two orders of magnitude past this machine's budget. | Not runnable locally on this hardware under any quantization. Excluded, listed only because it defines the upper edge of what "orchestration-focused" 2026 releases look like. |

**Verdict:** The incumbent's own coding-tuned sibling (`qwen3.6:35b-a3b-coding`) is the
lowest-risk experiment: same architecture, same size, narrower tune. GLM-4.7-Flash is
the most interesting new candidate given its explicit agent-benchmark score. The two
largest agent-native releases of the year (MiniMax M2, Kimi K2.6) are both far outside
this machine's memory budget and are excluded rather than stretched for.

---

## Ranked shortlist: worth pulling and probe-testing, newest-promise first

1. **GLM-4.7-Flash** (30B-A3B MoE, 19 GB q4). Roles 1, 4, 5. Newest and broadest
   evidence (SWE-bench, τ²-Bench, GPQA), same footprint class as gemma4:26b. Single
   highest-value pull: if it clears the judgment probe, it's a credible drop-in
   upgrade for the reasoning tier and a judge/orchestration option at once.
2. **Granite 4.0 H Tiny** (7B total, 1B active MoE, about 3.5 GB q4). Role 2, plus a
   role-3 long-output test. Lowest active-param count surveyed; cheap enough to probe
   alongside anything else with no real disk or bandwidth cost. Watch for
   preview-stability risk, since IBM's own 4.1/4.2 line moved away from MoE.
3. **qwen3.6:35b-a3b-coding**. Role 5. Zero-architecture-risk variant of the
   already-trusted incumbent, the cheapest possible "did the coding tune help
   tool-calling" experiment.
4. **Qwen3.8:27b** (dense, 18 GB q4). Roles 1, 3, 4. Dense bake-off partner against
   GLM-4.7-Flash and the incumbent MoE models, specifically to test whether dense
   consistency beats MoE for judgment or sustained generation despite the bandwidth
   penalty.
5. **gemma4:26b re-probe against the judgment gate** (no pull needed, already
   resident). Role 4. Zero-cost check before spending any budget on a dedicated judge
   model. Do this one first since it costs nothing to try.

**Explicitly excluded on memory/bandwidth grounds** (documented above for
completeness, not recommended): Mistral Small 4 (119B/6B), Qwen3.8-Flash-Next
(125B/6B), MiniMax M2 (229.9B/9.8B), Kimi K2.6 (1T/32B), and Llama 3.3 70B dense as a
default pick (it fits only as an occasional stretch option, consuming the entire
resident budget). Llama 4 (Scout/Maverick) and DeepSeek V4 were checked and found
stale or oversized respectively: Meta has not shipped a new open Llama since April
2025 and pivoted to closed-weight Muse Spark in April 2026, while DeepSeek V4's
smaller "Flash" variant (284B total, 13B active) still exceeds budget at about 160 GB
q4.
