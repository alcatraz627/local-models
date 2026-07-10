# Claude Code Usage Audit → Local-Model Offload Map

**Window:** last 3 days (2026-06-17 → 2026-06-20)
**Method:** sampled `~/.claude/projects/**/*.jsonl`. Per session: project slug + first human message (intent). Tool-use counted from `assistant` turns' `tool_use` blocks (subagents included). Bash commands classified by verb. Estimates flagged; raw counts are exact.

---

## 1. Scale of activity (measured)

| Metric | Value |
|---|---|
| Top-level sessions (non-subagent) | 26 |
| Total transcript lines | 67,072 |
| Assistant turns (incl. subagents) | 23,794 |
| Total `tool_use` calls | 12,646 |
| Input tokens (incl. cache read/create) | ~8.53 B |
| Output tokens | ~31.3 M |

The 8.5B input figure is dominated by **cache reads** (Claude Code re-feeds the rolling context each turn) — it is a context-pressure signal, not 8.5B of unique prompt. Output tokens (~31M) are the truer "work produced" measure. This is a heavy 3-day run: 6 of the projects are real coding/research efforts, the rest are short config/Q&A sessions.

### Tool-use distribution (12,646 calls)

```
  Bash          4098   32.4%   ████████████████
  Edit          2989   23.6%   ███████████
  Read          2685   21.2%   ██████████
  TaskUpdate     729    5.8%   ███   (todo plumbing, not "work")
  Write          596    4.7%   ██
  TaskCreate     457    3.6%   ██   (todo plumbing)
  Agent          297    2.3%   █    (sub-agent fan-out)
  WebSearch      279    2.2%   █
  WebFetch       147    1.2%
  StructuredOutput 90   0.7%
  ToolSearch      85    0.7%
  AskUserQuestion 55    0.4%
  Skill           39    0.3%
  github MCP      47    0.4%
  playwright MCP  ~28    0.2%
```

**Bash + Edit + Read = 77% of all tool calls** — this is a code-editing-heavy 3 days, not a chat-heavy one. Task* calls (1,186 combined, ~9%) are todo-list bookkeeping, not substantive work.

### Bash command shape (4,101 calls)

| Category | Count | Share | Notes |
|---|---|---|---|
| compound `cd <dir> && <cmd>` | 2,016 | 49% | wrapper around a real verb (edit/inspect/script) — understates the categories below |
| inspect/lookup (`ls cat rg wc find stat head`) | 742 | 18% | pure read-only file/grep recon |
| test/build (`pytest npm run tsc swift build`) | 309 | 8% | |
| fileops (`mkdir cp mv trash chmod`) | 192 | 5% | |
| script/transform (`python jq node sed awk`) | 103 | 3% | |
| git | 75 | 2% | low — user commits manually |
| http/curl (localhost probes) | 37 | 1% | |
| `claude-ipc` / svc / misc | ~600 | — | cross-session messaging, statusline, schedule helpers |

The true inspect/lookup share is **higher than 18%** because ~half of those are buried inside the `cd … && rg/ls/cat` compounds. Read-only recon (grep, list, cat, stat) is one of the single largest real activities.

---

## 2. Sessions & intents (the actual work)

| Project | Lines | Tool tot | Character | First human intent (paraphrased) |
|---|---|---|---|---|
| **Versable-enhancement-product** | 22,554 (2 sess) | 5,033 | multi-file feature + docs | "review notes on phase 1 docs — split technical doc out of product/jobs/create-*; re-scope S3/SES access control for prototype/reference/customer/cache data" |
| **--claude** (gcc config) | 14,022 (6 sess) | 2,423 | tooling, hooks, research | "fix guard-anthropic-credentials noise + malformed terminal output"; "add a `download` CLI command"; "review gcc personas for efficacy"; "scan 48h of transcripts for Anthropic API errors, diagnose"; "fable-eulogy: audit how fable behaved vs opus" |
| **sys-monitor** (Swift) | 10,759 (1 sess) | 1,454 | debugging + perf/UX | "/catchup — it's not working. Independent audit blueprint of how it works now + perf/UX improvements" |
| **Versable-two-enhancement-product** | 7,869 (5 sess) | 1,654 | scoped code edits | "Excel template column auto-sizing rules for human reading"; "which API key is gemini picking up?"; "fzf set up, profiler running — check perf" |
| **better-file-browser** (Chrome ext) | 5,845 (1 sess) | 860 | feature + bugfix | "/catchup — add features, rich-render .sh/.tsv/.jsonl; fix crumb dropdown XHR error in devtools" |
| **local-models** | 4,489 (2 sess) | 1,047 | research & synthesis | "audit the `lm` command setup"; "best candidates to replace Opus for pair coding? deepseek r1 vs frontier?"; "my use case is heavier go-implement-this-feature-across-files" |
| Versable-landing-app | 754 (2 sess) | 85 | small Q&A/edit | "base64 image in mdx → extract"; "mdx frontmatter tag validation for a Next.js blog" |
| Claude-i-dream | 600 (1 sess) | 84 | scripted run + review | "run i-dream weekly review, walk me through proposals, apply approved" |

