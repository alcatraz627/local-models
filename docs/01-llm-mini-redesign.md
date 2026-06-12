# llm-mini Interface Redesign — Plan

**Status:** ON HOLD — decided 2026-06-09 NOT to fold into llm-mini now. `q` already delivers the
"quick, useful, easy" need; llm-mini's unique value (cloud fallback, MCP/hook callability) serves the
*future* "Claude offloads to local" capability, not the current need. This doc is the reference for
IF/WHEN we revisit. Only action taken now: neutralize llm-mini's idle-watchdog (`config set
idle_timeout_min=0`) so it can't `pkill` our LaunchAgent server.
· **Date:** 2026-06-09
**Target:** `~/.claude/scripts/llm-mini/` (GLOBAL — inside the `~/.claude` repo, all sessions use it)
**Why now:** Slice 2 built `q` (intents, `think:false`, macOS smart defaults, warm-aware lifecycle).
This folds those lessons into llm-mini as the production home — and resolves a live conflict
between llm-mini's server management and our LaunchAgent-managed server.

---

## 1. Current interface (grounded)

**Surfaces** (one core dispatcher, `llm-mini-core.sh`):
- CLI: `llm-mini <prompt> | <template> [input] | pipe`; flags below.
- MCP: `mcp__llm-mini__ask` (global).
- Hook: `mini_quick(prompt, template)` — local-only, 3s timeout, 100 tokens (`hook.sh:14-24`).
- Chat: `llm-mini chat [--tools|--local|--cloud]` (separate REPL).

**Backends:** local Ollama `/api/generate`, flat prompt, `llama3.2`, temp 0, `stream:false`
(`core.sh:295-324`) · cloud Haiku via API or `claude -p` (`core.sh:326-382`) · `auto` = local→cloud
fallback (`core.sh:533-546`).

**Flags:** `--quality --local --json --max-tokens --template --context --timing --verbose --list -h`
(`core.sh:413-428`).
**Subcommands:** `engine chat history config templates help` (`core.sh:399-408`).
**Templates:** cmd-compose, doc-lookup, session-title, summarize (`{{input}}` sub, `core.sh:490-496`).
**Config:** `~/.claude/llm-mini.conf` (9 keys). **Engine:** Ollama lifecycle + idle-watchdog.

---

## 2. KEEP (works, don't touch)

- **Multi-surface single-core architecture** (CLI/MCP/hook/chat → one dispatcher). Excellent.
- **Local→cloud (Haiku) fallback** — resilience `q` does NOT have. This is llm-mini's killer feature; keep.
- **Template system** (`{{input}}`, `mini-prompts/`) — reuse; intents build on this.
- **Pipe/stdin capture, file auto-detect, `--context`** (`core.sh:388-462`) — good ergonomics.
- **Config file, history log, `--timing`, temp 0** — keep.

## 3. CHANGE (behavior / defaults)

| What | From | To | Why |
|---|---|---|---|
| Local request path | `/api/generate` flat | **`/api/chat`** (system+user) | enables system prompts / intents / smart defaults |
| Default local model | `llama3.2` | **`gemma4-e4b-warm`** (interactive) | better quality; aligns with Tier W |
| Thinking trace | (n/a for llama3.2) | **`think:false`** by default | gemma4 reasons by default; prompt-text "no think" doesn't stop it |
| Default system prompt | none | **macOS/Apple-Silicon + no-clarify** | the validated `q` smart defaults |
| `keep_alive` | none (server default) | **warm-aware** (-1 if resident, else 0) | don't un-pin the warm model |

## 4. RETOOL (under the hood)

- **Stop managing the server (MUST).** Remove `nohup ollama serve` (`engine.sh:173`), the
  idle-watchdog `pkill` (`engine.sh:121`), and `engine stop`'s `pkill` (`engine.sh:228`). The server
  is now owned by the LaunchAgent `com.alcatraz.local-models-ollama`; llm-mini must assume it's up.
  - `engine start/stop/switch/idle-watchdog` → **deprecate** (warn + delegate). Model warm/unload is
    the `warm` toggle's job; `engine status` → report the LaunchAgent server (read-only).
- **Request layer → `/api/chat`** with `{system, user, think, keep_alive, options}`. Single helper
  used by all surfaces.
- **Intents as system prompts** (see Add) layered over the existing template mechanism — reconcile
  "template" (user-prompt scaffold) vs "intent" (system role). Templates stay; intents are new.

## 5. ADD (new)

- **Intents:** `cmd` (single macOS command) / `ask` (≤2 sentences) / `raw` — from `q`. Selectable
  via subcommand or `--intent`.
- **`--think`** — opt back into the reasoning trace (off by default).
- **`warm on|off|status`** subcommand — surface the Tier W toggle through llm-mini.
- **Streaming** (`--stream`, default for interactive TTY; off when piped).
- **`--web`** — opt-in one-shot web search (Task 6), off by default.
- **(Maybe) per-intent model:** `cmd` could default to a sharper model; A/B showed prompt > model,
  so likely NOT needed — revisit only if accuracy demands.

## 6. HELP DOCS to update

- `show_help()` (`core.sh:97-199`) — new defaults, intents, `--think`, `warm`, `--web`; rewrite the
  ENGINE section (no longer lifecycle-managing); update BACKENDS/CONFIG.
- `~/.claude/features/llm-mini.md` — the Tier-2 feature doc (model, surfaces, engine semantics).
- Config defaults (`core.sh:227-238`, `llm-mini.conf`) — default_model, new keys.

---

## 7. The core decision: how do `q` and llm-mini relate?

- **A — Absorb `q` into llm-mini (recommended).** llm-mini-core gains intents/think/system-prompt/
  warm-aware/streaming; `q` becomes a thin alias (`q` = `llm-mini cmd` default) or is retired. One
  companion, globally. `q` gains cloud fallback + templates + MCP/hook; llm-mini gains snappiness.
- **B — Shared core, two front-ends.** Extract the request logic into a shared lib both call. More
  moving parts, more surface to maintain.
- **C — Keep separate.** llm-mini just gets the warm model + the engine-lifecycle fix; `q` stays the
  project's fast path. Least global change, but two divergent tools.

## 8. Risks / must-handle

- **Hook latency (mini_quick, 3s budget).** Switching the default to `gemma4-e4b-warm` (5.6GB) means
  a cold load can blow the 3s budget → session-title etc. fall back to empty. **Mitigation:** keep a
  tiny fast model (e.g. `llama3.2` or `gemma4:e2b`) for the hook/`mini_quick` path, OR require warm-on
  for hooks. **This is a decision (Q2).**
- **Global blast radius.** Every session uses llm-mini. Change is in the `~/.claude` repo → needs a
  `/migrate` entry (request-path + lifecycle + default-model change) and the COMMIT.md secret-scan on
  commit. Roll out behind config defaults so behavior is reversible.
- **temperature:** keep 0 for `cmd`; `ask` may want a small temp. Minor.

## 9. Open decisions (need user input)

- **Q1 — q↔llm-mini relationship:** A (absorb) / B (shared core) / C (keep separate).
- **Q2 — hook/default-model strategy:** tiny-fast-model for hooks + gemma4-e4b for interactive, vs
  one model everywhere (and accept the hook latency tradeoff).
- **Q3 — scope/sequencing:** do the global llm-mini rewrite now (with migration + commit ritual), or
  prototype the merged design in the project first, then graduate to `~/.claude`?

## 10. Proposed build order (after decisions)

1. Engine-lifecycle fix (stop the `pkill` conflict) — isolated, low-risk, fixes a live bug.
2. `/api/chat` request layer + `think:false` + warm-aware keep_alive.
3. Intents + macOS smart-default system prompts (port from `q`).
4. `warm` subcommand + per-surface model strategy (hook vs interactive).
5. Help docs + feature doc + config defaults.
6. `--web` (Task 6) + `--stream`.
7. Migration entry + COMMIT.md secret-scan + commit.
