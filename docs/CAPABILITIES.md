# CAPABILITIES — everything the lm suite can do

The full menu. Every ability, grouped by category, with real examples — read this when you're
wondering "can the local suite do X?". Everything runs on this machine; nothing leaves it.
Current state and architecture live in `STATE.md`; this file is the *what can I order* card.

All commands are on PATH (`q`, `see`, `review`, `imagine`, `warm`, `lm …`) and every one has
`-h` help. The suite is zero-idle: nothing stays in RAM unless you pin it (see § Residency).

---

## 1 · Ask & answer — `q`

The quick local LLM. Deterministic (temp 0), thinking off, sub-second when the warm companion
is pinned. Intents are one-word verbs from `intents/*.toml`.

```bash
q "why is the sky blue"                        # plain ask (warm small model)
q cmd "free up port 3001"                      # → one runnable macOS command
q title "$(cat draft.md)"                      # short title for anything
git diff | q commit                            # commit message from the piped diff
q summarize --file report.pdf                  # local PDF → summary (poppler extract, no cloud)
q explain-code --ctx bin/lm-serve              # walk a script
q describe-data --ctx data.csv                 # what's in this file
q qa --ctx contract.md "who signs off?"        # grounded Q&A over a document
q intents                                      # list every registered verb
```

Size tiers and control:

```bash
q --big "reason through this tradeoff"         # gemma4:26b — heavier reasoning/prose
q -m code "refactor this loop" --ctx f.py      # qwen3.6:35b-a3b — the coding tier
q -m llama3.2 "..."                            # any literal ollama model passes through
q -c "and shorter?"                            # continue the last exchange (or: q -c 214)
q --think "hard puzzle"                        # reasoning trace on (streams dim to stderr)
q --raw "no system prompt at all"              # blank-slate call
q --max-ctx 60000 --file big.md summarize      # widen the context truncation cap
q --timeout 120 --big "long job"               # wall-clock cap, structured timeout error
```

History (numbered, stable line numbers, `-1` = latest):

```bash
q history            # last 15, numbered
q show 214           # one full exchange
q show -1            # the latest
```

## 2 · Machine modes — q as an agent's worker

Stable JSON contracts (`docs/q-spec.md` §API, `api_version: 1`). Errors are structured codes
with fixed exit numbers — branch on `code`, never on message text.

```bash
q --json --ctx - qa "who signs off?" < doc.md              # one JSON object
# → {ok:true, text, model, ms, tokens_in, tokens_out, truncated}
q --stream-json "..."                                      # NDJSON: chunk / done / error frames
q --json --format schema.json "list 3 risks" --ctx plan.md # constrained decoding: output IS
# schema-valid JSON; envelope gains .data (pre-parsed) — Ollama format-field enforcement
```

## 3 · Vision — `see`

