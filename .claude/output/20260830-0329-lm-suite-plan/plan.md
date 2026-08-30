# Plan: give the lm suite its callers

2026-08-30. Produced by `/build-change` from `report.md` and `lane-1..5` in this directory. Owner's ask, verbatim: "check what kind of usage do I actually get out of the lm suite, IMO its the local code model / lm gemini gateway / image and vision models, especially the driver loop with the /ui-gripe related skills. Examine in detail for each. Do a structural analysis of what is being attempted, the gaps, the ideal workflow, how to bridge the gap, and actual research and a /plan to build that out for all. Also do the same for the performance / other aspects of running this. Also stuff like better models / tools / custom skills / more involved agent involvement in driving the dumb tools, etc".

This plan stops before implementation. Each slice goes through `/bloop` (the repo's own adversarial gate, 8/8 real defects found on its first runs).

## 1. Class and refuse conditions

Class: **Capability**. The suite cannot today run a UI review loop end to end, dispatch a judged unit to the local coder, or digest a corpus through gemini with a schema. It is really five changes; this plan sequences them and the first slice is the smallest.

One Behaviour-class fix rides in front because it is ten minutes and it is the repo's own hard rule: the residency schedule.

Refuse conditions, each fired with evidence:

1. Behaviour wrong or absent. `launchctl print gui/501/com.alcatraz.warm-evening-off` shows `last exit code = 127`; `~/.claude/logs/launchd/warm-morning.err.log` holds 21 lines of `bin/warm: line 47: ollama: command not found`; the warm-morning plist is absent from `~/Library/LaunchAgents/`. The L3 loop has zero live-UI rounds (`logs/compare-history.jsonl`: 26 build-week rows, 4 organic). `lm fleet` has zero code-tier runs (`logs/fleet-history.jsonl`, 27 rows, all `summarize` on a 3b model).
2. Cost paid repeatedly. Every `see` round on live UI is hand-composed (a Playwright/chrome-devtools call, then a `see` call); `see --ui` p50 20.4 s, p95 42.5 s (lane-5 §1). Gemini: 8 timeouts of 33 August calls, each retried by hand (lane-2 §1). First `q` of every session pays a cold load because nothing pins (q-history max 142 s).
3. Constraint violated. `CLAUDE.md` hard rule 1 (no idle penalty, backstop by schedule) is met only because the backstop is broken; `docs/STATE.md:38,78` document `warm-morning` as live. `rules/model-tier-routing.md` promises `lm fleet` and `lm gemini` lanes that nothing dispatches to (`rg -l "lm gemini|lm fleet" ~/.claude/skills` is empty).

Not a refuse condition, and therefore not in this plan: image generation. Zero demand (lane-4). One removal action (trash schnell) is listed under sequencing as a default, no build.

## 2. Problems, as triples

| # | Observation | Cost | Check that flips |
|---|---|---|---|
| P1 | `bin/warm:47,53,55` call bare `ollama`; launchd PATH is `/usr/bin:/bin:/usr/sbin:/sbin` | both warm jobs dead; snappy companion not delivered; backstop inert 8 weeks | `launchctl kickstart -k gui/501/com.alcatraz.warm-evening-off` then `launchctl print … \| rg 'last exit code = 0'` |
| P2 | no capture or re-render verb: `rg -n "playwright\|chrome-devtools\|screencapture" bin/ lib/` returns nothing | L3 loop unrunnable on live UI; agent composes shell each round | `see reshoot <loop-dir>` produces a new round image comparable to round 1 |
| P3 | `lib/vis-ledger.py:73-74` keys rounds on `divergences` only | ui-verify claims and ui-gripe findings cannot loop | ledger ingests a round whose ids came from `lm ui-verify --json` and reports transitions |
| P4 | no `caller` field in `see-history.jsonl` (`bin/see:42`); judge skills never call `skill-log.sh record` (`rg -l 'skill-log.sh record' ~/.claude/skills/{ui-gripe,vis-compare,ui-categorical-check}/SKILL.md` empty) | usage invisible; the 08-10 review nearly retired a used lane | `jq -r .caller logs/see-history.jsonl \| tail -1` non-empty; `skill-log.sh` shows a `ui-gripe` row after one run |
| P5 | no dispatch point for the code tier: routing rule names no command; `probe/runs/*.md:24,42` human verdicts unticked | the one proven pattern (33/33) never reused | `/dispatch-local` refuses without a red judge, then lands one green run logged as intent `code-dispatch` |
| P6 | `lib/gemini:28` `TIMEOUT=180`; `lib/gemini:81` never passes `--output-format json` | 8/13 recorded timeouts; prose contract regex-trimmed at `lib/gemini:216-231` | `lm gemini digest` returns parseable JSON; a 250 s web-lookup call completes under the new default |
| P7 | `lib/gemini` writes no token counts; "Claude verifies" has no mechanism (`rules/model-tier-routing.md:34`) | quota invisible; digests trusted as fact | `gem-history` rows carry `bytes_in/bytes_out`; digest output carries a `verified` sample with grep hits |
| P8 | `docs/STATE.md:38,78` claim warm-morning live; PENDING lists shipped vis-compare | the orientation doc lies to the next agent | `rg -n warm-morning docs/STATE.md` shows the corrected line |

Watch, not chase: the q-history 142 s outlier (probably cold load, unconfirmed); `lm opencode` usage (unlogged, unknown); the Gemini key type ahead of the September cutover (owner check, not a build).

## 3. Inheritance ledger

| Decision | How the repo already does it | Evidence | Adopting or deviating |
|---|---|---|---|
| history logging | one JSONL row per run via `_lib.sh` helpers, `history`/`show` verbs | `bin/_lib.sh:21-36`, `bin/see:42` | adopt; add fields, never a new log format |
| structured errors | named failure classes, exit codes, never raw stderr | `lib/gemini:198`, `lib/vis-ledger.py:35` shape checks | adopt for `reshoot` and `dispatch` |
| trust gate | computed set differences, fail-closed containment | `lib/vis-ledger.py:9,73`, `lib/findings-gate.py` | adopt: the gemini verification stub follows findings-gate's fail-closed shape |
| residency | `warm on/off`, Ollama's own registry as truth, no state file | `bin/warm:14` | adopt; PATH fix only |
| fan-out | `lm fleet -j N`, process-level, judge intent registered as a `q` intent | `lib/fleet:4,34` | adopt; `code-dispatch` is a new intent TOML, not a new runner |
| loop artefacts | one dir per loop, rounds as JSON, contact sheet | `docs/10 §10`, `outputs/see/<ts>/` | adopt; `reshoot` writes into the same loop dir |
| capture driver | none in `lm`; chrome-devtools and playwright MCP exist only in gcc skills | `rg` empty in `bin/ lib/` | **new precedent**: a `lib/reshoot` that shells to a headless capture (playwright CLI or `screencapture`/`ax`), recorded in the loop dir |
| skill telemetry | `skill-log.sh record` at post-run | `~/.claude/skills/bloop` (62 rows) | adopt in the four judge skills |
| verification gate | `scripts/verify.sh` (37 checks) + `vis-battery.py` (50) | `scripts/verify.sh` | every slice adds a check to one of them before the capability lands |
| launchd PATH | `lm-self-audit` dodges it by `bash /abs/path`; the warm jobs do not | `~/.claude/scheduled/warm-evening-off/script.sh:9` | deviate: fix at `bin/_lib.sh` so every `bin/*` is safe under launchd |

## 4. Parity ledger

| Must still hold | Why | Check that would catch its loss |
|---|---|---|
| identical image pair yields all-zero evidence | fabrication guard, adversarially validated | `vis-battery.py` F1 stays green |
| status words (fixed/persisting/regressed) are computed, never model-emitted | the L3 contract | `vis-battery.py` F10 stays green after the ingest generalisation |
| malformed ledger shapes fail loudly | F10b/F10c | same battery rows |
| `q` warm-aware `keep_alive` (pinned model never un-pinned by a call) | the no-idle contract | `warm on; q "x"; ollama ps` still shows the companion |
| `--no-read` diff rounds stay ~1 s and skip is not failure in telemetry | loop speed | `see diff A B --no-read --json` `ms` < 3000 and no `error` row |
| `see --ui --json` stays schema-valid on the big tier | agents parse `.data` | `lm ui-verify` self-test in `verify.sh` |
| gemini failure classes and exit codes unchanged | callers branch on them | `lm gemini` with no key still exits 11 `gemini_unavailable` |
| `imagine` preflight refuses half-downloaded models | the 38-minute hang | untouched; `verify.sh` preflight check |
| `lm fleet` judge-gating and `-j` cap | RAM protection | existing fleet check in `verify.sh` |
| `warm off all` sweeps every resident model | the backstop's meaning | after the PATH fix: `warm on; warm off all; ollama ps` empty |

## 5. Directives

| ID | Directive | Check |
|---|---|---|
| D1 | In `bin/_lib.sh`, prepend `/opt/homebrew/bin` (via `brew --prefix` with a literal fallback) to PATH before any `ollama`/`hf` call; re-register `warm-morning` through gcc-schedule; add a launchd-status line to `scripts/self-audit.sh` | P1 check; next Sunday's digest carries a `launchd:` line; `verify.sh` gains "warm jobs exit 0" |
| D2 (parity) | Correct `docs/STATE.md` lines 38 and 78 and the PENDING block | P8 check |
| D3 | Add `caller` (cwd) and `resident_before_call` to `see-history` and `q-history` rows | P4 check; `lm doctor` prints a cold-load rate |
| D4 | Add `skill-log.sh record` to `ui-gripe`, `vis-compare`, `ui-categorical-check`, `designer-reviewer` post-run | P4 check |
| D5 | Generalise `lib/vis-ledger.py` round ingest to `{id, class, status}`; keep `divergences` as one producer | P3 check; battery F10 rows green; new F11 row for a ui-verify-shaped round |
| D6 | Record a capture recipe at loop open (`kind: web\|native\|static`, url/app, viewport, wait rule) in the loop dir; add `see reshoot <loop-dir>` that replays it and runs the comparability gate | P2 check; F12 battery row: a recipe with a changed viewport is rejected |
| D7 | `lib/reshoot-web`: headless capture via playwright CLI with a settle heuristic, writing into `outputs/see/` conventions | one command turns a URL into a round image; `verify.sh` check against a local static page |
| D8 | A `/ui-loop` gcc skill that runs steps 0 to 6 of report §3.1, with the pre-flight "verdict cites the full-frame inventory" check at ingest | one live loop on the kanban board reaches `stop: policy-pass` or `stall` with a ledger |
| D9 | Score the four `probe/runs/qwen3.6*` files by hand (owner or a fresh opus seat with the owner's rubric) | no `☐` left in those files |
| D10 | `intents/code-dispatch.toml` + `/dispatch-local` skill: refuse without a red judge, restate the judge verbatim, call `lm fleet` or `q -m code`, apply, re-judge, escalate on second red, log intent `code-dispatch`; log `lm opencode` sessions | P5 check; `fleet-history` shows a `code-dispatch` row |
| D11 | Run five E1-shaped dispatches on varied real tasks (one per repo: local-models, kanban, forge-v6, slack-automation, versable-builder) and record green/red | a table in `probe/runs/dispatch-2026-09.md` with n≥5 |
| D12 | `lib/gemini`: default timeout 300 s, `--output-format json` passthrough, `bytes_in/out` in history, `digest <target> --schema` and `research "q"` verbs, a grep-back verification stub that fails closed on zero hits | P6, P7 checks; `verify.sh` gemini row extended |
| D13 | Wire `/pyramid-sweep`'s mining phase to `lm gemini digest` when the corpus exceeds the local tier's budget | one pyramid-sweep run shows a `gem-history` row with `session=pyramid-sweep` |
| D14 | Measurement session A: MTP on the MLX runner, gemma4:26b then qwen3.6, Ollama 0.33.0, gated by `lm probe` | a dated `docs/05` §1 addendum with tok/s and probe verdicts |
| D15 | Measurement session B: `OLLAMA_NUM_PARALLEL` 1 vs 2 under `lm fleet -j 2`; `mlx_lm.server` side by side on the code tier | same addendum |
| D16 | Bake-off on the i-dream dashboard fixture: gemma4:26b vs Qwen3-VL (MLX-VLM) vs Moondream 3 for `--ui`; OmniParser boxes as an L1 extractor prototype | a `docs/08` addendum with per-model verbatim/structure scores; swap `UI_VISION_MODEL` only on a win |
| D17 (owner) | Pull Qwen3-Coder-Next 80B-A3B Q4_K_M and probe it | probe run file with human verdicts |

## 6. Skeleton

```
bin/_lib.sh        lm_path_fix()         # D1, sourced first by every bin/*
                   hist_row KEY=VAL…     # D3, adds caller, resident_before_call
bin/see            see reshoot <loopdir> # D6 → lib/reshoot
lib/reshoot        replay(recipe.json) → round-N.png | error{not_comparable}
lib/reshoot-web    capture(url, viewport, wait) → png      # D7, playwright CLI
lib/vis-ledger.py  ingest(round: {items: {id: {class, status}}})   # D5
                   producers: vis-compare divergences | ui-verify claims | ui-gripe findings
intents/code-dispatch.toml                # D10
lib/gemini         digest <target> --schema S → {claims[], sources[], verified{hits,misses}}
                   research "q" → {answers[], null_when_unsure}  # D12
~/.claude/skills/ui-loop/SKILL.md         # D8: steps 0..6, pre-flight at ingest
~/.claude/skills/dispatch-local/SKILL.md  # D10
```

Data shape shared by every judge (D5): `{"id": str, "class": str, "status": "open|fixed|persisting|regressed|new", "evidence": [path]}`.

## 7. First running slice

Slice 0 (ten minutes, Behaviour): D1 + D2. Command: `launchctl kickstart -k gui/501/com.alcatraz.warm-evening-off && launchctl print gui/501/com.alcatraz.warm-evening-off | rg 'last exit code'`. Proof: `= 0`, and `warm on && sleep 5 && ollama ps` shows the companion, and `warm off all && ollama ps` shows nothing.

Slice 1 (the first capability slice, one day): D3 + D5 + D6 on the static-pair case only. Command: open a loop on the existing kanban dark/light pair (`outputs/see/` rows from 08-23), ingest a `ui-verify --json` claim set as round 1, run `see reshoot` on the static recipe, ingest round 2, and read `vis-ledger status`. Proof: transitions computed for claim ids, F10/F11/F12 green, `verify.sh` count rises by 3.

Everything after slice 1 (D7, D8, the web capture, the code dispatch, gemini) builds on an observed loop rather than a described one.

## 8. Sequencing

1. Slice 0 (D1, D2). Default: also `trash ~/.cache/huggingface/hub/models--black-forest-labs--FLUX.1-schnell` (31 GB, ruled 08-10).
2. Slice 1 (D3, D5, D6 static).
3. D4 (skill logging) and D9 (probe scoring, 30 minutes of the owner's time or an opus seat with his rubric).
4. D7 + D8: the web capture and the `/ui-loop` skill; first live target the kanban board, second versable-forge-v6 dev.
5. D10 + D11: code dispatch skill and the five-run evidence table.
6. D12 + D13: gemini verbs and pyramid-sweep wiring.
7. D14, D15, D16: measurement sessions, each a half day, each ending in a docs addendum and a probe verdict.
8. D17 only on the owner's call.

Model plan for the build: each slice through `/bloop` (main seat implements, opus medium adversarial validator, no fable seats); D11 dispatches run the local code tier by design; D16 bake-off reads run local VLMs, native Claude vision as ground truth.

## 9. Must not touch

`lib/vis-compare.py` extractors (validated twice; only consumers change). `bin/imagine` and the HF cache beyond the schnell trash. `config.sh` tier assignments until a probe or bake-off says otherwise. `MAX_LOADED_MODELS=2` and `KEEP_ALIVE=0` in `bin/lm-serve`. The `NOTE`-style comments in `config.sh` on vision model choice (they record measured trades).

## 10. Speculative appendix, not authorized by this plan

A faster `--ui` model swap before the bake-off. OmniParser bundled (AGPL review first). `mlx_lm.server` as a second serving runtime with a protocol shim. Dropping Qwen-Image (re-audit in six weeks). EAGLE/Medusa heads for Qwen3.6 (nothing shipped for MLX). A `q render` verb. Folding `q` into `llm-mini`.

## 11. Owner rulings this plan waited on

Presented on decision page `lm-suite-plan-0830` and answered 2026-08-30. Section 12 records the answers and supersedes section 8's ordering.

## 12. Rulings applied, 2026-08-30 (this section governs)

Answer string: `D1c D2a D3a D4a`. All defaults agreed. Two notes.

The frame is the def-01 note, verbatim: "since AI subscriptions are so accessible and much better than local models and I don't have a regulatory or cost reason to run local models directly (even lm gemini counts in this tier), their usage is only going to be as complements to the places where claude has limitations, the vision and sweep models being two big use cases. Lets also review from that perspective and see what can be dropped / changed / added." Saved as project memory `project-complements-only-doctrine`.

The resequenced order, per D1c:

1. Slice 0 is DONE as of 2026-08-30. The PATH fix landed in `bin/_lib.sh`. Both warm jobs run green under launchd. warm-morning is re-registered at daily 09:30 through gcc-schedule. The launchd health block in the weekly self-audit was exercised in both its failing and passing states. STATE.md is corrected. schnell is trashed and 31 GB reclaimed. verify.sh reads 34 passed, 3 failed. The 3 failures predate this change: one guard-model-tier pipe-test and two checks for retired gcc schedules named `image-tools-review` and `tier-telemetry-review`. They are flagged at the end of this section.
2. Gemini robustness comes next. This is D12 plus D13 with the scope widened to match the owner's words, "I want gemini to be more robust, a lot more robust". Concretely: a 300 s default timeout that is workload-aware. Retry with backoff on timeout rather than only on vanished sessions. `--output-format json` passthrough. Byte counts in gem-history. The `digest` and `research` verbs with the grep-back verification stub. A fallback from `gemini_unavailable` to `gemma4:26b` long-context instead of a bare structured failure. The key-type check ahead of the September cutover is surfaced to the owner, never performed by an agent. The Batch API is investigated for the classification workload.
3. The vision loop, D3 through D8, unchanged in content.
4. The code lane is demoted to evidence-gathering under the complements doctrine. D9 probe scoring and the five judged D11 dispatches stay. The `/dispatch-local` skill in D10 is built only if D11 clears. D17, the 80B pull, stays gated on D11 per D2a.
5. Measurement sessions D14 and D15 run after vision slice 1, per D3a. The D16 bake-off absorbs the "newer releases" note. Qwen3.8-27B shipped 2026-08-14 with native vision, a 262k context window, and a footprint near 17 GB. It is a candidate to replace `gemma4:26b` as both the BIG tier and the UI-vision tier. The other bake-off candidates stay: Qwen3-VL through MLX-VLM, Moondream 3, MiniCPM-V 4.5.
6. Qwen-Image keeps six weeks, per D4a. Drop it at the 2026-10-05 self-audit if usage is still zero.

The dropped, changed, added review the note asked for:

- Keep: `see` in all modes, the loop machinery, `lm gemini`, the `q` small tier, the probe and self-audit gauges.
- Park: `lm fleet` as a general fan-out. It revives only as a sweep tool behind a judge. The code lane as a cloud substitute is parked with it, and the 80B ambition too.
- Freeze: imagegen, as ruled above.
- Change: the local-lane promises in `rules/model-tier-routing.md` should be reworded to the complements doctrine. Filed to the gcc backlog rather than edited from here.
- Flag to owner: verify.sh expects the two retired gcc schedules named above. Either re-register them or delete the checks. Under the complements doctrine, deleting the checks is the consistent move. Done 2026-08-30: the checks were deleted, and the stale fable-sentinel check was fixed to know `~/.claude/.allow-fable-subagents`.

**Built the same day (2026-08-30), all verified by running them:** gemini robustness (all of item 2 except the Batch API investigation; 7 fake-backend tests plus one real call; the key-type check remains yours). Vision: `see reshoot` (static and web, comparability gate watched red), ledger `items` ingest (battery F13, watched red under mutation), `caller`/`resident` history fields, skill-log mandates in the four judge skills, the `/ui-loop` skill, and a live two-round loop on the kanban pair that caught a real ui-verify defect (judge ruled 1 of 5 claims and the gate said pass; fixed with a count assertion plus a big-tier escalation retry, re-run judged 5/5). Code lane: `intents/code-dispatch.toml`, opencode session logging, probe runs scored by an owner-delegated opus seat (verdicts flippable). Suites: battery 53/53, verify 38/0.

**New findings from the scoring seat (probe-scoring.md):** the probe corpus is 2 real observations, not 4 (two files are byte-identical replays, one is all-404 and void); and `passk-reliability` cannot fail by construction (temperature pinned to 0, warm sequential runs), so it has been a free pass in every run ever recorded. D11's five real dispatches remain the only evidence that counts for the 80B call, and the passk item needs a redesign (temperature sweep or dropped) before any future probe is quoted.
