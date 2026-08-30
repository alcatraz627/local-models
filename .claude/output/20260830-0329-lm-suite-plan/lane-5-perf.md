# Lane 5 -- Performance and Operations

Read-only research pass over `/Users/alcatraz627/Code/local-models`, 2026-08-30. All local
claims cite file:line or a command actually run this session; web claims are dated and marked
UNVERIFIED where a single source could not be corroborated.

## 1. Measured performance today (from the histories)

Computed from `logs/{q,see,fleet,gem,compare}-history.jsonl` and `outputs/imagine-history.jsonl`
(2,714 records total) via a one-off read-only Python pass, p50/p95 by `model`:

| stream | model | n | p50 | p95 | min | max |
|---|---|---|---|---|---|---|
| q | gemma4-e4b-warm | 1385 | 711 ms | 4,835 ms | 0 | 142,097 ms |
| q | gemma4:26b | 773 | 3,384 ms | 20,924 ms | 0 | 38,687 ms |
| q | qwen2.5-coder:3b | 36 | 854 ms | 3,376 ms | 0 | 6,477 ms |
| q | qwen3.6:35b-a3b | 24 | 16,802 ms | 51,413 ms | 4,998 | 59,717 ms |
| q | qwen3-coder-next:q4_K_M | 1 | 81,724 ms | n/a | n/a | n/a |
| see | gemma4:26b (the UI-inventory route) | 93 | 20,351 ms | 42,507 ms | 17 | 154,370 ms |
| see | apple-vision (`--ocr`, no model) | 71 | 340 ms | 779 ms | 147 | 1,151 ms |
| see | minicpm-v | 49 | 6,756 ms | 13,305 ms | 1,569 | 39,224 ms |
| gemini | gemini-3.5-flash | 197 | 9,000 ms | 109,000 ms | 0 | 289,000 ms |
| imagine | schnell | 9 | 31,000 ms | 33,000 ms | 13,000 | 46,000 ms |
| imagine | qwen (the pinned default, `config.sh:25`) | 9 | 248,000 ms | 478,000 ms | 143,000 | 553,000 ms |

`fleet-history.jsonl` (27 rows) and `compare-history.jsonl` (30 rows) do not carry per-model `ms`.
Fleet records `wall_s` per batch run, for example `{"model":"qwen2.5-coder:3b","items":1,"wall_s":2}`
(`logs/fleet-history.jsonl:1`). Compare records `wall_ms`/`extractors_ms` for the $0 evidence pack
(`logs/compare-history.jsonl:1`), roughly 6 to 10 seconds per pair, mostly the L2 judge call rather
than the extractors: `extractors_ms` is 9 to 14 ms.

Read the spread, not just the median. The warm companion's own p50 (711 ms) looks snappy, but its
max (142 s) and the `gemma4:26b` p95 (20.9 s) show cold-load events mixed into the same series. The
histories do not currently tag cold vs warm calls, so a per-call residency flag would turn this
ambiguity into a measured number (Sections 4 and 6).

The repo's own MLX-vs-llama.cpp measurement (`docs/05-perf-levers-and-usage-audit.md:21-42`,
2026-07-07, Ollama 0.30.10, `qwen3.6:35b-a3b-nvfp4` MLX vs the same model Q4_K_M llama.cpp/Metal,
1254-token prompt, 400-token gen):

| | Q4_K_M via llama.cpp | NVFP4 via MLX |
|---|---|---|
| cold load | 15.4 s | 4.9 s (3.2x) |
| prefill | 1,291 tok/s | 931 tok/s (-28%) |
| decode | 64-68 tok/s | ~70 tok/s (+5 to +9%) |

Decision recorded there: kept `CODE_MODEL` on Q4_K_M because the fleet/review workload is
prefill-heavy and lease-amortized, and the NVFP4 re-quant showed a judgment-terseness regression
under the probe (`probe/runs/qwen3.6_35b-a3b-nvfp4-20260707-131716.md`, cited in the doc). No
probe run file in `probe/runs/` carries an explicit tok/s field; `rg tok/s probe/runs/*.md`
returned nothing. The tok/s numbers above are the only ones in the repo, all from the one
2026-07-07 session, none since.

