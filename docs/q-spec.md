# `q` — quick local LLM companion (spec)

A one-line command for fast, direct answers from a local model — the thing you reach for instead of
opening ChatGPT for a quick question or a shell command. It trades depth for speed and zero-friction:
sub-second when warm, no clarifying questions, macOS-aware by default. For anything needing real
reasoning or code generation, use full Claude — `q` is deliberately shallow.

- **Source:** `~/Code/local-models/bin/q` · **On PATH:** `~/.local/bin/q` (exec-wrapper)
- **Backend:** the local-models Ollama server (`127.0.0.1:11434`, LaunchAgent-managed)
- **Config:** `~/Code/local-models/config.sh` (`WARM_MODEL`, keep-alive)

## Invocation surface

```
q "<prompt>"              ask intent (default)
q <intent> "<prompt>"     intent = cmd | ask | title | commit
q on | off | status       Tier W warm toggle (delegates to `warm`)
q history [N]             recent queries, numbered (default 15)
q show N                  entry N in full (prompt + response + metadata)
q -h | --help             help (per conventions/cli-help-design.md)
cmd | q "<instruction>"   piped stdin becomes input context (default 16k chars, --max-ctx)
git diff | q commit       commit message from the piped diff
```

### Intents

| Intent | System prompt shape | Output |
|---|---|---|
| `ask` (default) | direct, ≤2 sentences, no preamble | short prose |
| `cmd` | macOS/BSD command assistant; ONE command only | a single shell command |
| `title` | 2-5 word Title Case summary | a bare title |
| `commit` | commit-message writer; imperative subject <72 chars, why-over-what | a bare commit message |

### Flags

| Flag | Effect | Default |
|---|---|---|
| `--think` | show the reasoning trace (dimmed, on stderr) | off |
| `-c`, `--continue [N]` | continue the last exchange (or entry N): replays the chain as prior messages, adopts its model/intent unless overridden | off |
| `-m`, `--model M` | override the model for this call | `$WARM_MODEL` (gemma4-e4b-warm) |
| `--raw` | no system prompt (bare model) | off |
| `-h`, `--help` | show help | — |

## Behavior contract (the smart defaults)

1. **macOS / Apple Silicon is the permanent default.** Never hedges across OSes. Switches to Linux
   idioms *only* when the prompt explicitly names a "linux server" or "container".
2. **Thinking off by default.** Set via the Ollama `think:false` API flag — prompt-level "no thinking"
   does NOT disable it (verified). `--think` re-enables.
3. **Never asks clarifying questions.** Assumes the most likely intent and answers. A bad guess costs
   one more word, not a round-trip.
4. **Streams output** token-by-token (perceived latency ≈ first-token time).
5. **Warm-aware `keep_alive`.** If the target model is already resident (`warm on`), a `q` call keeps
   it resident (`keep_alive=-1`); otherwise it loads for the one call and unloads (`keep_alive=0`),
   never silently un-pinning your warm model.
6. **Deterministic.** `temperature: 0` (greedy decoding) — the same prompt yields the same answer,
   so a wrong answer is reproducible and fixable via the prompt, not random.
7. **Pipe-friendly stdin.** Non-TTY stdin is appended as input context below the instruction
   (`git log | q "summarize"`, `git diff | q commit`), truncated at `--max-ctx` chars (default
   16000) to respect the warm model's 8k-token window. The answer on stdout stays bare;
   `--think` traces go to stderr.
8. **Friendly server-down failure.** If the ollama server is unreachable, `q` prints a one-line
   hint (with the `launchctl kickstart` command) instead of a Python traceback.

## History

Every query is appended to `logs/q-history.jsonl` (best-effort; a log failure never breaks the
answer): `{ts, cid, intent, model, think, prompt, response, ms}`. `cid` is the conversation
chain id — fresh queries get their own `ts`, `-c` continuations inherit the target's, and
`q -c [N]` replays all same-cid entries as context (last 8 exchanges, ~18k char budget).
List recent with `q history [N]` (numbered by stable entry number = JSONL line; multiline
prompts are flattened to keep display numbers == line numbers); open any entry in full with
`q show N`; `q history --json [N]` emits raw JSONL for machine consumers.

## Models

| Model | Role |
|---|---|
| `gemma4-e4b-warm` | default; Tier W companion (num_ctx 8192, QAT 4-bit) |
| `qwen2.5-coder:3b` | alternate for `cmd` via `-m` |
| `gemma4:26b` / `:31b` | heavier, on-demand via `-m` |

