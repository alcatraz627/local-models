# lm CLI fixes: summary

Branch `lm-ergonomics` in `/Users/alcatraz627/Code/local-models-lm`. Evidence with before and after output: `/Users/alcatraz627/Code/local-models-lm/.claude/output/lm-fixes-evidence.md`.
`scripts/verify.sh`: 38 passed, 3 failed (the known guard-model-tier block path, warm-morning missing, warm-evening-off not loaded). No new failures.

| Item | Status | Note |
|---|---|---|
| D1 timeline speed | fixed | 39 s down to 0.06 s for `lm timeline 20` on the real 12 MB histories |
| D2 unknown flags | fixed | q, see, imagine, review, lm gemini exit 2 with one message; `--` escapes |
| D3 missing flag value | fixed | `need_arg` in all five parsers; `imagine critique` usage check |
| D4 status hides big tier | fixed | all rows shown, with tier labels |
| D5 review show -1 | fixed | counts review entries only |
| D6 model not shown | fixed | q stats line and `q history` show the model; `cold` marker |
| D7 failed see reads | fixed | error rows, marks in history and timeline; old rows recognised by their text |
| D8 gemini failure row | fixed | reason kept, real ms, `show` prints the step-log path. Side bug found, not fixed: the timeout auto-retry reuses `--session-id` for a new session |
| D9 UTC times | fixed | local `MM-DD HH:MM` in every history view and timeline |
| D10 doctor | fixed | yq, all tiers, vision, embed, MLX cache, PATH target check, gemini key, `--json` |
| D11 errors to stdout | fixed | lm, warm, imagine lines moved to stderr |
| D12 verb hints | fixed | `lm help <tool>` routes, did-you-mean, full fallback, `lm rag` row |
| D13 help text | fixed | all eight rows; q intent list generated from `intents/` |
| D14 --json | fixed | history verbs everywhere with `n`, plus doctor, timeline, `warm status` |
| D15 fallback model | fixed (read-verified) | path needs an unavailable gemini, not run |
| D16 imagine critique | fixed | ensure, host, keep_alive, logged as a critique row; server-down branch read only |
| D17 watch abc | fixed | numeric check, exit 2 |
| D18 sizes and tiers | fixed | decimal sizes as ollama prints them; sweep and vision labels |
| D19 warm status | fixed | "nothing resident" line |
| D20 NO_COLOR | fixed | stderr palette follows stderr; python paths check NO_COLOR |
| D21 gemini-direct | already fixed | re-checked, nothing still true |
| D22 stale docs | fixed | STATE.md and the lm per-command help line |
| D23 overview alignment | fixed | `...` and a wider pad |
| Idea 1 timeline `tool#N`, `--errors`, `--tool`, `--json`, `lm last` | built | |
| Idea 2 q `--json` intent, entry, cold_load | built | |
| Idea 3, 4 | skipped | per brief |
| Idea 5 did-you-mean | built | lm verbs, q intents, timeline tools, help jobs |
| Idea 6 `lm --version` | built | prints `lm 1.1` |
| Idea 7 tok/s from eval_duration | built | |
| Idea 8 shared arg helpers | built | in `bin/_lib.sh` |
| Idea 9 status lease TTL and tiers | built | |
| Idea 10 exit-code table | built | `docs/CAPABILITIES.md`; warm, imagine, lm moved onto it. review and ui-verify keep their own 1/3 codes, which the table documents |
