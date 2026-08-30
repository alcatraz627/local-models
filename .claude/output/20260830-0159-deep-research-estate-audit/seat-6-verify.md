# Seat 6: adversarial verification of four load-bearing claims

Read-only pass, 2026-08-30. No inference run, no files edited outside this path.
Every fact below carries the command or absolute path that produced it. Where a
check could not be made, the line says UNVERIFIED rather than guessing.

## Verdict summary

| Claim | Source | Verdict |
|---|---|---|
| A: gcc correction machinery does not reduce recurrence | seat-3 §3, §5.4 | **WEAKENED**, and its load-bearing sub-claim (the enforced slug has the worst trend) is **REFUTED** |
| B: versable-builder has no confirmed runtime dependency downstream | seat-5 §4.1 | **REFUTED** |
| C(i): model-dispatch.jsonl proves the routing rule is unenforced | seat-2 §4 | **REFUTED**, instrument artefact |
| C(ii): `lm fleet` and `imagine` dead since 2026-07-13 | seat-2 §4 | **SURVIVES** |
| C(iii): warm-evening-off LaunchAgent broken, exit 127 | seat-2 §5 | **SURVIVES**, root cause now identified |
| C(iv): FLUX.1-schnell 31 GB still on disk | seat-2 §4 | **SURVIVES** |
| D: V6 slipped 3-4 days to 10+, one module exercised, no coworker | seat-1 §4, seat-5 §4.2 | **WEAKENED**, the estimate comparison is unfair and the goalpost moved |

---

## CLAIM A

> "The gcc's correction machinery does not reduce recurrence: atone events
> tripled Apr to Aug (20 to 215/month), the top four slugs spiked in the month
> their rule was written, and the ONE mechanically-enforced slug
> (`declared-ready-without-runtime-exercise`, Stop hook
> `/Users/alcatraz627/.claude/scripts/hooks/declared-ready-stop.sh`) shows the
> worst trend, 3/3/7/16 monthly."

### Attack line 1: the denominator

Counted session transcripts by their first-line timestamp across
`/Users/alcatraz627/.claude/projects/*/*.jsonl` (3,375 top-level files; a further
2,194 at depth 9 and 11 are sub-agent transcripts, correctly excluded from a
session count).

| month | sessions | atone events | events per 1000 sessions |
|---|---|---|---|
| 2026-06 | 86 | 34 | 395.3 (denominator unreliable, see below) |
| 2026-07 | 1,275 | 59 | 46.3 |
| 2026-08 | 1,904 | 218 | 114.5 |

The per-session rate rises 2.47x from July to August, not the 3.64x the raw
count implies. So the denominator absorbs about a third of the spike and the
rest is real. That half of the claim holds.

The April endpoint does not. Only 2 sessions carry a May timestamp and 86 a June
one, against 1,275 in July. `cleanupPeriodDays` is 365 in
`/Users/alcatraz627/.claude/settings.json:3`, so retention did not delete them.
The corpus simply does not go back that far, which is consistent with the machine
migration the gcc's own `mac-migration/MANIFEST.md` references. **The Apr-to-Aug
ratio cannot be normalized at all.**

### Attack line 1b: April and May are a backfill, not live capture

This is the finding that breaks the series outright. Every one of the 20 April
rows carries a `migrated-from-v1` tag, as do 53 of the 100 May rows. The first
row of `/Users/alcatraz627/.claude/atone/events.jsonl` reads
`"[migrated v1, occurrence 1/1 of slug]"` in its `issue` field.

| month | events | tagged `migrated-from-v1` | carry `session_id` | carry `juror_verdict` |
|---|---|---|---|---|
| 2026-04 | 20 | 20 | 0 | 0 |
| 2026-05 | 100 | 53 | 6 | 17 |
| 2026-06 | 34 | 0 | 34 | 9 |
| 2026-07 | 59 | 0 | 59 | 41 |
| 2026-08 | 218 | 0 | 218 | 205 |

April is a one-per-slug import from an older format. It records slugs, not
incidents. Reading "20 in April" as a monthly incident count and comparing it to
August's live capture compares two different instruments. The schema table above
shows the instrument changing under the series in three separate steps:
`session_id` appears from June, and `juror_verdict` runs from 17% of May rows to
94% of August rows.

### Attack line 2: provenance and burst structure of August