## Design rationale (load-bearing decisions)

- **Prompt > model for small local models.** A 4B model + a BSD-aware terse system prompt beat a
  code-specialized model + a generic prompt. The value is the wrapper, not the weights.
- **The accuracy ceiling is macOS-vs-Linux, not size.** Small models default to Linux idioms
  (`ps --sort`, `/proc`); the `cmd` system prompt names macOS/BSD idioms explicitly.
- **`q` owns lifecycle per-request, not the server.** Server lifecycle is the LaunchAgent's job; the
  warm/unload decision is per-call `keep_alive`. `q` never starts/stops the server.

## Conventions adherence

- `conventions/cli-help-design.md` — help is colored (bold-yellow sections, cyan commands, green
  flags, dim descriptions), TTY/`NO_COLOR`/`TERM=dumb` aware, ≤60 lines, examples-first.
- On-PATH via exec-wrapper (symlink-safe), per `scripts/README.md` "consider a symlink under
  `~/.local/bin/`".
- Answer output is plain text → pipe-friendly (`q cmd "..." | pbcopy`). Styling is help-only.

## Non-goals / out of scope

- Reasoning, multi-step analysis, code generation → use full Claude.
- Clarifying dialogue → by design, never.
- Web search (`--web`) → deferred (off-by-default, needs a search-backend decision).
- MCP / Claude-calls-local → deferred to the future "Claude offloads to local" capability.

## API (machine modes — `api_version: 1`)

For GUI hosts and scripts (first consumer: better-file-browser's native-messaging host).
Stdout carries only the protocol; diagnostics go to stderr; no ANSI ever in these modes.

```
lm status --json                  state probe: ~30ms typical / ≤~250ms worst (two 120ms-capped
                                  curls); first call after server idle can spike once. exit 0
                                  whenever JSON was produced
  → {api_version, server, host, default_model, warm, resident_models[],
     available_models[], latency_class, toolkit_version}
q --json [flags] [intent] ["q"]   one JSON object: {ok:true, text, model, ms, truncated}
q --stream-json …                 NDJSON: {"t":"chunk","text"} … {"t":"done",model,ms,truncated}
```

Warmth is **read-only** for machine consumers: `lm status --json` reports `warm` /
`latency_class` so a GUI can set expectations ("first reply will take a moment"), but
residency is toggled only by the human (`warm on|off`). There is deliberately no
programmatic warm-up endpoint. `warm`/`latency_class` describe **`default_model` only** —
a client overriding with `-m` should judge its model against `resident_models` itself.

Context flags: `--ctx -` (stdin) / `--ctx FILE` · `--ctx-name S` (framing hint, defaults to the
file's basename) · `--max-ctx N` (truncate, default 16000 chars; reported via `truncated`) ·
`--timeout S` · `--intent X`. Hard cap: 400k chars → `ctx_too_large` (refuses rather than
summarizing 4% of a document).

Error contract (branch on `code` + exit, never on message text):

| code | exit | meaning |
|---|---|---|
| `invalid_args` / `no_such_entry` | 2 | empty query in machine mode, non-numeric `--max-ctx`/`--timeout`, bad `-c N` |
| `server_down` | 10 | unreachable pre-flight or died mid-request |
| `model_missing` | 11 | HTTP 404 from the server for the model |
| `ctx_too_large` / `ctx_unreadable` | 12 | document over hard cap / file missing |
| `timeout` | 13 | `--timeout` wall clock exceeded |
| `cancelled` | 130 | SIGTERM/SIGINT — a bash `trap` covers the pre-exec phase, then q execs python whose handler takes over; the dropped connection stops Ollama generating |

Document-grounded intents (prompt-craft lives HERE, never in clients): `summarize`,
`explain-code` (flags rm/curl-pipe-sh/sudo/cred access), `describe-data`, `qa` (document-only
ground truth). q never prompts interactively in any mode, so no confirmation flow exists to break.

## Integrations

- **Tab-title auto-base** — `~/.claude/scripts/tab-title/hooks/auto-base.sh` (UserPromptSubmit,
  async, fire-and-forget) titles a session from its first prompt via `q title`. Warm-gated: only
  fires when the warm model is already resident, so it never cold-loads for a nicety; a manually
  set base always wins.
- Shared helpers live in `bin/_lib.sh` (colors, help renderers, jsonl history, `ollama_up`,
  `ollama_resident`) — sourced by q/imagine/lm.
