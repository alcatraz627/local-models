# Output Reliability + Model Adaptation — Raising a Fixed Local Model's Efficacy

**Scope:** Software levers that make a *fixed* local coding model (M5 Pro 64 GB, Ollama/MLX) more **trustworthy and less rework-prone** — efficacy = output quality + trustworthiness per unit of *your* effort, counting rework and failed attempts. NOT about speed, NOT about bigger hardware.

**Date compiled:** 2026-06-20. All sources cited with URL + date + confidence.

---

## TL;DR — the efficacy-per-effort ranking

| Lever | What it buys | Effort to adopt | Efficacy/effort | Verdict |
|---|---|---|---|---|
| **1. Constrained/structured decoding** | Eliminates malformed-output rework class entirely (100% valid JSON/tool-calls) | **Low** (flag in Ollama/Outlines) | ★★★★★ | **Adopt now — high-payoff, low-effort** |
| **2. Verify→self-repair loop** | Catches the bugs *before you do* — biggest single rework-killer for agentic coding | **Low–Med** (harness wiring you mostly have) | ★★★★★ | **Adopt now — highest trust gain** |
| **5. Model routing / cascade** | Easy→lean local, hard→beefy/cloud; spends effort where it pays | **Med** (classifier + escalation rule) | ★★★★☆ | **Adopt — ties directly to your triad** |
| **3. Ensemble / sampling (Self-MoA, best-of-N)** | Quality bump on *genuinely hard* tasks only; wasteful elsewhere | **Med** (sample N + verifier) | ★★★☆☆ | **Selective — gate behind difficulty/verifier** |
| **4. Local LoRA fine-tune (MLX)** | Bakes *your* conventions into the model — the "isotope chemistry" lever | **Med–High** (data curation + train) | ★★★☆☆ | **Research-project; high ceiling, slow payoff** |

**The two cheap wins that compound:** structured decoding (kills format rework) + a verify-loop (kills logic rework). Together they remove the two largest rework classes for a solo agentic-coding workflow before any model swap or fine-tune.

---

## Lever 1 — Constrained / Structured Decoding

### What it is
At each decoding step the sampler **masks out tokens that would violate a grammar / JSON-schema / regex**, so the output is *structurally guaranteed* valid — not "usually valid if you prompt nicely." Implementations: **GBNF grammars (llama.cpp)**, **Outlines** (schema→regex→FSM), **XGrammar** (compiled CFG, now the default backend across vLLM/SGLang/MLC), **guidance**, plus the `format`/JSON-schema parameter in Ollama.

### Mechanism for raising efficacy/trust
The single most common silent failure in agentic coding is a tool-call or structured response that *almost* parses — a trailing comma, Markdown fence around JSON, a hallucinated field. That triggers a full retry round-trip (your effort + latency + possible cascading wrong-state). Constrained decoding makes that failure class **impossible**, not rare. The cost-study below quantifies it: "Structured Intent Extraction" with a 3B model had *near-zero benefit precisely because the model returned Markdown instead of raw JSON* — i.e. the failure constrained decoding fixes is real and measured at this model scale.

