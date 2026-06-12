# Local Models — V1 Plan

**Status:** V1 CORE SHIPPED (Slices 1+2) · vision = probe-gated · image-gen = trying (minimal) · MAGI 2026-06-09 · **Started:** 2026-06-09
**Owner:** alcatraz627 · **Scope:** this machine + optional LAN offload box. Not shipped to other systems.

A local-model subsystem that runs alongside cloud Claude: a place to experiment, a
local vision model that feeds Claude better image understanding, a local image
generator the user can iterate on like a reusable subsystem, and a fast companion
that absorbs small latency-sensitive tasks Claude would otherwise pay cloud latency for.

---

## 1. Hardware (fixed inputs)

| | Machine A (primary) | Machine B (LAN) |
|---|---|---|
| Model | MacBook Pro, **Apple M5 Pro** | MacBook **M4 Pro** |
| CPU / GPU | 18-core / 20-core, Metal 4 | — / — |
| Unified RAM | **64 GB** (~48 GB GPU budget) | **24 GB** (~16–18 GB GPU budget) |
| Free disk | ~736 GB | (ample) |
| Role | daily dev machine — must stay responsive | idle/dedicated — can be loaded freely |

## 2. Current state (what already exists)

- **Ollama** (official app build, 0.30.6) — working. Models pulled: `gemma4:31b` (19 GB), `gemma4:26b` (17 GB, MoE — fast). Server auto-started by the app; default keep-alive 5m.
- **`llm-mini`** — existing Claude-built subsystem (`~/.claude/scripts/llm-mini/`). CLI + chat REPL + **MCP server** (`mcp__llm-mini__ask`) + **hook-callable** (`mini_quick`) + engine lifecycle mgmt + prompt templates + **auto local→cloud-Haiku fallback**. This is the integration substrate for Requirement 3.
- Project dir: empty (clean slate).

## 3. The four tools — roles (consolidation)

| Tool | What it is | Role here |
|---|---|---|
| **Ollama** | model runner + API server (bundles llama.cpp) | always-available **programmatic backend** w/ short keep-alive |
| **LM Studio** | GUI model browser + OpenAI-compat server | **human experimentation** surface (Requirement 1) |
| **llama.cpp** | the low-level engine the others build on | foundation; use **directly only if** we outgrow the wrappers |
| **`llm-mini`** | existing fast-task router (local + cloud fallback) | the **companion/router** layer (Requirement 3) |

> Decision input pending from research agent (`docs/research/20260609-runtime-orchestration.md`).

## 4. Requirements

1. **Experiment** with local models freely.
2. **Vision + image-gen:**
   - *Vision* — local VLM that parses screenshots (debugging) & design mockups (planning), feeding structured text to cloud Claude.
   - *Image-gen* — local generation the user iterates on via prompts/presets/workflows (tone, style, procedure), **no fine-tuning**, swappable models.
3. **Offload small tasks** from Claude: latency-critical quick-QnA, codebase exploration (cf. `enh-qa-agent`), higher-frequency dreaming-subsystem passes, fire-and-forget companion calls (e.g. "given this conversation, produce a tab title"). Examples are illustrative, not exhaustive.

## 5. Hard constraints (the cutline for "is this worth it")

- **No idle penalty.** Zero noticeable system cost merely from HAVING models installed. Heavy compute only while actively serving an invoked task.
- **Latency justifies the QnA path.** If a quick query isn't fast, the user falls back to ChatGPT/Haiku — so the companion path must be genuinely snappy.
- **Image-gen:** heavy WHILE generating is fine; idle footprint must be ~0. Models swappable + prompt-customizable, no fine-tuning.

### Key resource lever already found
`gemma4:26b` loaded at **CONTEXT 262144** (256K window) → enormous KV-cache, a big part of the observed RAM. Most tasks need 8–32K. **`num_ctx` is a primary footprint knob.**

---

## 6. Levels of planning & decision (the structure)

| # | Layer | Core decision | Status |
|---|---|---|---|
| L1 | **Runtime** | which engines for which job; how they coexist (ports, shared model store) | research in flight |
| L2 | **Placement** | what runs on Machine A vs LAN Machine B | **QUESTION 1** |
| L3 | **Model** | specific models per capability (QnA / vision / image-gen / embeddings) + quant | research in flight |
| L4 | **Resource governance** | warm-vs-on-demand, keep-alive policy, `num_ctx`, lifecycle → enforce no-idle-penalty | **QUESTION 2** (latency) |
| L5 | **Integration** | how Claude / llm-mini / dreaming / tab-title call local models; fire-and-forget pattern; routing + fallback | extends `llm-mini` |
| L6 | **Image customization** | the "hooks for images": presets, prompt templates, workflows, swappable models | **QUESTION 3** (stack) |
| L7 | **Validation / testing** | benchmarks (latency, tok/s, idle + active footprint) + per-use-case quality bars | post-decisions |
| L8 | **V1 scope / cutline** | what ships in V1 vs deferred | post-decisions |

