# DESIGN (2026-06-20): Local-Model Orchestration — the disciplined collective

Status: **inline architecture, pending `/magi --mode full` adversarial review** (org throttling
blocked the fan-out at authoring time — re-run magi to stress-test §9 before committing to build).
Grounds: the efficacy research (`.claude/output/20260620-efficacy-architecture/`), the usage audit,
the judgment benchmarks, and the gcc integration surface (hooks/i-dream/atone/personas/memory/q-API).

---

## 0. The Fable reference — what we're actually replicating

"The now-dead Fable" = **Claude Fable 5** (Anthropic, launched 2026-06-09, disabled worldwide
2026-06-12–14 under a US export-control directive). Its defining trait: a **1M-token context that
holds an entire codebase in working memory** — read a full repo, plan a migration, generate+test
code, fix its own errors, prepare PRs in a single autonomous run. The capability you want from it is
**whole-repo structural comprehension** ("identify the overall structure").

You can't hold 1M tokens of a big repo on 64 GB. So you don't replicate the *mechanism* (giant
context) — you replicate the *capability* via a **structural Index** (a symbol/dependency map that
delivers whole-repo structure on demand without holding it all in context). And a second Fable-era
fact is the keystone of this whole design: **only ~1.6% of Claude Code is AI decision logic; 98.4%
is deterministic infrastructure** (permission gates, context mgmt, tool routing, recovery). That is
*literally your thesis* — "an army of fools under strict procedures" — validated by the best agent
harness in production.

---

## 1. Thesis

**Don't build a smart local model. Build a smart SYSTEM around dumb-but-disciplined local workers,
conducted by Claude.** Intelligence lives in the *procedures, the verification, and the structure* —
not the model. (Corroborated three ways: your own `docs/03` deterministic-orchestrator decision;
the efficacy finding "scaffold > size, a 4B recovers ~90% of frontier via context-control"; and the
Claude-Code 98.4%-deterministic architecture.)

---

## 2. Core concepts (the units)

| Unit | What it is | "Army of fools" role |
|---|---|---|
| **Worker** | one `q` call — cheap, single narrow task, structured I/O (`--json`), zero autonomy | the fool |
| **Procedure** | a deterministic recipe (script) sequencing Workers + Judges | the strict discipline; the unit of trust |
| **Conductor** | decomposes a goal → Procedure; routes; the smart layer (Claude; or a local supervisor for cheap loops) | the general |
| **Judge** | the verify-loop: tests / lint / types / constrained-decode / a critic-Worker; gates every step | the trust engine |
| **Index** | tree-sitter symbol+dependency map (code) + embeddings (docs) | Fable-lite structure + seek-out |
| **Governor** | resource policy: auto-picks tier / warmth / concurrency / ctx per task signal | solves "no knob-fiddling" |
| **Feedback Sink** | outcomes → i-dream / atone / preference-harvest → improvement | the self-tuning loop |
| **Bus** | the `q`/`lm` JSONL API + structured contracts that let units compose | the wiring |

---

## 3. The six capabilities → how each is realized

