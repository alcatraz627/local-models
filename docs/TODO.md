# Local Models — TODO

Living checklist. Full plan: `docs/00-plan.md`. `[~]` = in progress.

## Slice 1 — Foundation / resource governance  (DONE 2026-06-09)
- [x] Pull `gemma4:e4b-it-qat` (Tier W model)
- [x] Build `gemma4-e4b-warm` (num_ctx 8192) from Modelfile
- [x] Verify fresh load honors num_ctx + q8 KV cache (K(q8_0), flash enabled)
- [x] Test `warm on|off|status`; idle footprint 5.6GB ON / ~0 OFF
- [x] **Pivot:** self-hosted `ollama serve` (LaunchAgent) — app ignored launchctl env
- [~] Carry-over: warm+big coexistence is RAM-headroom-dependent (system_limited eviction);
      acceptable per no-degradation rule. Revisit if it bites in practice.

## Slice 2 — Snappy companion (extend llm-mini)
- [ ] **Make "quick" actually quick & direct**  ← feedback 2026-06-09
      `ollama run gemma4:12b "...path of procs on port 8001"` returned a *thinking trace +
      3-OS essay + summary table* for a one-command question. The quick path must:
        - inject environment context (macOS + zsh; assume my env; never enumerate other OSes)
        - disable the "Thinking…" trace on the quick path
        - be intent-typed: `cmd` → a single shell command only (post-extracted, copy-ready);
          `ask` → ≤2 sentences
        - use a terse, no-preamble system prompt
        - A/B the model for the `cmd` intent: e4b vs llama3.2 vs qwen2.5-coder:3b
      Acceptance: `q "…port 8001…"` returns ONE macOS command, no essay, fast.
- [ ] Wire the warm model into llm-mini's local tier (keep Haiku fallback)
- [ ] tab-title fire-and-forget via `mini_quick`

## Slice 3 — Vision parse
- [ ] gemma4 vision wrapper → `<vlm_parse>` handoff to Claude; moondream fast path

## Slice 4 — Image-gen subsystem
- [ ] ComfyUI + `comfy-start/stop` + Flux.1 schnell + git-tracked preset library

## Later / V2
- [ ] LAN M4 Pro offload + load-balancing; `qwen3-vl:32b`; persist `OLLAMA_*` env across reboot
