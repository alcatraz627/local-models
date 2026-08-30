# Seat 2 - local-models usage audit (2026-08-30)

## 1. Claim and verdict

Claim: "The local-models toolkit is used on real work after its build phase ended
on 2026-07-13; its capabilities serve the goals they were built for."

**Verdict: mixed.** Two capabilities (`q`, `see`) are genuinely load-bearing after
the build wave and stayed in use through August. Three capabilities the 2026-07-13
wave specifically added (`vis-compare`/L3 loop, `lm fleet`, `imagine`) were DEAD at
the scheduled 2026-08-10 audit, exactly as the checkpoint feared, and `imagine`
and `fleet` are still at zero runs as of 2026-08-30, six-plus weeks. `vis-compare`
partially revived after the audit (4 runs, 2026-08-23/28) tied to one real UI
project ("kanban"). The `lm gemini` lane is used, but for work outside this
toolkit's stated goals (a personal company-lookup task), with a 25/98 (26%)
error rate in the post-build period. The self-audit and adoption-review cron
infrastructure itself is the best-adopted thing in the repo: it fired on
schedule and correctly forced the disk-reclaim decision the checkpoint wanted,
and the owner then did not act on it.

## 2. Usage table (capability x month, before/after 2026-07-13 build-end)

Counts from `logs/*.jsonl` / `outputs/*.jsonl`, split at 2026-07-13 23:59:59Z (the
line the repo's own audit script uses as build-end).

| Capability | Runs before 07-13 | Runs after 07-13 | Last run | Callers | Failure signal |
|---|---|---|---|---|---|
| `q` (ask/qa/title/cmd/review intents) | 480 | 1742 | 2026-08-26 | mixed: 767 `title` (fire-and-forget tab titling), 678 `ask`, 213 `qa`, 21 `review`, 7 `cmd` | 0 explicit `error` field hits in 1742 post-build rows, `jq 'has("error")'` returns all false, but see §5 on what this metric can't see |
| `see` (vision reads) | 29 | 191 | 2026-08-28 | `ui` (structural inventory), `diff` (vis-compare evidence), `ocr` | no failure field in schema; not separately tracked |
| `lm fleet` (fan-out) | 27 (all 2026-07-07 to 07-13) | **0** | 2026-07-13 | none since build | n/a, never invoked again |
| `imagine` (image-gen) | 18 (all 2026-06-10 to 07-13) | **0** | 2026-07-13 | none since build | n/a |
| `lm gemini` | 164 (Jul, mostly build-window) | 33 (Aug) | 2026-08-24 | one external project session `studio_search_jul_26-fable` (company/website lookup, not a local-models goal) | 25 `error`(timeout) of 98 post-build calls, **26%** |
| `see diff` + `/vis-compare` | 26 (Jul, all build-window) | 4 (Aug: 08-23 x3, 08-28 x1) | 2026-08-28 | one real UI project (kanban board dark/light + hover-state diffing) | 0 declared, but one comparison scored `comparable: "poor"` / `similarity: "different"`, a real divergence caught, not a tool failure |
| `lm probe`, `asset-verify`, `findings-gate`, `e8-dom` | n/a (no history stream) | n/a | unknown | none found | the repo's own 08-10 audit says "check by hand, no history stream" for these; this seat found no evidence either way |

Sources: `logs/q-history.jsonl` (2222 lines), `logs/see-history.jsonl` (220),
`logs/fleet-history.jsonl` (27), `logs/gem-history.jsonl` (197),
`logs/compare-history.jsonl` (30), `outputs/imagine-history.jsonl` (18), all
queried with `jq -r '.ts[:7]' <file> | sort | uniq -c` for month buckets and
`select(.ts > "2026-07-13T23:59:59Z")` for the post-build split.

## 3. Built-for vs. actually-does

| Group | Built to do (docs/CAPABILITIES.md, CLAUDE.md) | Actually does today |
|---|---|---|
| `q` | quick local answers, macOS commands, schema-constrained agent-worker calls, session-title generation | **load-bearing, but mostly infrastructure, not "real work."** 767/1742 post-build calls (44%) are the `title` intent, fire-and-forget 2-5-word tab titles (`intents/title.toml:2`: "fire-and-forget"), not the ask/qa work the tool exists to answer. `ask`+`qa` (891 calls, 51%) is the genuine usage. `review` (21 calls) is thin and mixed: several against real diffs (`src/broker/router.ts`, `plugin/scripts/watch-inbox.sh`) but also toy fixtures (`def add(a,b): return a-b # bug`), suggesting a chunk of "review" traffic is testing the tool, not using it. |
| `see` | structural UI inventory, OCR, grounded vision Q&A, feeding vis-compare | **load-bearing.** 191 post-build calls, still active through 2026-08-28, with a real UI project (kanban board screenshots) driving `ui`/`ocr`/`diff` modes in the last week of the audit window. |
| `lm fleet` | batch fan-out (rules/model-tier-routing.md: "volume audit/verify -> `lm fleet`") | **dead.** 27 runs, all inside the 2026-07-07 to 07-13 build window (the routing experiment against real E1 code, per `docs/STATE.md` DONE ledger). Zero calls since. The gcc's own routing rule promises this lane and nothing routes to it, see §4. |
| `imagine` | local image generation (mflux/Flux, $0, offline) | **dead.** 18 runs, all inside the build window (2026-06-10 to 07-13). The 2026-08-10 audit (`~/.claude/assets/reports/20260810-local-models-review.md`) flagged this explicitly: "0 schnell generation(s), **DEAD** (0), THE 31GB WAS WASTED. Drop it." As of this audit (2026-08-30) the FLUX.1-schnell weights are **still on disk** (`du -sh ~/.cache/huggingface/hub/models--black-forest-labs--FLUX.1-schnell` gives `31G`), the audit's forced recommendation was never acted on. |
| `lm gemini` | large-context ingestion / breadth research, per `rules/model-tier-routing.md` ("large-context ingestion / mass ideation -> `lm gemini` session, digest back") | **used, but off-mission and unreliable.** All 33 post-build August calls are from one session (`studio_search_jul_26-fable`) doing a personal task, finding websites/contact emails for Bengaluru event/photography businesses, not the ingestion/research-digest role the routing rule describes. 25 of those calls (76%) errored with `"response":"timeout"`. |
| `see diff` / `/vis-compare` (L1/L2/L3) | "does B faithfully imitate A", the newest, largest capability per CLAUDE.md | **DEAD at the scheduled audit, partially revived after.** 08-10 audit: 0 compare runs, 0 loop rounds, both flagged DEAD, with a recommendation to consider retiring the skill from the menu. Since then, 4 runs (2026-08-23 x3, 2026-08-28) tied to a real "kanban" UI project, including one `comparable: "poor"` result that shows the tool actually catching a divergence, not just running clean. |
| The 5-capability 2026-07-13 wave (asset-verify, findings-gate, E8 web lane, imagegen convergence, plus vis-compare) | shipped through `/bloop` with an adversarial gate finding a real defect 8/8 times (CLAUDE.md, `_checkpoint.claude.md`) | **mostly unverifiable from histories.** Only vis-compare has a history stream and it shows revival; asset-verify, findings-gate, and the E8 lane have no logging stream at all, the repo's own 08-10 audit says "check by hand," and this seat (read-only, no inference) found no file or log evidence either way. This is a genuine coverage gap, not a dead-vs-alive finding, see §5. |

## 4. Divergences and likely mechanism

- **The routing rule promises a lane nothing enforces.** `rules/model-tier-routing.md`
  states "volume audit/verify -> `lm fleet`" and "large-context ingestion / mass
  ideation -> `lm gemini` session, digest back" as standing doctrine, always-loaded
  into every session (per this transcript's own system reminder). `lm fleet` has
  had zero calls since 2026-07-13 despite that promise; `lm gemini` is called, but
  for a task category (personal outreach research) the rule doesn't describe.
  `~/.claude/logs/model-dispatch.jsonl` (1085 dispatch records, 2026-07-07 to 08-29)
  shows every logged sub-agent dispatch going to sonnet (698), opus (298), fable
  (44), or haiku (10). **Zero entries route to a local/gemini lane**, confirming
  the rule is advisory text the gcc's own telemetry never exercises as a dispatch
  target. This matches the account's own documented pattern
  (`rules/skill-spec-update-not-honored-by-running-session.md`): a spec with no
  enforcement at the dispatch point is invisible to a running session.
- **`imagine`/`fleet` likely died because the project moved on, not because they
  failed.** No transcript in `~/.claude/projects/-Users-alcatraz627-Code-local-models/`
  postdates 2026-07-13 (the last build-session transcript is
  `8cc6c6e4-...jsonl`, 2026-07-13 15:32) except this audit's own session
  (`e2e2fc30-...`, 2026-08-30). Every post-build `q`/`see`/`gemini`/`compare` call
  in the histories therefore came from **other project directories** invoking the
  globally-installed `lm`/`q`/`see`/`imagine` binaries, the toolkit is used
  cross-project as designed, but nobody has sat down inside this repo's own
  directory to drive `fleet`/`imagine` since the build finished.
- **The forced decision from the 08-10 audit was made and then not executed.**
  The audit report explicitly frames schnell as a binary choice ("used -> keep.
  Unused -> drop it and reclaim 31GB") and the checkpoint calls this "the
  corrective" for an earlier miss where the agent didn't surface the zero-cost
  alternative. The weights are still present 20 days later. This is a
  human-side gap (nobody ran the trash command), not a tooling gap.
- **`review`'s three commits (2026-07-24, `cf3bb3a`/`91e8ae3`/`aa91c57`) landed
  ahead of any post-fix usage burst.** The only `review`-intent call after
  2026-07-24 is a single one on 2026-08-26, three weeks later, one call. The
  fixes (structured-mode failure contract, `--findings` tier default) shipped
  without a visible adoption signal either confirming or refuting them in
  production use.

## 5. Gaps

- **Structural:** `asset-verify`, `findings-gate`, and the E8 web lane have no
  history stream at all (CLAUDE.md's own "the histories are the API" claim does
  not cover them). This means the toolkit's own adoption-audit mechanism is
  structurally blind to three of the five 2026-07-13 capabilities, the 08-10
  report says so itself ("check by hand, no history stream"). A capability that
  can't report its own usage can't be told apart from a dead one by the exact
  audit built to make that call.
- **Identification:** `q-history.jsonl` and `see-history.jsonl` carry no caller
  field (no cwd, no project id, no session id in most rows; a `cid` field exists
  on some but is not a project identifier). This seat could not attribute
  post-build calls to specific projects beyond the one case (`gem-history.jsonl`'s
  `session` field) where the schema happens to carry it. Any per-project adoption
  claim beyond "some other project called it" is unverifiable from the histories
  as they're currently shaped.
- **Behaviour quirk, disproportionate cost:** the `lm gemini` lane's 26%
  post-build timeout rate, all inside one real (if off-mission) research task,
  suggests either a rate-limit/network issue specific to that workload
  (batch small-business lookups) or a reliability gap in the lane the
  routing rule recommends for exactly this shape of work ("large-context
  ingestion / mass ideation"). Not conclusively diagnosed from logs alone, the
  `error` rows all say `"response":"timeout","ms":0"`, consistent with either a
  client-side abort or an upstream stall, and this seat did not run inference to
  distinguish them (out of scope, read-only).
- **The `warm-evening-off` LaunchAgent is currently broken.** `launchctl print`
  shows `last exit code = 127` (command not found) against a minimal PATH
  (`/usr/bin:/bin:/usr/sbin:/sbin`). This is the scheduled backstop that enforces
  the repo's own "no idle penalty" hard rule (CLAUDE.md: "Nothing stays resident
  unless explicitly pinned or leased. A tool that silently keeps 23 GB warm is a
  bug."). A silently-broken shutdown cron is exactly the failure mode that rule
  exists to prevent, and this seat found no fresher fix commit for it.
  `com.alcatraz.lm-self-audit` and `com.alcatraz.local-models-ollama` are healthy
  (self-audit has produced a weekly digest every week through 2026-08-23; ollama
  server has an active PID).

## 6. Owner quotes (dated, verbatim)

1. "schnell download will be called a failure if no one even uses it." Quoted in
   `_checkpoint.claude.md` (2026-07-13T10:40:00+0530), attributed to the user
   in-session; this exact line drove the 08-10 audit's schnell keep/drop framing.
2. "Being able to parse and understand the image right now is way more valuable
   to me than screenshot recall." 2026-07-10, per
   `.claude/projects/.../memory/user_images_ephemeral_parse_now.md`, declining a
   screenshot-memory pipeline.
3. Checkpoint framing of the user's stated expectation (2026-07-13, indirect
   quote in `_checkpoint.claude.md` § Current Expectation): "The user expects a
   clean, well-documented hand-off and then a break. They are NOT waiting on
   anything. They explicitly want these capabilities **used**, not merely
   built."
4. Memory `local_agentic_tier_use_case.md` (session `460e2aa4`, undated within
   the file but the memory's own frontmatter session ties it to the build
   period): the user's target for a heavy local coding tier is "structured,
   agentic, multi-file feature work, the way they use Claude Code," with
   efficacy, not resource cost, as the gate, and calibration "very capable
   junior pair, not Opus offline."

No further verbatim owner quotes about local-models usage (post-07-13) were
found in the memory directory or in the one post-build project transcript
searched; this seat did not exhaustively read full transcripts (per scope: grep
only, "do not read whole").

## 7. Uncertainties

- Whether `asset-verify`, `findings-gate`, and the E8 web lane were used at all
  after 07-13 is genuinely unknown from this machine's files: they have no log
  stream, and this seat did not run them (out of scope) or search other
  projects' output directories for their artifacts (e.g. `e8-capture-*.json`),
  which the repo's own audit script names as the way to check them by hand.
- The `lm gemini` 26% timeout rate's cause (network, rate limit, or a lane
  defect) is not established, only that it happened, when, and on what task.
- Whether any `review`-intent call after 2026-07-24 came from a real PR/diff
  versus a test invocation could not be fully separated; the single 2026-08-26
  call's prompt content was not inspected in this pass (only its timestamp,
  via `jq -r 'select(.intent == "review") | .ts'`).
- Whether other projects' sessions invoke `lm fleet` or `imagine` through
  scripts this seat didn't search (e.g. a cron or CI step outside
  `~/.claude/logs/`) is not ruled out, only that the toolkit's own histories,
  which CLAUDE.md calls "the agent API," show zero.

