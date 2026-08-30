# Seat 5: Estate map + effort flow, May to August 2026

## 1. Claim and verdict

**Claim:** the owner's estate is a small number of connected systems, and effort
(commits, checkpoints, dispatches, dollars, minutes, attention) flows to them in a
way that can be laid beside what each delivers.

**Verdict: mixed.** The estate maps cleanly. Few real systems, real edges, and the
duplicate lineages turn out to be worktrees, not separate builds. Effort is
measurable and concentrated. But effort and delivered value diverge sharply for
the two biggest single line items. `versable-builder` (a UI kit) and `gcp` (a
planning tree) together account for 2.4 GB of transcript and 137 of 481
checkpoints (29%), and this audit found zero external consumers of either: no
coworker PR, no confirmed runtime import, no deploy. Meanwhile `slack-automation`,
built solo with no coworker committing to its own repo, demonstrably reaches every
coworker's PR and cost $9.39 in real GitHub Actions billing in August. The
cheapest system in the estate is the one with the clearest evidence of landing.

## 2. Estate map

```
                         +-------------------------+
                         |   gcp (planning tree)    |  no .git, contract/ dir
                         |  "V6 contract", specs    |<-+ referenced by name in
                         +------------+--------------+  | forge-v6 / foundry docs
                                      | names/specs      |
                                      v                  |
     +--------------+     +--------------------+   +----+-----------+
     | versable-    |---->| versable-forge-v6  |   | versable-       |
     | builder      | style| (V6 console, GCP  |   | foundry         |
     | (UI kit)     | ref  | Cloud Run, live)  |   | (runner, Cloud  |
     | solo, 685    |      +---------+-----------+  | Run, live)      |
     | commits      |                | worktrees: forge-auth,          |
     +--------------+                |  forge-gate, forge-ingestion    |
            ^                        +--------------+-------------------+
            | "same barrel pattern"       worktrees: foundry-auth,
            | (doc precedent only,        foundry-auth-deploy
            |  no npm import found)
            |
     +------+---------------------------------------------------+
     |        enhancement-product  (V5, the real product)        |
     |  Vercel (frontend) + Render (backend), tech.versable.ai   |
     |  3195 commits since 2024-10, 3 real coworkers on PRs      |
     |  worktrees: two-, four-, staging-, ep-docs-wt              |
     +------+-------------------------------+----------------------+
            |                               |
    +-------+--------+             +--------+--------+
    |  extractor /    |             |  walmart-mvp    |  Dockerfile, 3 coworkers
    |  extractor-     |             |  speedway       |  on PRs each, worktrees:
    |  webserver      |             |                 |  walmart-docs-wt/-nexus-wt,
    +-----------------+             +-----------------+  speedway-ref/-nexus-wt

     +-----------------------------------------------------+
     |  slack-automation (pr-board + PR review bot)          |
     |  solo repo (0 coworker PRs to it), but its OUTPUT      |
     |  posts on every coworker's PR and a live Slack board   |
     |  75 PRs, all by owner. $9.39 real GH Actions spend     |
     +-----------------------------------------------------+

     +-----------------------------------------------------+
     |  local-models (this repo). $0 local LLM toolkit        |
     |  DORMANT since 2026-07-24 (36 days). Consumed only      |
     |  as gcc rule references (4 files), not by product        |
     |  repos.                                                   |
     +-----------------------------------------------------+

     +--------------+   +--------------+   +--------------+
     | Dendron/     |   | docs/        |   | automation/  |
     | dormant 87d  |   | dormant 70d  |   | non-git,     |
     | (notes)      |   | (notes)      |   | scratch dir  |
     +--------------+   +--------------+   +--------------+

     ~/.claude (gcc): the substrate everything else runs inside.
     420 commits since May, 108/481 checkpoints (22%, the most of any single
     project), 564 MB transcript. Not a product; the tooling that runs
     the products.
```

## 3. Effort table

Commits are by author-date on the named repo's own `.git` (worktrees rolled
into their parent, not double-counted). Checkpoints are rows in
`~/.claude/checkpoints/index.jsonl` grouped by `project_root`. Transcript GB is
`du -sh` on the matching dir under `~/.claude/projects/`. Dispatches: the
model-dispatch log (`~/.claude/logs/model-dispatch.jsonl`, 1086 rows,
covering 2026-07 to 2026-08 only) carries no cwd or project field, so per-repo
dispatch counts are not derivable from it. See Uncertainties.

