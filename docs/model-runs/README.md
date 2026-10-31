---
reader: the owner and any agent choosing a model, or filing how one did
---

# Model runs: how off-lane models did on real work

This folder keeps the track record of models used outside the owner's usual lane. When you pick a model for a seat, read what it did here before trusting a spec sheet. The record is flawed and anecdotal, but it beats guessing.

## What counts as off-lane

The usual lane is Opus as the main agent, sometimes Fable. Everything else gets a record:

- a Claude model in a seat it rarely holds, such as Sonnet or Haiku as the main agent
- a non-Claude model in any seat: Gemini, Codex or GPT, a local model
- a familiar model doing an unusual job, such as Haiku as a validator

Routine sub-agent use in a lane the gcc already routes to, such as Sonnet for a bounded read-only sweep, does not need a record unless something surprising happened.

## Where things go

| File | Holds |
|---|---|
| `../model-notes.md` | The ledger: one table per model, one row per run, newest first. Every run gets a row. |
| `model-runs/<YYYYMMDD>-<model>-<role>-<topic>.md` | A long report, only when a run teaches something a row cannot hold. Link it from the ledger row. |

## How to file a run

1. Add a row to the model's table in `../model-notes.md`. Make the table if the model has none. The columns are date, task, how it was checked, result and a note.
2. If the run needs more than a row, write a report here and link it from the row's note.
3. Keep the model's standing read (the bold line above its table) current when a run changes it.

A report has these parts, and leaves out any that the run has nothing for:

- frontmatter with `model`, `role`, `date` and a one-line `verdict`
- **What to take from it**: the pick-time advice, first
- **The run**: session, task, repo, sub-agents, checkpoint
- **How it was checked**: what was run, and what was not
- **Where it left expected behavior**, **Where its judgment was thin**, **Where it ran against the gcc's tuning**: each point with its evidence
- **Use it for, avoid it for**

Write a claim only when you checked it. Mark anything else UNCONFIRMED.

## Reports

| Date | Model | Role | Report |
|---|---|---|---|
| 2026-10-31 | claude-sonnet-5-5 | main agent, UI plus engine build | `20261031-sonnet-5.5-main-ghostty-settings.md` |

## Where the gcc points here

`~/.claude/rules/model-tier-routing.md` tells agents to file an off-lane run here. `~/.claude/LOOKUP.md` lists this folder under local models.
