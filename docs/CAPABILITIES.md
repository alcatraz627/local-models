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
q --web "latest ollama release?"               # search first (DDG, no key), answer cites [n]
q --diy "summarize README.md"                  # q routes itself: intent/web/file/image/tier,
                                               #   every step narrated on the gray channel
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
see dashboard.png --ui                          # UI inventory: KIND/LAYOUT/HIERARCHY/ELEMENTS/ICONS/PATTERNS/PALETTE
see menu.png --ui "which item is enabled?"      # UI inventory + a focused answer
see --menubar "which app is focused?"           # capture the live macOS top strip, then --ui it
see panel.png --ui --json | jq .data            # schema-constrained {kind,theme,regions[].elements[],icons,palette}
see mockup.png --json                           # {ok,text,model,ms,artifact} for an agent
see receipt.png --ocr                           # EXACT text via Apple Vision — no model, ~300ms, verbatim
see shot.png --ocr --json | jq .data.words      # positioned text: {text, x,y,w,h, pos: top-left..bottom-right}
see shot.png --ocr --region top                 # crop-then-OCR: exact text from one region
see shot.png --region left --ui                 # crop first, then read — small crops read near-perfectly
see shot.png --crop 800x600+0+120 "count?"      # exact pixel window (WxH+X+Y from top-left)
see diff ref.png candidate.png                  # compare two images: $0 evidence pack + judged read
see diff a.png b.png --json | jq .evidence      # full pack: scores/text/color/grid/shape + nudges
see diff a.png b.png --only E5 --grid 32        # slice rerun of one extractor — delta, no model call
see more "what does the badge say?"             # drill into the LAST image (from its artifact copy)
see photo.png --glow                            # rendered read
see ui.png -m gemma4:26b                        # the stronger general-scene reasoner
see history · see show -1                       # every read is logged, replayable
see open -1 · see note "obs…"                   # the read's artifact folder · append a note to it
see reshoot <loop-dir>                          # replay the loop recipe (web: playwright · static: candidate file); wrong-size captures refused
```

Every read lands one discoverable **artifact folder** — `outputs/see/<ts>-<mode>-<img>/`
with the image *as read* (the crop / menubar strip, which would otherwise die with the
temp dir), `read.md`, `meta.json`, and `notes.md` via `see note`. `see open N` jumps to
it, `see more` re-targets it for follow-ups, and the newest 150 are kept. History lines
carry `artifact` + `crop` fields; the `--json` envelope exposes `artifact` for agents
building evidence trails.

**`see diff` evidence layer (L1).** A diff runs deterministic `$0` extractors
(`lib/vis-compare.py`, pure PIL — no numpy/opencv) and returns the full pack under
`.evidence`: E1 text/position diff, E3 palette/ΔE (CIE76), E4 dHash+aHash, E5 grid-ΔE
heatmap, E6 edge/shape grid — plus `cost`, `failures`, and paste-ready `next:` nudges.
Modality-adaptive (the icon case skips the text lanes, runs shape/color), with a
comparability gate for mismatched pairs. The doctrine holds: **scripts measure, the
model judges** — the VLM read is barred from disputing an extractor's number. The
artifact folder gains `evidence.json` + a `contact.png` (A│B│ΔE-heat), the two inputs a
downstream judge reads. `--only`/`--grid` re-run one extractor against a content-addressed
cache and return just the delta. Every run journals to `logs/compare-history.jsonl`.
The judgment layer (L2, a gcc `/vis-compare` skill) is not built yet — this is the
evidence half. Battery: `probe/fixtures/vis-battery.py` (F1-F8, model-free, in verify.sh).

`--menubar` screencaptures the main display's top strip and reads it (cropping first
is the biggest quality lever for widgets — a full-screen frame buries the strip);
needs Screen Recording permission, and reads the frontmost app's content instead of
the menu bar while a fullscreen app is active. `--ui --json` returns the inventory as
a schema-constrained object in `.data` (`intents/ui-inventory.schema.json`, Ollama
`format` enforcement, same contract as `q --format`) for agents that consume elements
rather than read markdown.

`--ui` is the sectioned UI-inventory read for websites/apps/widgets/mocks — enumerated
elements with verbatim labels and states, visual hierarchy, icon best-effort, formatting
patterns, coarse palette. It auto-routes to the big tier (`UI_VISION_MODEL`, measured better
at structure/state 2026-07-08; `-m` overrides) and honors an active `warm on big` lease for
batches. Benchmarked vs gemini vision on 15 real screenshots:
`.claude/output/20260708-vision-ui-batch/report.md` (gemini wins exact-string fidelity,
`see --ui` wins speed/cost/privacy; crop menu-bar strips before reading). Vision via the
gemini lane: `lm gemini "describe @shot.png"`.

### UI claim verification — `lm ui-verify`

The $0 verification gate for UI work: after a change, enumerable claims ("the Save
button is disabled", "the count shows 457") are checked mechanically against a
`see --ui --json` inventory, judged strictly by the local warm tier (pass / fail /
unsure — and unsure never passes). Aesthetics are not enumerable; those stay with
Claude (see the gcc `/ui-gripe` and `/designer-reviewer` skills, which run `see --ui`
as their structural first pass).

```bash
lm ui-verify shot.png "there is a Save button" "3 tabs are visible"
lm ui-verify shot.png --region top "the Logs tab is selected"    # crop = near-perfect reads
lm ui-verify --app Finder "there is a Force Quit menu item"      # LIVE accessibility tree — exact, no pixels
lm ui-verify shot.png --boxes "the count is in the top right"    # placement claims via measured positions
lm ui-verify shot.png "count shows 457" --json | jq .results     # for review agents
# exit 0 = every claim passed · exit 1 = any fail/unsure · evidence cites the artifact
```

Two evidence lanes: screenshots go through `see --ui --json` (general, good-but-verify);
running apps go through the accessibility tree via `ax` (`--app` — semantic and exact,
covers whatever the app exposes to accessibility; needs the Accessibility permission).
The trio for reading a UI: **AX tree** (native apps, exact) · **`see --ui`** (any pixels,
structured) · **`see --ocr`** (any pixels, verbatim text).

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

mflux (MLX Flux/Qwen) on the GPU. **A model must be FULLY downloaded before it will run** —
`imagine` preflights the HF cache and refuses (exit 12, ~0.5s) on a partial one, printing the
exact `hf download` command. This is deliberate: a half-downloaded model silently re-enters a
multi-GB fetch and looks identical to a very slow render (it once burned 38 minutes at 2% CPU).

```bash
imagine "a cozy reading nook, rainy window"     # default: qwen — quality-first, ~3min
imagine --enhance "neon ramen bar"              # local prompt-engineer pass first
imagine -m schnell "quick draft"                # ~46s — the LOOP model (see §13)
imagine --style watercolor --neg "text, logos" "koi pond"
imagine --from sketch.png "same but at dusk"    # image-to-image
imagine refine 12 "warmer light"                # SEED-LOCKED iterate on #12 — the loop's engine
imagine vary 12 · imagine redo 12               # variations / exact re-roll (fresh roll)
imagine critique 12                             # local VLM diagnoses the result
imagine gallery                                 # self-contained outputs/index.html
imagine history · star 12 · prune -y            # curate the output set
```

**Model split:** `qwen` is the default *finisher* (quality; speed was explicitly ruled not to
matter for final images — `config.sh:25`). `schnell` is the *scratch* model for convergence
loops, where every round is a throwaway and speed is the whole cost. `refine` is **seed-locked**
— it changes only what you name and holds the roll; `vary` re-rolls everything.

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
lm gemini ingest-repo [dir]                      # pack a whole repo (repomix, gitignore-aware, ~70% compressed) and ingest it
lm gemini ask "where is auth handled?"           # query the session (--session NAME = cross-project)
lm gemini digest <dir|files...>                  # one-shot corpus digest -> JSON claims, each quote grep-verified (fail-closed)
lm gemini research "official site of X?"         # web-shaped lookup -> JSON, null-when-unsure, 420s default cap
lm gemini --json "..."                           # {ok, text, model, ms, session} for agents
lm gemini history · show -1                      # every call logged (gem-history.jsonl, incl. bytes_in/bytes_out)
```

