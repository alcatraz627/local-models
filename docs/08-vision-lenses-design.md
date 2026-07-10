# Vision lenses — context-adaptive `see`

**Status:** design proposal (2026-06-25). Pairs with `docs/06-local-orchestration-design.md`
(the local collective) and the intents-as-data registry (`intents/*.toml` + `bin/q`).

## Outcome — BUILD SIMPLER (the registry is not justified)

A skeptic review (`.claude/output/20260625-vision-lenses/skeptic.md`) plus an empirical
3-way test on the real `img2` (MiniCPM-V under today's general prompt vs a single
self-adaptive prompt vs a hand-written `dashboard` lens, graded on recall AND fabrication)
killed the registry:

- **The `dashboard` lens did NOT beat the single adaptive prompt** — it missed the 522-block
  count (general caught it), missed 160 tool calls (adaptive caught it), and *fabricated*
  color semantics ("purple = bypassPermissions"). Specialized ≠ better.
- **All three missed the masthead numbers (62.5K/352.4K/52.3M) and read the message
  non-verbatim, identically** — verbatim fidelity is a MODEL-floor property, invariant to the
  prompt. A lens cannot fix OCR (skeptic C2, confirmed by data).
- **The biggest lever was the anti-fabrication clause, not the lens** — the adaptive prompt
  ("flag `[unsure]`, do not invent") fabricated least.

**Revised plan (supersedes §3–7 below).** Do NOT build the registry / auto-detect /
per-lens model routing / `--thorough`. Make ONE change to `see`'s default prompt: (1) a light
self-adaptive clause (identify type → emphasise the detail that matters for it); (2) a strong
anti-fabrication clause (`[unsure]` over guessing; do not invent elements; report only what is
confidently legible); (3) reframe `see` output as a **gestalt/structure** read — for exact
text/values the caller verifies (or uses native vision). Add `--as LENS` only if ≥2 real
callers ever force it. §3–10 below are retained as the explored-and-rejected alternative.

## 1. Problem

`see` reads an image with **one fixed prompt** (`bin/see:78` for the structured read,
`:75` for question mode). But "the important information" is not the same across image
kinds: an info-dense dashboard wants every metric/label/state captured; a painting wants
composition/palette/mood; an AI-generated image wants subject + *artifacts*; a social
screenshot wants author + post text + engagement. A single rubric under-serves all of
them — which is exactly the failure the `claude-instances` fidelity audit found: gemma4:26b
read "the shape, not the words," and even on the right model a generic prompt won't know
that a dashboard's *point* is its numbers while a painting's is its mood.

**Goals.** (1) Capture the right detail per context, by default. (2) Don't miss details.
(3) Don't make the human (or Claude) spell out "what to look for" on every call — adaptation
should come from context, not keystrokes. (4) Allow an explicit priority when genuinely
needed, without that becoming the normal path.

## 2. The core decision — where does the lens live?

"Separate capability in `see`" vs "built into Claude" is a **false dichotomy**: it conflates
two separable things.

- **Knowledge** — *what counts as important* for a dashboard vs a painting vs a tweet. (The rubric.)
- **Selection** — *which context applies* to this image, right now.

The "explicit every time" worry is about **selection**. The "cleaner" intuition for separate
is about **knowledge**. They need not share a home.

**Decision: knowledge in the tool as data; selection automatic.**

