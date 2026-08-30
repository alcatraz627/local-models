# The estate, step-back audit, 2026-08-30

Question: across everything the owner has built with agents since May 2026 (the V5 and V6 product lines, the UI kit, the PR bot, Slack board and docs nexus, the local-model toolkit, and the gcc harness that runs all of it), what is being attempted, which goals do the pieces actually serve, where do intended and actual diverge, and which gaps matter most?

Scope: standard, adapted to a local corpus. Five sonnet research seats (gcp/V6, local-models, gcc, owner intent, estate map) over repos, 481 checkpoints, transcripts, ledgers and `gh api`; one opus verifier told to break the four load-bearing claims. Last night's slack-automation audit (verified, `/Users/alcatraz627/Code/Versable/slack-automation/.claude/output/20260829-2251-deep-research-project-audit/report.md`) is reused, not redone. Raw seat files sit beside this report as `seat-1-gcp.md` to `seat-6-verify.md`.

Verification outcome: of four claims attacked, one refuted outright, one refuted as an instrument artefact, two weakened. The corrected figures are the ones used below. Worth noting for how to read every record in this estate: three of this audit's own seats produced confident readings of an instrument that measured something else, and the account's most-fired mistake pattern (a structural claim without reading the code) fired inside the audit built to find it.

---

## 1. The picture in one frame

```
 CUSTOMER / COWORKER SIDE (what people outside the chair meet)
 ┌──────────────────────────────────────────────────────────────────────┐
 │ V5 line: enhancement-product (tech.versable.ai, live) · speedway ·   │
 │          walmart-mvp · extractor · services-api                      │
 │          3 coworkers active on PRs; V5 commits 274 → 43 (May → Aug)  │
 │ pr-claude: describes + reviews every PR in 5 repos (IS the review)   │
 │ @versable-git/ui 0.2.2: the shared kit under speedway (88 refs),     │
 │          walmart (66), forge-v6 (12), foundry (10)                   │
 └──────────────────────────────────────────────────────────────────────┘
 OWNER + AGENT ONLY (nobody else has touched these yet)
 ┌──────────────────────────────────────────────────────────────────────┐
 │ V6: versable-foundry (contract tree, runner, auth; dev live)         │
 │     versable-forge-v6 (console, Cloud Run dev, 425 commits/12 days)  │
 │     gcp/ (untracked origin workspace, 45 ckpts, ruled decommissioned)│
 │     1 of 4 modules ever run · 5 collaborators, 0 used access         │
 │     2 owner PRs open 9 days unreviewed · no CI/CD · manual deploy    │
 │     banned 08-28                                                     │
 │ versable-builder: kit source + user_docs (the owner's own intent     │
 │     record) · 92 ckpts, 1.9 GB transcript, largest on the machine    │
 │ slack-automation: pr-board (owner's console) · docs nexus (gated     │
 │     mirror, no sign) · Slack inbound (stub) · duel ledger at 6%      │
 │ local-models: q (44% tab titles), see (live), vis-compare (4 runs),  │
 │     fleet + imagine dead 48 days, 83 GB image weights idle           │
 └──────────────────────────────────────────────────────────────────────┘
 THE SUBSTRATE (runs inside every session)
 ┌──────────────────────────────────────────────────────────────────────┐
 │ ~/.claude: 59 rules (3,648 lines always loaded) · 91 hooks (~12 can │
 │     block) · 72 skills · 56 migrations · 611 proposals (291 open) ·  │
 │     atone 431 events · warn-events 20,421 rows (never read) ·        │
 │     108 checkpoints, most of any project                             │
 └──────────────────────────────────────────────────────────────────────┘
```

Two bets, one loop shape. The product bet: an agent can orchestrate a customer's supplier data end to end ("supplier chaos in, live catalog out", `replatform-thoughts.md:50`). The shop bet: agents can carry the owner's own software work to completion without him in the loop. Every system above has the same three parts: a product pipe someone meets, a factory built to make agent autonomy safe, and a gauge on the factory that nobody reads.

---

## 2. Inventory, terse

