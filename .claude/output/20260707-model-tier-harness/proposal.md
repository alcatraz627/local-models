# Model-Tier Harness — detailed spec proposal

v2 — user-reviewed 2026-07-07 (session local-agent-9c): all 6 questions answered (§10),
effort matrix calibrated, vision lanes kept complementary, `lm gemini` naming decided,
image-tool observability SHIPPED (§7.5). Grounded in: the user's directive notes (Task
#18), `recon-gcc-surfaces.md`, `recon-gemini.md`. Recon cost: 2× sonnet, read-only.

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
- Sub-agent effort **must not exceed** the main agent's effort when the main is high/xhigh.
- **Effort tolerance scales inversely with model cost** (user calibration 2026-07-07):
  sonnet at medium/high is cheap enough to be liberal with — go `high` when the task
  benefits (if the tier supports it); reserve sonnet-`low` for frequent/numerous dispatches
  (wide fan-outs, per-item workers). Opus stays conservative at `medium` by default,
  `high` only for genuine judgment seats. `xhigh` on any sub-agent requires explicit user
  sanction.
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
| Vision | **complementary lanes, none ruled out** | native Read is fine (highest fidelity, already-in-context); `see` is practically free and gives a second perspective; gemini is abundant. Standalone "read this image" → `see` first, verify exact strings; in-conversation → native is natural. See §7.5 |
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

- **Explicit user instruction wins — after honest deliberation.** On "use opus for this" /
  "just fable it", the agent is *encouraged* to push back with a concrete alternative
  ("sonnet-high would cover this because X — want that instead?") and let the user accept
  or decline. What it may NEVER do is switch models without the user's explicit
  confirmation. Deliberate, propose once, then execute the user's call
  (`pushback-honesty` shape: evidence-backed, one round, no re-litigating).
- **Suggest-a-switch is encouraged mid-task too; silent-switch never.** An agent that sees
  a cheaper/better lane proposes it in one line and waits for the nod on anything
  model-level; lane-internal choices (which local intent, which judge) stay autonomous.
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
- `model` = fable/mythos-class → **hard block, no self-mute** (user-confirmed 2026-07-07).
  The rationale is precise: this tier is **priced per-token outside the subscription cap**
  — a sub-agent on it multiplies uncapped spend. The block keys on
  *subscription-uncovered pricing*, not "newest model": when Opus was the flagship the
  user didn't mind, and if a future flagship is cap-covered, the block is revisited, not
  auto-extended.
- Prompt smells mis-tiered (research/inventory verbs + model=opus + effort high; or
  ingestion-sized context hints with no gemini/local mention) → *warn*, log-only for the
  first 2 weeks, then re-evaluate FP rate per hook-design's measure-first doctrine.
- Every fire → `warn-log.sh` telemetry + the surface-to-user suffix.

**`ExitPlanMode`/plan-time check (Phase C, measured before trusted):** plan text contains
sub-agent/workflow language but no `Model plan:` block → one advisory nudge.

**Not** a UserPromptSubmit hinter for now — prompt-time guessing has the worst FP profile;
revisit with telemetry.

**Dispatch telemetry (user-confirmed):** `guard-model-tier.sh` also *logs every*
`Agent`/`Task` dispatch — `{ts, session, model, effort, prompt_head}` →
`~/.claude/logs/model-dispatch.jsonl` — so tier choices and their token/efficacy outcomes
are reviewable data, not anecdotes. Same pattern as the image-read log below.

### 7.5 Image-tool observability (SHIPPED 2026-07-07, ahead of the spec)

- `~/.claude/scripts/hooks/log-image-reads.sh` (PostToolUse · Read, live + verified): every
  Claude-native image read logs `{ts, session, file, bytes, w, h, est_tokens}` to
  `~/.claude/logs/image-reads.jsonl` (`est_tokens ≈ w·h/750`). Mute:
  `~/.claude/.no-image-read-log`.
- `~/.claude/scripts/image-tools-review.sh` + gcc-schedule **`image-tools-review`**
  (one-shot **Tue 2026-07-28 15:00**, calendar-visible): 21-day digest of native reads
  (est token spend, per session) vs `see` vs `imagine` vs gemini-wrapper usage → routing
  judgment or the head-to-head test.
- **Comparison notes that survive** (user asked): the original fidelity audit
  (`parse-comparison.md`, claude-instances session) is NOT on disk — only its citations in
  `.claude/output/20260625-vision-lenses/skeptic.md` and the `docs/08` §Outcome (local VLMs
  invent controls/misread themes; native = fidelity reference; `see` = gestalt read, verify
  exact strings). Sufficient for notes; not a designed head-to-head.
