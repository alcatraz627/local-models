# local-models — Goals & Audit

For humans and agents: the guiding goal behind each command, how it's implemented, whether the
approach holds up, and what to improve. Written from a full code read of `bin/*` + `config.sh` +
`modelfiles/` on 2026-06-12. Companion to `STATE.md` (index) and `00-plan.md` (history/decisions).

## North-star goals (the whole subsystem)

1. **No idle penalty** — zero noticeable cost from merely *having* models installed. Heavy compute
   only while serving an invoked task. (The hard constraint everything else bends around.)
2. **Snappy or it loses** — the quick-answer path must beat "open ChatGPT": first token <1s,
   short answer <3s when warm. If it isn't fast, it won't be used.
3. **Local-first, $0 marginal** — answers and images cost wall-time, not tokens. No cloud
   dependency after one-time weight downloads.
4. **Usable bare commands, not a framework** — every capability is a command on PATH with real
   help. A tool isn't delivered until it's invoked bare and works.
5. **Deliberate residency** — RAM use is an explicit user choice (`warm on`), never a timer or
   a daemon's guess.
6. **Iterate-by-prompt, not fine-tune** — image quality comes from prompts, presets, styles, and
   the local critique loop; models are swappable inputs.

## Architecture in one diagram

```
            ┌────────────────────────── lm (dispatcher) ─────────────────────────┐
            │            │                  │                       │            │
            ▼            ▼                  ▼                       ▼            │
        q (text)     imagine (images)   warm (residency)       lm status        │
            │            │    │             │                       │            │
            │   --enhance/critique          │                       │            │
            ▼            ▼    ▼             ▼                       ▼            │
   ┌─ ollama API (127.0.0.1:11434) ─────────────────────┐   ┌─ mflux (MLX) ─┐
   │  self-hosted `ollama serve` via LaunchAgent        │   │ .venv/bin/     │
   │  com.alcatraz.local-models-ollama → bin/lm-serve   │   │ mflux-generate*│
   │  KEEP_ALIVE=0 · MAX_LOADED=2 · flash-attn · q8 KV  │   │ HF cache       │
   └────────────────────────────────────────────────────┘   └────────────────┘
   Tier W: gemma4-e4b-warm (num_ctx 8192, ~5.6GB) pinned only by `warm on`
   Tier D: gemma4:26b etc — load on demand, unload immediately (keep_alive=0)
```

---

## Per-command goals & implementation notes

### `lm` — the front door (`bin/lm`, 52 lines)

**Goal:** one memorable entrypoint so nobody has to remember four commands — overview, examples,
and an at-a-glance health view. Discoverability, not functionality.

**How it works:** pure dispatcher — `lm q|imagine|warm` `exec`s the sibling script (zero overhead,
no re-parsing); `lm status` inlines a server ping (`/api/version`, 3s timeout) + `ollama ps`
(resident) + `ollama list | head -8` (on disk).

**Assessment: right design.** `exec` dispatch is the correct pattern (no wrapper PID, signals pass
through). Keeping `status` here instead of a fifth command is the right call.

**Notes / improvements**
- `lm status` says nothing about the **image side** (mflux venv present? HF cache size?) — it
  reports only the Ollama half of the system.
- `ollama list` truncated at 8 with no "…and N more" indicator.

### `q` — quick local LLM (`bin/q`, 174 lines · spec: `q-spec.md`)

**Goal:** replace "open ChatGPT for a 10-second question." Direct, usable answers — sub-second
warm — with **zero friction**: no clarifying questions, no multi-OS hedging, no reasoning-trace
tax. Deliberately shallow; real reasoning goes to cloud Claude.

**How it works:**
- Three intents select a system prompt: `ask` (≤2 sentences), `cmd` (ONE macOS/BSD command,
  with explicit BSD idioms baked in), `title` (2–5 words). `--raw` drops the prompt.
- Inline Python streams `/api/chat` with `think:false` (the API flag — prompt-level "no thinking"
  is ignored, proven), `temperature:0` (reproducible answers), token-by-token stdout.