Robustness (2026-08-30): workload-aware timeouts (oneshot/ask 300s, ingest/digest/research
420s, `--timeout` wins), one auto-retry at 1.5x on a wall-clock kill, and `--fallback-local`
to answer on `gemma4:26b` (marked local, weaker seat) when gemini is unavailable.

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

## 13 · Imitation fidelity — `see diff` + `/vis-compare` (the compare stack)

**"Does B faithfully imitate A?"** — for a rebuilt UI, a regenerated icon, a re-rendered
image. Not a distance score: a *judgment* about whether each difference matters. Three layers,
strict roles — **scripts measure, models judge, the ledger tracks.** Full design + the honest
built-vs-deferred inventory: `docs/10-visual-compare-design.md`.

```bash
# L1 · evidence ($0, deterministic, CANNOT fabricate a difference)
see diff a.png b.png --json          # full pack: text · colour/ΔE · hash · grid · edges
see diff a.png b.png --no-read       # evidence only, ~1s, no VLM seat — the LOOP default
see diff a.png b.png --only E5 --grid 32   # rerun ONE extractor finer; returns just the delta

# L2 · judgment (a gcc skill — Claude reads the pixels + your taste policy)
/vis-compare a.png b.png             # → looks-worse | neutral | improvement | not-worth-chasing
/vis-compare --revisit d1 --feedback "the radius call is wrong"

# L3 · loop (converge a candidate onto a reference)
/vis-compare --loop a.png b.png
.venv/bin/python lib/vis-ledger.py add outputs/see/loops/<slug>/ verdict.json --pack evidence.json
.venv/bin/python lib/vis-ledger.py status outputs/see/loops/<slug>/
```