| Repo | May | Jun | Jul | Aug | Checkpoints | Transcript | Deployed? | Who touches it |
|---|---|---|---|---|---|---|---|---|
| enhancement-product | 274 | 182 | 122 | 43 | 24 (incl. subdirs) | 189 MB | Vercel+Render, tech.versable.ai | Customer (production URL) plus 3 coworkers (nokusukun, prajwalx, saitejan: 36 of 89 PRs since May) |
| versable-builder | . | . | 258 | 427 | 92 | 1.9 GB | none found | Owner + agent only. 0 coworker PRs (3 total, all owner). Referenced by name in versable-foundry docs as a style precedent, no npm/import dependency found |
| gcp | n/a (no git) | n/a | n/a | n/a | 45 | 500 MB | n/a, planning tree | Owner + agent only; a non-code contract/spec tree |
| slack-automation | . | . | . | 192 | 30 | 66 MB | Slack bot + PR review bot, live | Owner-only commits (0/75 PRs by coworkers), but the output reaches all coworkers: posts on every human PR in 5 joined repos, a 3-person Slack thread changed a real model choice, $9.39 real GH Actions spend Aug 2026 |
| walmart-mvp | 4 | 40 | 1 | 300 | 16 (+worktrees) | 7.1 MB | Dockerfile | 3 coworkers, 50 of 63 PRs since May |
| speedway | . | . | 532 | 114 | 12 | 15 MB | Dockerfile | 3 coworkers, 35 of 49 PRs since May |
| versable-forge-v6 | . | . | . | 425 | 3 | 20 MB | Cloud Run, live (versable-forge-v6-dev) | Owner + agent only so far (1 PR, by owner). No coworker GitHub activity found |
| versable-foundry | . | . | . | 175 | 2 | 23 MB | Cloud Run, live (silica-runner-dev) | Owner + agent only (1 PR, by owner) |
| landing-app | 2 | 7 | 3 | 79 | 4 | 146 MB | not found via `gh api` under versable-git or alcatraz627, likely private/renamed | Unknown, unverified |
| internal-dashboard (`internal` on GH) | . | . | 18 | 8 | 0 | not separately mapped | Dockerfile present | 0 PRs of any kind since May, solo and unreviewed |
| extractor | 9 | 11 | . | . | 0 | not mapped | none | Unknown |
| extractor-webserver | 2 | 18 | . | 1 | 0 | not mapped | none | Unknown |
| services-api | . | . | . | 4 | 0 | not mapped | Dockerfile | Unknown |
| vons-pim | . | 7 | . | 1 | 0 | not mapped | Dockerfile | Unknown |
| scraper-runner | 9 | . | . | . | 0 | not mapped | none | Unknown |
| logger-crab | 10 | . | . | . | 0 | not mapped | render.yaml+Dockerfile | Unknown |
| pr-claude-testbed | . | . | . | 9 | 0 | not mapped | none | Test bed, not a product |
| local-models (this repo) | . | 11 | 79 | 0 | 14 | 78 MB | n/a, local CLI | Owner-only. Dormant since 2026-07-24 (36 days, main branch). Referenced by 4 files in `~/.claude/rules`/`features` as tooling doctrine |
| ~/.claude (gcc) | 20 | 36 | 119 | 245 | 108 | 564 MB | n/a, config/tooling | Owner + every agent session, the substrate, not a deliverable |
| Dendron | n/a | n/a | n/a | n/a | 0 | tiny | none | Dormant since 2026-06-04 (87 days) |
| docs/ (root notes dir) | n/a | n/a | n/a | n/a | 0 | tiny | none | Dormant since 2026-06-21 (70 days) |
| automation/ | n/a (no git) | n/a | n/a | n/a | 0 | 242 MB transcript | none | Non-repo scratch/checkpoint dir, but 242 MB of transcript sits under it: high session cost with no committed artifact |

## 4. Where effort and value diverge most, top 5

1. **`versable-builder`: 92 checkpoints (19% of all checkpoints), 685 commits,
   1.9 GB transcript (the single largest transcript directory on the machine),
   zero coworker PRs, and no confirmed runtime dependency from the two repos
   it is positioned to serve** (`versable-forge-v6`, `versable-foundry`). The
   only cross-reference found is a doc-level style precedent
   (`versable-foundry/canon/11-capability-manifest.md`, quoting
   `versable-builder/docs/KIT-HANDBOOK.md:10-11`), not an import. This is the
   biggest single effort concentration in the estate with the thinnest
   external-landing evidence found.

2. **`gcp`: 500 MB transcript, 45 checkpoints, and no git repository at all.**
   It is a planning/contract tree (`gcp/contract/v6/`), not a shippable
   system. It is real and load-bearing (forge-v6 and foundry docs cite it by
   name), but by this audit's own framework it cannot be scored against
   deploy/commit/PR metrics the way a repo can. Its "delivery" is other
   repos' plans, several turns removed from anything a customer touches.

