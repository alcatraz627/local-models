# E1 numeric position deltas — adversarial validation report

<!-- sessions: vis-ab-3c@2026-07-11 -->

**Change under test:** commit `29dd60d` — `moved` entries gain `from_xy`/`to_xy`/`delta_xy`
(lib/vis-compare.py), guarded by F9 in probe/fixtures/vis-battery.py.
**Validator:** one adversarial sonnet sub-agent (pinned, no nesting), findings returned
inline per the /bloop Phase 4.4 workaround; persisted here by the parent.

## VERDICT: ISSUES-FOUND

### BLOCKER — fabricated position on missing/partial boundingBox

`_load_ocr` read geometry with silent `bb.get(k, 0)` defaults and had no guard analogous
to the `if not t: continue` text check. An observation with no `boundingBox` at all got
center `[0.0, 0.0]` — and in the 1-vs-1 case produced a fully-formed fabricated motion:

```
"from_xy": [[0.0, 0.0]], "to_xy": [[0.85, 0.825]], "delta_xy": [0.85, 0.825]
text_summary: MOVED: "Ghost label" top-left -> bottom-right (d=+0.85,+0.82)
```

Real mac-ocr always populates `boundingBox` (0/3 missing on the fixture read), but
`--ocr-a/--ocr-b` are public CLI flags, so malformed input is in scope. The delta-
suppression logic only guards duplicate pairing — this was the unambiguous path.

### MINOR — F9 ambiguous assertion checked lengths only; center sort unverified

Mutation test: flipping the delta sign → F9 fails (good); removing the `(cy, cx)` sort
entirely → all F9 checks still passed. Gap: no coordinate-value assertions on the
multi-instance path.

### MINOR — NaN/Infinity in crafted bbox propagates into the pack JSON

`boundingBox.width: NaN` → `"delta_xy": [NaN, 0.0]` — bare `NaN` is not valid RFC 8259.
Python json and jq tolerate it (bin/see pipeline unaffected); strict parsers would throw.

### MINOR (pre-existing, design note) — label-set gate caps the numeric feature

Same 3×3 bucket on both sides (0.05,0.05 → 0.30,0.30) never enters `moved`, so no
`delta_xy` for within-bucket motion. The trigger `A[k]["pos"] != B[k]["pos"]` predates
this change; needs a doc note, not a code change (detection threshold is a Phase-D
calibration question).

### NIT — near-zero negative delta renders `-0.00`

Cosmetic; accepted.

## Attacks that found nothing (coverage)

Battery 17/17 with mac-ocr, 14/14 + clean skip without it (F9 truly model-free) ·
negative-direction moves format correctly · 2-vs-2 duplicates stay honest (delta None,
unpaired center bags) · exact-duplicate double-report → ambiguous path · corrupt JSON on
one side → pre-existing try/except degradation · real mac-ocr E2E on the login pair
(`"Refresh" (d=+0.67,+0.00)`) · `%`-in-text format-string safety · zero-size bbox is
degenerate-but-not-fabricated.

## Resolution (commit `7eeb4ce`)

- **BLOCKER fixed with a mechanism:** geometry is now as mandatory as text in
  `_load_ocr` — an observation with absent or non-finite `x`/`y`/`width`/`height`
  is skipped whole (same idiom as the text-less skip). No default, no clamp, no
  guess. This also kills the NaN leak at the boundary it entered through.
- **Guard strengthened for the exploited input class:** F9b plants a bbox-less
  observation and a NaN-width observation; asserts no `moved` entry, honest
  degradation to ADDED, and `json.dumps(pack, allow_nan=False)` succeeding.
  Red-then-green sequence confirmed (both F9b checks failed against `29dd60d`).
- **F9 ambiguous case** now asserts sorted center *values*, not list lengths —
  closing the mutation-test gap (sort removal is now caught).
- **Label-gate cap** documented in `docs/10-visual-compare-design.md` §9 (within-
  bucket motion produces no moved entry; numeric detection threshold = Phase D).
- **`-0.00` nit:** accepted, cosmetic.
- Battery after fixes: **19/19**.

