# Agent Scaffolds & Orchestration — Raising Efficacy of a Fixed Local Model

**Research date:** 2026-06-20
**For:** solo dev, M5 Pro 64GB Mac, Ollama/MLX, custom `q`/`lm` CLI suite
**Efficacy definition:** output quality + trustworthiness **per unit of the user's effort**, counting rework and failed attempts (NOT raw speed). The model is fixed; the harness around it is the lever.

---

## TL;DR — the central thesis is well-evidenced

The scaffold (the harness around the model: retrieval, context management, edit format, error-feedback shape, test loops, tool design, task scoping) moves real-world coding success **10–20 percentage points on SWE-bench-class tasks for the SAME model** — a delta as large as a model generation. For a fixed local model, scaffold work is the highest-leverage efficacy investment you can make. The most striking 2026 datapoint: a **4B small model recovers ~90% of frontier-agent performance** when given the right context-control + execution structure — i.e. structure substitutes for parameters.

**Mechanism of efficacy gain (why these raise quality/trust per YOUR effort):** every lever below either (a) **removes a class of failure the model makes unaided** (wrong file, broken diff, hallucinated API, stops too early) so you don't have to catch+redo it, or (b) **moves verification from you to the loop** (tests, linters, a critic pass) so trust is earned mechanically instead of by your manual review. Both reduce rework — the numerator and denominator of your efficacy ratio.

---

## 1. The "scaffold matters as much as the model" evidence (the load-bearing claim)

