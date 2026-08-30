# The lm suite: what you actually get out of it, and what would change that

2026-08-30. Five research seats (one per lane plus performance), each over the repo's histories, docs, prior research archives and the web; the parent read every file and re-ran the checks that mattered. Raw seat files sit beside this report as `lane-1-code.md` to `lane-5-perf.md`. The build plan is `plan.md` in the same directory.

Scope: local-models only. Four lanes you named (local code model, `lm gemini`, vision + the UI driver loop, image generation) and the operational cut across them.

## 1. Usage, in one table

Counts from the histories (`logs/*.jsonl`, `outputs/imagine-history.jsonl`); build week ended 2026-07-13, 48 days ago.

| lane | pieces | runs since 07-13 | last run | who calls it | verdict |
|---|---|---|---|---|---|
| `q` (ask/qa/cmd) | small warm tier | 891 real + 767 tab-titles + 21 review | 08-26 | every project, agents and you | load-bearing; the tab-titler is 44% of volume |
| `see` plain / `--ocr` | minicpm-v, Apple Vision | 29 in Aug (191 in Jul) | 08-28 | kanban, forge, data-forge, playwright captures | load-bearing but collapsed 85% after build week |
| `see --ui` | gemma4:26b | most of the 68 ui rows are July | Aug | same | used, slow: p50 20s, p95 43s, max 154s |
| `see diff` + `/vis-compare` | L1 pack, L2 judge, L3 ledger | 4 (Aug 23 x3, Aug 28) | 08-28 | kanban dark/light | alive by a pulse; L3 loop never ran on live UI |
| `/ui-gripe` | native judgment over see | 12 runtime-note entries through 08-24 | 08-24 | kanban, data-forge | the healthiest judge skill, real finds |
| `/ui-categorical-check`, `/designer-reviewer`, `/ui-direction` | | 1, 0, 0 recorded | | | unused or unlogged |
| `lm ui-verify --app` (AX tree) | `ax` 0.3.0 installed | no history stream | unknown | | the exact, fast path, invisible |
| code tier `qwen3.6:35b-a3b` via `q -m code` | | 24 calls ever, p50 17s | | | one n=1 win (33/33, 35s) on a judged task |
| `lm fleet` | | 0 (27 ever, all summarize on a 3b model) | 07-13 | nobody | dead; never ran the code tier |
| `lm probe` | 4 qwen3.6 runs | 0 | 07-07 | | every human-verdict box still unticked |
| `lm opencode` | | unlogged | | | no telemetry at all |
| `lm gemini` | gemini-3.5-flash, API key | 33 in Aug, 11 errors (8 timeouts) | 08-24 | hand-typed; batch transcript classification and company web lookups | used, off its stated role, no skill calls it |
| `imagine` | mflux, qwen default | 0 (18 ever) | 07-13 | nobody | dead; zero outputs ever used in real work; 84 GB of weights |
| weekly self-audit cron | | fired every Sunday | 08-23 | | the best-adopted thing in the repo |
| warm-morning / warm-evening-off | | exit 127 every run; morning plist deleted ~08-05 | | | the no-idle backstop has been inert its whole life |

## 2. The structural picture

```
                what exists                          what is missing
   ┌─────────────────────────────────┐    ┌──────────────────────────────────┐
   │ DUMB TOOLS (deterministic, $0)  │    │ CALLERS: no skill, hook or verb  │
   │  see --ocr · see diff · ax tree │    │  in ~/.claude routes work here.  │
   │  e8-dom · vis-ledger · findings │    │  Every run since July was typed  │
   │  -gate · asset-verify · probe   │◄───┤  by hand by you or by an agent   │
   │  fleet · gemini wrapper         │    │  that already knew the command.  │
   └────────────┬────────────────────┘    └──────────────────────────────────┘
                │ evidence.json, inventory, verdicts, histories
   ┌────────────▼────────────────────┐    ┌──────────────────────────────────┐
   │ GAUGES (all working)            │    │ TWO MECHANICAL LINKS             │
   │  histories · self-audit cron ·  │    │  capture + re-render (vision)    │
   │  08-10 adoption review · probe  │    │  judge-before-dispatch (code)    │
   │  runs · vis-ledger transitions  │    │  neither scripted; both are what │
   └────────────┬────────────────────┘    │  the driver loop needs to close  │
                │ read by nobody           └──────────────────────────────────┘
   ┌────────────▼────────────────────┐    ┌──────────────────────────────────┐
   │ DOCTRINE (correct, in prose)    │    │ TRUST MECHANISMS exist in 2 of 4 │
   │  scripts measure, models judge, │    │  lanes (vis-ledger, findings-    │
   │  trust = passing gate, no idle  │    │  gate). Gemini and code have the │
   │  penalty, route local first     │    │  sentence and no gate.           │
   └─────────────────────────────────┘    └──────────────────────────────────┘
```