### 2026 tooling + Mac/MLX maturity
- **Ollama**: native `format` param accepts a JSON schema; pair with Pydantic/Zod. Low temp (0) recommended for rigid adherence. *Mature, zero-install.* ([Ollama structured outputs blog](https://ollama.com/blog/structured-outputs), accessed 2026-06-20; confidence **high**)
- **Outlines + mlx-lm**: Outlines has a first-class **mlx-lm backend** — "supports all forms of structured generation available in Outlines" on Apple Silicon, converting schema→regex→constrained sampling. ([Outlines mlx-lm docs](https://dottxt-ai.github.io/outlines/latest/features/models/mlxlm/), accessed 2026-06-20; confidence **high**)
- **XGrammar**: universal deployment incl. Apple Silicon; **near-zero JSON overhead**, up to 3× speedup on JSON-Schema and >100× on CFG vs baselines; **XGrammar-2 released May 2026** targeting *agentic* dynamic grammars. ([XGrammar GitHub](https://github.com/mlc-ai/xgrammar), [arXiv 2411.15100](https://arxiv.org/abs/2411.15100), [XGrammar-2 arXiv 2601.04426](https://arxiv.org/pdf/2601.04426); accessed 2026-06-20; confidence **high**)
- **llama.cpp GBNF**: built-in `--grammar` / `--json-schema`; converts JSON-Schema Draft-7 subset to GBNF. The escape hatch when you need a *custom* grammar (e.g. a DSL, a constrained diff format) Ollama can't express. ([llama.cpp grammars README](https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md), accessed 2026-06-20; confidence **high**)
- mlx-omni-server ships an `OutlinesLogitsProcessor` for tool-call/function parsing on MLX. ([deepwiki mlx-omni-server](https://deepwiki.com/madroidmaq/mlx-omni-server/4.7-tool-calling-and-function-parsing), accessed 2026-06-20; confidence **med**)

A 2026 benchmark across Guidance/Outlines/llama.cpp/XGrammar/OpenAI/Gemini against the JSON-Schema Test Suite confirms broad correctness but **divergent edge-case handling** — pick one and pin it. ([arXiv 2501.10868](https://arxiv.org/html/2501.10868v1), accessed 2026-06-20; confidence **high**)

### Effort to adopt
**Low.** For Ollama: add a `format` schema to the request. For MLX path: `pip install outlines`, wrap the model, pass a Pydantic model. No training, no infra.

### Efficacy-per-effort: ★★★★★ — **high-payoff, low-effort. Do this first.**
Caveat: constraining *structure* does not constrain *correctness* — a schema-valid but semantically wrong tool call still happens. That gap is what Lever 2 closes.

---

## Lever 2 — Verification / Self-Repair Loops

### What it is
After generation, **run a real checker** — tests, linter, type-checker, compiler, execution — and **feed the errors back** as the next turn's context, looping until green. Family: agentic test/lint loop ("edit→run tests→self-correct until green"), **self-debugging** (traceback fed back), **Reflexion** (write a natural-language critique of the failure, store it, inject into the retry), **Self-Refine** (generate→self-critique→revise), and "generate-then-verify" with a *separate* checker model.

### Mechanism for raising efficacy/trust
This is the **single biggest rework-killer** for agentic multi-file coding, because the verifier — not you — catches the bug. The model's own confidence is poorly calibrated ("fluent, authoritative, high token-probability, and wrong"), so trust must come from an *external, deterministic* signal. A passing test suite is a trustworthy delegation receipt; a confident prose claim is not. The loop converts "I review every diff by hand" (high user-effort) into "I review the diff that already passed tests" (low user-effort, far less rework). 2026 frameworks treat this as table stakes: "lint/test loops run linters and tests after every AI edit," on a continuous **Plan–Act–Verify** cycle. ([Self-Debugging Agent](https://www.emergentmind.com/topics/self-debugging-agent), [Agentic Loops 2026 Guide](https://datasciencedojo.com/blog/agentic-loops-explained-from-react-to-loop-engineering-2026-guide/), accessed 2026-06-20; confidence **high**)

### 2026 tooling + Mac/MLX maturity
- The **harness**, not the model, owns this — and you already run an agentic harness. The lever is: ensure the agent loop *actually executes* `test`/`lint`/`tsc` after each edit and re-feeds failures, rather than declaring done off inspection. (Directly mirrors your own `exercise-based-verification` rule.)
- Reflexion adds a **memory of past failures** injected into retries — cheap to bolt on (keep a running "what went wrong last attempt" note in context). ([Reflexion via Agentic Loops guide], accessed 2026-06-20; confidence **high**)
- "Self-Spec" (model authors an executable spec first, then codes to it) lifted pass@1 on HumanEval **87→92% (GPT-4o), 92→94% (Claude 3.7)** — evidence that a verify-against-spec wrapper raises first-pass quality on a *fixed* model. ([Self-Spec OpenReview](https://openreview.net/forum?id=6pr7BUGkLp), accessed 2026-06-20; confidence **med** — frontier models, not local, but mechanism transfers)
- Local-specific: a self-distillation paper ("Embarrassingly Simple Self-Distillation Improves Code Generation") shows generate→filter-by-tests→reuse improves code gen cheaply. ([arXiv 2604.01193](https://arxiv.org/abs/2604.01193), accessed 2026-06-20; confidence **med**)

### Effort to adopt
**Low–Med.** Mostly *harness configuration* (make the loop mandatory, cap iterations, surface the failing test). The "separate checker" variant costs a second model call.

### Efficacy-per-effort: ★★★★★ — **highest trust gain per unit effort.**
The deterministic verifier is what makes delegation trustworthy. Pair with Lever 1: structured decoding guarantees the *form*, the test loop guarantees the *behavior*.

---

## Lever 3 — Ensemble / Sampling Methods

### What it is
Spend more *compute* (not your effort) to raise quality on a fixed model:
- **Self-consistency**: sample N answers, majority-vote.
- **Best-of-N**: sample N, pick the best via a **verifier / reward model** (for code: *which candidate passes the most tests* — an execution-grounded verifier, far stronger than a vote).
- **Mixture-of-Agents (MoA)**: multiple proposers → an aggregator model synthesizes.
- **Self-MoA**: one *strong* model is both proposer (sampled hot, N times) and aggregator.
- **Generate→critique→refine**: single-model iterative.

### Mechanism — and the 2026 caveat that reshapes the advice
The headline 2026 finding: **self-consistency is hitting diminishing/negative returns.** On tasks a model already solves, extra samples "introduce noise rather than signal" — Gemini-2.5-Pro gained **1.6% on MATH-500 at 15× the token cost**; HotpotQA gained **0.4% across 20 samples**. Recommendation: **difficulty-aware routing — apply sampling *only* to hard queries.** ([arXiv 2511.00751 "Self-Consistency Is Losing Its Edge"](https://arxiv.org/html/2511.00751), accessed 2026-06-20; confidence **high**)

Two efficiency variants recover most of the cost: **ReASC** (reliability-aware) saves 70–80% vs naive SC; **CISC** (confidence-informed) saves 40–50% with minor accuracy gain. ([arXiv 2601.02970](https://arxiv.org/pdf/2601.02970), accessed 2026-06-20; confidence **med**)

**Critical for a solo dev with ONE model: Self-MoA beats mixed MoA.** "Rethinking MoA" shows **quality of individual models matters more than diversity** — Self-MoA (sample the *one best* model hot, aggregate) beat mixed-model MoA by **+6.6% on AlpacaEval 2.0, +3.8% avg** across MMLU/CRUX/MATH. So you don't need a zoo of local models; you need to sample your *best* one well and aggregate. A sequential **Self-MoA-seq** sliding-window variant fits limited context. ([arXiv 2502.00674](https://arxiv.org/abs/2502.00674), accessed 2026-06-20; confidence **high**)

MoA cost reality: multi-layer MoA **triples latency for ~2–4 MT-Bench points** — "worth it for high-stakes async tasks, not for interactive serving." ([MoA analysis](https://www.spheron.network/blog/mixture-of-agents-gpu-cloud/), accessed 2026-06-20; confidence **med**)

### For coding specifically — prefer execution-grounded best-of-N
For code, a **verifier that runs the tests** dominates majority-vote: sample N candidates, keep the one(s) passing the most tests. This converts "ensemble" from a vote (noisy) into "best-of-N gated by the Lever-2 verifier" (grounded). Execution-guided generation (e.g. for SQL, [arXiv 2503.24364](https://arxiv.org/pdf/2503.24364)) is the same idea. Confidence **high** that test-gated best-of-N > vote for code.

### Effort to adopt
**Med.** Sampling N is trivial; the value is entirely in the *verifier*. Without an execution verifier, ensembles add compute for little trustworthy gain.

### Efficacy-per-effort: ★★★☆☆ — **selective, not default.**
Gate it: cheap difficulty signal (or "first attempt failed the test loop") → escalate to best-of-N-with-test-verifier on *that* task only. Blanket self-consistency wastes compute on tasks already solved.

---

## Lever 4 — Local Fine-tune / LoRA on Apple Silicon (the "isotope chemistry" lever)

### What it is
**LoRA/QLoRA via `mlx-lm`** to adapt your fixed base model to *your* codebase conventions, naming, idioms, internal APIs, comment style, and domain — by training small low-rank adapter matrices (base weights frozen). QLoRA keeps a 4-bit base + full-precision adapter for memory savings.

### Mechanism for raising efficacy/trust
Generic models produce *generically correct* code that violates *your* conventions → you rework it into house style every time. A LoRA trained on your repo's accepted diffs/PRs shifts the model's default output toward "the way this codebase does it," cutting the convention-rework tax and making delegation feel like a teammate who's read the codebase. It's the only lever that changes the model's *priors* rather than filtering its outputs — high ceiling, but the payoff is gradual and data-dependent.

### 2026 tooling + Mac/MLX maturity — strong
- **`mlx_lm.lora --train`**: point at a HF model + a **JSONL of 200–500 examples**; QLoRA on a 16 GB Mac fine-tunes an **8B model in ~1 hour**; Mistral-7B on 5k examples ≈ **90 min on M2 Max 32 GB, ~7 GB peak**. On your **M5 Pro 64 GB** this is comfortable, with headroom for larger ranks / bigger bases. ([mlx-lm LORA.md](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md), [Medium LoRA+MLX-LM](https://medium.com/@levchevajoana/fine-tuning-llms-with-lora-and-mlx-lm-c0b143642deb), accessed 2026-06-20; confidence **high**)
- Supported families: Llama, Mistral, Qwen2/Qwen3, Gemma, Phi, Mixtral, OLMo, etc. — covers the 2026 local-coder shortlist (Qwen3-Coder).
- **Serving the LoRA locally**: `mlx_lm.server` accepts an **`adapter` param per-request at inference time** — you can serve the base and hot-swap adapters without merging. Point any OpenAI-compatible client (Open WebUI, your `q` tool) at `localhost:8080`. ([mlx-lm server LoRA serving], accessed 2026-06-20; confidence **high**)
- Tooling ecosystem matured: **MLX-LoRA-Studio** (native Mac GUI, on-device), **mlx-tune** (SFT/DPO/GRPO + **LoRA continued-pretraining** for domain code, Unsloth-compatible API). ([MLX-LoRA-Studio](https://github.com/Goekdeniz-Guelmez/MLX-LoRA-Studio), [mlx-tune](https://github.com/ARahim3/mlx-tune), accessed 2026-06-20; confidence **high**)

### Effort to adopt
**Med–High.** Training is one command; the *real* cost is **data curation** — assembling clean instruction→accepted-code pairs from your repos (PRs, commit diffs, reviewed code). 200–500 good examples is the entry bar; quality of pairs dominates outcome. Plus an eval loop to confirm the adapter helps and didn't degrade general ability (catastrophic forgetting risk).

### Efficacy-per-effort: ★★★☆☆ — **research-project, high ceiling.**
Not the first move. Adopt *after* Levers 1+2+5 are in place and you've identified a *specific, repeated* convention-rework pattern worth baking in. Start with a tiny adapter on one convention (e.g. your error-handling idiom), measure rework reduction, then expand. The hardware is ready; the bottleneck is your labeled-data discipline.

---

## Lever 5 — Model Routing / Cascades

### What it is
Don't send every task to the same model. **Route**: predict the right model up front (easy→lean local, hard→beefy local or cloud). **Cascade**: start cheapest, escalate on a **confidence/quality check** (e.g. local test-loop failed, or classifier logprob below threshold). Frameworks: RouteLLM, FrugalGPT-style cascades.

### Mechanism for raising efficacy/trust — ties directly to your ease-effort-output triad
This is the *meta*-lever: it spends your premium resources (cloud tokens, slow big-model passes, *your attention*) only where they change the outcome. Trivial edits go to the lean local model (fast, free, good-enough); genuinely hard multi-file reasoning escalates to a beefier local model or cloud. The **2026 cost study (Local-Splitter)** measured this on real coding-agent workloads:

| Tactic | Measured effect |
|---|---|
| **T1 Local Routing** (route trivial reqs to local) | **29–69% cloud-token savings** — *the single strongest tactic*; 68.8% on explanation-heavy by routing ~45% of trivial reqs local |
| **T1 + T2** (route + local prompt-compression) | **45–79% savings**, the recommended default |
| T2 Prompt compression (local model shrinks context) | 18–22% |
| **T4 Local-draft → cloud-review** | **BACKFIRES: +31–41% MORE cloud tokens** on output-light work (review prompt re-sends full context) — only net-positive on RAG-heavy long-output (12.6%) |
| "turn everything on" | **Underperforms T1+T2** — no universal setting |

([Local-Splitter, arXiv 2604.12301](https://arxiv.org/html/2604.12301), accessed 2026-06-20; confidence **high**)

**The trap to avoid:** "local drafts, cloud reviews" (T4) *increases* cost/effort on typical coding work because re-sending the full conversation + draft triples cloud input. Prefer **route-then-commit** (decide tier up front) over **draft-everywhere-then-escalate** for short outputs.

### The confidence-calibration caveat
Cascade escalation needs a trigger, and **self-reported LLM confidence is poorly calibrated** — "fluent, authoritative, high token-probability, and factually wrong." So the most *trustworthy* escalation signal is **external**: did the Lever-2 test loop fail? did the structured-decode constraint get hit repeatedly? That's a far better "this is hard, escalate" signal than the model's own confidence. ([Local-Splitter; arXiv 2410.13284 Confidence Tokens; arXiv 2512.20012 edge-cloud-expert cascade], accessed 2026-06-20; confidence **high** on calibration claim)

### 2026 tooling + Mac maturity
- A lightweight **few-shot classifier** ("could a junior solve this in <10s? → local") is what the cost study used — cheap to build, no special infra.
- Your existing `q` tiering (small/big/code) + a cloud fallback ("just use chatgpt" mode) **is already a cascade** — the lever is making the escalation *rule* explicit and tied to the verifier signal, plus an edge-cloud-**expert** tier (escalate to *you* only when both local and cloud fail the verifier). ([arXiv 2512.20012](https://arxiv.org/pdf/2512.20012), accessed 2026-06-20; confidence **med**)

### Effort to adopt
**Med.** A working classifier + an explicit escalation rule. You already have the tier scaffolding.

### Efficacy-per-effort: ★★★★☆ — **adopt; it's the spine your other levers hang on.**
Routing decides *which* model; Levers 1–2 make each tier trustworthy; Lever 3 is the "escalate-by-sampling" rung; Lever 4 upgrades the local tier's priors.

---

## How the levers compose (recommended adoption order for a solo Mac dev)

```
┌──────────────────────────────────────────────────────────────────────┐
│  TASK                                                                  │
│   │                                                                    │
│   ▼                                                                    │
│  [5] ROUTE  ── trivial ──►  lean local model ─┐                        │
│   │                                            │                       │
│   └── hard ──►  beefy local / cloud ───────────┤                       │
│                                                ▼                       │
│                            [1] CONSTRAINED DECODE  (form guaranteed)   │
│                                                ▼                       │
│                            generate                                    │
│                                                ▼                       │
│                            [2] VERIFY: run tests / lint / types        │
│                               │ pass ──────────────────► DONE (trust)  │
│                               │ fail                                   │
│                               ▼                                        │
│                            self-repair loop (feed error back) ──┐      │
│                               │ still failing after K tries      │     │
│                               ▼                                  │     │
│                            [3] best-of-N + test-verifier  ◄──────┘     │
│                               │ still failing                          │
│                               ▼                                        │
│                            [5] ESCALATE tier / ask the human           │
│                                                                        │
│  [4] LoRA  =  upgrades the "lean/beefy local model" box's priors       │
│               toward YOUR conventions (offline, gradual)               │
└──────────────────────────────────────────────────────────────────────┘
```

**Week-1 (low-effort, high-payoff):** turn on **constrained decoding** for every structured/tool output (Lever 1), and make the **verify→self-repair loop mandatory** in the harness with the external test signal as the trust gate (Lever 2). These remove the format-rework and logic-rework classes — the two biggest — with near-zero build cost.

**Week-2:** formalize **routing/cascade** with the escalation rule keyed to the *verifier* (not model confidence), avoiding the T4 draft→review backfire (Lever 5).

**Selective:** gate **best-of-N-with-test-verifier** behind "first attempt failed" (Lever 3) — never blanket self-consistency.

**Later / research:** curate accepted-diff data and train a **convention LoRA** in MLX once a specific repeated rework pattern is identified (Lever 4).

---

## Confidence summary & open caveats

- **Constrained decoding (L1)** — *high confidence*, mature on Mac (Ollama native, Outlines+mlx-lm, XGrammar, GBNF). Closes form-rework. Does not ensure semantic correctness.
- **Verify loop (L2)** — *high confidence* it's the top trust lever; mechanism is harness-owned and matches your existing exercise-based-verification discipline.
- **Ensembles (L3)** — *high confidence on the diminishing-returns finding*; the actionable form for code is **test-gated best-of-N**, gated by difficulty. Self-MoA > mixed-MoA is well-supported and convenient (one model).
- **LoRA (L4)** — *high confidence the tooling is ready* on M5 64 GB; *medium confidence on payoff* — entirely gated by your data-curation effort and forgetting-control. Highest ceiling, slowest payoff.
- **Routing (L5)** — *high confidence* T1 local-routing is the strongest cost tactic and the T4 backfire is real; *medium confidence* on the best escalation trigger, but external-verifier-as-trigger is sound given poor confidence calibration.

**Cross-cutting trust principle (recurs in 4 of 5 levers):** the model's self-confidence is not a trustworthy signal — derive trust from *external, deterministic* checks (schema validity, passing tests, execution). Build every lever to lean on that, not on the model saying it's sure.
