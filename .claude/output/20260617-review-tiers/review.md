# Skeptical review — model size tiers + token-stats line

Scope: uncommitted changes in `/Users/alcatraz627/Code/local-models` — `config.sh`
(BIG/CODE_MODEL), `bin/q` (`resolve_tier`, `--big`/`--code`/`--no-stats`, token capture),
`bin/lm` (tier tagging in `lm models`). Read + exercised the jq/python/bash paths on
`/tmp` copies; no model calls made. `bash -n` clean on all three scripts.

Verdict: **solid, ship-ready.** No correctness bugs in the default config. Findings are
mostly edge-case / robustness / cosmetic. The two highest items are documentation gaps
about behaviors that are *intentional but undocumented*, not defects.

## Ranked findings

| # | Conf | File:line | Check | What's suspect | How to verify |
|---|------|-----------|-------|----------------|---------------|
| 1 | Med | `bin/lm:124-127` | 4 (tier-tag) | **Prefix-shadowing if a tier alias is a prefix of another.** With the *default* config there is no collision (verified). But the tags use `startswith` with first-match-wins ordering small→big→code. If a user ever sets `WARM_MODEL=gemma4` (a bare prefix), `gemma4:26b` and `gemma4:31b` get mis-tagged "small" and big never matches. Not a bug today; a latent footgun for non-default configs. Document that aliases must be full model names, or switch the match to exact-equality (`$n == $sm`) since the alias resolves to a concrete model anyway. | Ran jq with `sm=gemma4`: `gemma4:26b`/`:31b` both tagged "small". With default `sm=gemma4-e4b-warm`: correct, `gemma4-e4b-it-qat` does NOT match (good). |
| 2 | Med | `bin/q:106-114` | 1 (resolve_tier) | **Literal/alias keyword collision is silent & undocumented.** If someone has a model literally named `big`/`code`/`small`, `-m big` resolves to `$BIG_MODEL`, not their model — there is no escape hatch. Acceptable (these are unlikely Ollama names) but the comment at :106-107 only documents the *passthrough* direction, not the *shadowing* direction. One sentence would close it. | `resolve_tier big` → `gemma4:26b`; no way to force the literal. |
| 3 | Low | `bin/q:49,52` / `docs/q-spec.md` | 3 (stats) / docs | **Machine-mode `--no-stats` is a silent no-op.** `--no-stats` only affects the text-mode stderr line; in `--json`/`--stream-json` `tokens_in/out` are emitted unconditionally and `STATS` is ignored. Correct & arguably desirable (machine fields are cheap), but help text says "hide the token-spend line" without noting it's text-mode only — a machine consumer might expect `--no-stats` to drop the fields. Help string already hints "text mode" in q-spec but not in `q -h`. Minor doc tightening. | Read `bin/q:400` — stats branch is inside `if mode == "text"` + `isatty`; json/stream branches (406,409) add fields unconditionally. |
| 4 | Low | `bin/q:401` | 2 (tok/s) | **tok/s uses wall-clock `ms`, which includes model load time on a cold tier.** For `--big`/`--code` (load-on-demand), the first call's "N tok/s" will read artificially low because `t0` starts before the load. Not wrong (it IS the observed rate) but potentially confusing on a cold big-model call. Cosmetic; worth a mental note, not a fix. Div-by-zero is correctly guarded (`if ms else 0`, verified). | `python3 -c 'ms=0;...if ms else 0'` → 0, no crash. |
| 5 | Low | `bin/q:364-366` | 2 (token capture) | **`tok_in/tok_out` stay 0 if the stream errors before the done chunk, or if Ollama omits the counts.** Both are acceptable degradations (0 renders as "0 in / 0 out", no crash) and the error paths `emit_err` before reaching the stats line anyway. `obj.get("done")` is the right gate — non-final chunks carry `done:false` (falsy, verified), only the final `done:true` chunk has `prompt_eval_count`/`eval_count`. No bug. | Replayed both chunk shapes through `obj.get("done")` truthiness: `False`→skip, `True`→captures 12/34. |

## Clean checks (verified, no issue)

1. **resolve_tier resolution + quoting** (`bin/q:108-115,135-136,145`): `-m big`/`--big`/
   `-m <literal>`/`-m small` all resolve correctly. `$(resolve_tier "$2")` preserves
   multi-word values (`-m "model with spaces"` → intact) — the assignment-from-command-
   substitution is not word-split. `echo` always returns rc 0, so no `set -e` abort.

2. **`MODEL` default is consistent** (`bin/q:117`): `MODEL="$WARM_MODEL"` (not via
   `resolve_tier`) equals `resolve_tier small` — help text "default: small" is accurate.

3. **Stats purity** (`bin/q:397-409`): the dim stderr line is gated on BOTH `mode == "text"`
   AND `sys.stderr.isatty()` — cannot leak to stdout, cannot leak to a piped stderr.
   `--no-stats` mutes it. Machine modes only *add* `tokens_in`/`tokens_out` keys to the
   existing done/json object — backward-compatible, no api_version bump needed (additive).

4. **done-frame backward compat** (`bin/q:404-409`): stream `done` frame keeps `t/model/ms/
   truncated`, adds two keys. Existing consumers reading by key are unaffected.

5. **div-by-zero / null guards**: tok/s `if ms else 0` (verified). lm size `(.size // 0)`
   guards null size → `0GB`, no crash (verified with `{"name":"nosize"}`).

6. **`set -eo pipefail` safety** (`bin/q:19`, `bin/lm`): the new command substitutions
   (`resolve_tier`, the tier jq) cannot abort the script — `echo`/jq-with-valid-input
   return 0. The `lm` jq is preceded by a `jq -e .` validation gate (`bin/lm:110`) that
   already protects the pipe from a 500-body, so the new tier expression rides on
   already-validated JSON.

7. **lm tier tagging on default config** (`bin/lm:121-128`): exercised against a 7-model
   fixture incl. `gemma4-e4b-warm` vs `gemma4-e4b-it-qat` and `qwen3.6:35b-a3b` vs
   `qwen2.5-coder:3b` — every row tagged correctly, no double-tags, `gemma4:31b` (dropped)
   correctly untagged. Padding `[0:28]`/`[0:7]` truncates over-long names/sizes without
   error (truncation is intentional column-fit, not a bug).

## Comment quality (per ~/.claude/rules/comments.md)

Good overall — comments are human-first, explain WHY, no `[claude@]` tags, no plan refs.
Specific notes:

- `bin/q:106-107` (resolve_tier): clear, but only documents passthrough, not the
  alias-shadows-literal direction (see finding #2). Consider adding the shadowing caveat.
- `config.sh:7-13`: the tier block is genuinely useful (explains the MoE-vs-dense
  bandwidth rationale + points to research). The mid-comment line-wrap (`(chosen for fast
  MoE shapes, not / dense — ...)` spanning the WARM_MODEL comment) reads slightly awkwardly
  but is accurate. Minor.
- `bin/q:355` ("filled from the final done chunk's eval counts") and `:364` ("final chunk
  carries the token tallies") — accurate, concise, WHY-focused. Good.
- `bin/q:399` ("like the --think trace, TTY-only, muteable") — good cross-reference to the
  sibling pattern.
