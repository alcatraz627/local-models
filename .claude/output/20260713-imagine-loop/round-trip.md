# imagegen convergence lane — live round-trip record

<!-- sessions: vis-ab-3c@2026-07-13 -->

Protocol: `docs/10 §11`. This is the exercise record — what actually ran, and what
could not.

## Environment finding (surfaced to the user, NOT fixed — needs their call)

**`imagine -m schnell` cannot generate: its model cache is incomplete.**
`~/.cache/huggingface/hub/models--black-forest-labs--FLUX.1-schnell` holds **9.8 GB**
of a ~24 GB model, so every run re-enters `Downloading model from HuggingFace…
Fetching 13 files` and blocks on the network — observed as a 38-minute "generation"
pinned at 2% CPU with no output, and reproduced with a minimal 1-step 256px call.

- Root cause is the cache, not the code — no memory pressure (70% free), no resident
  models, no GPU contention.
- `qwen` (49 GB) is **fully cached** and works; the loop rounds below use it.
- **Not fixed here on purpose:** completing the pull is a multi-GB network action the
  user decides (standing rule: never download a model without explicit confirmation).
  Fix when wanted: `imagine -m schnell "<anything>"` and let it finish the fetch once.
- Why `verify.sh` didn't catch it: the suite deliberately excludes imagegen ("imagine
  generation (GPU, ~min)" is in its not-covered list). This is the gap that let a
  broken lane sit quiet — worth a cheap liveness check (a 1-step 64px render) rather
  than a full generation.

## What the loop proved (2 live rounds, qwen @ 8 steps, ~3 min/round)

Reference: `beanu-boss-spaceship-v3` (bright teal 3D render, relaxed orange tabby in a
detailed cockpit). Loop dir: `outputs/see/loops/imagine-spaceship/`.

| round | candidate | ledger transitions |
|---|---|---|
| 1 | text2img from a fresh prompt | 5 new (subject-color, palette, exposure, pose, render-style) |
| 2 | **seed-locked `refine 16`** on round 1's `fix_hint`s | **3 fixed** (subject-color, pose, render-style) · 2 persisting (palette, exposure) · 2 new (composition, wardrobe) · no stall |

Round 2's cat came back an **orange ginger tabby with a cream chest, lounging with its
eyes closed, in a stylized 3D render** — three divergences the verdict named, corrected
in one seed-locked pass. The loop works end to end: `imagine` → `see diff --no-read`
(0.74s, $0) → judge → `vis-ledger add` → `imagine refine` → repeat.

## CALIBRATION FINDING (the important one)

**For imagegen, the L1 pixel scores are a poor convergence signal — the judge's
divergence transitions are the real one.** Round 2 improved identity fidelity
dramatically while the machine scores barely moved (dhash 28 → 24, grid 93.8% →
**100.0%**, palette 25.7 → 24.5). Region/pixel ΔE saturates the moment the composition
differs, so it cannot see "the cat is now the right cat."

This does not weaken L1 — it re-scopes it. In this lane L1's job is what it always was:
**fabrication-proofing** (no divergence may be asserted that the pixels don't support).
Progress measurement belongs to the ledger's fixed/persisting/regressed transitions.
A loop that stopped on "scores stopped improving" would have quit exactly when it was
working. Worth folding into policy: `stall` on an imagegen loop must be read from
transitions, never from score deltas.