August's 218 events come from 84 distinct sessions, so this is not one audit
seat filing everything. But the distribution is heavily clumped:

- 44 of 218 events (20%) land on a single day, 2026-08-26.
- 30 of those 44 fall inside three clusters shorter than 26 minutes each
  (11 events 09:09 to 09:17, 10 events 12:35 to 13:00, 9 events 17:32 to 17:35).
- Across the month, 19 clusters of 3-or-more at a 600s gap account for 102 of
  218 events. July had 2 such clusters covering 8 of 59.
- 150 of 218 August events sit in sessions that filed 3 or more, against 26 of
  59 in July.

Three of the 09:09 to 09:17 ids (`mist-20260826-091141-c9`,
`mist-20260826-091506-3f`, `mist-20260826-091744-ff`) are cited inside
`/Users/alcatraz627/.claude/rules/dense-briefing-direct-answer.md` as the RCAs
that produced that file. So that cluster is a self-audit writing up a batch, not
eleven independent live corrections. **Filing practice changed in August, and the
raw count is partly a measure of that change.**

One related signal, reported with its caveat because it is weaker than it looks.
The tag `same-session-repeat` is August's most common tag (67 of 218, 31%, against
5 of 59 in July). It does not mean the ledger double-files. For
`dense-briefing-instead-of-a-direct-answer` there are 25 August events across 21
distinct sessions, so at most 4 could be a second filing in one session while 15
carry the tag. The tag is a semantic classification, meaning the failure recurred
inside one session. Its 4x rise shows classification drift rather than duplicate
counting. That is enough to undermine a month-over-month count, and it is not
evidence of inflation.

### Attack line 3: did the hook actually fire? Yes, 76 times in August

This is the decisive one. `declared-ready-stop.sh:60` writes telemetry through
`warn-log.sh`, which appends to
`/Users/alcatraz627/.claude/hooks/warn-events.jsonl` (20,421 rows).

| month | hard blocks | soft notes | heed lines | atone events for the slug |
|---|---|---|---|---|
| 2026-07 | 8 | 5 | 1 (`heeded:false`) | 7 |
| 2026-08 | **36** | **40** | 9 (`heeded:true`) | 16 |

In August the gate hard-blocked a premature "done" claim 36 times, 2.25x the 16
that reached the ledger, and recorded 9 cases where an earlier fire was heeded.
**The atone ledger counts what escaped the gate. It cannot count what the gate
stopped.** Seat-3 read a rising escape count as evidence that enforcement fails,
without checking whether the gate fired. It fired 76 times.

Two further problems with the 3/3/7/16 series:

1. **The hook produced no telemetry before July.** The first
   `"hook_id":"declared-ready"` row in the warn ledger is
   `warn-20260707-092928-24` at 2026-07-07T09:29:28Z. The May and June endpoints
   of the series describe months in which the gate's own instrument did not exist.