## 2. Memory and what fits

`ollama list` (run this session): 7 models on disk, largest three are `qwen3.6:35b-a3b` (23 GB),
`gemma4:26b` (17 GB), `gemma4-e4b-warm`/`gemma4:e4b-it-qat` (6.1 GB each), roughly 63 GB total on
disk, under the 64 GB unified memory (`sysctl hw.memsize` = 68,719,476,736 bytes = 64 GiB;
`system_profiler SPHardwareDataType`: Apple M5 Pro, 18 cores by the profiler's own count, 64 GB).
`MAX_LOADED_MODELS=2` (`bin/lm-serve:15`) caps concurrent residency to the warm companion (6.1 GB)
plus one big tier, either `gemma4:26b` (17 GB) or `qwen3.6:35b-a3b` (23 GB), for a resident ceiling
around 23 to 29 GB, leaving 35 to 40 GB for macOS, a Claude Code session, and anything else
running. `ollama ps` (run this session) currently shows nothing resident. The server is up
(`launchctl print` confirms `state = running`, pid 14644) but no model is loaded, consistent with
the companion no longer being kept warm (Section 3).

Image weights (`imagine`, mflux/MLX Flux) live on disk in the HF cache, not evaluated here. They
are load-per-invocation, not resident, so they do not compete with the Ollama residency budget.

## 3. Residency and idle-penalty compliance: the schedule is broken, and one leg is dead

This is the headline operational finding.

**`warm-evening-off` (daily 19:00, `off all` backstop) fails every run with exit 127.**
`launchctl print gui/501/com.alcatraz.warm-evening-off` (run this session): `last exit code = 127`.
`launchctl list` (run this session): `-  127  com.alcatraz.warm-evening-off`. The script
(`~/.claude/scheduled/warm-evening-off/script.sh:9`) runs
`bash -c "/Users/alcatraz627/Code/local-models/bin/warm off all"`. Root cause, confirmed directly:
`bin/warm:47` and its neighbors call bare `ollama ps` / `ollama stop`
(`bin/warm:47,53,55,60,62,65`), and `which ollama` (run this session) resolves to
`/opt/homebrew/bin/ollama`, a path not in launchd's default environment (`launchctl print` for the
same job: `default environment = { PATH => /usr/bin:/bin:/usr/sbin:/sbin }`).
`~/.claude/logs/launchd/warm-morning.err.log` (read this session) shows the exact failure text, 21
identical lines: `/Users/alcatraz627/Code/local-models/bin/warm: line 47: ollama: command not
found`. Two independent sources agree on the mechanism: STATE.md's own note (`docs/STATE.md:38`,
"the shutdown backstop") and this session's direct reproduction of the log trail.

`out.log` for `warm-evening-off` (read this session, 30 daily lines through 2026-08-29) shows only
`"running scheduled command (daily)"` with no further output. The script's `set -uo pipefail`
without `-e` means the `ollama` failures inside `bin/warm` do not halt the wrapper, so which exit
code survives to the script's own `rc=$?` depends on which internal call fails last. Either way,
`off all` never actually executes `ollama stop`. Net effect: the 2026-07-07 "shutdown backstop"
(`docs/STATE.md:38`) has been silently inert since it was created, for its entire 8-week life
through today.

