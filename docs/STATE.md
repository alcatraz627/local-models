# local-models — STATE (agent handoff / index)

Single source of truth for where this project is. Read this first. Last updated 2026-07-09.

**What it is:** a local-model toolkit on an Apple-Silicon Mac (M5 Pro, 64 GB), running alongside
cloud Claude. Hard rule: **no idle performance penalty** — nothing heavy resident unless invoked.
**The full command menu with examples: `docs/CAPABILITIES.md`.**

## Entrypoint

`lm` (on PATH) is the front door — `lm` for the overview, `lm status` for server/warm/models.
All commands are also directly on PATH (exec-wrappers in `~/.local/bin/` → `bin/`).

| Command | What | Help |
|---|---|---|
| `q "..."` | quick local LLM — answers, macOS commands (`q cmd`), titles; `--json`/`--format SCHEMA` (constrained decoding → `.data`), `--glow`; **`--web`** = search-then-answer (DDG, cited) · **`--diy`** = self-routing (planner picks intent/web/file/image/tier, gray-narrated, flags win); `q history`/`show N` | `q -h` |
| `imagine "..."` | local image gen (Flux/Qwen on GPU); `--enhance --from --style --neg --seed`; `history`/`show`/`critique` | `imagine -h` |
| `see <img> [q]` | local vision — structural read or grounded answer; **good-but-verify text**; `--ui` = sectioned UI inventory (elements/hierarchy/icons/patterns, big-tier routed, lease-aware) · `--ui --json` = schema-constrained `.data` · `--ocr` = EXACT text via Apple Vision (no model, ~300ms) · `--menubar` = capture+read the live top strip · `--crop WxH+X+Y`/`--region top…center` = crop-then-read (small crops read near-perfectly) · `see more "q"` = drill into the last image; every read lands `outputs/see/<ts>-…/` (source copy + read.md + meta.json; `see open N` · `see note "…"`) | `see -h` |
| `lm ui-verify <img> "claim"…` | the $0 UI verification gate — enumerable claims judged strictly (pass/fail/unsure; unsure never passes; exit 0 only when all pass) against either a `see --ui --json` inventory (screenshots) or `--app <Name>` = the LIVE accessibility tree via `ax` (native apps, exact); `--region/--crop` for focused reads, `--json` for agents | `lm ui-verify -h` |
| `review <pr#\|file\|dir>` | local code review — PR/files/folders/stdin; `--full` (whole files via API, no checkout), `--findings` (schema-constrained objects), `--glow` | `review -h` |
| `lm probe <model>` | judgment eval — the gate that decides if a model earns a tier | `lm probe` |
| `lm fleet <intent> <files…>` | batch fan-out: N files × one intent, concurrency-capped, Judge-gated, run record | `lm fleet -h` |
| `lm index [find X]` | repo symbol map — "where is X" with live staleness | `lm index -h` |
| `lm opencode [args]` | opencode on the local code tier — auto lease/release around the session | — |
| `lm gemini "..."` | the gemini lane (pinned gemini-3.5-flash, wrapper-only, read-only posture); `ingest`/`ask` per-project sessions (UUID create/resume); structured `gemini_unavailable` fallback. **VERIFIED end-to-end 2026-07-07** — auth = API key in `~/.gemini/.env` (600, wrapper-loaded; settings selectedType=gemini-api-key). Note: plan-mode gemini can READ the workspace it runs in — don't point it at dirs holding secrets | `lm gemini -h` |
| `warm on\|off [tier\|model] [ttl]` | companion pin (forever) or **bounded lease** for big tiers; `warm off all` sweeps | `warm -h` |
| `lm status` / `models` / `doctor` / `timeline` | server + resident + on-disk · tiers · smoke-check · merged history (q/imagine/see/fleet) | `lm` |

## Architecture

- **Server:** self-hosted `ollama serve` via LaunchAgent `com.alcatraz.local-models-ollama`
  (`bin/lm-serve`). Policy baked in: `MAX_LOADED_MODELS=2`, `KEEP_ALIVE=0`, flash-attn + q8 KV.
  Port 127.0.0.1:11434. **MLX is format-routed inside Ollama** (safetensors tags → MLX runner,
  GGUF → llama-server); measured verdict in `docs/05` §1 — Q4_K_M/llama.cpp kept for the code tier.
