# Visual Compare — implementation proposal + full context handoff

<!-- sessions: local-next-a4@2026-07-10 · STATUS: APPROVED PLAN, ready to build -->

**For the next session agent.** The canonical design is
[`docs/10-visual-compare-design.md`](../../../docs/10-visual-compare-design.md) —
read it in full before anything else. THIS document is everything the design doc
deliberately doesn't carry: how the plan got its shape, which alternatives were
already rejected and why, the traps the building sessions hit, and the concrete
kickoff list. Its purpose is that you never re-open a settled question or re-step
on a rake.

## 0 · One-paragraph orientation

Build a two-repo capability that compares two images (or an image vs a live
surface) for the "recreate a UI with a freer hand" workflow: deterministic
extractors in local-models produce machine-measured evidence (works on ICONS, not
just texty UIs), a gcc skill judges divergences against the user's editable taste
policy with Claude's native vision as the ONLY Claude seat, and a loop mode
tracks convergence across rounds in a ledger. Everything the agent consumes is
structured; every number is machine-made; every judged call is policy-traceable.

## 1 · The problem, in the user's own framing

- Use case: "Having claude recreate a UI based on a reference BUT with a freer
  hand … the ability to compare the old and new would be helpful." Two login
  pages: one hand-tuned, one Claude-rebuilt from extracted primitives. The user
  sees "glaring visual feel differences" instantly; the goal is NOT pixel
  perfection but smart imitation — "knowing what divergences look bad on the
  old / new, which ones are not worth it."
- The acceptance bar, verbatim: **"If I come running back in 2 days because this
  perfectly curated stack cannot handle two different icons that should look
  similar, then it's pointless."** Icons = no text = the OCR-anchored approach
  produces zero signal. Any implementation that only works on text-rich UIs
  fails the whole effort.
