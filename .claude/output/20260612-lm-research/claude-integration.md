# Research: hobby-grade enhancement + Claude Code integration for local-models

<!-- sessions: lm-research@2026-06-12 -->

Online research grounded against `docs/STATE.md` + `docs/GOALS.md` (read 2026-06-12).
Constraints applied as hard filters: no resident services beyond the existing ollama
LaunchAgent, no idle cost, bash-wrapper altitude, anti-over-engineering, llm-mini fold-in
deliberately deferred.

---

## 1. Claude Code ↔ local model integration patterns (2025–2026)

### The three shapes in the wild

**Shape A — MCP delegation servers ("Claude orchestrates, local model grunts").**
Many small projects expose Ollama as MCP tools so Claude Code can delegate summarize /
classify / extract / draft:

- [claude-sidekick](https://github.com/andrewbrereton/claude-sidekick) — "delegate simple tasks to save tokens"
- [OllamaClaude](https://github.com/Jadael/OllamaClaude) — claims up to 98.75% token reduction with file-aware tools
- [mcp-local-llm](https://github.com/aplaceforallmystuff/mcp-local-llm) — 6 tools (`local_summarize`, `local_draft`, `local_classify`, `local_extract`, `local_transform`, `local_complete`)
- [pal-mcp-server](https://github.com/BeehiveInnovations/pal-mcp-server) — multi-provider routing incl. Ollama
- [Ollama-Claude marketplace listing](https://mcpmarket.com/server/ollama-claude), [Composio toolkit](https://composio.dev/toolkits/ollama/framework/claude-code)

**Honest adoption read:** these are all tiny (mcp-local-llm: 6 stars, 10 commits). The
load-bearing lesson, stated explicitly in mcp-local-llm's own docs: **the MCP server is
not enough — you must put routing instructions in CLAUDE.md** ("teach Claude when to
delegate through explicit guidance rather than hoping it discovers the tools"). Without a
routing table, Claude just does the task itself — it's faster and better at it from its
own perspective, so the tool sits idle. This is the abandonment mode for Shape A.

**Shape B — hook/CLI-time deterministic calls (no orchestrator choice involved).**
This is what actually sticks, because there's no compliance problem: a hook or git step
*always* calls the local model for a bounded mechanical output.

- [Model-routing architecture writeup (dev.to/thebrierfox)](https://dev.to/thebrierfox/claude-code-is-burning-your-api-budget-the-model-routing-architecture-that-fixes-it-4bjl) — Tier 0 = local qwen2.5:7b for classification/routing/summarization/extraction, Tier 1 = Haiku for structured outputs, Sonnet/Opus above. Reported ~95% API-spend reduction on background classification cycles (84 heartbeats: 51.5k → 6k tokens). Caveats from the author: enforcement is manual (CLAUDE.md table, agents can ignore it), context handoff loses information, "the classifier itself must be cheap or savings evaporate."
- [model-matchmaker](https://github.com/coyvalyss1/model-matchmaker) — local hook that routes prompts to the right model tier.
- [Claude Code hooks reference (2026)](https://thepromptshelf.dev/blog/claude-code-hooks-complete-reference-2026/) — hooks as the deterministic surface.
- [Most of your Claude Code agents don't need Sonnet (dev.to)](https://dev.to/edwardkubiak/most-of-your-claude-code-agents-dont-need-sonnet-4587) — fallback_models pattern: local first, escalate to Haiku on validation failure. This is exactly the llm-mini architecture the user already owns.

**Shape C — full replacement (`ANTHROPIC_BASE_URL` → Ollama).**
Heavily blogged, mostly demo-grade:

- [Ollama official Claude Code integration](https://docs.ollama.com/integrations/claude-code), [Ollama blog: Anthropic API compat](https://ollama.com/blog/claude) (Ollama ≥0.14 speaks `/v1/messages` natively)
- [paddo.dev: Running Claude Code fully local](https://paddo.dev/blog/claude-code-local-ollama/) — documents a real gotcha: Claude Code's per-request attribution header **invalidates the local KV cache**, forcing re-processing of the ~20k-token system prompt every turn; fix is `CLAUDE_CODE_ATTRIBUTION_HEADER: "0"`.
- [Per-subagent provider routing is NOT supported](https://github.com/anthropics/claude-code/issues/38698) — open feature request; `ANTHROPIC_BASE_URL` is session-wide, so you cannot run "Opus orchestrator + local subagents" in one session today.
- Setup guides: [stationx](https://app.stationx.net/articles/claude-code-ollama), [gist with all backends](https://gist.github.com/renezander030/39249215616a095d74fe6c66b0348641)

**Used vs abandoned, summarized:**

| Shape | Reality |
|---|---|
| B: hooks/git/CLI deterministic calls | **Sticks.** Bounded task, no orchestrator compliance needed, latency tolerable |
| A: MCP delegation | Works only with explicit CLAUDE.md routing tables; otherwise idle. Marginal adoption |
| C: full local Claude Code | Novelty. Quality gap on multi-step agentic work; KV-cache + speed pain on consumer hardware; gets demoed, then dropped |

**Implication for this stack:** the deferred llm-mini fold-in is the *right* shape (B with
an MCP face) — and the research adds one missing piece: when activating it, the work is
~20% plumbing and ~80% writing the CLAUDE.md routing-table entry that tells Claude *when*
to call it. Don't adopt a third-party delegation MCP; you already have a better one with
a Haiku fallback.

---

## 2. Hobby-grade quality-of-life (filtered: no resident services, no idle cost)

### Passes the filter

- **Raycast + Ollama** — [official local-model support since v1.99](https://www.raycast.com/changelog/macos/1-99-0); the community [raycast-ollama extension](https://www.raycast.com/massimiliano_pasquini/raycast-ollama) is the mature one ([setup guide](https://localllmsetup.com/blog/raycast-ollama-mac-integration), [XDA experience report](https://www.xda-developers.com/combining-raycast-with-local-llm-best-productivity-change-i-made/)). Highlight text anywhere → hotkey → summarize/rewrite/translate via the local API. Raycast is something many users already run; the extension is a pure API client of the existing server — **zero added idle**, honors the existing KEEP_ALIVE=0 policy (each call loads/unloads unless `warm on`). Best non-terminal surface available for this stack.
- **Shell buffer integration** — zsh widgets that send the current buffer to Ollama on a keybind: [kollzsh-style plugin (Medium)](https://medium.com/@krugergui/using-llm-suggestions-locally-in-the-terminal-with-ollama-eed267317e52), [LLM Shell Ctrl+B helper](https://app.readytensor.ai/publications/llm-shell-mi7D28yZiwtd), [autocomplete.sh (HN)](https://news.ycombinator.com/item?id=41139049). **You don't need any of these projects** — a ~10-line ZLE widget that pipes the buffer to `q cmd` and replaces it gets the same effect at the right altitude.
- **Hold-key local dictation** — [local-whisper](https://github.com/luisalima/local-whisper) (whisper.cpp, hold key → speak → text at cursor, fully local) and [Yapper](https://github.com/ahmedlhanafy/yapper) (local STT + optional Ollama cleanup). Model loads on keypress; effectively no idle cost. Genuine hobby-fun; also pairs with `imagine` prompt entry. [MacWhisper + Ollama variant](https://deverman.org/using-macwhisper-for-dictation-with-ollama-for-local-mac-dictation/).
- **Clipboard as input** — no tool needed: `pbpaste | q "summarize"` — blocked today only because `q` rejects stdin. See recommendation #1.

### Fails the filter (rejected, with reasons)

- **Open WebUI as resident GUI** — the standard hobby move ([makeuseof](https://www.makeuseof.com/local-llm-felt-unfinished-until-put-proper-interface-in-front-of-it/), [tersesystems home-LLM writeup](https://tersesystems.com/blog/2025/02/05/running-llms-at-home/)) but it's a resident Python/Docker service = idle cost. If a GUI itch ever appears, run it **on demand** (`uvx open-webui serve`, kill after) — do not LaunchAgent it. Verdict: skip; `q history`/`q show` already covers the recall use case.
- **Tailscale serve for phone access** — well-documented ([Tailscale official blog](https://tailscale.com/blog/self-host-a-local-ai-stack), [KDnuggets guide](https://www.kdnuggets.com/accessing-local-llms-remotely-using-tailscale-a-step-by-step-guide), [laurentsv.com](https://laurentsv.com/blog/2025/03/25/ollama-tailscale-openwebui.html)) but it presupposes Open WebUI (resident, see above) AND tailscaled (another resident daemon if not already running). Only revisit if Tailscale gets installed for other reasons; even then it's a "neat once" feature, not a habit.
- **Continue.dev / editor-resident assistants** — indexing daemons + always-on extension; wrong altitude for this stack ([continue.dev + Ollama case study](https://www.johal.in/continue-dev-vscode-extension-python-ollama-local-models-codebase-embeddings-2025/)). Cloud Claude Code already owns the editor-agent role.
- **Ollama→llama.cpp migration for perf** — recurring HN theme ([the ecosystem doesn't need Ollama](https://news.ycombinator.com/item?id=47788385), [XDA: easiest to start, worst to keep](https://www.xda-developers.com/ollama-easiest-way-start-local-llms-worst-keep-running/)). Real but irrelevant at hobby grade: the gap is tok/s percentage points; the self-hosted LaunchAgent + policy env already extracts the value that matters (flash-attn, q8 KV, lifecycle control). Re-platforming would burn the project's main asset (a working, audited setup) for marginal gain. Skip.

---

## 3. What makes hobby LLM tooling stick vs rot

Sources: [Ask HN: are you running local LLMs? (2025)](https://news.ycombinator.com/item?id=44837130), [XDA: 5 months of daily local LLMs](https://www.xda-developers.com/running-local-llms-for-five-months-broke-every-assumption-i-had-about-them/), [XDA: local LLMs are actually good now](https://www.xda-developers.com/local-llms-are-good-now-wasted-months-not-realizing-it/), Shape A/B/C evidence above.

**What sticks (observed across retrospectives):**
1. **Tasks where local has a structural advantage** — privacy (documents you won't hand to a cloud), $0 marginal cost on high-volume mechanical calls, offline. "Novelty gets people in; privacy keeps them" (XDA). Cloud-parity general chat is abandoned fastest — the cloud model is simply better and the local one becomes a worse ChatGPT.
2. **Sub-second invocation from an existing habit surface** — terminal command, git hook, system hotkey. The Ask HN thread's abandonments are friction stories: GUI frontends dropped for being "slow with random crashes" (Alpaca), LM Studio's hard 2–3 min API timeout. Every survivor is invoked from where the user already is.
3. **Bounded, verifiable outputs** — commit message, one command, a title, a classification. Failures are cheap and visible.

**What rots:**
1. **Model churn as the hobby** — XDA's strongest finding: an early phase where benchmarking/comparing models becomes the activity itself, "the gap between decent models is much smaller than the time spent chasing improvements." (This stack's `prompt > model` lesson independently reached the same conclusion — that's validation, keep it.)
2. **Anything with per-use setup friction** (activate venv, open a GUI, start a service).
3. **Index/state that goes stale** — RAG/embedding setups rot when the index needs manual refresh; users stop trusting results, then stop using the tool.
4. **Delegation that depends on an orchestrator's goodwill** (Shape A above).

**Read against this stack:** the existing design already embodies the stickiness findings
(bare PATH commands, sub-second warm path, no daemons, prompt-over-model). The growth
moves are therefore about **adding habit surfaces** (stdin/pipes, git hook, Raycast
hotkey, Claude Code hook) — not new capabilities. The biggest stickiness risk identified:
`q` rejecting stdin walls it off from pipes, clipboard, and agents — the three cheapest
habit surfaces.

---

## 4. Proven local-offload candidates (and where local disappoints)

### Proven good

| Subtask | Evidence | Fit here |
|---|---|---|
| **Commit messages from staged diff** | Purpose-built [tavernari/git-commit-message](https://ollama.com/tavernari/git-commit-message) (8B, 40+ tok/s on Apple Silicon, 4B mini variant exists); [aicommit2](https://github.com/tak-bro/aicommit2) (multi-backend incl. Ollama); [ollama-commit](https://github.com/clianor/ollama-commit); weekend-build writeups ([1](https://dev.to/himanshu231204/how-i-built-an-ai-powered-git-commit-tool-using-ollama-in-a-weekend-3okj), [2](https://dev.to/himanshu231204/i-built-a-cli-tool-that-writes-git-commit-messages-using-local-ai-ollama-1p52)) | Strong — `git diff --staged \| q commit`; gemma4-e4b likely sufficient (prompt > model); 4B mini variant of the dedicated model is the fallback if not |
| **Titles / classification / routing** | Tier-0 routing writeup (95% spend cut on classification cycles, above); mcp-local-llm `local_classify`; bounded outputs are the canonical small-model task | Already built (`q title`) — the gap is wiring, e.g. into the user's existing Claude Code tab-title hook |
| **Bounded summarization** (a diff, a log chunk, one doc — NOT a codebase) | mcp-local-llm `local_summarize`; meeting-notes pipelines ([whisper + Ollama summaries](https://dev.to/zackriya/local-meeting-notes-with-whisper-transcription-ollama-summaries-gemma3n-llama-mistral--2i3n)) | Good once `q` accepts stdin |
| **Embeddings / semantic code grep** | [grepai](https://github.com/yoanbernabeu/grepai) — 100% local, Ollama embeddings, semantic search + call graphs, built for AI agents; [Show HN: semantic grep with local embeddings](https://news.ycombinator.com/item?id=45157223); [Ollama embeddings docs](https://docs.ollama.com/capabilities/embeddings). Reject [mgrep](https://github.com/mixedbread-ai/mgrep) — uploads chunks to Mixedbread's cloud store | Conditional — works, but index staleness is the documented rot vector (§3); use on-demand reindex, never a watcher daemon |
| **Draft-then-verify (local drafts, Claude reviews)** | mcp-local-llm's whole philosophy; OllamaClaude's token-reduction claims | **Partially hype.** Works for prose/boilerplate volume; for code, the routing author's own caveat applies — context handoff loses information, and Claude re-reading/fixing a mediocre local draft can cost more than writing it fresh. Only adopt for genuinely mechanical volume (docstrings, test scaffolds, log triage) |

### Where local models disappoint (documented, not vibes)

- **Long-context degradation** — performance drops sharply as context grows and as the relevant span shrinks: [Lost in the Haystack](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12478432/); [coding agents as long-context processors (arXiv)](https://arxiv.org/html/2603.20432v1).
- **Multi-step agent loops** — small models hold 3–4 step chains, then lose coherence on tasks requiring an updated mental model of codebase state ([haimaker ranking](https://haimaker.ai/blog/best-ollama-models-for-coding-agents/), [agentic programming survey, arXiv](https://arxiv.org/pdf/2508.11126)).
- **Build-graph / cross-system dependency understanding** — Ask HN, verbatim: "doesn't do a great job of understanding the build graph, nor dependency relationships between the host system's libraries."
- **Anything cloud-parity** — general reasoning/chat; this stack's non-goals section already says so.

The existing `q` non-goal boundary ("deliberately shallow; real reasoning goes to cloud
Claude") matches the evidence exactly. No change needed to the division of labor.

---

## Ranked recommendations for THIS stack

Value/effort-ranked. **[flag]** = change to an existing command; **[glue]** = wiring two
things you already own; **[new]** = new component.

| # | Recommendation | Kind | Effort | Why / honesty note |
|---|---|---|---|---|
| 1 | **`q` stdin support** (`[ -t 0 ] \|\| QUERY="$QUERY\n\n$(cat)"`) — already flagged in GOALS.md as cheap | [flag] | S | The single highest-leverage change: unlocks pipes, `pbpaste \| q`, git hooks, AND Claude-hook calls. Every other text recommendation depends on it. The "real pull" the audit was waiting for is this list |
| 2 | **`q commit` intent** — system prompt for conventional-commit drafting over `git diff --staged` via stdin; optionally a `prepare-commit-msg` hook in chosen repos | [flag] | S | Best-proven offload category in the wild (§4). Try gemma4-e4b + good prompt first per the project's own lesson; `tavernari/git-commit-message:mini` (4B) only if it loses the A/B |
| 3 | **Wire `q title` into Claude Code surfaces** — tab-title focus/base strings, session naming, via the user's existing `~/.claude/scripts/tab-title` + hook infra | [glue] | S | Shape B (the shape that sticks): deterministic hook call, bounded output, zero compliance problem. First real Claude→local integration with no new component |
| 4 | **`imagine` agent-usability fixes** (`--no-open` / TTY gate; already audit item #4) | [flag] | S | Prereq for any agent ever calling `imagine`; trivially cheap |
| 5 | **Raycast Ollama extension** pointed at the existing server | [new, 3rd-party] | S | Only worthwhile *new* QoL surface found: system-wide highlight→hotkey, zero idle, pure API client of the server you already govern. Skip if Raycast isn't already in use — don't install a launcher for this |
| 6 | **zsh ZLE widget → `q cmd`** (Ctrl-key: send buffer, replace with command) | [glue] | S | ~10 lines in .zshrc; beats installing kollzsh/llm-shell. A daily-touch habit surface |
| 7 | **Activate the llm-mini fold-in** when ready for Claude-delegation proper — llm-mini's MCP face backed by this stack's server, plus a CLAUDE.md routing-table entry (local: classify/title/summarize-bounded/draft-boilerplate; Haiku: structured-output fallback; Sonnet+: everything else) | [glue] | M | The research's main verdict on the deferred decision: the architecture is right and now evidence-backed; the missing 80% is the routing instructions, not plumbing. Do NOT adopt claude-sidekick/OllamaClaude — strictly worse than what's owned |
| 8 | **Semantic grep, on-demand** — trial grepai (local Ollama embeddings) on one repo; reindex manually/per-session, never a watcher | [new] | M | Real but conditional: index staleness is the documented rot vector. Pilot before committing; drop without guilt if reindex friction kills it |
| 9 | **Hold-key local dictation** (local-whisper or Yapper) | [new] | M | Hobby-fun, fully local, no idle. Pure want-based — zero workflow necessity |
| — | **Skip: Open WebUI (resident), Tailscale phone access, `ANTHROPIC_BASE_URL` full-local Claude Code, Continue.dev, llama.cpp re-platforming** | — | — | Each fails a hard constraint or is documented novelty-churn; reasons in §2/§1 |

### One-line strategic summary

The stack's design already matches what survives in the field; the gap is **habit
surfaces, not capabilities** — open `q` to stdin, then attach it to git, the shell
buffer, and Claude Code's deterministic hook points, and activate the llm-mini fold-in
as the delegation face when that wiring proves itself.