- **Two-tier model lifecycle:** one small **warm** companion (`gemma4-e4b-warm`, ~5.6 GB,
  `warm on` = forever-pin) + on-demand big models. **Leases** (`warm on code [ttl]`) pin a big
  model with a bounded TTL that self-heals — used by `lm fleet` and `lm opencode` automatically.
  Scheduled warmth: `warm-morning` (weekdays 09:30) + `warm-evening-off` (daily 19:00 `off all`,
  the shutdown backstop) via gcc-schedule + calendar companions.
- **Tiers (config.sh):** small=`gemma4-e4b-warm` · big=`gemma4:26b` · code=`qwen3.6:35b-a3b`
  (probe-gated 9/9) · vision=`minicpm-v`. MoE-first on this 307 GB/s machine.
- **Intents are data:** `intents/<name>.toml` (ask/cmd/title/commit/summarize/explain-code/
  describe-data/qa/review/complete) — adding a verb is dropping a file.
- **Histories are the API:** `logs/q-history.jsonl` (successes AND failures), `logs/see-history.jsonl`,
  `logs/fleet-history.jsonl`, `outputs/imagine-history.jsonl` — merged by `lm timeline`, mined
  weekly by `scripts/self-audit.sh` (gcc-schedule `lm-self-audit`, Sun 11:00 → digest + proposal
  on recurring failures). Fleet runs leave full records in `outputs/fleet/<ts>-<intent>/`.
- **OpenCode:** `~/.config/opencode/opencode.jsonc` has the `ollama` provider (all local chat
  models, qwen3.6 default). Use `lm opencode` so the lease is handled.
- **Image models** live in the HF cache; `imagine` = mflux (project `.venv`).

## Key files

- `bin/` — `lm q imagine warm see review probe lm-serve` · `_lib.sh` (colors/help/jsonl-history/
  residency/`resolve_tier`) · `config.sh` (tier vars)
- `lib/` — orchestration internals, NOT on PATH: `fleet` (fan-out runner) · `repo-index` ·
  `gemini` (the gemini lane) · `ui-verify` (the UI claim gate)
- `intents/` — the registry + schemas: `review-findings` · `ui-inventory` · `ui-verify`
- `outputs/see/` — the vision artifact store (one folder per read: source copy as read,
  read.md, meta.json, notes.md; newest 150 kept; `see open N`)
- `scripts/self-audit.sh` — the weekly feedback sink
- **`scripts/verify.sh` — the one-command smoke battery (~30s): run after ANY change and at
  session start after a handoff.** 23 checks: syntax, doctor, q envelope+format, fleet+lease,
  index, gemini lane (skips cleanly when unavailable), histories/timeline, sink, gcc hooks
  (pipe-tests), schedules. Its header lists what it deliberately does NOT cover.
- `probe/` — `items.toml` (9-item judgment suite) · `runs/` (verdicts) ·
  `fixtures/unfinished-v1/` (the finish-a-codebase exercise: fixture + conduct.sh + RESULTS.md —
  qwen3.6 completed it 16/16 under a pytest Judge, 2026-07-07)
- `docs/CAPABILITIES.md` — **the exhaustive food menu** (all abilities, grouped, with examples)
- `docs/05-perf-levers-and-usage-audit.md` §1 — **the measured MLX verdict (2026-07-07)**
- `docs/07-implementation.md` — the phased plan (Phase 1 largely built; see PENDING)
- `docs/09-local-fleet.md` — fleet design from 269 real sub-agent dispatches
- `docs/03-tool-orchestration-decision.md` — local models do NOT drive their own tools
- `docs/04` — stay on Ollama · `docs/NEXT-SESSION.md` — last session's agenda state
- Research archives: `.claude/output/20260616-model-tiers/` · `20260619-*` (landscape, judgment
  benchmarks, re-rank) · `20260620-*` (perf levers, usage audit, efficacy architecture) ·
  `20260707-1334-mlx-report/` (the MLX verdict, styled HTML)
- LaunchAgents: `com.alcatraz.local-models-ollama` · `com.alcatraz.warm-morning` ·
  `com.alcatraz.warm-evening-off` · `com.alcatraz.lm-self-audit`

## DONE (ledger — one line per wave; detail lives in git log + the linked reports)