## 7. Decisions (locked 2026-06-09)

- **Q1 — Placement → Everything on Machine A for V1.** LAN M4 Pro offloading + load-balancing deferred to **V2**.
- **Q2 — Latency bar → Snappy** (first token <1s, short answer <3s). Sets a small always-warm model.
- **Q3 — Image stack → Max control / subsystem → ComfyUI.** Research-confirmed: git-trackable JSON workflows = the reusable subsystem. Draw Things optional later as a fast interactive scratchpad.

## 8. Research in flight (background agents, 2026-06-09)

- `docs/research/20260609-runtime-orchestration.md` — Ollama vs LM Studio vs llama.cpp vs MLX; coexistence + idle footprint.
- `docs/research/20260609-vision-models.md` — VLM survey for screenshots/designs; is gemma4 vision enough to start.
- `docs/research/20260609-image-gen-stack.md` — Draw Things vs ComfyUI vs mflux; preset/workflow subsystem.

## 9. V1 Plan (decided)

### 9.1 Target architecture (all on Machine A; LAN offload = V2)

```
MACHINE A (M5 Pro 64GB)
┌──────────────────────────────────────────────────────────────┐
│ TIER W — WARM, USER-TOGGLEABLE (`warm on|off`)               │
│   gemma4-e4b-warm  (num_ctx 8k) · ~6GB when ON, 0 when OFF    │
│        │  snappy companion engine                            │
│        ▼                                                      │
│   Claude(cloud) ◄──► llm-mini (router) ◄── tab-title,        │
│                          │                  quick-QnA,        │
│                          │                  dream passes      │
│ TIER D — ON-DEMAND (keep_alive=0, load→unload, zero idle)     │
│   gemma4:26b/31b ── heavier local reasoning                  │
│   gemma4:26b     ── vision parse (screenshots/designs)─►Claude│
│   moondream      ── fast vision fallback (1.9GB)             │
│ TIER I — ON-DEMAND, KILLED WHEN IDLE                          │
│   ComfyUI + Flux.1[schnell] ── image-gen subsystem           │
│     └ git-tracked workflows + prompt presets + LoRA/IP-Adapter│
└──────────────────────────────────────────────────────────────┘
  Self-hosted `ollama serve` (LaunchAgent) · MAX_LOADED_MODELS=2 · flash+q8 KV · no MLX
  LM Studio = experimentation GUI only (manual launch, never at login)
```

### 9.2 Resource-governance policy (enforces the no-idle-penalty rule)

- **Two-tier lifecycle.** Tier W = one small warm model (snappy path). Tier D/I = everything
  big, on-demand, unloaded immediately.
- **Custom Modelfiles:** `num_ctx 8192`, `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`
  → KV cache ~46GB → ~0.7GB.
- **Server:** self-hosted `ollama serve` via LaunchAgent `com.alcatraz.local-models-ollama`
  (Ollama.app ignores `launchctl` env, so it cannot apply launch-only settings). Policy lives in
  `bin/lm-serve`: `OLLAMA_MAX_LOADED_MODELS=2`, `OLLAMA_KEEP_ALIVE=0` (Tier W overrides per-request),
  `OLLAMA_FLASH_ATTENTION=1` + `OLLAMA_KV_CACHE_TYPE=q8_0` (verified active). MLX unavailable in 0.30.6.
- **Memory-pressure eviction (Apple Silicon reality):** Ollama also evicts when *free system RAM*
  (not GPU budget) can't fit a new model (`system_limited=true`). So warm+big coexist only with RAM
  headroom; under pressure the active task wins and the warm model reloads (~2-3s). Correct
  no-degradation behavior, not a bug.
- **ComfyUI:** `comfy-start` / `comfy-stop` wrappers, `--cache-none`; never resident.
- **Idle-footprint target: < ~6GB when Tier W ON; ~0 when OFF.** Everything else 0 when not invoked.

### 9.2.1 Tier W on/off control (user-toggleable warm state)

You decide when to pay the warm-start cost vs. shut it down completely. A `warm` CLI flips
Tier W between resident and fully off — no daemon, no background timer, just an explicit switch:

```
warm on       # load the Tier W model with keep_alive=-1 → stays resident (snappy path live)
warm off      # `ollama stop` the model → fully unloaded, ZERO warm footprint
warm status   # show resident state + context window (ollama ps)
warm restart  # off → on
```

- **ON** → snappy local companion live, ~6GB resident.
- **OFF** → zero warm cost; the snappy path degrades gracefully to cold-load-on-demand or the
  cloud-Haiku fallback (via `llm-mini`).