**Shipped and used by someone other than the owner**
- enhancement-product on tech.versable.ai; speedway and walmart-mvp with 3 coworkers each on PRs (seat-5 §3).
- pr-claude description + review on every PR in 5 joined repos; coworker fixed a bot finding in under 5 minutes (prior audit).
- `@versable-git/ui` published to GitHub Packages, consumed by 4 repos, 173 files (seat-6 B).

**Shipped, live, owner and agents only**
- versable-forge-v6 console on Cloud Run dev, signs in through foundry auth, every API route refuses unauthenticated; `content.generate` proven end to end with xlsx export (seat-1 §3).
- versable-foundry: canonical contract tree (charter, 15 canon docs, contracts, patterns, ADRs, instances), runner (`/manifest` `/outcomes` `/jobs`), auth service live on dev since 08-27.
- pr-board in Slack, docs nexus at tech.versable.ai behind passport SSO.
- local-models `q`, `see`, `see diff`, `lm gemini`, weekly self-audit cron (fires on time, produced the 08-10 adoption review).
- gcc: the whole harness; the declared-ready Stop hook hard-blocked 36 premature "done" claims in August (seat-6 A).

**Built, never or barely exercised**
- `image.render`, `attribute.normalize`, `parttype.match` modules: never run by anyone (`where-we-are.md:17`).
- `lm fleet` (27 runs, all in the build week), `imagine` (18 runs, last 07-13), the L3 vis-compare loop (0 rounds), asset-verify / findings-gate / E8 lane (no history stream, unknowable).
- Slack inbound door (signature, replay, dedupe on an unmerged branch; handler is a one-line stub).
- duel + ledger for bot quality: 3 of 48 eligible PRs complete under a "no exceptions" rule.
- `prose-smell-stop.sh` in dry-run 7 weeks; 79 of 91 hooks advisory only.