2. **The hook was rewritten mid-series.** `git log --follow` in
   `/Users/alcatraz627/.claude` shows v2 landing 2026-07-02 (`9c4040c`, "hooks:
   precision-audit lanes 1/2/3/5 ... declared-ready v2"), telemetry rollout the
   next day (`f7b5ad2`), and further tuning 2026-07-12 (`5f682bd`). The file's own
   header, lines 30 to 37, states: "hard-block recall on the *historical*
   true-positive set is LOW BY DESIGN, not a gap ... The count of *hard blocks*
   drops; the count of *correct* hard blocks stays." The gate was deliberately
   tuned to block less. Reading a rising ledger count against a gate designed to
   demote self-disclosed gaps to a soft note measures the wrong thing twice.

Normalized against sessions, the slug's trend is also not "worst": 5.49 per 1000
sessions in July, 8.40 in August, a 1.53x rise against the corpus-wide 2.47x.
**The one enforced slug rose more slowly than the ledger as a whole.**

### Verdict: WEAKENED overall, sub-claim REFUTED

The corpus-wide "recurrence is not falling" observation survives in weakened
form. Per-session atone rate did rise 2.47x from July to August, and no
counter-evidence contradicts that. But the "tripled Apr to Aug (20 to 215)"
framing is invalid, and the sentence built on the enforced slug is refuted.

**Corrected statement for the report:**

> Atone events per 1000 sessions rose from 46.3 in July to 114.5 in August
> (218 events over 1,904 sessions), a 2.47x rise once session volume is held
> constant. The April-to-August comparison should be dropped: all 20 April rows
> and 53 of 100 May rows are tagged `migrated-from-v1`, a one-per-slug import
> from an older format, and no transcript corpus survives to normalize them.
> August's count is also clumped, with 44 events on 2026-08-26 alone and 30 of
> those inside three sub-26-minute self-audit clusters. The claim that the one
> mechanically-enforced slug shows the worst trend does not hold: the
> declared-ready Stop hook hard-blocked 36 turns and issued 40 soft notes in
> August against 16 events that reached the ledger, its telemetry only begins
> 2026-07-07, its v2 rewrite of 2026-07-02 deliberately lowered hard-block recall
> by design, and normalized per session the slug rose 1.53x against the ledger's
> own 2.47x. The ledger measures escapes, not incidence, so it cannot answer
> whether enforcement reduces recurrence. That question is open, not settled
> against.

Live-ledger caveat: the file held 431 rows when I read it against seat-3's 428,
and August 218 against its 215. The ledger is being written to during this audit.

---

## CLAIM B

> "versable-builder (UI kit, 685 commits, 1.9 GB transcript, 92 checkpoints) has
> no confirmed runtime dependency from versable-forge-v6 or versable-foundry;
> only a doc-level style citation."

### What I found

`versable-builder` publishes `@versable-git/ui`, and four downstream repos depend
on it as a real package.

**The publisher.** `/Users/alcatraz627/Code/Versable/versable-builder/packages/ui/package.json`
declares `name: @versable-git/ui`, `version: 0.2.2`, and
`publishConfig.registry: https://npm.pkg.github.com`.

**The consumers.**

| repo | manifest declaration | files referencing it |
|---|---|---|
| `versable-forge-v6` | `dependencies: @versable-git/ui 0.2.1` (exact pin) | 9 files, 12 references |
| `speedway` | `dependencies: @versable-git/ui ^0.2.2` | 88 |
| `walmart-mvp` (frontend/package.json, `walmart-mvp-frontend`) | `dependencies: @versable-git/ui ^0.2.2` | 66 |
| `versable-foundry` | no root manifest; auth/package.json is `@versable-git/auth-service` | 10 |
| `enhancement-product` | none | 0 |

**It resolves off the registry, not a workspace link.**
`/Users/alcatraz627/Code/Versable/versable-forge-v6/package-lock.json` resolves
`node_modules/@versable-git/ui` to
`https://npm.pkg.github.com/download/@versable-git/ui/0.2.1/b0fdf9bbf13b27f8c1b6a6209fac0549aa4a5ae9`.
That is a published tarball with a content hash, so the kit is genuinely built,
versioned, published and installed.

Sample import sites in forge-v6:
`src/lib/table-url-sync.ts:5`, `src/lib/capability-meta.ts:12`,
`src/lib/breadcrumbs.ts:24`, `src/lib/status.ts:1`,
`src/components/kit.tsx:61` (a re-export barrel).

### Verdict: REFUTED

**Corrected statement:**

> versable-builder publishes `@versable-git/ui` to GitHub Packages
> (`packages/ui/package.json`, v0.2.2). Four repos consume it as a declared
> runtime dependency: forge-v6 pins 0.2.1 exactly and imports it in 9 files,
> speedway pins ^0.2.2 across 88 files, walmart-mvp's frontend pins ^0.2.2 across
> 66 files, and versable-foundry references it in 10. forge-v6's lockfile
> resolves it from the registry with a content hash, not a workspace link. The
> kit's effort is not stranded; it is the shared UI layer under most of the
> estate's active front ends. What is fair to say is that forge-v6's *usage* is
> thin (12 references, mostly type imports plus one barrel) relative to
> speedway's 88, and that forge-v6 sits one patch version behind.

Note this correction weakens seat-5's whole §4.1 ranking, since versable-builder
was placed first as the largest effort with the thinnest landing evidence. On
this evidence it is closer to the opposite.

---

## CLAIM C

### C(i) REFUTED: "zero dispatches to a local or gemini lane proves the rule is unenforced"

`/Users/alcatraz627/.claude/scripts/hooks/guard-model-tier.sh` is the sole writer
of `model-dispatch.jsonl`. Line 27:

```
case "$TOOL" in Agent | Task) ;; *) exit 0 ;; esac
```

It is a PreToolUse hook that exits immediately on any tool other than `Agent` or
`Task`, and the field it records is `.tool_input.model`, the Claude sub-agent
model pin. A `q`, `see`, `lm fleet` or `lm gemini` call is a **Bash** tool call.
**The log cannot record a local or gemini lane by construction.** The absence
seat-2 cited is a property of the instrument, not a fact about routing.

The real evidence is in the local-models histories, and the local lanes are alive
in August:

| history | August rows | last run |
|---|---|---|
| `logs/q-history.jsonl` | 39 | 2026-08-26T20:01:12Z |
| `logs/gem-history.jsonl` | 33 | 2026-08-24T09:04:28Z |
| `logs/see-history.jsonl` | 29 | 2026-08-28T10:42:22Z |
| `logs/compare-history.jsonl` | 4 | 2026-08-28T10:42:22Z |

(paths relative to `/Users/alcatraz627/Code/local-models/`)

**Corrected statement:**

> `model-dispatch.jsonl` records only `Agent`/`Task` dispatches
> (`guard-model-tier.sh:27`), so it structurally cannot show a local or gemini
> lane, and its silence on them is not evidence. The local-models histories show
> the lanes are in use: 39 `q` calls, 33 `lm gemini` calls, 29 `see` calls and 4
> `compare` calls in August, the most recent on 2026-08-28. What is genuinely
> unmeasured is the routing *decision*: no instrument records that a task which
> could have gone local went to sonnet instead.

### C(ii) SURVIVES exactly: `lm fleet` and `imagine` dead since 2026-07-13

- `logs/fleet-history.jsonl`: 27 rows, first 2026-07-07T09:23:27Z, **last
  2026-07-13T09:36:43Z**, zero August rows.
- `outputs/imagine-history.jsonl`: 18 rows, first 2026-06-10T10:55:59Z, **last
  2026-07-13T08:32:26Z**, zero August rows.

I checked whether invocations happened without logging. A tree-wide grep for
`"command":"[^"]*lm fleet` across `/Users/alcatraz627/.claude/projects/` returns
real invocations only from local-models build sessions (5f021e2d, 8cc6c6e4) plus
one `lm fleet -h` in a `~/.claude` benchmark sub-agent dated 2026-07-17, which is
a help call that would not log a run. The 70 files matching the string "lm fleet"
are overwhelmingly plan documents naming it as a routing target, not invocations.
The most notable is
`/Users/alcatraz627/Code/Versable/versable-builder` doc 71's Model Plan, which
routes "inspector tests → lm fleet · judge: the node test files (cheap volume)".
**The lane is being planned for and not run.**

### C(iii) SURVIVES with the mechanism: warm-evening-off broken, exit 127

`launchctl print gui/501/com.alcatraz.warm-evening-off` returns `state = not
running`, `runs = 2`, `last exit code = 127`, PATH
`/usr/bin:/bin:/usr/sbin:/sbin`.

Root cause, which seat-2 did not isolate: the target binary resolves fine under
that PATH. I confirmed with `env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin /bin/bash
-c 'command -v /Users/alcatraz627/Code/local-models/bin/warm'`, which succeeds.
What fails is inside it. `bin/warm` calls `ollama` at 11 sites (first at line 14),
`ollama` lives at `/opt/homebrew/bin/ollama`, and homebrew's bin is not on the
launchd PATH. Under that PATH `command -v ollama` returns nothing. **Exit 127 is
`ollama: command not found` raised from inside `warm`, not a missing script.**
The one-line fix is a PATH export in
`/Users/alcatraz627/.claude/scheduled/warm-evening-off/script.sh` or an
`EnvironmentVariables` PATH in the plist.

One correction to severity: `runs = 2` counts runs since the job was loaded, not
since it was created on 2026-07-07, and the machine rebooted on 2026-08-28. So
"it has only ever run twice" is not supported. What is supported is that every
run it has recorded exited 127. Live blast radius is currently nil: `ollama ps`
returns an empty table, so nothing is resident right now.

### C(iv) SURVIVES: FLUX.1-schnell 31 GB still on disk

`du -sh ~/.cache/huggingface/hub/models--black-forest-labs--FLUX.1-schnell`
returns **31G**, 20 days after the 2026-08-10 audit's drop recommendation, and
`imagine` has not run since 2026-07-13.

New fact the seats missed: schnell is not the largest resident model.
`models--Qwen--Qwen-Image` is **49G**, and `models--InstantX--FLUX.1-dev-Controlnet-Canny`
adds 3.3G, for roughly 83 GB of image-gen weights total. Qwen is the kept default
per the generate-image skill, so it is the defensible one, but the reclaimable
total under a "no `imagine` runs in 48 days" reading is closer to 83 GB than 31.

---

## CLAIM D

> "V6 took 10+ days against a 3-4 day 'V1 showable' estimate, only
> content.generate of four modules has been exercised by a human, the paid
> production run has not happened, and no coworker or customer has touched V6;
> meanwhile gcp/ is 'a planning tree with no git' whereas seat-1 says the
> contract tree lives, git-tracked, in versable-foundry."

### D1: the gcp-versus-foundry contradiction is not one

Both statements are true and describe different trees.

- `git -C /Users/alcatraz627/Code/Versable/gcp rev-parse --show-toplevel` returns
  `fatal: not a git repository`, and `gcp/.git` does not exist. Seat-5 is right.
- `/Users/alcatraz627/Code/Versable/versable-foundry` is git-tracked with `canon/`
  and `contracts/` under active commit (`6de58ad` 2026-08-28, `159c764` and
  `71798d3` 2026-08-27). Seat-1 is right.

`gcp/` holds `contract/`, which mirrors foundry's tree (`00-charter.md`, `canon`,
`contracts`, `plans`, `v6`). Seat-1's own finding is that this mirror silently
diverged for ten days before being caught. So gcp/ is an untracked working tree
carrying 45 checkpoint files, roughly 90 screenshots, a `findings/` dir and a
stale contract mirror, at 168 MB on disk. The live canonical contract is
foundry's. **No contradiction to resolve. Both seats should be quoted as
written.**

