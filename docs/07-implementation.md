# Implementation — the local-model collective

How we build and use the orchestration system. Behaviour- and product-first; professional but lean.
Translates the research (`docs/05`, `.claude/output/2026061*`) and the MAGI verdict
(`docs/06 §9` → `~/.claude/assets/magi/20260621-0030-local-orchestration-arch/06-final-artifact.md`)
into something you build from. **Companion, not replacement, for `06` (the why) — this is the what + how.**

---

## 0. What it is (the product)

A disciplined local-model collective. **Claude conducts; cheap `q` workers execute scoped, verified
sub-tasks under deterministic procedures; the system tunes its own resource use and proposes its own
improvements.** You delegate and trust a result because it *passed a gate* — not because a model said
so. It is built **additively on the existing `q`/`lm`/`imagine` suite** — most of the substrate is
already there; we add thin coordination, not a framework.

What already exists and we reuse as-is:

| Need | Already in the suite |
|---|---|
| The Bus (machine I/O) | `q --json` / `q --stream-json` (stable contract) |
| The outcome log | `logs/q-history.jsonl` — `{ts,cid,intent,model,think,ms,...}` per call |
| Policy-as-data | `config.sh` — `WARM_MODEL` / `BIG_MODEL` / `CODE_MODEL` tiers |
| The Governor's signal | `lm status --json` — `{warm,latency_class,available_models,default_model}` |
| Residency contract | warm-aware `keep_alive` (`-1` resident / `0` load-and-unload) |
| Inspectable artifacts | `imagine` → `outputs/index.html` gallery + history |

### At a glance

```
  you ─"do X across these files"─▶ CLAUDE   (Conductor: decompose · judge)
                                     │ reads signal → allocates
                                     ▼
                                 GOVERNOR    (config.sh policy table — no knobs)
                       ┌───────────┼───────────┐
                       ▼           ▼           ▼
                    q worker    q worker  …  q worker      (the "fools")
                       └─────────┐ │ ┌─────────┘
                                 ▼ ▼ ▼
                                JUDGE        (tests · lint · schema)
                              pass │ → result = a diff you approve
                                   ▼
           logs/q-history.jsonl ─▶ weekly self-audit ─▶ atone / i-dream
              (outcomes)            proposals → you approve → intents/ , prefs
```

---

## 1. Design principles (the lean line)

The values that keep this *professional but lean* — not enterprise (heavy, ceremonial, premature),
not hacky (fragile, magic, silent). These are the tie-breakers when a choice is unclear.

1. **Reuse the substrate; add only coordination.** If the suite already does it, wire to it. New code
   is glue between existing contracts, not a parallel framework.
2. **Contracts over implementations.** Callers speak `q --json` and a Procedure manifest. Swap a
   model, a recipe, or a runner without touching callers. *(This is the main churn-resistance lever.)*
3. **Config-as-data.** Tiers, Governor policy, and Procedure steps are *data* (`config.sh`, TOML).
   Behaviour changes are edits, not rewrites.
4. **Trust is a passing check, never model confidence.** Every worker output crosses a deterministic
   Judge before it reaches you.
5. **Borrow and propose; never seize or self-commit.** Warmth stays user-sovereign; tuning is a
   proposal for human review. The loop suggests; the human commits.
6. **Build behind a proof.** Nothing past Phase 0 ships until **Task #8** shows a local coder clears
   the efficacy bar. No cathedral for an absent tenant.
7. **One front door, invisible machinery.** You still type `q` / `lm`. The army-of-fools is invisible
   and the snappy path stays snappy.

---

## 2. Behaviour spec

### 2.1 How a task flows

```
 request ─▶ GOVERNOR ─▶ PROCEDURE ─▶ q WORKERS ⇄ JUDGE ─▶ result
 (you/Claude) allocate   sequence    (the fools)  gate
              tier+warm   (TOML)                   (tests/lint/schema)
```

A worker is one `q --json` call: one narrow task, structured in, structured out, no autonomy. A
Procedure is a small ordered recipe of workers with a Judge between steps. The Conductor (Claude)
decomposes the goal and reads the Judge's verdict.

### 2.2 Self-setup — the Governor (no knob-fiddling)

The Governor is a **policy table read from `config.sh`**, not a daemon. It reads the task signal
(intent, input size, image present?, repo present?) plus `lm status --json`, and *allocates per task*
— which is why it stops over-eating memory:

| Signal | tier | warmth | ctx |
|---|---|---|---|
| interactive `q` ask/cmd/title | lean (`WARM_MODEL`) | warm | small |
| scoped single-file edit | moderate (`BIG_MODEL`) | on-demand | medium |
| agentic Procedure | beefy (`CODE_MODEL`) | **exclusive lease** | large |
| image / screenshot in | vision VLM | on-demand | — |
| batch worker army | lean/moderate | on-demand, concurrency-capped | small |

The exclusive lease for agentic work is the existing "active task wins, no-idle" behaviour, *named
and automatic*. This is the ease-effort-output triad mechanized — one data table replaces every knob.

### 2.3 Failure behaviour

Salvage-first and throttle-aware (this session's double-throttle is the live case): workers write
output before returning → a killed worker is salvageable; triage (reuse `fleet-triage.py`) →
re-dispatch only the dead; honour `Retry-After`, exponential backoff **with jitter**, a **shared**
token-bucket (not per-worker); drop to sequential batches on a second throttle. Local `q` workers are
throttle-immune (self-hosted Ollama) — backoff guards the Claude-conductor calls. No retry is "done"
until its Judge passes.

### 2.4 Self-improvement behaviour

Outcomes already land in `logs/q-history.jsonl`. The Feedback Sink (a `Stop`/`PostToolUse` hook) routes
them: **failures → atone** (the fools' RCA log), **patterns → i-dream / `preference-harvest.sh`** as
*proposals*. Every tuning change to a Procedure, the Judge, routing, or Governor policy lands as a
proposal/diff for human review — those are code, same gate as code. The only auto-applied change is a
bounded, reversible, logged scalar (e.g. concurrency cap ∈ [1, cores-2]).

---

## 3. Product / UX spec

- **The core experience:** you delegate a scoped task and trust the result *because it passed a gate*.
  For edits, the **diff-review gate** is the trust surface — you approve a diff, you don't audit prose.
- **Surfaces stay stable and additive.** `q` / `lm` / `imagine` keep their current shape and speed;
  orchestration adds an `lm run <procedure>` verb and Claude-delegated procedures — it never slows the
  snappy `q` path.
- **Transparency by default.** Every warm eviction is visible in `lm status` (it shows the truth, not
  a lie, even after a crashed lease); every tuning change is a visible proposal; the Judge's verdict is
  shown with the result.
- **Inspectability follows the `imagine` precedent** — a Procedure run leaves a small, self-contained
  record (the `outputs/index.html` gallery pattern), so you can see what the army did.
- **Ergonomics inherited from `q`:** sensible defaults, never asks clarifying questions (assumes
  intent), `-h` help on every command, structured errors with stable exit codes.

---

## 4. Resistance to churn (why it won't rot)

This is a first-class goal, not an afterthought:

- **Stable contracts, swappable insides.** `q --json` is the only thing callers bind to; models,
  recipes, and runners change underneath without breaking them.
- **Behaviour lives in data.** Tiers, policy, and Procedure manifests are editable config — no code
  rewrite to change what runs where.
- **No stale caches.** The Index rebuilds on the file-edit hook signal and reads live on staleness —
  never a TTL that lies after the repo changes.
- **No silent drift.** Human-in-loop gates mean the system can't tune itself into a different system
  while you aren't looking.
- **Borrowed maintenance.** It leans on gcc systems (hooks, i-dream, atone, `preference-harvest`,
  `fleet-triage.py`) that are maintained elsewhere — less surface we own.
- **Gated growth.** You only build what a proof justifies, so there's no orphaned machinery to keep
  alive. Less code is less to update — the `q` suite is ~540 lines; keep additions that order.

---

## 5. The build (phased, with concrete artifacts)

### Phase 0 — habit + perf + the gate *(unconditional, days)*
| Add / change | Behaviour delivered | Done when |
|---|---|---|
| MLX backend (Task #22) — **`OLLAMA_USE_MLX` is inert on 0.30.6 (tested, see lm-serve NOTE)**; needs a newer Ollama or `mlx_lm.server` | ~2× decode if/when active | the working toggle identified, then tok/s measured |
| Governor policy table in `config.sh` (extend the tier vars) | per-task allocation, no knob-fiddling | a `lm`/`q` call resolves tier from signal, not flags |
| Routing-glue: Claude → `q` for the safe ~40% (recon, shell, commits, scoped edits behind a diff gate) | the offload habit, no new engine | the 4 lean/moderate task-types run on `q` with a review gate |
| `q` habit (Task #23) + local RAG embedder (Task #24) | lean offload + research re-fetch killed | `q cmd`/`commit` are reflex; RAG answers a repeat lookup |
| **▶ Task #8 — probe the top-3 coders on the 6-item judgment harness** | **the gate** | a measured verdict: does a local coder clear the efficacy bar? |

If Task #8 **fails**, stop here — the lean/moderate habit is the whole win, and the rest is not built.

### Phase 1 — the trust spine *(only if Task #8 clears)*
| Add | Behaviour delivered | Done when |
|---|---|---|
| `bin/procedure` — a small bash runner over TOML step-manifests | repeatable, inspectable multi-step recipes | a 3-step Procedure runs + leaves a record |
| Judge step (tests/lint/types + `q` critic; constrained decoding via Ollama `format`/GBNF) | outputs gated before they reach you | a deliberately-broken worker output is *caught*, not shipped |
| Salvage + throttle wrapper (reuse `fleet-triage.py`) | survives a real throttle | exercised against an **induced 429**, salvages survivors |
| Governor v0 (the `config.sh` table, read-only) + lease-based warmth | auto tiering; warmth borrowed-and-restored | an agentic run evicts + **reloads** the user's warm model |
| Lean `ctags`/tree-sitter Index, rebuilt on the edit hook | whole-repo structure on demand (Fable-lite) | a worker answers "where is X" from the map |
| Feedback Sink: `Stop` hook → atone + i-dream proposals (write-to-proposals only) | self-improvement that can't drift | a worker failure shows up as an atone event + a proposal |

**Gate to Phase 2:** ≥3 human-approved proposals applied AND the throttle wrapper survived a real
event with salvage. Only then revisit: a real DAG runner, a bounded auto-tuned scalar, a deeper Index,
the Conductor interface for a local supervisor.

---

## 6. Intent graduation — the action library that grows itself

An `intent` in `q` is a named *(system-prompt + default tier + ctx requirement)* — today `ask`, `cmd`,
`title`, `commit`, `summarize`, `explain-code`, `describe-data`, `qa`. **An intent is the smallest
"strict procedure for the fools": a crystallized sub-prompt + tool/ctx pattern.** This feature lets
the library *grow itself from your real usage*, on review — and it's the bridge between the lean `q`
offload and the orchestration's Procedures.

### The behaviour
You keep doing a shape — `q explain-code --ctx <some script>`, or a recurring "review this hook for X"
— and a weekly lookback notices the pattern and proposes it as a *named* intent you can then call in
one word. A common action you do by hand becomes a first-class verb. It's **preference-graduation
applied to actions**: same harvest → propose → human-review → promote loop, new payload.

### The three pieces
1. **Intents-as-data (the enabler, load-bearing).** Today intents are hardcoded `case "$INTENT"`
   blocks in `bin/q`. Move them to a registry — `intents/<name>.toml` *(name, system-prompt, default
   tier, `needs_ctx`, optional `ctx_glob`)* — and have `bin/q` read it. Adding an intent becomes
   *dropping in a file*, not editing code. (Config-as-data; this is the prerequisite for everything else.)
2. **Log enrichment.** `q-history.jsonl` already logs `{intent,prompt,model,ms}`; add `ctx_name` /
   `ctx_source` so the lookback can cluster by *what kind of thing* the intent ran on.
3. **The lookback (`intent-harvest.sh`).** A sibling of `preference-harvest.sh`: mine `q-history.jsonl`
   for recurring `(intent × prompt-shape × ctx-class)` clusters above a frequency floor, and write
   *candidate intents* (proposed name + crystallized sub-prompt + `ctx_glob`) to
   `topics/intent-candidates-YYYY-MM-DD.md`. **Propose, never auto-add** (the self-improvement rule).
   You review; an approved candidate becomes a file in `intents/`.

### Schedule + phasing
Weekly via `gcc-schedule` with its calendar companion — same pattern as `preference-harvest`. They're
the same *kind* of audit, so fold both into one weekly **self-audit** pass (preferences + intents +
later Governor-policy proposals) rather than three crons. *Intents-as-data is a **Phase 0** enabler
(small, improves usability immediately); the harvest is a **Phase 1** self-improvement feature.* The
independent Claude-linked scheduler is the delivery surface; the human is always the gate.

### Why it's lean + churn-resistant
Intents live in data → the library grows with zero `bin/q` churn. The harvest only proposes → no
drift. It reuses the harvester + scheduler + review-loop that already exist → net-new code is one
mining script + a registry loader, not a framework.

## 7. What we deliberately do NOT build (hold this line)

So future work doesn't creep enterprise:
- **No DAG/state-machine runner** until ≥2 Procedures genuinely need shared-state concurrency (bash + a
  TOML manifest is the seam until then).
- **No Governor daemon** — it's a config table.
- **No local supervisor model** — Claude conducts until a local model posts a measured τ²-bench pass^k.
- **No deep semantic/embedding code-index** — a symbol map covers it; embeddings stay for docs/RAG.
- **No auto-executed tuning** beyond one bounded reversible scalar.
- **No new framework or heavy dependency.** Bash, JSONL, TOML, the existing `q` API.

---

## 8. Where it lives — placement & layout

**Stays at `~/Code/local-models` — one repo, don't split, don't move.** Already a standalone git repo
whose `~/.local/bin` wrappers point at `bin/`; shares one server (`lm-serve`), one lib (`_lib.sh`),
one front door (`lm`). Splitting fragments the reused substrate; moving breaks the PATH install.

The growth risk is `bin/` becoming a grab-bag — so separate the user-facing verbs from the machinery:

```
~/Code/local-models/                    ← one repo, stays put
├─ bin/          user verbs ON PATH (small, flat, stable)
│    q  lm  imagine  warm  lm-serve  _lib.sh
├─ lib/          orchestration internals, NOT on PATH          ← new
│    procedure  governor  intent-loader  judge
├─ intents/      intent registry (data, *.toml)                ← new
├─ procedures/   procedure manifests (data, *.toml)            ← new
├─ scripts/      project-local automation (gcc-schedule'd)     ← new
│    intent-harvest.sh   self-audit.sh
├─ config.sh     policy-as-data (tiers · governor)
└─ docs/  outputs/  logs/  modelfiles/  presets/
```

**The gcc boundary (the real future-proofing).** The system leans on gcc services. Hold this line so
the project and gcc don't bloat each other:

```
  PROJECT (owns the WHAT)            gcc / ~/.claude (provides SERVICES)
  ──────────────────────            ──────────────────────────────────
  intents/ procedures/ lib/   ◀──   hooks             (triggers)
  intent-harvest, the Judge   ◀──   gcc-schedule      (the weekly cron)
  q-history.jsonl (outcomes)  ──▶   i-dream / atone   (the sinks)
                                    preference-harvest (GLOBAL: prefs)
```

Rule of thumb: *is it about local-models specifically, or how Claude works everywhere?*
Project-specific (q-intents, procedures, the Judge) → here, scheduled via gcc-schedule.
Cross-project (preferences) → gcc. (Why `preference-harvest` is global but `intent-harvest` is local.)

---

## 9. CLI cookbook (the experience)

```bash
# ── Today (already works) — the lean offload ───────────────────────────
q cmd "find files over 100MB under ~/Downloads"     # → one shell command
git diff | q commit                    # → commit message from the diff
q explain-code --ctx ~/.claude/scripts/preference-harvest.sh

# ── Phase 1 — delegate a scoped procedure ──────────────────────────────
#   Claude conducts · fools execute · Judge gates · you approve a diff
lm run review-hook --ctx ~/.claude/scripts/foo.sh
  → governor: lean+warm · 3 workers · judge=shellcheck
  → ✓ shellcheck passed → presents a diff for your approval

# ── Intent graduation — a habit becomes a verb ─────────────────────────
#   After weeks of `q explain-code --ctx <script>`, the weekly self-audit proposes:
cat topics/intent-candidates-2026-06-28.md
  ## candidate: audit-script   (seen 11×: explain-code on ~/.claude/scripts/*.sh)
  sub-prompt: "Explain + flag anything dangerous…"  ctx_glob: ~/.claude/scripts/*.sh
#   you approve → drop in intents/audit-script.toml → now it's a one-word verb:
q audit-script --ctx ~/.claude/scripts/new-thing.sh

# ── Transparency — the system never hides state ────────────────────────
lm status          # shows the warm model truthfully — even after a lease evict+restore
```