- **Source of truth** = Ollama's own loaded-model registry (`ollama ps`); no separate state file.
- **Default at login = OFF** (no surprise idle cost). Run `warm on` when entering a session
  that wants snappy local inference.

### 9.3 Model shortlist (V1)

| Capability | Model | Footprint | Lifecycle |
|---|---|---|---|
| Snappy companion | `gemma4:e4b` Q4 (A/B vs current `llama3.2`) | ~6GB | **warm** |
| Heavier local reasoning | `gemma4:26b` (MoE) | ~17GB loaded | on-demand |
| Vision parse | `gemma4:26b` (already multimodal — no new pull) | on-demand | on-demand |
| Fast vision fallback | `moondream` | 1.9GB | on-demand |
| Image-gen | `Flux.1 [schnell]` Q5 via ComfyUI | ~8GB disk | on-demand |
| *(V2)* Vision upgrade | `qwen3-vl:32b` (best OCR, ~23GB) | — | deferred |

### 9.4 Integration (extends `llm-mini`, not new infra)

- Point `llm-mini`'s local tier at the warm `gemma4:e4b`; keep its Haiku cloud fallback.
- Companion entry points = thin wrappers over llm-mini:
  - *quick-QnA* — `llm-mini "..."` (retune model + prompt templates).
  - *tab-title fire-and-forget* — tab-title subsystem calls `mini_quick` with a strong
    title-from-conversation prompt.
  - *vision parse* — new `vision-parse <image>` wrapper → on-demand gemma4 vision →
    emits structured `<vlm_parse>` block → Claude reasons over it (VLM parses, Opus reasons).
- Examples are illustrative; define the contract, build incrementally.

### 9.4.1 Snappy companion — output discipline (why "quick" must mean terse)

Real failure (2026-06-09): `ollama run gemma4:12b "how to find the program path of all
processes running on port 8001"` returned a reasoning trace **plus** a three-OS essay **plus**
a summary table — the opposite of useful for a one-command question. "Quick" is not just about
latency; it's about a *direct, usable* answer. Causes → fixes:

| Cause | Fix |
|---|---|
| Raw `ollama run` = the model's default verbose/hedging persona | Strong system prompt: terse, direct, no preamble, no caveats unless asked |
| No environment context → covers Linux+macOS+Windows | Inject "macOS + zsh; assume MY environment; never enumerate other OSes" |
| `Thinking…` reasoning trace = latency + verbosity tax | Disable thinking on the quick path (think=off, or a non-reasoning model) |
| No output contract | Intent-typed: `cmd` → a single command only (post-extracted); `ask` → ≤2 sentences |
| General chat model for a CLI task | A/B `cmd` intent: e4b vs llama3.2 vs `qwen2.5-coder:3b` (code-tuned = terse) |

Mostly **configuration of llm-mini's existing `cmd-compose` path**, not new infra. This is a
named V1 acceptance test: the port-8001 query must return ONE macOS command, no essay.

### 9.5 Image-gen subsystem (the "hooks for images")

Four-layer conditioning, all inference-time (no fine-tuning):
prompt templates (`.txt`, git-tracked) → community LoRAs (`LoraLoader`, read-only artifact)
→ IP-Adapter (image-reference style) → ControlNet (structure) + seed-pinning for reproducible
heroes. Workflows live as versioned JSON. *(Advanced ControlNet/IP-Adapter = V1.5.)*

### 9.6 Testing / acceptance bars

| Path | Metric | Bar |
|---|---|---|
| Idle footprint | RAM, nothing invoked | < ~6GB |
| Snappy QnA | first token / total (short) | <1s / <3s |
| Vision parse | cold-load + parse on a real screenshot; OCR fidelity | usable; < ~20s |
| Image gen | seconds/image (Flux schnell) | < ~60s |

Test with **real** inputs (real screenshot set, real "kill port 3001"-type queries).

### 9.7 Build sequence

1. **Foundation / resource governance** — Modelfiles (`num_ctx`) + Ollama env policy + `warm` toggle.
   *Gate:* idle footprint ~0 (Tier W OFF) / <6GB (ON); big models unload after use. ← **start here**.
2. **Snappy companion** — wire warm `gemma4:e4b` into `llm-mini`; prove tab-title + QnA latency.
3. **Vision parse** — gemma4 vision wrapper + `<vlm_parse>` handoff + moondream fast path; real screenshots.
4. **Image-gen subsystem** — ComfyUI + `comfy-start/stop` wrappers + Flux schnell + git-tracked workflow + preset library.
5. **Validation pass** — run §9.6; tune; declare V1 live.

### 9.8 Deferred to V2

