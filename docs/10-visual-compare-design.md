# Visual Compare — a full-stack capability for "does B faithfully imitate A?"

<!-- sessions: local-next-a4@2026-07-10 · STATUS: PLAN, awaiting user approval -->

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
// evidence-pack.json  (L1, lm)
{ "meta": {"a": "...", "b": "...", "normalized": [800,600], "modality": "iconlike",
           "comparable": "good|poor", "skipped_extractors": ["E1","E2"]},
  "scores": {"dhash": 12, "ahash": 9, "similarity": "close",
             "grid_delta_pct": 14.2, "palette_delta_avg": 6.1},
  "text_diff":   {"removed": [...], "added": [...], "moved": [...]},        // texty
  "spacing":     {"pairs": [{"text": "...", "dx_pct": 1.2, "dy_pct": -3.0}],
                  "rhythm": {"a": [24,24,32], "b": [24,31,31], "drift": "..."}},
  "color":       {"palette_pairs": [{"a": "#2563eb", "b": "#1d4ed8", "dE": 9.1,
                  "word": "noticeable"}], "element_samples": [...]},
  "grid_heat":   {"n": 16, "top_cells": [{"cell": [12,3], "dE": 31.5}]},
  "edge_shape":  {"top_cells": [{"cell": [3,3], "density_a": 0.42, "density_b": 0.18}]},
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

## 6 · Validation matrix (built BEFORE the capability is called done)

Fixture pairs, each with planted ground truth, run in the battery where model-free:

| Fixture | Ground truth | Guards against |
|---|---|---|
| F1 login-pair (exists: diff-a/b) | count/move/add | regression of today's behavior |
| F2 **icon pair**: generated glyph + perturbed copy (hue +15°, radius 4→10px, stroke −1px) | E4 distance >0, E5/E6 locate the corner cells, E3 catches hue | the user's 2-day test |
| F3 identical pair (same file twice) | ALL extractors ~zero; judge says clean | fabrication |
| F4 theme pair (same layout, inverted palette) | systematic ΔE everywhere + E1 empty diff | global-shift readability |
| F5 incomparable pair (icon vs dashboard) | `comparable: poor`, graceful | garbage-in handling |
| F6 chart pair (axis relabel + one bar taller) | E1 catches label, E5 locates bar cell | mixed modality |

Battery: F1–F6 extractor assertions are model-free → verify.sh checks. L2 judged
outputs: manual fixture review once per policy change (documented, not automated —
judging the judge needs the human).

Live acceptance: one real pair from the user (the login pages), one real icon pair,
run end-to-end, user grades the verdict — THAT gate, not the battery, closes Phase D.

## 7 · Phases & effort

- **A · evidence pack** (lm): E0 normalize/probe/gate, E2–E6, pack schema, contact
  sheet, fixtures F1–F6 + battery wiring. (~half day)
- **B · judge** (gcc): /vis-compare skill + policy.md v1 (drafted from the user's
  stated doctrine, then user-edited) + suppressions plumbing. (~2h)
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
