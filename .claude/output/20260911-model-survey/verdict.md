# Local-model testing: unified verdict

2026-09-11. Five candidates run through their real gates on this machine, each with a case
report in this directory. This is the synthesis, the per-tier decision, and what changed.

## Bottom line

The wins are exactly where the complements-only doctrine says they should be: vision and
sweep. The one general-purpose candidate that looked strongest on paper (GLM-4.7-Flash)
failed the trust gate hardest. Nothing beyond the doctrine earned adoption.

## Decisions per config.sh tier

| Tier | Incumbent | Decision | Why |
|---|---|---|---|
| `VISION_MODEL` (`see`) | minicpm-v (5.5 GB) | SWAPPED to minicpm-v4.6 (1.6 GB), applied | Beats the old model on UI structure, hallucinates nothing, a third of the disk. Reversible; old model kept as fallback. |
| `UI_VISION_MODEL` (`see --ui`) | gemma4:26b (17 GB) | HOLD, with a path | Qwen3-VL-8B ties it perfectly at 6 GB, but needs MLX-VLM wired into `see` and harder fixtures before a swap. Also test whether minicpm-v4.6 can just cover `--ui` and retire the 17 GB model from vision entirely. |
| sweep lane (`lm fleet`) | none dedicated | ADD granite4:tiny-h as an option | 1.5x faster than gemma4-e4b, viable behind the fleet's constrained-decoding + Judge gate. Not a warm-companion swap. Probe on a real batch job before defaulting. |
| `WARM_MODEL` | gemma4-e4b (6.1 GB) | KEEP | Granite is a worse general assistant (wrong tool call, verbose); its speed only pays off in the gated sweep lane. |
| `BIG_MODEL` (reasoning) | gemma4:26b (17 GB) | KEEP | GLM-4.7-Flash, the only beyond-doctrine candidate worth probing, failed. |
| judge seat | none dedicated | USE resident gemma4:26b | 8/8 on the judgment gate. Zero new model needed. |
| `CODE_MODEL` | qwen3.6:35b-a3b (23 GB) | KEEP | The coding-sibling test is D11-gated and was not run this session. |
| `IMAGINE_MODEL` | qwen (mflux) | KEEP | No candidate has a confirmed better Apple-Silicon path. Note: mflux here already ships flux2 / ideogram4 / qwen-edit / z-image generators if you ever want them. |

## Evidence, one line each (full case reports linked)

- Stage 0, gemma4:26b as judge: 8/8 meaningful items clean. `case0-gemma-judge.md`.
- Stage 1a, minicpm-v4.6 vs minicpm-v: candidate 5/5 and 4.5/5 on UI, incumbent missed the ACTIVE column and invented two badges. `case1a-minicpm46.md`.
- Stage 1b, granite4:tiny-h: 93.5 vs 62 tok/s, but failed tool-decision and over-answered. Conditional sweep-lane accept. `case1b-granite.md`.
- Stage 2, Qwen3-VL-8B vs gemma4:26b: perfect tie (5/5, 4/4) at 6 GB vs 17 GB. `case2-qwen3vl.md`.
- Stage 3, GLM-4.7-Flash: 3/9 fails including a fabricated default, and 1/5 reliability at temperature 0.7. Rejected. `case3-glm.md`.

## What the methodology proved

The probe caught what benchmarks could not. GLM-4.7-Flash has the best leaderboard numbers
in the whole survey and is the least trustworthy candidate here: it fabricates an absent
detail, it codes before asking, and it gives five different answers to one trivial shell
question at temperature 0.7. The temp-0 probe showed 5/5 identical and hid that completely,
which is why the supplementary temp-0.7 check (added after Stage 0 flagged the blind spot)
earned its place. "Trust = a passing gate, never a spec sheet" did real work today.

## What changed on the machine

- Installed: minicpm-v4.6 (1.6 GB), granite4:tiny-h (4.2 GB), mlx-vlm 0.7.0 in the venv
  (Qwen3-VL-8B weights ~6 GB in the HF cache).
- config.sh: VISION_MODEL now minicpm-v4.6 (verified: plain `see` works).
- Deleted: glm-4.7-flash (19 GB), the failed candidate, per pull-probe-prune.
- New tool: `scripts/mem-guard.py`, the memory watchdog (see below).
- Policy: disk budget is now hard rule 3 in CLAUDE.md, pointer in STATE.md.
- Footprint: 115 GB (57 Ollama + 58 HF), inside the 150 target. Suite green: verify.sh 38/0, vis-battery 53/53.

## The crash and the guard

An earlier turn ran the MLX Qwen3-VL model and gemma4:26b at the same time; unified memory
ran out and the kernel's jetsam killer took down every agent on the machine. Two fixes:
`scripts/mem-guard.py` (a daemon that kills the largest model process when kernel memory
pressure rises, never touching agent processes, logging to logs/mem-guard.jsonl), and a
strict discipline of running one heavy model at a time. What actually kept later runs clean
was the sequential discipline: the guard never fired a kill, so its crash-prevention is a
design claim, not a proven one. Adversarial review (2026-09-12) hardened its trigger from
lagging free-page counts to the kernel pressure level and fixed a path-substring hole in its
never-kill list; it remains a backstop, unproven in a real OOM.

## Recommended next steps (owner decisions)

1. Confirm the vision swap in daily use, then prune the old minicpm-v (−5.5 GB).
2. If reclaiming the 17 GB gemma4:26b from vision is worth it, wire MLX-VLM into `see` and
   re-test Qwen3-VL-8B and minicpm-v4.6 on harder `--ui` fixtures (ambiguous selection,
   partial highlights, dense tables).
3. Run granite4:tiny-h on one real `lm fleet` batch before making it a sweep default.
4. Two prune candidates unrelated to this survey: qwen2.5-coder:3b (1.9 GB, in no tier) and
   gemma4:e4b-it-qat (6.1 GB, appears redundant with the warm model). Left for your call.