### D2 SURVIVES as of the record: only content.generate exercised

`/Users/alcatraz627/Code/Versable/gcp/contract/v6/where-we-are.md:17` (written
2026-08-28 00:35, live rows re-measured 02:14):

> "`image.render`, `attribute.normalize` and `parttype.match` have never been run
> by anyone."

Corroborated at `gcp/contract/v6/v2-remains.md:15`. The last 300 lines of
`gcp/NIGHT-CHANNEL.md` mention all four module names (content.generate 10,
attribute.normalize 8, image.render 7, parttype.match 4) but as subjects of
design, docs and route work, not as completed runs. I found no entry claiming a
run of the other three. **UNVERIFIED whether anything changed in the roughly 48
hours between that document and now**, since no newer status page exists. The
freshest artefacts are `gcp/.claude/wal.jsonl` (last entry 2026-08-29T20:30:48Z)
and `gcp/findings/20260830-console-date-formatters.md`, neither of which touches
module runs.

### D3: the paid run, where the claim is now stale

Two distinct facts, and the seats have only the first.

**The run has not completed.** `gcp/NIGHT-CHANNEL.md:1043`, gcp-opus at 02:49:
staged it, signed in (`POST /api/session 200`), uploaded
`065-ACDelco Input.xlsx` through the console (`POST /api/files 200`, 16 rows),
validated the mapping, and then `POST /api/jobs was refused by the auto-mode
classifier`. It stopped rather than routing around, and fixed
`client_job_id console/389-acdelco-paid-run-1` so a retry cannot double-spend.

