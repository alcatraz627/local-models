# Lane 1 - local code model lane (fleet, probe, opencode, review, config)

Scope: `config.sh` CODE_MODEL, `lm probe`, `lm fleet`, `lm opencode`, `review`, `q --diy`,
the `unfinished-v1` exercise, and the routing doctrine. Read-only research, no inference run.

## 1. Actual usage (measured, not guessed)

**Fleet: dead.** `logs/fleet-history.jsonl` has 27 lines total, all from 2026-07-09 through
2026-07-13 (`jq -r '.ts' logs/fleet-history.jsonl | sort | uniq -c`). Of those 27 runs: 26 are
`intent=summarize` on `model=qwen2.5-coder:3b` (the *small* coder, not the CODE_MODEL tier), and
1 is `intent=qa` on `gemma4:26b` (`jq -r '.intent'` / `jq -r '.model'` on the same file). **The
code tier (`qwen3.6:35b-a3b`) has never once been dispatched through `lm fleet`** in its
recorded history. The 2026-08-10 adoption review (`~/.claude/assets/reports/20260810-local-models-review.md`)
confirms this at 30-day granularity: `fleet | 0` runs in the last 30 days, next to `q | 1678`,
`see | 52`, `imagine | 0`, and frames the open question directly: "did the fleet/local-coder
seat get real work? ... If it never ran again, the experiment was interesting and unadopted."
The weekly self-audits (`logs/self-audit/20260719.md` through `20260823.md`) show `fleet runs | 0`
every single week since; `20260823.md`'s only active stream is `gemini | 26 calls, 6 failures`.

