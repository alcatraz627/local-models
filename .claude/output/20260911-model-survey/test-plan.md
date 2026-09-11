# Model test plan: scenarios, acceptance criteria, staging

2026-09-11. Turns the survey shortlist into runnable tests. Every candidate is
probe-gated before trust; a candidate that only looks better on a spec sheet fails.
Budget policy (CLAUDE.md hard rule 3) governs pulls: baseline ~105 GB, target <150 GB.

## Gates by dimension

- Text / code / judgement / orchestration: the 9-item judgment probe (`bin/probe <model>`,
  scored markdown to `probe/runs/`). It runs at temperature 0, so `passk-reliability`
  cannot fail there; I add a supplementary reliability check at temperature 0.7 (5 cold
  runs, count distinct answers) for any text candidate.
- Vision / UI: hand-labeled UI-discrimination fixtures (built below) plus the OCR verbatim
  fixture at `probe/fixtures/ocr-fixture.png`, scored against my ground-truth labels.
- Throughput (the sweep role): tokens/sec on a fixed prompt versus the incumbent, measured
  live on Ollama 0.33.3.

## Ground-truth fixtures I build for the vision rounds

Real UI screenshots the `see` store already keeps become labeled fixtures. For each, I
record the ground-truth facts by reading the image myself, then score each model on how
many it gets right and whether it hallucinates any element that is not present.

- FX-UI-1: a kanban board screenshot. Labels: column count and names, card counts per
  column, which card or control is visibly active, dark/light.
- FX-UI-2: a settings screen. Labels: which nav item is selected, toggle states, section
  order.
- FX-OCR: `probe/fixtures/ocr-fixture.png`. Labels: the exact strings present.

A model earns a vision-role win only by matching ground-truth facts at least as well as
the incumbent with zero hallucinated elements (the measured trust boundary: local vision
is a verifier, not a critic).

## Scenarios and acceptance criteria per candidate

### Stage 0: gemma4:26b re-probe (judge seat), free, resident
- Scenario: run the full 9-item judgment probe on the already-resident model.
- Acceptance: it clears the judge-relevant items (abstention, abstention-hard,
  tool-decision, scope-trap, multiturn-if) as cleanly as the code incumbent did. If yes,
  the judge seat costs zero new model. If no, a dedicated judge is justified.

### Stage 1a: MiniCPM-V 4.6 (vision default), Ollama, ~1.6 GB
- Scenario: run FX-UI-1, FX-UI-2, FX-OCR head-to-head against the incumbent minicpm-v.
- Acceptance: matches or beats incumbent OCR verbatim accuracy and general-read facts at a
  smaller footprint, zero hallucinated elements. A tie at lower memory still wins (strict
  efficiency upgrade).

### Stage 1b: Granite 4.0 H Tiny (sweep/grunt), Ollama, ~3.5 GB
- Scenario: throughput on a fixed 200-token summarization prompt versus gemma4-e4b, plus
  the instruction-following and structured-output probe items (multiturn-if, tool-decision,
  scope-trap).
- Acceptance: faster tokens/sec than gemma4-e4b AND holds the instruction-following items.
  Speed without reliable structured output does not qualify for the sweep lane.

### Stage 2: Qwen3-VL-8B (UI discrimination), MLX-VLM, ~6 GB + deps
- Scenario: install mlx-vlm; run FX-UI-1 and FX-UI-2 standalone; compare against the
  current `see --ui` target gemma4:26b on the same labels.
- Acceptance: beats gemma4:26b on UI-structure facts (selected item, states, proportions)
  with no hallucinated elements. This is the highest-value target; a clear win justifies
  the new MLX-VLM runtime dependency.

### Stage 3: GLM-4.7-Flash (reasoning/judge/orchestration), Ollama, ~19 GB, beyond doctrine
- Scenario: full 9-item judgment probe plus the temperature-0.7 reliability check.
- Acceptance: clears the probe at least as well as the incumbents. Because this is beyond
  the doctrine, a pass is evidence to bring to the owner for review, not an auto-swap.

### Deferred: qwen3.6:35b-a3b-coding
- Gated on the unrun D11 decision and would push the footprint toward the transient band.
  Run only if Stages 0-3 leave clear budget and time; otherwise skip with a note.

## Order and footprint math

0 (free) → 1a (+1.6) → 1b (+3.5) → 2 (+~8) → 3 (+19). Peak ~137 GB, under the 150 target.
Losers are deleted after probing (pull-probe-prune). If a tag fails to resolve or a
runtime will not install, the phase is skipped with a recorded reason and the plan
continues.

## Outputs

One case report per stage in this directory (`caseN-<slug>.md`), then a unified verdict
in `verdict.md`.
