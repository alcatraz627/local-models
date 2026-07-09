# RAG swim test — local vector DB over gcc docs, agent answers from retrieval only

<!-- sessions: local-next-a4@2026-07-10 -->

**Verdict: the stack works.** 12/13 answers correct, 0 fabrications, both negative
probes refused cleanly. The single failure was a retrieval miss (fact buried under an
unrelated heading), and the answering model correctly said NOT IN CONTEXT rather than
guessing — the honesty contract held exactly where it mattered.

**Status: test scaffolding, not an adopted capability** (user call 2026-07-10:
"probably don't wanna use RAG locally, this is JUST for the test"). `lm rag` is
dispatchable but unadvertised; keep-vs-trash decision pending.

## The stack (built for this test, ~1 hour)

| Piece | Choice | Why |
|---|---|---|
| Embedder | `nomic-embed-text` via local Ollama (274 MB, 768-dim) | on-demand load, zero-idle, honors the residency contract |
| Store | `sqlite-vec` v0.1.9 in the project venv | a 3.9 MB file — no server, no idle cost |
| Answerer | `q --ctx -` on the warm small tier (gemma4-e4b) | conductor retrieves, model only answers (docs/03) |
| Corpus | gcc docs: rules/ features/ conventions/ + 6 root indices | 88 files → 865 chunks; secret-scanned before ingest |

Ingest: 865 chunks embedded in **17 s**. Eval: 13 grounded answers in **51 s** (~4 s
each). Total cost: **$0**, nothing left the machine.

## Protocol

The grader (Claude main agent) authored 13 questions from the real docs with ground
truth verified against the files on disk at eval time (several rules were edited by a
sibling session this same week, so in-context copies were not trusted). The answering
agent saw ONLY the top-6 retrieved chunks per question — never the files. Prompt
contract: cite excerpts per claim; if the excerpts lack the answer, reply exactly
NOT IN CONTEXT.

11 positives (exact values, procedures, cross-doc, paths, numbers) + 2 negatives
(plausible questions whose answers are verified absent from the corpus).

## Results

| # | id | type | verdict |
|---|----|------|---------|
| 1 | corrections-max | exact | **FAIL — retrieval miss** (see below) |
| 2 | commit-scan | procedure | pass |
| 3 | gate-mute | exact | pass — includes the machine-wide-mute nuance edited into the doc this week |
| 4 | subagent-ceiling | cross-doc | pass |
| 5 | bash-version | exact | pass |
| 6 | diagram-width | number | pass |
| 7 | cron-retire | procedure | pass |
| 8 | agent-tag | exact | pass |
| 9 | ctx-70 | procedure | pass |
| 10 | proposals-file | paths | pass |
| 11 | wal-retention | number | pass |
| 12 | NEG-k8s | negative | pass (refused; paraphrased rather than exact sentinel) |
| 13 | NEG-dbpass | negative | pass (exact NOT IN CONTEXT) |

**Metrics**

- Answer accuracy: **12/13 (92%)** · fabrications: **0/13**
- Negative-probe compliance: **2/2** refused (1 exact sentinel, 1 paraphrase)
- Retrieval hit-rate, doc-level: **11/11** · chunk-level: **10/11**
- Answerer: warm small tier sufficed — no --big escalation was needed anywhere

## The one failure, root-caused

Q: "max patterns mistake-patterns.md may hold?" (expected: 20). The answer chunk lives
in `corrections.md § How /atone writes the event` — a **"Rules for the file" paragraph
under a heading about something else entirely**. The chunk embedding prepends
`path § heading`, so the vector leans toward atone-event semantics and the chunk ranks
outside top-8 for any "max patterns" phrasing. The model, given chunks without the
fact, correctly refused. Classic RAG lesson, reproduced on real docs: **facts filed
under unrelated headings are invisible to heading-weighted retrieval**. (Fixes exist —
per-paragraph chunking, heading-less embedding variants, hybrid BM25 — none built,
since this stack is test-only.)

## What this answers for "fleet at real volume"

The ingest leg IS the volume test: 865 embed calls batched through the local lane in
17 s wall with zero babysitting, and the 13-question judged eval ran unattended in
51 s. The local stack handles real batch work at effectively zero cost; the offset vs
cloud dispatch for THIS job class is total (100% local, $0). The remaining open
question from STATE § PENDING — a Claude-called `lm fleet` sweep over a code task —
stays open; this test exercised volume through the embed/eval path instead.

## Files

- `questions.json` — the eval set with expected answers + sources
- `answers.jsonl` — full answers with citations and per-question latency
- Scaffolding (pending keep/trash): `lib/rag`, `lib/rag.py`, `config.sh`
  RAG_EMBED_MODEL, `bin/lm` rag dispatch (unadvertised), `outputs/rag/index.db`,
  `.claude/conventions/env-access.md` (the env pattern doc stays regardless — it
  records the project convention, not the RAG stack)
