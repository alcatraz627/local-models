# Decision: local file reading & tool orchestration (2026-06-16)

Decision record for "should the local model read/parse local files by orchestrating its own
tools?" Resolved by a full MAGI deliberation (5 voters, unanimous). Full archive:
`~/.claude/assets/magi/20260616-1630-local-tool-orchestration/`. Read this before re-opening
the question — the no is reasoned, not reflexive.

## What triggered it

A user ran `q describe-data --model gemma4:31b "summarize the financials in <path>.pdf"`. The
path was only **text in the prompt** — nothing read the file — so the model truthfully said "I
can't access your filesystem." The ask that followed: a composable tool library the model
orchestrates itself, reading multiple local files, no cloud.

## The verdict

```
✓ YES — build (deterministic, cheap, no new runtime)
   1. ctx_required guard: summarize/describe-data/explain-code/qa REFUSE with no
      document and nudge at a path named in the prompt. THIS fixes the incident.
   2. q --ctx/--file extracts text LOCALLY by type: PDF→pdftotext, Word/RTF/HTML→
      textutil, text/csv/json/code as-is, binaries refused (file --mime-encoding).
   3. Multi-file = pipes + Claude Code composing them. No local loop.

✗ NO — do not build (fails capability, security, AND purpose)
   A model-driven loop where a heavy local model picks which tool/file to read
   next, iterating. The model CHOOSING the next step is the part that fails.
```

The line the whole panel drew:

```
DETERMINISTIC PIPELINE                     MODEL-DRIVEN LOOP
resolve path → extract → ONE q --ctx call  model emits tool_call → run → feed
→ answer                                   back → repeat
clears ~90%-of-Opus for "read this file"   ~0.95/call compounds to ~66% at 8
                                           steps; multi-file cliff; injection
```

## Why NO (the three reasons, so they're not re-litigated)

1. **Capability.** `gemma4:31b` was the wrong instinct twice: Gemma has no reliable native
   tool-calling (needs a QLoRA XML hack) and a 31B *dense* model is bandwidth-bound (~12–22 tok/s),
   so a multi-round loop is slow. The realistic local tool-caller is **Qwen3-Coder-30B-A3B**
   (~96% well-formed calls, 70–130 tok/s MLX). Even then, a single-shot / 2–3-call sequence is the
   ceiling; once the model *chooses* the next file it's in the multi-step regime this project's own
   research (`.claude/output/20260612-lm-research/claude-integration.md`) flags as local models'
   weakest area — below the user's ≥90%-of-Opus bar.
2. **Security.** A loop where document *contents* steer which read commands fire is indirect prompt
   injection (OWASP LLM01). "Read-only over $HOME" is an exfiltration primitive, and a weak-adherence
   local model is the least able to resist a malicious document. The thin companion's "returns text,
   never executes" invariant was a correct boundary.
3. **Purpose.** A heavy per-task model picking tools is the "multi-step analysis" `q-spec` names a
   non-goal, and the per-intent-model pattern `docs/00-plan.md §12` killed (after *prompt > model*
   won the A/B). **Claude Code is already the world-class local orchestrator that reads files and
   runs tools safely** — a local loop would be a worse copy. "Quarantine in `lm agent`" changes the
   door, not the room.

## What "composable tools" correctly means here

The user's composability instinct is right — but the orchestrator is **you + Claude Code**, not a
local model. The Unix tools already compose through stdin (`cat`, `ls`, `rg`, `pdftotext`). The
**only** genuinely missing primitive was *type→text extraction*, now inside `q --ctx/--file`. We
deliberately did **not** build a registry re-wrapping coreutils (`read-file`/`scoped-ls`/`scoped-rg`)
— that's the "junk drawer" the user pushed back on, and `find`/`grep`/`git` carry exec/write params
that make an allowlist a security hole anyway.

## If this is ever revisited — probe first, don't build on faith (~2h)

- 3 read-only, **typed-verb** tools (`read_file(path)`, `convert(path,fmt)`, `list_dir(path)`) —
  typed verbs, **never** allowlisted binaries; `realpath`-jail under one `--root`, deny symlink
  escape, no shell interpolation, hard `≤3-iteration` + wall-clock caps.
- Caller = **Qwen3-Coder-30B-A3B** via Ollama native `/api/chat` `tools` (the `/v1` path silently
  drops tool calls). 15-task eval. **GO only if ≥90% valid tool_calls AND ≥85% correct in ≤3 calls
  AND p50 <12s.**
- **Critical control:** run the non-loop `q --ctx` baseline on the same tasks. If it matches quality
  (it will, for read-and-summarize), the loop fails the anti-over-engineering bar — 2h spent to
  avoid a 500-line mistake.

## Provenance
- MAGI archive (proposals, votes, supervisor nomination): `~/.claude/assets/magi/20260616-1630-local-tool-orchestration/`
- Winner: voter-4 (ml-realist), 4.84; matched the supervisor's pre-vote nomination; no override.
- Related locked decision this upholds: `docs/00-plan.md §12`.
