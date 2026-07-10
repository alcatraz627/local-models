# Adversarial review — Vision lenses design (`docs/08-vision-lenses-design.md`)

**Reviewer stance:** trying to kill this. Verdict at the bottom.
**Grounded in:** `bin/see`, `bin/q`, `config.sh`, `intents/review.toml`, the
fidelity audit (`parse-comparison.md`), `/tmp/mk_ocr.py`. Read this session.

---

## CRITICAL

### C1 — The cited evidence does not support the lens design; it was already acted on, differently

The doc's whole §1 problem statement leans on the fidelity audit: *"gemma4:26b
read 'the shape, not the words'"* (`08:13`). But that audit
(`parse-comparison.md`) tested **gemma4:26b**, and its finding was *model
choice*, not *prompt choice*. The fix that finding actually motivated already
shipped: `config.sh:33` now defaults `VISION_MODEL=minicpm-v`, with a comment
(`config.sh:28-32`) saying minicpm *"transcribed verbatim text/commands/counts
that gemma4:26b MISSED."*

So the verbatim-fidelity problem the doc opens with was a **model** problem and
is **already solved** by the model swap. The doc's own §1 sentence even concedes
this: *"even on the right model a generic prompt won't know that a dashboard's
point is its numbers"* (`08:14-15`) — but that is a much weaker, unproven claim,
and it is the *only* thing left for lenses to fix once the model swap is
accounted for. The doc borrows the **drama** of the gemma verbatim failure to
justify machinery that addresses a **different, smaller, undemonstrated**
problem (per-context emphasis). That is motivated framing. Nowhere does the doc
show minicpm-v *under the current general prompt* missing a dashboard number
that a `dashboard` lens would have caught. There is no before/after on the actual
model. The load-bearing evidence is about a model you no longer use.

**Consequence:** the headline justification ("don't miss details") is already
delivered by the model swap. Lenses must justify themselves on the residual
("right emphasis per context"), which the doc never measures.

### C2 — The verbatim lenses are built on a substrate the doc's own evidence calls untrustworthy

`parse-comparison.md` documents minicpm/gemma **inventing UI that isn't there**
(an "audio/volume" button on img2, `parse-comparison.md:46-47`) and
**mislabeling a light theme as dark** (img4, `:76-77`). The doc proposes
`doc`, `dashboard`, `ui-ux` lenses whose entire value proposition is *"verbatim
OCR,"* *"every metric verbatim,"* *"capture every label."* A lens prompt cannot
make a 5.5GB local VLM stop hallucinating controls or misreading colors — it
only changes what you *ask* for, not OCR accuracy. The audit's own takeaway
(`:85-87`) is explicit: *"Treat its specific UI claims with suspicion ... its
long-text transcription as unreliable ... native for what exactly does it say."*

A `dashboard` lens that promises "every KPI tile, verbatim" sets a fidelity
expectation the model demonstrably cannot meet, and worse: by asking for an
*exhaustive* enumeration you increase the surface for confident fabrication
(the model will fill the requested slots). The crisper the rubric, the more the
model is pushed to hallucinate completeness. The doc's mitigation —
*"lenses are supersets (every lens still reports verbatim text first)"*
(`08:163`) — assumes the verbatim read is good. The evidence says it isn't.

**This is the deepest problem.** The lens layer is a prompt-engineering
refinement sitting on a transcription floor that the project's own audit rates
as unreliable for exactly the content the flagship lenses target.

---

## MAJOR

### M2 — Open-question #1 (the single self-adaptive prompt) is the right answer for ~3 of 4 slices, and the doc never argues against it

The doc files this as an open question (`08:176-178`) but never disposes of it.
It should, because it largely wins. A single prompt — *"First identify the image
type (dashboard / UI / document / artwork / AI-generated / other), then report
the detail that matters for that type: for dense UI capture every label and
value verbatim; for artwork describe composition, palette, mood; always report
all legible text first and flag anything anomalous"* — fits in the existing
`bin/see:78` string, costs **zero** extra calls (the type-identification and the
read happen in one pass), needs **no** registry, **no** `--as`, **no**
auto-detect classify call, **no** loader, **no** golden-set-per-lens.