- **Knowledge → `see/lenses/*.toml`** (not Claude's head), because:
  1. **Reusable by every caller.** The better-file-browser extension calls `see --json`
     directly; the local collective (`docs/06`) has weak local models calling `see` under
     procedure. If the rubric lives only in Claude's prompt-crafting, those callers get
     nothing. The tool is the shared substrate.
  2. **Durable + improvable.** A lens is tuned once, versioned, diffed, regression-tested.
     Claude re-deriving "what matters in a dashboard" ad hoc each call is inconsistent,
     unauditable, and evaporates after the call.
  3. **Self-documenting.** `see lenses` lists them, exactly like `q intents`.
- **Selection → automatic**, three paths, only the last explicit:
  1. **Caller infers from task** (primary). Claude passes `--as dashboard` because it is
     *auditing a dashboard* — context from the work, not the user's keystrokes.
  2. **Auto-detect** (bare call). `see x.png` with no lens → one cheap classify → a lens.
  3. **`--as LENS`** explicit override — the escape hatch, not the default workflow.

So "built into Claude" is wrong *if* it means the rubric lives only in Claude (extension +
local models lose it). "Separate" does **not** force explicitness — the selection layer
removes it. The answer is a **shared capability**: durable rubric in the tool, selection by
Claude's judgment or auto-detect. Claude still contributes its context-awareness — it
*selects* among the tool's lenses rather than *inventing* the rubric each time.

## 3. Architecture

```
        see <image>  [--as LENS]  [--thorough]  [-m MODEL]
              │
   selection ─┤  1. --as LENS         explicit override (rare)
              │  2. caller-inferred   Claude passes --as from task context
              │  3. auto-detect       bare call → 1 classify call → lens
              ▼
   LENS (see/lenses/<name>.toml)  =  system_prompt + default model + detect hints
              │
   --thorough?┤ no → single parse  →  text out / --json {ok,text,model,lens,ms}
              │ yes → run N lenses → Claude merges (don't-miss-details mode)
```

The loader **mirrors the intent registry verbatim** (`bin/q`: `INTENT_DIR`,
`intent_exists`, `intent_sys` via `yq -p toml`). For lenses:

```bash
LENS_DIR="$DIR/see/lenses"
lens_exists() { [ -f "$LENS_DIR/$1.toml" ]; }
lens_sys()    { yq -p toml -r '.system_prompt // ""' "$LENS_DIR/$1.toml" 2>/dev/null; }
lens_model()  { yq -p toml -r '.model // ""'         "$LENS_DIR/$1.toml" 2>/dev/null; }
```

`bin/see:78` (the hardcoded structured-read string) becomes: *resolve lens → its
`system_prompt`*, with the current string moving to `see/lenses/general.toml` as the default.

## 4. The lens registry

Schema (extends the intent schema with `model` + `detect`):

```toml
name = "dashboard"
summary = "info-dense UI: capture every metric, label, axis, state"
model = "minicpm-v"                      # optional; else config VISION_MODEL
detect = "charts, tables, KPI tiles, dense numbers, legends"   # hint for auto-detect
system_prompt = '''...what-matters rubric for this context...'''
```

**Starter lenses (ship only ones with a named caller — see §9 risk):**

| lens | what matters | default model | real caller |
|---|---|---|---|
| `general` | type + verbatim text + layout + anomalies (today's default) | minicpm-v | bare `see` |
| `dashboard` | every metric/label/axis/legend/state, verbatim; panel structure | minicpm-v | dashboard audits |
| `ui-ux` | elements + their STATE (active/disabled/selected) + layout + UX flags | minicpm-v | UI PR review, the extension |
| `doc` | verbatim OCR + reading-order + tables; chart → ▲▼ trend + values | minicpm-v | the extension's file previews |
| `art` | subject + composition + palette + style/technique + mood | gemma4:26b | image critique (`imagine`) |
| `ai-gen` | subject + style + ARTIFACTS/anomalies (hands, gibberish text, warping) | gemma4:26b | `imagine` output triage |
| `alt` | one tight paragraph: what a person *perceives* (a11y/gestalt) | minicpm-v | quick captions |

Model routing encodes the fidelity finding: text-critical lenses → MiniCPM-V (verbatim win);
aesthetic/scene lenses → gemma4:26b (general reasoning). Per-call `-m` still overrides.

## 5. Selection detail

- **Caller-inferred (primary).** Claude/sub-agent passes `--as <lens>`. This is where the
  "VLM parses, Claude reasons" split pays off: Claude knows *why* it is looking, so it picks
  the lens; `see` does the parse. No user keystrokes; no extra model call.
- **Auto-detect (fallback for bare calls).** One classify call: a tiny prompt to the default
  vision model — "Which fits best: dashboard / ui-ux / doc / art / ai-gen / social / general?"
  → map to a lens. Cost: one extra short call, only when no `--as` is given. `detect` hints
  in each lens seed the classifier's option list.
- **`--as` override.** Explicit, for when both auto-paths are wrong.

## 6. Don't-miss-details mode

`see x.png --thorough` runs 2–3 complementary lenses (e.g. `doc` for text + `ui-ux` for
structure + `art`/`alt` for composition) and returns all parses; Claude merges. Trades
latency for coverage; for the high-stakes "read everything" case. Single-lens stays default.

## 7. Implementation plan (slices, each shippable + testable)

1. **Registry + `--as` + `general` lens.** Add the `lens_*` loader to `bin/see` (copy the
   `intent_*` pattern). Move `bin/see:78`'s string into `see/lenses/general.toml`. Add
   `--as LENS`, `see lenses` (list, mirror `q intents`), and `lens` in `--json` output.
   *No behavior change with no `--as`* (general == today). ~40 lines + 1 toml.
2. **3–4 real lenses.** `dashboard`, `ui-ux`, `doc`, `ai-gen` — each with a named caller.
   Per-lens `model` routing.
3. **Auto-detect.** The classify call on bare invocations; `--no-detect` to force `general`.
4. **`--thorough`.** Multi-lens fan + labelled concatenation for Claude to merge.

## 8. Validation plan

- **Per-lens golden set.** For each lens, 2–3 images with a written "must-capture" list
  (extend `/tmp/mk_ocr.py`'s ground-truth method; reuse the `claude-instances` 4-image set,
  which already has native ground truth). Pass = the lens surfaces every must-capture item.
- **Don't-miss-details check.** The `dashboard` lens on a real dashboard must enumerate *all*
  KPI tiles, not a sample. Score = captured / total, target ≥ 0.9; log misses.
- **Auto-detect accuracy.** Label ~20 images by true type; measure classify hit-rate; a wrong
  lens must degrade gracefully (still produces a usable general read).
- **Regression.** `see x.png` (no flags) output must equal today's general read byte-for-byte
  (the `general` lens is the same string) — guards against accidental behavior change.
- **Caller-path test.** A sub-agent given only "audit this dashboard image" should call
  `see --as dashboard` *without being told the flag* — verifies selection comes from context.

## 9. Sanity checks & risks

- **Over-abstraction (atone: speculative-abstractions).** Ship a lens only when a caller
  exists *today*. `general` + `ui-ux` + `dashboard` + `doc` have callers now; `social` does
  not — do **not** pre-build it. Lenses graduate from real use, like intents did.
- **The crutch test.** If, in practice, humans end up typing `--as` on most calls, the
  selection layer has failed — that is the metric to watch, not lens count. Caller-inferred +
  auto-detect must carry ≥ ~90% of calls or the design is not meeting goal (3).
- **Latency.** Auto-detect adds one call on bare invocations. Mitigations: `--as` (Claude's
  path) skips it; keep the classify prompt tiny; cache classify by image hash within a run.
- **Classify-error cascade.** A wrong lens could hide detail. Mitigation: lenses are supersets
  (every lens still reports verbatim text first); `--thorough` for high stakes.
- **Model hang.** MiniCPM-V timed out on one high-res image (img4, >240s). `see`'s 180s
  timeout errors cleanly, but `--thorough` multiplies exposure — cap concurrency, keep the
  per-call timeout, surface partial results.
- **Lens drift / maintenance.** Rubrics rot as models improve. Each lens carries `updated`;
  the golden set is the regression guard.
- **Grounding (atone: structural-claim).** Every claim about the loader here is from
  `bin/q`/`bin/see` read this session, not assumed; the `lens_*` snippet is the literal
  `intent_*` pattern.

## 10. Open questions (for the skeptic + user)

1. Is the registry worth it, or is a single richer self-adaptive prompt ("identify the type,
   then report type-appropriate detail") good enough — saving all machinery? (Tradeoff:
   one-call simplicity + weaker-model self-adaptation vs durable tunable rubrics.)
2. Auto-detect as a separate classify call, or fold "identify type" into the read prompt
   (one call, model self-routes)? Latency vs accuracy.
3. Is per-lens model routing premature, given one model (MiniCPM-V) may suffice once tuned?
4. Does `--thorough` earn its complexity, or is "Claude calls `see` twice with two lenses"
   enough without a dedicated mode?