- Consumer identity: **"this one's not for human use … meant for a model, so
  helpful discovery messages + hard blocks for params it will not think of
  unless wrong."** The tool's user is an agent. `~/.claude/conventions/
  agent-first-tools.md` is the governing convention — read it before coding.

## 2 · Settled decisions — do NOT re-litigate these

| Decision | Why (and what was rejected) |
|---|---|
| "Visual feel" judgment does NOT go into lm | The June vision audit measured local VLM shade/spacing reads as fabrication-prone; `--ui` deliberately bans pixel estimates (docs/08). The judge is Claude native vision in a gcc skill. |
| Machine layer must be modality-adaptive | The icon test kills text-anchored designs. dHash/aHash + grid-ΔE + edge-density grids run on everything; OCR lanes only when text exists. |
| No numpy/opencv/SSIM/DCT-pHash | Dependency-free by design: PIL (already in the venv via mflux) + pure python. dHash+aHash+grid metrics cover the decisions at this scale. CV-grade element-boundary detection (radii, shadows) was considered and REJECTED — brittle, heavy, poor returns; that fidelity tier belongs to DOM-vs-DOM via the existing Playwright MCP when the candidate is live. |
| One Claude seat, sparse, announced | User: balance cheap-and-frequent vs expensive-but-valuable, with the process adapting or the model EXPLICITLY specifying. Resolution: extractors always ($0), local gemma read off-by-default in loops, native judge fires only when the controlling agent invokes it — at tool-NUDGED moments (ledger stall, scores under floor, user ask) — and announces seat+cost class BEFORE running. |
| gemini is not in the core | Optional `--second-opinion` lane, untrusted-verify posture, off by default. The design must never depend on it. |
| No new subsystem for niche wins | Precedent from the same session: user rejected `lm latest` as over-indexing on one test — and the websearch domain-rerank (a general fix) then solved that exact case. Bias: extend general mechanisms, don't mint subsystems. |
| Models judge, scripts measure | The week's doctrine, proven across ui-verify/--ocr/diff: every number from an extractor, every taste call from the judge, judge contractually barred from disputing extractor facts, gestalt observations tagged `gestalt`. |
| Fixtures before extractors | F3 (identical pair must come back CLEAN) is the fabrication guard and exists from hour one. A comparator that invents differences is worse than none. |

## 3 · What already exists to build on (all verified live, on `feat/q-adaptive`)

- **`see diff A B ["focus"]`** (bin/see) — v1 shipped: OCR text/position diff
  (REMOVED/ADDED/MOVED with 3×3 labels) + one big-tier two-image VLM call with
  the machine diff injected as trusted evidence; artifact stores both sources;
  `--json` carries `text_diff`. First live run on planted fixtures
  (probe/fixtures/diff-a/b.png) got every fact right. Phase A EXTENDS this —
  same verb, new extractors, do not fork a second surface.
- **Positional OCR** — `see --ocr --json` → `.data.words` with normalized
  x/y/w/h + script-computed 3×3 `pos` (mac-ocr `--format jsonl`; top-left
  origin verified against two anchors). `ui-verify --boxes` already consumes it.
- **Artifact store** (`outputs/see/<ts>-<mode>-<slug>/`), history JSONL with
  `img2`/`artifact`/`crop` fields, `see open/more/note` verbs.
- **The judge-skill skeleton** — `/ui-gripe` (gcc) is the sibling shape: fork
  context, evidence-first phases, report contract, runtime-notes. `/vis-compare`
  copies its skeleton.
- **Doctrine docs** — `~/.claude/conventions/agent-first-tools.md` (five
  obligations); `docs/03` (models never drive tools); `docs/08` (why --ui bans
  measurements); q-spec §--web/--diy (the plan-then-execute + deterministic-
  backstop pattern this capability repeats).

## 4 · Traps the building sessions actually hit — step around them

1. **bash 3.2 heredocs inside `$()` misparse apostrophes** — bin/see warns
   about it and the diff machine-layer python got written around it. Keep
   single quotes out of PY blocks inside command substitution, or test
   immediately.
2. **Scans must read RAW user input, never assembled state** — the diy file-
   scan ran over a mutated QUERY and matched an injected `</input>` tag as a
   path. Freeze the source of truth before layered mutations (RAW_PROMPT
   pattern in bin/q).
3. **Small local models judge well but EXTRACT poorly** (measured repeatedly:
   file paths, image paths, probe commands all missed). Every extraction needs
   a deterministic conductor backstop; trust the model only for judgment calls.
4. **Trailing punctuation breaks word-level file tests** (`./x.png,`) — strip
   `[,.;:!?"')]` before `-f` checks.
5. **Cold big-tier loads blow fixed timeouts under contention** — see's request
   clock is now residency-aware (180s warm / 420s cold). Batches want a
   `warm on big <ttl>` lease; loop mode should lease at round start.
6. **Machine contention is real on this box** — sibling sessions + resident
   models made the verify battery time out twice. Time-box live tests, prefer
   the small fixtures, and treat full-battery timeouts as environment, not code.
7. **`glow` hangs headless** — render-check markdown with `awk` fence-count +
   `bat`, never `glow` in a non-TTY tool call.
8. **`bash -n a b c` only checks `a`** — syntax-check files individually.
9. **verify.sh checks need text-bearing fixtures** — the art presets have no
   text; an OCR-position assertion against them fails. `probe/fixtures/`
   has ocr-fixture.png (known text, known corner) and diff-a/b.png (planted
   diffs). F2/F3/F… fixtures follow the same pattern: PLANT the ground truth.
10. **Synthetic repro ≠ workload repro** (atoned this session) — when a
    fixture passes but the user's real pair misbehaves, replay THEIR pair
    before concluding anything.
11. **Multi-image single-call works on gemma4:26b** (order held: FIRST=A,
    SECOND=B) — verified once; keep the order-labeling in the prompt and
    re-verify if the model tag ever changes.

## 5 · Kickoff checklist (Phase A, fixtures-first — the concrete list)

1. Read: docs/10 (full), this file, agent-first-tools.md, bin/see (the diff
   branch + artifact tail), q-spec §adaptive.
2. Fixtures BEFORE extractors (`probe/fixtures/` + generator snippets in a
   small `probe/fixtures/make-fixtures.py` so they're reproducible):
   F2 icon pair (glyph + hue+15°/radius/stroke perturbation) · F3 identical
   pair · F4 theme pair · F5 incomparable pair · F6 chart pair. F1 exists.
3. E0 normalize + modality probe + comparability gate (bin/see diff branch).
4. E4 dHash/aHash → `scores` block; wire F3 assertion (all ~zero) into
   verify.sh IMMEDIATELY — the fabrication guard runs from the first commit.
5. E5 grid-ΔE + E3 palette/ΔE (CIE76 pure-python) + E6 edge-density grid.
6. Evidence-pack schema (docs/10 §5) + cost/failures blocks + compare-history
   journal + `next:` nudge emission + `--only`/`--grid` slice reruns with
   delta output + submit-time hard blocks.
7. Contact sheet (PIL composite: A | B | heatmap tint) into the artifact dir.
8. Battery: F1–F8 model-free assertions (F7 rerun-delta, F8 PATH-hidden
   mac-ocr salvage). Run each extractor against F2 AND F3 — every extractor
   must both detect planted diffs and stay silent on identical input.
9. Docs: CAPABILITIES §3, STATE ledger+PENDING, q-spec untouched.
10. Commit per logical unit on a feature branch off main (`feat/vis-compare`),
    push; do NOT touch gcc in Phase A.

Phase B (gcc: /vis-compare + policy.md v1 + suppressions + --revisit +
announce-before-spend) and the rest: per docs/10 §7. Policy.md v1 is DRAFTED
from §4's ladder then handed to the user for edit — do not polish it solo.

## 6 · Genuinely open (small — decide with the user, not unilaterally)

- Skill name: `/vis-compare` is the working name; user hasn't blessed it.
- Contact-sheet layout (A|B|heat vs stacked) — pick in Phase A, cheap to change.
- Whether `see diff` keeps its local-VLM prose call as default in one-shot
  (non-loop) use once the judge exists — revisit at Phase D calibration.
- compare-history.jsonl → self-audit wiring (add the stream row in Phase A or
  defer to first real week of use).

## 7 · Acceptance

- All F1–F8 battery-green on a quiet machine.
- The user's real login pair AND a real icon pair, end-to-end, user grades the
  verdicts (Phase D gate — the user's grading closes this, not the battery).
- The 2-day test: an icon pair "that should look similar" produces a useful,
  non-empty, non-fabricated comparison. That is the bar this exists to clear.