Three facts explain every lane at once.

1. Every lane has its dumb tools and its gauge built and working. What no lane has is a caller: `rg -l "lm gemini|lm fleet|imagine" ~/.claude/skills` returns nothing; `see`/`ui-gripe` are called by hand. The routing rule promises lanes at the top of every session and nothing at the dispatch point reads it. This is the same shape the estate audit found in the gcc: doctrine in text, no reader where it binds.
2. The gauges were read once (the 08-10 review said "dead, drop 31 GB, consider retiring vis-compare") and not acted on. The suite instruments itself better than anything else you own and the instrument is unread.
3. The two lanes with a real job (vision and code) each lack exactly one mechanical link. Vision: nothing captures or re-renders, so the L3 loop can only run where the re-render is scripted (imagegen, which nobody needs). Code: nothing writes the judge before dispatch, so the one proven pattern (scoped worker under a judge, 33/33) costs more to set up than doing the edit in cloud.

The owner's own tension, from the estate audit, sits underneath: "never halt" plus "trust nothing the agent says it verified". The local lanes are the cheapest possible verifier seat, which is why the vision loop is the lane worth building: it is the mechanical "read the whole frame before claiming done" that the 10x S3 UI rule wants and cannot enforce in text.

## 3. Per lane

### 3.1 Vision + the UI driver loop (the one to build)

Attempted: three layers with strict roles; L1 extractors adversarially validated twice; `--ocr` at 340 ms exact; `--ui` routed to the 26B model because minicpm-v misread selected states; `ax tree` wired into `ui-verify --app`; `vis-ledger` computing fixed/persisting/regressed as set differences; four judge skills.

Gap: no capture, no re-render, no history for the AX path, `--ui` at 20 to 43 s per read, judge skills mostly unlogged, the "whole frame first" rule binds nowhere mechanically. L3 ran end to end once, on imagegen.

Ideal loop, agent-driven, dumb tools in every mechanical seat:

```
target (URL | app | image pair) + claims or reference
  0 capture   web: chrome-devtools/playwright, settle heuristic, viewport recorded
              native: ax tree (exact) + screencapture only when pixels matter
  1 measure   see --ui --json · see --ocr · see diff --json · ax --json · e8
  2 judge     Claude: /ui-gripe | /vis-compare | /ui-categorical-check | ui-verify
              gate: verdict must cite the full-frame inventory, not just the claim
  3 ledger    vis-ledger ingests {id, class, status} from any judge
  4 fix       Claude edits code
  5 reshoot   replay the step-0 recipe into the same loop dir; comparability gate
  6 loop      stop on policy-pass / stall, signals unchanged
```