Where the single prompt delivers ~90% of the value:
- **Per-context emphasis** (the residual problem from C1): a competent VLM
  *can* shift emphasis on instruction within one prompt. This is exactly the
  kind of conditional the instruction-following is for.
- **The "don't make the caller spell it out" goal (§1 goal 3):** fully met —
  the model self-adapts, no keystrokes, no Claude inference needed.
- **Reusability by extension + local collective (the doc's #1 argument for the
  tool, `08:36-39`):** *equally* met. The richer prompt lives in
  `see/lenses/general.toml` (or just `bin/see`) and every caller gets it for
  free. The doc's claim that knowledge "in Claude's head" is lost to other
  callers is a **strawman** — nobody proposed putting it in Claude's head; the
  alternative is one richer prompt *in the tool*, which is just as shared,
  durable, versioned, and diffable as seven prompts in the tool.

Where the single prompt actually fails (the real 10%):
- **Per-lens model routing** (`08:108-109`): one prompt can't send art→gemma and
  dashboard→minicpm. But see M5 — this routing is itself premature.
- **`--thorough` multi-pass merge:** genuinely needs >1 call. But see M6.
- **Auditable per-context regression:** seven golden sets vs one. Marginal, and
  the per-lens golden sets don't exist yet anyway (C4).

So the registry buys you: model-per-lens (premature, M5) + thorough mode
(unproven, M6) + finer regression buckets (nice-to-have). That is a thin
residual for ~120 lines + 7 toml files + a classify-call subsystem + a
maintenance surface. **The doc inverts the burden of proof:** it treats the
registry as the default and the single prompt as the thing needing
justification. It's the other way around — the project's own
`speculative-abstractions-without-a-load-bearing-caller` rule says inline until
≥2 real callers force the abstraction.

### M3 — "Selection automatic" relocates the burden onto Claude and onto a hallucination-prone classify call; it does not remove it

§5's claim that selection is automatic rests on two paths (`08:113-119`):

