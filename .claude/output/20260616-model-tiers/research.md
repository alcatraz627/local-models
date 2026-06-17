# Two-tier local model choice — SMALL (warm) + BIG (on-demand) for M5 Pro 64GB

<!-- sessions: model-tiers@2026-06-16 -->
Research date: 2026-06-16. Hardware: MacBook Pro **M5 Pro, 64 GB** unified RAM
(~48 GB usable GPU budget, **~307 GB/s** memory bandwidth — HALF of M5 Max).
Stack: self-hosted `ollama serve`, flash-attn + q8 KV, no-idle. Confidence flags:
**[solid]** multi-source · **[single-source]** · **[computed]** arch/bandwidth math ·
**[hearsay]** community anecdote. Builds on the 2026-06-12 coding-models report.

---

## 0. BOTTOM LINE

```
┌──────────────────────────────────────────────────────────────────────────┐
│ TIER     KEEP / CHANGE          MODEL                  RAM      ~tok/s    │
├──────────────────────────────────────────────────────────────────────────┤
│ SMALL    KEEP (already right)   gemma4-e4b (QAT 4-bit) ~5-6GB   40-60     │
│ (warm)   optional: drop to E2B for max snap on titles/cmd ~1.5GB 60-90+   │
│ BIG      USE WHAT YOU HAVE      gemma4:26b (MoE, 4B act) ~21-27GB 30-45    │
│ (on-dem) ADD for agentic/code   qwen3.6:35b-a3b (MoE)   ~20GB MLX 30-45   │
├──────────────────────────────────────────────────────────────────────────┤
│ DROP     gemma4:31b (dense) — 2-2.5x slower than the 26B you already have │
│          for a 2-4 pt quality gain. Bandwidth-bound on 307GB/s. Pointless.│
└──────────────────────────────────────────────────────────────────────────┘
```

- **Small tier:** gemma4-e4b is **still the right pick** as of 2026-06. Its main
  ≤8GB rival, Qwen3.5-4B, "is comparable in capability but costs 2-5x the
  reasoning tokens" — fatal for a snappy <1s warm companion. Gemma E-series is
  purpose-built for low-latency/edge and is the explicit M5 small-model pick.
- **Big tier:** **you already own the answer — gemma4:26b** is MoE (3.8B active),
  2-2.5x faster than the 31B, and is the documented "strong default" for local
  general work + writing. Add **qwen3.6:35b-a3b** only if you want a sharper
  coding/agentic/tool-calling model (it leads gemma 26B by ~21 pts on SWE-bench).
- **gemma4:31b VERDICT: DROP IT.** Dense ⇒ bandwidth-bound. On this 307GB/s
  machine it lands ~12-18 tok/s and gives ~2-4 benchmark points over the 26B MoE
  you already have at 30-45 tok/s. The "non-encoder hype" doesn't help: every
  decode token must stream all ~31B weights from memory; the MoE streams only the
  active ~4B. The 31B is the textbook wrong-architecture-for-this-machine buy.

---

## 1. gemma4:31b — KEEP or DROP? → **DROP**

The user's literal question: *"I got gemma4:31b because of the hype around its
non-encoder design, but if I can't use that then what's the point."*

**Direct answer: there is no point on this hardware. Delete it.** Here's why,
with numbers:

### The dense-vs-MoE speed gap is not subtle — it's ~2.5x to ~19x