- **Warm-aware `keep_alive`** (`bin/q:131-137`): if the target model is already resident →
  `keep_alive=-1` (don't un-pin); else `0` (load, answer, unload). This is the per-request half
  of the no-idle-penalty contract.
- Best-effort history to `logs/q-history.jsonl`; `q history`/`q show N` with stable line numbers.

**Assessment: right design, validated.** The load-bearing insight is **prompt > model** — the A/B
kept gemma4-e4b over a code-tuned model because the accuracy ceiling was macOS-vs-Linux idioms,
not parameters. The wrapper IS the product; the weights are a commodity.

**Notes / improvements**
- **`--think` likely pays without showing** — with `think:true` Ollama returns the trace in a
  separate `message.thinking` field, but the stream loop prints only `message.content`
  (`bin/q:159`). So `--think` adds latency yet the trace never renders. Verify, then either print
  the thinking dimmed or drop the flag.
- **Server-down = raw Python traceback.** `urllib` gets connection-refused and dumps a stack.
  Should catch and print one line: `server down — launchctl kickstart gui/$UID/com.alcatraz.local-models-ollama`.
- **No stdin support** — `git log | q "summarize"` is explicitly rejected in help ("quote the
  task instead"). Cheap to add (`[ -t 0 ] || QUERY="$QUERY\n\n$(cat)"`) and natural for agents;
  revisit if a real pull appears (don't build speculatively).
- History grows unbounded (fine for years at this volume; noted for completeness).

### `warm` — residency toggle (`bin/warm`, 52 lines)

**Goal:** resolve the snappy-vs-no-idle tension by making residency a **deliberate, explicit
choice**: `warm on` = pay ~5.6GB for a sub-second companion; `warm off` = zero footprint.
No daemon, no timer, no state file.

**How it works:** `on` = a 1-token `/api/generate` with `keep_alive=-1` (load + pin);
`off` = `ollama stop`; `status` = `ollama ps`. **Ollama's own registry is the source of truth** —
there is nothing to drift.

**Assessment: exactly right.** The no-state-file decision eliminates a whole class of bugs.
Smallest script in the toolkit and complete for its job.

**Notes / improvements**
- `WARM_KEEP_ALIVE` is the only config value not env-overridable (`config.sh:11` hardcodes vs
  the `${VAR:-}` pattern of its siblings). Trivial inconsistency.

### `imagine` — local image generation (`bin/imagine`, 239 lines)

**Goal:** a $0, fully-local **iteration loop** for images — idea → (optional local-LLM prompt
enhancement) → generate on the GPU → inspect → (optional local-vision critique) → refine.
Observable at every step; reproducible via seeds + PNG-embedded metadata.

**How it works:**
- **Model registry** (`resolve_model`, `bin/imagine:31-40`): friendly name → mflux binary +
  variant + model-aware default steps/guidance (schnell 4 steps, qwen 20, dev 20+g3.5). Adding a
  model = one case line.
- **`--enhance`**: gemma4 (the warm companion) as prompt engineer — terse idea → rich diffusion
  prompt, fallback to the raw idea on any failure.
- **`critique IMG ["goal"]`**: gemma4:26b vision examines a result against the stated intent —
  the generate→critique→refine loop, all local.
- `--style` presets, `--from` img2img, `--neg`, `--stepwise`, `--seed`; pre-run summary +
  post-run report; JSONL history mirroring `q`'s `history`/`show`.

**Assessment: right altitude.** mflux-as-subprocess beats the deferred ComfyUI subsystem for V1 —
no resident service (Tier I = zero idle by construction), and the registry keeps models swappable.
The enhance/critique loop is the differentiating feature and it correctly reuses the LLM stack.

**Notes / improvements**
- **Probable bug — `--enhance` can un-pin the warm model.** `enhance_prompt`
  (`bin/imagine:59-63`) posts to `/api/chat` with **no `keep_alive`**, so the server default
  (`OLLAMA_KEEP_ALIVE=0`) applies and the warm model unloads after the call — silently defeating
  `warm on`. `q` guards exactly this (`bin/q:131-137`); `imagine` skipped the guard. Fix: add the
  same resident-check, or simply always send `keep_alive:-1` when the target equals `$WARM_MODEL`
  and it's resident. **Verify at runtime first** (warm on → imagine --enhance → ollama ps).
- **Auto-`open` on every generation** (`bin/imagine:236`) — great interactively, wrong for
  scripted/agent use (Preview windows popping). Gate on `[ -t 1 ]` or add `--no-open`.
- **`--neg` is unguarded** — help says it needs dev/qwen, but the flag is passed to schnell
  anyway; either warn-and-drop for schnell or let mflux error early with a clear message.
- `SEED=$RANDOM` is 0–32767 — a small seed space for "random". Harmless, but
  `SEED=$((RANDOM * 32768 + RANDOM))` costs nothing.
- `--strength` without `--from` is silently ignored (no guard).
- The model list now lives in three places (registry case, help MODELS section, config comment) —
  when Task 13 adds `ideogram4`/`z-image-turbo`, all three need touching. Acceptable at this
  scale; just know it.

### `lm-serve` — the server policy (`bin/lm-serve`, 25 lines + LaunchAgent)

**Goal:** make the resource policy **deterministic and version-controlled**. The GUI Ollama.app
ignores `launchctl setenv`, so launch-only settings (MAX_LOADED_MODELS, flash-attn, q8 KV) never
applied — self-hosting `ollama serve` is the only way to own the policy.

**How it works:** exports policy env (`KEEP_ALIVE=0`, `MAX_LOADED_MODELS=2`,
`FLASH_ATTENTION=1`, `KV_CACHE_TYPE=q8_0`) then `exec`s ollama. Started at login by
`~/Library/LaunchAgents/com.alcatraz.local-models-ollama.plist`.

**Assessment: correct and verified** (q8 KV + flash-attn confirmed active in server logs;
the dead `OLLAMA_USE_MLX` was removed rather than cargo-culted — good hygiene).

**Notes / improvements**
- Hardcodes `/opt/homebrew/bin/ollama` — a brew upgrade keeps that path stable, but a
  `command -v` fallback would survive relocation. Trivial.
- Known sharp edge (documented in plan §11): if Ollama.app is ever opened manually it will fight
  for port 11434.

---

## Cross-cutting audit

### Is the overall approach the best way? Yes, for these constraints.

- **Bash wrappers over HTTP API + subprocess** is the right altitude: no resident runtime, no
  framework, each script readable in one sitting (542 lines total). The alternatives were
  considered and rejected with evidence (plan §12): raw `ollama run` fails the output contract;
  ComfyUI is a resident service (idle cost) deferred until workflow reuse has real pull;
  per-intent model selection lost the A/B to prompt engineering.
- **The two-tier lifecycle (warm pin + keep_alive=0 default) genuinely resolves** the
  snappy-vs-no-idle tension — and the discovery that eviction is free-RAM-driven means the design
  degrades correctly under pressure (active task wins, warm reloads later).
- **Consistency is a feature**: all four commands share the same help conventions, history/show
  pattern, and TTY/NO_COLOR-aware styling. An agent that learns one learns all.

### Ranked improvement list

| # | Item | Kind | Effort |
|---|------|------|--------|
| 1 | `imagine --enhance` un-pins the warm model (missing `keep_alive` guard) | bug — **FIXED 2026-06-12** (q's guard copied into `enhance_prompt`; doc-confirmed: per-request `keep_alive` overrides `OLLAMA_KEEP_ALIVE`) · verified 2026-06-12 | done |
| 2 | `q --think` paid the latency but never printed `message.thinking` | bug — **FIXED 2026-06-12** (trace now streams dimmed to stderr; stdout stays the bare answer) · verified 2026-06-12 | done |
| 3 | `q` server-down → Python traceback instead of a one-line hint | UX — **FIXED 2026-06-12** (`ollama_up` + `server_down_msg`, verified) | done |
| 4 | `imagine` auto-`open` breaks scripted/agent use | **DONE 2026-06-12** — TTY-gated + `--open`/`--no-open` | done |
| 5 | `--neg` silently passed to models that don't support it | **DONE 2026-06-12** — warn-and-drop on non-dev/qwen | done |
| 6 | `lm doctor` — one smoke check | **DONE 2026-06-12** — 11 checks, all green | done |
| 7 | Shared helpers for duplicated blocks | hygiene — **DONE 2026-06-12** (`bin/_lib.sh`: colors, help, jsonl history/show, `ollama_resident`, `ollama_up` — every helper has ≥2 callsites; verified live) | done |
| 8 | Tiny: `$RANDOM` seed space · `WARM_KEEP_ALIVE` not env-overridable · `--strength` guard · `lm status` image-side blind spot | hygiene | S each |

Items 1–7 closed 2026-06-12 (1–2 same-day, 3–7 in the build round). Item 8 partially done
(`$RANDOM` seed space widened); leftovers: `WARM_KEEP_ALIVE` env-override, `--strength`-without-
`--from` guard, `lm status` image-side blind spot.

A skeptical-review pass (2026-06-12, `.claude/output/20260612-skeptical-review/review.md`,
18 findings) drove a fix round: star JSONL corruption via `awk -v` escapes, history-numbering
drift on multiline prompts, `ollama_resident` prefix over-match, per-file prune keep-set,
`lm`/auto-base config decoupling, mid-stream traceback, HIST argv cap, verb flag warnings,
gallery `-o` paths. Deferred knowingly: star-vs-append race (no locking; documented), pre-cid
ts-collision chains (legacy entries only), auto-base state race (window minimized, comment owns it).
Pending feature work (q `--web`, imagine registry additions, upscale step) is tracked in
`STATE.md` § PENDING — the June 24 review prioritizes it; this list is orthogonal (correctness
and usability of what's already shipped).

### Non-goals (so nobody re-litigates them)

- Reasoning / code generation / multi-step analysis → cloud Claude.
- Fine-tuning → never; iteration is prompts + presets + critique.
- A daemon, scheduler, or auto-warming heuristic → residency stays a human choice.
- Folding `q` into `llm-mini` → deliberately deferred until the Claude→local pull is real.
