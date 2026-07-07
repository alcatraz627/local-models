# Recon: existing gcc surfaces governing model/tier choice

Read-only inventory for the model-tier harness spec. Goal: know what already
exists so the new spec extends it instead of duplicating it.

## 1. The two existing tier rules

### `~/.claude/rules/subagent-model-ceiling.md`

- **Scope:** governs which model a *sub-agent dispatch* (`Agent` tool /
  Workflow `agent()`) may run on. Hard rule: "**Opus is the hard ceiling for
  sub-agents**" — the session flagship (Fable/Mythos-class) is never allowed on
  any sub-agent at any nesting depth, only on the supervising main loop.
- **Mechanism is a checklist, not a hook:** four numbered items — (1) every
  `Agent` dispatch must carry an explicit `model:` param, never inherit; (2) a
  tiering table (`sonnet` = default for research/inventory/mechanical,
  `opus` = judgment-heavy analysis/review only, `haiku` = trivial lookups,
  flagship = never); (3) "close the nesting leak" — every delegation prompt
  must tell the sub-agent either "don't spawn sub-agents" or "any sub-agent you
  spawn must carry an explicit model pin of sonnet or lower"; (4) in-flight
  agents are grandfathered.
- **Provenance:** graduated 2026-07-07 from two same-day occurrences in the
  versable-builder session ("do NOT CALL FABLE" → recurrence → user asked for
  a standing rule). This is the newest rule in the ruleset (same date as this
  recon).
- **Gaps relevant to the harness spec:**
  - Covers **cloud model tier only** (Fable/Opus/Sonnet/Haiku). Zero mention
    of local models (`lm`, the local-models suite) or Gemini/other providers.
  - Covers **effort/reasoning level**: not at all. No mention of `effortLevel`,
    thinking budget, or "xhigh"/"medium"/"low" effort settings (the session's
    own `settings.json` sets `"effortLevel": "xhigh"` — this rule doesn't
    touch that axis).
  - **Enforcement is 100% advisory** — a checklist the *dispatching* agent is
    supposed to follow. There is no hook that inspects an `Agent`/`Task` tool
    call's `model` field and warns/blocks if absent or set to the flagship.
    (Compare: `guard-subagent-output.sh` does exactly this kind of dispatch-time
    inspection for a *different* concern — see §3.)
  - Applies only to **sub-agent dispatch**, not to the top-level session model
    choice itself (e.g., picking Opus vs Sonnet vs Fable for the *main* loop
    on a given task), which is a separate decision surface with no rule at all.

### `~/.claude/rules/contain-subagent-token-sprawl.md`

- **Scope:** governs *whether to fan out at all* (orchestration/parallelism
  decision), not which model. Core test: "does this decompose into N
  genuinely-independent units that each need real read/reason work?" Small /
  mechanical / single-lookup work → inline or one bounded agent. Genuinely
  large/parallel/verification-heavy work → fan-out justified.
- Explicitly notes ultracode ("token cost is not a constraint") raises the
  ceiling but doesn't mandate a workflow for every task — a trivial task still
  goes inline even under ultracode.
- **Gap relevant to the harness spec:** this rule is about **fan-out width**
  (how many agents), not model **tier** per agent. It's the sibling axis: the
  new harness needs both "should this be N agents" (existing) and "what model
  should each agits pinned to" (existing, cloud-only) and "should any of this
  route to a local model instead" (missing entirely).

### Net gap the harness spec should fill

