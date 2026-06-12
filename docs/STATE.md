# local-models — STATE (agent handoff / index)

Single source of truth for where this project is. Read this first. Last updated 2026-06-11.

**What it is:** a local-model toolkit on an Apple-Silicon Mac (M5 Pro, 64 GB), running alongside
cloud Claude. Hard rule: **no idle performance penalty** — nothing heavy resident unless invoked.

## Entrypoint

`lm` (on PATH) is the front door — `lm` for the overview, `lm status` for server/warm/models.
All commands are also directly on PATH (exec-wrappers in `~/.local/bin/` → `bin/`).

| Command | What | Help |
|---|---|---|
| `q "..."` | quick local LLM — answers, macOS commands (`q cmd`), titles (`q title`); `q history`/`q show N` | `q -h` |
| `imagine "..."` | local image gen (Flux/Qwen on GPU); `--enhance --from --style --neg --seed --stepwise -m`; `imagine history`/`show`/`critique` | `imagine -h` |
| `warm on\|off\|status` | Tier W toggle — pin a small model resident (snappy) vs zero-idle | `warm -h` |
| `lm status` | server + resident + on-disk models | `lm` |

## Architecture

- **Server:** self-hosted `ollama serve` via LaunchAgent `com.alcatraz.local-models-ollama`
  (`bin/lm-serve`) — the GUI Ollama.app ignored env, so we own it. Policy baked in:
  `MAX_LOADED_MODELS=2`, `KEEP_ALIVE=0`, flash-attn + q8 KV. Port 127.0.0.1:11434.
- **Two-tier model lifecycle:** one small **warm** model (`gemma4-e4b-warm`, num_ctx 8192, ~5.6 GB)
  for the snappy path; everything big loads on-demand and unloads immediately. Resolves the
  snappy-vs-no-idle tension.
- **`q`** drives lifecycle per-request (`keep_alive`, warm-aware); never starts/stops the server.
- **`imagine`** = mflux (MLX Flux) wrapper. Model registry (`resolve_model`) maps a name → mflux
  binary + variant + default steps. `--enhance` uses gemma4 as a prompt engineer; `imagine critique`
  uses gemma4:26b vision to diagnose a result (the generate→critique→refine loop, all local).
- **Image models** live in the HF cache (`~/.cache/huggingface`), not Ollama. First use downloads.

## Key files

- `bin/` — `lm` `q` `imagine` `warm` `lm-serve` · `_lib.sh` (shared: colors/help/jsonl-history/`ollama_up`/`ollama_resident`) · `config.sh` (WARM_MODEL, IMAGINE_MODEL)
- `modelfiles/gemma4-e4b-warm.Modelfile` · `presets/skybound-isles.{json,png}` (a locked wallpaper)
- `docs/00-plan.md` (plan + build log + V1 line) · `docs/q-spec.md` · `docs/STATE.md` (this)
- `docs/GOALS.md` — **goals + audit per command** (guiding goal points, implementation notes, ranked improvements; 2026-06-12)
- `.claude/output/20260612-lm-research/` — 4 research reports (consolidation · claude-integration · coding-models · assets-sessions; 2026-06-12)
- `docs/research/` — runtime, vision, image-gen, **imagegen-techniques** (consolidated reference),
  **art-direction-brief** (the art-director persona's playbook)
- Personas (global): `~/.claude/personas/` — `art-director` (image gen), `closer`/`platform-builder`/`pragmatist` (strategy triad)
- LaunchAgent: `~/Library/LaunchAgents/com.alcatraz.local-models-ollama.plist`

## DONE

- **q** — built, standardized (cli-help-design help, `history`/`show`, deterministic temp 0,
  history log, on PATH), macOS/BSD smart defaults, `think:false`, intents (ask/cmd/title/commit),
  warm-aware, **stdin piping** (`git diff | q commit`), friendly server-down error (2026-06-12).
- **_lib.sh consolidation** (2026-06-12) — colors/help/history/residency-guard/health-check shared
  across q/imagine/lm; closed the duplicated-guard class that caused the enhance un-pin bug.
- **Tab-title auto-base** (2026-06-12) — UserPromptSubmit hook
  (`~/.claude/scripts/tab-title/hooks/auto-base.sh`) titles sessions from the first prompt via
  `q title`; warm-gated, fire-and-forget, manual base wins.
- **Iteration + asset layer** (2026-06-12) — imagine logs the FULL reproducible config (+
  `parent`/`kind` lineage); `redo/vary/refine N` verbs; `star N` / `prune [-y]` / `gallery`
  (self-contained `outputs/index.html`, dark/light); `q -c [N]` conversation continuation
  (cid chains); `lm doctor` (11-check smoke) + `lm timeline`; `history --json` on both tools.
- **Skeptical-review hardening** (2026-06-12) — 18-finding adversarial review + fix round
  (JSONL-corruption, numbering-drift, resident-match, prune keep-set, config decoupling).
  Report: `.claude/output/20260612-skeptical-review/review.md`.
- **gcc discovery** (2026-06-12) — `~/.claude/features/local-models.md` + CLAUDE.md Tier-2
  pointer: other Claude instances can now find the suite.
- **Server + warm** — LaunchAgent, `num_ctx`/q8-KV governance, `warm` toggle, verified no-idle.
- **llm-mini** — watchdog neutralized (`idle_timeout_min=0`) so it can't pkill our server; full
  fold-in deliberately **deferred** (over-engineering; serves a future Claude→local goal).
- **imagine** — mflux wrapper; model registry (schnell/flux2/qwen/dev), model-aware steps/guidance,
  `--enhance`/`--from`/`--style`/`--neg`/`--guidance`/`--stepwise`/`--seed`, `history`/`show`,
  observability (pre/post summary, `--metadata`, auto-open), **`critique`** vision-loop.
- **lm** entrypoint + full help/examples across all commands.
- **Personas** — art-director (TUI-wizard creative-direction) + the strategy triad.
- **Research** — runtime / vision / image-gen sweeps + two consolidated guides.
- **Vision probe PASSED** — gemma4:26b vision gives accurate image critiques (→ built `imagine critique`).
- **Scheduled** — local review **Tue Jun 24, 3 PM IST** (Google Calendar) to prioritize the pending below.

## PENDING

- **`--web` for q** (Task 6) — deferred per MAGI (needs a search-backend decision; no proven pull yet).
- **Imagegen §8 upgrades** (Task 13) — 1 of 5 done (`critique`). Still: add `ideogram4` + `z-image-turbo`
  to the registry (best-text + fast-draft); a `--good` quality alias; a refine/upscale step
  (`mflux-upscale-seedvr2`); a Qwen text helper (auto-quote). **→ the June 24 review decides order.**
- **Proper dev-based ControlNet** — the minecraft-style "you" test washed out on schnell+dev-ControlNet;
  the real fix needs the gated FLUX.1-dev base (license + ~24 GB) + a voxel LoRA + a photo of the user.
- **Deferred-with-triggers (V2):** llm-mini/MCP fold (Claude calls local), LAN M4-Pro offload.

## Key lessons (load-bearing)

- For small local models, **the prompt is a bigger quality lever than the model** (4B + good
  system prompt beat a code model + generic prompt).
- `think:false` must be the **API flag** — prompt-level "no thinking" is ignored.
- The accuracy ceiling for `cmd` is **macOS-vs-Linux**, not size → BSD-aware system prompt.
- A tool isn't delivered until it's **on PATH and invoked as a bare command** (atone S3 this session).
- gemma4 **can't generate images** (it's the prompt-engineer/critic); diffusion does the pixels.