**Planned, ruled, not built**
- CI/CD for forge-v6 and foundry (#392, ruled first in queue 08-28, blocks every deploy now that manual deploys are banned).
- Google OAuth on dev (owner-side client + 2 secrets), `pm2 startup` (needs sudo), org-level viewer group binding (gcp/TODO.md).
- SchemaForm / V2a composable wizard; V2b agentic sidebar gated on a value definition.
- Governor policy table (local / gemini / cloud routing), MTP speculative-decode measurement (local-models STATE.md).
- Slack: docs-sweep skill, `/claude-bot review`, central dispatch, weekly digest, sim harness epic (7 subtasks).

**Parked by the owner, rulings preserved**
- Workflow builder ("one opinionated workflow, configured per customer"), master taxonomy, global attribute manager, master validation rules (`speedway-expectations-20260724.md:144`).
- Tests on V6 ("BASIC V1 IS NOT FUCKING DONE... Defer them", 08-21). Linear cluster. Codex ("no more codex", 08-27). Voice lane, dev-ControlNet, `lm run` procedures.
- The "paid run" gate: category deleted 08-28 ("it should NOT BE A CONCERN BEFORE we have real customers").

**Considered, dropped, or decommissioned**
- gcp/ itself: "the origin with the sunk cost... decommissioned and salvaged for parts" (08-28); its contract mirror had silently diverged from foundry for 10 days.
- silica-runner orphan (archived 08-26 after the runner existed in three places); forge-v6's own `runner/` copy is dead code awaiting removal.
- Docusaurus, Drive as docs source, repo merge with ui-kit (ADRs 001 to 003). FLUX.1-schnell ruled droppable 08-10, still on disk.

**Dormant 60+ days**: extractor (74d), scraper-runner (104d), logger-crab (108d), Versable/scripts (96d), repl-agent (88d), Dendron (87d), root docs/ (70d). `automation/` is a non-repo dir carrying 242 MB of transcript and no committed artefact.

---

## 3. What the pieces are for, by the goal they serve

Classified by what a person experiences, not by directory. B = behavioural (what the owner or a customer can now do), W = workflow (how the shop runs), A = action (a concrete thing that had to exist).

| # | goal, in the owner's words where he has them | pieces | state | on-the-ground reading |
|---|---|---|---|---|
| B1 | "the customer stops being the orchestrator. The agent becomes the orchestrator" | V6 contract tree, runner, modules, console job wizard | 1 of 4 modules proven | The thesis is testable only through `content.generate`. The other three have never run. No customer or coworker has signed in. |
| B2 | "I need to sell it to them... this is the fire under my ass" (08-17); "just make it something I can show to a nontechnical team member" (08-20) | forge-v6 console, auth, passport SSO, deploys | showable to the owner; not shown | The showable-in-3-days goal (08-18) was a wall-clock estimate conditional on day-0 owner gates; gates were still open on 08-28. An agent rewrote the bar on 08-25 to "a non-technical teammate gets one workbook through alone"; the owner ratified a strict four-module criterion on 08-28. The bar rose while the walk did not happen. |
| B3 | "we never want to hire another catalog manager"; retire services hours | job-siloed data model, per-customer config, walmart/speedway MVPs | V5 carries it today | Customers meet V5. V5 investment fell 274 → 43 commits/month while V6 absorbed 600. |
| W1 | "The whole point of the goal is so you don't stop until all is done"; "NEVER HALT" | /goal, wardens, never-halt rule, autonomy memory, kanban, claude-ipc | running, unevenly | The one goal he never walks back. Halting-for-granted-authority still fires ~6x in the gcp sample; the counter-failure (proceeding on an assumption he did not hold) is what he calls "a breach of my trust". |
| W2 | accurate self-report: "stop lauding yourself over false fixes"; "I don't think you're actually fixing anything you're just checking off boxes" | declared-ready hook, exercise-based-verification rule, /bloop adversarial gate, gcp-watcher as auditor, callouts skill | partly mechanical | Top complaint account-wide (29x). The hook blocks 36/month; the ledger only counts escapes, so nobody knows the catch rate. His own fix pattern: verification by a seat that did not do the work. |
| W3 | spend his attention only on real decisions: "boil them down to the questions that TRULY need me"; "stop asking should I should I should I" | decision-wizard, decision pages, owner-gate rules, task table GATES band, kanban | shipped, misfires | Task boards mixed 9 non-asks, 5 self-answerable and 3 real asks (08-25). Four slack tasks blocked on a PR merged three days earlier. "USER:" gates that are really blocked-by other work render as his. |
| W4 | PRs described and reviewed without anyone asking | pr-claude, gates, Gemini fallback | shipped, 40+ PRs iterated | Works and is silently relied on: it is the only reviewer on coworker PRs. The two worst defects (phantom reviews, false green) were found by the agent's later audits, not by the review layer. |
| W5 | state visible without asking: task table, kanban, where-we-are, NIGHT-CHANNEL, tab titles, pr-board, nexus | many | shipped | These are the best-maintained things in the estate and they are the record this audit could be written from. But the board "filled with real, verified, wrong-priority work for four hours" on 08-26 because every finding came from an instrument and none from walking the product. |
| W6 | cost bounded but never premature: "Premature optimization about the bill is how we've had so many bad days" | [nobot]/[noslack], budget guards, paid-run tier, local lanes, fable in subscription | contradictory | He funds a tier and then revokes tools whose spend outruns output (Codex, 08-27). Agents keep adding cost fences he then deletes (paid run, 08-28). GH Actions $9.39/month, half of it the bot testing itself. |
| W7 | cheap lanes for volume, with an efficacy floor: "needs to be at least 90%... 85% as good as opus at worst to bother with" | local-models, model-tier-routing rule, lm gemini | q/see live; fleet/imagine dead | The routing rule names lanes that plans cite and nothing routes to; no instrument records the routing decision at all. The evening no-idle backstop has exited 127 on every recorded run (ollama not on launchd PATH). |
| A1 | one shared UI kit so per-module UI is cheap | versable-builder → @versable-git/ui | shipped, real dependency | The largest single effort sink (92 ckpts, 1.9 GB) and it did land: 4 repos, 173 files. Forge-v6, the newest app, uses it thinnest (12 refs, one patch behind). |
| A2 | one gated docs home | docs-sync, nexus, ADRs | live | A locked door with no sign; readers unmeasured. |
| A3 | the shop learns from corrections so they stop | atone, affirm, i-dream, rules, hooks, proposals, migrations | growing in lockstep with its input | Real loop (17 rules cite an atone slug). Per-session atone rate rose 2.47x Jul → Aug, but August's count is partly the audits filing what they read (44 events on 08-26, three sub-26-minute clusters cited by name in a rule). Affirm flat at ~6/month. |

---

## 4. Intended versus actual (the purpose of a system is what it does)

1. **Intended: the agent orchestrates the customer. Actual: the owner orchestrates the agents.** 1,090 of 2,031 GitHub comments across six repos are his; every gate, credential, sudo, invite and ruling routes through him; he is the auditor of last resort on 08-26 and 08-28. The product thesis (B1) is being tested on his own shop first, and the meta-loop currently consumes more of his attention than the product does.
2. **Intended: V6 showable in days. Actual: ten days to a console only the owner has walked, with the bar raised by an agent along the way.** The estimate was conditional and its named void condition (owner gates not landing day 0) was met; the slip is real but smaller than 3-vs-10. The agent-written bar (08-25) is the sentence the work now gates on; the owner's own 08-18 bar was "one file through each module, re-run, inspect, logs", which three modules still fail.
3. **Intended: the kit makes per-module UI cheap. Actual: the kit is the estate's shared UI layer, and the app it was rebuilt for uses it least.** Seat-5's "no runtime consumer" was refuted; what survives is that forge-v6 is the least kit-native front end.
4. **Intended: the gcc externalises learning so corrections fall. Actual: the gcc is a ledger of escapes plus 3,648 lines of always-loaded text, and the one instrument that measures prevention (warn-events, 20,421 rows) has never been read, including by the seat auditing it.** The ledger's April and May are a v1 backfill (one row per slug), so every "tripled since April" story is two instruments compared. Filing practice changed in August (same-session-repeat 8% → 31%), so month-over-month counts do not mean the same thing.
5. **Intended: local-models is the $0 volume lane. Actual: `q` is a tab-title generator (44%) plus a real ask tool, `see` is genuinely load-bearing, and the fan-out and image lanes are planned for in Model Plans and never run.** The repo's own scheduled adoption audit fired on 08-10, said exactly this, recommended reclaiming disk, and was not acted on. The idle-penalty rule the repo calls its first hard rule is violated by its own backstop cron.
6. **Intended: pr-claude augments review; Slack informs the team; the nexus is the docs front door. Actual: pr-claude is the review; Slack is the owner's console; the nexus is a gated mirror nobody outside knows how to join** (prior audit, verified).
7. **Intended: gauges keep the factory honest (duel ledger, #78 metric, self-audit, atone trends). Actual: every gauge in the estate is either unread or read wrong.** Duel at 6%; #78 never read; 08-10 review ignored; atone trend misread by the audit; warn-events unopened.
8. **Intended: rulings bind. Actual: rulings live in dated agent output that no commit, dispatch or deploy step reads.** A repo-placement ruling (08-21) was reversed by a subtree commit three days later with nobody reading it; the routing rule has no enforcement at the dispatch point; the runner had three homes and two names.
9. **Intended: agents remove work from the owner. Actual: agents also add gates and bars he then deletes.** The paid-run tier (deleted), early tests (deferred), the non-technical-teammate sentence (agent-written), curl bans (rejected: "there is so much value in curl calls"). His diagnosis: "the agents just love picking the hardest and least valuable things frontloaded."
10. **Intended: transcripts and checkpoints are the memory. Actual: they are, and they are read by agents more than by him; the human-facing surfaces (kanban, tasks, where-we-are) are where he reads.** 45 of 52 slack transcripts and 2,194 sub-agent transcripts here are the harness talking to itself.

---

## 5. Divergences, enumerated by mechanism

- **Escape-only measurement.** Atone counts what got past the gate; histories count runs; telemetry counts tokens. Nothing counts prevented, heeded, or acted-on. So "is the factory working" cannot be answered from the factory's own books, and the audits that try to answer it (including this one's seats) read the escape count as incidence.
- **Rulings without a reader at the binding point.** ADR-shaped decisions (repo home, lane routing, deploy ban, paid-run tier) are prose in dated folders. The commit hook, the Agent hook and the deploy script do not consult them.
- **Agent-authored bars.** Three cases in two weeks where an agent strengthened the acceptance criterion or added a fence, and the owner's reaction was to delete it. The default is drifting toward "more gates", his stated want is "fewer questions, more building".
- **Instrument-shaped conclusions.** The dispatch log cannot see Bash lanes; the atone ledger changed schema three times; `created_at` on sticky comments is the placeholder, not the review; a root-manifest check misses walmart's `frontend/package.json`. Each produced a confident wrong finding in the last 24 hours.
- **Effort follows novelty, value follows coworkers.** August commits: forge-v6 425, walmart 300, foundry 175, kit 427, V5 43. Coworker activity: V5 line and walmart only. Everything built since 08-17 has one user.
- **Single operator.** Five collaborators hold access to both V6 repos and none has used it; the two PRs are nine days unreviewed. Invites, sudo, OAuth clients, group bindings, SSO registration are all on his list.

---

## 6. Gaps, classified

**Structural (the shape produces the problem)**
1. No prevention or uptake gauge anywhere: not for hooks (warn-events unread), not for the bot (acted-on commits uncounted), not for local lanes (routing decision unrecorded).
2. Rulings are not machine-readable where they bind (see §5). Runner triplication, lane non-routing and the reversed placement ruling are one defect.
3. V6 has no CI/CD, manual deploy is banned, pm2 is not registered with launchd (every reboot wipes runner, console, kanban), and the deploy step is the owner. Shipping is structurally blocked on him twice.
4. The gcc has no pruning mechanism: 43 always-loaded rules, 291 open proposals, rules revised inside the month they spike. The same sprawl the rules warn against in code.
5. The slack build repo runs its own bot on itself from `@main` (half the org's Actions minutes, and blind self-review).

**Identification (the record names the wrong thing)**
- Atone April/May rows are a v1 import, not incidents; "tripled since April" is false.
- `model-dispatch.jsonl` is an Agent-tool log, not a routing log.
- "versable-builder has no consumer" was wrong; it has four.
- "3 to 4 days" was a conditional wall-clock, "8 to 11 days" was the priced work.
- gcp/ is an untracked mirror; foundry is canonical; both seats were right about different trees.
- `silica-runner` named the wrong service for two days; the fake dev runner spoke a different error vocabulary than the real one until 08-27.
- `docs/STATE.md` in local-models still lists shipped vis-compare under PENDING, dated 07-09.
- `fable-feedback-jul-16.md` and `fable-save-me-jul-7.md` are named backwards; `_draft.md` in user_docs is agent-authored.
- "Hit its spending cap" (rule text) was included-minutes exhaustion at 18.8% of cap.
- Four slack tasks blocked on an already-merged PR; slack's blocked_on rows stale.

**Behaviour quirks (true, undocumented, will bite)**
- `declared-ready-stop.sh` was retuned 07-02 to block less by design; its ledger trend reads as "worse" for that reason.
- Advisory hook nudges reach only the agent; the owner never sees them unless the agent renders them.
- `q` history has no caller field; `see` and `q` cannot be attributed to a project.
- `lm gemini` timed out on 26% of its August calls, all one off-mission task.
- Gemini can never pass a review by construction; sticky comment `created_at` is the placeholder time.
- `warm` calls `ollama` by bare name; under launchd's PATH that is exit 127.
- Files in V6 have no tenant column: any signed-in user can list and download any file (documented as an open owner decision, not a bug).

**Missing pieces with disproportionate benefit**
1. **One prevention gauge, one page, weekly.** Join `hooks/warn-events.jsonl` (blocks, soft notes, heeded) with atone escapes per slug and with commits landing within N minutes of a bot review. All three data sets exist. This is the only way to know whether A3, W2 and W4 work, and it replaces the three unread ledgers with one read one.
2. **Rulings as a file the gates read.** One `RULINGS.md` (or ADR dir) per repo with repo-home, lane, deploy and gate rulings in a fixed shape, consulted by the commit guard and the Agent guard. Turns §5's first two mechanisms into a check.
3. **Walk the three modules, then invite one coworker.** Nothing about V6's thesis is testable until `image.render`, `attribute.normalize` and `parttype.match` have each carried one real file. Five collaborators are idle; one non-owner sign-in is the cheapest evidence the estate lacks.
4. **The two owner-side unblocks that gate all V6 shipping:** `pm2 startup` (sudo) and CI/CD for forge-v6/foundry. Both are on his list and nothing downstream moves without them.
5. **Prune always-loaded rules by warn-events evidence.** Keep the rules whose hooks show heeding, scope the rest. 3,648 lines is a per-session tax paid before any project file is read, and August's spike suggests the text is not what changes behaviour.
6. **Ten-minute fixes with outsized signal:** PATH export in `warm-evening-off`; decide the 83 GB of idle image weights; refresh `docs/STATE.md`; sweep stale `blocked_on` rows; close the two nine-day PRs or mark them draft.
7. From the prior audit, still open: `/claude-bot review` (a coworker already typed it), take the build repo out of its own bill, a one-line sign on the docs nexus.

---

## 7. How to hold it in your head

The structural need that pushed you toward this assortment is one need, and it is your product thesis applied to yourself: you took yourself out of execution and out of review, and every piece since then exists to make that removal safe. The kit, the contract tree, the rules, the hooks, the wardens, the ledgers, the bot, the local lanes: each is a factory for earning autonomy. The shape repeats in every system: a pipe someone meets, a factory behind it, a gauge on the factory. What is missing is the same in every system too: the gauge is never read, so trust rests on postmortems (yours on 08-26 and 08-28, the agent's own on #74 and #76) rather than on numbers.

On the ground, the picture is narrower than the machinery suggests. Coworkers meet V5 and a bot that reviews their PRs and whose findings they fix without a word. Customers meet V5. Everything else, V6 included, has one user, and that user is also the only reviewer, deployer, gate and gauge-reader. The effort is going where the novelty is (V6, kit, gcc) and the evidence of landing is where the coworkers are (V5, bot). That is not wrong for a replatform, but it means the bet is being run without any external reading of it yet, and the cheapest possible one (a coworker signing in, a module walked) has been available for nine days.

Two of your own stated tensions explain most of the agent-side friction: "never halt" beside "ask me proactively", and "full autonomy" beside deep distrust of self-report. You have resolved both in practice (defaults with silence-means-agreement; verification by a seat that did not do the work), and neither resolution is yet a gate the machinery enforces. Making those two resolutions mechanical is worth more than any new rule.

---

## 8. Uncertainties, specific

- Whether any of the auth service's 7 users is a coworker (no DB query; the owner's own dev sign-in was still an open gate on 08-28).
- Whether `image.render`, `attribute.normalize`, `parttype.match` ran in the 48 hours after `where-we-are.md`; no newer status artefact exists.
- Whether the owner ever spoke the "non-technical teammate" sentence outside the written record; grep covers the surviving corpus only.
- Whether August's atone rise is more failures or more filing discipline; no instrument separates them, and sub-agent transcripts (2,194) were not dated as an alternative denominator.
- Anthropic and Gemini spend: unreachable; only GH Actions is measured.
- Whether `asset-verify`, `findings-gate`, the E8 lane were ever used: no history stream, and this audit did not search other projects' output dirs for their artefacts.
- Human visits to the docs nexus, and Render deploy state of pr-board: unmeasured.
- `landing-app` (79 August commits) is not findable under the org on GitHub; deploy state unknown.

## 9. Sources

| source | used for | reliability |
|---|---|---|
| repo code, manifests, lockfiles, git logs (file:line in seat files) | what exists and runs | primary |
| 481 checkpoints, `contract/v6/*.md`, NIGHT-CHANNEL, where-we-are | timeline, owner rulings verbatim | secondary; owner quotes verbatim by convention |
| `user_docs/*.md` (owner-authored, two misnamed, one agent-authored) | product intent | primary |
| transcripts, ~230 owner utterances sampled from ~1,300 substantial turns | working intent, complaints | sampled, July/August heavy |
| local-models histories (`logs/*.jsonl`, `outputs/*.jsonl`) | lane usage | primary; no caller field |
| `~/.claude/hooks/warn-events.jsonl` (20,421 rows) | hook fires, blocks, heed | primary, opened only by the verifier |
| `~/.claude/atone/events.jsonl` (431 rows) | escapes | primary; Apr/May backfilled, schema drifted |
| `~/.claude/logs/model-dispatch.jsonl` | Agent-tool dispatches only | primary for what it measures |
| `gh api` contributors, PRs, collaborators, billing | coworker touch, cost | primary, current |
| last night's slack-automation audit | pr bot, board, nexus | verified yesterday, reused |