| Evidence | Number | Source | Conf |
|---|---|---|---|
| Same model (Claude Opus 4.5), 3 different agent systems | scores spread **50.2% → 55.4%** (5.2 pts) from scaffold alone | [digitalapplied, Jun 2026](https://www.digitalapplied.com/blog/swe-bench-verified-june-2026-benchmark-vs-scaffolding-analysis) | High |
| Scale AI on harness choice | **"10 to 20 point swings to harness choices"** | same | High |
| Opus 4.8: vendor scaffold vs standardized SEAL harness | 69.2% vs 51.9% — **17.3 pt gap, same weights** | same | High |
| Weaker model + strong scaffold beats stronger model + generic scaffold | Sonnet 4.5 + CCA scaffold **52.7%** > Opus 4.5 + proprietary **52.0%** | [digitalapplied](https://www.digitalapplied.com/blog/swe-bench-verified-june-2026-benchmark-vs-scaffolding-analysis) | High |
| Open scaffold ≈ funded scaffold on same base | OpenHands+CodeAct v3 **68.4%** vs Augment **72.0%** (same base) → "retrieval, context management, error-recovery drive most of the delta" | same | High |
| **4B SLM recovers ~90% of frontier-agent performance** under tight param/context budget via context control + adaptive tool loading + rubric supervision | "shift from scale-driven to structure-driven agent design" | [arXiv 2603.06713](https://arxiv.org/pdf/2603.06713) | Med-High |

**The six harness variables that drive the delta** (use as your efficacy checklist): context management · attempt budget · tool-use integration · retry/recovery logic · file navigation (search/indexing) · error-feedback formatting. ([digitalapplied](https://www.digitalapplied.com/blog/swe-bench-verified-june-2026-benchmark-vs-scaffolding-analysis))

**Takeaway for a fixed local model:** you cannot change the weights, but you control all six variables. That is where your efficacy gains live.

---

## 2. Coding-agent frameworks that run local models (Ollama / OpenAI-compatible)

| Framework | Local support | Key scaffold features | Mac/Ollama maturity | Effort | Efficacy/effort |
|---|---|---|---|---|---|
| **aider** | `ollama_chat/<model>` (preferred over `ollama/`); auto-sets context window (Ollama defaults to 2k and **silently truncates** — aider fixes this) | **repo-map** (whole-repo relationship map, tree-sitter), **architect/editor split**, multiple **edit formats** (diff/diff-fenced/whole/architect), **2nd attempt with failing-test output**, git-commit-per-change | High — first-class Ollama docs, CLI-native (matches your `q`/`lm` style) | Low | **High** |
| **Continue.dev** (VS Code/JetBrains) | First-class Ollama; **per-role model routing** | route by role: local small model for `autocomplete`, bigger/local for `chat/edit/apply`; tab-complete <300ms | High — "most flexible local setup" | Low-Med | **High** (if you want IDE) |
| **Cline** | 30+ providers + Ollama/LM Studio | plan/act, **parallel agents + Kanban** (2026), checkpoints | High; VS Code-bound | Med | Med-High |
| **Roo Code** (Cline fork) | Ollama | **mode separation: Architect / Code / Debug / Ask** — built-in planner→coder split | High; VS Code | Med | High (for mode discipline) |
| **OpenHands** | LiteLLM → Ollama/llama.cpp/vLLM/**MLX**; SDK for custom agents | CodeAct (actions-as-code), strong retrieval+error-recovery; **68.4% SWE-bench on open base** | Med — heavier, container-oriented | Med-High | Med (overkill for solo single-file) |
| **Goose** (Block) | Ollama | extensions/MCP tool system, offline-capable | Med-High | Med | Med |
| **Zed agents** | Ollama-capable | fast native editor, agent panel | Med (newer agent layer) | Low-Med | Med |

Sources: [aider Ollama docs](https://aider.chat/docs/llms/ollama.html), [aider modes](https://aider.chat/docs/usage/modes.html), [Continue routing](https://www.iamraghuveer.com/posts/continue-dev-model-routing/), [Continue+Ollama 2026](https://localaimaster.com/blog/continue-dev-ollama-setup), [open-source agents comparison 2026](https://wetheflywheel.com/en/guides/open-source-ai-coding-agents-2026/), [Pinggy CLI agents 2026](https://pinggy.io/blog/best_open_source_cli_coding_agents/). Confidence: High for aider/Continue; Med for the rest (vendor-blog sourced).

**Curated pick for your setup:** **aider** is the closest fit — CLI-native (mirrors `q`/`lm`), best-documented Ollama path, and it bundles the three highest-leverage scaffold features (repo-map, architect/editor, edit-format + test-retry) in one tool. **Continue** if you want the IDE + the per-role-routing trick (local model on autocomplete, where latency matters and capability doesn't).

---

## 3. The scaffold FEATURES that drive reliability (per-lever)

Each row: what it is · the **mechanism** (how it cuts YOUR rework) · Mac/Ollama maturity · effort · efficacy/effort.

### 3a. Repo-map / context selection
- **What:** a compact, ranked map of the whole repo's symbols + relationships injected into context (aider's tree-sitter map; or AST/graph code-RAG).
- **Mechanism:** the model edits the **right file with the right neighbors in view** instead of inventing a plausible-but-wrong location or signature. Kills the "edited the wrong place / hallucinated an API that exists elsewhere" failure class — the single most common cause of multi-file-edit rework. For small models this matters MORE: they have less to recall, so just-in-time retrieval substitutes for parametric memory.
- **Maturity:** High (aider built-in). Effort: Low (free with aider). **Efficacy/effort: High.**
- Sources: [aider repo-map](https://aider.chat/docs/llms/ollama.html), [context-engineering playbook 2026](https://www.digitalapplied.com/blog/context-engineering-agent-reliability-playbook-2026).

### 3b. Plan-then-edit (architect/editor split)
- **What:** one pass reasons a plan (architect), a second pass converts plan→concrete file edits (editor). Recommended editor formats: `editor-diff` / `editor-whole`.
- **Mechanism:** separates two skills small models can't do in one shot — "propose a solution" vs "emit a valid structured diff." Splitting them means a reasoning-strong-but-edit-weak model stops corrupting files, and even **the same model twice** beats itself once ("two requests can provide better results"). Trust gain: the plan is reviewable by you *before* any file is touched — cheap veto point, less rollback.
- **Maturity:** High (aider native; Roo Code "Architect mode"). Effort: Low. **Efficacy/effort: High.**
- Source: [aider modes](https://aider.chat/docs/usage/modes.html).

### 3c. Edit-format / diff discipline
- **What:** force the model to emit a structured edit (unified diff / search-replace block) rather than reprint the whole file.
- **Mechanism:** a diff that *applies cleanly* is a binary, machine-checkable contract — a malformed edit fails loudly and retries, instead of silently mangling a file you discover broken later. Also far fewer tokens, so larger files stay in budget. **Caveat:** weaker/local models score lower on diff formats than on `whole` (diff needs deeper context understanding); for a small model, prefer `whole` or `editor-whole` for correctness and accept the token cost, OR use architect mode so a capable editor handles the diff.
- **Maturity:** High. Effort: Low (a config flag). **Efficacy/effort: High.**
- Sources: [aider edit leaderboard](https://aider.chat/docs/leaderboards/edit.html), [aider-polyglot edit](https://llm-stats.com/benchmarks/aider-polyglot-edit), [polyglot benchmark explainer](https://agileleadershipdayindia.org/blogs/ai-coding-benchmarks-decoded/aider-polyglot-benchmark-leaderboard.html).

### 3d. Test-execution loop (the trust engine)
- **What:** run the test/compiler/linter after each edit; feed the **actual failure output** back for a repair attempt (aider's "2nd attempt with failing-test output"; PEV = Plan-Execute-Verify).
- **Mechanism:** this is what converts self-correction from harmful to helpful. **Intrinsic self-correction (no external signal) often DEGRADES output**; with execution feedback it's strongly positive — GPT-4o-mini assertion-correctness +21.76 pts (53.6→75.4%), Gemini-2.0-flash +32 pts (57.3→89.3%) on an iterative test-repair loop. The objective, executable signal is the mechanism. **This is your biggest trust lever:** green tests are earned trust you didn't have to manually verify.
- **Maturity:** High (aider `--test-cmd`/`--auto-test`; any harness with a run loop). Effort: Med (write/expose a fast test or lint command — pairs with a `make verify`-style affordance). **Efficacy/effort: High.**
- Sources: [self-refine unit-tester loop, Dec 2025](https://medium.com/@floralan212/self-refining-llm-unit-testers-iterative-generation-and-repair-via-error-guided-feedback-7c4afd7f5f55), [agent feedback loops 2026](https://newsletter.owainlewis.com/p/the-10x-skill-for-ai-engineers-in), [agentic program repair from test failures](https://arxiv.org/html/2507.18755v1).

### 3e. Error-feedback formatting (cheap, underrated)
- **What:** feed the model *parsed, actionable* errors, not raw dumps. Bad: "violation detected." Good: "use `logger.info({event,...})` instead of `console.log`."
- **Mechanism:** an actionable error enables self-correction *without you*; a vague one bounces back to you. One of the six harness variables behind the 10–20 pt swing. Also: disable the model's ability to *suppress* checks (no `// eslint-disable`) so it fixes rather than silences.
- **Maturity:** High. Effort: Low-Med. **Efficacy/effort: High.**
- Source: [Augment harness-engineering guide](https://www.augmentcode.com/guides/harness-engineering-ai-coding-agents).

---

## 4. Multi-step / multi-agent orchestration patterns

| Pattern | What it is | Mechanism (efficacy gain) | Fixed-local fit | Effort | Eff/effort |
|---|---|---|---|---|---|
| **Generate → critique → refine (self-refine)** | model drafts, then critiques, then revises — iteratively | Works **only with an external signal** (tests/lint/types). Pure intrinsic critique can degrade. Gate iterations on a stopping criterion (don't fix-loop forever; "refined ≠ always better"). | Good IF you wire a real verifier | Low-Med | Med-High |
| **Planner → coder → reviewer split** | distinct roles/passes (Roo Code modes; aider architect/editor) | each pass has ONE job + a clean context → less cross-contamination; reviewer pass catches the coder's misses before they reach you. Reviewable plan = cheap veto. | Strong | Med | High |
| **Deterministic orchestrator + "dumb" model on tight tasks** (Agentless-style) | a hardcoded workflow (localize → repair → validate) drives the model through narrow, well-scoped steps instead of free-roaming agency | **This is the highest-trust pattern for a fixed small model.** The smart logic lives in YOUR deterministic controller; the model only does small, bounded, verifiable sub-tasks it can actually nail. Removes the "agent wanders / over-acts" failure class. Same-input-same-output reliability. Maps perfectly to your `q`/`lm` CLI: you orchestrate, the model fills tight holes. | **Best fit** | Med (you build the controller) | **High** |
| **Draft + verify (two models / two passes)** | a generate pass + a separate verify pass against a spec | verification is moved off your plate onto a second pass checking against a living spec/tests; catches architectural drift invisible to unit tests (e.g. "did it reuse the existing auth pattern?"). | Good | Med | Med-High |
| **Hybrid: deterministic skeleton + AI tactics** | state-machine hardcodes the *what/when*; model decides *how* within bounds | industry 2026 consensus for high-stakes flows: "rules execute consistently, AI reasons where it adds value." Bounds the blast radius of a wrong model call. | Strong | Med-High | Med-High |

Sources: [agentic-vs-deterministic orchestration 2026](https://liviaerxin.github.io/blog/agentic-vs-deterministic-orchestration), [Agentless workflow (localize→repair→validate)](https://arxiv.org/pdf/2604.03515), [self-refine survey](https://arxiv.org/pdf/2510.12399), [CoRefine confidence-guided stopping](https://arxiv.org/pdf/2602.08948), [PEV architecture](https://www.augmentcode.com/guides/harness-engineering-ai-coding-agents). Confidence: High for the pattern existence; Med for exact local-model deltas (most numbers are frontier-model or general-agent).

**The mechanism that unifies them:** decomposition + a checkpoint between steps. Every split inserts a point where either a deterministic check OR you can veto cheaply, *before* error compounds across a multi-file change. The smaller/dumber the model, the tighter the sub-tasks should be — that's the deterministic-orchestrator insight, and it's the one most aligned with both your workload (agentic multi-file coding) and your efficacy-not-speed metric.

---

## 5. Tool & context discipline — the "less is more" levers

| Lever | Mechanism | Source | Conf |
|---|---|---|---|
| **Reduce the toolset** | "Vercel reported that **reducing an agent's available tools improved task success rates**." Fewer tools = fewer wrong-tool selections = less rework. For a small model, every extra tool is a chance to mis-route. | [Augment](https://www.augmentcode.com/guides/harness-engineering-ai-coding-agents) | High |
| **Tight task scoping** | "every model performs significantly better inside a structured harness than in raw chat... not optional." A narrow, bounded task is one a small model can actually complete reliably; a broad one invites wandering. | [MindStudio 2026](https://www.mindstudio.ai/blog/best-open-source-llms-agentic-coding-2026) | Med |
| **Adaptive / just-in-time tool loading** | load only the tools+context the current step needs (vs dumping everything). Part of how the 4B SLM hit ~90% of frontier-agent perf. | [arXiv 2603.06713](https://arxiv.org/pdf/2603.06713) | Med-High |
| **Deterministic constraint layers (feedforward)** | a wired linter that *blocks the PR* beats a prompt saying "follow standards" — constraints execute deterministically, prompts don't. Hard CI gates (`eslint: error`, complexity caps) catch the model's misses mechanically. | [Augment](https://www.augmentcode.com/guides/harness-engineering-ai-coding-agents) | High |
| **Context-awareness / budget signal** | tell the model remaining context after each tool call so it self-manages; avoids the Ollama-2k-silent-truncation class of bug. | [context-engineering playbook](https://www.digitalapplied.com/blog/context-engineering-agent-reliability-playbook-2026), [aider Ollama](https://aider.chat/docs/llms/ollama.html) | High |

**Principle:** for a small/local model, **constrain the surface area** — fewer tools, narrower tasks, smaller just-in-time context, hard mechanical gates. Capability you don't have is replaced by structure that prevents the failure. This is the cheapest efficacy lever (mostly config + scoping discipline, little code).

---

## 6. Priority recommendations for a solo dev on a Mac (ranked by efficacy/effort)

1. **Adopt aider with `ollama_chat/` + fix the context window** (it does this automatically; the 2k-default silent-truncation is a real trap). Unlocks repo-map + architect/editor + edit-format + test-retry in one move. *Low effort, High payoff.*
2. **Turn on a test/lint loop** (`--test-cmd` / `--auto-test`, or a `make verify`). This is your trust engine — converts self-correction from harmful to helpful and moves verification off your plate. *Med effort, High payoff.*
3. **Use architect mode** (or Roo Code's Architect/Code modes) so your model plans first, edits second, with a reviewable plan as a cheap veto point. *Low effort, High payoff.*
4. **For your own `q`/`lm` orchestration: build the deterministic-orchestrator pattern** — YOUR code drives narrow, verifiable sub-tasks; the model fills tight holes. Best structural fit for a fixed small model + your efficacy-not-speed metric. *Med effort, High payoff.*
5. **Cut the toolset and tighten task scope.** Fewer tools, smaller just-in-time context, hard lint gates. *Low effort, High payoff — pure discipline.*
6. **Diff-format caveat:** for a weak local model prefer `whole`/`editor-whole` for correctness; use diff only behind a capable editor pass. *Config-only.*

---

## Caveats / confidence notes
- Most hard percentage deltas are measured on **frontier models** (Opus, Gemini, GPT-5) on SWE-bench-class tasks. The *direction* and *mechanism* generalize to local models (and the 4B-SLM result directly supports stronger gains for small models), but exact local-model point-gains are not cleanly benchmarked per-lever — treat specific numbers as frontier-evidence, the local extrapolation as Med confidence.
- Self-refine literature is explicit that **intrinsic** (no-external-signal) loops can *degrade* output — don't add a critique loop without a real verifier and a stopping criterion.
- Several framework-comparison sources are vendor/SEO blogs (Med confidence); the primary-source claims (aider docs, arXiv, Augment harness guide, the SWE-bench scaffold analysis) are High confidence.