**But the owner dissolved the category.**
`gcp/_20260828-gcp-watcher-evening.claude.md:15`, under "What the owner decided
today, in his words":

> "**The 'paid run' category is deleted.** Validation is 'does this help the
> testing phase', never the bill. 'Premature optimization about the bill is how
> we've had so many bad days... it should NOT BE A CONCERN BEFORE we have real
> customers.' Build no fence, no ledger, no tier."

So "the paid production run has not happened" is true as a fact about the walk
and misleading as a description of the blocker. As of 2026-08-28 the thing gating
V1 is not an unauthorized spend. It is that nobody has walked three of the four
modules.

### D4 SURVIVES for git: no coworker has touched V6, though access exists

`gh api` on both repos:

| repo | contributors | PRs (all states) | collaborators |
|---|---|---|---|
| `versable-git/versable-forge-v6` | `alcatraz627` (403) only | #1, by alcatraz627, open since 2026-08-21 | alcatraz627, nokusukun, prajwalx, saitejan, anhtuanbui2, cseong413 |
| `versable-git/versable-foundry` | `alcatraz627` (155) only | #1, by alcatraz627, open since 2026-08-21 | same six |

The only non-owner comment on either PR is from `pr-review-automation[bot]`.
`gh api repos/.../commits?per_page=40` returns `["alcatraz627"]` for both.

