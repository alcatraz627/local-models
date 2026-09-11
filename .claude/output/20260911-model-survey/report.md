# Local-model survey and swap-audit, 2026-09-11

Synthesis of three research passes (text-tiers.md, vision-ui.md, imagegen.md) against
the suite's current `config.sh` tiers. Scored on the goal's axes: performance, memory,
disk, scale of work, and which candidate complements a real Claude gap. Every figure
below is secondary-source until an `ollama pull` / `ollama show` (or an MLX checkpoint
fetch) confirms it, and no candidate is trusted until it clears its named gate.

## The doctrine lens (the value bar this survey is scored against)

Owner ruling 2026-08-30: local lanes exist to complement where cloud Claude is limited,
the two named use cases being vision and sweep. Owner refinement 2026-09-11: run
the survey independent of the doctrine, but treat it as a guidestone. Inside it the
value bar is low and a proven use case need not be re-justified. Beyond it a new promise
must clear a much higher bar and earn its place through testing and review before the
doctrine moves.

- Inside the doctrine (low bar): vision reading, UI-structure discrimination (the
  `/ui` bundle), and the sweep/grunt-work lane (`lm fleet`).
- Beyond the doctrine (high bar, survey-only until tested and reviewed): general
  reasoning, judgement seat, orchestration/code, image generation.

## Machine and runtime facts that bound everything

- M5 Pro, 64 GB unified, ~307 GB/s bandwidth. Bandwidth-bound, so MoE (low active
  params) beats dense at equal quality. Resident budget target ~40 GB per big model so a
  ~6 GB warm companion still fits.
