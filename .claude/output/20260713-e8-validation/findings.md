# E8 DOM computed-styles lane — adversarial validation

<!-- sessions: vis-ab-3c@2026-07-13 -->

**Under test:** lib/e8-dom.py, lib/e8-extract.js, battery F12/F12b. **Validator:** sonnet,
isolated worktree, mutation-testing mandated; findings inline, persisted by the parent.

## VERDICT: ISSUES-FOUND (6 fixed, all guarded by F12c)

### MAJOR — alpha dropped from color parsing (a FALSE NEGATIVE, the worst class)

`rgba(0,0,0,0)` → `rgba(0,0,0,1)` — transparent to opaque black, about the most dramatic
change a surface can make — measured **dE 0.0, "negligible"**. The regex captured only
three groups. This is worse than a fabricated divergence: it actively mislabels a real,
huge change as nothing, with false precision.

**Fixed:** colors are composited onto white by their alpha before ΔE, so alpha changes
register in the same units as every other color claim.

### MAJOR — `opacity: 0` elements fabricated divergences

`invisible()` only special-cased `border-color`. An element invisible on both sides still
reported full color/background divergences. **Fixed** by generalizing the rule from a
border special-case to a principle: *a change nobody can see is not a change* — an unseen
element yields nothing.

### MAJOR — zero-geometry `box-shadow` double-reported one visible change

`box-shadow: <currentColor> 0 0 0 0` renders nothing, but its color follows `currentColor`
— so a text recolor emitted a second, phantom divergence. **Fixed** (same principle).

### MAJOR — malformed `styles` / duplicate / missing selectors

A list-shaped `styles` or a numeric style value tracebacked with empty stdout; duplicate
`id`s (a real authoring mistake) silently collided in a dict comprehension, dropping an
element from the comparison with no warning. **Fixed:** an `index()` gate that dies
structured on a missing/duplicate selector or a non-object `styles` — a dropped element
is a lie of omission.

### MINOR — self-contradicting coverage clamped to a clean-looking "fully covered"

`dom_elements < captured` (impossible input) reported `uncaptured: 0`. **Fixed:** flagged
with a warning; coverage is reported as unknown rather than fabricated. Also:
marked-but-unpaired elements no longer count as "unmarked" (their fix hint was wrong).

### MINOR — `letter-spacing: normal` vs `0px`

Identical rendering, different string; a CSS reset on one side fabricated a typography
divergence. **Fixed** via a render-equivalence table.

## What held

`invisible()` never over-fires (a visible border-color change is always reported; a
0→2px border transition is not suppressed). Real browsers resolve `color-mix()`/`oklch()`
/`color(display-p3 …)` to flat rgb() before serialization, so the regex's graceful
`None` is correct. Space-separated CSS Color 4 syntax parses. Non-dict garbage in
`elements[]`, a bare-array capture, and a missing `elements` key all die structured.
Mutation tests: neutering `invisible()`, breaking the coverage math, and forcing ΔE to 0
each turn the battery red — the guards do real work.

Battery 39 → 48. Live captures re-verified after hardening: 3/3 real divergences, no
regression.
