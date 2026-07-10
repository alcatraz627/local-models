# Augmentation research digest — cross-ranked for this stack

<!-- sessions: local-next-a4@2026-07-10 -->

Synthesis of three parallel research sweeps (`local-inference.md` · `harness.md` ·
`sysutils.md`, 792 lines total, all sourced). Ranked by leverage-per-effort for THIS
machine and toolkit, with wiring suggestions into the existing verbs. Star counts and
license claims are as-searched; spot-check before betting on any single number.

## Convergent findings (multiple researchers, independently)

- **whisper.cpp** (local-inference #10, sysutils #10) — ears for the stack. Metal/ANE
  encoder, ~10x realtime on this chip, per-utterance load fits zero-idle exactly.
  The single most agreed-on addition.
- **On-device OCR, two lanes** — sysutils backs thin Vision-framework CLIs
  (ocrit / mac-ocr: zero-install-class, word-level boxes); local-inference backs
  PaddleOCR-VL (0.9B model, tables/formulas). Take the native CLI first — it slots in
  as a `see` fallback sense for pixel-only text; pull the model only if tables/formulas
  become a real workload.
- **Structured beats scraped** — osquery (SQL over processes/sockets/packages) and
  AeroSpace JSON window queries are the same idea `see --ui --json` and `ui-verify`
  already bet on: typed reads over text scraping, at the OS layer.

## Tier 1 — free or config-level (do whenever convenient)

1. **Prefix-cache discipline** — fleet/judge calls share rubrics; keeping the shared
   prefix byte-identical (no timestamps in system prompts) + an active lease makes
   Ollama's KV reuse fire on every fan-out call. Zero infrastructure, pure discipline.
2. **SQLite FTS5 over the toolkit's own histories** — q/see/fleet/gem JSONL logs are
   exactly the corpus FTS5 eats; exact-token recall (error codes, flags) that vector
   search misses. Already on every Mac. Would give `lm timeline` a search verb.
3. **fswatch** — FSEvents-driven "fire when the file lands" replaces the polling
   watcher loops this account keeps hand-rolling (see shell-mem's BG watchers).
4. **mdfind** — metadata search (kind/date/EXIF) rg can't see; zero install.
5. **terminal-notifier + dnd** — a notify hand plus an "is the human interruptible"
   sense; pairs with the existing notification patterns in scheduled jobs.

## Tier 2 — small installs, genuinely new senses/hands

6. **Native Vision OCR CLI (ocrit or mac-ocr)** — text-from-pixels fallback for
   `see` when an app has no AX tree and local VLM recall isn't enough. Candidate
   wiring: a `see --ocr` lane that runs both and lets the caller diff.
7. **ax-cli / AXorcist** — the semantic-UI ground truth lane. Role/title/value/state
   for every element, `wait`/`watch` primitives instead of screenshot polling. This is
   the natural THIRD leg for `ui-verify`: AX tree for native apps (exact), `see --ui`
   for web/pixels (general), native vision for judgment. Early-stage tooling — trial
   before trusting.
8. **whisper.cpp** — as above. Ears.
9. **osquery (osqueryi one-shot mode)** — typed system state for agents; skip the
   daemon, keep zero-idle.
10. **cliclick** — minimal fallback hand (coordinate clicks); pairs with an OCR/AX
    read for targeting. Tiny.
11. **Peekaboo** — the full computer-use package (annotated screenshots + click/type
    against element IDs, background-app input WITHOUT focus stealing — which would
    retire the desktop-automation focus-steal confirm friction for some flows). Bigger
    adoption: Screen Recording + Accessibility grants, MCP server optional. Trial as
    a complement to the see/ui-verify lane, not a replacement.

## Tier 3 — harness adds (medium effort, clear fit)

12. **Context7 MCP** — version-pinned live docs at query time; cheapest hallucination
    reducer with zero overlap against anything present.
13. **Repomix** — the packing step the `lm gemini ingest` lane currently hand-rolls
    with cat loops; tree-sitter compression ~70%. Direct upgrade to an existing verb.
14. **ast-grep** — structural search beside the rg mandate; MCP or plain CLI.
15. **semgrep as a deterministic pre-pass** — run before `/code-review` /
    `/security-review` so the LLM pass spends judgment on what pattern-matching
    can't catch.
16. **Sandboxing, two tiers** — Safehouse (seatbelt wrapper under the hooks; the
    hooks currently run in-process and are the ONLY backstop) for the harness
    process; Apple `container` 1.0 (this machine is on macOS 26 — requirement met)
    for genuinely untrusted agent-generated code. Different threat models; trial
    Safehouse on one scheduled job first.
17. **CodeGraph / Serena** — call/import graph + LSP-grade symbol precision. Note the
    overlap: `lm index` already answers "where is X" — these add "what CALLS X" and
    refactor-grade edits. Adopt only if that question starts burning tool calls;
    avoid GitNexus regardless (PolyForm Noncommercial — license landmine).

## Tier 4 — motivated but gated (measure or wait for the trigger)

18. **MTP speculative decoding** — the researcher reports a 74% throughput gain
    (10.5→18.3 tok/s, 27B-class) on the MLX path and claims Ollama hasn't exposed MTP
    flags. **That contradicts STATE § PENDING**, which names `-mtp-*` tags and
    `OLLAMA_MLX_MTP_*` env vars from prior local recon — one of the two is stale.
    Either way the parked "MTP — unmeasured" item just gained a strong motivation;
    the measurement session should start by checking what today's Ollama actually
    exposes. **Counter-finding worth keeping: classic draft-model speculative decoding
    goes BACKWARD on llama.cpp/Metal — never enable it on the GGUF-routed tiers.**
19. **MLX continuous batching (vllm-mlx / mlx_lm.server)** — up to ~4x at 8x
    concurrency maps directly onto fleet fan-out, but means serving outside stock
    Ollama. Gate: only if the fleet-over-code-task run shows real queueing pain.
20. **KV-cache Q4 (MLX)** — the serve policy already bakes q8; the Q4 increment buys
    32K+ context on the big tiers. Fold into the MTP measurement session.
21. **Kokoro/Piper TTS (mlx-audio)** — a voice, if spoken status ever matters.
22. **Reranker (bge-reranker-v2-m3) + EmbeddingGemma-on-ANE** — real upgrades to the
    RAG lane, which is ARCHIVAL by user decision; park with it. (The reranker is the
    textbook fix for the swim test's one failure — heading-dominated retrieval —
    noted here so the report's root cause has a named remedy if RAG is ever revived.)
23. **GEPA / BAML / semantic router / Claude Squad** — each fine, each waiting on a
    trigger that hasn't fired (prompt-tuning need, schema-quirky model, routing
    frequency, visual multi-pane preference).

## Endorsed skips (researcher reasoning checked, sound)

exo (needs a second Mac) · stock vLLM (CUDA-first) · llama.cpp Metal spec-dec (goes
backward — see #18) · GitNexus (license) · mem0 (would drift against the existing
layered memory — the externally-mutated-state caution applied to memory) · cloud-VM
agent platforms (local equivalents already built) · GUI clipboard managers (no stable
API; a pbpaste→FTS5 loop is more durable) · yabai SIP mode (AeroSpace reads state
without touching SIP) · btop/mactop as agent-facing observability (osquery is typed).

## Suggested first bites (if asked to pick)

1. FTS5 over the histories + prefix-cache discipline — free, touches existing verbs.
2. ocrit + ax-cli trial wired as evidence lanes for `see`/`ui-verify` — extends this
   week's vision work directly.
3. Repomix into `lm gemini ingest` — one existing verb, immediate quality bump.
4. The MTP/KV measurement session — resolves the STATE-vs-research contradiction and
   the longest-parked PENDING item in one sitting.