So five coworkers hold access to both repos and none has committed, opened a PR,
or commented. New fact: **each repo's single PR has been open since 2026-08-21,
nine days, unreviewed by a human.**

The owner is not absent, though. `NIGHT-CHANNEL.md:1115`: "**Owner ran the
deploy**; build SUCCESS 4m37s, serving 9b4b74a". And an agent almost shipped the
finding "the owner has been testing against a fake" before retracting it as false
(`NIGHT-CHANNEL.md:1278`). "No coworker has touched V6" is right. "Nobody has
touched V6" would not be.

UNVERIFIED: the auth service reports `7 users`
(`where-we-are.md`, warden `:6229`, `db=postgres`). I did not query the table, so
whether any of the seven is a coworker rather than a seeded or agent account is
not established. Against it, `where-we-are.md` item 2 still asks the owner to
"Accept the invite and sign into dev", which implies even the owner had not
completed a dev sign-in as of 2026-08-28.

### D5: the 3-4 day estimate, and a goalpost that moved

**The estimate was conditional, and its own stated failure condition was met.**
`/Users/alcatraz627/Code/Versable/versable-foundry/plans/v6-decision-set.md:101`:

> "Wall clock with five streams after day 1, **if every owner gate lands on day
> 0**: **3 to 4 days**"

and lines 109 to 111:

