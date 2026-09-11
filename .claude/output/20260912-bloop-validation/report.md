# Adversarial validation report: local-model integration wave

2026-09-12. One opus adversarial seat attacked the session's build (mem-guard.py, the
`see --mlx` backend, the sweep tier, and the survey verdict's premises), executing each to
prove failures. Verdict: ISSUES-FOUND. All findings triaged and dispositioned below.

## What held up under attack
- `see --mlx` happy path works and records `model:"mlx:…Qwen3-VL-8B-Instruct-4bit"`; the
  `--ocr`/`--mlx` and `diff`/`--mlx` guards both fire (exit 2, exercised).
- `resolve_tier sweep` maps to `granite4:tiny-h` (exercised); `lm fleet -m sweep` runs.
- Plain `see` on the new `minicpm-v4.6` default works. vis-battery 53/53.
- Attack B refuted by execution: model memory lives in the `llama-server` runner (killable),
  not in `ollama serve`; the kill-set matches it and `kill_one` frees it.
- The survey verdict is well-calibrated: it does NOT swap on the Qwen3-VL 100% tie (correctly
  HOLDs); the applied vision swap rests on a discriminating result (minicpm-v4.6 4.5/5 vs the
  incumbent 2/5 on the incumbent's documented weak spot), not the tie.

## Findings and dispositions

| # | Sev | Finding | Disposition |
|---|---|---|---|
| 1 | MAJOR | mem-guard never auto-started by the risk-creating path (`see --mlx`); protection depended on a human pre-launching it | FIXED: `see --mlx` preflight arms the guard (pgrep-checked) and warns on a big-model co-load. Verified: a fresh guard (pid 12022, pressure trigger) launches on the mlx path |
| 2 | MAJOR | memory metric (free+inactive pages) overstates reclaimable memory and lags jetsam under macOS compression | FIXED: primary trigger is now the kernel pressure level (`kern.memorystatus_vm_pressure_level` at warn or above); the free-page floor is a coarse secondary. `--once` shows pressure plus swap |
| 3 | MAJOR/MINOR | NEVER regex false-excludes a real model process by launch-path substring (e.g. a venv under `~/Code/Claude`) | FIXED: NEVER now matches process IDENTITY (token basenames), not the full path. Mutation-tested 5/5 (model-in-/Claude-path killable; real Claude spared) |
| 4 | MINOR | dead KILLSET branches (`ollama.*runn`, `ollama_llama` matched nothing); only `llama-server` is load-bearing | FIXED: trimmed to `mlx_vlm`, `mlx.launch`, `mlx_lm`, `llama-server` with a note to add ollama's runner name if it changes |
| 5 | MINOR | daemon single-instance lock trusted a bare pidfile pid (defeated by pid reuse); an unkillable offender could tight-loop | FIXED: single-instance and see's preflight both use `pgrep -f scripts/mem-guard.py`; a survivor is skipped for 30s. The pid-reuse bug was caught live during re-test |
| 6 | MINOR | `see --mlx --ui --json` silently drops the schema contract (FMT not passed to mlx) | FIXED: warns that the mlx backend does not enforce the schema and `.data` is best-effort |
| 7 | NIT | no early preflight on the mlx repo id (`-m mlx:does/not-exist` fails late) | DEFERRED: low value; a missing image still errors early |
| 8 | NIT/overclaim | verdict credited the guard for what the sequential discipline achieved (guard never fired) | FIXED: `verdict.md` now states the sequential discipline kept runs clean; the guard is an unproven backstop |

## Re-test after fixes
- vis-battery 53/53, verify.sh 38/0.
- `see --mlx` correct (kanban 5/5), guard armed on the mlx path (new start record).
- NEVER identity fix mutation-tested 5/5.

## Method note
The re-test found a real bug the first fix introduced: a stale pidfile whose pid had been
reused made both `see` and the daemon believe a guard was running when none was, so no guard
launched. The pgrep-based fix resolved it. This is exactly why the fix round is re-tested by
execution, not inspection.

Source findings: adversarial seat transcript (opus), repro artifacts at /tmp/killset_test.py
and /tmp/kill_test.py.