3. **`slack-automation` is the cheapest system in dollar terms** ($9.39 of the
   org's real August GH Actions bill; the repo itself has zero coworker
   commits), and shows the clearest, most independently corroborated evidence
   of landing anywhere in the estate: bot review comments on every joined
   repo's coworker PRs, a real Slack thread where a non-owner engineer
   flagged a cost spike, and a coworker (prajwalx) shipping a fix "four
   minutes and 56 seconds" after a bot finding (per seat-4/seat-5's
   independently gathered evidence, reused here rather than re-derived, see
   `seat-4-ground.md` and `seat-5-verify.md` in the sibling audit at
   `/Users/alcatraz627/Code/Versable/slack-automation/.claude/output/20260829-2251-deep-research-project-audit/`).
   Low effort, high measured landing: the inverse of finding 1.

4. **`local-models` (this repo) is dormant 36 days on its main branch,** yet
   it is cited as standing tooling doctrine in 4 files under
   `~/.claude/rules` and `~/.claude/features`, and its transcript (78 MB) and
   checkpoints (14) are still accruing engagement from other sessions reading
   `docs/STATE.md` even while the repo's own git history has stopped. Effort
   here is invisible to a commit-count view, because the "delivery" is
   indirect: doctrine baked into `~/.claude`, not code shipped from this
   repo.

5. **`enhancement-product` is the only system in the estate with a live
   customer-facing URL** (`tech.versable.ai`) and the deepest commit history
   (3195 commits back to 2024-10-14), but its August commit volume (43) is
   the lowest of the year (May 274 down to Aug 43), while newer systems
   (`versable-forge-v6` at 425, `versable-foundry` at 175, `walmart-mvp` at
   300 in August alone) absorbed the effort that used to go here. This reads
   as a genuine platform migration (V5 to V6), not neglect: `versable-forge-v6`
   and `versable-foundry` are both live on Cloud Run. But it means the one
   system with confirmed customer traffic is currently the least invested.

## 5. Dormant / duplicate lineage list

**Dormant (no commit or file activity 60+ days as of 2026-08-30):**
- `local-models` main branch: last commit 2026-07-24 (36 days; just under the
  60-day bar, flagged because its worktree-agent branches are even older:
  2026-07-13 and 2026-07-10)
- `Dendron/`: last note touched 2026-06-04 (87 days)
- `docs/` (root scratch dir): last touched 2026-06-21 (70 days)
- `extractor`: last commit 2026-06-17 (74 days)
- `scraper-runner`: last commit 2026-05-18 (104 days)
- `logger-crab`: last commit 2026-05-14 (108 days)
- `scripts/` (Versable root): last commit 2026-05-26 (96 days)
- `repl-agent`: single commit, 2026-06-03 (88 days)
- `vons-pim`: last commit 2026-08-14, but only 8 commits total since June,
  thin, not dead, worth watching