1. **Caller-inferred** — *"Claude passes `--as dashboard` because it is auditing
   a dashboard."* This is not free automation; it is **Claude doing extra work
   on every call** and having to know (a) the flag exists, (b) the lens names,
   (c) which lens fits. The doc's own caller-path test (`08:150-151`) admits this
   is unproven — *"a sub-agent given only 'audit this dashboard' should call
   `see --as dashboard` without being told the flag."* If that test *fails*
   (likely — sub-agents don't reliably discover undocumented flags), the whole
   "primary" selection path collapses to either auto-detect or explicit, i.e.
   the crutch the design exists to avoid. The doc bets its primary path on
   emergent flag-discovery and never de-risks it.

2. **Auto-detect** — one classify call to *the same hallucination-prone VLM*
   that invented an audio button. When it picks wrong, it **hides the detail the
   user needed**: classify a dense dashboard as `art` and you get
   composition/palette/mood — the numbers are *gone*, not merely de-emphasized,
   because the `art` lens doesn't ask for them. The doc's mitigation
   ("lenses are supersets, every lens reports verbatim text first," `08:163`)
   directly **contradicts** the lens table: the `art` lens row (`08:104`) is
   *"subject + composition + palette + style + mood"* — no verbatim-text clause.
   So either the table is wrong or the superset mitigation is. They can't both
   hold. This is the project's own `proposed-fix-breaks-design-invariant`
   pattern: the "supersets" invariant in §9 contradicts the lens definitions in
   §4.

**Net:** "automatic" = "Claude works harder" OR "a flaky classifier silently
drops content." Neither is the clean win §2 sells.

---

## MAJOR (engineering / validation)

### C4 / M4 — The validation plan tests the easy thing and is partly circular

- **The golden-set method it "extends" is synthetic.** `/tmp/mk_ocr.py` renders
  *crisp monospace text on a clean background* (`mk_ocr.py:14-34`) — a best-case
  OCR target, the opposite of the messy real screenshots (anti-aliased UI, low
  contrast, dense layout) where the audit found the model failing. Passing the
  golden set proves the model reads clean synthetic text, which was never in
  doubt. It does **not** prove the `dashboard` lens enumerates all KPIs on a
  *real* dashboard.
- **The "captured / total ≥ 0.9" dashboard check (`08:144-146`) has no
  hallucination term.** A model that emits 10 plausible-but-wrong KPI values
  scores 0.9 if 9 names happen to match. Recall without a precision/fabrication
  guard is the wrong metric for a tool whose documented failure mode is
  *inventing* content (C2). The metric rewards exactly the failure.
- **Auto-detect accuracy on "~20 labeled images" (`08:146-147`)** — fine as far
  as it goes, but "a wrong lens must degrade gracefully" is asserted, not
  tested, and contradicts C4/M3 (the `art` lens does *not* degrade gracefully on
  a dashboard — it drops the numbers).
- **The regression test (`08:148-149`) — "byte-for-byte equal to today's
  general read"** — is the *only* rigorous check here, and it only proves you
  didn't break the status quo. It proves nothing about whether lenses *add*
  value.

There is **no test in §8 that compares a lens against the single richer prompt**
— i.e. no test that would tell you whether the entire registry is worth building.
The validation validates the implementation, not the decision.

### M5 — Per-lens model routing is premature and the doc half-admits it

The lens table routes `art`/`ai-gen` → gemma4:26b and the rest → minicpm-v
(`08:104-109`), justified by "the fidelity finding." But the fidelity finding
(`parse-comparison.md`) **only tested screenshots/UI**, not art or AI-gen images
— there is *zero* evidence in the audit that gemma beats minicpm on a painting.
The routing for the aesthetic lenses is asserted from intuition, not the cited
data. Open-question #3 (`08:181`) concedes minicpm "may suffice once tuned." So
build with one model, prove a second is needed, *then* route. Routing now is a
speculative branch (`lens_model()`, `08:78`) wired before any measurement
demands it.

### M6 — `--thorough` is complexity the doc itself can't defend

Open-question #4 (`08:182-183`) asks whether `--thorough` earns its keep vs
*"Claude calls `see` twice with two lenses."* It doesn't answer. The answer is
**no**: if Claude is already the merge-reasoner (the doc's whole "VLM parses,
Claude reasons" thesis), then Claude calling `see --as doc` then `see --as ui-ux`
and merging the two outputs itself is strictly simpler than a `--thorough` mode
that fans out, labels, concatenates, caps concurrency, and surfaces partials
(`08:124-126`, `08:165-167`). `--thorough` adds a concurrency-management surface
(the img4 >240s hang multiplied, `08:165`) to do something the caller can already
do with two plain calls. Cut it.

---

## MINOR

### m7 — Latency mitigation "cache classify by image hash within a run" is underspecified and probably useless
`see` is a one-shot CLI process (`bin/see` runs and exits). There is no "run"
spanning multiple `see` invocations to cache across — each call is a fresh
process. In-process caching saves nothing because one process classifies at most
one image. The mitigation (`08:161`) names a cache scope that doesn't exist in
the tool's process model. Either it means a cross-process cache (unspecified,
and a `cache-externally-mutated-state` hazard) or it's a no-op.

### m8 — `set -eo pipefail` + `yq` loader: the `intent_*` copy needs the same care the original got
The doc says the loader "mirrors the intent registry verbatim" (`08:71-72`).
Note `bin/q`'s helpers swallow yq errors with `2>/dev/null` and `// ""`
fallbacks (`bin/q:130-131`) *because* `see` runs under `set -eo pipefail`
(`bin/see:10`) — a yq failure mid-pipe under `pipefail` would abort. Fine if
copied faithfully, but "verbatim" copies of the happy path that drop the
error-swallowing will break under `pipefail`. Low risk, flagged so it's not
lost.

### m9 — Who maintains seven rubrics, and against what?
The doc waves at "lenses graduate from real use" (`08:157`) and "each lens
carries `updated`" (`08:168`), but there is no owner, no cadence, and the
regression guard (the golden set) doesn't exist yet (C4). Seven prompt-blobs
that rot as models improve, with no enforced re-tuning trigger, is a
maintenance liability the doc acknowledges (`08:168`) but does not staff.

### m10 — Blind spot: how does the extension actually pick a lens?
§2 argument #1 (`08:36-39`) leans hard on "the better-file-browser extension
calls `see --json` directly." But the extension is *not Claude* — it can't
"infer from task context." So for the extension, selection collapses to
**auto-detect** (the flaky classify call) or a **hardcoded `--as`** the
extension author chose. The doc's primary selection path (caller-inferred by
Claude) **does not exist** for the headline non-Claude caller. The extension
gets only the two weaker paths. This undercuts the §2 reusability argument it's
attached to.

