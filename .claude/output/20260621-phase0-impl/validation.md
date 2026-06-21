# Phase 0 implementation — validation criteria

Checked after EACH task; all re-checked once the batch is done. Four dimensions per task:
**behaviour** (user-observable correctness) · **runtime** (actually executed + observed, not just
parses) · **code** (sound, lean, convention-following) · **intent** (matches the design goal).

Marks: `[ ]` pending · `[x]` passed · `[!]` failed/needs-fix.

---

## P0-1 — Scaffold intents/ registry ✅
- [x] **behaviour:** `intents/` exists; `intents/README.md` states the schema; hand-authoring is "drop a file"
- [x] **runtime:** all 8 sample files parse with `yq -p toml` (the generation step round-tripped them)
- [x] **code:** format matches `docs/07 §6` (name, summary, needs_ctx, system_prompt); default_tier/ctx_glob documented-as-reserved only (not wired)
- [x] **intent:** config-as-data foundation in place; the keystone for intent graduation

## P0-2 — Extract the 8 intents to registry files (EXACT prompts) ✅
- [x] **behaviour:** all 8 intents present (`ask cmd title commit summarize explain-code describe-data qa`)
- [x] **runtime:** ALL 8 `yq -p toml -r .system_prompt` outputs **byte-identical** to the original `bin/q` SYS (extracted from source, machine-compared — `ALL 8 BYTE-IDENTICAL ✓`)
- [x] **code:** `needs_ctx=true` exactly for summarize/describe-data/explain-code/qa; false for ask/cmd/title/commit
- [x] **intent:** zero behaviour change — prompts relocated, not edited

## P0-3 — Rewire bin/q to load from the registry ✅
- [x] **behaviour:** ctx-guard fires `ctx_required` (exit 2) for all 4 doc-intents *before* server contact; `ask`/unknown-token pass through; live `q title`→"Classic Pangram Example", `q describe-data`→correct schema. (`--raw`/bare-`q` are unchanged code paths — re-confirmed in FINAL sweep)
- [x] **runtime:** exercised live (title + describe-data answered correctly); guards exit 2 with bogus host (short-circuit proven); **latency: yq ~12ms/call, no perceptible regression** vs warm first-token
- [x] **code:** all THREE sites (case-SYS, positional recognizer, ctx-guard) now derive from the registry — single source of truth; `bash -n` OK (shellcheck not installed locally); 2 yq reads/call, no loops
- [x] **intent:** intents are data — a new file is immediately usable (proven); no `bin/q` edit to add one

## P0-4 — `q intents` discoverability ✅
- [x] **behaviour:** `q intents` lists all 8 with summary + a `*` marker for needs_ctx
- [x] **runtime:** ran it (saw 8); dropped a throwaway `tldr.toml` → auto-appeared → removed
- [x] **code:** globs the registry (no hardcoded list); reuses `_lib` `_sec`/`_opt`; no new deps
- [x] **intent:** the growing intent set is discoverable

## P0-5 — OLLAMA_USE_MLX=1 in lm-serve → ⊘ NOT DONE (correctly — ground truth)
- [x] **behaviour:** flag **not added.** `bin/lm-serve` carries a tested human NOTE: `OLLAMA_USE_MLX` is *absent from Ollama 0.30.6's config dump → never activates*. Adding it = cargo-cult.
- [x] **runtime:** the NOTE is prior runtime evidence (server config dump checked). Re-adding an inert var changes nothing measurable.
- [x] **code:** respected the human NOTE (didn't silently override); no cargo-cult config introduced
- [!] **intent:** the MLX *lever is real but NOT a flag on this Ollama* — it needs a build that actually exposes it, or `mlx_lm.server`. My earlier "just set the flag" advice was WRONG for 0.30.6. docs/05 + docs/07 corrected; Task #22 reframed.

---

## FINAL — all-done sweep ✅
- [x] re-ran runtime checks: byte-identity (8/8), guards (4/4 exit 2), live intents (title/describe-data/ask/cmd), --json valid, -c continuation ("ok"→"ko")
- [x] behaviour spot-check: `ask`→Four · `cmd`→pwd · `--json`→valid object · `-c`→ko · `history`→numbered · `q intents`→8
- [x] no snappy-path regression (yq +~12ms/call vs warm first-token; --json reported ms=338)
- [x] `git diff` reviewed: `bin/q` +39/−28 (additive; SYS case removed); `intents/` new; minimal
- [x] validation doc fully resolved; P0-5 resolved by respecting ground truth (not deferred)