**Duplicate lineages, all confirmed as git worktrees of one parent repo, not
independent builds** (so they do not multiply the estate's real system count,
but they do multiply checkpoint/transcript overhead per parent):
- `enhancement-product` fans into worktrees `two-enhancement-product`,
  `four-enhancement-product`, `staging-enhancement-product`, `ep-docs-wt`
  (4 worktrees; `two-enhancement-product` alone carries 201 MB of transcript
  and 7 checkpoints, on top of the parent's own 189 MB and 7)
- `speedway` fans into worktrees `speedway-ref`, `speedway-nexus-wt`
- `walmart-mvp` fans into worktrees `walmart-docs-wt`, `walmart-nexus-wt`
- `versable-forge-v6` fans into worktrees `forge-auth`, `forge-gate`,
  `forge-ingestion`
- `versable-foundry` fans into worktrees `foundry-auth`,
  `foundry-auth-deploy`

## 6. Uncertainties

- **Per-repo agent-dispatch attribution is not derivable.**
  `~/.claude/logs/model-dispatch.jsonl` (1086 rows, spans 2026-07-07 to
  2026-08-30 only, no May/June data) carries only `ts`, `session_id`, `tool`,
  `model`, `prompt_head`. No `cwd` or `project` field. Cross-mapping
  `session_id` (a UUID) to a project would require matching each of the 211
  distinct session_ids against `~/.claude/projects/*/*.jsonl` filenames,
  which this audit did not do at scale. Flagging rather than fabricating.
  Model split overall: sonnet 699, opus 298, fable 41 (plus 3
  `claude-fable-5`), haiku 10, null 35.
- **Anthropic/Claude API spend is not reachable**, the same conclusion as the
  seat-4/seat-5 audit this report reuses; no billing endpoint for Claude Code
  usage was queried by this seat either.
- **`landing-app` deploy status is unconfirmed.** It shows real August commit
  activity (79 commits) but is not found under the `versable-git` GitHub org
  nor as `alcatraz627/landing-app` via `gh api`. It may be a differently
  named or private repo. Not verified either way.
- **`internal-dashboard`'s GitHub identity is inferred, not confirmed.** The
  local dir name doesn't match any org repo. `internal` was assumed as the
  best name match by pushed_at recency and is unverified as the same
  project.
- **PR/commit counts reflect local clone history only**, not squash-merge
  practices on GitHub. A repo with heavy squashing could show fewer local
  commits than actual work performed. Not corrected for.
- **"Value landing" for `versable-forge-v6`/`versable-foundry` rests on
  confirmed live Cloud Run URLs** (`docs/infrastructure.md`) plus pm2
  processes running locally (`versable-forge-v6`, `foundry-auth`,
  `silica-runner` all online). This shows the systems run, not that anyone
  outside the owner has used them yet. Genuinely early stage: the
  coworker-PR evidence exists for the V5 line (`enhancement-product`,
  `walmart-mvp`, `speedway`) but not yet for V6.
- **Checkpoint `project_root` granularity is inconsistent.** Some rows point
  at a repo root, others at a subdirectory (`enhancement-product/frontend`,
  `enhancement-product/backend` counted separately from
  `enhancement-product`). The effort table above merges these by eye where
  obvious; a stricter roll-up might change individual counts by a few points
  without changing the ranking.

## 7. Source table

| Finding | Command / file |
|---|---|
| Repo list + git status | `ls -la /Users/alcatraz627/Code/Versable`, `/Users/alcatraz627/Code/Claude` |
| Worktree detection | `cat <dir>/.git` for each NO_GIT dir (worktree gitdir pointers) |
| Commit totals/first-last | `git -C <repo> log --reverse --format=%ad --date=short \| head -1`; `git -C <repo> log -1 --format=%ad` |
| Monthly commit counts | `git -C <repo> log --format=%ad --date=format:%Y-%m \| sort \| uniq -c` |
| local-models branches/status | `git branch -a`, `git log -1` per branch, `git status --short` |
| gcc (~/.claude) commit history | same, run in `/Users/alcatraz627/.claude` |
| Checkpoints by month/project | `python3` parse of `/Users/alcatraz627/.claude/checkpoints/index.jsonl` (481 rows, fields `ts`, `project_root`) |
| Dispatch log by month/model | `python3` parse of `/Users/alcatraz627/.claude/logs/model-dispatch.jsonl` (1086 rows) |
| Transcript sizes | `du -sh /Users/alcatraz627/.claude/projects/*` |
| Deploy markers | `find`/`ls` for `vercel.json`, `.vercel`, `render.yaml`, `Dockerfile`, `fly.toml`, `Procfile` per repo |
| Live deploy confirmation | `enhancement-product/frontend/docs/tech/system/deployment-services.md`; `versable-forge-v6/docs/infrastructure.md` (Cloud Run URLs); `gh api repos/versable-git/enhancement-product --jq .homepage` returned `tech.versable.ai` |
| Coworker PR evidence | `gh api repos/versable-git/<repo>/pulls?state=all&per_page=100 --paginate`, filtered to `created_at >= 2026-05-01`, grouped by `user.login` |
| Org repo list | `gh api orgs/versable-git/repos?per_page=100 --paginate` |
| GH Actions billing $9.39 / 4,668 min Aug 2026, coworker Slack thread, 4m56s fix turnaround | reused verbatim from `/Users/alcatraz627/Code/Versable/slack-automation/.claude/output/20260829-2251-deep-research-project-audit/seat-4-ground.md` and `seat-5-verify.md` (last night's sibling audit, not re-derived) |
| versable-builder cross-reference | `rg -l "versable-builder" versable-forge-v6 versable-foundry enhancement-product`; `versable-foundry/canon/11-capability-manifest.md` |
| Dendron/docs dormancy | `stat -f "%Sm %N"` on `Dendron/notes/root.md`, `docs/*.md` |
| pm2 live processes | `pm2 list` |
| gcc rule cross-references to local-models | `rg -l "local-models\|q --format\|see --ui\|imagine\|vis-compare" ~/.claude/rules ~/.claude/features` returned 4 files |