**The rule that will bite you:** in a loop, read progress from the **ledger's transitions**
(`fixed` / `persisting` / `regressed`), *never* from the scores. Region metrics saturate the
moment composition moves — one live round fixed 3 of 5 divergences while grid-delta ROSE
93.8% → 100%. A loop that stops on "scores plateaued" quits exactly when it is working. The
ledger states this in-band so it can't be misread.

### Companion tools (`lib/`, all model-free)

```bash
# Are the derived rungs of an asset as good as their size allows?
.venv/bin/python lib/asset-verify.py icon.png icons/*.png --json
#   Judges each rung against a best-achievable resample AT ITS OWN SIZE — so "a 30px icon
#   can't hold every edge" isn't held against it. Exit 1 if any rung is beatable.

# The $0 review pre-gate's trust layer (fail-CLOSED)
git diff | review --findings --json -m small | jq '.data' \
  | .venv/bin/python lib/findings-gate.py --root .
#   Drops any finding whose file:line does not exist. Survivors are OPINIONS to triage,
#   never verdicts. (-m small: the 35b code tier ignores Ollama's format constraint.)

# Exact CSS from a live web surface (so the judge never estimates a colour)
#   1. run lib/e8-extract.js in any browser driver (Playwright/CDP MCP), save both captures
#   2. .venv/bin/python lib/e8-dom.py cap-a.json cap-b.json
```

**Imagegen convergence** (§5 + this stack): `imagine -m schnell` → `see diff --no-read` →
judge at nudged moments → `imagine refine N "<the verdict's fix_hints>"` (**seed-locked**, or
every divergence reads as new and the ledger becomes meaningless) → repeat. Proven live: one
refine fixed 3 of 5 divergences.

---

*Server: self-hosted ollama (LaunchAgent), 127.0.0.1:11434, MAX_LOADED=2, KEEP_ALIVE=0,
flash-attn + q8 KV. MLX is format-routed inside Ollama (safetensors tags → MLX runner); the
measured verdict kept Q4_K_M on the code tier — `docs/05` §1. Tiers: `config.sh`.*
