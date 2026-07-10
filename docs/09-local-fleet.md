# The local fleet — where local models fit the workflow

Grounded in a scan of 14 days of real Claude sub-agent usage (269 dispatches across
Versable / .claude / local-models / claude-instances). Answers: *what work goes to a
local fleet, what harness serves it, and is it direct-called / Claude-called / a mix.*

## 1. The demand (measured, not guessed)

269 sub-agent dispatches in 14 days. ~65% were Versable **doc/code audit → reconcile →
verify** fan-outs. The dominant shape across ALL projects: Claude decomposes a big task
into N **scoped, verifiable, low-stakes-per-call** sub-tasks, fans them out, collects,
and synthesizes. That fan-out is currently paid in cloud tokens + throttle risk (wide
fans triggered the 429 storms).

## 2. Use-case catalog — what the fleet does (and does NOT)

| Class | Fleet-fit | Why |
|---|---|---|
| Audit a page/doc/file against a rubric | ✅ ideal | scoped, verifiable, huge volume |
| Doc reconcile / drift / contradiction hunt | ✅ ideal | compare two sources, flag deltas — mechanical judgment |
| Skeptical / adversarial review of a claim/finding | ✅ ideal | homework-checking; N independent skeptics is cheap locally |
| Recon / map / "where is X" (read-only) | ✅ strong | grep-fan-out + summarize; no writes |
| Voice / prose consistency sweep | ✅ strong | check against a style, flag violations |
| MAGI voters | ◐ partial | cheap lenses → local; synthesis + hardest lens → Claude |
| Rewrite / fix / apply | ◐ split | mechanical transforms → local behind a diff gate; judgment → Claude |
| Research (web + synthesis) | ✗ Claude | needs web access + strong synthesis |
| Design / decompose / final decision | ✗ Claude | the conductor's job, never delegated |

**The line:** the fleet does the *legwork* (audit, verify, recon, homework-check) in
parallel; Claude keeps *decomposition, synthesis, and the final call*. A fleet worker's
output is trusted because it **crosses a gate**, not because the model is smart.

## 3. The fleet model

- **Several MODERATE models, not one big one.** A small stable (e.g. `qwen3.6:35b-a3b`
  the gate winner, `gemma4:26b`, a small coder) run **concurrency-capped** — 64GB RAM
  fits ~2–3 moderate models resident at once, so the Governor caps concurrency, not the
  user. Throughput comes from rotation + parallelism, not model size.
- **Decoupled, not spawned-per-task.** Unlike a Claude sub-agent (shares Claude's
  context, dies with the session, costs tokens, throttles), a fleet worker is a plain
  `q`/`review` call against the always-on local server: $0, throttle-immune, available
  when Claude is rate-limited.
- **Gated.** Weaker models → every batch output crosses a Judge (tests/lint/schema, or
  Claude spot-checks a sample) before it's trusted. This is `docs/07`'s Judge.

## 4. The harness ladder — what to build

1. **A batch fan-out runner** (the core; `docs/07`'s `bin/procedure` / a `lm fleet`).
   Input: a rubric/prompt + a list of items (files, docs, PRs). It fans them across the
   local models concurrency-capped, applies a Judge, returns structured results. This is
   ~90% of the value — it turns "40 audits on cloud sub-agents" into "40 audits on the
   local fleet, free."
2. **A persistent pool + submit/collect** (only if volume demands) — always-on workers
   Claude submits tasks to and collects from, fully decoupled/async. Grows from #1.
3. **An MCP surface** — expose `fleet_audit(items, rubric)` / `see` / `review` as native
   MCP tools, so Claude *and* the better-file-browser extension call the same fleet.

Start at #1. It's the justified Phase-1 build now that the Task #8 gate is GREEN
(`qwen3.6` went 9/9 on the judgment suite).

## 5. Direct vs Claude-called vs mix — the ratio

- **Today: ~100% direct** — you type `q`/`see`/`review`. There's no runner for Claude to
  fan out to, so all the fan-out volume goes to *cloud* sub-agents.
- **After the runner: ~70% Claude-called, ~30% direct.** The 269 dispatches are
  Claude-initiated fan-outs — that's where the fleet earns its keep (volume + cost +
  availability). Direct stays your quick interactive tasks (a review, an image read, a
  commit message) — lower volume, higher frequency.
- **So the build shifts the ratio.** The runner unlocks the Claude-called majority; until
  it exists, the fleet can't absorb the workload that actually dominates your usage.

The mix isn't a preference to pick — it's an outcome of *what you build*. Build the
fan-out runner and the Claude-called majority follows, because that's the shape of the
work you already do.