A local head-to-head on identical hardware (RTX 4090, 24GB, Q4/Q6)
([n1n.ai benchmark, 2026-04-06](https://explore.n1n.ai/blog/benchmarking-google-gemma-4-26b-31b-locally-2026-04-06)) **[solid]**:

| Gemma 4 variant | Generation tok/s | Notes |
|---|---|---|
| **26B MoE (A4B)** | **149.6** | "ideal for real-time coding assistants/chatbots" |
| **31B dense** | **7.84** | VRAM maxed → offload; CPU-only AMD actually *beat* the GPU (8.8) because dense is **memory-bandwidth-bound** |

That's a ~19x decode gap *on a GPU* once the dense model is bandwidth/offload
constrained. On a clean fit the gap is ~2-2.5x: a dedicated comparison says the
26B MoE "is consistently 2-2.5x faster" while the dense model "wins on raw
quality… but the margins are small — typically **2-4 points**"
([avenchat / gemma4-ai, 2026](https://avenchat.com/blog/gemma-4-26b-vs-31b)) **[solid]**.

### On the M5 Pro specifically (307 GB/s)

Cross-referencing Apple-Silicon ladders:
- Gemma 4 **31B dense** hits ~20-26 tok/s only on an **M4 Max** (≈600 GB/s, double
  this machine) ([gemma4-ai Mac perf](https://gemma4-ai.com/blog/gemma4-mac-performance),
  [InsiderLLM Mac guide](https://insiderllm.com/guides/best-local-llms-mac-2026/)) **[solid]**.
  On **M5 Max** without proper flash-attn it's been measured at **~15 tok/s**
  ([Ollama issue #15368](https://github.com/ollama/ollama/issues/15368)) **[single-source]**.
- The **M5 Pro has HALF the M5 Max bandwidth.** Dense decode scales ~linearly with
  bandwidth, so expect **~12-18 tok/s** for the 31B here **[computed]** — below the
  "feels responsive" threshold, and the model owns ~24-32 GB while doing it.
- gemma4 dense also hits a **flash-attention bug on Apple Silicon**: its hybrid
  50 sliding-window + 10 global layers with dual head dims (256/512) aren't handled
  correctly by the FA kernel, hurting Apple-Silicon perf and stability
  ([Ollama issue #15368](https://github.com/ollama/ollama/issues/15368)) **[single-source]**.
  MLX doesn't fully support the gemma4 dense arch yet either. So the 31B is both
  slow *and* the rough-edges model on your exact stack.

### What the 31B is actually good at (and why it doesn't matter for you)

The 31B dense is the highest *single-token quality* gemma — #3 open model on
LMArena text (~1441 Elo) — i.e. a touch better prose/arena feel than the 26B. But:
(a) the gap is 2-4 points; (b) the prior research already flagged **gemma4 weak at
tool-calling** (SWE-bench Verified 52.0 vs Qwen3.6's 73.4, and half its MCPMark)
([buildfastwithai](https://www.buildfastwithai.com/blogs/qwen3-6-35b-a3b-review)) **[solid]**;
(c) the 26B MoE carries essentially the same gemma writing voice and function-calling
support at 2.5x the speed. There is no task on this machine where the 31B's tiny
quality edge beats paying 2.5x the latency. **Drop it: `ollama rm gemma4:31b`** —
reclaims ~18-20 GB of disk.

---

## 2. Best BIG model for reasoning + technical writing + reading/summarizing files

The framing is right: **on a 307 GB/s machine, weigh MoE with small active params
heavily** — that's the antidote to the bandwidth limit (see §4). Candidates that
fit ~40 GB:

| Model | Total / Active | Quant→RAM | ~tok/s M5 Pro | Best at |
|---|---|---|---|---|
| **gemma4:26b** (ON DISK) | 25.2B / 3.8B MoE | Q4_K ~17GB · Q6/Q8 ~21-27GB | **30-45** | General reasoning, **technical writing/prose** (best in-tier voice + instruction adherence), summarizing files, vision (you already use it for `imagine critique`). Native function-calling, weaker than Qwen agentically. |
| **qwen3.6:35b-a3b** | 36B / 3B MoE | Q4/MLX-4b ~18-20GB · Q8 ~37GB | **30-45** (MLX) | Coding (SWE-bench 73.4), **tool-calling/agentic** (2x gemma's MCPMark), math/reasoning. More verbose, list-happy in prose; turn thinking OFF for instruction work. |
| gemma4:12b (ON DISK) | 12B dense | Q4 ~8GB | 25-40 | Lighter dense fallback; fine but the 26B MoE dominates it on quality at similar speed. |
| Qwen3.6-27B dense | 27B dense | Q4 ~17GB · Q6 ~22GB | 12-22 | Highest quality-per-token coding, but dense ⇒ slow; "deep review" not "driver". |
| GLM-4.7-Flash | 30B MoE | Q4 ~18GB | 60-80 | Very fast but "~Sonnet 3.5 class," below the gemma/qwen tier. Skip unless you want raw speed over quality. |

### The winner for the user's stated big-tier need (reasoning + tech writing + file summarizing): **gemma4:26b — already downloaded.**

- It's **MoE** (3.8B active) → fast despite 26B total: documented **30-45 tok/s**
  on M4/M5-class Macs ([InsiderLLM](https://insiderllm.com/guides/best-local-llms-mac-2026/))
  and ~31 tok/s generation on an M3 Max 64GB ([Towards AI test](https://pub.towardsai.net/i-tested-alibaba-qwen3-6-35b-a3b-30cc4658a382)) **[solid]**.
- It is **the better gemma for this machine in every way that matters**: same writing
  voice and function-calling as the 31B, ~2.5x faster, less RAM, and it *barely slows
  down at long context* — it degrades only ~32% from 32k→128k vs Qwen3.6's ~65%
  ([modtechgroup long-context test](https://modtechgroup.com/the-model-that-barely-slows-down-gemma-4-26b-vs-qwen-3-6-35b-at-long-context/)) **[solid, NVIDIA but arch transfers]**.
  That long-context-stays-fast property is exactly what you want for *reading and
  summarizing files*.
- Prior research already crowned gemma4-26B "the strong default for local general
  work" and the real-work-shootout winner (12/12 tasks, only model writing correct
  unit tests, perfect tool calling in *fast* mode)
  ([tort_mario real-work test](https://medium.com/@tort_mario/local-llms-in-real-work-gemma-4-qwen-3-6-and-qwen-coder-d43811c7e9b2)) **[single-source, detailed]**.

**So the 31B is redundant** — its only sibling advantage (a hair more prose
quality) is swamped by the 26B's 2.5x speed and long-context resilience. You bought
the slow one; you already own the fast one.

### When to add Qwen3.6-35B-A3B as a SECOND big model

If the big tier is for **coding agents / tool-calling / multi-step technical work**,
gemma's documented weakness there (52 vs 73.4 SWE-bench, half the MCPMark) is real.
Qwen3.6-35B-A3B is also MoE (3B active, same ~30-45 tok/s class) and clearly stronger
agentically. The two are complementary:
- **gemma4:26b** = prose/docs, summarizing, general reasoning, vision (the default big).
- **qwen3.6:35b-a3b** = code, tools, agentic steps (the second big, on-demand).

Both are MoE and stay fast. Neither is dense. That's the whole point.

---

## 3. SMALL (warm) tier — is gemma4-e4b still right? → **YES, keep it**

The warm companion needs: <1s first token, ~5-6GB resident, terse Q&A / macOS
commands / titles / summarize. Candidates surveyed:

| Small model | RAM (Q4) | ~tok/s M5 | Verdict for a *warm snappy companion* |
|---|---|---|---|
| **gemma4-e4b** (current, QAT 4-bit) | ~5-6GB | 40-60 | **KEEP.** Purpose-built for low-latency/edge; strong summarization; good instruction-following; doesn't waste tokens. Your prompt-engineering already tunes it (STATE.md: "prompt is a bigger lever than the model"). |
| gemma4-e2b | ~1.5GB | 60-90+ (158 on M5 Max MLX) | **Optional downgrade** for the *snappiest* path (titles, `q cmd`, one-liners). Explicitly the M5 small-model pick in InsiderLLM. Less smart than E4B — keep E4B as default, consider E2B only if you want a separate ultra-fast title/cmd model. |
| Qwen3.5-4B | ~3GB | 30-45 | **AVOID as warm.** "Comparable capability but **2-5x the reasoning tokens** → responses 2-3x longer" ([codersera](https://codersera.com/blog/gemma-4-vs-qwen-3-5-comparison-2026/), [XDA](https://www.xda-developers.com/ran-gemma-4-and-qwen-35-for-same-local-tasks-one-pulled-ahead/)). Reasoning bloat is the enemy of a snappy companion. Good if you need reasoning, wrong for terse. |
| Phi-4-mini (3.8B) | ~3.5GB | 15-20 (slower) | Solid MMLU (68.5) but slower tok/s and no advantage over gemma E4B for this role. Skip. |
| Llama 3.3 8B | ~5GB | — | "best all-around" general 8B but bigger/slower than E4B with no win on the terse-companion axis. Skip. |

**Conclusion: gemma4-e4b remains the correct small warm model as of 2026-06.** Its
nearest competitor (Qwen3.5-4B) is disqualified by reasoning-token bloat — the exact
opposite of what a <1s companion needs. The only change worth *considering* is
adding **gemma4-e2b** as an even-faster path for the truly trivial intents
(`q title`, `q cmd`) while E4B stays the default for `q ask`/`q summarize`. Not
required — E4B alone is fine.

---

## 4. Bandwidth reality — why MoE crushes dense on THIS 307 GB/s machine

Apple-Silicon decode speed is **memory-bandwidth-bound**, not compute-bound: every
generated token requires streaming the active weights from unified RAM through the
memory bus. Approx ceiling:

```
   max decode tok/s  ≈  memory_bandwidth / (active_params × bytes_per_param)
```

On the M5 Pro at **307 GB/s**, with 4-bit weights (~0.5 byte/param):

| Architecture | Active params/token | Bytes streamed/token | Bandwidth-ceiling tok/s | Real-world tok/s |
|---|---|---|---|---|
| **gemma4:26b MoE** | ~3.8B | ~1.9 GB | ~160 (ceiling) | **30-45** (overhead, KV, q6) |
| **qwen3.6:35b-a3b MoE** | ~3B | ~1.5 GB | ~200 (ceiling) | **30-45** |
| **gemma4:31b dense** | ~31B | ~15.5 GB | **~20 (ceiling)** | **12-18** |

The dense 31B must stream **~8x more bytes per token** than the MoE's active set, so
it's **~2.5x slower in practice** (overheads compress the ceiling gap). This is
exactly what the empirical tests show: 26B MoE 149 tok/s vs 31B dense 7.8 tok/s on a
bandwidth-constrained GPU ([n1n.ai](https://explore.n1n.ai/blog/benchmarking-google-gemma-4-26b-31b-locally-2026-04-06)),
"2-2.5x faster" on a clean fit ([avenchat](https://avenchat.com/blog/gemma-4-26b-vs-31b)),
and the dense model going *faster on CPU than GPU* because both are bandwidth-walled.

**The takeaway the user intuited is correct:** large-total / small-active MoE is the
right shape for a half-bandwidth M5 Pro. You get 26-35B worth of "knowledge in the
weights" while only paying the bandwidth tax of ~3-4B per token. The 31B dense pays
the full tax every token — it's the one architecture this machine is worst at.

---

## 5. Concrete recommendation + commands

**Standardize on (all already on disk except the optional Qwen pull):**

1. **SMALL / warm:** `gemma4-e4b` — keep as-is. (Optional: pull `gemma4:e2b` ~1.5GB
   for an ultra-fast title/cmd path; not required.)
2. **BIG / on-demand default:** `gemma4:26b` — already downloaded. Make this the
   `q -m big` / heavy alias. Reasoning, technical writing, file summarizing, vision.
3. **BIG / on-demand coding+agentic (optional add):** if you want a sharper tools/code
   model than gemma, pull the MoE Qwen:
   ```bash
   ollama pull qwen3.6:35b-a3b      # ~20GB at 4-bit; MoE, ~30-45 tok/s, strong tool-calling
   ```
   (Or run it via your MLX venv — MLX gives ~15-30% more tok/s and the prior research
   flags Ollama 0.19's MLX backend as the integration point.)

**Drop:**
```bash
ollama rm gemma4:31b              # dense, bandwidth-bound, redundant vs the 26B MoE you own
```

If you keep exactly one big model: **gemma4:26b**. If two: **gemma4:26b** (general/prose)
+ **qwen3.6:35b-a3b** (code/agentic). The 31b is in neither list.

### num_ctx / KV guidance (carry over from prior research)
- gemma4:26b: docs/summaries rarely need >32k; pin `num_ctx 32768` (Q6/Q8). gemma's
  sliding-window KV keeps long context cheap — it's the long-context-stays-fast model.
- qwen3.6:35b-a3b: `num_ctx 65536` q8 KV ≈ 20GB weights + ~3GB. Fine standalone.
- Keep `OLLAMA_FLASH_ATTENTION=1` (required for q8 KV). Note the gemma4 *dense* FA bug
  on Apple Silicon — another reason to avoid the 31B; the 26B MoE is the cleaner path.

---

## Sources (load-bearing)

- https://explore.n1n.ai/blog/benchmarking-google-gemma-4-26b-31b-locally-2026-04-06 — 26B MoE 149.6 vs 31B dense 7.84 tok/s; dense beats GPU on CPU (bandwidth-bound)
- https://avenchat.com/blog/gemma-4-26b-vs-31b — "26B MoE 2-2.5x faster, dense wins quality by only 2-4 pts; 26B is the better local choice"
- https://gemma4-ai.com/blog/gemma4-mac-performance — Gemma 4 tok/s ladder by Apple chip (31B dense 20-26 only on M4 Max)
- https://insiderllm.com/guides/best-local-llms-mac-2026/ — M5 small pick (Gemma E2B 30-45 tok/s); 26B MoE 30-45, 31B dense 18-28, Qwen3.6-35B-A3B 35-55
- https://github.com/ollama/ollama/issues/15368 — gemma4 dense flash-attn bug + ~15 tok/s 31B on M5 Max; MLX not supported for dense
- https://modtechgroup.com/the-model-that-barely-slows-down-gemma-4-26b-vs-qwen-3-6-35b-at-long-context/ — Gemma 26B degrades 32% vs Qwen3.6 65% at long context
- https://pub.towardsai.net/i-tested-alibaba-qwen3-6-35b-a3b-30cc4658a382 — Qwen3.6 SWE-bench 73.4 vs Gemma 26B 52.0 (21-pt gap); M3 Max 64GB ~31 tok/s
- https://www.buildfastwithai.com/blogs/qwen3-6-35b-a3b-review — gemma weak tool-calling (MCPMark half of Qwen); SWE-bench gap
- https://codersera.com/blog/gemma-4-vs-qwen-3-5-comparison-2026/ + https://www.xda-developers.com/ran-gemma-4-and-qwen-35-for-same-local-tasks-one-pulled-ahead/ — Qwen3.5-4B 2-5x reasoning-token bloat (why it's wrong for warm)
- https://medium.com/@tort_mario/local-llms-in-real-work-gemma-4-qwen-3-6-and-qwen-coder-d43811c7e9b2 — gemma 26B won 12/12 real-work shootout
- https://localaimaster.com/blog/small-language-models-guide-2026 + https://www.sitepoint.com/best-local-llm-models-2026/ — small-model ≤8GB landscape (Phi-4-mini, Llama, Gemma E-series)