**`warm-morning` (weekdays 09:30, pin the companion) is not merely broken. It no longer exists.**
`launchctl print gui/501/com.alcatraz.warm-morning` (run this session): `Could not find service
"com.alcatraz.warm-morning" in domain for user gui: 501`. `ls ~/Library/LaunchAgents/` (run this
session, 48 entries) has no `com.alcatraz.warm-morning.plist`. Only `local-models-ollama`,
`warm-evening-off`, and `lm-self-audit` remain from this project's launchd footprint. Its log
files still exist and tell the story: `~/.claude/logs/launchd/warm-morning.out.log` (read this
session) runs daily from 2026-07-08 through 2026-08-05 and then stops, no entries for the following
25 days through today, 2026-08-30. `warm-morning.err.log` (read this session) is 21 lines of the
identical `ollama: command not found` at `bin/warm:47`, one per failed run. The job was evidently
disabled or its plist removed around 2026-08-05/06, most plausibly because it never worked (every
run failed the same way as `warm-evening-off`) and someone, human or a prior session, unloaded it
rather than fixing the PATH. `docs/STATE.md:38-39` still documents it as live ("Scheduled warmth:
`warm-morning` (weekdays 09:30) plus `warm-evening-off`..."), which is now stale by 25 days.

**Net operational state, as of this session:** the "no idle penalty" rule (`CLAUDE.md` hard rule
#1) is trivially satisfied right now, because nothing is resident and nothing has successfully
pinned anything since early August. But the companion's "snappy by default" promise
(`docs/STATE.md:35`, plain `q` implicitly warm) is not being delivered: every session's first `q`
call pays a cold load unless a human runs `warm on` by hand that session. The q-history max of
142,097 ms (Section 1) is very plausibly one such cold-load-plus-swap event on a machine also
running Claude Code and other pm2 services.

**`lm-self-audit` (weekly, Sun 11:00) is still correctly wired.** It shells to
`bash /Users/alcatraz627/Code/local-models/scripts/self-audit.sh`, an absolute path to `bash`
itself rather than a bare `ollama`/`warm` invocation, so it does not hit the same PATH trap.
History files exist through `logs/self-audit/20260823.md` (last Sunday before this session); no
`20260830.md` yet, because today's run (Sun 11:00) had not fired at the time of this read (session
ran around 03:30). The 2026-08-23 digest (read this session) shows low volume: 3 `q` calls, 2
`see`, 0 fleet, 26 gemini calls with 6 failures (timeouts). A useful low-cost health signal that is
itself working, in contrast to the warm schedule.

No health alert exists for a failing LaunchAgent. Nothing pages or surfaces the 127s; they sit
silently in `.err.log` files that only a human, or this audit, reads.

## 4. What was attempted (context for the gap list)

- The perf-lever audit (`docs/05-perf-levers-and-usage-audit.md`) ranked MLX first, verified it
  format-routes rather than being a flag (Section 1 above), and made a measured, non-default call
  to keep Q4_K_M/llama.cpp for the code tier. A real ROI decision, not cargo-culting a library
  switch.
- KV/flash-attn: `OLLAMA_FLASH_ATTENTION=1` plus `OLLAMA_KV_CACHE_TYPE=q8_0` are baked into
  `bin/lm-serve:17-19`, verified by the server log per the comment there (not re-verified this
  session; read-only, no server restart performed).
- MoE-first model choice (`config.sh:6-11`) is deliberate for this 307 GB/s-bandwidth machine.
  Active-parameter count, not total size, is the throughput driver, and the tier comments say so.
- MTP measurement is flagged pending (`docs/STATE.md:196-200`) with an explicit counter-finding
  already on record: draft-model speculative decoding regresses on llama.cpp/Metal, so it must
  never be turned on for the GGUF-backed code tier even if MTP pans out elsewhere. That caution is
  echoed in `docs/04-ollama-vs-llamacpp-decision.md:34` ("MoE-A3B gains little from spec-decode").
- The weekly self-audit cron (`scripts/self-audit.sh`, gcc-schedule `lm-self-audit`) is the one
  feedback loop that is actually running and producing digests.

## 5. Gaps

**Unmeasured performance levers**
- MTP / speculative decoding on the MLX path specifically, not the GGUF/llama.cpp path, which is
  already ruled out. `docs/STATE.md:196-200` names this as the single open measurement task.
- KV-cache quantization levels beyond q8_0 (q4?) are untested; no doc mentions a q4 KV trial.
- Batch/concurrency (`OLLAMA_NUM_PARALLEL`) is not set anywhere found in `config.sh` or
  `bin/lm-serve`, so it defaults to 1: every local call to a given resident model serializes.
  `lm fleet`'s "concurrency-capped" fan-out (`docs/STATE.md:22`) is therefore fanning out
  processes, not necessarily getting parallel decode from one model instance. Worth confirming
  whether fleet's concurrency cap already accounts for this or is leaving throughput on the table.
- Prompt caching across `q` calls, Ollama's own prefix/prompt-cache behavior (distinct from the
  `see diff`/compare content-addressed cache, an already-built mechanism per `docs/STATE.md:129`),
  is not discussed anywhere in the repo's docs.
