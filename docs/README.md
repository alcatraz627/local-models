---
reader: anyone looking for a doc in this project, or about to add one
---

# Docs: index and rules

Every doc in this folder is listed here once. Start with the first table. The rest is reference and history.

## Start here

| Doc | Read it for |
|---|---|
| [STATE.md](STATE.md) | What works today, the model in each seat, and the open work. |
| [CAPABILITIES.md](CAPABILITIES.md) | Every command, with examples and limits. |
| [GOALS.md](GOALS.md) | What each command is for and how its approach was judged. |

## Guides

How to do one thing. Kept current.

| Doc | Read it for |
|---|---|
| [opencode.md](opencode.md) | Running the opencode coding agent on the local models. |
| [model-refresh-guide.md](model-refresh-guide.md) | The monthly check for a better local model. |
| [model-notes.md](model-notes.md) | How models outside the usual lane did on real work, one row per run. |
| [model-runs/README.md](model-runs/README.md) | What counts as such a run, and how to file a long report. |
| [q-spec.md](q-spec.md) | The contract for `q`: intents, the JSON envelope, schema-bound answers. |

## Design and decisions

Numbered in the order they were written. Each one records what was decided or designed on its date. When one disagrees with STATE.md or CAPABILITIES.md, those two are right. Code comments cite these by number (`docs/03`), so the numbers never change. There is no 02.

| Doc | Subject | Kind |
|---|---|---|
| [00-plan.md](00-plan.md) | The first plan for the project, June 2026. | history |
| [01-llm-mini-redesign.md](01-llm-mini-redesign.md) | Folding `q` into the older llm-mini tool. | on hold |
| [03-tool-orchestration-decision.md](03-tool-orchestration-decision.md) | Why the command reads files and runs tools, never the model. | decision |
| [04-ollama-vs-llamacpp-decision.md](04-ollama-vs-llamacpp-decision.md) | Why the server is Ollama. | decision |
| [05-perf-levers-and-usage-audit.md](05-perf-levers-and-usage-audit.md) | Speed measurements and a usage audit, June 2026. | measurement |
| [06-local-orchestration-design.md](06-local-orchestration-design.md) | Several local models working as one system. | design |
| [07-implementation.md](07-implementation.md) | The build plan for that system. | design |
| [08-vision-lenses-design.md](08-vision-lenses-design.md) | Reading modes for `see`. | design |
| [09-local-fleet.md](09-local-fleet.md) | Batch work across many files. | design |
| [10-visual-compare-design.md](10-visual-compare-design.md) | Checking that one image faithfully copies another. | design |
| [11-speech-lane.md](11-speech-lane.md) | Speech to text: `lm hear`. | design |

## History

| Doc | Read it for |
|---|---|
| [LEDGER.md](LEDGER.md) | When each thing was built and why, newest first. |

## Reviews

One report per review or trial, named by date. Never edited after the fact; a later finding gets a new report.

| Doc | Subject |
|---|---|
| [reviews/20260926-lm-codex-pi-review.md](reviews/20260926-lm-codex-pi-review.md) | The toolkit, Codex and the Pi, reviewed for owner decisions. |
| [reviews/20260926-lm-followup-audit.md](reviews/20260926-lm-followup-audit.md) | Behavior audit of the commands before the follow-up work. |
| [reviews/20260926-lm-implementation-trials.md](reviews/20260926-lm-implementation-trials.md) | Results of that follow-up work and its model trials. |
| [reviews/20260927-codex-idream-live-pass.md](reviews/20260927-codex-idream-live-pass.md) | One bounded live run of Codex on i-dream. |
| [reviews/20260927-csync-mac-peer-review.md](reviews/20260927-csync-mac-peer-review.md) | The Mac as a capability peer for the Pi assistant. |
| [reviews/20261022-model-comparison.md](reviews/20261022-model-comparison.md) | Seven models on 42 vision cases; the basis for today's vision default. |
| [reviews/20261120-lm-and-the-z-tool-standard.md](reviews/20261120-lm-and-the-z-tool-standard.md) | The lm commands measured against the z- tool standard, with what to align. |
| [model-runs/20261031-sonnet-5.5-main-ghostty-settings.md](model-runs/20261031-sonnet-5.5-main-ghostty-settings.md) | Sonnet 5.5 as the main agent on one build. |

## Research

Background reading gathered in June 2026, before the tools were built. It is not the current model list.

| Doc | Subject |
|---|---|
| [research/20260609-runtime-orchestration.md](research/20260609-runtime-orchestration.md) | Model servers compared. |
| [research/20260609-vision-models.md](research/20260609-vision-models.md) | Vision models for screenshots. |
| [research/20260609-image-gen-stack.md](research/20260609-image-gen-stack.md) | Image generation tools compared. |
| [research/20260610-imagegen-local-workflows.md](research/20260610-imagegen-local-workflows.md) | Image generation on Apple Silicon. |
| [research/20260610-imagegen-pipeline.md](research/20260610-imagegen-pipeline.md) | Conditioning and pipeline techniques. |
| [research/20260610-imagegen-prompting.md](research/20260610-imagegen-prompting.md) | Prompting image models. |
| [research/20260610-imagegen-techniques.md](research/20260610-imagegen-techniques.md) | The techniques above, consolidated. |
| [research/20260610-art-direction-brief.md](research/20260610-art-direction-brief.md) | Art direction for an image assistant. |

## Archive

Superseded files, kept so old links resolve. Nothing here is current.

| Doc | Was |
|---|---|
| [archive/TODO.md](archive/TODO.md) | The June 2026 task list. Open work is in STATE.md now. |
| [archive/NEXT-SESSION.md](archive/NEXT-SESSION.md) | A per-session agenda. Replaced by STATE.md. |
| [archive/qol-backlog.md](archive/qol-backlog.md) | One small idea for `q` output, never built. |

`archive/next-session-reminder.sh` is a one-time reminder that fired in July 2026. No schedule runs it.

## Rules for adding a doc

1. **Pick the kind first.** The kind decides the name and the folder.

| Kind | Name | Where | Edited later? |
|---|---|---|---|
| Guide or reference | a plain name, `opencode.md` | `docs/` | yes, kept current |
| Design or decision | the next number, `12-topic.md` | `docs/` | only to mark it superseded |
| Review, trial or audit | `YYYYMMDD-topic.md` | `docs/reviews/` | no |
| Model run report | `YYYYMMDD-model-role-topic.md` | `docs/model-runs/` | no |
| Research notes | `YYYYMMDD-topic.md` | `docs/research/` | no |

2. **Open with who it is for.** The first lines are frontmatter with one `reader:` line, then a title, then a sentence or two saying what the doc is. Older docs predate this and are left as they are.
3. **List it here.** Add one row to the right table above. `probe/fixtures/docs-index.py` fails when a doc is missing from this index or a link here points nowhere, and `scripts/verify.sh` runs it.
4. **Say what is true now in STATE.md, not in a new file.** Task lists, agendas and "next session" notes go stale the day they ship. Open work has one home, the table in STATE.md.
5. **Retire by moving.** A doc that no longer holds goes to `docs/archive/` with a row saying what replaced it. Its old path is fixed wherever it was linked.
6. **End a current doc with its sources and a review date**, as STATE.md does, so a reader can tell how fresh it is.

Reviewed 2026-11-20.