A local VLM reads images/screenshots into text. Structural read by default; grounded answer
when you ask one. Text is good-but-verify (don't trust exact strings blindly).

```bash
see ~/Desktop/shot.png                          # verbatim text + UI + layout + anomalies
see chart.png "is the trend up or down?"        # grounded answer
see mockup.png --json                           # {ok,text,model,ms} for an agent
see photo.png --glow                            # rendered read
see ui.png -m gemma4:26b                        # the stronger general-scene reasoner
see history · see show -1                       # every read is logged, replayable
```

## 4 · Code review — `review`

The `review` intent on the code tier (probe-gated qwen3.6). First-pass reviewer, not a Claude
replacement.

```bash
review                                          # your uncommitted changes (git diff)
review --staged                                 # staged only
review 214                                      # a GitHub PR by number (gh pr diff)
review 214 --full                               # + FULL changed files at the PR head via API —
                                                #   nothing is checked out, no tree is touched
review 214 --repo owner/name                    # a PR in another repo
review-pr 214                                   # packaged full-PR review
review src/server/ bin/deploy.sh                # folders (gitignore-aware walk) + files
cat snippet.ts | review                         # piped code
review --findings 214                           # schema-constrained: .data.findings =
                                                #   [{file, line, severity, finding, suggestion}]
review --glow                                   # human-pretty render
review history · review show -1                 # reviews live in q-history
```

## 5 · Image generation — `imagine`

mflux (MLX Flux/Qwen) on the GPU. Models auto-download to the HF cache on first use.

```bash
imagine "a cozy reading nook, rainy window"     # default: qwen (best text rendering)
imagine --enhance "neon ramen bar"              # local prompt-engineer pass first
imagine -m schnell "quick draft"                # fast model; -m dev / flux2 / any HF repo
imagine --style watercolor --neg "text, logos" "koi pond"
imagine --from sketch.png "same but at dusk"    # image-to-image
imagine refine 12 "warmer light"                # iterate on generation #12
imagine vary 12 · imagine redo 12               # variations / exact re-roll
imagine critique 12                             # local VLM diagnoses the result
imagine gallery                                 # self-contained outputs/index.html
imagine history · star 12 · prune -y            # curate the output set
```

## 6 · Judgment & evals — `lm probe`

The gate that decides whether a model earns a tier. 9 items: ask-vs-assume, abstention (×2),
pass^k consistency, tool-decision, multi-turn constraints, multi-file coding, scope-trap,
invariant-aware edit. Verdicts are human; the report pre-flags.

```bash
lm probe qwen3.6:35b-a3b          # → probe/runs/<model>-<ts>.md scored report
lm probe some-new-model:tag       # audition anything before trusting it
```

Precedents: qwen3.6 9/9 (kept) beat the 51 GB coder 7/9 (reclaimed); the NVFP4 re-quant kept
conclusions but leaked deliberation — caught here, not by benchmarks (docs/05 §1).

## 7 · Fan-out & orchestration — `lm fleet`

One intent × N files, concurrency-capped, every output through a Judge, run record on disk.
Turns cloud sub-agent fan-outs (audit/reconcile/verify) into free local ones.

```bash
lm fleet review src/*.sh                        # audit every script
lm fleet qa --prompt "who owns this?" docs/*.md # same question across N docs
git diff --name-only | lm fleet review --items-from - -m code
lm fleet summarize notes/*.md --judge 'jq -e ".text|length>100"'   # custom gate:
                                                #   CMD <result.json>, $FLEET_ITEM = source
lm fleet review src/ -j 3 --timeout 600 --json  # machine mode → index.jsonl on stdout
ls outputs/fleet/<ts>-review/                   # meta.json · items.txt · results/ · index.jsonl
```

Multi-file completion (the conductor pattern): `probe/fixtures/unfinished-v1/` — a partial
codebase + pytest Judge + `conduct.sh`; qwen3.6 finished it 16/16. The `complete` intent is
the worker contract (`q complete --ctx -`).

## 8 · Residency & performance — `warm`, leases, status

The no-idle policy (server `KEEP_ALIVE=0`) means models load per call unless pinned. Two pins:

```bash
warm on                        # the companion (small, forever) — q goes sub-second
warm off                       # back to zero idle RAM
warm on code                   # LEASE the code tier — bounded 60m, self-heals if forgotten
warm on code 4h                # longer session · 'forever' opts out of the bound
warm on gemma4:26b 30m         # lease any model
warm off code · warm off all   # release one / sweep everything resident
warm status                    # what's resident + how long it stays
```

Automation: `lm fleet` and `lm opencode` lease automatically and release on exit. Scheduled:
weekday 09:30 companion warm-up, daily 19:00 `warm off all` shutdown backstop (gcc-schedule,
calendar-visible). After 3 cold loads of the same big model in 5 minutes, `q` prints a one-line
lease suggestion (never auto-pins — residency is yours).

```bash
lm status                      # server · resident · on-disk at a glance
lm status --json               # <150ms machine probe: warm/latency_class/models
lm models                      # ● resident, tier labels, sizes
lm doctor                      # 11-point smoke check of the whole toolkit
```

## 9 · Editor & agent integration

```bash
lm opencode                    # opencode on the local coder — lease handled around the session
lm opencode run "fix the failing test"          # headless one-shot
# provider config: ~/.config/opencode/opencode.jsonc (all local chat models, qwen3.6 default)
```

### The gemini lane — `lm gemini` (wrapper-only, never the binary directly)

Throughput + huge-context work on a separate, abundant budget (model pinned
`gemini-3.5-flash`; read-only posture — it generates text, never edits or executes).

```bash
lm gemini "brainstorm 20 names for this tool"    # one-shot
cat big-spec.md | lm gemini "list the risks"     # piped stdin becomes context
lm gemini ingest src/*.py docs/*.md              # feed a corpus into THIS project's session
lm gemini ask "where is auth handled?"           # query the session (--session NAME = cross-project)
lm gemini --json "..."                           # {ok, text, model, ms, session} for agents
lm gemini history · show -1                      # every call logged (gem-history.jsonl)
```

If gemini is unavailable (auth/tier/not installed) you get a structured
`gemini_unavailable` error (exit 11) — the calling agent flags it to the human and falls
back to Claude/lm lanes (rules/model-tier-routing.md). The wrapper isolates the backend:
today's deprecated `gemini-cli` (EOL 2026-12) swaps out later with zero caller changes.

Claude (and any agent) drives the suite through the machine modes: `q --json` workers,
`review --findings`, `see --json`, `lm fleet --json`, `lm status --json`. Local models never
drive their own tools (docs/03) — the orchestrator extracts context, the model answers.

## 10 · Repo intelligence — `lm index`

A lean symbol map per repo: "where is X" answered instantly, no model call.

```bash
lm index                       # build/refresh the map for the cwd
lm index ~/Code/other-repo     # any repo — the map is stored centrally, never in the target
lm index find fleet_worker     # → lib/fleet:132  function  fleet_worker
lm index find parse ~/Code/x   # substring matches after exact, capped at 50
lm index status                # map size, built time, staleness
```

Engine: universal-ctags when installed, else built-in rg definition-patterns (py/js/ts/go/rs/
sh/rb/java/c — including extensionless shebang scripts). Maps auto-rebuild when any file in the
repo is newer than the map — freshness is real mtimes, never a TTL.

## 11 · Observability & the feedback loop

Every command logs; the histories are the API for everything downstream.

```bash
lm timeline 30                 # one merged timeline: q (✗ on failures) · imagine · see · fleet
q history · see history · review history · imagine history     # per-tool, numbered
q show -1 | glow -             # any past answer, rendered
bash scripts/self-audit.sh     # the weekly digest, on demand: volume, failure codes × model,
                               #   latency by model, fleet pass rates → logs/self-audit/
```

The self-audit runs Sundays 11:00 (gcc-schedule `lm-self-audit`): it digests the week and files
ONE gcc proposal if a failure code recurs ≥5× — propose, never auto-fix. `q` failures (timeout,
server-down, cancelled, model-missing) are history lines too, so patterns are minable.

## 12 · Rendering — `--glow`

Any text-producing command renders markdown to the terminal with `--glow`. TTY-only, silent
plain-text fallback when glow is missing or output is piped — agents always get bytes-identical
plain output.

```bash
q --glow --big "explain quaternions with headers and lists"
review --glow 214
see photo.png --glow
```

---

*Server: self-hosted ollama (LaunchAgent), 127.0.0.1:11434, MAX_LOADED=2, KEEP_ALIVE=0,
flash-attn + q8 KV. MLX is format-routed inside Ollama (safetensors tags → MLX runner); the
measured verdict kept Q4_K_M on the code tier — `docs/05` §1. Tiers: `config.sh`.*
