# Raising local-model EFFICACY via software, not hardware (2026-06-20)

Efficacy = **output quality + trustworthiness per unit of the user's effort, counting rework**
(`~/.claude/memory/global/feedback_efficacy_over_speed.md`). The watermelon question: improve
the *growing system*, not the fruit size. Detail files:
[scaffolds-orchestration](scaffolds-orchestration.md) · [context-retrieval](context-retrieval.md) ·
[reliability-adaptation](reliability-adaptation.md).

## The thesis (all three agents converged, HIGH confidence)

**Scaffold moves the *same model* 10–20 pts** on SWE-bench-class tasks (Opus 4.8: 69.2% vendor
harness vs 51.9% standardized — identical weights). A **4B model recovers ~90% of frontier-agent
performance** via context-control + tool discipline. **Unifying mechanism:** every lever either
removes a failure-class the model makes unaided (wrong file, broken diff, hallucinated API, stops
early) OR moves verification from the user into the loop (tests/lint/critic). Both cut rework →
directly raise efficacy as the user defines it.

## The ecosystem (your analogy → the levers)

```
 SOIL & ROOTS   what you feed it      → context engineering   ★★★★★ cheapest, biggest
 WATER LOOP     closing the loop      → verify + self-repair  ★★★★★ the trust engine
 GREENHOUSE     the harness           → scaffold/orchestration★★★★☆ structure > size
 CROP ROTATION  right plant per plot  → routing / cascade     ★★★★☆ the tiered spine
 GENE EDITING   deep customization    → LoRA on your conventions ★★★☆☆ high ceiling, research
 GREENHOUSE FX  redundancy            → test-gated best-of-N   ★★☆☆☆ selective only
```

## Prioritized adoption ladder (efficacy-per-effort)

1. **Strong system prompt** (★★★★★, ~0 effort) — smaller models gain *disproportionately*
   (arXiv 2602.15228 corroborates your own 4B-beats-coder finding). You already do this in `q`.
2. **AGENTS.md convention injection** (★★★★★) — inject repo conventions so the model stops
   guessing your style. Near-zero effort.
3. **Constrained / structured decoding** (★★★★★, low effort) — Ollama `format` schema /
   Outlines+mlx-lm / XGrammar-2 / GBNF *guarantee* valid JSON/tool-calls → kills the format-rework class.
4. **Verify → self-repair loop** (★★★★★) — run tests/lint/types, feed errors back. External
   feedback flips self-correction from harmful to **+21–32 pts**. The trust engine — a passing
   test is a delegation receipt; model confidence is not (LLM self-confidence is miscalibrated).
5. **Structural repo map** (★★★★☆) — aider's tree-sitter + PageRank symbol graph. **Beats BOTH
   raw file dumps AND vector RAG for code** (2026 embeddings "are not code-oriented").
6. **Context hygiene / anti-context-rot** (★★★★☆) — keep prompts tight; task + key code at
   START and END; summarize-and-restart on long runs. Small models degrade by info *position*.
7. **Routing / cascade keyed to the verifier** (★★★★☆) — easy→lean, hard→beefy/cloud;
   29–69% savings. **Trap: "local-draft → cloud-review" BACKFIRES** (+31–41% cloud tokens by
   re-sending context) — prefer route-then-commit over draft-everywhere-then-escalate.
8. **Stable-prefix KV / prompt caching** (★★★☆☆) — reuse system-prompt KV across calls.
9. **Cross-session memory file** (★★★☆☆) — a curated NOTES/decisions file cuts re-explaining.
10. **Test-gated best-of-N** (★★☆☆☆, selective) — only when first attempt fails; pick the
    candidate passing the most tests. Blanket self-consistency = ~1% gain at 15–20× cost.
    **Self-MoA > mixed-MoA** — sample your one best model hot; no model zoo needed.
11. **Convention LoRA** (★★★☆☆, research project) — mlx-lm QLoRA, ~1hr / 200–500 examples,
    `mlx_lm.server` hot-swaps adapters. Adopt only after 1–7 and once a *specific* repeated
    convention-rework is identified. Bottleneck = data-curation discipline.

## Best framework fit + alignment with your existing decisions

- **aider** is the closest fit (CLI-native like `q`/`lm`, best Ollama path, bundles repo-map +
  architect/editor split + test-loop). Continue (per-role routing) and Roo (Architect/Code/Debug)
  are alternatives. **Ollama trap:** default 2k context silently truncates — aider auto-fixes.
- **Your `docs/03` deterministic-orchestrator decision is the recommended pattern** — Agentless-style
  localize→repair→validate: your code drives narrow verifiable sub-tasks, the model fills tight
  holes. The research independently endorses exactly this for a fixed local model.
- **Weak local models handle `whole`/`editor-whole` edit formats better than diffs** — prefer those.
- **Re Task #24 (embedder+RAG):** for *code*, a repo map beats vector RAG; keep RAG for the
  *docs/research* re-fetch tax (its original justification), not for code retrieval.