- Default `num_ctx` per intent was not audited this session; KV grows linearly with it
  (`docs/05:44`), so an oversized default on any intent is a silent tax.

**Operational**
- No health check or alert on LaunchAgent failure. The two `warm-*` jobs have been silently broken
  (one for its entire life, one for 25 of its roughly 29 days) with zero surfaced signal. `lm
  doctor` / `lm status` (mentioned in `docs/STATE.md:27`) were not run this session (read-only
  scope), but even if they report residency correctly, neither is scheduled to catch a launchd job
  silently failing. The self-audit digest audits the histories, not the schedules.
- The PATH trap is a repo-wide launchd hazard, not a one-off. Any future gcc-schedule job that
  calls `bin/warm`, `bin/lm-serve`, or anything invoking `ollama`/`hf`/other Homebrew tools
  directly (rather than via an absolute path, the way `lm-self-audit`'s wrapper happens to dodge
  it) will hit the same exit-127 failure mode. The fix belongs at one shared point, not per-script
  (see Section 6).
- No per-call cost/energy record. Nothing in the histories tracks watts, thermal state, or battery
  vs AC.
- No cold-start telemetry. The histories record wall-clock `ms` but not whether the call is a cold
  load, a warm hit, or a lease in flight. Section 1's 142-second outlier is unexplained without it.

**Doctrine vs reality**
- The CLAUDE.md hard rule ("no idle penalty ... a tool that silently keeps 23 GB warm is a bug")
  is being met only by accident right now, not by the warm/lease mechanism working, but by the
  mechanism being broken in the safe direction: nothing pins, so nothing idles. The design intent
  was a deliberate snappy companion plus bounded leases (`docs/STATE.md:35-39`); what is actually
  running is neither idle-penalty-free by design nor snappy by delivery. It happens to land on the
  compliant side of one rule while silently failing the other stated goal.

## 6. What "no idle penalty, instant when needed" looks like mechanically

