# Visual Compare — a full-stack capability for "does B faithfully imitate A?"

<!-- sessions: vis-ab-3c@2026-07-12 · STATUS: ALL PHASES DONE — A (L1 evidence: lib/vis-compare.py + see diff, F1-F9b), B (L2 judge: /vis-compare + policy.md v3), D (calibration: acceptance signed 2026-07-12, 2 real pairs user-graded), C (loop: lib/vis-ledger.py + see diff --no-read + /vis-compare --loop protocol, F10/F10b/F10c). Every phase adversarially validated; E7/E8 remain documented lanes (§10) -->

The independent vision capability the recreate-with-a-freer-hand workflow needs:
compare two images (or an image against a live surface), produce machine-measured
evidence plus a policy-driven judgment of which divergences matter, and support an
iterative narrowing loop until the candidate passes taste. Spans both repos: **lm
owns evidence** (deterministic extractors, $0, fabrication-proof), **gcc owns
judgment** (native vision + the user's taste policy + feedback memory).

The acceptance bar, verbatim: *"If I come running back in 2 days because this
perfectly curated stack cannot handle two different icons that should look similar,
it's pointless."* The design below is built around that test — every extractor and
every fixture must earn its place on non-text images too.

---

## 1 · Use-case taxonomy (what this must handle)

| # | Case | Signal profile | Stress on the design |
|---|------|----------------|----------------------|
| U1 | UI recreation (the login pair: hand-tuned original vs Claude-rebuilt from primitives) | text + layout + color + component shapes | the flagship case; needs ALL layers |
| U2 | **Icons / glyphs that should match** | NO text; shape, silhouette, color, stroke | kills OCR-anchored designs; needs shape+color extractors |
| U3 | Theme variants (same UI, light↔dark or pre/post token change) | systematic color shift | the interesting signal is what *didn't* follow the system — extractors must report per-region, not global |
| U4 | Chart/dataviz re-render | text (labels) + geometry | mixed-modality; axis text exact, mark shapes gestalt |
| U5 | Visual regression (pre/post code change) | usually near-identical | anti-fabrication: an identical pair MUST come back clean |
| U6 | Brand asset fidelity (logo exports, marketing crops) | shape + palette, often no text | same lane as U2 |
| U7 | Responsive/reflow (desktop vs mobile of one page) | same content, different layout | "moved" is expected; content parity is the question — policy decides, extractors just report |
| U8 | Generated-image iteration (imagine output vs reference art) | pure gestalt | consumes the same evidence pack later; not built for, not blocked |
| U9 | Iterative convergence (candidate v1→v2→v3 vs one reference) | any of the above, repeated | needs a divergence LEDGER across rounds, not one-shot reports |

Non-goals: pixel-perfect certification (contradicts the imitation policy), animation/
hover states (static frames only — capture states as separate pairs), sub-pixel
rendering forensics (font hinting, AA diffusion — below every layer's floor, and
below the policy's floor too).

---

## 2 · Architecture — three layers, strict roles

```
            ┌─ L1 · EVIDENCE (lm, deterministic, $0) ──────────────────┐
 A.png ──▶  │ normalize → modality probe → run APPLICABLE extractors    │
 B.png ──▶  │ E1 text·pos diff   E2 spacing deltas   E3 palette/ΔE      │
            │ E4 perceptual hash E5 grid-ΔE heatmap  E6 edge/shape grid │
            │ (E7 AX geometry · E8 DOM computed styles — live surfaces) │
            │ → evidence-pack.json + annotated contact sheet            │
            └──────────────────────┬───────────────────────────────────┘
                                   ▼
            ┌─ L2 · JUDGMENT (gcc skill, native vision + policy) ──────┐
            │ sees BOTH images + contact sheet + evidence pack          │
            │ + taste-policy.md + suppressions from past user feedback  │
            │ → verdict.json: divergences classified                    │
            │   looks-worse | neutral | improvement | not-worth-chasing │
            └──────────────────────┬───────────────────────────────────┘
                                   ▼
            ┌─ L3 · LOOP (skill mode, for Claude-built candidates) ────┐
            │ apply fixes (CSS/code, exact values known on the B side)  │
            │ re-render → re-compare → LEDGER: fixed/persisting/new/    │
            │ regressed → stop on policy-pass or 2 non-improving rounds │
            └───────────────────────────────────────────────────────────┘
```

Role discipline (the week's proven doctrine): **models never estimate a number,
scripts never make a taste call.** Every number in the report traces to an
extractor; every "looks worse" traces to the judge; the judge is contractually
barred from disputing extractor facts.

---

## 3 · L1 — the evidence extractors (lm side)

All pure-Python/PIL (venv already has PIL via mflux) + the existing mac-ocr lane.
No numpy, no opencv — dHash/aHash + grid metrics deliberately replace DCT-pHash and
SSIM to stay dependency-free; combined they cover the same decisions at this scale.

**E0 · normalize + modality probe** (runs always)
- Letterbox both images to a common working size (preserve aspect; record scale
  factors — all reported coordinates stay in each ORIGINAL's space).
- Probe: OCR word count per side, image dimensions, color count. Yields modality
  flags: `texty` (≥5 words both sides), `iconlike` (≤256px min-dimension or ≤2
  words), `mixed`. Extractor applicability keys off these — **the icon pair runs
  E3–E6 and skips E1/E2 silently** (reported in the pack, so the judge knows what
  evidence exists).
- Comparability gate: aspect ratios wildly different (>2× off) or dHash distance
  beyond a sanity ceiling → the pack says `comparable: "poor"` with why; the judge
  leads with that instead of manufacturing a comparison. (U7 sets policy override.)

**E1 · text + position diff** (texty only — exists today in `see diff`)
REMOVED/ADDED/MOVED with 3×3 grid labels. Extension: keep raw normalized coords in
the JSON (grid labels remain in prose).

**E2 · spacing & alignment deltas** (texty only — new)
For text fragments matched across sides: Δx/Δy as % of frame; inter-row rhythm
(consecutive baseline gaps) per side + drift; left-edge alignment clusters
(fragments sharing an x-edge in A that no longer share it in B).

**E3 · palette + region color** (always)
- Dominant palette per side (PIL adaptive quantize, k=6) matched by nearest-ΔE:
  `#2563eb → #1d4ed8 (ΔE 9)` pairs + unmatched entries.
- For matched TEXT fragments (texty): fg/bg point-samples behind each box → per-
  element ΔE. For iconlike: per-grid-cell mean color feeds E5 instead.
- ΔE = CIE76 on Lab (pure-python conversion, ~20 lines). Report both hex and a
  plain word (negligible <2 / subtle 2–8 / noticeable 8–20 / different >20).

**E4 · perceptual hash distance** (always)
dHash + aHash (8×8, pure PIL), Hamming distance 0–64 each, plus a combined
similarity word (near-identical / close / related / different). This is the icon
case's headline scalar and the loop's cheapest trend signal.

**E5 · grid-ΔE heatmap** (always)
N×N grid (16×16 UIs, 8×8 icons) of per-cell mean-color ΔE between normalized
sides. Output: the top-k divergent cells with grid coords + a compact ASCII
heatmap in the prose report. Localizes "WHERE it diverges" with zero semantics —
works identically on icons and dashboards.

**E6 · edge/shape grid** (always; the silhouette lane)
PIL FIND_EDGES → per-cell edge-density vectors per side → per-cell density delta.
Catches stroke-weight changes, corner-radius character, missing shape detail —
the icon divergences E3/E5 miss when colors match. (Explicit limit: reports THAT
and WHERE shape changed, not what shape it became — that description is the
judge's, who can see.)

**E7/E8 · live-surface evidence** (documented lanes, thin glue)
E7: `ax tree` element geometry when both sides are running native apps. E8: DOM
computed styles via the existing Playwright/chrome MCP when the candidate is a
live page — exact values for B, so L1 measures only A. These are workflow lanes
in the skill docs, not new binaries.

**Surface & artifacts**
- `see diff A B` keeps its verb. `--json` returns the full evidence pack (schema
  §5). Text mode: current sections + MEASURED DELTAS + COLOR + SHAPE sections,
  each machine-labeled.
- Artifact folder gains `evidence.json` + `contact.png` — a side-by-side sheet
  (A | B | ΔE-heatmap tint overlay), composited by PIL. The sheet is for human
  eyes AND is what L2's native vision reads as one attachment.
- The big-tier VLM call inside `see diff` stays (local report useful standalone),
  but L2 does NOT reuse its prose — the judge re-reads images natively; only the
  machine pack is shared truth.

---

## 4 · L2 — the judge (gcc skill: `/vis-compare`)

> **BUILT** at `~/.claude/skills/vis-compare/` (`SKILL.md` + `policy.md` v1 +
> `runtime-notes.md`). Adversarially validated; the key hardening was an anti-fabrication
> **self-check** (every `gestalt:false` value must trace to a cited evidence path) after a
> dry-run judge fabricated grid coords for text divergences — prose rules don't bind a
> model, a checkable step does. Canonical class slugs are pinned in `policy.md`;
> suppression fingerprints key on stable content anchors (text string / palette hex), not
> drift-prone grid coords. `policy.md` v1 is a DRAFT awaiting the user's taste edit.

A sibling of `/ui-gripe` (same skeleton: fork, evidence-first, report contract).

Inputs: A, B, evidence pack, contact sheet, `policy.md`, `suppressions.jsonl`.

**The taste policy** (`skills/vis-compare/policy.md`, user-editable — this is where
"my feedback" lives durably):
- Divergence classes ranked by default severity: information loss > affordance
  loss > hierarchy/emphasis shift > brand color drift > spacing rhythm >
  micro-typography > texture/decoration.
- The imitation doctrine, written once: pixel-fidelity is NOT the goal; deliberate
  improvements are welcome; divergences below X on the class ladder default to
  not-worth-chasing unless they compound.
- Per-project overrides allowed (a versable section can pin brand hexes as strict).

**Feedback loop**: when the user overrules a verdict ("stop flagging the button
radius"), the skill appends `{pair-context, divergence-fingerprint, ruling}` to
`suppressions.jsonl`; future runs load it and pre-classify matches. Fingerprint =
class + grid region + evidence signature, so it survives re-renders. Periodic
graduation: recurring suppressions get folded INTO policy.md (same
promotion path as atone→rules).

**Verdict contract** (`verdict.json`, schema §5): every divergence carries its
machine evidence refs, a class, a judgment, a fix hint (CSS-level when B is web),
and a stable `id` (for the ledger). Plus `overall`: pass / pass-with-notes /
diverges, judged against policy, never against a numeric threshold alone.

**Anti-fabrication guards** (mirrors of the week's lessons):
- The judge may not report a color/size/position fact absent from the pack —
  it may only ADD gestalt observations, each tagged `gestalt` (unmeasured).
- Identical-pair discipline: if extractors report near-zero everywhere, the
  judge's job is to say "no meaningful divergence" — fixture-tested (§6).

## 5 · Output schema (the contract both repos build against)

```json
// evidence-pack.json  (L1, lm) — as shipped
{ "meta": {"a": "...", "b": "...", "dims_a": [256,256], "dims_b": [256,256],
           "letterboxed": false, "modality": "iconlike", "comparable": "good|poor",
           "comparable_why": null, "grid_n": 8, "skipped_extractors": ["E1","E2"]},
  "scores": {"dhash": 12, "ahash": 9, "similarity": "close",
             "grid_delta_pct": 14.2, "palette_delta_avg": 6.1},
  "text_diff":   {"removed": [...], "added": [...], "moved": [...]},        // when OCR fed
  "text_summary": "REMOVED ...",                                           // human string for the VLM
  "color":       {"palette_pairs": [{"a": "#2563eb", "b": "#1d4ed8", "dE": 9.1,
                  "word": "noticeable", "weight": 0.31}],                  // weight = A-side area share
                  "unmatched_a": [...], "unmatched_b": [...], "avg_dE": 6.1},
  "grid_heat":   {"n": 16, "top_cells": [{"cell": [12,3], "dE": 31.5}], "hot_cell_pct": 14.2, "mean_dE": 8.0},
  "heatmap_ascii": "...",
  "edge_shape":  {"n": 16, "top_cells": [{"cell": [3,3], "density_a": 0.42, "density_b": 0.18, "delta": 0.24}], "hot_cell_pct": 6.0},
  "cost":        {"wall_ms": 8280, "extractors_ms": 9, "model_calls": [{"seat":"local-read","model":"...","ms":8271}]},
  "failures":    [{"stage":"vlm","code":"vlm_unavailable","retriable":true,"fix":"..."}],
  "next":        [{"reason":"...","cmd":"see diff a b --grid 32"}],         // paste-ready nudges
  "params_hash": "2fa50a1b980f5c89",
  "artifact": ".../outputs/see/<ts>-diff-.../" }

// verdict.json  (L2, gcc)
{ "overall": "pass|pass-with-notes|diverges", "policy_version": "...",
  "iteration": 2,
  "divergences": [{ "id": "d-btn-fill", "class": "brand-color",
      "where": {"grid": [12,3], "desc": "primary button"},
      "evidence": ["color.palette_pairs[0]", "grid_heat.top_cells[0]"],
      "judgment": "looks-worse|neutral|improvement|not-worth-chasing",
      "gestalt": false, "fix_hint": "background: #2563eb", 
      "status": "new|persisting|fixed|regressed" }],
  "suppressed": ["d-radius-…"], "notes": "..." }

// ledger.json (L3, per loop directory) — verdicts over iterations + trend of scores
```

## 5.5 · Cost & failure telemetry (histories are the API, here too)

Every run — L1, L2, loop round — carries and journals its own accounting:

```json
// rides inside evidence-pack.json AND verdict.json
"cost": { "wall_ms": 41200, "extractors_ms": 900,
  "model_calls": [ {"seat": "local-read", "model": "gemma4:26b",
                    "tokens_in": 2100, "tokens_out": 480, "ms": 38000, "retries": 0} ] },
"failures": [ {"stage": "E1", "code": "ocr_missing", "retriable": true,
               "fix": "npm install -g mac-ocr"} ]
```

- **Journal**: one line per run to `logs/compare-history.jsonl` (successes AND
  failures — the weekly self-audit gains a compare stream; failure classes
  trend like gemini's do now).
- **Failure taxonomy** (each carries `retriable` + a `fix` the agent can act on):
  `img_unreadable · ocr_missing · vlm_timeout · vlm_truncated · comparable_poor ·
  judge_schema_broken · judge_low_confidence`. Extractor failures are SOFT —
  the pack ships with what succeeded (fleet's salvage-first pattern), the
  failure block says what's missing and how to get it.
- **Retry semantics, fixed**: extractors auto-retry once (cheap, silent);
  the local VLM read retries once on timeout with the residency-aware clock;
  **the judge is never auto-retried** — it is the expensive seat, so failure
  emits a nudge (§5.6) and the controlling agent decides.

## 5.6 · Slice reruns, feedback, and nudges (the controlling-agent surface)

This tool's user is an agent, so it follows `~/.claude/conventions/
agent-first-tools.md` (the five obligations) — governing convention for every
surface below.

- **Content-addressed pack cache**: evidence packs key on hash(A, B, params);
  reruns are incremental. `see diff A B --only E5 --grid 32` re-runs ONE
  extractor and returns the **delta** (what changed in the pack), not the
  whole pack again — observation never costs a re-read.
- **Judge revisit with feedback**: `/vis-compare --revisit <divergence-id|all>
  --feedback "the radius call is wrong — compare the input corners
  specifically"`. Re-judges only the named slice(s) with the feedback in
  context; verdict is patched; the ledger records the re-ruling (`revisited`).
- **Nudges — the tool tells the agent when a rerun would help** (`next:` block,
  present in both text and JSON output; every nudge is an exact paste-ready
  command, per errors-propose-fixes):
  - `comparable: poor` → the crop/normalize retry command that would fix it
  - texty probe but E1 came back empty → image-quality flag + `--only E1` retry
  - grid heatmap saturated (>60% cells hot) → `--grid 32` refinement command
  - dHash says close but grid says hot (contradictory signals) → `--only E6` shape pass
  - judge tagged any divergence `confidence: low` → the `--revisit` command with focus
  - loop trend stalled 2 rounds → "escalate to native judge" (see §5.7)
- **Hard blocks at submit time** (reject early, explain, propose): `--only` of
  an extractor the modality probe skipped (error says WHY it was skipped and
  the `--force-modality` override); `--grid` outside 4–64; `--loop` against a
  `comparable: poor` pair; judge invoked without an evidence pack (points at
  the exact `see diff --json` command to produce one).

## 5.7 · Model-use map (every seat, explicit — nothing implicit anywhere)

| Seat | Model | Fires when | Cost class | Who decides |
|---|---|---|---|---|
| E0–E8 extractors | **none** | every run | $0, ~1s | always on |
| Local prose read (optional in `see diff`) | gemma4:26b (local) | on demand — **off by default in loop rounds** (`--no-read` is the loop default) | $0, 30–60s (lease for batches) | controlling agent |
| **L2 judge** | **Claude, native vision** — the only Claude seat | when `/vis-compare` is invoked | expensive-but-valuable (context/attention) | controlling agent, explicitly |
| Second opinion | gemini (vision) | **never by default**; `--second-opinion gemini` documented lane | abundant/cheap, untrusted-verify posture | user/agent opt-in per call |
| Sub-agents | none in the core path | — | — | — |

The cheap-and-frequent ↔ expensive-but-valuable balance, as process rules the
tool enforces rather than vibes:

1. **Extractors always, judge sparse.** Loop rounds iterate on machine evidence
   (free); the native judge fires at moments the controlling agent picks —
   and the tool NUDGES those moments rather than deciding: ledger stall
   (2 rounds without a `fixed`), all machine scores under policy floor
   (candidate ready for final judgment), or explicit user ask.
2. **Every judge invocation announces itself** before running: seat, expected
   cost class, and what cheaper alternative exists ("machine trend still
   improving — native judgment can wait"). The agent proceeds knowingly; the
   spend is in the cost block afterward. Explicit, never ambient.
3. **gemini stays out of the core** — it adds an abundance lane, not a
   capability the design depends on; if invoked, its output is untrusted-
   verify like everywhere else in the stack.

## 6 · Validation matrix (built BEFORE the capability is called done)

Fixture pairs, each with planted ground truth, run in the battery where model-free:

| Fixture | Ground truth | Guards against |
|---|---|---|
| F1 login-pair (exists: diff-a/b) | count/move/add | regression of today's behavior |
| F2 **icon pair**: generated glyph + perturbed copy (hue +15°, radius 4→10px, stroke −1px) | E4 distance >0, E5/E6 locate the corner cells, E3 catches hue | the user's 2-day test |
| F3 identical pair (same file twice) | ALL extractors ~zero; judge says clean | fabrication |
| F4 theme pair (same layout, inverted palette) | systematic ΔE everywhere + E1 empty diff | global-shift readability |
| F5 incomparable pair (icon vs dashboard) | `comparable: poor`, graceful, `next:` nudge with the crop command | garbage-in handling + nudge emission |
| F6 chart pair (axis relabel + one bar taller) | E1 catches label, E5 locates bar cell | mixed modality |
| F7 rerun patch (F2 then `--only E5 --grid 32`) | delta-only output, pack patched in place, cost block shows the increment | slice-rerun contract |
| F8 failure salvage (F1 with mac-ocr PATH-hidden) | pack ships E3–E6, failures block names E1 + fix, exit 0 | soft-failure + fix-proposing |

Battery: F1–F6 extractor assertions are model-free → verify.sh checks. L2 judged
outputs: manual fixture review once per policy change (documented, not automated —
judging the judge needs the human).

Live acceptance: one real pair from the user (the login pages), one real icon pair,
run end-to-end, user grades the verdict — THAT gate, not the battery, closes Phase D.

## 7 · Phases & effort

- **A · evidence pack** (lm): E0 normalize/probe/gate, E2–E6, pack schema WITH the
  cost/failures blocks + compare-history journal, pack cache + `--only` slice
  reruns, nudge emission, contact sheet, fixtures F1–F8 + battery wiring.
  Governing convention: agent-first-tools obligations. (~a day now — telemetry
  and rerun surfaces are load-bearing, not bolt-ons)
- **B · judge** (gcc): /vis-compare skill + policy.md v1 (drafted from the user's
  stated doctrine, then user-edited) + suppressions plumbing + `--revisit`
  feedback reruns + the announce-before-spend contract (§5.7.2). (~3h)
- **C · loop**: `--loop` mode, ledger, convergence stop-rules, E7/E8 lane docs.
  (~2h)
- **D · calibration**: real-pair runs, user feedback → policy v2, acceptance sign-off.

Order is A→B→D, with C after first real use (the loop's ergonomics should be
shaped by one manual round-trip, not guessed).

## 8 · Honest limits (so nobody discovers them in prod)

- Sub-pixel rendering (hinting, AA diffusion) is invisible to every layer and
  deliberately below policy floor.
- E5/E6 localize WHERE, not WHAT — shape *description* is native-vision gestalt,
  tagged as such.
- Static frames only; states are compared as separate pairs.
- DDG-class flakiness doesn't apply (fully offline), but big-tier residency does:
  the standalone `see diff` prose call wants a lease for batches (documented).
- The judge is as good as native vision + policy: it will catch what's worth
  fixing, not everything a trained human eye feels. That gap is accepted by the
  imitation doctrine, and F-pair calibration keeps it visible.

## 9 · L1 as shipped — built vs deferred (honest inventory)

Surfaced by an adversarial validation pass; recorded so nobody mistakes the
design's ambition for the current code. Built and battery-green: E0 (modality
probe + comparability gate), E1 (text/pos diff from OCR; moved entries carry
numeric `from_xy`/`to_xy`/`delta_xy`), E3 (palette/ΔE,
**population-weighted** so a re-encode can't fabricate a divergence — the F3b
guard), E4, E5, E6, contact sheet, slice-rerun cache, `next:` nudges, the
compare-history journal, and soft-failure handling (a down/failed VLM or absent
mac-ocr still ships the pack with an honest `failures` entry).

Deliberately **deferred** (the design describes them; the code does not yet do
them — do not assume they exist):

- **E0 letterboxing.** No shared normalized canvas; each extractor stretch-resizes
  A and B to its own grid, so cell coords are grid-relative, not original-space.
  Fine for same-aspect pairs; the comparability gate catches >2× aspect mismatch.
  `meta.letterboxed:false` and `dims_a`/`dims_b` say so. Reflow (U7) fidelity waits
  on real letterboxing.
- **E2 spacing/alignment deltas** — unbuilt (texty-only lane).
- **E3 texty per-element fg/bg sampling** (`element_samples`) — only the iconlike
  grid-cell-mean path exists; the per-text-fragment color sampling that U1 wants is
  not built. E3 currently reports the global palette match, not per-element color.
- **E1 within-bucket motion.** `moved` entries carry numeric centers since
  2026-07-11 (`from_xy`/`to_xy` always; `delta_xy` only for an unambiguous
  1-vs-1 pairing — averaging duplicates would fabricate a motion; observations
  with absent/non-finite geometry are skipped whole, F9/F9b guards, validation:
  `.claude/output/20260711-e1-coords-validation/report.md`). Still deferred:
  *detection* is label-gated (`A[k]["pos"] != B[k]["pos"]`), so text moving
  within its 3×3 bucket produces no `moved` entry — and no delta — at all.
  A numeric detection threshold is a Phase-D calibration question.
- **Telemetry (§5.5) — partial.** `failures` emits `vlm_unavailable` + `ocr_missing`
  and `cost.model_calls` records the VLM seat, but token counts are not captured and
  there is no auto-retry (extractor or VLM). The taxonomy's other codes are defined,
  not yet wired.

These are Phase-B-onward or calibration-time items; the fabrication guard, the
modality adaptivity, and the $0/model-independent contract — the load-bearing
claims — are the ones that hold today.

## 10 · L3 loop as shipped (Phase C, 2026-07-12)

The loop's **mechanical half** is `lib/vis-ledger.py` (bare python3, no model, no
PIL) plus `see diff --no-read` (the loop-round default — skips the VLM prose seat:
no model call, no ollama probe, no failure entry, ~1s/round). The **driving half**
is the `/vis-compare` skill's `--loop` mode (gcc side): apply fixes → re-render →
`see diff A B --no-read --json` → `vis-ledger.py add <loop-dir> <verdict|pack>` →
obey the signals. Loop dirs live at `outputs/see/loops/<slug>/`.

**Status words** — set comparisons over divergence ids; the judge never assigns
them (role discipline, §2):

| status | meaning |
|---|---|
| `new` | never seen in any prior round |
| `persisting` | present in the previous round, still present |
| `regressed` | absent in the previous round but seen earlier — it came back |
| `fixed` | present in the previous round, absent now (transitions-only) |

**Convergence signals**: `stop: "policy-pass"` on judge overall `pass` only
(`pass-with-notes` nudges "converged is the user's call" instead); `stall: true`
after 2 consecutive rounds with zero `fixed` (streak resets on any fix) → nudge
escalates to the native judge. The §5.6 hard block holds here: an `add --pack`
whose meta says `comparable: poor` is rejected before the ledger is touched.
Adds are sequential by design (one controlling agent per loop) — no file lock.
Guards: F10 (transitions/stall/stop), F10b (malformed shapes die structured),
F10c (a mid-write crash can't tear the ledger). Adversarial validation:
`.claude/output/20260712-loop-ledger-validation/report.md` — the gate found the
shape-validation gap + a status-fabricates-empty-loop inconsistency, both fixed
with mechanisms.

### E8 · DOM computed styles — BUILT 2026-07-13 (live-web lane)

`lib/e8-extract.js` + `lib/e8-dom.py`. The tool owns the **diff, not the browser**:
the capture script runs in any driver that can evaluate JS (Playwright/CDP MCP, a CI
harness) and its JSON feeds the diff — exactly as `bin/see` owns OCR while
`vis-compare.py` owns the text diff. Elements opt in via `id`/`data-e8`; color props
carry the same CIE76 ΔE as E3, so a number means the same thing in both lanes.

Two rules the **live** browser run taught (a synthetic fixture could not):

- **An invisible property is not a divergence.** Computed `border-color` follows
  `currentColor`, so recoloring text fabricates a phantom border diff even at
  `border-width: 0`. Suppressed when the border can't be seen on either side — the
  same fabricated-difference class E3's population-weighting kills.
- **Coverage is stated, never implied.** Only marked elements are captured, so the
  output reports `captured` / `dom_elements` / `uncaptured` with a nudge. A silent
  "3 elements compared" reads as complete when it isn't.

Guards F12/F12b (model-free). Live-proven on `probe/fixtures/e8-{a,b}.html`: 3/3
planted divergences, 0 phantoms, 4/4 coverage (captures kept as fixtures).

### E7 · AX geometry (documented, NOT built)

`ax` CLI element frames when both sides are running native apps — element-level
positions/sizes, so `moved` gains true element identity instead of OCR keys. Thin
glue into the same pack shape; stays unbuilt until a native-app loop demands it.

## 11 · The imagegen convergence lane (`imagine` × the L3 loop)

The same loop drives **local image generation** toward a reference: `imagine`
proposes, the L1 extractors measure, the judge rules, the ledger tracks, `imagine
refine` applies the correction. Every round is $0 (local GPU + local extractors);
only the judge moments cost the expensive seat.

```
reference A ──▶ imagine --from A --strength S "<prompt>"  ──▶ candidate B
                                                               │
   ┌───────────────────────────────────────────────────────────┘
   ▼
see diff A B --no-read --json   ($0, ~1s — machine evidence)
   │
   ├─ scores under floor / stall / explicit ask ─▶ /vis-compare A B  ──▶ verdict.json
   │                                                                       │
   ▼                                                                       ▼
vis-ledger.py add <loop-dir> verdict.json --pack evidence.json  ──▶ signals
   │                                                            (stop | stall | continue)
   ▼
imagine refine <N> "<delta from the verdict's fix_hints>"   ──▶ next candidate
```

**The load-bearing constraint: refine, don't re-roll.** `imagine refine N "delta"` is
**seed-locked** — it changes only what you name and holds the roll. `vary`/a fresh
prompt re-rolls the whole image, so every divergence would read as `new`/`regressed`
and the ledger's convergence semantics become meaningless. Seed-locked refinement is
what makes `fixed`/`persisting` say something true about an imagegen loop. Re-roll
only when abandoning the roll entirely (and start a new loop dir when you do).

**Read progress from the LEDGER, never from the scores.** Proven on the live round-trip
(2026-07-13): a seed-locked refine fixed 3 of 5 divergences — the cat came back the right
cat, the right pose, the right render style — while the L1 scores went *sideways*
(dhash 28→24, grid 93.8%→**100.0%**, palette 25.7→24.5). Region/pixel ΔE saturates on any
composition change, so it cannot see identity converging. In this lane L1's job is the one
it always had — **fabrication-proofing**, no claim the pixels don't support — while
progress lives in the ledger's `fixed`/`persisting`/`regressed` transitions. A loop that
stopped on "scores stopped improving" would have quit exactly when it was working.

Practical notes: `qwen` is the working model here (~3 min at 8 steps); `--strength` is the
freedom dial on `--from` (lower = closer to A); the `imagine critique` local-vision seat is
a cheap pre-read but never a substitute for the policy judge. **Check the model cache
first** — `verify.sh` now fails on a partial one, because a half-downloaded model makes
`imagine` hang re-fetching instead of generating (that is what a "slow" generation at 2%
CPU actually is). Live round-trip record + the environment finding:
`.claude/output/20260713-imagine-loop/round-trip.md`.