| Capability | Realized by | gcc / API integration |
|---|---|---|
| **Scale** | parallel Worker pool under one Procedure (concurrency capped by Governor) | `q --json` + JSONL histories (the Bus) |
| **Judge** | Judge unit: deterministic checks + a critic-Worker + constrained decoding | personas (critic role), llama.cpp GBNF / Ollama `format` |
| **Seek out** | Index queries (repo-map + RAG) and web | Qwen3-Embedding-0.6B (Task #24), `q --ctx/--file` |
| **Delegate** | Conductor routes scoped sub-tasks to Workers; Claude delegates to the collective | hooks; `q` as a Claude tool (MCP / `ANTHROPIC_BASE_URL`) |
| **Identify structure** | the Index (tree-sitter symbol graph) = Fable-lite | a new `bin/index` builder (offline, cached) |
| **Collect feedback** | Feedback Sink pipes outcomes into the self-improvement loops | PostToolUse/Stop hooks → i-dream pins, atone, `preference-harvest.sh` |

---

## 4. The adaptive Governor (your no-knob-fiddling requirement)

The pain: max-tuning eats memory; per-task fiddling is tedious. The fix is a **deterministic policy
keyed on task signal** — not ML, not manual. It *allocates per task* instead of *max-always*, which
is precisely why it stops eating memory it doesn't need.

- **Signals (in):** intent (`q`'s ask/cmd/title/agentic), input size, latency need (interactive vs
  batch), image present?, repo present?, judge-criticality.
- **Allocation (out):** tier (lean/moderate/beefy/vision), warmth (warm / on-demand / **exclusive**),
  concurrency cap, `num_ctx`.

| Task signal | tier | warmth | ctx | notes |
|---|---|---|---|---|
| interactive `q` ask/cmd/title | lean | warm | small | the snappy path you have |
| scoped single-file edit | moderate | on-demand | medium | load → do → unload |
| agentic Procedure (multi-step) | beefy | **exclusive** | large | Governor evicts warm, gives it the box, reloads warm after — your existing "active task wins, no-idle" rule, automated |
| screenshot / image in | vision | on-demand | — | spin VLM, parse to structured text, unload |
| batch fool-army (N workers) | lean/moderate | on-demand | small | concurrency-capped, no warm churn |

This is the **ease–effort–output triad, mechanized** (the memory you baked) + the no-idle rule
enforced automatically. One policy table replaces all the knobs.

---

## 5. Phases (build order = efficacy-per-effort, gated)

- **Phase 0 — Substrate.** MLX on (perf, Task #22); harden `q`'s structured-I/O contract (the Bus);
  Governor v0 as a policy table. *Everything downstream needs these.*
- **Phase 1 — Discipline (the MVP).** Procedure engine + Worker pool + the **Judge** (verify-loop +
  constrained decoding). This is the army-of-fools-under-procedure core, and per the efficacy
  research the Judge is the single highest trust-per-effort lever ("external feedback flips
  self-correction from harmful to +21–32 pts").
- **Phase 2 — Structure & Search.** The **Index** (repo-map = Fable-lite) + RAG for docs. Lights up
  "identify structure" + "seek out." (Repo-map beats vector RAG for *code*; RAG is for *docs*.)
- **Phase 3 — Claude integration.** `q`/`imagine`/vision as delegated tools (the 3 top cases below);
  routing/cascade — **route-then-commit, NOT draft→cloud-review** (that backfires +31–41% tokens).
- **Phase 4 — Self-improvement.** Feedback Sink → i-dream / atone / preference-harvest. The system
  tunes its own Governor policy + Procedures from outcomes.
- **Phase 5 — Depth.** Judge panels, test-gated best-of-N (**Self-MoA** — your one best model sampled
  hot, no model zoo), a convention LoRA (the "isotope" lever).

---

## 6. Cross-interactions (the nervous system)

```
        ┌──────────── hooks = the nervous system ────────────┐
        │ UserPromptSubmit→trigger   PostToolUse/Stop→harvest │
        └───────────────────────┬─────────────────────────────┘
                                 ▼
   goal ─▶ CONDUCTOR ─▶ GOVERNOR ─▶ PROCEDURE ─▶ WORKERS ⇄ JUDGE ─▶ result
   (Claude)   │  decompose │ allocate  │ sequence   (q army)  │ gate
              │            │           │                      │
              │            ▼           ▼                      ▼
              └── INDEX (structure/seek) ───────────▶ FEEDBACK SINK
                                                        │
                                          i-dream / atone / preference-harvest
                                                        │
                                          tunes ◀───────┘ (Governor policy + Procedures)
```

The loop closes: outcomes flow into dreaming/atone/preference-harvest, which **adjust the Governor's
policy and the Procedures** — so the collective gets better and self-tunes without you touching knobs.

---

## 7. The Claude integration surface (top 3 + the dreaming scope)

1. **`q` quick-asks / the fool-army.** Claude fans *scoped, verifiable* sub-tasks to `q` Workers
   under a Procedure. A PreToolUse nudge can route "give me a command / quick lookup" patterns to
   `q` instead of a full Claude turn.
2. **`imagine` image-gen.** Claude calls `imagine`; the generate→critique→refine loop stays local
   (already built).
3. **Vision / screenshot parsing.** A local VLM (Qwen3-VL-30B-A3B or Moondream) parses provided
   images/screenshots into **structured text** that Claude reasons over — your existing
   "VLM parses, Claude reasons" pattern (`docs/00-plan.md`). Governor spins it up on image input,
   unloads after.

**More (the dreaming/atone/hooks scope you flagged):** nudges that route work by Governor policy;
atone capturing *local-worker* failure patterns (the fools' RCA log); preference-harvest learning the
*routing* policy over time; a `structure` command Claude calls to get the repo-map on demand.

---

## 8. The "army of fools" doctrine (the boundary)

Many cheap disciplined calls **beat** one expensive smart call **when the task is decomposable AND
verifiable**. The discipline (Procedures + Judges) substitutes for per-worker intelligence. The
boundary, from this session's judgment research: **non-decomposable, judgment-heavy, trust-critical
work stays with the smart Conductor (Claude)** — the fools can't be trusted to know when to ask or
abstain (reasoning-tuning even *hurts* that). The fools execute; the Conductor judges.

---

## 9. Open decisions — RESOLVED via `/magi --mode full` (2026-06-21)

> **SETTLED.** 5-voter panel (4 personas + jester), voting winner voter-2 / merge. Verdict +
> build sequence: `~/.claude/assets/magi/20260621-0030-local-orchestration-arch/06-final-artifact.md`.
> TL;DR: build small + gated; **Task #8 is the real Phase 0 gate**; bash+TOML-manifest (not DAG-now);
> warmth user-sovereign (borrow-restore-announce); self-improvement = auto-propose, never auto-execute.
> Original open questions (now answered) below.

1. **Conductor split:** Claude-only, or a *local* supervisor model for cheap inner loops (cost vs
   the judgment gap)?
2. **Procedure engine:** bash recipes (fits the suite) vs a real DAG/state-machine runner?
3. **Index investment:** how much to build vs lean on Claude's own context window?
4. **Fleet failure semantics:** abort/retry/salvage for Worker armies (this session's API-throttle
   pain is the live example — the Procedures need throttle-aware backoff).
5. **Governor authority:** can it preempt a user's `warm` choice, or is warmth always user-sovereign
   (the existing "warmth is read-only for machine consumers" decision)?
6. **Self-improvement write-bar:** what outcomes are allowed to auto-tune policy vs require human
   review (the preference-graduation human-in-loop rule applies)?