Neither rule says anything about: (a) local models as a tier option, (b)
effort-level selection, (c) a decision procedure/nudge that fires *before* the
dispatch to suggest the right tier (both existing rules are "remember to do
X" checklists the agent self-enforces, not hook-backed nudges), (d) top-level
session model choice (only sub-agent dispatch is covered).

## 2. Other rules touching "model" — none are about model *choice*

`rg -l "model|tier|effort" ~/.claude/rules/` returns 38 hits, but that's almost
entirely noise from unrelated senses of the words ("severity tier" S1/S2/S3 in
`corrections.md`/atone, "Tier 0/1/2/3" placement tiers throughout every rule's
frontmatter, "cost model"/"data model" as generic nouns). Narrowing to files
that actually contain the word "model" as a standalone token (`rg -l '\bmodel\b'`)
and excluding `subagent-model-ceiling.md` itself gives only:

| File | The actual "model" mention | Relevant? |
|---|---|---|
| `rules/shell.md:149` | "Fast model → `scripts/llm-mini/llm-mini.sh`" — one line in the "prefer existing scripts" table | No — just a pointer to llm-mini, not a tier rule |
| `rules/pushback-honesty.md:22` | "a wrong cost **model**" — generic noun, unrelated | No |
| `rules/00-index.md:61` | The index's own summary row for `subagent-model-ceiling` | Not a separate rule |
| `rules/cache-externally-mutated-state.md:28` | "after the **model** went warm" — refers to an Ollama model residency example (`lm warm on`), used as an illustration of externally-mutated cache state, not a tier-choice rule | No |
| `rules/testing.md:62` | "state what it deliberately does NOT **model**" — verb sense, test-simulator rule | No |
| `rules/structural-claim-without-reading-code.md:20` | "cost **model**, data flow" — generic noun | No |

**Confirmed: no other rule in `~/.claude/rules/` governs model/tier/effort
selection.** The two rules in §1 are the entire existing footprint.

## 3. Hook architecture

### The FP-cost framework (`~/.claude/features/hook-design.md`)

Core principle: weigh a hook's false-positive rate **by the cost of a false
fire**, not the raw rate, then match consequence to that cost:
- **block** (`decision:block`) — reserved for catastrophic/irreversible/shared-
  state actions (credential writes, `git push`, `rm`, prod deploys). High
  cost-of-*miss* justifies the friction of a block.
- **warn** (`additionalContext` nudge) — frequent-but-recoverable patterns
  where a false fire is cheap to dismiss (the doc's examples:
  `guard-structural-claim.sh` at ~98% FP kept as a *Stop*-time nudge because
  each false fire only costs one cheap grounding `Read`;
  `guard-speculative-export.sh` at ~35% FP floor deliberately kept warn-only).
- **nudge/log-only** — advisory signals being measured before being trusted.

**Implication for the model-tier harness hook:** a model-tier nudge (e.g.
"this dispatch has no `model:` param" or "this looks like a mechanical task
being sent to a heavy model") is a **warn-tier** case by this framework — a
missing/wrong model pin is recoverable (re-dispatch), not catastrophic, so it
should follow the `additionalContext` nudge pattern, not a block. A "trying to
dispatch the flagship model as a sub-agent" case is arguably closer to a block
candidate (it directly re-breaches the hard ceiling rule), same shape as
`guard-anthropic-credentials.sh`'s "no self-liftable mute" posture.

### The hinter pipeline (`~/.claude/features/hinter-pipeline.md`)

Separate mechanism: `UserPromptSubmit` hook chain
(`~/.claude/scripts/hint-injector.sh`) runs hinters from `~/.claude/hinters/`
in sort order, each optionally emitting `additionalContext`. Currently only
one hinter is active (`00-autocorrect.sh`, typo correction). Prompts are
**never rewritten**, only annotated. This is the pattern for a nudge that
should fire on the *user's prompt* (e.g., "this prompt smells like a job for
the light/local lane") rather than on a tool call — a different insertion
point than PreToolUse.

### PreToolUse hooks currently registered (from `~/.claude/settings.json`)

The only existing hook that inspects an `Agent`/`Task` dispatch (matcher
`"Agent|Task"`) is **`guard-subagent-output.sh`** — read in full
(`~/.claude/scripts/hooks/guard-subagent-output.sh`). It is the closest
architectural precedent for a model-tier nudge and worth copying the shape
of:
- Reads `tool_input.prompt` (falls back to `.description`) from the PreToolUse
  JSON payload — the *only* thing inspectable at dispatch time.
- Two cheap heuristics (regex over the prompt text) decide whether to fire at
  all; no LLM call, no external state.
- **Stakes-scaled escalation**: calls `stakes-tier.sh <cwd>` to check if the
  repo is high-stakes; only blocks when (material-verb detected) AND (repo is
  high-stakes) AND (no persistence instruction at all). Everything else falls
  through to an advisory `additionalContext` nudge.
- Emits `{hookSpecificOutput: {hookEventName: "PreToolUse", additionalContext: $c}}`
  for the warn path, `{decision:"block", reason:$r}` for the block path.
- Appends a fixed suffix to every nudge: "→→ SURFACE this to the user in your
  reply as a bordered callout (rules/surface-hook-nudges-to-user.md)" — because
  (per that rule) a PreToolUse `additionalContext` reaches the agent only,
  never the user's transcript directly; the agent is the only relay.
- Telemetry via `~/.claude/scripts/hooks/warn-log.sh --hook <name> --action
  block|nudge --heeded unknown` on every fire (for later FP-rate audits, per
  the hook-design.md worked examples).
- Self-mute convention: `touch ~/.claude/.subagent-output-off` (file check) or
  `SUBAGENT_OUTPUT_OFF=1` (one-shot env var) — both patterns repeat across the
  other guard-*.sh hooks in the directory.

**All other PreToolUse hooks in the directory** (confirmed by directory
listing + settings.json wiring, not individually read — names/matchers only):
safe-delete.sh (Bash, blocks `rm`), guard-user-commit.sh (Bash, blocks commits
in this repo without secret-scan), guard-git-push.sh (Bash), guard-anthropic-
credentials.sh (Bash|Edit|Write|MultiEdit, hard-blocks credential writes per
`rules/never-modify-anthropic-credentials.md`), block-nested-claude.sh
(blocks `~/.claude/.claude/` paths), prefer-ripgrep.sh (Bash, blocks raw
`grep`), plus ~15 `guard-*`/`prefer-*`/`warn-*` scripts that are warn/nudge-
only by naming convention (`warn-*`, `prefer-*` = advisory; `guard-*` is mixed,
some block some warn — `guard-subagent-output.sh` above shows one `guard-*`
can do both depending on stakes). Two structural-claim-style hooks
(`guard-structural-claim.sh`, `guard-absence-claim.sh`) run at **Stop**, not
PreToolUse — they audit the agent's own response text after the fact, a third
insertion point distinct from PreToolUse-on-dispatch and UserPromptSubmit-on-
prompt.

## 4. Glossary + memory terms

`~/.claude/GLOSSARY.md` (User Shorthand table) defines, each with a canonical
memory-file pointer:
- **efficacy** — "effectiveness/quality of output relative to the effort *they*
  spend — not raw speed." Canonical: `memory/global/feedback_efficacy_over_speed.md`.
- **one-shotting** — "Hoping a task lands in a single unplanned attempt... a
  *failed* one-shot wastes more than structured plan→implement→review."
  Canonical: `memory/global/feedback_structure_over_oneshot.md`.
- **ease–effort–output triad** — "the user's mental model for routing a task
  to a tool, weighing ease of invoking, their own effort, and the output
  quality the task needs." Canonical: `memory/global/user_work_routing_triad.md`.
- **"just use chatgpt" (mode)** — the light-path escape hatch entry, same
  canonical file as the triad.

All three canonical files exist and were read in full:
- `feedback_efficacy_over_speed.md` — lead comparisons with efficacy, not
  speed; count total effort including rework; "willing to dedicate resources"
  is an efficacy lever, not a speed one.
- `user_work_routing_triad.md` — two-lane model: "just use chatgpt" (light,
  one-off, low-stakes) vs "the agent" (structured, must-be-right, multi-file).
  Explicitly ties to the local-models project: "the heavy local agentic tier
  exists to serve the STRUCTURED lane offline; one-offs stay on ChatGPT/small
  `lm` (`q`)."
- `feedback_structure_over_oneshot.md` — plan→implement→review as default for
  non-trivial work; one-shotting only fine for genuinely trivial one-offs;
  explicitly marked "Candidate for graduation to a `rules/*.md` behavioral
  mandate (pending user confirm)" — i.e., this is itself an unpromoted rule
  candidate, relevant context since the harness spec is adjacent territory.

**Implication for the harness spec:** the ease–effort–output triad and the
efficacy-over-speed preference are the *existing* decision framework a
model-tier chooser should plug into — the harness isn't inventing a routing
philosophy, it's operationalizing one that's already established as user
doctrine but currently unenforced by any tool/hook.

## 5. How local models and llm-mini are currently presented to agents

### `~/.claude/features/llm-mini.md` (Tier 2 feature doc)

Presents `llm-mini` as a **fast sub-second** utility model (Ollama llama3.2
local, Haiku cloud fallback) for: session titles, doc lookups, command
composition, short summaries. Explicit anti-scope: "Do NOT use llm-mini for:
reasoning, code generation, multi-step analysis." Four surfaces (CLI, chat
REPL, MCP `mcp__llm-mini__ask`, hook-callable `mini_quick`). This is a
**different, older/lighter tool** than the local-models project's `q`.

### `~/.claude/features/local-models.md` (Tier 2 feature doc, this project)

Presents the `~/Code/local-models` suite: `q` (quick answer), `imagine` (image
gen), `see` (local vision), `review` (local code review), `warm` (residency
toggle), `lm` (front door). Explicit good/bad task split: "Good offload tasks
(proven, glance-verifiable): commit messages, titles, terse one-command
lookups, image prompt enhancement/critique. **Not** suitable for multi-step
reasoning or code generation — that stays with cloud Claude." Points to
`~/Code/local-models/docs/STATE.md` (current state) and `docs/GOALS.md`
(per-command goals/rationale) as the living source of truth — this recon did
not re-read those since they're already the project's own docs, not gcc-side.

Note also (from the per-project memory index already in context):
`local_agentic_tier_use_case.md` states the heavy local-agentic tier's bar is
"Claude-Code-like multi-file work (not one-offs); dedicate resources iff
efficacy is ballpark of cloud, else route to cloud," candidate model
Qwen3-Coder-Next 80B-A3B. This is project-local goal-setting, separate from
(but directly feeding) the harness's tier-selection logic.

**Gap:** both feature docs describe *what the tools do* — neither is wired
into any rule or hook that would nudge an agent, at decision time, toward
"this task is light → use `q`/llm-mini" or "this task is heavy local-capable
→ consider the local agentic tier" vs. cloud. The routing logic lives only in
prose (the triad memory file) with no mechanical prompt.

## 6. Placement guidance (per `~/.claude/PLACEMENT.md`)

Two-axis rule: **category** (`rules/` = behavioral mandate, `features/` = how
a subsystem works, `conventions/` = output/authoring standard, root = indices/
state) × **tier** (0 = inline in CLAUDE.md always, 1 = brief+pointer, 2 =
pointer-only, 3 = LOOKUP.md only). Key mechanics:
- For `rules/`, tier is **advisory only for loading** — Claude Code natively
  auto-loads every file under `rules/*.md` in full every session regardless
  of tier (this is a documented special case, "Loading reality" section).
  Only a `paths:` frontmatter glob actually gates loading (project/language-
  scoped rules). A new model-tier-harness rule with no `paths:` would load
  every session in full, same as the two existing tier rules.
- 15-line rule: content >15 lines must have its own sub-file regardless of
  tier — a harness spec is certainly >15 lines, so it's a dedicated file no
  matter what.
- 3 hard anti-patterns most relevant here: don't duplicate content that
  already lives in `subagent-model-ceiling.md`/`contain-subagent-token-
  sprawl.md` (link via `related:` instead); don't bury a MANDATORY rule at
  Tier 2 (if the harness introduces a new hard mandate, it's Tier 0/1); don't
  create nested subdirectories (flat `rules/`, `features/`, `conventions/`
  only, sub-categorize by filename prefix).

**Recommended placement for the three artifact types the spec will likely produce:**

| Artifact | Category | Tier | Rationale |
|---|---|---|---|
| A new/extended rule (e.g. "local-tier routing is mandatory before X") | `rules/` | 0 or 1 if genuinely MANDATORY and silent-failure-risky; else 2 | Follows the same shape as `subagent-model-ceiling.md` (Tier not stated there but it's inline-summarized in CLAUDE.md's Tier-0 core as `rules/subagent-model-ceiling.md` is NOT currently listed in the CLAUDE.md Tier-0/1 tables shown to this session — it lives at Tier-2-or-implicit via the always-loaded `rules/*.md` mechanism only) |
| A new feature doc explaining the harness mechanics (how the tier chooser works, what it inspects, how to invoke it) | `features/` | 2 (pointer + triggers, e.g. `topic:model-tier`, `tool:lm`) | Same shape as `features/llm-mini.md` / `features/local-models.md` — on-demand, not always-loaded |
| A new PreToolUse/UserPromptSubmit hook for the nudge | `~/.claude/scripts/hooks/` (or `hinters/` if prompt-time) | n/a (hooks aren't tiered, they're wired in `settings.json`) | Should reuse `guard-subagent-output.sh`'s shape: cheap regex heuristics, `warn-log.sh` telemetry, `additionalContext` + the surface-to-user suffix, a `.{name}-off` mute file + one-shot env var, and per hook-design.md should default to **warn**, escalating to block only for the "flagship model re-breach" unambiguous case |

Also relevant: `rules/00-index.md` is a **derived** file — after adding/renaming
any `rules/*.md`, regenerate it with `bash ~/.claude/scripts/rules-index.sh`
rather than hand-editing (its own README states this).

## Abstract (5 bullets)

- Exactly two rules govern model/tier choice today: `subagent-model-ceiling.md`
  (Opus-max ceiling for sub-agent dispatch, checklist-enforced, cloud-only,
  zero effort-level or local-model coverage) and
  `contain-subagent-token-sprawl.md` (fan-out-width decision, not model tier).
  Confirmed via full-tree grep that no other rule touches model selection.
- Hook precedent for a dispatch-time model-tier nudge already exists:
  `guard-subagent-output.sh` (PreToolUse, matcher `Agent|Task`) inspects the
  dispatch prompt with cheap regex, stakes-gates block vs warn via
  `stakes-tier.sh`, and is the template to copy for a "no model: pin" or
  "flagship-on-subagent" nudge.
- `hook-design.md`'s FP-cost framework says a missing/wrong model pin is a
  **warn-tier** case (recoverable via re-dispatch); only the flagship-ceiling
  re-breach looks block-worthy, mirroring `guard-anthropic-credentials.sh`'s
  no-self-mute posture.
- The user's existing routing doctrine (efficacy-over-speed, the
  ease-effort-output triad, anti-one-shotting) already answers "when should
  work go light vs structured, local vs cloud" in prose
  (`memory/global/*.md` + `GLOSSARY.md`) but has zero mechanical enforcement
  today — the harness's job is to operationalize doctrine that already exists
  rather than invent new philosophy.
- `local-models.md` and `llm-mini.md` are both purely descriptive feature docs
  with an explicit good/bad task split but no hook or rule wired to them;
  PLACEMENT.md dictates a new rule goes in `rules/` (auto-loads in full
  regardless of tier unless `paths:`-scoped), a new mechanics doc goes in
  `features/` at Tier 2, and any new hook lives in `scripts/hooks/`
  (or `hinters/` for prompt-time) wired through `settings.json`.