LAN M4 Pro offloading + load-balancing (`llmlb`/OLOL), `qwen3-vl:32b` vision upgrade,
`vllm-mlx` prefix caching, deeper dreaming integration, advanced image conditioning.

## 10. Research (completed 2026-06-09)

- `docs/research/20260609-runtime-orchestration.md` (415 lines)
- `docs/research/20260609-vision-models.md` (357 lines)
- `docs/research/20260609-image-gen-stack.md` (image-gen)

## 11. Build log

### Slice 1 — Foundation / resource governance — DONE (2026-06-09)

Files: `bin/warm`, `bin/lm-serve`, `config.sh`, `modelfiles/gemma4-e4b-warm.Modelfile`,
LaunchAgent `~/Library/LaunchAgents/com.alcatraz.local-models-ollama.plist`.

Gates:
- num_ctx 8192 (256K→8K): KV cache ~5GB → ~190MB. ✓
- Tier W ON: 5.6GB, 100% GPU, keep_alive Forever (<6GB gate). ✓
- Tier W OFF: `ollama ps` empty → ~0 idle. ✓
- `warm on|off|status` toggle both directions. ✓
- flash attention + q8 KV cache active (`K (q8_0)`, `flash_attn=enabled`). ✓ — required self-hosting.

Findings (the path was not straight):
- **Ollama.app ignores `launchctl setenv`** — launch-only settings (MAX_LOADED_MODELS, flash, q8)
  never applied while the app owned the server. Pivoted to self-hosted `ollama serve` (LaunchAgent).
  Corrects an earlier assumption that GUI apps inherit launchctl env.
- **Eviction is free-system-RAM-driven**, not MAX/GPU (`system_limited=true`). Coexistence needs
  RAM headroom; correct no-degradation behavior. Machine was at ~10GB free / 20GB compressor.
- **MLX not available** in Ollama 0.30.6 (`OLLAMA_USE_MLX` unrecognized) — backend is llama.cpp/Metal.
- App is not a login item → no port-race at login; dormant unless manually opened (then it would
  clash on 11434 — disable its launch-at-login if you ever enable it).

### Slice 2 — Snappy companion (`q` tool) — core DONE (2026-06-09)

`bin/q`: `on|off|status` passthrough + intent-typed queries (`cmd`/`ask`) + flags
(`--think`, `-m`, `--raw`); `think:false` by default; streaming; warm-aware `keep_alive`
(won't un-pin a warm model).

Validated:
- **`think:false` is the only thing that kills the reasoning trace** — prompt-level "no thinking"
  does NOT work (proven against gemma4-e4b). Must be the API flag.
- Latency (warm): `q cmd` 0.79s, `q ask` 0.91s — sub-second. ✓
- Format: single command / ≤2 sentences, no essay, no multi-OS, no thinking. ✓

Model A/B (cmd intent): **kept gemma4-e4b**. qwen2.5-coder:3b was not better (wrong `pkill`,
markdown backticks). The real accuracy gap was **macOS-vs-Linux, not model size** — both models
reached for GNU `--sort`. Fix = BSD-aware system prompt with macOS idioms (`lsof -i`, `ps -m`),
which removed the Linux flags. e4b stays run-to-run variable on complex queries (4B ceiling) —
acceptable for a quick companion. qwen2.5-coder:3b retained as a `-m` override.

Smart defaults (2026-06-09): macOS/Apple Silicon is the **permanent** default; switches to Linux
only on explicit "linux server/container" mention (validated both directions); never asks
clarifying questions — assumes intent and answers. Tradeoff: e4b gives poor commands on vague
queries (4B ceiling), acceptable for zero-clarification quick work.

Pending: wire into llm-mini (Task 4); opt-in web search (Task 6, needs search-backend decision).

## 12. V1 line + direction (MAGI 2026-06-09)

V1 core = **Slices 1+2** (resource governance + `q`), shipped and in daily use. Per the MAGI
synthesis (`~/.claude/assets/magi/20260609-1604-local-models-direction/`):

- **Slice 3 Vision** — probe-gated: a ~30-min gemma4 screenshot probe decides build-vs-defer.
- **Slice 4 Image-gen** — user opted to give it a try → **minimal "show something"** via mflux/Flux,
  separate from q work, foldable later. ComfyUI workflow/preset subsystem stays deferred.
  (gemma4 cannot generate images — needs a diffusion model.)
- **Deferred (named triggers):** `--web`, cloud fallback, llm-mini/MCP fold, LAN offload (see §9.8).
- **Killed framing:** the "four tools" tiering (Ollama + `q` is the runtime); per-intent model
  selection (A/B proved prompt > model); chasing the 4B run-to-run variance (model ceiling).

Governing principle: *build only what a real consumer pulls, behind a contract the future can
extend; when unsure the pull is real, buy the cheapest probe instead of a slice.*