The doctrine already describes the target correctly (`CLAUDE.md`: "nothing stays resident unless
explicitly pinned or leased"; `docs/STATE.md:35-37`: forever-pin companion plus bounded leases).
The gap is entirely in the supervision layer, not the design:

1. A tiny always-warm companion (`gemma4-e4b-warm`, 6.1 GB, `WARM_KEEP_ALIVE=-1` per
   `config.sh:15`), pinned once at login and re-pinned if it ever drops. This is what
   `warm-morning` was for and is currently not doing.
2. Bounded leases for big tiers, already built (`warm on code [ttl]`, self-healing TTL, `bin/warm`
   header comment) and already used by `lm fleet` / `lm opencode` automatically per
   `docs/STATE.md:37`. This half of the design is sound and does not need a schedule at all, since
   the TTL self-heals without a cron.
3. A hard-off backstop at day's end (`warm-evening-off`) so nothing survives an accidental
   `warm on --forever` past the session. Currently the piece that has been silently dead 8 weeks.
4. Telemetry that proves it. The histories already carry `ms` per call (Section 1); adding a
   `resident_before_call` boolean (read from `ollama ps` at call time, one extra `_lib.sh` check)
   would let `lm doctor`/`self-audit` report a cold-load rate directly, instead of this session
   having to infer it from outlier `ms` values.

## 7. Bridge: smallest changes first

**10-minute fixes**
- Fix the PATH trap once, at the shared choke point. Either add
  `OLLAMA=/opt/homebrew/bin/ollama` (or the output of `brew --prefix`) as a variable in
  `bin/_lib.sh` and use it everywhere `bin/warm` currently calls bare `ollama`, or prepend
  `export PATH="/opt/homebrew/bin:$PATH"` at the top of `bin/warm` (and any other `bin/*` script a
  LaunchAgent invokes directly) before it sources `_lib.sh`/`config.sh`. The second option is
  smaller-diff and matches what `lm-self-audit`'s wrapper accidentally gets right by invoking
  `bash /abs/path`. This single fix repairs both `warm-evening-off` and, once its plist is
  restored, `warm-morning`.
- Re-register `warm-morning`. The plist is gone from `~/Library/LaunchAgents/`; if kept, it needs
  recreating (gcc-schedule) after the PATH fix above, or it will fail silently again.
- Add a health-check line to the weekly self-audit (or a cheap standalone check): `launchctl list |
  grep -E 'warm-(morning|evening-off)'` and flag any non-zero last-exit-status. This turns the next
  PATH-class regression into a digest line instead of a silent 8-week outage.
- Update `docs/STATE.md:38-39` to stop asserting `warm-morning` is live. It has not run since
  2026-08-05.

**Measurement sessions (not code changes, need dedicated time plus `lm probe` afterward)**
- MTP on the MLX path: `docs/STATE.md:197-198`'s own next step. Check `ollama show` / the server
  log for MTP surface on the currently-installed Ollama build, then measure with the existing
  probe harness before trusting any throughput claim, per the repo's own "trust equals a passing
  gate" rule.
- `OLLAMA_NUM_PARALLEL` trial: measure `lm fleet` throughput at `NUM_PARALLEL=1` (today's implicit
  default) vs `2`, on the same intent/model, watching memory headroom (KV cache scales with
  `NUM_PARALLEL` times `num_ctx`, per the concurrency finding in Section 9). Cheap to try,
  currently untried.
- A raw `mlx_lm.server` or `vllm-mlx` side-by-side against Ollama-MLX on `qwen3.6:35b-a3b`, given
  the web-research gap in Sections 8 to 9 below (native MLX runtimes reportedly beat Ollama's
  in-process MLX runner by a wide margin). Worth confirming on this exact model and machine before
  adopting, since the adapter cost is real: `docs/05:47-48` notes the OpenAI-`/v1` vs
  Ollama-`/api/chat` protocol mismatch would need a shim in `_lib.sh`.

**Re-architecture (park until the above two tiers are done)**
- A per-call `resident_before_call` telemetry field, and a cold-start dashboard in `lm doctor`.
- If the MLX-vs-Ollama-MLX gap in Section 9 replicates on this machine, a protocol-adapter layer to
  run `mlx_lm.server`/`vllm-mlx` alongside Ollama for the code tier specifically, gated behind the
  same probe-based trust bar the repo already applies to every model swap.

---

## 8. External research: Ollama on Apple Silicon, MLX vs native runtimes (2026-08-30)

Ollama's MLX integration has moved fast since the repo's own 2026-07-07 measurement, and the newer
web claims are more favorable to Ollama-MLX than the repo's own number. This is a live tension the
repo should re-measure, not assume. Two independent write-ups (dated April to May 2026, UNVERIFIED
against Ollama's own release notes, which were not fetched this session) describe Ollama v0.30
(dated "May 13, 2026" by one source) promoting the MLX engine to the default Apple Silicon path,
citing "93% faster decode" and Gemma-4 MTP speculative decoding at "over 2x" on Macs, plus better
KV-cache reuse for repeated prompts
([runaihome.com, "Ollama v0.30 on Apple Silicon"](https://runaihome.com/blog/ollama-v030-mlx-stable-upgrade-2026/);
[runaihome.com, "Ollama MLX on Apple Silicon in 2026"](https://runaihome.com/blog/ollama-mlx-apple-silicon-2026/)).
These are secondary blog sources, not Ollama's own changelog. Treat the specific percentages as
directional, not load-bearing, until cross-checked against `ollama --version` / release notes on
this machine. The repo's own 2026-07-07 measurement was on Ollama 0.30.10 and already found MLX
format-routing working (`docs/05-perf-levers-and-usage-audit.md:22-24`). If these blog claims
describe the same 0.30-series MLX integration, the repo's own qwen3.6-a3b measurement (MLX 5 to 9%
faster decode, 28% slower prefill) is the more trustworthy number for this specific model class (a
MoE model with roughly 3B active params). The cited "93% faster decode" claim is unscoped to model
family and may be dominated by dense-model or Gemma-4-MTP-specific gains that do not transfer to an
A3B MoE. This needs a re-run, not a re-read, given how fast the ecosystem is moving.

Native MLX runtimes (mlx-lm, vllm-mlx) reportedly beat Ollama's in-process MLX runner by a much
larger margin than Ollama-MLX beats Ollama-llama.cpp. One source (dated 2026, specific date not
visible in the search snippet, UNVERIFIED) reports raw `mlx-lm` at 130 tok/s vs Ollama's
llama.cpp-backend 43.5 tok/s on Qwen3.5-35B-A3B on an M4 Max 128 GB, roughly 3x
([groundy.com](https://groundy.com/articles/mlx-vs-llamacpp-on-apple-silicon-which-runtime-to-use-for-local-llm-inference/)),
corroborated in shape, not in the exact figure, by a second source claiming `vllm-mlx` reaches "up
to 525 tok/s" on Qwen3-0.6B and beats both mlx-lm and llama.cpp across sizes tested, with the
MLX-vs-llama.cpp gap narrowing to near-zero above roughly 27B dense params because inference
becomes memory-bandwidth-bound rather than compute-bound
([yage.ai, "MLX vs llama.cpp on Apple Silicon"](https://yage.ai/share/mlx-apple-silicon-en-20260331.html),
dated 2026-03-31). The two numbers (Ollama-MLX "93% faster decode" vs raw-mlx-lm "3x Ollama") are
not directly comparable: one compares Ollama's two internal backends, the other compares Ollama
(any backend) to a standalone runtime. But together they suggest Ollama's in-process MLX runner,
even when engaged, leaves real throughput on the table relative to `mlx_lm.server` or `vllm-mlx`
directly. This matches `docs/05:45-48`'s already-identified "full MLX serving" lever 3, which the
repo marked dead only because `OLLAMA_USE_MLX` did not exist as a flag. The underlying option
(running `mlx_lm.server` or `vllm-mlx` alongside Ollama, behind a protocol adapter) was never
actually re-evaluated after MLX shipped natively, and this research suggests it still has headroom.
Source model-size note: the sample cited (Qwen3.5-35B-A3B, roughly 3B active) is close enough to
this repo's `qwen3.6:35b-a3b` (same shape) to be a meaningfully relevant comparison, not just an
analogous one. Worth a direct repro before trusting the 3x figure.

## 9. External research: speculative decoding / MTP, and operational sidecar patterns (2026-08-30)

MTP-style speculative decoding on Ollama's MLX path (Gemma-4-specific) is reported real and large;
general EAGLE/Medusa-style decoding for Qwen3.x on MLX is not clearly available yet. The same
runaihome.com sources report "Gemma 4 MTP speculative decoding (>2x speedup on Macs)" as part of
the Ollama v0.30 MLX promotion, but this is scoped to the Gemma-4 model family specifically
(multi-token-prediction draft heads trained into that model), not a general Qwen3 capability.
Separate academic search results on EAGLE-3/Medusa (dated through mid-2026, all arXiv preprints,
UNVERIFIED for production availability) describe strong GPU-cluster speedups (3 to 6.5x on H100)
for LLaMA/Qwen/DeepSeek architectures, but none of the results found this session describe an
EAGLE/Medusa draft-head implementation shipped for Qwen3.x specifically on MLX/Apple Silicon. The
research area is active but the tooling gap, a trained draft model or head for this repo's exact
`qwen3.6:35b-a3b`, was not closed by anything surfaced in this search. This is consistent with the
repo's own stance (`docs/STATE.md:199-200`): draft-model speculative decoding on llama.cpp/Metal
already measured as a regression for A3B MoE, and MTP remains an open, Gemma-biased question rather
than a settled Qwen win. Recommendation: the MTP measurement session should target `gemma4:26b` (or
whichever Gemma tier is in use) first, where the vendor claim is model-specific and plausible, and
treat a Qwen3.6 MTP win as unproven until directly tested. Do not generalize the Gemma result onto
the code tier.

Ollama concurrency (`OLLAMA_NUM_PARALLEL`) defaults to 1, one request at a time per loaded model,
and every additional parallel slot needs its own KV cache, so memory scales as `NUM_PARALLEL` times
context length
([ssdnodes.com](https://www.ssdnodes.com/learn/ollama-num-parallel-and-max-queue)),
corroborated by [glukhov.org](https://www.glukhov.org/llm-performance/ollama/how-ollama-handles-parallel-requests/),
undated but describing the same mechanism: same-model concurrent requests get batched, and overflow
queues FIFO up to `OLLAMA_MAX_QUEUE` (default 512). One source's own benchmark (undated, UNVERIFIED)
claims a 20 to 40% latency increase per request at `NUM_PARALLEL=4` under full load, with 3 to 4x
total throughput, a real tradeoff, not a free lunch, and directly relevant to whether `lm fleet`'s
"concurrency-capped fan-out" (`docs/STATE.md:22`) is currently exploiting or ignoring this knob
(Section 5 flags this as unverified in-repo).

No source found describes a project matching this repo's exact shape: a local-model CLI sidecar
specifically supervising warm/cold state for Claude Code. The closest matches are generic "run
Claude Code against Ollama" guides describing Ollama's new native Anthropic-Messages-API endpoint
(reported shipped "January 2026" in `v0.14.0`, and an `ollama launch` convenience command for
pointing coding tools at local models, both UNVERIFIED, single-source, and from a listicle-style
outlet). These solve a different problem, routing Claude Code's own inference to a local model,
than this repo's actual design (a companion CLI suite Claude Code calls out to), so they are not
directly transferable. The PATH-supervision problem itself (Sections 3, 6, 7) is a generic macOS
launchd pattern with well-documented fixes independent of the Ollama-specific research
([riaf gist](https://gist.github.com/riaf/cf662d965ebd1b8b47453dd79cdd5578);
[Bits By Me, "launchd PATH whack-a-mole"](https://bitsby.me/til/2026-04-04/launchd-path-whack-a-mole/),
2026-04-04). Both agree the fix is either an explicit `EnvironmentVariables` PATH block in the
plist, or sourcing the shell environment inside the invoked script. Both also warn that `brew
services restart` regenerates a Homebrew-managed plist and wipes manual `EnvironmentVariables`
edits, which does not apply here since these are hand-authored plists, not brew-managed ones.

Thermal/energy: one source (dated 2026, specific outlet not clearly attributable in the search
snippet, UNVERIFIED) reports the base M5 MacBook Air (fanless) thermal-throttles measurably more
than the M5 Pro/MacBook Pro (active cooling) under sustained compute load. Not directly applicable
since this machine is confirmed M5 Pro (actively cooled) via `system_profiler`, but worth knowing
the fanless-Air tier would behave differently if this suite is ever run there.

## 10. Uncertainties

- Whether the repo's 2026-07-07 MLX measurement and the web-reported "Ollama v0.30 MLX promotion,
  93% faster decode" describe the same Ollama release is not confirmed. `ollama --version` on this
  machine was not checked this session (read-only scope covered `ollama list`/`ps`, not `version`).
- The exact date and authority of the "Ollama v0.30 ... May 13, 2026" claim: sourced from a
  secondary blog, not Ollama's own release notes/GitHub. Treat as directional.
- Whether `lm fleet`'s concurrency cap already sets `OLLAMA_NUM_PARALLEL` or relies on the default
  of 1 was not found in `config.sh`/`bin/lm-serve`, but `lib/fleet` internals were not read this
  session (outside the explicitly listed file set). Worth a direct grep before acting on Section
  5's flag.
- Whether `warm-morning`'s plist removal was deliberate (a human decision) or an artifact of some
  other cleanup (for example a gcc-schedule retirement flow) is unknown. The WAL/session history
  that would answer this was not in scope for this lane.
- The 142,097 ms max q-history outlier (Section 1) is plausibly a cold-load-plus-swap event, but
  not confirmed against a specific timestamp/process trace.
- Raw mlx-lm "130 tok/s vs Ollama 43.5 tok/s" figure (Section 8): a single search-synthesized
  citation, on hardware different from this machine (M4 Max 128 GB vs this M5 Pro 64 GB), and the
  total-vs-active parameter framing was not independently re-derived. Treat as a strong directional
  signal to re-measure locally, not a number to plan around.

## 11. Source table

| # | Source | Date | Corroboration |
|---|---|---|---|
| local | `docs/STATE.md`, `docs/05-perf-levers-and-usage-audit.md`, `docs/04-ollama-vs-llamacpp-decision.md`, `config.sh`, `bin/lm-serve`, `bin/warm`, `logs/*.jsonl`, `outputs/imagine-history.jsonl`, `probe/runs/*.md`, `logs/self-audit/20260823.md`, `~/Library/LaunchAgents/*.plist`, `~/.claude/scheduled/{warm-evening-off,lm-self-audit}/script.sh`, `~/.claude/logs/launchd/{warm-morning,warm-evening-off}.{out,err}.log` | as of 2026-08-30 session | direct read/run this session |
| local | `launchctl print`, `launchctl list`, `ollama list`, `ollama ps`, `pm2 list`, `sysctl hw.memsize`, `system_profiler SPHardwareDataType`, `which ollama` | 2026-08-30 around 03:30 | direct run this session |
| web | [runaihome.com, Ollama v0.30 MLX stable](https://runaihome.com/blog/ollama-v030-mlx-stable-upgrade-2026/) | secondary blog, self-dated 2026 | single-source, UNVERIFIED against Ollama's own changelog |
| web | [runaihome.com, Ollama MLX 2026](https://runaihome.com/blog/ollama-mlx-apple-silicon-2026/) | secondary blog, self-dated 2026 | corroborates the above (same publisher, not independent) |
| web | [yage.ai, MLX vs llama.cpp on Apple Silicon](https://yage.ai/share/mlx-apple-silicon-en-20260331.html) | 2026-03-31 | independent of runaihome; gives the memory-bandwidth-ceiling explanation |
| web | [groundy.com, MLX vs llama.cpp](https://groundy.com/articles/mlx-vs-llamacpp-on-apple-silicon-which-runtime-to-use-for-local-llm-inference/) | undated in snippet, 2026 | secondary, single-source for the 130 vs 43.5 tok/s figure |
| web | [ssdnodes.com, Ollama concurrency](https://www.ssdnodes.com/learn/ollama-num-parallel-and-max-queue) | undated, 2026-era | corroborated by glukhov.org on mechanism, not on the specific latency percentages |
| web | [glukhov.org, parallel requests](https://www.glukhov.org/llm-performance/ollama/how-ollama-handles-parallel-requests/) | undated | independent corroboration of NUM_PARALLEL/batching mechanism |
| web | [riaf gist, launchd PATH fix](https://gist.github.com/riaf/cf662d965ebd1b8b47453dd79cdd5578) | undated | generic macOS pattern, standard fix |
| web | [Bits By Me, launchd PATH whack-a-mole](https://bitsby.me/til/2026-04-04/launchd-path-whack-a-mole/) | 2026-04-04 | independent corroboration of PATH-fix options |
| web | EAGLE-3/Medusa arXiv preprints (Spheron blog, E2E Networks blog, multiple arXiv PDFs) | 2026, various | academic/GPU-cluster focus; no Qwen3-on-MLX shipped implementation found |
| web | thermal/M5-Air throttling claim | outlet unclear in snippet, 2026 | single-source, UNVERIFIED, not directly applicable (this machine is M5 Pro) |
