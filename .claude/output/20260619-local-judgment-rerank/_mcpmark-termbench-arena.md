# MCPMark / Terminal-Bench / Agent Arena — candidate open-model scores

Research date: 2026-06-19. Live web sources (not training memory). Numbers reported ONLY where a published score genuinely exists; otherwise "no data".

Confidence flags: **[solid]** = on an authoritative leaderboard or vendor card · **[single-source]** = one secondary source · **[hearsay]** = blog/comparison only.

## LEADERS (calibration)

| Benchmark | Leader | Score | Top open model | Source | Date |
|---|---|---|---|---|---|
| MCPMark (Pass@1, model leaderboard) | OpenAI gpt-5-2-high | 57.5% ±1.1 | (Qwen/GLM closed-ish variants on board; no candidate present) | https://mcpmark.ai/leaderboard | 2026-06 |
| Terminal-Bench 2.0 | OpenAI GPT-5.5 | 0.827 (82.7%) | GLM-5.1 (Zhipu) — 0.690, rank #10 | https://llm-stats.com/benchmarks/terminal-bench-2 | 2026-06 |
| Terminal-Bench 2.1 (newer split) | Claude Fable 5 | 88.0% | — | https://codingfleet.com/blog/terminal-bench-leaderboard-2026/ | 2026-06 |
| Agent Arena (Net Improvement / steerability) | Claude Fable 5 (High) | 14.05% ±1.53 NetImp, rank #1 | (open: Gemma 4 31B at #27) | https://arena.ai/leaderboard/agent | 2026-06-18 |

Note: MCPMark's official board uses **Pass@1**; the labellerr secondary source reports a percentage labeled "MCPMark" that does not match an official-board cell, so candidate MCPMark numbers below are secondary-source.

## Candidate models × benchmarks

| Model | MCPMark | Terminal-Bench (version) | Agent Arena rank | Source | Date | Confidence |
|---|---|---|---|---|---|---|
| Qwen3-Coder-Next 80B-A3B | no data | no data | no data | (searched mcpmark.ai, llm-stats TB2, arena.ai — absent) | 2026-06-19 | n/a |
| Qwen3-Coder-30B-A3B | no data | no data (only in AA Intelligence Index v4.1 composite, no standalone TB cell published) | no data | https://artificialanalysis.ai/models/qwen3-coder-30b-a3b-instruct | 2026-06-19 | n/a |
| Qwen3.6-35B-A3B | 37.0% | 51.5% (**TB 2.0**); also rank #32 / 0.515 on llm-stats TB2 board | no data (Qwen 3.6 *Plus* is on Arena #21, a different/larger variant — NOT this model) | MCPMark+TB: https://www.labellerr.com/blog/qwen3-6-35b-a3b-open-source-ai-model/ ; TB board: https://llm-stats.com/benchmarks/terminal-bench-2 | 2026-06-19 | TB [solid] · MCPMark [single-source/hearsay] |
| Qwen3.6-27B (dense) | no data | 0.593 (59.3%), rank #20 (**TB 2.0**) | no data | https://llm-stats.com/benchmarks/terminal-bench-2 | 2026-06-19 | TB [solid] |
| Devstral-Small-2 24B | no data | no data (Mistral card cites only SWE-bench Verified 68.0%, NOT Terminal-Bench) | no data | https://mistral.ai/news/devstral-2-vibe-cli/ | 2026-06-19 | n/a |
| GLM-4.7-Flash (30B MoE) | no data | no data for the *Flash* variant specifically (parent **GLM-4.7** = 41% on **TB 2.0**) | no data | parent: https://github.com/zai-org/GLM-4.5/blob/main/README.md | 2026-06-19 | parent-only [single-source] |
| GLM-4.5-Air (106B-A12B) | no data | no data (no standalone TB cell found; GLM family TB numbers are quoted for 4.6/4.7, not Air) | no data | (searched GLM README, llm-stats, TB2 board — absent) | 2026-06-19 | n/a |
| Gemma 4 31B (dense) | 18.1% | 42.9% (**TB 2.0**, from comparison table) | **rank #27**, NetImp 12.72% ±1.68 | MCPMark+TB: https://www.labellerr.com/blog/qwen3-6-35b-a3b-open-source-ai-model/ ; Arena: https://arena.ai/leaderboard/agent | 2026-06-19 | Arena [solid] · TB/MCPMark [single-source/hearsay] |
| Gemma 4 26B (MoE-A4B) | no data | no data | no data (26B not on Arena top-28; "Arena #6 ELO 1441" claim is the general LMArena text board, not Agent Arena) | (searched) | 2026-06-19 | n/a |
| OLMo 3-Think 32B | no data | no data (appears only inside AA Intelligence Index "Terminal-Bench Hard" composite, no standalone published cell) | no data | https://artificialanalysis.ai/models/olmo-3-1-32b-think | 2026-06-19 | n/a |

## Notes / caveats

- **Naming check.** All nine candidate names resolve to real released models (HF cards exist for Qwen3.6-35B-A3B, Qwen3-Coder-30B-A3B, Devstral-Small-2-24B-Instruct-2512, GLM-4.7/GLM-4.5, Gemma 4, OLMo 3.1 32B Think). "Qwen3-Coder-Next 80B-A3B" has a technical report (arxiv 2603.00729) but I found **no benchmark-leaderboard presence** on any of the three target benchmarks.
- **Terminal-Bench version discipline.** Every TB number above is **TB 2.0** (the current llm-stats board and the labellerr comparison are both 2.0). A separate **TB 2.1** split exists (Fable 5 leads at 88.0%); none of the candidates appear on the 2.1 split.
- **MCPMark caveat.** The official mcpmark.ai board (Pass@1) contains **none** of the candidates — only larger qwen-3-coder-plus / qwen-3-max / glm-4-5 entries. The "MCPMark 37.0% / 18.1%" figures for Qwen3.6-35B-A3B / Gemma4-31B come from a single secondary blog and could not be cross-confirmed against the official board → treat as [single-source/hearsay].
- **Agent Arena.** Only **Gemma 4 31B** (rank #27) among the candidates is on the Agent Arena board. "Qwen 3.6 Plus" (rank #21) is a distinct larger variant, not Qwen3.6-35B-A3B or 27B. GLM-4.5-Air, GLM-4.7-Flash, Devstral, Qwen3-Coder*, OLMo 3 are all absent.
- **Strongest verified candidate signals:** Qwen3.6-27B (TB 2.0 59.3% [solid]) and Qwen3.6-35B-A3B (TB 2.0 51.5% [solid]) are the only candidates with leaderboard-grade TB numbers. Gemma 4 31B is the only candidate with a verified Agent Arena rank.