- **The head-to-head test (devise when review data is ambiguous):** probe-style fixture —
  N labeled images with a ground-truth key, run through native Read / `see` / gemini,
  graded on recall + fabrication + cost-per-read. Reuses the unfinished-v1/probe pattern.

## 8. Pairing tools (the friction fix)

Today gemini = a raw bash call whose output is an untrusted blob. The fix mirrors what just
worked for the lm suite — a thin wrapper with a machine contract + history.

**Naming (deliberated, user flagged `gem` ↔ Ruby's `/usr/bin/gem` conflict):**
**`lm gemini`** — a subcommand of the existing front door, machinery in `lib/gemini`.
Reasoning: the primary caller is an agent, not human fingers, so verb length is irrelevant
while discoverability and convention-sharing are everything — as an `lm` subcommand it
appears in the `lm` overview, inherits `_lib.sh` (colors/help/history), lands in
`lm timeline` and the weekly self-audit for free, and adds zero PATH surface. The precedent
already exists: `lm opencode` wraps a non-local surface because `lm` has become the
model-tooling front door, not strictly "local". A standalone `lm-gemini` name buys nothing
over this; if interactive brevity is ever wanted, a one-line PATH alias can point at it.

**`lm gemini` (new):**
- `lm gemini "prompt"` · `cat doc | lm gemini summarize` · `--json` → `{ok, text, ms,
  session, model}` envelope (same consumer shape as `q --json`).
- **Model pinned explicitly to `gemini-3.5-flash`** on every call (user-confirmed default;
  recon found no persisted default, and other gemini models "have not been so reliable").
- `lm gemini session <name>` → persistent session (wraps `--resume`/`--session-file`),
  **per-project boundary** (user-confirmed); cross-project references are allowed and
  manual — Claude passes the pointer/summary from one session into another explicitly.
- `lm gemini ingest <paths...>` feeds a corpus; `lm gemini ask "q"` queries it — the
  "persistent gemini the main agent offloads context to."
- **Availability contract (user-confirmed):** if gemini/auth is unavailable (Google auth is
  shaky), the wrapper fails with a structured `gemini_unavailable` error, the agent FLAGS
  it to the user in the reply, and falls back to the Claude family / lm lanes. Never block
  on gemini.
- **Wrapper-only access (user-confirmed, becomes a rule line):** Claude never invokes the
  `gemini` binary directly — always through `lm gemini`. That's what makes the
  deprecated-backend swap (gemini-cli today, EOL 2026-12-18 → antigravity/ACP later) a
  wrapper-internal change with zero caller churn.
- `logs/gem-history.jsonl` mirroring q-history (successes AND failures) → self-audit +
  the image-tools review mine it for free.
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

## 10. Decisions record (user, 2026-07-07) — all six questions answered

1. **Account:** stay on whatever is authed (Google auth is shaky anyway). If gemini is
   unavailable, FLAG it to the user and fall back to Claude family / lm. (The hard
   data-governance gate in edge case 5 is relaxed to standing judgment: still no secrets,
   per existing rules.)
2. **Backend:** wire `gemini-cli` now (Antigravity "is being a pain to set up"). Swap-out
   later must be cheap → **Claude never calls gemini directly, wrapper only.**
3. **Default model:** `gemini-3.5-flash`, explicitly intended (other gemini models "not so
   reliable"); the wrapper pins it per call.
4. **Block:** HARD block on fable/mythos-as-sub-agent, no self-mute. Rationale = uncapped
   per-token pricing, not flagship-ness; revisit only if a future flagship is cap-covered.
5. **Model Plan:** required in EVERY qualifying plan + dispatch telemetry to gcc logging
   (`model-dispatch.jsonl`) for token/efficacy review. Even when the instinct doesn't
   change, the explicit thought is the point.
6. **Session boundary:** per-project; cross-project reference allowed via manual handoff
   (Claude carries the pointer).

**Remaining open questions (small, non-blocking):**
- **Vision head-to-head test:** the old fidelity audit survives only as citations
  (§7.5) — run the designed test NOW as part of Phase B, or wait for the Jul-28 review
  data to decide whether it's needed?
- **Dispatch-telemetry review:** fold `model-dispatch.jsonl` into the same Jul-28 review,
  or leave it for the weekly consolidation to surface?
- **`lm gemini` naming:** decided here as an lm subcommand (see §8 deliberation) — veto if
  you'd rather have the standalone `lm-gemini` binary name.

---
*Recon sources: `recon-gcc-surfaces.md` (300 lines) · `recon-gemini.md` (161 lines), both in
this directory. Tier containment held: 2× sonnet read-only recon, no nesting, no opus/fable
sub-agents; synthesis by the main agent.*