- Disk is NOT the constraint (135 GB free). Memory, bandwidth, and runtime support are.
- Ollama is now 0.33.3 (the repo's measured tok/s came from 0.30.10), so every
  incumbent throughput number is stale and must be re-measured before it anchors a
  comparison.

## The three gates (how promise becomes trust)

| Dimension | Gate | Note |
|---|---|---|
| text / code / judgement / orchestration | `probe/items.toml` (9 judgment items) | `passk-reliability` cannot fail at temperature 0, so it is not real evidence; the gate is effectively 8 items |
| vision / UI | `vis-battery` + the UI ground-truth fixtures (the dashboard structural-read test) | the test that separated minicpm-v from gemma4:26b is the one to re-run |
| image-gen | `asset-verify` / `vis-compare` against a reference | quality-first; speed is explicitly not scored |

## Per-tier swap audit

| config.sh tier | Incumbent | Best newer candidate | Beats on | Doctrine | Verdict |
|---|---|---|---|---|---|
| `VISION_MODEL` (`see`) | minicpm-v, 5.5 GB | MiniCPM-V 4.6 (~1.6 GB, Ollama-native) | memory (−4 GB), throughput (2.4x its own baseline), same OCR lineage | inside (low bar) | Pull and probe. Drop-in, no new runtime, strict efficiency upgrade. Verify OCR parity on the fidelity fixtures first. |
| `UI_VISION_MODEL` (`see --ui`) | gemma4:26b, 17 GB | Qwen3-VL-8B-Instruct via MLX-VLM (~6 GB q4) | UI grounding (94.4% ScreenSpot; incumbent has no UI-grounding score, won the role by default), memory (−11 GB), scale (256K ctx) | inside (low bar) | Highest-value pull in the survey. Attacks the suite's weakest, highest-value spot. Cost: a new MLX-VLM runtime dependency, because Ollama's Qwen3-VL path is broken on Apple Silicon (#16264 OPEN, verified today). |
| sweep / grunt (`lm fleet`; no dedicated tier today) | gemma4-e4b as the general small | Granite 4.0 H Tiny (7B/1B-active MoE, ~3.5 GB) | scale/throughput (1B active is the lowest surveyed), memory (−2.5 GB), long-input RAM (hybrid Mamba-2, >70% reduction claimed) | inside (low bar) | Probe as a sweep lane. Watch the "preview" stability flag; IBM's own 4.1/4.2 line dropped hybrid-MoE, so confirm it is still maintained. |
| `WARM_MODEL` (small) | gemma4-e4b, 6.1 GB | Granite 4.0 H Tiny (as above) | memory, throughput | inside (sweep-adjacent) | Only if Granite probes clean on general prose; otherwise keep gemma4-e4b (warm, proven, zero migration). |
| `BIG_MODEL` (reasoning) | gemma4:26b (MoE 3.8B active), 17 GB | GLM-4.7-Flash (30B/3B-active MoE, 19 GB q4) | reasoning (SWE-bench 59.2, τ²-Bench 79.5, vendor-reported) at ~same footprint | beyond (high bar) | Survey-only. Plausible upgrade, but general reasoning is parked. Pull-and-probe is allowed; adopting it needs testing plus your review before the doctrine moves. |
| `CODE_MODEL` (code/tool) | qwen3.6:35b-a3b (MoE), 23 GB, cleared probe 9/9 | qwen3.6:35b-a3b-coding (same arch, coding tune, 23 GB) | possibly tool-calling; zero architecture risk | beyond (high bar); also gated on the unrun D11 five-dispatch decision | Cheapest experiment, but the code lane is already gated on D11. Re-run the 9-item probe on the sibling; do not treat a coding tune as an improvement without it. |
| judge seat (no dedicated tier) | none; gemma4:26b reused ad hoc | gemma4:26b re-probe (zero new cost), then GLM-4.7-Flash | zero disk/bandwidth if gemma4:26b calibrates | beyond (high bar) | Do the free thing first: probe the already-resident gemma4:26b against the judgment gate before pulling any dedicated judge. |
| `IMAGINE_MODEL` | qwen (Qwen-Image, mflux) | none actionable today | — | beyond / frozen | No change. Every model that plausibly beats Qwen-Image on in-image text lacks a confirmed Apple-Silicon runtime. Watch-later: Qwen-Image-2512 via `mlx-gen` (an integration change, not config-only). |

## What to actually do, in order

1. Free, now, inside doctrine: re-probe the already-resident gemma4:26b against
   the judgment gate. Zero pull, settles the judge-seat question.
2. Inside doctrine, high value: pull MiniCPM-V 4.6 (Ollama, low-risk) and pull
   Qwen3-VL-8B through MLX-VLM (new runtime, but it targets the UI-discrimination
   gap the suite named as its weakest). Probe both against the UI ground-truth fixtures.
   These are the survey's strongest, doctrine-aligned wins.
3. Inside doctrine, sweep: probe Granite 4.0 H Tiny as a grunt/sweep lane.
4. Beyond doctrine, survey-only: GLM-4.7-Flash is the one general-purpose
   candidate worth a probe run, because it spans reasoning plus judge plus orchestration
   at a 17-GB-class footprint. Treat a passing probe as evidence to bring back for your
   review, not as license to swap `BIG_MODEL`.
5. No action: image-gen. Qwen-Image stays the default.

## Carried caveats

- Ollama Qwen3-VL is blocked on Apple Silicon (#16264 OPEN, verified 2026-09-11); MLX-VLM
  is the clean path and a genuine new dependency to weigh.
- All parameter counts, disk sizes, and benchmark scores are secondary-source; the
  text-tiers pass found Ollama library pages internally inconsistent. Confirm with
  `ollama pull` plus `ollama show` before committing budget.
- Excluded on memory/bandwidth grounds (documented, not recommended): Mistral Small 4
  (119B), Qwen3.8-Flash-Next (125B), MiniMax M2 (230B), Kimi K2.6 (1T), DeepSeek V4-Flash
  (284B); Llama 3.3 70B fits only as an occasional stretch that consumes the whole budget.
  Meta shipped no new open Llama since April 2025.

## Source reports (same directory)

- `text-tiers.md`: 5 role sections, GLM-4.7-Flash / Granite / Qwen3.8 / qwen3.6-coding.
- `vision-ui.md`: Qwen3-VL-8B / MiniCPM-V 4.6 / Moondream 3 / InternVL3.5; #16264 verified.
- `imagegen.md`: no swap warranted; Qwen-Image-2512 watch-later.
