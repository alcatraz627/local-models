# Seat 3: gcc as a factory, evidence audit

## 1. Claim and verdict

**Claim:** the gcc is a factory whose machinery measurably changes agent behaviour
toward the owner's goals, and its growth is proportionate to the behaviour it
corrects.

**Verdict: MIXED, leaning CONTRADICTED on the "measurably changes behaviour"
half; SUPPORTED on the "growth is proportionate to what it corrects" half.**

The gcc is unambiguously a factory in the structural sense. It has a mine
(atone/affirm), a smelter (weekly reviews, i-dream, `/atone`), a foundry
(`rules/`, `hooks/`), and a warehouse (proposals backlog, migrations). Growth
tracks recurrence closely: the four highest-volume atone slugs are exactly
the four with the most elaborate rule text. But the top slugs are not
converging toward zero after their rules were written. Three of the four
spiked hardest in the month immediately after their rule was created or
revised (§3). The mechanism that would prove "it works" (count falls after
rule lands) is measurable and, for the corpus's own highest-severity
recurring failures, it does not fall. The system is real, instrumented, and
growing in lockstep with the problems it names. Whether it is *correcting*
those problems at the rate it is *documenting* them is the open question, and
the data available says no, not yet.

## 2. Size table

| Component | Count | Lines | Growth |
|---|---|---|---|
| `rules/*.md` | 59 files | 4,828 total; 3,357 in the 43 files marked `always` in `rules/00-index.md` | see below |
| CLAUDE.md (global) | 1 file | 206 lines | see below |
| GLOSSARY.md | 1 file | 160 lines | see below |
| always-loaded rule text every session | 43 rules + index + CLAUDE.md | 3,357 + 85 + 206 = 3,648 lines | pure per-session context tax before any project file is read |
| `features/*.md` | 33 files | not summed | |
| `conventions/*.md` | 26 files | not summed | |
| `skills/**/SKILL.md` | 72 files | | |
| `scripts/hooks/*.sh` | 91 scripts | | |
| hooks that hard-block via literal `exit 2` | 4 | `block-curl-post-auth.sh`, `guard-github-agent-marker.sh`, `hook-feedback.sh`, `prevent-unsolicited-index-manipulation.sh` | |
| hooks that block via JSON `"decision":"block"`/deny | 8 (incl. 2 test files) | `atone-stop-gate.sh`, `filename-dot-stop.sh`, `declared-ready-stop.sh`, `guard-cluster-e-smells.sh`, `guard-secret-file-read.sh` plus tests | |
| total hooks that can actually block | roughly 12 of 91, about 13% | the remaining roughly 79 are advisory (`additionalContext`, warnings, telemetry) | |
| hook registrations in `settings.json` `hooks` block | 111 across 13 lifecycle events (`PreToolUse` 42, `PostToolUse` 21, `Stop` 16, `UserPromptSubmit` 15, `SessionStart` 5, others fewer) | | |
| `migrations/*.md` | 56 entries (incl. `_TEMPLATE.md`, `MIGRATIONS.md`), roughly 54 real migrations | | numbered 0001 to 0055, spans 2026-04-16 (`0001-namespace-introduction.md`, per rules git log) through 2026-08-27 |
| `proposals.jsonl` | 611 rows | | `open` 291, `done` 173, `rejected` 145, `superseded` 2 (§3) |
| `logs/model-dispatch.jsonl` | 1,085 rows | | 2026-07: 442, 2026-08: 643. The telemetry itself only starts in July, so no pre-July baseline exists |
| `atone/events.jsonl` | 428 rows | | by month: 04:20, 05:100, 06:34, 07:59, 08:215 (§3) |
| `affirm/events.jsonl` | 23 rows | | by month: 05:7, 06:3, 07:6, 08:7. Affirm volume is flat while atone volume triples |
| `assets/reports/` dated dirs | roughly 194 | | by month: 04:16, 05:18, 06:34, 07:67, 08:59 (partial month, already near July's total) |
| `checkpoints/index.jsonl` | 481 rows | | |

Sources: `wc -l`, `find`, and `jq`/`python3 -c` reads over each file, all run this
session; exact commands reproducible from the transcript.

## 3. The feedback loops, dated, with the gauge checked

**Loop shape (as designed):** mistake, then `/atone` writes `events.jsonl`, then
weekly review or i-dream consolidates, then a `rules/*.md` file is written
(often citing "Graduated from atone slug X"), then optionally a hook is built
to make the rule mechanical, then the slug's future event rate should fall.

17 of 59 rule files (`grep -l "Graduated from atone" rules/*.md`) explicitly
name this provenance, confirming the loop is real and not just narrated.

### Trace 1: `dense-briefing-instead-of-a-direct-answer`

- Events by month: 2026-07: 2, 2026-08: 25.
- Rule file `rules/dense-briefing-direct-answer.md` frontmatter:
  `updated: 2026-08-26`. The rule was written or revised inside the same
  month it is spiking, days before this audit. It states its own provenance:
  "S3, 23 events, 13 in one week of August 2026, 1712 advisory warnings
  issued without the count falling" and "Three weekly audits in a row asked
  for this file."
- Gauge check: cannot yet show post-rule effect. The rule postdates nearly
  all of its own evidence by days. What it does show: an advisory hook fired
  1,712 times on this exact pattern without the underlying count moving,
  which the rule's own text treats as proof advisory-only enforcement
  failed here.

### Trace 2: `literal-request-over-intent`

- Events by month: 2026-06: 1, 2026-07: 4, 2026-08: 17.
- Rule file `rules/literal-request-over-intent.md`: `updated: 2026-08-13`
  (rule text itself says "9 events, S3, four of them in the last seven days
  as of 2026-08-13"). The ledger now shows 22 total for the slug, so 13 more
  events accrued after the rule's most recent revision, all within the same
  month.
- Gauge check: rate did not fall after the 2026-08-13 revision. The 17
  August events span the whole month, not just the days before the 13th.

### Trace 3: `structural-claim-without-reading-code`

- Events by month: 2026-05: 4, 2026-06: 7, 2026-07: 2, 2026-08: 16.
- Rule/hook history from `git log --follow`: the guard was added 2026-06-19
  ("i-dream weekly review 2026-06-14: apply P4/P12, add structural-claim
  guard + performative rule"), and the rule file itself was last touched
  2026-07-28.
- Gauge check: partial support, then reversal. July (2 events) looks like a
  real post-rule improvement versus May to June (4, 7). But August alone (16
  events) is more than double the entire May plus June plus July total (13)
  combined. This is the clearest single case of "worked short-term, then the
  underlying behaviour re-emerged at a higher rate than before the fix,"
  which is exactly the shape a purely advisory, always-loaded text rule
  produces once novelty wears off and the rule becomes background noise in
  a 3,357-line always-on block.

### Trace 4: `declared-ready-without-runtime-exercise`

- Events by month: 2026-05: 3, 2026-06: 3, 2026-07: 7, 2026-08: 16.
- This is the one rule in the sample with a real mechanical Stop-hook gate
  (`scripts/hooks/declared-ready-stop.sh`, confirmed via
  `"decision":"block"` grep), not merely advisory text, per
  `rules/exercise-based-verification.md` (`updated: 2026-06-15`).
- Gauge check: monotonic increase every month since the hook existed, 3, 3,
  7, 16. The one slug with actual enforcement shows the worst trend of the
  four. Either the hook's trigger conditions are narrower than the
  behaviour class, or mechanical enforcement is catching a rising baseline
  it cannot suppress, or (most likely per the rule text's own account of "a
  Swift menu-bar app, a TS refactor, a release script, a not-on-PATH CLI, an
  S3 suite called green off `--collect-only`") the failure mode keeps
  finding new costumes the specific gate doesn't cover, which is consistent
  with §5's structural gap.

### The `prose-smell-stop.sh` case: a named admission of non-enforcement

`rules/audience-aware-writing.md` documents its own hook
(`scripts/hooks/prose-smell-stop.sh`) as running in "measure-first dry-run"
since 2026-07-10. It posts a "WOULD-BLOCK" notice and a `block-dry`
telemetry record, and only actually blocks (`decision:block`) if the
environment variable `PROSE_SMELL_ENFORCE=1` is set, confirmed present in
the hook source (`grep -n "PROSE_SMELL_ENFORCE"
scripts/hooks/prose-smell-stop.sh`, line 198). The rule states promotion to
real enforcement "waits on fire-rate telemetry," meaning the factory has a
QA station whose output gate has been sitting in advisory mode for at least
seven weeks as of this audit.

### Affirm loop, for contrast

Affirm (the positive-reinforcement counterpart) logged 23 events total across
May to August, essentially flat (7, 3, 6, 7 per month) while atone tripled
(100 to 215 May-versus-August, with June/July as a mid-range trough). The
ledger the owner is asked to trust as evidence of "what's working" is an
order of magnitude thinner than the ledger of what's failing, and it isn't
growing alongside it.

## 4. Behavioural goals: stated vs experienced

**Stated (CLAUDE.md, GLOSSARY.md §The principal-agent frame, rules/README.md):**
externalize learning so future agents benefit without full story in context;
route disagreement through evidence not sycophancy; spend the owner's
attention only where it buys alignment; a rule "lives or dies by adherence"
and demotes or promotes accordingly.

**What the numbers say the owner is actually experiencing, dated, in their
own words (§7) and in the rule provenance text:**

- More ceremony, not fewer corrections, in the near term. Three of the four
  highest-volume rules were written or revised in the same month (2026-08)
  as their worst-ever event count, meaning the owner was actively living
  through the failure while also authoring or re-authoring the rule meant
  to stop it.
- A widening gap between advisory and mechanical fixes. Only roughly 12 of
  91 hooks (about 13%) can actually block anything; the rest are
  `additionalContext` nudges the rule `surface-hook-nudges-to-user.md`
  itself says are invisible to the user unless the agent manually renders
  them.
- `rules/dense-briefing-direct-answer.md` states plainly: "1712 advisory
  warnings issued without the count falling," the clearest first-person
  admission in the corpus that an entire enforcement tier (warn-and-hope)
  has been running at scale and not working, on the account's single
  most-fired pattern.

## 5. Divergences: stated purpose vs measured effect

1. **Advisory volume vs behaviour change.** 1,712 prior warnings on the
   dense-briefing pattern, zero measured drop in the underlying slug rate,
   named in the rule's own text, not inferred here.
2. **The rule corpus is itself a scaling cost the doctrine warns about
   elsewhere.** `rules/contain-subagent-token-sprawl.md` and
   `rules/right-sized-code.md` both caution against unbounded
   growth-as-default; the always-loaded rule text is 3,648 lines and rising
   by multiple new or expanded files per week (dense-briefing:
   `updated: 2026-08-26`; literal-request: `2026-08-13`). The same session
   pressure the rules warn against in code is present in the rules
   themselves, with no visible cap or pruning mechanism beyond "max 20
   patterns" in the derived `mistake-patterns.md` (not the raw ledger).
3. **`prose-smell-stop.sh` sits in measured dry-run for 7-plus weeks** while
   the corpus keeps citing it as an enforcement mechanism in
   cross-references, a gap between "this exists as a gate" and "this
   gates."
4. **`declared-ready-without-runtime-exercise` has real hook enforcement and
   the worst trend of the four traced slugs** (monotonic 3, 3, 7, 16). This
   is the most direct evidence against "enforcement works": the mechanism
   exists, is wired, and the behaviour it targets is still accelerating.
   UNVERIFIED whether this is because the hook's trigger surface is
   narrower than the true behaviour class (plausible per the rule's own
   "never wears the same costume twice" framing) or because volume of work
   overall grew in August (§6 uncertainty).
5. **Model-dispatch telemetry only exists from 2026-07 onward** (1,085 rows,
   0 before July). There is no pre-July baseline against which to measure
   whether model-tier routing (a governance goal) has actually shifted
   spend, only a July-to-August comparison (442 to 643), which is also
   consistent with "more work happened," not "routing improved."

## 6. Gaps

- **No raw denominator.** Every count above (atone events, proposals,
  dispatch calls) is a raw monthly total with no normalization against total
  sessions or total tool-calls in that month. An August spike could partly
  reflect more work done, not a worse hit rate. UNVERIFIED, no session-count
  ledger was found in this pass to normalize against.
- **The derived `mistake-patterns.md` view was not independently
  cross-checked** against the raw ledger's slug counts beyond the four
  traced above; its "max 20 patterns" cap means it structurally cannot
  represent the full recurrence picture the raw ledger holds.
- **i-dream's actual pass/fail judgments were not read** (only its presence
  and the `dream/` subdirectory under atone were confirmed to exist); this
  seat did not open `_tldr.txt` or dream output files, so the "does
  i-dream's own gauge show it working" sub-question is UNVERIFIED, not
  answered.
- **Kanban board and claude-ipc usage were not inspected** (out of time
  budget for this seat). The audit brief asked for these; they are absent
  from this report and should be treated as a gap, not a "found nothing."
- **Disproportionate-benefit gap:** the one rule with mechanical enforcement
  (`declared-ready`) shows the worst trend of the traced set, which is the
  opposite of what "mechanical enforcement works better than advisory text"
  would predict, worth a dedicated follow-up seat, since it inverts the
  audit's working hypothesis rather than confirming it.

## 7. Owner quotes (verbatim, dated, 10 shown)

1. "NEVER HALT. If something is a blocker, step aside and complete the rest."
   (`rules/never-halt-on-authority-you-hold.md`)
2. "either behave and write like a proper commenter or do not comment on
   PRs." (`rules/github-agent-marker.md`, 2026-08-24 ruling)
3. "a decision SET is presented as ONE decision page (the format that
   already works), never N rows." (`rules/owner-gate-means-actionable-today.md`,
   owner ruling 2026-08-26)
4. "the note is the real ruling" (same file, same date)
5. "covering your tracks, performative thoroughness in place of actual
   thoroughness." (`rules/pushback-and-self-criticism.md`, pin
   `pin-20260529152121-e6`)
