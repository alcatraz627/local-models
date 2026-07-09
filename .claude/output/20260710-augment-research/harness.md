# Augmenting the harness — ranked tool findings

Research date: 2026-07-10. Scope: tools that extend a heavily-customized Claude
Code setup (hooks on every lifecycle event, custom skills, MCP file/input/browser
tools, persistent memory, WAL/checkpointing, cross-session IPC, launchd-scheduled
agents, a local Ollama tier, a gemini side-lane) — not replacements for any of
that, additions to it.

Ranked by fit to this specific setup, not general popularity. "Effort" is rough
adoption cost, not runtime cost.

---

## 1. Agent Safehouse — macOS kernel sandbox wrapper

**What it is:** a single shell script that wraps any agent CLI (`safehouse claude
...`) in a deny-first `sandbox-exec` policy — the agent gets zero filesystem/network
access except what you explicitly grant.
**Why it fits:** this setup runs Claude Code with heavy autonomy (launchd-scheduled
sessions, desktop automation, `--dangerously-skip-permissions`-adjacent workflows)
with no OS-level backstop today — the only protections are hooks, which run in the
same process and can be bypassed by a bug in the hook itself. Safehouse adds a
second, kernel-enforced layer underneath the hooks, not instead of them.
**Maturity/effort:** young (first release ~May 2026) but simple — `brew install
eugene1g/safehouse/agent-safehouse` or a single downloaded script, no daemon, no
rebuild of existing tooling. Low effort, test on one scheduled job first.
**Source:** https://github.com/eugene1g/agent-safehouse

## 2. CodeGraph — local-first code knowledge graph MCP server

**What it is:** an MCP server that pre-indexes a repo into a SQLite-backed
call/import/symbol graph and serves structural queries ("what calls this",
"what does this file depend on") instead of making the agent grep-and-read its
way there.
**Why it fits:** matches the local-first, no-cloud-egress posture already
established by the `lm` suite — no embeddings API, no code leaves the machine.
Independent benchmarks in the search results show 58–70% fewer tool calls on
large-codebase navigation tasks, which is exactly the kind of thing that currently
burns tool-call budget in long sessions.
**Maturity/effort:** MIT license, 47k+ GitHub stars, one-command index + MCP
config entry. Medium effort (index the repo once, wire into `.mcp.json`).
**Source:** https://github.com/colbymchenry/codegraph

## 3. Serena — LSP-powered semantic code retrieval/editing MCP

**What it is:** launches real language servers (the same ones VS Code uses) and
exposes go-to-definition, symbol search, and refactor-grade edits over MCP —
symbol-level understanding, not text search.
**Why it fits:** complements CodeGraph rather than duplicating it — CodeGraph
answers "what's connected to what" (structure), Serena answers "show me this
exact symbol's definition/references correctly" (precision), across 40+
languages via real LSPs. Worth running both if the codebase mix is large and
polyglot; CodeGraph alone if it's one or two languages.
**Maturity/effort:** MIT, open source, `pip`/`uvx` install. Medium effort — needs
a working language server per language used.
**Source:** https://github.com/oraios/serena

## 4. ast-grep MCP — structural (AST-based) code search

