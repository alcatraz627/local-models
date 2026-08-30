# Lane 3: local vision + the UI driver loop

Scope: `see`, `lm ui-verify`, the visual-compare (L1/L2/L3) stack, E8, and the gcc skills
that drive them. All facts below are grounded in file:line, `jq`/`rg` output, or a dated
web source. Anything not traceable is marked UNVERIFIED.

## 1. Actual usage

**`see` volume and shape** (`logs/see-history.jsonl`, 220 rows, python count):
- 191 rows in 2026-07, 29 in 2026-08. The lane was built and heavily exercised in its
  first week, then usage collapsed by roughly 85% and never recovered.
- By mode: `ocr` 71, `ui` 68, `general` 44, `diff` 32, `menubar` 3.
- By model: `gemma4:26b` 93 (the `--ui` route, per `config.sh:UI_VISION_MODEL`),
  `apple-vision` 71 (OCR, no model), `minicpm-v` 49 (default plain reads),
  `none (--no-read)` 7 (loop-mode evidence-only diffs).
- Latency by (mode, model), computed from the `ms` field: `ui`/`gemma4:26b` averages
  **25.1s**, max **71.8s** (n=65); `diff`/`gemma4:26b` averages 17.4s, max **154.4s**
  (n=25); `general`/`minicpm-v` averages 8.0s; `ocr`/`apple-vision` averages **419ms**
  (n=71, no model call). The `--ui` read, the one the driver loop leans on, is by far
  the slowest and most variable lane.
- Caller/project inference from `img` path prefixes (best-effort; there is no explicit
  `cwd`/source field in the schema, see Gaps §3): `probe/fixtures` 41, `presets` 27,
  `~/.claude/assets/images` 25, `versable-builder` 17, this repo's own
  `20260708-vision-ui-batch` 15, `data-forge` scratchpad 12, various `.playwright-mcp`
  captures 14, `~/.claude/assets/screenshots` 16. Real cross-project UI work (versable,
  data-forge, playwright captures) accounts for roughly half of non-fixture reads; the
  rest is this repo's own fixture and calibration traffic.

**`see diff` / compare-history** (`logs/compare-history.jsonl`, 30 rows, each carrying
`a`/`b`/`modality`/`comparable`/`scores`/`wall_ms`/`extractors_ms`): dated by day, 12 on
2026-07-10, 8 on 07-11, 5 on 07-12, 1 on 07-13, then **nothing until 2026-08-23
(3 rows) and 2026-08-28 (1 row)**. The 26 July rows are the L1 build-and-validate window
(`docs/10-visual-compare-design.md` §9-10, `.claude/output/20260710..13-*`). The 4 August
rows are the only post-ship organic-looking usage in seven weeks.