6. "WHY IS THIS FUNCTION EVEN NEEDED OH GOD JUST DECLARE A LOCAL VARIABLE."
   (`rules/speculative-abstractions-without-a-load-bearing-caller.md`,
   2026-05-16)
7. "this all could have been shown as a TUI wizard with options and
   explainers." (`rules/owner-decisions-go-through-a-wizard.md`, 2026-08-20)
8. "boil them down to the questions that TRULY need me, or state the tl;dr
   critical picked choices without the surrounding gossip." (same file,
   same date)
9. "even when asked to 'update their todos' they write to the file but do
   not update in the Claude Code TUI." (`rules/todo-discipline.md`,
   provenance section, 2026-06-09)
10. "where else do we treat examples as quotas" (`rules/examples-as-quotas.md`,
    generalization the owner asked for, pinned across five daily digests
    2026-08-16 through 2026-08-20)

## 8. Uncertainties (specific)

- Whether August's atone spike reflects a real behavioural regression or a
  denominator effect (more total sessions or work in August). No
  session-count ledger was checked.
- Whether the `declared-ready` hook's narrow trigger surface (its own
  `STRIP_RE` pattern excludes collect/dry-run/lint invocations by design)
  means the 2026-08 spike is happening entirely outside what the hook can
  see, versus the hook seeing it and still not stopping it. The hook logic
  was not traced against actual August event transcripts.
