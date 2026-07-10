# Visual-compare Phase A — adversarial validation + dispositions

<!-- sessions: vis-compare-A@2026-07-10 -->

A sonnet validation sub-agent reviewed Phase A (branch `feat/vis-compare`)
adversarially. Verdict: **ISSUES-FOUND**. Every finding was grounded in a run or a
file:line. The sub-agent's report-file write was blocked by a gcc guard (sub-agents
can't write report files), so the parent session (this file) persists it.

## What the validation confirmed CLEAN (tried to break, could not)

CIE76 sRGB→Lab→ΔE math, dHash/aHash/Hamming logic, the comparability-gate math (F5),
slice-rerun delta correctness across chained reruns, the 14/14 battery, non-diff
`see` paths, §2 settled decisions (no numpy/opencv/gemini), bash 3.2 compatibility,
contact-sheet generation, and a live end-to-end `see diff --json` run.

## Findings and dispositions

| # | Sev | Finding | Disposition |
|---|-----|---------|-------------|
| 1 | major | **Fabrication guard hole**: a JPEG-85 re-encode (perceptually identical) gave `palette_delta_avg 28.7` with 3 "different" pairs while E4/E5 stayed zero. Greedy nearest-ΔE palette match, unweighted average, no ceiling → low-population tail colors fabricate divergence. | **FIXED** — E3 average is now population-weighted by A-side area share (`lib/vis-compare.py:e3_palette`); JPEG re-encode drops to 2.0, F2 hue still caught, F4 theme correctly low (that's E5's job). New battery guard **F3b** (JPEG re-encode → clean) would have caught it. |
| 2 | major | **L1 gated behind ollama**: `ollama_up \|\| emit_error` ran before the $0 extractor call, so a down server returned nothing — not even the model-independent pack. | **FIXED** — `bin/see`: for diff the gate is soft; L1 runs, VLM is skipped, `vlm_unavailable` failure recorded. Verified: dead-port run exits 0 with a full pack. |
| 3 | major | **VLM failure discarded the pack**: a model timeout after successful extraction called `emit_error` (exit) before the artifact/journal write. | **FIXED** — same soft-failure path; a diff VLM error notes + continues, pack + evidence.json still written. |
| 4 | major | **`skipped_extractors` lied**: E1 marked skipped while `text_diff` was populated (asymmetric OCR + iconlike modality). | **FIXED** — E1 is "skipped" iff `text_diff is None`, never when it's present. Verified consistent. |
| 5 | major | **E0 letterbox unbuilt**; `meta.normalized` reported A's own dims, not a shared size. | **PARTIAL/DOCUMENTED** — renamed to honest `dims_a`/`dims_b`/`letterboxed:false`; letterboxing deferred (docs/10 §9). Comparability gate mitigates the extreme case. |
| 6 | major | **E3 texty per-element fg/bg sampling unbuilt** (`element_samples`); only iconlike grid-mean path exists. | **DEFERRED/DOCUMENTED** — docs/10 §9. Phase-B/calibration item; hits U1 hardest. |
| 7 | major | **Telemetry partial**: no failure codes emitted, no retry, token counts discarded. | **PARTIAL** — now emits `vlm_unavailable` + `ocr_missing`, records the VLM seat; token counts + retry deferred (docs/10 §9). |
| — | minor | corrupt image → raw traceback | **FIXED** — clean JSON error, exit 12. |
| — | minor | literal `$0` in `see -h` | **FIXED** — reworded to "deterministic evidence pack". |
| — | minor | E1 numeric coords; §5.6 skipped-extractor hard-block moot; E2 unbuilt | **DOCUMENTED** — docs/10 §9. |

## Net

The four correctness bugs (#1-#4) that undermined Phase A's load-bearing claims
(the fabrication guard and the $0/model-independent contract) are **fixed and
guarded by new/existing battery checks**. The design-scope gaps (#5-#7 + minors)
are either honestly documented as deferred (docs/10 §9) or partially built. Battery
grew to 14/14. The fabrication guard now holds for perceptual identity, not just
byte identity — the class of input the original fixtures never exercised.
