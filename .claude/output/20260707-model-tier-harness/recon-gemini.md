# Gemini CLI recon — 2026-07-07

Read-only inventory of the `gemini` CLI setup on this machine, done for the
model-tier harness planning work (task #18 in the local-models project).

## 1. Entrypoint and version

- Binary: `/opt/homebrew/bin/gemini` (on PATH)
- Version: `0.43.0`
- Installed via Homebrew formula `gemini-cli` (`brew install gemini-cli`),
  installed on-request, depends on `node`.
- **The formula is deprecated.** `brew info gemini-cli` states: *"Deprecated
  because it is not supported upstream! It will be disabled on
  2026-12-18."* Replacement path Homebrew points at:
  `brew install --cask antigravity-cli`.
- Installed version (0.43.0) is already behind stable (0.46.0) — the bottle
  hasn't been upgraded since install.
- No `npm`/`npx` global install, no pip/pipx install — Homebrew is the sole
  install path.

## 2. Config / auth surface

All state lives under `~/.gemini/`:

| Path | Contents |
|---|---|
| `~/.gemini/settings.json` | `{"security":{"auth":{"selectedType":"oauth-personal"}}}` — auth mode only, no model override |
| `~/.gemini/config/config.json` | `{"userSettings":{"remoteControlHostname":"aakarshs-m5-pro-local-deep-eclipse","themeMode":"THEME_MODE_INHERIT"}}` |
| `~/.gemini/google_accounts.json` | `{"active":"aakarsh@versable.ai","old":[]}` — signed in with the Versable work Google account, not a personal one |
| `~/.gemini/oauth_creds.json` | mode 600, contains `access_token`/`refresh_token`/`id_token`/`scope`/`expiry_date` (values not read) |
| `~/.gemini/projects.json` | two prior workspaces registered: `fastfetch-explorer`, `enhancement-product` (Versable) |
| `~/.gemini/history/` | per-project subdirs for those same two projects |
| `~/.gemini/config/mcp_config.json` | empty (0 bytes) |
| `~/.gemini/config/plugins/` | `android-cli-plugin`, `chrome-devtools-plugin`, `modern-web-guidance-plugin` — bundled plugins, not user-added |

**Model default:** no explicit model override anywhere in `settings.json`,
`config.json`, shell rc files (`~/.zshrc`/`.zprofile`/`.zshenv`), or the
process environment (`GEMINI_MODEL`/`GOOGLE_API_KEY`/`GEMINI_API_KEY` all
absent). Whatever "gemini-3.5-flash" default the user set up on 2026-07-06 is
**not persisted in config** — it's either the CLI's built-in default or was
passed per-invocation via `-m/--model` and never saved. I did not invoke
`gemini` live to check the runtime default, to avoid burning API quota or
tripping an interactive first-run flow during a read-only recon pass. Flag
this as **unconfirmed** rather than verified.

- `gemini mcp list` → "No MCP servers configured." (empty, confirms the 0-byte config file)
- `gemini gemma status` → Gemma local-model routing (LiteRT-LM) is present as
  a subcommand but **not set up** — binary not installed, model not
  downloaded, server not running, not enabled in settings. This is an
  on-device small-model routing feature bundled in the CLI, currently dormant.

## 3. Usage history — none found

- `~/.zsh_history` (2903 lines): **zero** mentions of `gemini` or `antigravity`
  in any casing.
- `bash ~/.claude/scripts/shell-mem.sh` has no `search` subcommand (its actual
  subcommands are hook-callback-shaped: `shell-log-search`,
  `shell-log-tail`, etc.) — didn't chase further since zsh_history already
  gave a clean negative.
- Searched all `~/.claude/projects/**/*.jsonl` transcripts for
  `gemini-3.5-flash|gemini `. The only hit inside the `local-models` project
  is this current recon task's own transcript (circular — it's this task
  writing the word "gemini"). A handful of hits in unrelated Versable
  transcripts (`versable-builder`, `enhancement-product`) turned out to be
  plain-English mentions of "Gemini" as a competitor LLM name in prose, not
  CLI invocations — no command-line usage, no friction notes.
- **Conclusion: the `gemini` CLI has never actually been driven from this
  machine's shell or from a Claude Code session.** The `~/.gemini/projects.json`
  / `~/.gemini/history/` entries for `fastfetch-explorer` and
  `enhancement-product` show it *has* been opened in those two directories
  (likely by the user directly, interactively), but there's no trace of what
  was asked or how it went.

## 4. Capabilities relevant to pairing (from `gemini --help`)

- **Modes:** interactive (default) or headless via `-p/--prompt` (appends to
  stdin if piped) or `-i/--prompt-interactive` (one-shot prompt, then drops
  into interactive).
- **Sessions:** `-r/--resume [latest|N]`, `--session-file <path>`,
  `--session-id <uuid>`, `--list-sessions`, `--delete-session <N>` — full
  session persistence/resume support, scoped per-project (confirms the
  `~/.gemini/history/<project>/` layout above).