**Probe: run 4 times, never scored.** `probe/runs/` has 8 files (`ls probe/runs/`), the latest
being `qwen3.6_35b-a3b-nvfp4-20260707-131716.md`. Every human-verdict checkbox in that file is
still `☐ pass  ☐ fail`, unfilled. The probe's own contract (`probe/items.toml:1-4`) says "the
**human verdict** is the decision (trust = observation, not the model's confidence)." No run in
`probe/runs/` has that human step completed, so by the harness's own rule none of the 4 qwen3.6
runs is a real go/no-go data point yet, only the auto-heuristic flags (`PASS?`/`REVIEW`) exist.
The auto-flags on the latest run: 6 `PASS`/`PASS?`, 2 `REVIEW` (tool-decision, the new
`invariant-aware-edit` item), 1 clean `PASS` (multiturn-if).

**`lm opencode`: configured, no usage evidence found.** `~/.config/opencode/opencode.jsonc`
wires the `ollama` provider with `qwen3.6:35b-a3b` as `"model"` default, meaning opencode's
default IS the code tier, plus three other local models. `bin/lm:184-192` implements
`lm opencode` as a lease-wrap (`warm on code`, run opencode, trap-based unpin on exit, "NOT
exec, the trap must outlive the child," per the inline comment). No history file logs opencode
sessions (unlike q/see/fleet), so usage cannot be measured from this repo's own instrumentation.
This absence is itself a gap (see §3).

**`review`: logs into q-history (it's a `q` intent), not a separate stream.** `bin/review:44,66-68`
confirms reviews are aliased into `logs/q-history.jsonl`. No `logs/review-history.jsonl` exists.
Recent commits (`git log` head: `cf3bb3a fix(review): --findings defaults to the small tier`,
`91e8ae3`, `aa91c57`, all dated 2026-07-24) show active hardening work on `review --findings`
(retry/exit-3 contract, structured-mode failure behavior). This argues someone is actively fixing
`review` even without dedicated telemetry proving end-user calls.

**`q --diy` / `q --format`:** `logs/q-history.jsonl` has 2,222 lines total (across all intents,
not code-specific). This is the dominant `q` usage stream overall, but it was not isolable to
code-tier calls without a deeper `jq` cut than time allowed; flagged as a research gap, not
asserted either way.

## 2. What was attempted (design intent vs. what happened)

- **docs/03-tool-orchestration-decision.md**: local models do NOT drive their own tools. The
  orchestrator (Claude) always applies edits and runs judges; the local model is a scoped
  worker, never an autonomous agent. This boundary is treated as settled ("so they're not
  re-litigated," `docs/03:40`) and every later design (fleet, the E1 experiment) respects it.
- **docs/09-local-fleet.md** (`docs/09:1-40`): grounded in a scan of 269 real Claude sub-agent
  dispatches over 14 days. Its own use-case table marks "Rewrite / fix / apply" as only `◐
  split` fit ("mechanical transforms → local behind a diff gate; judgment → Claude") and
  explicitly excludes "Design / decompose / final decision" (`✗ Claude, never delegated`). The
  fleet model calls for "several MODERATE models, not one big coder," run concurrency-capped.
- **The Jul-13 fleet-over-real-code-task experiment**
  (`.claude/output/20260713-fleet-code-task/experiment.md`): the strongest positive evidence in
  the repo. `qwen3.6:35b-a3b` reimplemented a real, previously-shipped change (E1 numeric-position
  deltas) against a pre-written mechanical judge (battery F9/F9b), scoring **33/33 GREEN on round
  1**, 35.2s wall time, 1,383 tokens out, and correctly implemented a spec-only requirement (the
  malformed-geometry skip rule) that was never shown as a test. The experiment's own decision
  section is careful about scope: "the scoped-worker-under-a-judge seat is CLEARED... NOT evidenced:
  the autonomous tier." Decomposition, fixture authorship, and repo navigation were all supplied
  by the cloud orchestrator in the prompt. This is **n=1**, self-administered, on a task the repo's
  own team designed and already knew the answer to (a reference implementation existed).
- **The routing rule this experiment proposed** (`experiment.md`, "Routing rule (proposed for
  docs/STATE)"): route to local code tier when ALL of, unit scoped to named functions/files,
  a mechanical judge exists BEFORE dispatch, the orchestrator applies+judges. This rule was
  **proposed but never wired into any dispatch path**. No skill, hook, or CLI flag anywhere in
  the repo operationalizes "check these three conditions, then call `lm fleet`/`q -m code`."
- **`probe/fixtures/unfinished-v1/`** (per `docs/STATE.md`): qwen3.6 completed a "finish a
  codebase" exercise 16/16 under a pytest judge (2026-07-07), a second depth-style positive
  signal, with the same caveat (scoped, judge-gated, cloud-authored task).
- **The 80B candidate** (Qwen3-Coder-Next 80B-A3B, named in project memory as the target model)
  was **never pulled to disk**. The experiment doc says directly: "not on disk (~50GB pull = user
  decision)." The repo has been running its "code tier" as `qwen3.6:35b-a3b` (35B-A3B), a smaller,
  different model from the one the user's own stated efficacy bar names as the candidate.

## 3. Gaps, why nothing routes to this lane

1. **No dispatch point exists.** The routing rule (§2) was written down once, in a project-scoped
   experiment doc, and never became a skill, a gcc rule, or a CLI ergonomic. Nothing in `~/.claude/`
   (checked `rules/model-tier-routing.md`, `features/model-tier-harness.md`) tells a Claude session
   *when in a real task* to reach for `lm fleet`/`q -m code` instead of doing the edit itself. The
   global routing rule only says "code changes → main/opus seat; local coder only behind a Judge,"
   correct but too abstract to trigger a callsite decision; it names no command.
2. **Fleet's own harness is judge-optional in practice.** `docs/09` calls the fleet "Judge-gated,"
   but the 27 real fleet runs on record are `summarize` (a judgment task, not code), the harness
   was validated for code exactly once, outside `lm fleet` itself, via a bespoke worktree script
   (`experiment.md`'s own recipe), not through `lm fleet <intent> <files>` at all. There is a gap
   between "fleet CAN judge-gate code" (asserted) and "fleet HAS judge-gated code" (never observed
   in `logs/fleet-history.jsonl`).
3. **No fixture/judge library for real work exists outside the one-off E1 case.** The
   scoped-worker-under-a-judge pattern needs a pre-existing failing test/schema/battery *before*
   dispatch. Nothing generates or catalogs these for arbitrary tasks; the E1 case worked because
   the repo's own battery (F9/F9b) already existed for unrelated reasons. For a typical ad hoc task
   a Claude session would have to hand-write the judge first, which is exactly the kind of upfront
   cost that makes "just do it myself" cheaper in the moment.
4. **Efficacy is unverified at the target scale.** The candidate model (Qwen3-Coder-Next
   80B-A3B) was never tried; the model actually gated (`qwen3.6:35b-a3b`) has one n=1 win on a
   task the team already knew how to solve. `lm probe`'s 4 recorded qwen3.6 runs are all
   unscored by a human. So there is currently **no scored evidence** meeting the project's own bar
   ("trust = a passing gate, never model confidence," CLAUDE.md) that the code tier is trustworthy
   across a spread of tasks, only one dramatic anecdote.
5. **Ergonomics:** `lm opencode` has no session logging, so its own maintainers cannot tell if it
   gets used; a session that tries it once and doesn't log a JSONL row leaves no trace for the
   self-audit loop that everything else in this repo is instrumented for.
6. **The `--format` constraint gap** noted in root CLAUDE.md, "the 35b code tier ignores Ollama's
   format constraint," means schema-constrained output (`review --findings`, `q --format`) is
   NOT reliable on the code tier itself. You must pin `-m small` for schema compliance, which is
   in tension with wanting the *coding-specialized* model to also emit structured findings.

## 4. The ideal workflow (concrete)

Given the settled boundary (docs/03: local never drives tools) and the one proven pattern
(scoped-worker-under-a-judge), the ideal hand-off looks like this:

```
Claude session identifies a scoped unit (named files/functions, no open design questions)
        |
        v
Claude WRITES the judge FIRST (a failing test / schema check / battery delta). This is the
gate, and it must exist and be RED before dispatch, per rules/exercise-based-verification.md's
own doctrine applied to the local worker
        |
        v
Claude calls `lm fleet <intent> <files>` (or `q -m code --ctx`) with the task spec, the judge's
contract restated in the prompt (verbatim, not paraphrased) and nothing implying autonomy
beyond the named files
        |
        v
Claude (never the local model) applies the patch mechanically
        |
        v
Claude re-runs the SAME judge. Green on round 1 -> done, log the win. Red -> escalate one step
(retry once with the failure fed back; second failure -> do it in cloud), per model-tier-routing's
"escalate on evidence, never anticipation"
```

Where this belongs in the gcc: **a skill, not a bare CLI verb**, something like
`/dispatch-to-local-coder` (or a mode of `/bloop`, which already runs an adversarial-validation
loop and already understands "gate before trust") that (a) checks the three routing-rule
conditions from §2 before offering the option at all, (b) refuses if no judge exists yet and
offers to help write one, (c) calls `lm fleet` or `q -m code` under the hood, (d) logs the
outcome somewhere self-audit can see it distinctly from `summarize` fan-outs. A `fleet` intent
tag like `code-dispatch` would let `jq` separate real code attempts from doc/summarize noise;
currently they are indistinguishable in `logs/fleet-history.jsonl` by intent name alone once
code intents appear. This is the single highest-leverage missing piece: right now the
*capability* is proven on paper (n=1) but the *habit* of reaching for it has no hook anywhere a
session would see it.

## 5. Bridge, smallest changes ordered by benefit

1. **Score the 4 existing probe runs by hand.** Near-zero cost, unblocks everything downstream;
   right now the repo doesn't even know by its own rule whether qwen3.6 is trusted.
2. **Tag a `code`-specific fleet intent** (e.g. `intents/code-fix.toml`) distinct from
   `summarize`, so self-audit and the 30-day review can actually see code-lane usage separately
   from the doc-fan-out noise that's dominated `logs/fleet-history.jsonl` since day one.
3. **Wire the routing rule into one callsite.** Even a one-line addition to
   `rules/model-tier-routing.md`'s decision table ("scoped + judge exists → `lm fleet`/`q -m
   code`, see local-models docs/09") would give a session something concrete to match against,
   rather than the current abstract "code changes → main/opus; local coder only behind a Judge."
4. **Run the E1-style experiment 5-10 more times on varied real tasks**, not just the one the
   team already solved, before treating "the seat is cleared" as more than a promising anecdote.
   This is the load-bearing gap between what's claimed and what's shown.
5. **Pull and probe the actual named candidate** (Qwen3-Coder-Next 80B-A3B). The repo has been
   gating on a different, smaller model (`qwen3.6:35b-a3b`) than the one the user's own efficacy
   bar names. At Q4_K_M this needs ~52GB VRAM (see §6), which is tight but plausible on 64GB
   unified memory with careful residency management (nothing else warm).
6. **Add session logging to `lm opencode`** so usage becomes visible to the same self-audit loop
   everything else in this repo goes through. Currently the tool with the code tier as its
   *default* model is the one piece of the lane with zero usage telemetry.

---

# Part B - external research (Aug 2026)

## 6. Best local coding models for a 64GB Apple Silicon Mac (Aug 2026)

| Model | Params/active | Quant fitting 64GB w/ headroom | Reported perf | Benchmark standing | Tool-calling | Availability |
|---|---|---|---|---|---|---|
| **Qwen3-Coder-Next 80B-A3B** | 80B total / 3B active | Q4_K_M ~52GB VRAM; Q5_K_M ~64GB (too tight to leave room for a warm companion); Q6 ~75GB (won't fit) [Qwen3-Coder-Next GGUF discussion, HF, 2026](https://huggingface.co/unsloth/Qwen3-Coder-Next-GGUF/discussions/1) | GPU (H100) 60-120 tok/s; no confirmed Mac-specific M4/M3 Max numbers found in search | SWE-bench Verified 70.6-74.2% (source-dependent), SWE-bench Pro 44.3%, SWE-bench Multilingual 63.7%, Aider 66.2, "comparable to models with 10-20x more active params" [Qwen team blog](https://qwen.ai/blog?id=qwen3-coder-next); [MarkTechPost, Feb 2026](https://www.marktechpost.com/2026/02/03/qwen-team-releases-qwen3-coder-next-an-open-weight-language-model-designed-specifically-for-coding-agents-and-local-development/); [LocalAIMaster](https://localaimaster.com/models/qwen-3-coder-next) | Purpose-built for coding agents; Qwen family described as the tool-calling default for 2026 local agents [PromptQuorum](https://www.promptquorum.com/power-local-llm/best-local-models-tool-calling-2026) | Ollama, GGUF (unsloth), MLX-LM |
| **Qwen3.6:35b-a3b** (current CODE_MODEL) | 35B / 3B active | Fits comfortably at ~23GB (per this repo's own config comment) | This repo measured 33/33 on a real judged task, 35.2s, resident | Probe-gated 9/9 per repo (unscored by human, see §1) | Repo notes it ignores Ollama's `--format` constraint for schema output | Ollama (already installed here) |
| **Qwen3-Coder 30B-A3B Instruct** | 30B / ~3B active | Fits with room to spare | 33 tok/s reported for coding on Apple Silicon [apxml, Best Local LLMs Apple Silicon Mac, 2026](https://apxml.com/posts/best-local-llms-apple-silicon-mac) | Not directly SWE-bench-cited in results found | Reliable per Qwen-family tool-calling reputation | Ollama, MLX |
| **GLM-4.6 / GLM-4.5-Air** | 357B (GLM-4.6) / 106B (GLM-4.5-Air, MoE) | Full GLM-4.6 needs data-center GPUs, does not fit 64GB; GLM-4.5-Air is the realistic local variant | LiveCodeBench v6 jumped to 82.8% (GLM-4.6, cloud-scale) [huggingface.co blog, "Best Open-Source LLM Models 2026"](https://huggingface.co/blog/daya-shankar/open-source-llms) | Strong on cloud hardware; local-fit variant (Air) benchmarks not directly found | MIT-licensed, commercial-use variants exist | Cloud-scale primarily; not a realistic single-model fit for this machine at full size |
| **GLM-4.7-Flash** | ~30B total / ~3B active (MoE) | Should fit comfortably alongside a warm companion | 95% accuracy at 52 tok/s cited [PromptQuorum, tool-calling 2026](https://www.promptquorum.com/power-local-llm/best-local-models-tool-calling-2026) | Not independently cross-verified in this pass | Cited specifically in a tool-calling benchmark roundup | Not confirmed on Ollama registry as of this search |
| **DeepSeek-Coder-V2-Lite** | 16B / 2.4B active | ~12GB, easily fits alongside other models | 90.2% HumanEval (DeepSeek-Coder-V2 family, not confirmed Lite-specific) [Tembo.io / promptquorum roundups](https://www.tembo.io/blog/best-local-llm-for-coding) | Strong for its size class; older generation vs. Qwen3.6/Coder-Next | Reasonable | Ollama |
| **Devstral Small 2** (Mistral) | 24B dense | Fits, dense so heavier per-token cost than the MoE options | Framed as "fits a single 4090"; no Apple Silicon-specific numbers found | Not independently benchmarked in this pass | Mistral function-calling format, generally solid | Ollama, HF |
| **Gemma 4 26B A4B** (this repo's BIG_MODEL) | 26B total / 3.8B active | ~17GB per this repo's own docs | LiveCodeBench jumped 29.1% to 80.0% for the Gemma-4 family generation-over-generation (dense 31B figure, not the MoE A4B specifically) [dev.to Gemma 4 guide](https://dev.to/aniruddhaadak/gemma-4-complete-guide-2026-architecture-benchmarks-deployment-3en9); [Aurigait Gemma 4 guide](https://aurigait.com/blog/gemma-4-features-benchmarks-guide/) | "Fastest local coding model by tokens per second, trading some benchmark performance for speed" per one roundup, UNVERIFIED against a primary Google source in this pass | Adequate, not coding-specialized | Ollama (already this repo's `BIG_MODEL`) |

**Bottom line for the 64GB constraint:** Qwen3-Coder-Next 80B-A3B at Q4_K_M (~52GB) is the
tightest realistic fit that leaves any headroom for macOS plus a warm companion. Q5_K_M (~64GB)
would need the machine to run essentially nothing else, which conflicts with this repo's hard
"no idle penalty, warm companion always available" rule. **UNVERIFIED**: no source found gave a
direct Apple Silicon M4/M3 Max/M5-class tok/s number for Qwen3-Coder-Next specifically; every
number found was either H100/GPU or for other Qwen variants (30B-A3B: 33 tok/s). Given this
repo's M5 Pro has ~307 GB/s bandwidth (per project CLAUDE.md), roughly comparable to an M4 Max's
~400+ GB/s tier but on the lower end, extrapolating from the 30B-A3B's 33 tok/s figure to an
80B-A3B model with the same 3B active-parameter count would put a **rough, unverified estimate**
in a similar tok/s range (MoE speed scales primarily with active params, not total). This is
extrapolation, not a measured result, and should be treated as a hypothesis to test via `lm probe`
before trusting it.

## 7. Agent harnesses for driving a local model on this shape of work

- **OpenCode** (~165k stars, per one 2026 roundup) is described as the dominant open-source
  coding-agent harness in 2026, provider-agnostic, and this repo already uses it (`lm opencode`).
  [futureagi.com](https://futureagi.com/blog/best-agent-harness/); [sanj.dev comparison](https://sanj.dev/post/comparing-ai-cli-coding-assistants/)
- **Aider** and **Cline**: both support Ollama backends. One source frames "simple tasks locally,
  unit tests, docstrings, single-file edits" as Aider/Cline's local-model sweet spot rather than
  complex multi-file agentic work [Kunal Ganglani, Claude Code alternatives, 2026](https://www.kunalganglani.com/blog/claude-code-alternatives-open-source).
  This lines up with docs/09's own use-case table (mechanical transforms fit local; judgment
  doesn't).
- A head-to-head using the SAME model (Kimi K2.5) across OpenCode/Cline/KiloCode found
  meaningfully different results per harness: "OpenCode handling complex refactoring smoothly
  while Cline worked reasonably well" [BSWEN comparison](https://docs.bswen.com/blog/2026-03-15-opencode-vs-kilocode-vs-cline-comparison/).
  This means **harness choice is not neutral**; this repo's existing OpenCode integration is a
  reasonable default rather than an arbitrary one.
- **No source found** discusses a harness with a *native, built-in* judge/test-loop specifically
  for local models. Every "judge-gated" pattern found in this research (including this repo's
  own) is hand-rolled orchestration around the harness, not a harness feature. This confirms the
  repo's docs/03 decision (local models don't drive tools, an external judge gates them) is
  aligned with the state of the field rather than reinventing something that exists elsewhere.
- 2026 churn to note: Gemini CLI retired June 18 2026, Roo Code archived May 2026, OpenCode
  dropped Claude Pro/Max login after an Anthropic dispute [pinggy.io CLI roundup, 2026](https://pinggy.io/blog/best_open_source_cli_coding_agents/).
  The harness landscape is still consolidating; OpenCode's survival and continued Ollama-provider
  support make it the safer bet to keep building on rather than switching.

## 8. Speculative decoding / MTP on Metal (Aug 2026 state, vs. this repo's docs/05 counter-finding)

The repo's `docs/05-perf-levers-and-usage-audit.md` §1 recorded a counter-finding that
draft-model speculative decoding **regresses** on llama.cpp/Metal as of its measurement date. The
2026 external picture is more nuanced and has moved since:

- **MTP (multi-token-prediction) speculative decoding is now natively supported for Qwen3.x
  models on Ollama's MLX runner**, gated behind an `--experimental` flag when it first landed,
  using a `DRAFT` directive in the Modelfile [Unsloth Qwen3.6 docs](https://unsloth.ai/docs/models/qwen3.6).
  A HuggingFace GGUF repo (`froggeric/Qwen3.6-27B-MTP-GGUF`) packages an MTP-enabled build
  specifically for this. This is a genuinely different mechanism from the classic
  small-draft-model-verified-by-big-model speculative decoding this repo's docs/05 tested. MTP
  uses the model's OWN built-in multi-token-prediction head, not a separate draft model, so
  docs/05's counter-finding (about draft-model spec-dec) does not necessarily transfer to MTP.
- One independent report claims **1.4-2.2x faster generation with no accuracy change** using
  MTP on Qwen3.6-class models [runaihome.com](https://runaihome.com/blog/speculative-decoding-llama-cpp-local-llm-setup-2026/).
  A separate hands-on blog reports **18 tok/s on a 27B model on a MacBook** using "MLX + native
  MTP speculative decoding" [vinoth12940.github.io](https://vinoth12940.github.io/blog/articles/genai-20260519-local-mtp-speculative-decoding/). Both UNVERIFIED against a primary Ollama/Qwen source in this pass, and neither is independently
  corroborated by a second source, so treat as promising but not confirmed.
- **General MLX vs. llama.cpp on Metal**: a comparative production-grade study finds "MLX offers
  the best raw throughput and system efficiency" on Apple Silicon [arxiv 2511.05502](https://arxiv.org/pdf/2511.05502).
  A newer runtime called **BaseRT** claims 1.04-1.56x speedup over llama.cpp on M4 Pro across six
  models [arxiv 2607.00501](https://arxiv.org/pdf/2607.00501). This repo has not evaluated
  BaseRT and it does not appear to be Ollama-integrated, so it's a research-only lead, not
  actionable today.
- **Bottom line**: the repo's docs/05 finding (classic draft-model spec-dec regresses on
  llama.cpp/Metal) still appears consistent with the broader 2026 picture for THAT mechanism.
  What's changed since is **native MTP support landing in Ollama's MLX runner specifically for
  Qwen3.x**, a different mechanism the repo has not yet evaluated. It's worth a fresh probe run
  (`lm probe` plus a tok/s measurement) rather than assuming the old counter-finding still
  applies, since MTP was explicitly out of scope for what docs/05 tested.

## 9. Uncertainties

- No primary-source (Qwen team, Ollama release notes) confirmation was fetched for MTP/Qwen3.6
  claims in §8; all came from third-party blogs/aggregators, flagged UNVERIFIED throughout.
- No Apple Silicon M-series tok/s number was found specifically for Qwen3-Coder-Next 80B-A3B; the
  extrapolation in §6 is a hypothesis, not a citation.
- GLM-4.7-Flash's Ollama/registry availability was not confirmed independently.
- Whether `lm opencode` sessions actually happened (vs. just being configured) could not be
  determined from repo telemetry; this is a genuine local-analysis gap (§3.5), not resolved by
  external research.
- The repo's `q-history.jsonl` (2,222 lines) was not broken down by code-vs-other intent in the
  time available; flagged as an unclosed sub-question in §1, not asserted either way.

## 10. Source table

| Title | URL/path | Date | Reliability note |
|---|---|---|---|
| Repo: docs/STATE.md, docs/03, docs/09, docs/05 | local, /Users/alcatraz627/Code/local-models/docs/ | living doc, last STATE update 2026-07-09 | Primary, high, this project's own design record |
| logs/fleet-history.jsonl, logs/self-audit/*.md | local | 2026-07-09 through 2026-08-23 | Primary, high, raw telemetry |
| .claude/output/20260713-fleet-code-task/experiment.md | local | 2026-07-13 | Primary, high, but n=1 self-administered experiment |
| ~/.claude/assets/reports/20260810-local-models-review.md | local | 2026-08-10 | Primary, high, 30-day adoption audit |
| Qwen3-Coder-Next blog (Qwen team) | https://qwen.ai/blog?id=qwen3-coder-next | 2026 | Primary vendor source, high |
| MarkTechPost Qwen3-Coder-Next release | https://www.marktechpost.com/2026/02/03/... | 2026-02-03 | Secondary tech-press, medium-high |
| LocalAIMaster Qwen3-Coder-Next review | https://localaimaster.com/models/qwen-3-coder-next | 2026 | Secondary, medium |
| unsloth Qwen3-Coder-Next GGUF HF discussion | https://huggingface.co/unsloth/Qwen3-Coder-Next-GGUF/discussions/1 | 2026 | Community/primary quant data, medium-high |
| apxml Best Local LLMs Apple Silicon Mac | https://apxml.com/posts/best-local-llms-apple-silicon-mac | 2026 | Secondary aggregator, medium |
| PromptQuorum tool-calling roundup | https://www.promptquorum.com/power-local-llm/best-local-models-tool-calling-2026 | 2026 | Secondary aggregator, medium |
| HuggingFace open-source LLM blog (daya-shankar) | https://huggingface.co/blog/daya-shankar/open-source-llms | 2026 | Secondary, medium |
| Unsloth Qwen3.6 docs (MTP) | https://unsloth.ai/docs/models/qwen3.6 | 2026 | Primary-adjacent (official quantizer/docs partner), medium-high |
| runaihome.com spec-dec setup guide | https://runaihome.com/blog/speculative-decoding-llama-cpp-local-llm-setup-2026/ | 2026 | Secondary blog, medium, uncorroborated |
| vinoth12940.github.io MTP blog | https://vinoth12940.github.io/blog/articles/genai-20260519-local-mtp-speculative-decoding/ | 2026-05-19 | Individual blog, low-medium, uncorroborated |
| arXiv 2511.05502 (MLX/MLC/Ollama/llama.cpp/PyTorch MPS comparison) | https://arxiv.org/pdf/2511.05502 | academic preprint | Primary academic, medium-high |
| arXiv 2607.00501 (BaseRT) | https://arxiv.org/pdf/2607.00501 | academic preprint | Primary academic, medium-high |
| sanj.dev Aider/OpenCode/Claude Code comparison | https://sanj.dev/post/comparing-ai-cli-coding-assistants/ | 2026-06 | Secondary, medium |
| BSWEN OpenCode/KiloCode/Cline comparison | https://docs.bswen.com/blog/2026-03-15-opencode-vs-kilocode-vs-cline-comparison/ | 2026-03-15 | Secondary, medium |
| pinggy.io CLI coding agents roundup | https://pinggy.io/blog/best_open_source_cli_coding_agents/ | 2026 | Secondary aggregator, medium |
| Gemma 4 guide (dev.to, aurigait) | https://dev.to/aniruddhaadak/gemma-4-complete-guide-2026-architecture-benchmarks-deployment-3en9 / https://aurigait.com/blog/gemma-4-features-benchmarks-guide/ | 2026 | Secondary, medium |
