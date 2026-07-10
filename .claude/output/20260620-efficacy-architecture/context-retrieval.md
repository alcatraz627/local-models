# Context Engineering & Retrieval — Raising the Efficacy of a Fixed Local Coding Model

**Date:** 2026-06-20
**Setup target:** M5 Pro, 64 GB unified memory, Ollama/MLX, agentic multi-file coding, solo dev.
**Efficacy definition used throughout:** output quality + trustworthiness *per unit of the user's effort, counting rework* — NOT speed.

> Thesis (well-supported by 2026 evidence): for a *fixed* small/mid local model, **what you put into the context window is a larger quality lever than the model's parameter count**. "Context engineering" — selecting, structuring, compressing, and persisting the right context — is the highest efficacy-per-effort surface available without changing hardware. The 2026 framing shift is explicit: prompt engineering moved from *"how to ask"* to *"what to provide"* ([Medium / Prompt Engineering 2026](https://medium.com/codetodeploy/prompt-engineering-2026-series-0-introduction-3e331e955433), 2026).

---

## TL;DR ranking — efficacy-per-effort for a solo Mac dev

| Rank | Lever | Efficacy/effort | One-line why |
|------|-------|-----------------|--------------|
| 1 | **System-prompt design for small models** (role + conventions + structured task framing) | ★★★★★ | Near-zero effort, disproportionately helps small models; corroborates user's 4B-beats-codemodel finding |
| 2 | **AGENTS.md / convention injection** | ★★★★★ | Write once, every session inherits project rules → less re-explaining, less rework |
| 3 | **Structural repo map (tree-sitter / aider PageRank)** | ★★★★☆ | Automatic, zero-config relevant context; beats raw file dumps AND naive vector RAG for code |
| 4 | **Context compression / pruning + "context rot" avoidance** | ★★★★☆ | Keeping context SMALL is itself a quality lever; small models rot faster |
| 5 | **Prompt/KV caching for a stable system prompt** | ★★★☆☆ | Mostly a speed/cost win, but enables keeping a richer stable preamble cheaply |
| 6 | **Cross-session memory / state** | ★★★☆☆ | Reduces re-explaining; tooling still maturing, drift risk |
| 7 | **Code-embedding RAG (vector search)** | ★★☆☆☆ | Real but lowest ROI for code specifically; structural maps usually win; use as *complement* |

---

## Lever 1 — System-prompt design for SMALL models (the user's own finding, corroborated)

**What it is.** A carefully engineered system prompt: explicit role priming ("senior software engineer…"), task framing, output-format constraints, and 1–3 few-shot exemplars — applied to a *fixed* model.

**Mechanism for efficacy.** Small instruction-tuned models have less internalized "default behavior," so the system prompt fills a larger share of the behavioral gap. A good prompt narrows the quality gap to larger models, which directly cuts rework (fewer malformed diffs, fewer off-spec answers, more trustworthy first attempts).

**Evidence / corroboration of user's finding.**
- *An Empirical Study on the Effects of System Prompts in Instruction-Tuned Models for Code Generation* (Cheng & Mastropaolo, arXiv 2602.15228, **2026-02-18**): system prompts "significantly impact code generation performance across model scales"; **smaller models show particularly pronounced improvements** from carefully engineered prompts, "narrowing the performance gap with larger models" — measured in pass@k. **This directly corroborates the user's observation that a 4B + good system prompt beat a code model + generic prompt.** Confidence: HIGH (peer-style empirical study, on-point).
- *Toward Green Code: Prompting Small Language Models* (arXiv 2509.09947, 2025): role prompting + few-shot tested on StableCode-3B, Qwen2.5-Coder-3B, CodeLlama-7B, Phi-3-Mini — instruction-tuned SLMs respond strongly to role + few-shot. Confidence: HIGH.
- *The Impact of Prompt Programming on Function-Level Code Generation* (arXiv 2412.20545): prompt structure measurably moves function-level pass rates. Confidence: MEDIUM-HIGH.