- **Output formats:** `-o/--output-format {text,json,stream-json}` — JSON and
  streaming-JSON output are both supported, relevant for programmatic/agent
  piping.
- **Approval / autonomy modes:** `--approval-mode {default,auto_edit,yolo,plan}`,
  plus a standalone `-y/--yolo` flag and a policy-engine (`--policy`,
  `--admin-policy`, `--allowed-mcp-server-names`). `--allowed-tools` is
  flagged deprecated in favor of the policy engine.
- **Workspace scoping:** `--include-directories` (comma-separated or repeated)
  to widen the workspace beyond CWD; `-w/--worktree` to launch inside a new
  git worktree; `--skip-trust` to bypass the workspace-trust prompt.
- **ACP mode:** `--acp` (Agent Client Protocol) — positions it as embeddable
  in another agent/editor rather than only a standalone terminal tool.
- **Extensibility:** `gemini extensions`, `gemini skills`, `gemini hooks`,
  `gemini mcp` subcommands — extension/skill/hook/MCP management all exist as
  first-class CLI surfaces (parallel to Claude Code's own skills/hooks/MCP).
- **File attachment / context window:** not stated in `--help` text directly
  (no `--file`/`--attach` flag visible); presumably files are referenced via
  `@path` syntax inside the prompt the way Gemini CLI historically works, or
  via `--include-directories`. Context window size is not surfaced by the CLI
  itself — would need the web docs or a live query to confirm, and I did not
  fetch the web per the read-only/no-network-research scope of this task.

## 5. A second, related surface: Antigravity

`~/.gemini/` also contains two directories that are **not** part of the
`gemini` CLI proper — they belong to **Antigravity**, Google's separate
agentic IDE product, which is installed as a full GUI app:
`/Applications/Antigravity.app`.

- `~/.gemini/antigravity/` — small state dir (`antigravity_state.pbtxt`,
  `brain/`, `builtin/`, `conversations/`, `knowledge/`), last touched 6 Jul.
- `~/.gemini/antigravity-cli/` — much more active: `history.jsonl` (43
  entries, most recent 7 Jul 01:43), per-day `cli-YYYYMMDD_HHMMSS.log` files,
  `conversation_summaries.db`, `cache/`, `conversations/`. This looks like the
  CLI-side companion process/state for the Antigravity app, **not** a
  separately invokable `antigravity` shell command — `command -v antigravity`
  found nothing on PATH, and it's not a Homebrew cask
  (`brew list --cask` has no antigravity entry). The bundled binaries under
  `~/.gemini/antigravity-cli/bin/` (`agentapi`, `webm_encoder`) look like
  internal helpers the app shells out to, not a user-facing CLI.
- Homebrew's own deprecation notice for `gemini-cli` (see §1) points at
  `antigravity-cli` as the intended replacement, so Google appears to be
  consolidating the standalone `gemini` CLI into the Antigravity product line.
  Worth knowing before investing integration work in the `gemini` binary
  specifically — it has a stated end-of-life on 2026-12-18 (~5.5 months out).

## 6. Existing gcc integration

`rg -l "gemini" ~/.claude/rules ~/.claude/features ~/.claude/scripts` returned
**nothing**. No rule, feature doc, or script anywhere in `~/.claude/`
currently references gemini. This is a clean slate — any pairing/harness
integration work would be greenfield, not touching or conflicting with
existing infrastructure.

## Summary abstract

- `gemini` CLI: Homebrew `gemini-cli` v0.43.0 at `/opt/homebrew/bin/gemini`,
  **deprecated formula, EOL 2026-12-18**, Homebrew's suggested replacement is
  `antigravity-cli`.
- Auth: OAuth-personal, signed in as `aakarsh@versable.ai` (work account, not
  personal); no model default persisted anywhere in config, env, or shell rc —
  the "gemini-3.5-flash" default is unconfirmed locally, flag as such.
- **Never actually invoked** from this machine's shell or from any Claude Code
  session — `~/.zsh_history` and all `~/.claude/projects` transcripts are
  clean; only prior touch is `~/.gemini/projects.json` showing it was opened
  interactively in two other repos at some point, with no record of what
  happened.
- Capabilities worth designing around: headless `-p` mode with stdin
  piping, JSON/stream-JSON output, session resume (`--resume latest`),
  `--approval-mode`/`--yolo` autonomy levers, and an ACP mode for embedding —
  all good building blocks for a pairing/harness integration.
- A second, more-actively-used surface shares the same `~/.gemini/` directory:
  **Antigravity** (`/Applications/Antigravity.app`), Google's separate agentic
  IDE, whose CLI-side companion (`~/.gemini/antigravity-cli/`) has real usage
  history (43 entries, last active same day) — worth distinguishing from the
  standalone `gemini` binary before building integration, since Homebrew's own
  deprecation notice is steering toward Antigravity as the long-term surface.
- No existing gcc rule/feature/script references gemini anywhere — this is
  greenfield integration work with no prior conventions to conform to.