Bridge, ordered: log the four judge skills and add a caller field to see-history (1 h) · `see reshoot <loop-dir>` recipe replay (1 day) · generalise vis-ledger ingest to `{id, class, status}` so ui-verify and ui-gripe findings loop (1 day) · a web capture wrapper writing into `outputs/see/` (1 week) · a $0 element-box detector (OmniParser-class, AGPL to review) as a second L1 extractor beside the VLM inventory (prototype) · a faster `--ui` model only after a bake-off on the existing i-dream ground-truth fixture (Qwen3-VL via MLX-VLM since Ollama #16264 is still open; Moondream 3 for grounding).

### 3.2 Local code model

Attempted: MoE-first tier, a 9-item judgment probe, fleet fan-out under a Judge, `lm opencode` with auto-lease, one experiment where the 35B re-implemented a real change 33/33 in 35 s.

Gap: no dispatch point; the probe's human verdicts never filled; fleet never ran the code tier; opencode unlogged; the code tier ignores Ollama's format constraint; the named 80B candidate never pulled; efficacy unproven beyond n=1.

Ideal: a skill (a `/bloop` mode or `/dispatch-local`) that refuses unless a judge exists and is red, restates the judge contract verbatim in the prompt, calls `lm fleet` or `q -m code`, applies the patch itself, re-runs the judge, escalates to cloud on the second red, and logs a `code-dispatch` intent so self-audit can see it.

Bridge: score the 4 probe runs by hand (30 min) · a `code-dispatch` fleet intent and opencode session log (1 h) · the skill above (1 day) · 5 to 10 E1-style runs on varied real tasks before calling the seat cleared (measurement) · pull and probe Qwen3-Coder-Next 80B-A3B at Q4_K_M (~52 GB, nothing else warm; a decision for you) · a Qwen3.x MTP probe on the MLX runner, which is a different mechanism from the draft-model spec-dec docs/05 rejected.

### 3.3 `lm gemini`

Attempted: a wrapper that pins the model, isolates the key, keeps per-project UUID sessions with self-heal, hard-kills hangs, and returns structured failure classes. Auth moved to API key on 07-07, which is why the 06-18 shutdown of the hosted consumer CLI did not touch it.

Gap: 61% of calls are stateless one-shots; ingest was used by two projects ever; the two real workloads (batch transcript classification, web lookups) are hand-typed with the whole prompt re-embedded; 180 s timeout kills the exact workloads that need the lane; `--output-format json` never used, so a prose contract is regex-trimmed instead; "Claude verifies" has no mechanism; no token counts logged; the Homebrew formula EOLs 2026-12-18; the key's Standard-vs-auth status is unverified against the September cutover.

Ideal: `lm gemini digest <target> --schema <intent>` returning `{claims, sources}` with a grep-back verification stub, called from `/pyramid-sweep`'s mining phase; `lm gemini research "q"` with a 300 s+ default and a null-when-unsure JSON contract for the web-lookup shape; batch mode for the classification workload.

Bridge: raise the default timeout to 300 s and document it (10 min) · JSON output passthrough (1 h) · token/byte logging (1 h) · verification stub (half day) · pyramid-sweep wiring (1 day) · check the key type before September (you).

### 3.4 Image generation

Attempted: a good tool (registry, preflight, enhance, critique, seed-locked refine) and a convergence loop that worked once.

Finding: 18 runs ever, none in 48 days, none of the outputs used anywhere in ~/Code or ~/.claude; every one of the 1,986 raster images in Versable came from elsewhere; `/svg` owns the real asset demand; qwen at 2.5 to 8 min per image; hosted APIs would have cost under $1 for the whole history. Your own stated preference (parse now, not recall) cuts against it.

Recommendation: trash schnell now (31 GB, already ruled 08-10), keep qwen and the skill as a thin wrapper, no more investment in the loop until a caller exists; re-audit in six weeks and drop qwen too if still zero. If a real raster need appears, FLUX.2 Klein 4B or Z-Image-Turbo at roughly 10 to 15 s per image on this machine replaces qwen, not more loop machinery.

### 3.5 Performance and running it

Measured (p50/p95): warm companion 0.7 s / 4.8 s with a 142 s cold-load outlier; `gemma4:26b` 3.4 s / 21 s; code tier 17 s / 51 s; `see --ui` 20 s / 43 s; OCR 0.34 s; gemini 9 s / 109 s; imagine-qwen 248 s / 478 s. Memory: 63 GB of Ollama models on disk, resident ceiling ~29 GB under `MAX_LOADED_MODELS=2`, nothing resident right now.

Broken: both warm jobs fail on `ollama: command not found` because `bin/warm` calls bare `ollama` and launchd's PATH lacks `/opt/homebrew/bin`; warm-evening-off has exited 127 every run for 8 weeks; warm-morning's plist was deleted around 08-05 after 21 identical failures; STATE.md still lists it live. The no-idle rule is satisfied by accident and the snappy-companion promise is not delivered: first `q` of every session pays a cold load.

Unmeasured: MTP on the MLX runner (Ollama is now 0.33.0; the repo's numbers are from 0.30.10); `OLLAMA_NUM_PARALLEL` (unset, so fleet's `-j 2` fans out processes against a serialising server); KV q4; per-intent `num_ctx`; cold-vs-warm tagging in the histories; native `mlx_lm.server` vs Ollama-MLX for the code tier (web claims of 3x are single-source and on different hardware).

Bridge: PATH fix at one choke point in `bin/_lib.sh` plus re-register warm-morning (10 min) · a launchd health line in the weekly self-audit (10 min) · STATE.md correction (5 min) · `resident_before_call` field in the histories (1 h) · three measurement sessions with `lm probe` as the gate: MTP on gemma4 first then qwen, NUM_PARALLEL 1 vs 2, mlx_lm.server side by side.

## 4. Cross-cutting: models, tools, skills, agent involvement

Models worth a bake-off on this machine, each gated by the existing probe or ground-truth fixture, never adopted on a blog number:

| role | candidate | why | risk |
|---|---|---|---|
| code tier | Qwen3-Coder-Next 80B-A3B Q4_K_M | your named efficacy candidate; SWE-bench Verified ~70%+ | ~52 GB, nothing else warm; no Mac tok/s number exists |
| UI grounding | Qwen3-VL 8B or 30B-A3B via MLX-VLM; Moondream 3 | GUI grounding built in; 2B-active MoE | Ollama path crashes (#16264 open); MLX-VLM is a second runtime |
| element boxes | OmniParser v2 (July 2026 detector) | deterministic boxes beside the VLM prose | AGPL half needs review |
| OCR | MiniCPM-V 4.5 | matches the repo's own verbatim-fidelity finding | none |
| long context fallback | gemma4:26b, Qwen3.6/3.8-27B at 256k | $0 fallback when gemini is unavailable | 17 GB resident |
| imagegen, if ever | FLUX.2 Klein 4B, Z-Image-Turbo | 10 to 20x faster than qwen | no demand |

Tools: chrome-devtools or playwright MCP as the capture driver (already installed, never wired into `lm`); `ax` 0.3.0 (installed, unlogged); pixelmatch/odiff only if screenshot volume grows; Satori for OG images instead of diffusion.

Custom skills that would give the lanes a caller: `/dispatch-local` (code, judge-first) · `see reshoot` + a `/ui-loop` driver that runs steps 0 to 6 above · `/pyramid-sweep` mining phase on `lm gemini digest` · the four judge skills logging their runs.

Agent involvement in driving the dumb tools: the correct division already exists in every SKILL.md (scripts measure, Claude judges). What is missing is the agent driving the mechanical steps around the judgment (capture, re-render, apply, re-measure) through one verb each instead of composing shell by hand each round. That is the whole plan for the vision lane and most of it for code.

## 5. What this asks of you

Defaults applied unless you say otherwise: trash schnell; keep qwen and `imagine` as-is; fix the PATH trap and re-register warm-morning; raise the gemini timeout; log the judge skills; score the probe runs by hand comes to you as a 30-minute task.

Open picks, on the decision page: which lane goes first (my pick: vision loop, then perf fixes, then code dispatch, then gemini wiring); whether to pull the 80B coder (52 GB, a day of probing); whether to spend a measurement session on MTP and mlx_lm.server now or after the vision loop; whether to drop qwen-image too (49 GB) now rather than in six weeks.

## 6. Uncertainties

Whether `lm opencode` or `asset-verify`/`findings-gate`/E8 were ever used (no history streams). Whether the Gemini key is a Standard key at risk in September. Whether Ollama 0.33.0's MLX runner changes the 0.30.10 numbers for an A3B MoE. Any Mac tok/s for the 80B coder. Whether the Aug-10 review's "0 compare runs" counted skill-log rows rather than history rows. Real accuracy of Qwen3-VL, Moondream 3, OmniParser on this repo's fixtures, which only a local bake-off answers.