- **2026-07-10 · visual-compare L1 (evidence half):** **`see diff` evidence pack** —
  deterministic `$0` extractors (`lib/vis-compare.py`, pure PIL, no numpy/opencv): E1 text/pos ·
  E3 palette/ΔE (CIE76) · E4 dHash+aHash · E5 grid-ΔE heatmap · E6 edge/shape grid;
  modality-adaptive (icons skip the text lanes) + comparability gate. `--json` returns the full
  pack in `.evidence`; the artifact gains `evidence.json` + `contact.png` (A│B│ΔE-heat);
  `--only`/`--grid` slice reruns diff a content-addressed cache and return just the delta
  (~0.06s, no model); every run journals to `logs/compare-history.jsonl`. Fixtures-first:
  `probe/fixtures/make-fixtures.py` (F2-F6) + `vis-battery.py` F1-F8 in verify.sh — the
  fabrication guard (identical pair → all zero) runs on every change. Both L1 and the L2
  judge were adversarially validated + hardened (L1: E3 population-weighting killed a
  JPEG-re-encode fabrication; L2: a self-check that every measured claim trace to a cited
  evidence path, after a dry-run judge fabricated grid coords). Design + built-vs-deferred:
  `docs/10-visual-compare-design.md`.
- **2026-07-10 · visual-compare L2 (judge):** **`/vis-compare` gcc skill** at
  `~/.claude/skills/vis-compare/` — native-vision judgment over the L1 pack + contact
  sheet, classifying each divergence against a user-editable `policy.md` (imitation
  doctrine + 8-rung divergence ladder with canonical slugs + weight-aware floor) into
  looks-worse / neutral / improvement / not-worth-chasing, never a raw score. `verdict.json`
  contract, `--revisit` + `suppressions.jsonl` feedback (stable content-anchor fingerprints),
  announce-before-spend. `policy.md` v1 is a DRAFT awaiting the user's taste edit. Phase
  C (loop) / D (calibration) pending.
- **2026-07-10 · compare + placement:** **`see diff A B`** — two-layer image compare for
  recreate-with-a-freer-hand workflows (deterministic OCR text/position diff both sides +
  one big-tier two-image judged report: TEXT CHANGES/LAYOUT SHIFTS/ADDED-REMOVED/STYLE/
  FIDELITY NOTES; artifact stores both sources; `text_diff` in --json). **Positional OCR**:
  `see --ocr --json` → `.data.words` with x/y/w/h + script-computed 3×3 `pos`;
  **`ui-verify --boxes`** makes placement claims rulable (verified blind). Shakedown menu:
  diy one-line traces · routing into q-history (`q show N` explains it) · websearch
  release-domain rerank (turned the claude version-compare green — the general fix beat
  the rejected lm-latest subsystem) · `lm doctor` optional-extras · residency-aware see
  timeouts · `q models`.
- **2026-07-10 · q adapts:** **`q --diy`** (plan-then-execute: warm model emits a
  schema-constrained plan, the script validates + executes — web/file/image/tier/intent,
  gray-narrated, deterministic prompt-scan backstop, doc-intents degrade instead of
  erroring) + **`q --web`** (`lib/websearch`: DDG lite, no key, cited answers, offline
  degrade). Also: LICENSE (MIT) · self-audit digest gains per-day error trend (acting on
  the Jul-10 digest: 15/18 gemini errors were day-1 auth setup, not live) · verify.sh 32.