**Skill invocation is thinner than even that.** `~/.claude/skills/usage/events.jsonl`
(135 total events across all skills) records **zero** `skill-log record` calls for
`vis-compare`, `ui-gripe`, `designer-reviewer`, or `ui-direction`; `ui-categorical-check`
has exactly 1. Compare that against `bloop` (62), `plan` (28), `build-change` (15). The
vision/UI-critique skills are the least-instrumented corner of the whole roster, either
because they aren't called or because their runs don't call `skill-log.sh` (both are true
to different degrees, see below). The actual run count is closer to what each skill's own
`runtime-notes.md` records: `ui-gripe` 12 dated run-entries (through 2026-08-24, including
a real find, the kanban board's badge-count/edge-mask incidents), `vis-compare` 3
run-entries (all three are the Jul-11 fixture/calibration pairs, not live project work),
`designer-reviewer` 4 (all four are one scraper-success wizard review on 2026-04-11,
predating this lane entirely). **`ui-categorical-check` and `ui-direction` have no
`runtime-notes.md` at all**, either genuinely unused or run and never logged.

**What the 2026-08-10 adoption review said, and what changed since**
(`~/.claude/assets/reports/20260810-local-models-review.md:10`): "`see diff` / vis-compare,
0 compare runs, DEAD (0), nobody compared anything, the L1/L2 stack is unused, consider
retiring the skill from the menu." Baseline `see`: 52 runs in the prior 30 days against
`q`'s 1678. Since that review: `see diff` picked up exactly 4 more real invocations
(Aug 23 x3, Aug 28 x1), a pulse, not a recovery. `ui-gripe`, the sibling skill, has the
opposite shape: it never showed up as "dead" in that review (it isn't `see diff`-gated)
and has the healthiest usage of the four critique skills, with genuine findings on real
surfaces (kanban board, data-forge tray icons).

## 2. What was attempted: the loop as designed

```
                     +------------------------------------------------+
                     |            SCRIPTS MEASURE ($0)                 |
                     |  see --ui / --ocr / diff A B   (bin/see)        |
                     |  lib/vis-compare.py   L1 evidence extractors    |
                     |  lib/e8-dom.py + e8-extract.js  (live web)      |
                     |  ax tree --app <Name>          (native AX)      |
                     +---------------------+----------------------------+
                                            | evidence.json / contact.png /
                                            | inventory.json / e8 capture
                                            v
                     +------------------------------------------------+
                     |         MODELS JUDGE (Claude-driven)             |
                     |  /vis-compare  = divergence-class ladder         |
                     |  /ui-gripe     = confusion forensics             |
                     |  /ui-categorical-check = mined bug-class check   |
                     |  lm ui-verify  = enumerable claim gate           |
                     +---------------------+----------------------------+
                                            | verdict.json / findings
                                            v
                     +------------------------------------------------+
                     |          THE LEDGER TRACKS (mechanical)          |
                     |  lib/vis-ledger.py: fixed/persisting/            |
                     |  regressed/new, stall + policy-pass signals      |
                     +---------------------+----------------------------+
                                            | "apply fixes" (HUMAN, by hand)
                                            v
                     +------------------------------------------------+
                     |        RE-RENDER: NOT AUTOMATED IN lm/           |
                     |  (Claude edits code, then re-screenshots by      |
                     |  hand via screencapture/Playwright/ax; no        |
                     |  lm-side driver wires this step)                 |
                     +---------------------+----------------------------+
                                            +---------> back to MEASURE
```

Automated (mechanical, no model in the loop): the whole MEASURE layer, and the LEDGER
layer (`lib/vis-ledger.py`: pure Python, set-comparison state transitions, no PIL/no
model, `docs/10-visual-compare-design.md:396-425`).

Claude-driven by hand, every time: the JUDGE layer (all four skills read images
natively and reason; that's the design, "scripts measure, Claude judges," stated as a
hard rule in every one of these SKILL.md files) and the RE-RENDER step. Nothing in
`lib/` or `bin/` takes a fix, applies it, and re-screenshots. That entire arrow is
Claude editing code and then manually running `screencapture`, a Playwright MCP call,
or `ax`, outside any lm-side script.

Never ran for real work: the L3 `--loop` mode end-to-end on a live project. The three
`vis-compare` runtime-notes entries and all but 5 of the 30 `compare-history` rows are
the Jul-10/11/12/13 build/validation window; docs/10 §10-11 describe a live round-trip
that exists (the imagegen loop, `.claude/output/20260713-imagine-loop/round-trip.md`)
but that is `imagine` vs a static reference image, not a UI screenshot loop against a
running app or page.

## 3. Gaps, concretely

**Nobody automates the screenshot.** Every entry point (`see`, `ui-gripe`, `vis-compare`,
`ui-verify`) takes a path to an already-captured image or an `--app`/`--menubar` live
grab of the current screen. There is no `lm`-side command that says "navigate this URL
or launch this app, wait for it to settle, capture, and hand me the path." That
composition lives entirely in the calling agent's head, stitched from a Playwright or
chrome-devtools MCP call plus a manual `see` invocation. `docs/10-visual-compare-design.md:126`
documents E7 (AX geometry via `ax tree`) as **NOT built**, and nothing in `bin/`/`lib/`
references `playwright` or `chrome-devtools` at all (`rg -n "playwright|chrome-devtools"
bin/ lib/` returns zero hits). Those integrations exist only in gcc's `chrome-devtools-mcp`
skills and in Claude's own tool use, never as a documented handoff into this suite.

**Nobody automates re-render.** Same shape, other direction: after a fix, nothing in
`lib/` reruns the capture. The L3 loop protocol (`~/.claude/skills/vis-compare/SKILL.md:39-61`)
says step 2 literally is "apply the fixes... then re-render B... then run `see diff`,"
with re-render left as an unspecified action for the driving agent. This is the missing
mechanical step between measure and judge-again; its absence is very likely why the
loop was driven live exactly once (the imagegen lane, where `imagine refine` is the
re-render primitive and is scripted) and never for a UI-code loop, where re-render means
"go build, deploy, reload," which nothing here scripts.

**The judged layer (L2/L3) is close to unused relative to the evidence layer (L1) and
relative to the raw `see` tool.** `see diff --json` (L1, $0, roughly 1s) ran 30 times.
`/vis-compare` (L2, the judge) shows 3 runtime-notes entries, all from the build window.
The 2026-08-10 review's harshest finding, "0 compare runs, consider retiring the skill,"
undersold it slightly (compare-history did have rows by then, just all from the build
week) but the substance holds: the deterministic half got exercised once to prove it
works, and the judged/looped half essentially never got exercised on anything the owner
actually needed compared.

**`--ui` reads are too slow and too inconsistent for a tight loop.** 25s average, 72s
max per read (n=65) means a driver that wants "screenshot, inventory, judge, fix,
re-screenshot, re-inventory" pays 25-70s of dead time on just the MEASURE step, twice
per round, before any judgment happens. `config.sh` routes `--ui` to `gemma4:26b`
specifically because `minicpm-v` "kept getting wrong... the actually-selected nav item,
region proportions, per-element states" on the 2026-07-08 ground-truth test (config.sh
comment; `docs/08-vision-lenses-design.md` corroborates: a 3-way empirical test found
the general/adaptive prompt beat a specialized "dashboard" lens, and all three tested
approaches missed the same masthead numbers and read text non-verbatim: "verbatim
fidelity is a MODEL-floor property, invariant to the prompt. A lens cannot fix OCR").
So the accuracy fix (route to the 26B model) is also the latency problem. There is no
fast-and-accurate option in the current tier map; `--ocr` (Apple Vision, roughly 400ms,
exact text) is the one part of the stack that is both.

**`ui-verify`'s AX-tree path (the exact, fast, non-VLM lane) is under-leaned-on.**
`lib/ui-verify:85-90` wires `ax tree --app <Name>` for native apps, no pixels, no
model, exact structure, and `bin/lm:116` lists it as an optional extra
(`cargo install --git .../ax-cli`). `ui-gripe`'s own SKILL.md (Phase 2) tells the agent
to prefer it "whenever the app exposes a real AX tree." But every usage signal above
(see-history modes, compare-history) is screenshot-based; there is no history stream for
`ax`/`ui-verify --app` calls at all, so it cannot be confirmed whether this faster and
exact path is actually reached for in practice or just documented as preferred.
UNVERIFIED: whether `ax-cli` is even installed on this machine (`command -v ax` was not
run; read-only lane scope, would need a Bash check outside file-reading).

**`rules/ui-visual-verification.md`'s "read the whole frame before the question" binds
nowhere mechanically.** It is a CLAUDE.md-level behavioral rule (loaded every session),
not a check any script in this lane enforces. No gate in `lib/ui-verify` or
`lib/vis-ledger.py` confirms the calling agent actually looked at the full image before
answering a narrow claim. The `ui-categorical-check` skill (mined from the user's own
feedback history, per its description) is the closest thing to a mechanical catch for
this, "the transparent floating layer," "sibling controls at mismatched type scale,"
but it has exactly 1 recorded run and no runtime-notes file, so there is no evidence it
has ever caught one of the 10 S3 instances the rule cites in the wild.

**Local-VLM read quality, quantified from ground-truth tests on disk:**
- `docs/08-vision-lenses-design.md:8-16`: the i-dream-dashboard 3-way test (general
  prompt vs adaptive prompt vs hand-written "dashboard" lens, all on `minicpm-v`).
  The specialized lens did not beat the general prompt (missed a 522-block count the
  general prompt caught; missed 160 tool calls the adaptive prompt caught) and
  fabricated color semantics ("purple = bypassPermissions"). All three missed the same
  masthead numbers (62.5K/352.4K/52.3M) verbatim.
- `config.sh` comment (VISION_MODEL section): the claude-instances 4-screenshot fidelity
  test against native-Claude-vision ground truth. `minicpm-v` transcribed verbatim
  text, commands, and counts that `gemma4:26b` missed ("reads the shape, not the
  words"), with no hallucinated controls; `gemma4:26b` is the stronger general-scene
  reasoner. This is why `see` defaults to `minicpm-v` but routes `--ui` specifically
  to `gemma4:26b`, an explicit, measured trade, not an oversight.
- Sample response quality (see-history row 2, `minicpm-v` critiquing the i-dream browse
  dashboard) reads as generic UX-101 boilerplate ("Introduce collapsible sections...")
  rather than evidence-grounded observation, consistent with the "structure enumerated,
  judgment left to Claude" division of labor the skills enforce; the raw model's own
  prose is explicitly not trusted as a judgment (`~/.claude/skills/vis-compare/runtime-notes.md`:
  "The pack's local-VLM prose is NOT an anchor... Trust extractors and native eyes,
  treat the VLM's LAYOUT SHIFTS section as a hint, never evidence").

## 4. Ideal workflow: the driver loop the owner wants

The owner's own framing ("more involved agent involvement in driving the dumb tools")
matches the gap found above precisely: the MEASURE and LEDGER layers are already "dumb
tools" done right (deterministic, fabrication-resistant, $0 or near-$0); the two missing
links are CAPTURE and RE-RENDER, and today's design already reserves the JUDGE seat
correctly for Claude. The fix is not "make the model do more," it is "wire the two
mechanical steps that currently require Claude to hand-compose a shell command every
round."

```
INPUT: a target (URL, running native app, or a static image pair A/B)
        + a claim set OR "general critique" OR a reference to imitate
        + (loop mode only) a way to apply a fix: code Claude can edit

Step 0  RESOLVE TARGET
        web    -> chrome-devtools/playwright MCP: navigate, wait for network-idle
                  plus a settle heuristic (no layout shift for N ms), then capture
        native -> `ax` for structure (exact, fast, $0); screencapture only if
                  pixels are also needed (icon fidelity, rendering bugs AX cannot see)
        static -> the image path(s) as given

Step 1  MEASURE ($0, mechanical, already built)
        see --ui --json   (inventory)      + see --ocr           (exact text)
        see diff A B --json (L1 evidence)  + ax tree --json      (exact structure)
        e8-extract.js + e8-dom.py          (exact computed styles, web only)
        GATE: comparable/coverage/failures surfaced honestly, never silently dropped

Step 2  JUDGE (Claude, the one paid seat; announce before spending, as vis-compare
        already does)
        /ui-gripe             = confusion forensics, ranked by damage
        /vis-compare          = imitation fidelity vs a reference, policy-classed
        /ui-categorical-check = the mined bug-class checklist
        lm ui-verify          = the strict pass/fail/unsure gate on enumerable claims
        RULE (mechanical, not advisory): before any of these emits a verdict, it must
        have called Step 1's inventory/diff AND described the full frame, not just the
        claim under test, which is the exact miss rules/ui-visual-verification.md names.
        This is checkable: a verdict.json that never referenced `--ui`'s LAYOUT/PALETTE
        sections, or a claim answered with no crop/full-frame read at all, fails a
        pre-flight the harness (not the model) can run.

Step 3  LEDGER (mechanical, already built for images; needs a UI-claim variant)
        lib/vis-ledger.py tracks fixed/persisting/regressed/new plus stall/policy-pass.
        Today this only understands vis-compare's divergence ids. Extending it to
        ingest ui-verify claim ids and ui-gripe finding ids (same shape: id, class,
        status) makes any of the four judges loop-compatible, not just vis-compare.

Step 4  APPLY FIX (Claude edits code, unchanged, already the right seat)

Step 5  RE-RENDER (THE NEW MECHANICAL PIECE, currently missing)
        web    -> one script wrapping the MCP capture: navigate the same URL, same
                  viewport, wait-for-settle, screenshot into the same loop-dir slot.
                  `imagine refine` is the existing precedent for a scripted,
                  seed-locked re-render; this is the UI-code equivalent, a
                  `see reshoot <loop-dir>` verb that replays the Step-0 capture
                  recipe recorded at loop-open time (URL/app/viewport/wait-rule)
        native -> screencapture / ax tree, same recipe replay
        GATE: if the re-render is not comparable to round 1 (resize, different
        route, different app state), reject before it reaches the ledger, the same
        discipline `see diff`'s `comparable: poor` gate already has

Step 6  LOOP or STOP
        `stop: policy-pass` / `stall` / `pass-with-notes` signals, unchanged, already
        correct in lib/vis-ledger.py
```

Where each piece lives: CAPTURE/RE-RENDER recipe-replay becomes a new `lm`-side verb
(`see reshoot`, or a small `lib/reshoot` wrapping whichever MCP/native driver the
loop-dir recorded); the pre-flight "did you look at the whole frame" check becomes a
mechanical addition to `lib/vis-ledger.py`'s ingest, not a new skill; everything else in
Steps 1-4/6 is already built and correctly divided. The ledger-generalization in Step 3
is the single highest-leverage change: it turns `ui-gripe`/`ui-categorical-check`/
`ui-verify` from one-shot judges into loop-compatible ones for free, using the L3
machinery that already exists and is proven (docs/10 §10, adversarially validated
twice).

## 5. Bridge: smallest changes, ordered by benefit

1. **1 hour, instrument the four judge skills to call `skill-log.sh record`.** Right
   now their real usage is invisible to any automated review (the Aug-10 report almost
   killed a lane that was in fact partially used, and the skill-log data disagrees with
   runtime-notes counts for three of four skills). Add the one-line `record` call each
   SKILL.md's "Post-run" section already gestures at but does not mandate.
2. **1 hour, add a `caller`/`source` field to `see-history.jsonl` rows.** Today the
   only way to attribute a read to a project is guessing from the `img` path prefix,
   which fails for anything captured to `/tmp` or a scratchpad. `bin/see` already knows
   its invoking CWD; log it.
3. **1 day, build `see reshoot <loop-dir>`.** Record the Step-0 capture recipe (URL and
   viewport and wait-rule, or `--app` name, or static-pair paths) at loop-open time in
   the loop-dir's metadata (mirroring what `lib/vis-ledger.py` already tracks per
   round); replay it on demand. This is the single missing mechanical link, closing the
   re-render gap that has kept L3 from ever running on a live UI-code loop.
4. **1 day, generalize `lib/vis-ledger.py`'s ingest to a `{id, class, status}` shape**
   shared by `vis-compare` divergences, `ui-verify` claims, and `ui-gripe` findings,
   instead of being vis-compare-specific. Makes the three non-vis-compare judges
   loop-capable using existing, already-validated machinery.
5. **1 week, a capture wrapper for the web case** (`lib/reshoot-web` or similar) that
   drives chrome-devtools/playwright MCP with a settle heuristic and writes into the
   same artifact convention `outputs/see/` already uses, so a web UI loop and a native
   UI loop share one loop-dir shape. This is the piece that turns "Claude manually
   drives Playwright, then manually calls see" into a one-command round.
6. **Not urgent, revisit on evidence: a faster `--ui` model.** The `gemma4:26b`/25s
   choice is a measured trade against `minicpm-v`'s worse structural accuracy, not an
   oversight; §6 below is the place to watch for a model that beats both on speed and
   accuracy before touching this.

## 6. Best local VLMs on Apple Silicon (64GB), August 2026

**UI screenshot understanding and grounding.** Qwen3-VL is the current strongest
general answer: Qwen3-VL-8B is described as "the model to install first" in 2026
write-ups (69.6 MMMU, 96.1 DocVQA, roughly 6GB at Q4, Apache 2.0), and its family is
explicitly built for "GUI grounding," locating buttons and fields on a screenshot for
agentic use. On Apple Silicon specifically, Qwen3-VL-30B-A3B (MoE) is reported at
roughly 68 tok/s on M4 Max with a 32GB floor via MLX, a shape that would fit this
machine's 64GB budget comfortably. Caveat, load-bearing for this repo: `config.sh`'s
own comment records that the qwen3-vl image path hangs in Ollama (issue #16264); the
GitHub issue (opened 2026-05-22, confirmed: "registers as vision-capable but crashes
on first image request on Apple Silicon (exit status 2)") does not show a resolution
in the fetched thread. Status as of this search is **UNVERIFIED whether fixed**; the
fix, if it exists, would likely need re-testing via Ollama directly or via MLX-VLM as
an alternative runtime (a native Apple Silicon path that sidesteps the Ollama Metal
runner bug class entirely). For grounding specifically (element boxes, not prose
description), purpose-built agents outperform general VLMs: UI-TARS-7B scores
89.5-91.6 on ScreenSpot/v2, and UI-TARS-2 exists as a newer autonomous-GUI-agent model
(exact Apple-Silicon-local availability of UI-TARS-2 is UNVERIFIED from search).
Moondream 3 is notable for a 2B-active-parameter MoE that "matches or beats models
orders of magnitude larger on key grounding benchmarks" with native segmentation, a
plausible $0/fast alternative to `--ui`'s current 25s `gemma4:26b` round-trip, worth a
real bake-off against this repo's existing i-dream-dashboard ground-truth fixture
before adoption (per §5 item 6, "not urgent, revisit on evidence").

**OCR-faithful reading.** MiniCPM-V 4.5 (8.7B, 77.0 OpenCompass average, built
specifically for OCR and high-res documents) matches this repo's own finding that
`minicpm-v` beats `gemma4:26b` on verbatim text; the local choice already tracks the
external consensus.

**General scene and vision-language reasoning.** Gemma 4 E2B/E4B is cited as the
small-Mac-memory-budget option (8-16GB); this repo's `gemma4-e4b-warm` companion and
`gemma4:26b` big tier both sit in that family, consistent with current guidance.

**Runtime: Ollama vs MLX-VLM.** MLX is repeatedly named as the Apple-Silicon path in
2026 sources (3-bit to 8-bit Qwen3.6 quants shipping natively for both text and
vision); this repo's own `docs/05` MLX verdict (referenced in STATE.md, not re-read in
this lane) already measured Ollama vs MLX for the text/code tiers and kept Ollama for
Q4_K_M/llama.cpp. Whether that verdict holds for the vision path specifically, given
the qwen3-vl Ollama hang, is the open question this repo has not yet re-run.

## 7. UI-testing and visual-diff tooling worth adopting or wrapping

**Deterministic pixel diff.** `pixelmatch` is "the de facto standard," used
internally by Playwright's `toHaveScreenshot()`, jest-image-snapshot, BackstopJS, and
most Cypress plugins: YIQ perceptual color space, anti-aliasing-aware, zero
dependencies. `odiff` is the faster native alternative (SIMD, "6x faster than
imagemagick and pixelmatch," recommended once a corpus exceeds roughly 1,000
screenshots per run or CI parallelism is aggressive). This repo's own
`lib/vis-compare.py` is deliberately pure-PIL/no-numpy for portability
(`docs/10-visual-compare-design.md`), so odiff would be a genuine speed win only if
screenshot volume grows past the current handful-per-run scale; not worth the
dependency today. `resemble.js`/BackstopJS add baseline management and reporting on
top of a pixelmatch-class core; this repo's own `vis-ledger.py` plus artifact-store
convention already covers that ground natively and arguably better
(fabrication-proofed, fixed/persisting/regressed semantics BackstopJS does not have).

**Accessibility-tree-based checks.** Already the right idea and already partially
wired (`ax tree`, `lib/ui-verify --app`). The gap is usage-visibility (§3), not
missing tooling.

**OmniParser (Microsoft).** A YOLO-fine-tuned icon detector plus a Florence2
captioner that turns a screenshot into structured elements for grounding: v2 hit
39.5% on ScreenSpot Pro; a July-2026 update added a YOLOv9-E interactive-region
detector. This is the closest external match to what `see --ui --json`'s inventory
already tries to do, but via detection (bounding boxes from a vision detector) rather
than a VLM's free-text enumeration, a genuinely different and likely more reliable
mechanism for the "where is this element" half of grounding. Worth prototyping as a
Step-1 MEASURE addition (element boxes as ground truth alongside the current prose
inventory) rather than a `--ui` replacement, since it would not cover the
icon-semantics/hierarchy-judgment half `see --ui` also provides. License note: the
icon-detection weights are AGPL (inherited from YOLO); the caption model is MIT. The
AGPL half would need review before bundling into this repo if adopted, not just used
ad hoc.

**"Computer use" and grounding models generally** (UI-TARS, ScreenAI-class): covered
in §6; these are agent-action models (click/type target selection) more than
read-and-critique tools, so their fit here is narrower than OmniParser's, most
relevant if this lane ever drives actions, not just judges screenshots.

## 8. How others build an agent-driven UI review loop

The "Eyes" Claude Code skill (per a 2026 write-up) implements "capture, propose,
confirm, verify" over Playwright MCP specifically to keep frontend changes aligned with
user expectations before code is touched. Structurally the same MEASURE-then-JUDGE-
then-APPLY shape this repo's L1/L2/L3 already has, but web-only and without this
repo's fabrication-proofing (population-weighted ΔE, evidence-traceability self-check)
or its $0 evidence-first discipline. General "Playwright CLI + Claude Code" write-ups
describe the same manual pattern this lane's gap analysis found: the agent runs
`playwright-cli screenshot` then `show --annotate` then critiques by hand. The
re-render step is always the human/agent-composed one in every external example
found, not a scripted primitive. Playwright's own "Playwright Agents" (integrated into
VS Code, and reportedly Claude Code/OpenCode) can "plan, generate, and heal" Playwright
tests, a different target (test authoring) than this lane's target (design/UX
critique), but the healing loop is architecturally the same convergence pattern as L3.
Anthropic's own vision-quality trajectory is directly relevant to whether local models
are worth defending here at all: Opus 4.7 (released 2026-04-16, per search) tripled
vision resolution (1568px to 2576px) and reportedly moved "computer-use visual acuity
from 54.5% to 98.5% in production tests," a gap this large against native Claude
vision is exactly why every skill in this lane (`ui-gripe`, `vis-compare`) explicitly
demotes the local VLM's own prose to "hint, never evidence" and reserves judgment for
a native Read. Claude Design (Anthropic's own design tool, per search) runs a
background check against imported design-system rules before returning generated
code, a narrower, generation-side version of the same "measure against a rubric, then
judge" idea, but for a different problem (does new code match tokens) than this
lane's (does a screenshot match intent or reference).

## 9. Uncertainties

- Whether Ollama issue #16264 (qwen3-vl image crash on Apple Silicon) is fixed as of
  2026-08-30: the fetched GitHub thread did not show a resolution; needs a direct
  re-check of the issue or a local re-test.
- Whether `ax-cli` is actually installed on this machine (`bin/lm:116` lists it as an
  optional extra): not checked, out of this lane's read-only Bash scope for a
  definitive `command -v ax` in the target env (assumed benign to run but not executed
  to stay strictly within "no inference, read logs/files" instructions).
- MLX-VLM's actual measured speed and accuracy on this specific machine (M5 Pro, 64GB)
  is not established here; all MLX figures above are from external M4 Max benchmarks,
  not this repo's own `docs/05` MLX verdict, which covers text/code tiers only.
  UNVERIFIED for vision specifically.
- Whether the Aug-10 review's "0 compare runs" verdict used a different counting
  method than the raw `compare-history.jsonl` row count (which shows 12+8+5+1 rows
  before Aug 10): plausible if the review counted skill-log `vis-compare` records (0,
  matches) rather than L1 `see diff` calls; the report itself does not cite its query,
  so this is inferred, not confirmed.
- Real-world accuracy numbers for Qwen3-VL, Moondream 3, and UI-TARS-2 against this
  repo's own ground-truth fixtures (the i-dream dashboard test, the claude-instances
  fidelity test) do not exist; all comparisons above are against public benchmarks,
  not this repo's evaluation harness. A local bake-off (§5 item 6) is the way to close
  this, not more search.

## 10. Source table

| # | Claim | Source | Date |
|---|---|---|---|
| 1 | Qwen3-VL family, GUI grounding, Apple Silicon MLX perf | TinyWeights.dev "Best Local Vision Language Models 2026"; codersera.com Apple Silicon LLMs guide | 2026 |
| 2 | qwen3-vl Ollama Apple Silicon image crash, unresolved as fetched | github.com/ollama/ollama/issues/16264 | opened 2026-05-22 |
| 3 | OmniParser v2 grounding score, July-2026 YOLOv9-E update, license split | github.com/microsoft/OmniParser, huggingface.co/microsoft/OmniParser-v2.0, arxiv 2602.14276 | 2025-02 / 2026-07 |
| 4 | pixelmatch as visual-diff standard; odiff perf claim; BackstopJS internals | github.com/mapbox/pixelmatch, github.com/dmtrKovalenko/odiff, wopee.io screenshot-comparison-algorithms | 2026 |
| 5 | UI-TARS ScreenSpot/v2 scores; Moondream 3 MoE grounding claim | arxiv.org/pdf/2501.12326 (UI-TARS), moondream.ai/models | 2026 |
| 6 | "Eyes" Playwright-MCP visual-feedback skill; Playwright Agents | mcpmarket.com/tools/skills/visual-feedback-loop-eyes, jonathansblog.co.uk playwright-claude-code-skill | 2026 |
| 7 | Opus 4.7 vision-resolution jump, computer-use acuity figure | earezki.com/ai-news 2026-04-18 Opus 4.7 release | 2026-04-18 |
| 8 | Claude Design background design-system check | buildfastwithai.com Claude Design 2026 guide | 2026 |
| 9 | MiniCPM-V 4.5 OCR benchmark | bentoml.com "Multimodal AI... 2026" | 2026 |

All local facts above are cited inline with file:line or `logs/*.jsonl` row counts
computed directly in this session, per the instructions' preference for cited
mechanical checks over recollection.