---

## What I could NOT fault

- The grounding discipline is real: the `lens_*` snippet (`08:74-79`) does
  faithfully mirror `bin/q:128-131`, and §9's structural-claim note is honest.
- Slice 1 (registry + `--as` + `general` lens, no behavior change) is genuinely
  low-risk *if* you build it — it's an additive escape hatch.
- The "knowledge as data, not in Claude's head" instinct is correct **as a
  principle**; the error is concluding it requires *seven* lenses rather than
  *one richer prompt in the tool*.

---

## VERDICT: BUILD SIMPLER

The single self-adaptive prompt (open-question #1) wins. Build that, not the
registry. Concretely:

**DO build (slice 1, trimmed):**
- Replace `bin/see:78` with **one richer self-adaptive prompt**: "identify the
  image type, then report type-appropriate detail; always report all legible
  text verbatim first; flag anomalies." Put it in the tool (in `bin/see`, or a
  single `see/lenses/general.toml` if you want it diffable/versioned — that
  satisfies the "knowledge as data + reusable by every caller" goal completely).
- Keep `--as LENS` **only as a thin explicit override** that swaps the system
  prompt, AND only once you have ≥2 *real* callers that pass it (the project's
  own speculative-abstraction rule). Until then, don't even ship `--as`.

**DO NOT build (cut these slices):**
- **Auto-detect classify call (slice 3)** — it relocates the problem onto a
  hallucination-prone extra call that *silently drops* content on misclassify
  (C2/M3), and the single prompt already self-routes emphasis for free.
- **Per-lens model routing (M5)** — no evidence art/ai-gen need gemma; prove it
  with measurement first.
- **`--thorough` (slice 4 / M6)** — Claude calling `see` twice and merging is
  strictly simpler and the doc can't defend the mode.
- **The seven-lens registry (slice 2)** — speculative until callers force it;
  `social` already cut by the doc's own #9, and `art`/`ai-gen`/`alt` have no
  load-bearing caller today either.

**Before building anything, run the one test §8 omits:** on the *real* 4-image
audit set, compare `minicpm-v` under (a) today's general prompt, (b) the single
richer self-adaptive prompt, (c) a hand-written `dashboard` lens. Score recall
**and** fabrication. If (b) ≈ (c), the registry is dead. If (b) ≪ (c) on a real
dashboard with no added hallucination, *then* you have a load-bearing caller for
exactly one lens — build that one, inline, and stop.

**The deeper caution (C2):** whatever you build, do not let any lens promise
"verbatim / every value" fidelity. The project's own audit rates this model's
transcription unreliable and its UI claims hallucination-prone. A lens cannot
fix OCR. Frame `see` output as a *gestalt/structure* read to be verified by
native vision for anything cited — which is exactly what `parse-comparison.md`
already concluded before this design was written.