> "three days is real for the agent hours if the streams parallelize as D8 says.
> **It stops being real if any of three things happens:** the day-0 owner gates
> (items 1, 3, 5, and 9's pool if A) land on day 1 or 2..."

Total hands-lane work was priced at **8 to 11 days** on the same line 100. The
3-to-4 was the parallelized wall clock conditional on gates clearing immediately.
`where-we-are.md` §3 shows owner gates still open on 2026-08-28: `pm2 startup`
needing sudo, accepting the dev invite, registering the passport client. So the
estimate's named precondition failed, which the estimate itself said would void
it. Comparing 10 elapsed days to a conditional 3-4 without the condition is not
a fair comparison.

**And the bar changed, written by an agent.** The 2026-08-18 goal, at
`v6-decision-set.md:27`, in the owner's words: *"keep the goal in mind in the
next few days"*, glossed as "V1 showable in three days is the standing goal", with
day 3 defined at line 63 as "showable: one file through each module as an
explicit job, re-run, inspect, logs".

The bar `where-we-are.md:7` now gates on is: "**a non-technical teammate** gets
one real workbook through the console alone." Its earliest written appearance is
`/Users/alcatraz627/Code/Versable/versable-forge-v6/docs/plan/02-overnight-v1-manual.md:3`,
"Written 2026-08-25 by **gcp-watcher**, acting as warden", under the heading "The
sentence". I grepped the full transcript corpus for the phrase. Every hit sits
inside a `tool_result` block, meaning an agent reading agent-written text back.
**I found no instance of the owner typing it.** The owner did ratify a strict
criterion later, on 2026-08-28, as D2a: "V2 criterion strict, all four modules
walked, where 'stranger' means a person who was not here signing in through
auth" (`where-we-are.md:86`).

So the sequence is: owner sets "showable in three days, one file through each
module" on 08-18; an agent restates the bar on 08-25 as an unaided non-technical
teammate; the owner ratifies a strict four-module criterion on 08-28. The bar
became stricter, and the strengthening step was the agent's.

UNVERIFIED: whether the owner said the "non-technical teammate" sentence aloud or
in a transcript that has since been compacted away. My search covers written
occurrences in the current corpus only, so absence here is weaker than proof.

### Verdict: WEAKENED

**Corrected statement:**

> V6's console, runner and auth took roughly ten elapsed days from the 2026-08-18
> decision set. The 3-to-4-day figure it is measured against was a parallelized
> wall-clock estimate explicitly conditioned on every owner gate landing on day 0
> (`v6-decision-set.md:101`, with the void condition spelled out at 109 to 111).
> The same document priced the work at 8 to 11 hands-lane days. Owner gates were
> still open on 2026-08-28, so the estimate's own precondition failed and the
> slip is smaller than a bare 3-versus-10 comparison suggests. The acceptance bar
> also tightened over that window, from the owner's "one file through each module,
> re-run, inspect, logs" (08-18) to "a non-technical teammate gets one real
> workbook through the console alone", first written by the gcp-watcher agent on
> 2026-08-25 and ratified by the owner as D2a on 2026-08-28. Substantively:
> `content.generate` is proven end to end, the other three modules have never
> been run by anyone (`where-we-are.md:17`), the ACDelco run was staged to the
> point of a refused `POST /api/jobs` and not completed, and the owner deleted the
> "paid run" category as a gate on 2026-08-28 ("Validation is 'does this help the
> testing phase', never the bill"). On GitHub, both repos show `alcatraz627` as
> sole contributor with one owner-opened PR each, unreviewed since 2026-08-21,
> while five coworkers hold collaborator access and have used none of it.

---

## New facts the research seats missed

1. **The atone ledger's April and May rows are a v1 backfill.** All 20 April rows
   and 53 of 100 May rows carry `migrated-from-v1`. Any month-over-month series
   crossing that boundary compares two instruments.
   (`/Users/alcatraz627/.claude/atone/events.jsonl`)

2. **The atone schema grew three times during the series.** `session_id` from
   June, `juror_verdict` at 17% of May rising to 94% of August, `stakes` and
   `juror_health` on 285 of 431 rows. Seat-3 treated the ledger as a fixed
   instrument.

3. **`/Users/alcatraz627/.claude/hooks/warn-events.jsonl` exists and answers the
   "does enforcement work" question directly.** 20,421 rows, per-hook fire counts
   with block/soft/nudge action and heed tracking. Top firers all-time:
   `prefer-ripgrep` 6,947, `prefer-tmp-py-over-inline` 4,083, `persona-suggest`
   2,118, `safe-delete` 808. No seat opened it.

4. **The transcript corpus does not predate July in any useful volume.** 2 May
   sessions, 86 June, 1,275 July, 1,904 August, despite
   `cleanupPeriodDays: 365`. Any pre-July denominator is unavailable.

5. **versable-builder is the estate's shared UI dependency**, published to GitHub
   Packages and consumed by four repos across 173 non-publisher files. This
   inverts seat-5's §4.1 ranking.

6. **`walmart-mvp` declares the kit in `frontend/package.json`, not at the root**,
   which is why a root-manifest check misses it.

7. **The warm-evening-off failure is a PATH problem inside `bin/warm`**, not a
   missing script: `ollama` is at `/opt/homebrew/bin/ollama` and launchd's PATH is
   `/usr/bin:/bin:/usr/sbin:/sbin`.

8. **Image-gen weights total roughly 83 GB, not 31.** `Qwen-Image` 49G,
   `FLUX.1-schnell` 31G, `FLUX.1-dev-Controlnet-Canny` 3.3G.

9. **The declared-ready hook's own header documents that it was tuned to block
   less** (`declared-ready-stop.sh:30-37`). Any trend read against it has to
   account for a deliberate precision-over-recall change on 2026-07-02.

10. **Both V6 repos have an unreviewed owner-opened PR open since 2026-08-21**,
    with five collaborators who have never used their access.

11. **The 2026-08-26 self-audit produced 44 atone events in one day**, 30 inside
    three sub-26-minute clusters, three of which are cited by name inside
    `rules/dense-briefing-direct-answer.md` as that file's own RCAs. The ledger
    partly records the audits that read it.

---

## Could not check (UNVERIFIED)

- Whether any of the auth service's 7 users is a coworker rather than a seeded or
  agent account. Would need a DB query, out of read-only scope.
- Whether `image.render`, `attribute.normalize` or `parttype.match` were run in
  the roughly 48 hours after `where-we-are.md` was written. No newer status
  artefact exists.
- Whether the owner ever spoke the "non-technical teammate" sentence outside the
  written record. My grep covers the surviving transcript corpus only.
- Whether the atone rate rise from July to August reflects more failures or more
  filing discipline. No instrument separates them, and the `same-session-repeat`
  classification drift (8% to 31%) means the two months' rows do not mean the
  same thing.
- Sub-agent seat count per month as an alternative denominator. 2,194 sub-agent
  transcripts exist at depth 9 and 11 but I did not date them. If August is
  sub-agent-heavier than July, the real per-unit-of-work rise is smaller than
  2.47x.