- Whether i-dream's own dashboards (not opened this pass) show a different,
  more favorable trend than the raw ledger. Genuinely unknown, flagged as a
  gap in §6, not asserted either way.
- Kanban and claude-ipc sections of the brief are unaddressed; no claim is
  made about them.

## 9. Source table

| Claim | Source |
|---|---|
| Rules count/lines | `ls ~/.claude/rules/*.md \| wc -l`; `wc -l ~/.claude/rules/*.md \| tail -1` |
| always/scoped split | `grep -c "\| always \|" / "\| scoped \|" ~/.claude/rules/00-index.md` |
| Always-loaded line total (3,357) | python parse of `rules/00-index.md` always rows against each file's line count, this session |
| CLAUDE.md/GLOSSARY.md lines | `wc -l ~/.claude/CLAUDE.md ~/.claude/GLOSSARY.md` |
| Skills/features/conventions counts | `find ~/.claude/skills -name SKILL.md \| wc -l`; `ls ~/.claude/features/*.md \| wc -l`; `ls ~/.claude/conventions/*.md \| wc -l` |
| Hooks total plus block-capable subset | `ls ~/.claude/scripts/hooks/*.sh \| wc -l`; `grep -lE '^\s*exit 2\b'` and `grep -lE '"decision"\s*:\s*"block"\|deny'` over same glob |
| settings.json hook registrations | `python3 -c "json.load(...)['hooks']"` over `~/.claude/settings.json` |
| Migrations count | `ls ~/.claude/migrations/*.md \| wc -l` plus head/tail listing |
| proposals.jsonl status/month | python jsonl parse, `ts` field, this session |
| model-dispatch.jsonl lane/model/month | python jsonl parse, this session |
| atone events severity/slug/month | python jsonl parse of `~/.claude/atone/events.jsonl`, `id` field prefix `mist-YYYYMMDD` |
| affirm events month | python jsonl parse of `~/.claude/affirm/events.jsonl`, `id` prefix `aff-YYYYMMDD` |
| Rule `updated:` frontmatter dates | `grep -A2 "^updated:"` on the four traced rule files |
| Rule git history | `git log --follow --format="%ad %s" --date=short -- rules/<file>.md` in `~/.claude` |
| assets/reports monthly counts | `ls assets/reports/ \| grep -oE "^[0-9]{8}" \| cut -c1-6 \| sort \| uniq -c` |
| checkpoints/index.jsonl count | `wc -l ~/.claude/checkpoints/index.jsonl` |
| prose-smell dry-run status | `grep -n "PROSE_SMELL_ENFORCE"` in `scripts/hooks/prose-smell-stop.sh`; corroborated by rule text in `rules/audience-aware-writing.md` |
| "Graduated from atone" rule count (17) | `grep -l "Graduated from atone" ~/.claude/rules/*.md \| wc -l` |
| Owner quotes | verbatim from the rule files cited inline above, each quoted text already present in the CLAUDE.md system context loaded this session |
