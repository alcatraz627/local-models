# Seat 1: gcp / Silica Praxis replatform, estate audit

Read-only research seat. Everything below is measured from the corpus at
`/Users/alcatraz627/Code/Versable/` unless marked UNVERIFIED. Timestamps are
file mtimes or git commit dates as returned by the tools, not recalled.

## 1. The claim, and the verdict

> "The gcp / Silica Praxis replatform (the contract tree, the runner, the
> versable-forge-v6 console, foundry auth) has a known, evidenced state: what
> is live and used, what is code-only, what is doc-only, what was planned and
> dropped."

**Verdict: supported, with one important correction to how the claim is
usually framed.** The estate keeps a genuinely evidenced, self-auditing
record of its own state. `gcp/contract/v6/where-we-are.md`,
`decommission-ledger.md`, `runner-home-ruling.md`, and `why-the-board-was-wrong.md`
are each dated, cite the instrument that produced every line, and were
explicitly rewritten when a prior page was found stale. But the record is
also honest that it has repeatedly not bound the work: the runner had three
copies on disk as of 2026-08-26 because a repo-placement ruling from
2026-08-21 was never read by the agent that reversed it three days later, and
a four-hour stretch on 2026-08-26 filled the task board with real, verified
work that was not what the owner needed, because every finding came from an
instrument and none from walking the product as a user. So "known and
evidenced" is true of the paperwork; "acted on" is a separate, weaker claim,
and the estate's own docs say so.

## 2. Timeline, 2026-08-17 to 2026-08-30

Reconstructed from `gcp/contract/PLAN.md`, the 47 `_2026*.claude.md`
checkpoints in `gcp/`, and commit-date histograms of `versable-forge-v6` and
`versable-foundry`.

- **2026-08-17**: Charter, contract tree structure decided; owner's answers
  become `gcp/contract/00-charter.md`. `gcp/contract/PLAN.md:1`.
- **2026-08-18**: Contract tree first draft (canon, contracts, patterns, ADRs,
  instances) written; conformance suite run against live `services-api` (11
  pass, 20 fail, 19 not runnable of 50 rows); tree-wide adversarial review,
  31 findings landed same day. Owner rules the V6 decision set (D1 A, app
  renamed `versable-forge-v6`; D2 A Cloud SQL; D3 B Next.js on Cloud Run;
  D11 keep qsync; D13 A). Day 0: `silica-runner` (runner step 0) and
  `versable-forge-v6` (console scaffold) both created on disk.
  `gcp/contract/PLAN.md:37-45,58-77`.
- **2026-08-19 to 2026-08-20**: Runner step 1 (`/manifest`, schema generator,
  `/outcomes`, jobs index); forge-v6 commit volume climbs fast, 70 commits on
  the 20th alone. `versable-forge-v6` git log.
- **2026-08-21**: Owner rules a three-repo split
  (`gcp/.claude/output/20260821-1449-three-repo-split-change/plan.md`, cited
  in `runner-home-ruling.md`): D7 merges `silica-runner` into
  `versable-forge-v6`; D10 says "the runner is not foundry." Neither runs.