- **2026-07-10 · capability wave:** `see --ocr` (Apple Vision exact text) · `ui-verify --app`
  (live AX-tree evidence via `ax`) · `gemini ingest-repo` (repomix) · Context7 MCP · gcc skills
  wired + maiden-tested (/ui-gripe found a real pricing-copy bug on run #1). The gemini "@-token"
  bug's true mechanism found + fixed (plan-mode model reads paths mentioned in piped content).
- **2026-07-10 · RAG swim test:** full local RAG lane built, evaled 12/13 / 0 fabrications over
  the gcc docs, then ARCHIVED by user call (parse-now > recall) —
  `.claude/output/20260710-rag-swim-test/report.md`
- **2026-07-09 · vision wave:** see artifact store (`outputs/see/`, fixes --menubar dead path) ·
  `--crop`/`--region` crop-then-read · `more`/`open`/`note` verbs · `lm ui-verify` v1 (screenshot
  lane) · gemini session self-heal · /ui-gripe skill authored.
- **2026-07-07 · agent wave:** MLX verdict (docs/05 §1, Q4_K_M kept) · `lm fleet` · 16/16
  codebase-finisher under a pytest judge · `q --format` · warm leases + `lm opencode` +
  scheduled warmth · feedback sink + weekly self-audit · `lm index`.
- **2026-07-05:** `see` (bake-off: minicpm-v) · `review`/`review-pr` · `probe` harness ·
  code-tier gate GREEN (qwen3.6 9/9, 51 GB reclaimed).
- **2026-06:** q/imagine/lm core · intents-as-data · server+warm policy · the research base
  (docs/03/04/05/09, `.claude/output/2026061*` + `2026062*`).

## PENDING — what can be done next (with the first command to run)

- **Visual-compare L2/L3 (judge + loop)** — Phase A (the evidence pack, above) is done and
  battery-green; next is the gcc `/vis-compare` skill: a native-vision judge over the evidence
  pack + contact sheet, a user-editable `policy.md` (divergence-class ladder), `suppressions.jsonl`
  feedback memory, and `--revisit`. Then the `--loop`/ledger convergence mode (Phase C) after one
  manual round-trip. First: draft `policy.md` v1 from `docs/10 §4`, then the user edits it.
  Calibration gate (Phase D): the user's real login pair + a real icon pair, user-graded.
- **Fleet over a real code task** — the one fleet leg still unexercised: a genuine Claude-called
  sweep over real files. First command: `lm fleet review src/*.ts --judge 'npx tsc --noEmit'`
  (or any intent × file-set with a mechanical judge). Measures the cloud-dispatch offset.
- **Governor policy table** — codify when work routes local/gemini/cloud (user notes 2026-07-07;
  pairs with the gcc model-tier harness + the Jul-28 telemetry review).
- **MTP speculative decode measurement** — the July research claims +74% throughput on the MLX
  path and contradicts this doc's earlier note about Ollama `-mtp-*` flags; one measurement
  session settles both. Start: check `ollama show` / server log for MTP surface on current build.
  (Counter-finding to keep: draft-model spec-dec REGRESSES on llama.cpp/Metal — never enable it
  on GGUF tiers.)
- **Gated / deferred:** `procedures/*.toml` + `lm run` (needs a 2nd real recipe) ·
  `review-pr` worktree variant · imagegen §8 upgrades ·
  dev-ControlNet · voice lane (whisper.cpp ears + Kokoro voice — researched, fits zero-idle,
  waiting on user want).
- **Archived, not pending:** the RAG lane (see DONE; `lm rag` dispatchable, unadvertised;
  rebuild ≈20s). The Jul-10 augmentation research digest ranks further candidates:
  `.claude/output/20260710-augment-research/digest.md`

## Key lessons (load-bearing)

- For small local models, **the prompt is a bigger quality lever than the model**.
- `think:false` must be the **API flag** — prompt-level "no thinking" is ignored.
- **Re-quantized weights need re-gating** — NVFP4 kept conclusions, lost terseness; the probe
  caught what tok/s couldn't. Trust = a passing gate, never a spec sheet.
- **MLX in Ollama is format-routed, not a toggle** — verify engagement from the server log line,
  never the tag name. Benchmark prefill with fresh prompts (KV-cache reuse inflates ~30×).
- **Leases, not pins, for big models** — bounded TTLs self-heal; `keep_alive` is last-writer-wins.
- **Worker retry feedback must ship evidence + a character-precise delta** — restating the spec
  converges never; the delta converged in one round (unfinished-v1 RESULTS.md).
- **Conductor pipelines are bash, never inline zsh** — zsh `echo` expands `\n` inside JSON envelopes.
- A tool isn't delivered until it's **on PATH and invoked as a bare command**.
- **Synthetic repro ≠ workload repro** — a bug report is only cleared by replaying the reporter's
  workload class; six synthetic shapes all passed while the first real 1.3MB pack failed.
- **Pick the evidence lane by surface:** AX tree for running native apps (exact), `see --ui` for
  any pixels (structured), `see --ocr` for verbatim strings. Verify before quoting; judge natively.
- **Vision trust boundary (measured):** zero fabrications on enumerables, weak on aesthetics —
  local vision is a verifier and checklist-generator, never a critic.