Per-project tool mix confirms the split: **local-models** alone holds 230/279 WebSearch + 110/147 WebFetch (it's the research session); **Versable-enh / sys-monitor / better-file-browser** are Bash/Edit/Read/Write dominated (the coding sessions).

---

## 3. Task-types → local-model tier map

Shares are % of the 3-day *substantive* activity (excludes Task* bookkeeping), estimated from tool mix + intent reading. Flagged as estimates.

```
TASK TYPE                          SHARE   BEST LOCAL TIER       VERDICT
────────────────────────────────────────────────────────────────────────
Read-only recon / lookups          ~22%    lean → moderate       OFFLOAD
Multi-file feature coding          ~28%    beefy (cloud today)   STAY (mostly)
Scoped single-file edits           ~14%    moderate              OFFLOAD (review)
Research & synthesis (web)         ~12%    task-dedicated+beefy  HYBRID
Debugging                          ~10%    beefy / cloud         STAY
Config & doc edits / drafting       ~8%    lean → moderate       OFFLOAD
Shell-command composition           ~3%    lean                  OFFLOAD now
Git ops / commit msgs               ~2%    lean                  OFFLOAD now
Planning / scoping / judgment       ~1%*   cloud                 STAY
```
\* Planning is a *small share of tool calls* but disproportionately high-value — it gates everything else. Tool-call share understates its importance.

---

### 3a. Read-only recon / lookups — ~22% — **lean → moderate — OFFLOAD**

The single biggest offloadable chunk. 742 explicit `ls/cat/rg/wc/find/stat` calls plus roughly that many again buried in `cd … && rg …` compounds. Examples:
- Versable-enh: repeated `rg` over backend for symbol/usage location before an edit.
- better-file-browser: `cat`/`stat` on devtools error context paths.
- sys-monitor: `ls` + reading `_checkpoint.claude.md`, `Package.swift`.

**Tier:** A **lean** model (gemma-e4b ≤8B) handles "where is X / what does this file contain / compose the grep." When the lookup needs to *reason over* the result (e.g. "which of these 6 call sites is the writer"), bump to **moderate**.
**Why it's safe:** read-only, no mutation, cheap to re-run if the answer is wrong. This is exactly the `q` / file-Q&A surface already built in local-models.

### 3b. Multi-file feature coding — ~28% — **beefy (cloud today) — STAY, mostly**

The largest *value* bucket. 2,989 Edits + 596 Writes, concentrated in Versable-enh (1,466 Edits), sys-monitor (554), better-file-browser (268). Examples:
- Versable-enh: split a combined product+technical doc, re-architect S3 access-control modelling across data classes (prototype/reference/customer/cache) — touches many files, requires holding cross-file invariants.
- better-file-browser: add rich-rendering for `.sh/.tsv/.jsonl` AND fix the crumb-dropdown XHR bug in the same session — coupled change across content.js + renderers.

**Tier:** **beefy** (Qwen3-Coder-Next 80B+) is the aspirational home, but on an M-series 64GB box it's currently slower and lower-efficacy than cloud for *trustworthy* multi-file edits. This is the bucket that matches the user's stated use case ("heavier go-implement-this-feature-across-files, similar to how I use claude code"). **Stays on cloud Claude until local beefy efficacy is proven** — see local-models Task #19 (honest local-coder vs Opus-4.8 comparison).

### 3c. Scoped single-file edits — ~14% — **moderate — OFFLOAD with review**

The clean win between recon and multi-file. Examples:
- Versable-two: "Excel `write_data_to_excel_template` column auto-sizing by min-char threshold" — one function, well-specified.
- Versable-landing: extract a base64 image from one mdx file; add mdx frontmatter tag validation.
- Versable-two: "which API key is gemini picking up?" — trace one file, no edit.

**Tier:** **moderate** (Qwen3.6-35B-A3B / gemma-26B) drafts the edit; user (or cloud) reviews the diff. The single-file scope caps the blast radius, making local review affordable.

### 3d. Research & synthesis (web) — ~12% — **task-dedicated + beefy — HYBRID**

Almost entirely the local-models sessions: 279 WebSearch + 147 WebFetch + 297 Agent fan-outs. Examples:
- "best local candidates to replace Opus for pair coding"; τ-bench / BFCL / Terminal-Bench score gathering; HF-tag verification.

**Tier:** split it.
- **task-dedicated (embedder for RAG/search):** the *retrieval* half — "find the relevant benchmark numbers across these sources" — is a recurring job an **embedding specialist** (e.g. a local embedder feeding a small RAG index over fetched pages) does well and cheaply.
- **beefy / cloud:** the *synthesis + adversarial verification* half (cross-source ranking, calling out a model that doesn't exist) still wants a strong reasoner. Cloud Claude or a local beefy model.

### 3e. Debugging — ~10% — **beefy / cloud — STAY**

Examples: sys-monitor "it's not working, audit how it works now" (Swift, opaque runtime); better-file-browser crumb-dropdown XHR error; the gcc "scan 48h transcripts, diagnose the API-error spike" investigation. These need root-cause reasoning across runtime state + code + logs — the `[root-cause]` discipline. **Stays cloud** until local beefy is trusted; a **moderate** model can assist with the *narrow* "explain this stack trace / this function" sub-step.

### 3f. Config & doc edits / drafting — ~8% — **lean → moderate — OFFLOAD**

Examples: the `download` CLI command spec; doc restructuring prose in Versable-enh; gcc persona prompt rewrites; mdx frontmatter conventions. Drafting + summarization is **moderate**'s sweet spot; short config tweaks and titles are **lean**.

### 3g. Shell-command composition — ~3% — **lean — OFFLOAD NOW**

Composing the `rg`/`find`/`jq` invocation (distinct from running it). 103 script/transform + much of the grep-building. **lean** does this sub-second today — this is the lowest-risk, highest-frequency immediate win.

### 3h. Git ops / commit messages — ~2% — **lean — OFFLOAD NOW**

Only 75 git calls (user commits manually), but commit-message drafting and `status`/`diff` summarization is textbook **lean**. Trivial, safe, already a documented lean use-case.

### 3i. Planning / scoping / judgment — ~1% of calls, high value — **STAY (cloud)**

Low tool-call count, disproportionate leverage. Examples: the S3-access-control re-scope decision (dev/staging/prod × cache/user/enhancement/reference data); "split technical doc out or keep inline?"; the i-dream proposal walk-through-and-approve loop; the fable-vs-opus behavioral audit. **Must stay on cloud Claude** — these are the trust-critical, multi-constraint judgment calls where a wrong answer is expensive and hard to detect.

---

## 4. What MUST stay on cloud Claude (the hard line)

1. **Multi-file feature implementation with cross-file invariants** (3b) — the S3 access-control re-architecture, the better-file-browser coupled feature+fix. Local beefy is the *aspiration* (matches the user's stated primary use), not yet the *trust floor*.
2. **Root-cause debugging over opaque runtime** (3e) — Swift menu-bar "it's not working," the API-error-spike diagnosis. Needs reasoning across logs + code + state.
3. **Planning / scoping / judgment** (3i) — data-classification scoping, doc-architecture decisions, approve/reject loops. Wrong-and-confident here is the worst failure mode.
4. **Adversarial synthesis** — the verification half of research (3d): catching a hallucinated model id, ranking conflicting benchmark sources.

Everything in §3a, 3c, 3f, 3g, 3h (recon, scoped edits, drafting, shell-compose, git msgs) — roughly **45–50% of substantive activity by volume** — is offloadable to lean/moderate **today** with a review gate. The high-value 28% multi-file bucket is the prize that waits on local-beefy efficacy (Task #19).

---

## 5. Honest caveats

- Shares are **estimates** from tool-mix + intent reading, not a labeled per-call ground truth. The ±5pp uncertainty is real; the *ordering* (recon and multi-file edits are the two biggest buckets) is robust.
- The `cd <dir> && <cmd>` compounds (49% of Bash) mean inspect/edit/script are each undercounted in the flat Bash classification; the per-project tool mix corrects for this.
- Subagent tool calls are folded into the totals — the 297 Agent + much Bash/Read in local-models/fable-eulogy is fan-out research, which inflates "research" tool volume relative to wall-clock user time.
- Token totals include cache reads (8.5B input is context re-feed, not unique work). Output tokens (~31M) are the better effort proxy.