- **2026-08-24**: Commit `72c4ad2` in `versable-foundry` ("Bring the runner
  into the foundry", git-subtree) moves the runner into
  `versable-foundry/runner/`, citing no ruling and reversing D7/D10 without
  saying so. `gcp/contract/v6/runner-home-ruling.md`.
- **2026-08-25 to 2026-08-26**: Heavy build days (70 and 101 commits in
  forge-v6 respectively). Evening of the 26th: owner walks the app, hits a
  dead end, says "all 3 of you burning tokens but nothing of value getting
  done", which triggers the `why-the-board-was-wrong.md` postmortem. The
  runner triplication is found and diagnosed the same evening.
  `gcp/contract/v6/why-the-board-was-wrong.md`, `runner-home-ruling.md`.
- **2026-08-27**: Owner arms a standing goal for a central multi-project auth
  module ("gcp-fable owns the central auth module end to end (owner,
  2026-08-27)"), spec ruled, `auth-dev` deployed live same day.
  `gcp/_20260827-auth-goal-armed.claude.md:5,19`.
- **2026-08-28**: Owner ruling session: deletes the "paid run" cost gate,
  rules the reaper is intended, orders "0 MANUAL DEPLOYS ANYMORE" (D4a, the
  deploy-lift permission removed from every seat's allow list), sets a docs
  standard, states three concrete goals for the project.
  `gcp/_20260828-gcp-watcher-evening.claude.md:8-27`. Decommission ledger for
  `gcp/` itself is written (`decommission-ledger.md`); the folder is ruled
  "the origin with the sunk cost... decommissioned and salvaged for parts."
- **2026-08-29 to 2026-08-30**: Session-end auto-checkpoints only
  (`gcp/_precompact-checkpoint.claude.md`, mtime 2026-08-29T22:59); no new
  dated `_2026*` checkpoint files after the 28th as of the audit's read.
  `versable-forge-v6` shows 5 further commits on 2026-08-30 (last read
  `d74086e`, `git log --oneline -5`).

## 3. Inventory table

| Piece | State | Evidence | Last touched |
|---|---|---|---|
| Contract tree (`versable-foundry/{canon,contracts,adr,patterns,instances,guides,plans}`) | **live**, canonical home, git-tracked, pushed to `origin/versable-git/versable-foundry` | `versable-foundry` git log (b467a55 head, 20 recent commits listed), remote `origin` confirmed | 2026-08-30 (b467a55) |
| Same tree copied under `gcp/contract/` (minus `v6/`) | **doc-only, stale mirror**, ruled dead 2026-08-28 | `gcp/contract/v6/decommission-ledger.md`: "not a port waiting to happen; it is a stale mirror," foundry newer on 17 files, identical on the rest | ruling 2026-08-28 |
| The runner (Python, `/manifest` `/outcomes` `/jobs`) | **live**, one canonical copy as of 2026-08-26 ruling | `versable-foundry/runner/`, pm2 process `foundry-runner` (renamed from `silica-runner`) serving `uvicorn examples.forge_v1:app` per `runner-home-ruling.md` | ruled 2026-08-26, renamed same day per the paste block in that doc |
| `~/Code/Versable/silica-runner/` (the orphan checkout) | **dropped, archived** | Does not exist on disk (`ls` returns No such file or directory); `runner-home-ruling.md` names it "the orphan," recommends archiving to `_archive/silica-runner-orphan-20260826`, referenced as already moved in a later checkpoint (`gcp/_20260827-auth-goal-armed.claude.md:11`: "orphan at ~/Code/Versable/_archive/silica-runner-orphan-20260826") | archived 2026-08-26 |
| `versable-forge-v6/runner/` (the tracked but unused third copy) | **code-only, dead code, ruled removable** | `runner-home-ruling.md`: "Nothing in the app, its scripts, its Dockerfile or its cloudbuild references it; the app reaches the runner over HTTP" | flagged 2026-08-26 |
| `versable-forge-v6` (Console app) | **live**, deployed to Cloud Run dev, actively developed | `versable-forge-v6` git log: 425 commits, 2026-08-18 through 2026-08-30, remote `origin/versable-git/versable-forge-v6`; `contract/v6/where-we-are.md`: "dev console (Cloud Run) up, serves 47dc867; signs in through auth-dev; every API route refuses unauthenticated" | commit `d74086e`, git log head |
| foundry auth service (`versable-foundry/auth/`) | **live on dev**, deployed | `auth-module-status.md`: stage 3 "LANDED 2026-08-27: auth-dev live (serves 8b7f56d)"; `where-we-are.md`: "warden auth service :6229 up, /health/deep 200, db=postgres, 7 users" | 2026-08-27 deploy, status re-measured 2026-08-28 |
| `foundry-auth`, `foundry-auth-deploy` dirs | **git worktrees of `versable-foundry`**, not separate repos | `.git` files point to `versable-foundry/.git/worktrees/{foundry-auth,foundry-auth-deploy}`; `git worktree list` confirms `[auth/module]` and `[auth/deploy]` branches | active through 2026-08-30 |
| `forge-auth`, `forge-gate`, `forge-ingestion` dirs | **git worktrees of `versable-forge-v6`**, not separate repos | `.git` files point to `versable-forge-v6/.git/worktrees/{forge-auth,forge-gate,forge-ingestion}` | forge-auth mtime 2026-08-28 |
| `versable-forge-v6/runner/`'s Secret Manager token wiring (forge-7) | **resolved** | `Dockerfile:26` `RUN --mount=type=secret,id=gh_token`; `cloudbuild.yaml:44` `--secret id=gh_token,env=GITHUB_PACKAGES_TOKEN`, both present, no longer the mismatch `PLAN.md` flagged on 2026-08-18 | resolved sometime before 2026-08-28 (cloudbuild.yaml mtime) |
| SchemaForm / V2a composable wizard | **planned, deferred** | `v6-decision-set.md`: "V1 does not have... schema-generated forms (V2a, SchemaForm)"; `PLAN.md` foundry-3 "visual polish batch on SchemaForm in progress" as of 2026-08-18 evening | parked, no evidence of further work found |
| The deck (`plans/v6-deck.html`) | **built, parked** | `PLAN.md` row 23/forge-10: "built, reviewed, fixed; purpose unconfirmed" then "forge-10... no longer parked... reworked in foundry-12... The deck rework (forge-10) stays parked" | 2026-08-18/19 |
| `versable-foundry-presentation.html` (foundry-12) | **built, published privately** | `PLAN.md` foundry-12: published at a `claude.ai/code/artifact/...` URL, "first pass done 2026-08-19 01:00 IST; owner review next" | 2026-08-19 |
| `attribute.normalize`, `parttype.match`, `image.render` modules | **code-only, never exercised** | `where-we-are.md` section 1: "image.render, attribute.normalize and parttype.match have never been run by anyone" | measured 2026-08-28 |
| `content.generate` module | **live, proven end-to-end** | `where-we-are.md`: "Run is proven for content.generate end to end through the console against the real runner, xlsx export included"; NIGHT-CHANNEL 17:55 entry: export "VERIFIED END TO END THROUGH THE RUNNING CONSOLE, ON A REAL JOB" | 2026-08-27/28 |
| `gcp/` folder itself (contract mirror, bin/, findings/, src/ snapshot) | **planned for decommission**, in progress | Owner ruling 2026-08-28 quoted verbatim in `decommission-ledger.md`: "decommissioned and salvaged for parts, all of them" | ruled 2026-08-28, not yet fully executed (the ledger is the plan, not a completion record) |
| `src/services-api/`, `src/runner-service*/` inside `gcp/` | **dropped, dead, no importer** | `decommission-ledger.md`: "rg finds no code importer, only prose mentions... none of which execute it. Move to _archive/" | measured 2026-08-28 |
| CI/CD (#392) | **planned, not built** | `auth-module-status.md` / `where-we-are.md`: "CI/CD first" (D8a, ruled 2026-08-28); replaces manual deploy after D4a removed deploy permission from every seat | ruled 2026-08-28, no CI/CD workflow files found in this audit's scope |
| Google OAuth sign-in on dev | **planned, blocked on owner action** | `auth-module-status.md` section 5: needs owner-created OAuth client plus two secrets; not started as of that doc | open as of 2026-08-27 |
| Passport SSO (Versable Internal bridge) | **live on dev, fixed same day** | `gcp/_20260828-gcp-watcher-evening.claude.md`: "Passport AND password sign-in fixed and LIVE on dev... He ran the deploy; I verified from the live URL" | fixed and deployed 2026-08-28 |

## 4. Behavioural goals vs. what the pieces actually do

The charter (`versable-foundry/00-charter.md`) states the goal in the owner's
terms: stop re-solving the same module (content generation, image
generation, part-type matching, attribute normalization, extraction) per
customer app; make modules swappable and upgradable without "two weeks of
dev time." The intended seam: **a module owns running the capability and
reporting outcomes; an app owns the customer, workflow, and per-customer
config** (`00-charter.md`, "Where the line sits").

What is actually true on 2026-08-28, per `where-we-are.md` sections 1 and 4:

- The seam mostly holds for one module (`content.generate`), which is proven
  end-to-end through the real console against the real runner, both themes,
  with xlsx export. The other three declared modules exist as contract-shaped
  code but have literally never been exercised by a human. The charter's
  "swap in a module cheaply" promise is unverified for 3 of 4 modules.
- **A trust gap the charter did not anticipate is now the stated Tier 1
  blocker**: "Honest failure messages, the results page for a finished image
  job, and a half-worked run saying so" (`where-we-are.md` section 2). The
  charter's emphasis was ease of swap; the emerging bottleneck is closer to
  "does the UI tell a non-technical user the truth about what happened."
- The charter's "app owns per-customer config, orchestration" line is
  realized as the Workflow Console (`versable-forge-v6`), and it is the one
  piece proven against a real customer file per `where-we-are.md`: "The bar:
  a non-technical teammate gets one real workbook through the console alone.
  Upload, map, run, read, export." Only the upload/map/read/export legs are
  proven for all four modules; run is proven for one.
- **Auth diverges from the charter's original silence on identity.** The
  charter names "users, sessions, orgs, workspaces, roles" as app
  responsibility, but the estate built a shared, module-external auth
  service (`versable-foundry/auth/`) intended to serve multiple apps
  (forge, later speedway, walmart) from one user table
  (`auth-module-status.md` section 2 diagram), a cross-app identity layer
  the charter's language implies is closer to the module side ("the module
  only ever sees a verified caller and a tenant id") but which the team
  placed in the reusable "foundry" half. This is the team's own extension of
  the charter, not a divergence flagged as wrong by anyone in the record.
- **Deployment discipline diverges sharply from the "showable in three days"
  charter estimate.** `v6-decision-set.md` priced V1 at 3 to 4 days wall
  clock (2026-08-18); as of `where-we-are.md` (2026-08-28, ten days later) V1
  is still gated on a single paid production-data run that has not happened,
  and the owner's own words that day were "the agents just love picking the
  hardest and least valuable things frontloaded", a direct owner observation
  that intended prioritization (ship something a customer can use) diverged
  from actual prioritization (proof, tests, infra).

## 5. Gaps

**Structural**
- Runner triplication (section 3, `runner-home-ruling.md`). The root cause is
  named in the record itself: "nothing in this estate makes a repo-placement
  ruling a thing a commit has to pass." A ruling lived in a dated agent
  output folder, not in an ADR the commit gate reads.
- The `gcp/` folder duplicated the entire contract tree as a stale, silently
  diverging mirror for at least ten days before being caught
  (`decommission-ledger.md`, "The one finding that changes the size of the
  job").
- `image.render`'s preview route had an unbounded row count (`route.ts:52`)
  that could reach roughly $80 per request before a review caught it and
  demoted the finding to a payload issue rather than a live spend hole
  (NIGHT-CHANNEL entries #375, 19:00 to 19:20).

**Identification (record names the wrong thing)**
- The pm2 process, Cloud Run service, and directory were all named
  `silica-runner` for two days after the runner's actual home moved to
  `versable-foundry`, which `runner-home-ruling.md` states directly caused
  "an hour of confusion and one false accusation between lanes" on
  2026-08-26.
- The guidebook documented an output field (`images.rendered`) that appears
  zero times in the manifest or source; corrected 2026-08-27
  (NIGHT-CHANNEL 18:15 entry).
- A "fake" runner used for console-only dev diverged from the real runner's
  vocabulary of error and review codes entirely, a different set, not just
  different values, until fixed 2026-08-27. Any UI screen built against the
  fake before that fix was validated against strings the real system never
  emits (NIGHT-CHANNEL 18:15/18:35 entries, #374).

**Behaviour quirks**
- Seven distinct "fixture that cannot fire" bugs were found in one day
  (2026-08-27) by a single reviewer systematically re-testing routes: tests
  that passed while asserting nothing, because the mutation they were meant
  to catch could never occur given the fixture (NIGHT-CHANNEL, running count
  "SEVENTH FIXTURE-THAT-CANNOT-FIRE" at 20:30).
- Files have no tenant/team column at all. "Any signed-in user can list and
  download any file" is documented as a deliberate open owner decision, not
  a bug, per `docs/plan/01-tenancy-explained.md` (NIGHT-CHANNEL 20:10 entry).

**Missing pieces with disproportionate benefit**
- pm2 is not registered with launchd; every machine reboot silently wipes
  the local runner, console, and kanban processes (`where-we-are.md` section
  1: "the machine rebooted at 00:17... needs sudo, so it is yours"). Named as
  the single item that would have prevented that outage.
- CI/CD (#392) does not exist yet; every deploy today is manual and the
  owner explicitly capped manual deploys at zero as of D4a (2026-08-28),
  making CI/CD's absence a hard blocker on further shipping rather than a
  nice to have.

## 6. Owner-voice quotes, dated, verbatim

1. 2026-08-18, evening: *"maybe look into B later"* (on Firestore vs Cloud SQL, D2). `v6-decision-set.md`.
2. 2026-08-18: *"Next JS latest"* (D3, hosting/frontend). `v6-decision-set.md`.
3. 2026-08-18: *"list is fine, let's try to keep qsync if possible even under deadline"* (D11). `v6-decision-set.md`.
4. 2026-08-18: *"can borrow setup ideas from enhancement-product for next js"* (D13). `v6-decision-set.md`.
5. 2026-08-18: *"keep the goal in mind in the next few days"* (V1 showable-in-three-days goal). `v6-decision-set.md`.
6. 2026-08-18: *"forge for the final customer main app with big balls, foundry for the builder / contract stuff, just tagging"* (naming ruling). `v6-decision-set.md`.
7. 2026-08-26, evening: *"all 3 of you burning tokens but nothing of value getting done."* `gcp/contract/v6/why-the-board-was-wrong.md`.
8. 2026-08-28: *"the origin with the sunk cost... decommissioned and salvaged for parts, all of them"* (ruling on `gcp/` itself). `gcp/contract/v6/decommission-ledger.md`.
9. 2026-08-28: *"Premature optimization about the bill is how we've had so many bad days... it should NOT BE A CONCERN BEFORE we have real customers."* `gcp/_20260828-gcp-watcher-evening.claude.md`.
10. 2026-08-28: *"Why do we need a dummy path when the ENTIRE PRODUCT'S VALUE is data refinement of some form or the other."* `gcp/_20260828-gcp-watcher-evening.claude.md`.
11. 2026-08-28: *"there is so much value in curl calls in A LOT OF CASES."* (rejecting a proposed curl ban) `gcp/_20260828-gcp-watcher-evening.claude.md`.
12. 2026-08-28: *"the agents just love picking the hardest and least valuable things frontloaded."* (owner's diagnosis of the team) `gcp/_20260828-gcp-watcher-evening.claude.md`.
13. 2026-08-28, relayed via warden: *"I want you to worry more about the building / docs work instead of being stuck on deploys."* `gcp/_20260828-gcp-fable-queue-drained.claude.md`.
14. 2026-08-28: *"you're not supposed to run deploy yourself anymore, checkin with gcp-watcher."* `gcp/_20260828-gcp-fable-queue-drained.claude.md`.
15. 2026-08-28: *"why did you waste these tokens without at least a smoke check"*; *"your task list looks constipated... frontload the building work"*; *"stop asking me stupid fucking questions over and over just fucking plan validate build it and show me dude, maybe get the implementation plan validated by me but stop asking should I should I should I."* `gcp/_20260828-gcp-fable-queue-drained.claude.md`.

## 7. Uncertainties, specific

- **Whether the runner rename/consolidation is fully complete today** is
  UNVERIFIED beyond the 2026-08-26 paste-block instructions and the
  2026-08-27 checkpoint's mention of the orphan already being archived. No
  Aug 29 or 30 checkpoint confirms `pm2 list` currently shows only
  `foundry-runner`.
- **Whether the deployed dev console is currently up to date** is
  UNVERIFIED as of this audit's read. `where-we-are.md` (2026-08-28) flags
  "the deployed dev console is 47dc867; local forge main carries newer
  commits, so a re-merge precedes any redeploy" as a standing caveat not
  yet retired in any later checkpoint this audit found.
- **Whether `gcp/`'s decommission (ledger step 1: `src/` moved to
  `_archive/`, 133 MB) has actually run** is UNVERIFIED. The ledger states
  the plan and hands steps to "hands," but no later checkpoint in this
  audit's window confirms the move happened. (`src/` was not independently
  checked for existence/size in this pass; scope was `contract/`, `bin/`,
  `TODO.md`.)
- **Whether CI/CD (#392) exists in any form** is UNVERIFIED beyond the
  ruling that it is first in the queue; no `.github/workflows` or
  `cloudbuild` trigger config was inspected in this pass for its presence.
- **The paid production run (Tier 1 blocker in `where-we-are.md`)**, whether
  it has since happened, is UNVERIFIED. No later dated checkpoint in this
  audit's window confirms or denies it.
- Two atone/incident events referenced as "unfiled" as of 2026-08-28
  (`gcp/_20260828-gcp-fable-queue-drained.claude.md`) were not traced
  further; their current status is UNVERIFIED.
- Live network checks (curling `auth-dev`, the console's `/build-info`,
  actual pm2 process list) were **not** performed. This audit is
  filesystem/git/checkpoint evidence only, per the read-only, no-mutation
  scope given.

## 8. Source table

| Source | What it supplied |
|---|---|
| `gcp/contract/00-charter.md` | the problem statement, module/app seam, working principles |
| `gcp/contract/PLAN.md` | the day-0/day-1 timeline, forge/foundry task queues, silica-runner day-0 landing |
| `gcp/contract/plans/v6-decision-set.md` | owner rulings D1 to D13, V1 scope table, day-priced sequencing |
| `gcp/contract/v6/runner-home-ruling.md` | the three-copy runner finding, the two-rulings-that-never-executed diagnosis |
| `gcp/contract/v6/where-we-are.md` | live/dead status table, Tier 1-4 path to V1, honesty debts, owner decisions of 2026-08-28 |
| `gcp/contract/v6/why-the-board-was-wrong.md` | the 2026-08-26 owner-frustration incident, instrument-vs-walk analysis |
| `gcp/contract/v6/decommission-ledger.md` | full inventory of `gcp/` itself, what is stale mirror vs. live, owner's decommission ruling |
| `gcp/contract/v6/auth-module-status.md` | auth service stage table, code inventory, path-to-live diagram |
| `gcp/_20260827-auth-goal-armed.claude.md` | owner's armed goal for auth, standing constraints, live commitments |
| `gcp/_20260828-gcp-watcher-evening.claude.md` | owner ruling session verbatim quotes, shipped/verified list |
| `gcp/_20260828-gcp-fable-queue-drained.claude.md` | standing constraints/caveats ledger, more owner quotes |
| `gcp/_precompact-checkpoint.claude.md` | most recent (2026-08-29) session state, confirms no newer dated checkpoint |
| `gcp/TODO.md` | deferred GCP org-admin items, unrelated to the replatform core but part of `gcp/` |
| `versable-forge-v6/` git log | 425 commits, daily volume histogram, remote, head commit |
| `versable-forge-v6/NIGHT-CHANNEL.md` (tail) | route-by-route test hardening log, fixture-cannot-fire findings, live deploy verification entries |
| `versable-forge-v6/docs/README.md` | cross-repo doc map confirming which repo owns which doc |
| `versable-forge-v6/Dockerfile`, `cloudbuild.yaml` | confirmation that the forge-7 secret-wiring gap from 2026-08-18 is closed |
| `versable-foundry/` git log, `git worktree list` | confirms canonical runner/contract home, worktree structure for `foundry-auth`/`foundry-auth-deploy` |
| `foundry-auth/.git`, `foundry-auth-deploy/.git`, `forge-auth/.git`, `forge-gate/.git`, `forge-ingestion/.git` | confirms these five dirs are git worktrees, not independent repos |
| `ls silica-runner` (filesystem) | confirms the orphan directory no longer exists on disk |