**Concrete recipe (curated for this setup):**
1. **Role prime**: "You are a senior engineer working in *this* repo. Prefer the existing patterns over inventing new ones."
2. **Structured task framing**: tell it to (a) restate the task, (b) list files it will touch, (c) propose a plan, (d) only then edit. (Aligns with the user's anti-one-shotting → plan+review preference already baked into the project.)
3. **Output contract**: exact diff/format, "no prose unless asked."
4. **1–2 few-shot exemplars** of a correct edit in *this* codebase's style — few-shot is now classed as a *context-engineering* method, not just prompt phrasing ([Analytics Vidhya, 2026-01](https://www.analyticsvidhya.com/blog/2026/01/master-prompt-engineering/)).

**Mac maturity:** N/A (model-agnostic, works on any Ollama/MLX model today).
**Effort to adopt:** Very low (one file, iterate). **Efficacy/effort: ★★★★★.**

---

## Lever 2 — AGENTS.md / convention injection

**What it is.** A markdown file at repo root with persistent project-specific guidance: build/test commands, coding conventions, constraints the model *cannot infer* from the code alone. Read and injected into the agent's context every session.

**Mechanism for efficacy.** Eliminates the largest recurring tax in agentic coding — *re-explaining the project every session*. The model gets the conventions for free, so it produces on-convention work the first time → less rework, higher trust. This is the cheapest persistent-memory mechanism that exists.

**Evidence / tooling (2026):**
- [Augment Code — How to Build Your AGENTS.md (2026)](https://www.augmentcode.com/guides/how-to-build-agents-md): defines AGENTS.md as the standard context file giving agents build commands, conventions, test rules, constraints not inferrable from code. Confidence: HIGH.
- [particula.tech — AGENTS.md Explained (2026)](https://particula.tech/blog/agents-md-ai-coding-agent-configuration): open format, root-level, persistent operational guidance. Confidence: HIGH.
- *Configuring Agentic AI Coding Tools: An Exploratory Study* (arXiv 2602.14690, 2026): empirical look at how teams configure agent instruction files. Confidence: MEDIUM-HIGH.
- **Security caveat:** AGENTS.md is an injection surface — VS Code injects it by default; a hostile repo's AGENTS.md can hijack an agent ([prompt.security, 2026](https://prompt.security/blog/when-your-repo-starts-talking-agents-md-and-agent-goal-hijack-in-vs-code-chat)). For a *solo dev on own repos* this risk is ~nil, but don't auto-trust AGENTS.md from cloned third-party repos. Confidence: HIGH.

**Mac maturity:** Fully supported — most local agent front-ends (Cline, Continue, aider via conventions file) read it today.
**Effort to adopt:** Very low (write one file per repo). **Efficacy/effort: ★★★★★.**

---

## Lever 3 — Structural repo map (tree-sitter / ctags / dependency graph) vs raw file dumps

**What it is.** Parse the repo with tree-sitter, extract symbol *definitions and references*, build a symbol graph, rank by relevance (aider uses **personalized PageRank** over the graph), and feed the model a **token-budgeted map** of the most relevant signatures — not full file contents.

**Mechanism for efficacy.** A repo map gives the model *structural awareness* (what exists, where, how it connects) at a fraction of the tokens of dumping files. This is exactly the right move for small models because (a) it keeps context small → less context rot, (b) it surfaces the *right* symbols so the model edits the correct file the first time → less rework, (c) it adapts automatically to the conversation with zero user effort.

**Why structural beats both raw dumps AND naive vector RAG for code:**
- Raw file dumps blow the budget and trigger lost-in-the-middle (Lever 4).
- Vector RAG retrieves *semantically similar* chunks, but "current embedding models are not code-oriented and lack effective translation between natural language and code" → "simple vector similarity search often retrieves irrelevant or out-of-context snippets" ([Qodo, 2026](https://www.qodo.ai/blog/rag-for-large-scale-code-repos/)). Aider's graph approach is "automatic, graph-based, zero-effort context that adapts to the conversation," prioritizing structural analysis over fragile semantic ranking ([aider repomap docs](https://aider.chat/docs/repomap.html); [DeepWiki: Aider Repository Mapping](https://deepwiki.com/Aider-AI/aider/4.1-repository-mapping-system)). Confidence: HIGH.

**Evidence / tooling (2026):**
- **aider** — tree-sitter repo map + PageRank ranking, `--map-tokens` budget (default ~1k). 43k★, ~15B tokens/wk as of Apr 2026, first-class local-LLM support ([aider docs](https://aider.chat/docs/); [Tekai catalog](https://tekai.dev/catalog/aider)). Confidence: HIGH.
- **Continue `@codebase`** — indexes and retrieves repo context for local models; "handles context window management and model-specific prompting better than other extensions tested" ([DevToolReviews 2026](https://www.devtoolreviews.com/reviews/cline-vs-roo-code-vs-continue)). Confidence: MEDIUM-HIGH.
- **Original mechanism writeup:** [aider — Building a better repository map with tree-sitter](https://aider.chat/2023/10/22/repomap.html) (foundational, still the design in 2026). Confidence: HIGH.
- **MCP-based structural graphs** (emerging): tree-sitter knowledge graphs exposed over MCP ([arXiv 2603.27277, Codebase-Memory](https://arxiv.org/pdf/2603.27277)); graph-guided localization (*LocAgent*, arXiv 2503.09089). Confidence: MEDIUM (research-stage).

**Mac maturity:** Excellent. aider runs natively, tree-sitter wheels install cleanly on Apple Silicon, points at any local Ollama/MLX endpoint. ctags is a `brew install universal-ctags` away.
**Effort to adopt:** Low–Medium (adopt aider, or wire a repo-map step). **Efficacy/effort: ★★★★☆** (top pick for *automatic* context that doesn't depend on the user curating files).

---

## Lever 4 — Context compression / pruning / "context rot" mitigation

**What it is.** Actively keeping the context window *small and relevant*: summarize old turns, prune stale tool outputs, hierarchical (hot/warm/cold) layering, and avoid the temptation to stuff a giant context.

**Mechanism for efficacy.** "Context rot" is real and **hits small models harder**. Adding tokens *lowers* output quality even on simple tasks; relevant info in the *middle* of a long context degrades accuracy by >30% (lost-in-the-middle, U-shaped attention). So *less context, better placed* = higher quality and trust per attempt. This is counterintuitive but load-bearing: feeding a small model *more* often makes it *worse*.

**Evidence (2026):**
- **Chroma context-rot study**: tested 18 frontier models (incl. Qwen3); **every model degrades as input length grows, even on retrieval/replication**; models in the **7–8B range degrade significantly based purely on where info sits** ([ZenML / Chroma writeup](https://www.zenml.io/llmops-database/context-rot-evaluating-llm-performance-degradation-with-increasing-input-tokens); [Morph: Context Rot](https://www.morphllm.com/context-rot), 2026). Confidence: HIGH.
- **Lost-in-the-middle**: U-shaped accuracy, >30% drop for mid-context info ([Morph, 2026](https://www.morphllm.com/context-rot)). Implication: put the *task and the most relevant code at the START and END* of the prompt. Confidence: HIGH.
- **Coding-specific pruning tools (2026):** *SWE-Pruner* — self-adaptive, goal-driven context pruning for coding agents (arXiv 2601.16746); *Squeez* — task-conditioned tool-output pruning for coding agents (arXiv 2604.04979); *SWE-Pruner* prunes repository code context specifically. Confidence: MEDIUM (research-stage, not yet drop-in tools).
- **Hierarchical pattern (production consensus 2025–26):** hot layer (last ~10 turns verbatim) + compressed warm + external cold store ([AgentMarketCap, 2026-04](https://agentmarketcap.ai/blog/2026/04/11/agent-context-engineering-sliding-windows-memory-2026); [Redis: context rot](https://redis.io/blog/context-rot/)). **Caveat:** do NOT aggressively compress active operational instructions / system prompt — over-summarizing them causes failures. Confidence: HIGH.

**Practical rules for this setup:**
- Prefer a tight repo map + 2–3 targeted files over `@codebase`-everything.
- Put task statement and key code at prompt **start and end**, filler in the middle.
- For long agentic runs, summarize-and-restart rather than letting context balloon (Cline/Continue do sliding-window + summarization; on a 32k–128k local context this matters more, not less).

**Mac maturity:** Tooling-dependent — Cline/Continue do automatic summarization/windowing today; the research pruners are not yet packaged.
**Effort to adopt:** Low (discipline + use a front-end that windows) to Medium (custom pruning). **Efficacy/effort: ★★★★☆.**

---

## Lever 5 — Prompt caching / KV reuse for a stable system prompt

**What it is.** Compute the KV cache for an identical prompt *prefix* (system prompt + conventions + repo map preamble) once, then reuse it across requests so only the new suffix is processed.

**Mechanism for efficacy.** This is primarily a **speed/cost** lever, but it has a real *efficacy* second-order effect: it makes it *cheap to keep a richer, stable preamble* (full role + conventions + few-shot) on every call without paying prefill each time — so you're not tempted to trim the high-value stable context to save time. Stable-prefix discipline = consistent behavior = more trustworthy outputs.

**Evidence / framework maturity on Mac (2026):**
- *Production-Grade Local LLM Inference on Apple Silicon* (arXiv 2511.05502, 2026): comparative study of MLX, MLC-LLM, Ollama, llama.cpp, PyTorch MPS — directly relevant to this hardware. Confidence: HIGH.
- **Ollama**: cross-request prefix/prompt cache with LRU, **session-scoped**, no paging ([jonathanding KV cache notes](https://jonathanding.github.io/llm-learning/en/articles/ollama-kv-cache-scheduling/)). Confidence: MEDIUM-HIGH.
- **MLX**: prompt cache **on disk** + rotating KV with configurable window — strongest "compute system prompt once, reuse later" story on Mac. Confidence: MEDIUM-HIGH.
- **llama.cpp**: sliding-window per-session; **host-memory prompt caching** (`--cache-ram`) lets you compute the system prompt once and hot-swap it ([llama.cpp discussion #20574](https://github.com/ggml-org/llama.cpp/discussions/20574); [Jesse Quinn writeup](https://jessequinn.info/blog/llama-cpp-cache-ram-prompt-caching)). **Watch-out:** `--cache-ram` with some quant types triggers a `GGML_ASSERT` crash. Confidence: MEDIUM.
- **Discipline note:** caching matches from the **start** of the prompt — keep the first ~90% of the prompt byte-identical across calls or you lose the cache. Don't reorder system-prompt sections per-request ([openclaw issue #40256](https://github.com/openclaw/openclaw/issues/40256)). Confidence: HIGH.

**Mac maturity:** Good (MLX best for on-disk reuse; Ollama fine for same-session; llama.cpp most control but rough edges).
**Effort to adopt:** Low if you keep a stable prefix; Medium to wire `--cache-ram`/on-disk cache explicitly. **Efficacy/effort: ★★★☆☆** (speed lever with a modest quality dividend; keep the prefix stable for free).

---

## Lever 6 — Cross-session memory / state

**What it is.** A persistent store (file or DB) of project facts, decisions, and "what we did last time," retrieved at the start of each new session so you don't re-explain.

**Mechanism for efficacy.** Cuts the re-explanation tax across sessions and prevents the model from re-litigating settled decisions → less user effort, fewer regressions, more trust. This is the cross-session sibling of AGENTS.md (which handles *static* conventions; memory handles *evolving* state).

**Evidence / pattern (2026):**
- **Three-tier memory is the 2026 standard**: Tier 1 in-context working memory (lossless), Tier 2 compressed session memory (anchored incremental summarization), Tier 3 external persistent cross-session store extracted *before* compression fires, retrieved at session start ([Medium: Context & Memory Management](https://medium.com/tech-ai-made-easy/context-and-memory-management-sessions-long-term-memory-summarization-pruning-compression-9323bf3068e3), 2026). Confidence: MEDIUM-HIGH.
- **Memory vs compression are distinct**: compression shrinks *this* session's context; memory persists *across* sessions — don't conflate ([mem0.ai](https://mem0.ai/blog/context-compression-vs-memory-in-ai-agents), 2026). Confidence: MEDIUM.
- **Failure mode:** "agents fail not because they forget everything, but because they remember the *wrong* things" — memory drift ([dev.to: Dynamic Context Pruning Guide 2026](https://dev.to/creative_santu/the-2026-guide-to-dynamic-context-pruning-preventing-agentic-memory-drift-1jp9)). Keep memory curated and small, not a growing dump. Confidence: MEDIUM-HIGH.

**Curated approach for a solo Mac dev (low-tech wins):** a hand-curated `NOTES.md` / decisions log injected like AGENTS.md beats a heavyweight vector-memory system for one person — it avoids drift and stays auditable. Reserve mem0/vector memory for when notes genuinely don't scale.

**Mac maturity:** mem0 and similar run locally; the *simple file approach* is fully mature and zero-dependency.
**Effort to adopt:** Low (curated file) to Medium (mem0/vector memory). **Efficacy/effort: ★★★☆☆** (high value, but drift risk and tooling immaturity cap it; the file version is the safe high-ROI form).

---

## Lever 7 — Code-embedding RAG (local embeddings + vector search)

**What it is.** Chunk the codebase (ideally function-aware), embed with a local model, store vectors locally, and retrieve top-k snippets by semantic similarity to feed the model.

**Mechanism for efficacy.** Retrieves *relevant snippets instead of stuffing a giant context* → smaller, more focused prompt → less rot, potentially the right code surfaced. **But for code specifically this is the weakest of the seven levers**, because NL↔code embedding quality is the bottleneck and structural maps (Lever 3) usually outperform it. Best used as a *complement* (hybrid vector + BM25 + structural), not the primary mechanism.

**Why it ranks last for code (not for docs):**
- "General-purpose embeddings miss code structure… use dedicated code search tools for navigating codebases" ([PyImageSearch RAG, 2026-02](https://pyimagesearch.com/2026/02/23/vector-search-using-ollama-for-retrieval-augmented-generation-rag/); [Morph Ollama RAG guide](https://www.morphllm.com/ollama-rag)). Confidence: HIGH.
- Hybrid (vector + BM25 + AST/stack-graph) beats pure vector — e.g. [project-rag](https://github.com/Brainwires/project-rag) uses FastEmbed + LanceDB with hybrid retrieval and an AST RepoMap fallback. Confidence: MEDIUM.

**Local tooling + embedding models (2026):**

| Tool | Role | Mac maturity | Notes |
|------|------|--------------|-------|
| **simonw/llm + `llm-embed` + sqlite-vec** | CLI-first embed + store + KNN in SQLite | Excellent | Simplest local stack; `llm embed-multi` then sqlite-vec KNN. [TIL: sqlite-vec](https://til.simonwillison.net/sqlite/sqlite-vec); [LLM 0.26 tools](https://simonw.substack.com/p/large-language-models-can-run-tools). Confidence: HIGH |
| **sqlite-vec** | Vector search *inside SQLite*, SIMD, runs anywhere | Excellent | Zero-server, file-based, ideal for solo. [asg017/sqlite-vec](https://github.com/asg017/sqlite-vec). Confidence: HIGH |
| **Chroma** | Local vector DB, content-addressed IDs + path metadata | Good | Heavier than sqlite-vec; common in tutorials ([Morph Ollama RAG](https://www.morphllm.com/ollama-rag)). Confidence: MEDIUM-HIGH |
| **LlamaIndex** | Indexing/retrieval orchestration | Good | More framework than you need for one repo. Confidence: MEDIUM |

**Embedding-model choices (run locally on Mac):**

| Model | Why | Confidence |
|-------|-----|-----------|
| **Qwen3-Embedding (0.6B / 4B / 8B)** | #1 MTEB multilingual (8B = 70.58), **fine-tuned for programming languages**, 32K ctx, code-search-capable; 0.6B is the light pick for this box ([Quartalis 2026](https://blog.quartalis.co.uk/embedding-models-comparison-2026/); [Morph Ollama embeddings](https://www.morphllm.com/ollama-embedding-models)) | HIGH |
| **nomic-embed-text** | 768-dim, fast, handles code-related content, ubiquitous in Ollama ([Morph](https://www.morphllm.com/ollama-rag)) | HIGH |
| **BGE-M3** | Strong multilingual retrieval, hybrid dense+sparse | MEDIUM-HIGH |
| **Jina Code Embeddings v2/v5** | Code-specialized; open-weight code embeddings now matching commercial APIs on MTEB ([Quartalis 2026](https://blog.quartalis.co.uk/embedding-models-comparison-2026/)) | MEDIUM |

**Function-aware chunking matters:** respect code boundaries (don't split mid-function) — the single biggest quality knob in code RAG ([Morph Ollama RAG](https://www.morphllm.com/ollama-rag)).

**Mac maturity:** Excellent for the *plumbing* (simonw/llm + sqlite-vec + Ollama embeddings all run natively). The *retrieval quality for code* is the limiter, not the Mac.
**Effort to adopt:** Medium (chunk + embed + wire retrieval). **Efficacy/effort: ★★☆☆☆** for code (use as complement to Lever 3, or primary only for *docs/large* corpora). Note this matches the project's existing pending task #24 (simonw/llm + Qwen3-Embedding-0.6B) — viable, but rank it *below* a repo map.

---

## Cross-cutting synthesis for this solo Mac dev

```
EFFORT  ─────────────────────────────────────────────►  HIGH
  │
  │  ★★★★★  System prompt    ★★★★★ AGENTS.md
  │         (Lever 1)              (Lever 2)
EFFICACY   ★★★★☆ Repo map      ★★★★☆ Compression/anti-rot
  │         (Lever 3)              (Lever 4)
  │                          ★★★☆☆ KV cache   ★★★☆☆ Memory file
  │                                (Lever 5)        (Lever 6)
  │                                          ★★☆☆☆ Code RAG
  ▼                                                (Lever 7)
 LOW
```

**Recommended adoption order (each step compounds):**
1. **Write a strong system prompt** (role + plan-then-edit framing + output contract + 1–2 few-shot). Free, biggest small-model multiplier — and the one your own experiment already proved.
2. **Add an AGENTS.md** per repo (conventions, build/test, constraints). Stops re-explaining.
3. **Adopt aider (or a tree-sitter repo map)** for automatic structural context. Beats both file-dumps and vector RAG for code.
4. **Practice context hygiene**: keep prompts tight, task at start+end, summarize-and-restart on long runs (let Cline/Continue window for you).
5. **Keep a stable prefix** so MLX/Ollama prompt caching kicks in for free (and use MLX on-disk cache if you want it explicit).
6. **Curate a NOTES/decisions file** for cross-session state before reaching for mem0/vector memory.
7. **Add local embedding RAG only if** docs or a large corpus genuinely exceed what a repo map covers — and prefer hybrid (vector + BM25 + structural), function-aware chunking, Qwen3-Embedding-0.6B or nomic-embed-text via simonw/llm + sqlite-vec.

**The single highest-leverage insight:** for a *fixed* small model, **smaller-but-righter context > bigger context**. Levers 1–4 all serve that. Cline shipping a compact prompt system "at 10% the length, designed specifically for local models" to make Qwen3-Coder-30B usable ([cline.bot/blog/local-models](https://cline.bot/blog/local-models), 2026) is the same thesis in production form.

---

## Confidence & caveats

- HIGH-confidence claims rest on multiple 2026 sources or on-point empirical papers (system-prompt study, context-rot study, aider repo-map design).
- Research-stage tools (SWE-Pruner, Squeez, MCP knowledge graphs) are flagged MEDIUM — directionally validated, not yet drop-in.
- Embedding-model leaderboard numbers (MTEB 70.58 for Qwen3-8B) are vendor/blog-reported; treat exact figures as indicative.
- Security: AGENTS.md and any repo-sourced injected context is an attack surface — low risk for own repos, real for cloned third-party ones.