**What it is:** search/rewrite tool that matches on the abstract syntax tree
instead of text — `verifySession($ARG)` returns real call sites, not comment or
string-literal false positives.
**Why it fits:** `rg` (already mandated in this setup) is fast but text-only;
ast-grep is the structural complement for refactor-scale queries ("find every
call to this function regardless of argument formatting") where ripgrep produces
noise. Small, sits alongside existing search tooling without replacing it.
**Maturity/effort:** mature, actively maintained, ships an MCP server directly.
Low effort — CLI install + one MCP entry.
**Source:** https://ast-grep.github.io/blog/ast-grep-agent.html

## 5. Claude Code native OpenTelemetry

**What it is:** built-in instrumentation — spans per model request and tool
execution, token/cost metrics, structured log events for prompts and tool
results — that ships in Claude Code itself, off by default.
**Why it fits:** this setup already hand-rolls dispatch telemetry
(`~/.claude/logs/model-dispatch.jsonl`) for the model-tier-routing rule; native
OTel is the same idea done by the vendor, at finer grain (per-tool-call spans,
not just per-dispatch), and it's zero new dependency — just a collector to point
it at.
**Maturity/effort:** shipped, documented, off by default. Medium effort — the
instrumentation is free, but you need somewhere to send it (local otel-collector,
or a hosted sink like #6 below).
**Source:** https://code.claude.com/docs/en/agent-sdk/observability

## 6. Braintrust `trace-claude-code` plugin

**What it is:** a Claude Code plugin that auto-captures every session as
hierarchical traces (LLM calls, tool usage, timing) in Braintrust's hosted UI,
with a companion plugin that lets Claude query those traces back from the
terminal.
**Why it fits:** the "just works" version of #5 — no collector to run, traces
are queryable within minutes of `BRAINTRUST_API_KEY` being set. Tension worth
naming: it's a hosted SaaS sink, which cuts against the local-first posture
elsewhere in this setup — reasonable as an opt-in debugging tool, not as the
default telemetry path.
**Maturity/effort:** production plugin, low effort (env var + setup script). SaaS
account + API key required.
**Source:** https://github.com/braintrustdata/braintrust-claude-plugin

## 7. Apple `container` CLI 1.0 — VM-per-container isolation

**What it is:** Apple's official Swift tool (shipped stable 1.0 in June 2026)
that boots a genuinely separate lightweight VM (own kernel, via
Virtualization.framework) per container on Apple Silicon — not a shared-kernel
container like Docker.
**Why it fits:** a heavier complement to Safehouse (#1). Safehouse restricts
what the *harness process* can touch on the host; `container` gives a real
kernel boundary for running agent-*generated* code you don't trust at all
(a script the agent just wrote and wants to execute) — the two solve adjacent
but different problems.
**Maturity/effort:** stable as of June 2026, requires macOS 26, no Docker-socket
compatibility (Compose/devcontainers won't work against it). Medium effort.
**Source:** https://github.com/apple/container

## 8. Claude Squad — worktree-based multi-agent TUI

**What it is:** a Go terminal app that runs multiple agent CLI instances in
parallel, each in its own git worktree + tmux pane, with a dashboard showing
what every agent is touching.
**Why it fits:** complements native Agent Teams (already in use — this very
research task is running as an Agent Teams teammate) for the specific case of
wanting a persistent visual multi-pane view across isolated worktrees, rather
than in-conversation teammate messaging. Different interaction model, same
underlying git-worktree isolation pattern already familiar from this setup's
scheduling/IPC habits.
**Maturity/effort:** actively maintained, single install script. Low-medium
effort — worth a trial run before making it a habit, to avoid duplicating what
Agent Teams already does well.
**Source:** https://github.com/smtg-ai/claude-squad

## 9. Context7 — version-pinned live documentation MCP

**What it is:** an MCP server that fetches current, version-specific library
docs at query time and injects them into context, instead of the model
answering from stale training data.
**Why it fits:** cheapest, most broadly-cited high-leverage addition across every
source consulted — directly reduces hallucinated API usage on any library work,
with no architectural overlap with anything already in this setup.
**Maturity/effort:** mature, widely adopted, `npm`-installable MCP server. Low
effort. API key recommended for higher rate limits but not required.
**Source:** https://github.com/upstash/context7

## 10. Firecrawl MCP — structured web scrape/crawl/extract

**What it is:** MCP server exposing scrape, crawl, map, and structured-extract
tools — full-page and multi-page data retrieval, not just search-and-summarize.
**Why it fits:** the built-in WebSearch/WebFetch tools (used for this very
research) summarize a page through a small model; Firecrawl is the complement
for tasks that need the actual structured content of a page or a whole site
crawl (e.g., pulling a full API reference or scraping a doc site the agent needs
to reason over directly, not just a summary of it).
**Maturity/effort:** production-grade, well documented. Low effort, but external
API key + per-call cost — position as an occasional-use tool, not a default.
**Source:** https://github.com/firecrawl/firecrawl-mcp-server

## 11. semgrep — pattern-based static analysis CLI

**What it is:** multi-language static analysis that finds bug variants and
security patterns via rule-based structural matching, independent of any LLM
judgment.
**Why it fits:** this setup already has `/code-review` and `/security-review`
skills that are LLM-judgment-only; semgrep is a deterministic pass that could
slot in as a pre-check before the LLM review runs, catching the class of bug
that pattern-matching finds faster and more reliably than reasoning does.
**Maturity/effort:** mature, huge rule registry, CLI-first (no MCP server
strictly needed — can be shelled out to from a skill or hook). Medium effort to
wire into an existing skill.
**Source:** https://github.com/semgrep/semgrep

## 12. Repomix — whole-repo context packer

**What it is:** packs an entire repository into a single AI-friendly file, with
tree-sitter compression cutting token count by roughly 70% while preserving
structure.
**Why it fits:** most useful for the `lm gemini` large-context ingestion lane
already defined in this setup's model-tier routing — Repomix is the packing step
that makes "dump the whole repo into gemini's huge context window" actually
practical instead of a hand-rolled `find | cat` script.
**Maturity/effort:** category leader (26k+ stars, large install base), mature
CLI. Low effort.
**Source:** https://github.com/yamadashy/repomix

## 13. agent-seatbelt (CJHwong) — seatbelt sandbox with PII hooks

**What it is:** an alternative macOS Seatbelt wrapper (same underlying mechanism
as Safehouse, #1) that adds content-level PII detection hooks specifically
targeting Claude Code and Codex.
**Why it fits:** worth evaluating against Safehouse rather than adopting both —
this one leans into hook-level composability (PII scanning at the content layer),
which pairs naturally with a setup that already has PreToolUse/PostToolUse hooks
on everything. Pick this over Safehouse specifically if the PII-hook angle is the
priority; pick Safehouse if simplicity and Homebrew installability matter more.
**Maturity/effort:** young, smaller project than Safehouse. Low effort to trial.
**Source:** https://github.com/CJHwong/agent-seatbelt

---

## Skip these, here's why

**GitNexus** (the other breakout code-graph tool, 28k+ stars) — technically
excellent (deepest Claude Code integration of anything reviewed: 16 MCP tools +
skills + hooks) but published under the PolyForm Noncommercial License. The
user's email domain indicates paid/professional work; a noncommercial license on
core tooling is a landmine that surfaces later as a compliance problem, not a
technical one. CodeGraph (#2 above) covers the same use case under MIT with no
such restriction — take that instead.

**mem0 MCP** (hosted or self-hosted) — this setup already runs a deliberately
layered memory system: per-project memory files with typed frontmatter
(user/feedback/project/reference), a global tier, WAL for what-happened, and
`atone`/`affirm` for graduated patterns — each with an explicit write bar and a
single source of truth. Bolting on a second memory system with its own
auto-extraction heuristics (mem0 captures "at session start, context compaction,
task completion, session end") creates two independently-mutating memory stores
that will drift out of sync — the exact class of problem the account's own
externally-mutated-state caution exists to prevent, just applied to memory
instead of a status cache.

**Cloud-VM multi-agent platforms** (Claude Code Web, GitHub Copilot Coding
Agent, Jules, Codex Web) — these solve "assign a task, close the laptop, get a
PR back," which is a real capability, but this setup has already built local
equivalents tuned to the machine: launchd-scheduled agents with Calendar
companions, cross-session IPC (`claude-ipc`), and Agent Teams for in-session
parallelism. Moving orchestration to a vendor's cloud VM trades away the
hook/memory/WAL infrastructure already invested in, in exchange for a walled
garden with less control over exactly the lifecycle events this setup hooks
into. Revisit only if a specific task genuinely needs "runs for hours,
unattended, machine can be off" — none of the above local tooling covers that
one case.
