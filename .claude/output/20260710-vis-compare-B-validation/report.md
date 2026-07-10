# Visual-compare Phase B (judge skill) — adversarial validation + dispositions

<!-- sessions: vis-compare-A@2026-07-10 -->

A sonnet validation sub-agent reviewed the `/vis-compare` gcc skill adversarially,
running `see diff` live on four fixture pairs and cross-checking the dry-run
verdict against the pack source pixel-by-pixel. Verdict: **ISSUES-FOUND**, one
BLOCKER. (Guard-blocked from writing its own report; parent persists it.)

## Findings and dispositions

| # | Sev | Finding | Disposition |
|---|-----|---------|-------------|
| 1 | **BLOCKER** | The dry-run verdict.json assigned `where.grid [3,1]`/`[4,1]` to two TEXT divergences with `gestalt:false`, but `text_diff.removed`/`added` carry no position (vis-compare.py:263). The judge eyeballed coords into a measured slot — the anti-fabrication rule (policy.md) is unenforceable prose, violated on run #1. | **FIXED** — `where.grid` now valid ONLY from a grid-bearing evidence cell (grid_heat/edge_shape); text divergences use `desc` + (for moved) the text_diff from/to LABELS, never invented coords. Added a mandatory **pre-write self-check** in SKILL.md Phase 4: every `gestalt:false` value must trace to a cited evidence[] path or it's dropped/flagged. Produced verdict.json corrected. |
| 2 | major | `allowed-tools: Read, Bash` can't write verdict.json / patch it / append suppressions (GUIDELINES mandates Write/Edit) — copied from ui-gripe which never writes structured files. | **FIXED** — added `Write, Edit`. |
| 3 | major | Three `class` naming schemes (policy phrases / docs hyphen-slug / verdict bare words) — breaks the fingerprint + suppression match. | **FIXED** — pinned canonical slugs in policy.md (`info-loss`/`affordance-loss`/`hierarchy-shift`/`brand-color`/`spacing-rhythm`/`micro-type`/`texture`/`layout-placement`), required verbatim. |
| 4 | major | No ladder class for a plain reposition (button moved regions, dominance unchanged); dry-run misclassed it "hierarchy". Recurs for U7 reflow. | **FIXED** — added the `layout-placement` rung. |
| 5 | major | The `--revisit`/suppressions fingerprint won't survive a re-render for text divergences: ungrounded grid coords (F1) + no letterboxed coord space (docs/10 §9) + undefined "evidence-signature". | **FIXED** — fingerprint reworked to stable anchors (class-slug + text-string for text divergences / grid-cell for shape-color divergences), grid dropped from text fingerprints; letterbox caveat documented. |
| 6 | minor | verdict.json omits the `cost` block (design §5.5 says it rides here too). | **FIXED** — added `cost` to the verdict contract. |
| 7 | minor | `confidence: low` revisit nudge is dead (no `confidence` field in the verdict). | **FIXED** — added `confidence` per divergence. |
| 8 | nit | Phase 0 suppression pre-classification sequenced before divergences exist. | **FIXED** — reworded to "hold in mind, apply per-divergence in Phase 3". |

## What held up (tried to break, could not)

Every `.evidence` field the skill cites exists with that exact name in two live packs
(no stale `meta.normalized`). verdict.json top-level + per-divergence field set matches
docs/10 §5. F3 identical → all scores 0, text_diff empty (discipline holds structurally).
F5 incomparable → `comparable:poor` + crop nudge. `contact.png`/`evidence.json` land in
the artifact folder. Frontmatter valid, skill live-registered.

## Net

The BLOCKER — the anti-fabrication guard being unenforceable and immediately violated —
is the headline lesson: prose rules do not bind a model; a **mechanical self-check**
does. That check (every measured value must trace to a cited evidence path) is now in
the skill, and the one real verdict is corrected. The four MAJORs (tool perms, class
enum, missing placement class, fingerprint fragility) are fixed; the minors/nit too.
