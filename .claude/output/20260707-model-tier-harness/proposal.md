# Model-Tier Harness — detailed spec proposal

Draft for user review — 2026-07-07 · session local-agent-9c.
Grounded in: the user's directive notes (Task #18), `recon-gcc-surfaces.md` (what exists),
`recon-gemini.md` (the gemini surface). Recon cost: 2× sonnet, read-only, no nesting.

## 0. What this is, in one paragraph

One authoritative source that tells every agent **which lane, model, and effort level a piece
of work should run on** — cloud Claude (haiku/sonnet/opus/fable), the local lm suite, or
gemini — with the decision made **proactively at plan time**, enforced by a hook nudge
(because prose rules don't bind mid-flight agents), and supported by pairing tools that make
the non-Claude lanes first-class instead of "a bash call returning an untrusted diff."
It operationalizes doctrine the user has already established (efficacy-over-speed, the
ease–effort–output triad, anti-one-shotting, the Opus-ceiling rule) — it invents no new
philosophy, it makes the existing one mechanical.

## 1. Motivation (evidence, not vibes)

- **The Fable burn:** last week Fable-as-main dispatched Fable sub-agents for research that
  didn't need them — a multiplied bill for zero quality gain. The ceiling rule that resulted
  (`subagent-model-ceiling.md`) is checklist-only; nothing inspects a dispatch mechanically.
- **269 sub-agent dispatches in 14 days** (docs/09 audit) are dominated by scoped-verifiable
  audit/reconcile/verify work — much of it local-fleet-shaped, all of it billed as cloud.
- **Gemini is set up but unused:** recon found the CLI has *never been invoked* from shell or
  any Claude session. Its budget (much larger than Claude's weekly cap before usage pricing)
  and throughput are pure unclaimed capacity.
- **The routing doctrine has no data path:** efficacy/triad/one-shotting live in
  `memory/global/` + `GLOSSARY.md` prose. Per the gcc's own
  `skill-spec-update-not-honored` rule: a mandate without a mechanical gate is advisory.

## 2. The lane × tier ladder (the core table)

| Lane | Members | Cost | Strengths | Trust posture |
|---|---|---|---|---|
| **Local** | `q` small/big/code · `see` · `review` · `imagine` · `lm fleet` · `lm index` | ~$0, throttle-immune | volume, always-on, privacy | trust = a **passing gate** (judge/tests/schema), never model confidence |
| **Gemini** | `gemini-3.5-flash` (headless `-p`, `-o json`, `--resume`) | separate, much larger budget | throughput, huge context, breadth ideation | **untrusted content**: digest/candidates in, Claude verifies before load-bearing use |
| **Claude · haiku** | sub-agent only | ¢ | trivial lookups | low |
| **Claude · sonnet** | sub-agent default | $ | research, inventory, mechanical multi-step | medium; verify claims that matter |
| **Claude · opus** | **main daily driver** + judgment sub-agent seats | $$ | judgment, review, synthesis-adjacent work | high |
| **Claude · fable** | main agent ONLY, occasional | $$$$ | genuinely vague + complex tasks | never a sub-agent, at any depth (hard rule, existing) |

**The effort axis (new — no existing rule covers it):** `low / medium / high / xhigh`.
- Sub-agent effort **must not exceed** the main agent's effort when the main is high/xhigh;
  default sub-agent effort is **medium**, `low` for mechanical stages, `high` only for
  judgment/verify seats. `xhigh` on a sub-agent requires explicit user sanction.
- Tool-call *count* is not effort — a low-effort agent may make many calls (the user's
  explicit carve-out: "tool calls are fine").

## 3. Decision rules — task class → lane (the authoritative when-to-use)

Default = **the smallest adequate lane; escalate on evidence, never on anticipation.**

| Task class | Lane / model / effort | Notes |
|---|---|---|
| Trivial lookup, title, one-command | local `q` (warm) or haiku | glance-verifiable |
| Mechanical transform / rename sweep | sonnet low, or local fleet if scoped-verifiable | |
| Recon / inventory / "where is X" | sonnet low–medium; `lm index` first for symbols | this proposal's own recon = the pattern |
| Audit / reconcile / verify at volume | **local fleet** (judge-gated) | the 65% shape from the 269-dispatch audit |
| Web research | sonnet medium (fan out only if genuinely parallel) | opus only if the judgment IS the research |
| Massive context ingestion (project corpus, long logs, big PRs) | **gemini persistent session** → digest back | protects the main agent's context; loss of cohesion is the accepted price |
| Massive ideation spread | gemini breadth → Claude curates | cheap divergence, expensive convergence |
| Judgment / adversarial review seat | opus medium–high | the one sub-agent seat that earns opus |
| Synthesis, final calls, user-facing writing | main agent | never delegated (docs/09 line) |
| Vision (structural read) | local `see` first | `see --json`; verify exact strings |
| Vision (hard/semantic) | gemini or native | |
| Image generation | local `imagine` | |
| Audio / other modality | gemini (or acquire a local model) | must be named in the plan |
| Code changes | main agent or opus seat; local code model **only behind a Judge** | unfinished-v1 precedent: 16/16 with pytest gate |

**Escalate** (tier or effort, one step at a time) when: a lower tier failed its gate or
required >2 retry rounds; the user corrected the output; stakes are irreversible/outward;
the task resists decomposition. Record *why* in one line.
**De-escalate** when: the work decomposes into scoped-verifiable units; output is
glance-verifiable; a lower tier has passed this gate before.

## 4. The plan-time obligation (the proactive half)

Any plan that involves (a) sub-agents/workflows, (b) large-context ingestion, or (c) a
modality tool (vision/imagegen/audio) **must include a Model Plan** — one line per stage:

```
Model plan:
  recon      → sonnet · low    · read-only, no nesting     (inventory, 2 agents)
  ingest     → gemini · —      · session: proj-index       (400k corpus → digest)
  verify ×N  → local fleet     · judge: pytest             ($0, throttle-immune)
  review     → opus   · high   · judgment seat
  synthesis  → main            —
```

No plan-with-sub-agents without this block. It costs four lines and is exactly the thing the
user keeps having to ask for after the fact.

## 5. Edge cases (spec'd now so agents don't improvise)

1. **Mixed task** → split lanes per stage (the Model Plan forces this); never one big agent
   because splitting felt like overhead.
2. **Nested spawns** → constraints propagate: every delegation prompt carries the ceiling
   AND the effort bound (extends the existing rule's item 3 with the effort axis).
3. **Gemini unavailable / quota / EOL'd** → fall back to sonnet fan-out; never block on
   gemini; log the fallback so the audit sees demand.
4. **Local server down** → cloud fallback, note the cost delta; don't silently absorb.
5. **Sensitive content** → local lane preferred. **Gemini is authed as the WORK account
   (`aakarsh@versable.ai`, recon-confirmed)** — until the user resolves that, no personal
   data and no non-Versable proprietary code goes to gemini. This is a data-governance
   gate, not a performance one.
6. **Ultracode** → raises fan-out *width*, changes nothing about ceiling/effort tiering
   (consistent with `contain-subagent-token-sprawl.md`).
7. **Persistent gemini session drift** → sessions are rebuildable caches keyed per project;
   claims from an old session are stale-cache-suspect (the gcc's
   `cache-externally-mutated-state` logic applies to session memory too).
8. **Model unavailable / renamed** → the rule names tiers, `config`-like pins name models;
   a missing model falls back one lane with a logged note, never upward to fable.

## 6. Exceptions & escape hatches (written down, as asked)

- **Explicit user instruction wins** — "use opus for this", "just fable it": obey for that
  scope, no re-litigating; the agent may note a cheaper lane once, then comply
  (`pushback-honesty` shape: say it once, don't argue).
- **Suggest-a-switch is encouraged; silent-switch is not.** Mid-task, an agent that sees a
  cheaper/better lane proposes it in one line; it switches only for reversible, in-scope work.
- **Mute conventions** (per existing hook patterns): `touch ~/.claude/.model-tier-off`
  (session mute) · `MODEL_TIER_OFF=1` (one-shot). The **flagship-as-sub-agent block has no
  self-mute** (same posture as the credentials guard — only the human lifts it).
- **Emergency lane:** everything degraded → main agent does the work inline and records the
  miss; delivery beats routing purity.

## 7. Enforcement — the hook nudge (because prose doesn't bind)

Per `hook-design.md`'s FP-cost framework and the `guard-subagent-output.sh` template
(recon §3 — cheap regex on the dispatch payload, stakes-scaled, telemetry, mute file):

**`guard-model-tier.sh` (PreToolUse, matcher `Agent|Task`, new):**
- `model` param **absent** → *warn* nudge: "dispatch has no model pin — sonnet default /
  opus judgment / never fable (rules/model-tier-routing.md)". Recoverable → warn tier.
- `model` = fable/flagship → **block**. Direct re-breach of the hard ceiling; the one
  block-worthy case; no self-mute.
- Prompt smells mis-tiered (research/inventory verbs + model=opus + effort high; or
  ingestion-sized context hints with no gemini/local mention) → *warn*, log-only for the
  first 2 weeks, then re-evaluate FP rate per hook-design's measure-first doctrine.
- Every fire → `warn-log.sh` telemetry + the surface-to-user suffix.

**`ExitPlanMode`/plan-time check (Phase C, measured before trusted):** plan text contains
sub-agent/workflow language but no `Model plan:` block → one advisory nudge.

**Not** a UserPromptSubmit hinter for now — prompt-time guessing has the worst FP profile;
revisit with telemetry.

## 8. Pairing tools (the friction fix)

Today gemini = a raw bash call whose output is an untrusted blob. The fix mirrors what just
worked for the lm suite — a thin wrapper with a machine contract + history:

**`gem` (new, ~q-shaped):**
- `gem "prompt"` · `pbpaste | gem summarize` · `gem --json` → `{ok, text, ms, session}`
  envelope (same consumer shape as `q --json`).
- `gem session <name>` → persistent per-project session (wraps `--resume`/`--session-file`);
  `gem ingest <paths...>` feeds a corpus into the session; `gem ask "q"` queries it. This is
  the "persistent gemini the main agent offloads context to."
- `logs/gem-history.jsonl` mirroring q-history (successes AND failures) → the weekly
  self-audit mines gemini usage/failures for free.
- Implementation detail that de-risks the deprecation: **the wrapper is the contract**;
  backing it with deprecated `gemini-cli` today (works, EOL 2026-12-18) and swapping to
  antigravity-cli/ACP later is a wrapper-internal change, invisible to callers — the same
  contracts-over-implementations principle as docs/07.
- lm-side pairing is already done (this session): `--json` everywhere, `review --findings`,
  fleet, leases, `lm index`.

## 9. Placement & rollout (per PLACEMENT.md recon)

**Phase A — the spec lands (one gcc session):**
1. `~/.claude/rules/model-tier-routing.md` — §§2–6 of this proposal (the table, decision
   rules, Model-Plan obligation, edge cases, escape hatches). `related:` links to the two
   existing rules; extends, never duplicates. Auto-loads (rules/ always loads in full).
2. One Tier-0 brief line in CLAUDE.md's core (it's a MANDATORY-with-silent-failure rule —
   burying it is the anti-pattern PLACEMENT names).
3. `~/.claude/features/model-tier-harness.md` — Tier-2 mechanics doc (hook, gem, telemetry).
4. `guard-model-tier.sh` + settings.json wiring + `rules-index.sh` regen.
5. Retitle/extend `subagent-model-ceiling.md` to point at the new rule for the effort axis
   (don't fork the ceiling).

**Phase B — pairing tools:** `gem` wrapper + history + session mgmt; self-audit extension.
Decide the account question first (edge case 5).

**Phase C — measured tightening:** plan-time nudge; 2-week FP audit of the warn heuristics;
antigravity migration decision by ~Nov 2026 (ahead of the Dec EOL).

## 10. Open questions for the user (blocking Phase B, not Phase A)

1. **Gemini account:** stay on `aakarsh@versable.ai` or re-auth personal? (Determines what
   data may flow there — edge case 5 stands until answered.)
2. **Backend bet:** wrap deprecated `gemini-cli` now (recommended — contract isolates the
   swap) or investigate Antigravity/ACP first?
3. **Default model:** `gemini-3.5-flash` is NOT persisted in any config (recon) — confirm
   it's the intended default; the wrapper would pin it explicitly via `-m`.
4. **Block appetite:** comfortable with a hard block on flagship-as-sub-agent (recommended),
   or warn-only everywhere to start?
5. **Model-Plan threshold:** required for EVERY plan with sub-agents (recommended — it's 4
   lines), or only above N agents / large-ctx?
6. **Session boundary for `gem`:** per-project (recommended, matches `~/.gemini` layout) or
   per-topic?

---
*Recon sources: `recon-gcc-surfaces.md` (300 lines) · `recon-gemini.md` (161 lines), both in
this directory. Tier containment held: 2× sonnet read-only recon, no nesting, no opus/fable
sub-agents; synthesis by the main agent.*