## 8. Source table

| Claim | Source |
|---|---|
| Monthly/post-build run counts, all capabilities | `logs/q-history.jsonl`, `logs/see-history.jsonl`, `logs/fleet-history.jsonl`, `logs/gem-history.jsonl`, `logs/compare-history.jsonl`, `outputs/imagine-history.jsonl`, `jq -r '.ts[:7]'`/`select(.ts > "2026-07-13T23:59:59Z")` queries, run 2026-08-30 |
| `title`/`ask`/`qa`/`review`/`cmd` intent split | `jq -r '.intent' logs/q-history.jsonl` post-build, `intents/title.toml:2` for the "fire-and-forget" framing |
| `review` commits and dates | `git log --oneline -- bin/review` gives `cf3bb3a`, `91e8ae3`, `aa91c57` (2026-07-24 per `cf3bb3a`'s own message) |
| 08-10 scheduled audit fired and its verdicts | `~/.claude/assets/reports/20260810-local-models-review.md` (full text quoted in §3/§4); the generating script `~/.claude/scripts/local-models-review.sh` |
| schnell still on disk | `du -sh ~/.cache/huggingface/hub/models--black-forest-labs--FLUX.1-schnell` gives `31G`, run 2026-08-30; `config.sh:24-25` still documents it as "dropped" |
| Model-dispatch telemetry shows no local/gemini-lane sub-agent dispatches | `~/.claude/logs/model-dispatch.jsonl`, 1085 lines, `jq -r '.lane // .model'` gives sonnet 698 / opus 298 / fable 44 / haiku 10 / null 35, zero local/gemini entries |
| No post-build project transcript exists except this audit session | `ls -la ~/.claude/projects/-Users-alcatraz627-Code-local-models/*.jsonl`, latest pre-audit file `8cc6c6e4-d1b1-4b8c-8c47-989d3ed2af4a.jsonl` dated 2026-07-13 15:32 |
| `warm-evening-off` broken | `launchctl print gui/$(id -u)/com.alcatraz.warm-evening-off` gives `last exit code = 127` |
| `lm-self-audit` healthy, weekly digests through 08-23 | `ls logs/self-audit/` (files through `20260823.md`); `cat logs/self-audit/20260823.md` |
| Owner quotes | `_checkpoint.claude.md` (2026-07-13), `.claude/projects/-Users-alcatraz627-Code-local-models/memory/user_images_ephemeral_parse_now.md`, `.../memory/local_agentic_tier_use_case.md` |
| Checkpoint text ("next move is NOT more building, use the stack, 2026-08-10 audit, DEAD if nobody does") | `_checkpoint.claude.md:11-16`, symlinked from `_20260713-vis-ab-3c.claude.md` |
