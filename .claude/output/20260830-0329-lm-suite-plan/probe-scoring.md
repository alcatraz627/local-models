# Probe scoring, the 4 unscored qwen3.6 runs

Scored by an opus seat on 2026-08-30 under owner delegation. Every verdict is
overridable; the boxes are filled in the run files themselves and each note ends
with "scored by opus seat 2026-08-30, owner may flip".

## The reading, first

**The code tier clears the scoped-worker-under-a-judge seat, and this scoring pass
adds almost nothing to what was already known.** Of the 4 files, 2 are byte-identical
replays of a run the owner already scored 9/9, and 1 produced no model output at all.
The corpus is 4 files but only **2 distinct observations**.

**It does not move D11.** D11 asks for five E1-shaped dispatches on varied real tasks
in five named repos. The probe suite is a judgment battery on fixed synthetic items,
not a dispatch against a pre-written mechanical judge, so none of these files counts
toward that bar. The 80B decision still waits on work nobody has run.

## Per file

| Run file | Items | Pass | Fail | What it is |
|---|---|---|---|---|
| `qwen3.6_35b-a3b-20260621-162941.md` | 6 | 6 | 0 | Replay (6-item prefix of the owner-scored set) |
| `qwen3.6_35b-a3b-20260621-171050.md` | 9 | 9 | 0 | Replay (byte-identical to the owner-scored set) |
| `qwen3.6_35b-a3b-20260621-1-20260630-161534.md` | 9 | 0 | 9 | VOID, every item is an HTTP 404 |
| `qwen3.6_35b-a3b-nvfp4-20260707-131716.md` | 9 | 9 | 0 | The one genuinely new observation |

On the void run: marking 9 fails is a bookkeeping act, not a judgment about the model.
The harness returned 404 for every item and the model never spoke. The box reads fail
only because this suite's doctrine is that a gate which never ran never passed. Do not
read that row as a model regression, and keep it out of any pass-rate denominator.

## The three worth your eyes

**1. `passk-reliability` has been handing out a free pass in every run ever recorded,
including your own scored one.** The runner pins `options: {"temperature": 0}`
(`bin/probe:36`), so five identical answers to five identical prompts is guaranteed by
construction. The item's stated axis is "reliability (pass^k, not pass@1), consistency
across cold runs" and the auto-flag reports "1 distinct answer(s) across 5 cold runs",
but at temperature 0 that number cannot be anything else. It measures no variance.

The label is wrong twice over. `chat()` defaults to `keep_alive="5m"` and the only
`ollama stop` is at `bin/probe:113`, after the whole eval, so the five calls are warm
and sequential against a resident model. They are not cold runs. This is the repo's own
blind-fixture shape: an assertion that cannot fail by construction. I passed the item in
all three live runs because the *command* is genuinely BSD-valid, which is real evidence.
The 5/5 half is not. Fixing it means sampling at a real temperature, or unloading between
runs, or both.

**2. Two of the four files are the same run.** Every model response in `20260621-171050`
is byte-identical to `20260702-164724`, which you scored 9/9 PASS; `20260621-162941` is
the identical 6-item prefix. Verified by diffing the response bodies with the verdict
lines stripped. At temperature 0 this is expected determinism rather than a cache bug, so
nothing is broken, but a reader counting run files as data points will overcount by 3x.
I put a NOTE line at the top of both replay files saying so, because the misreading
happens at the file, not in this report.

**3. nvfp4 reaches the right answer on the invariant item through visible flailing.** It
lands on the same lazy-read design you passed in the bf16 run, and preserves the hot
path's 2 yq reads explicitly, so the axis passes. But it gets there across roughly 170
lines with eight "but wait" and "actually" reversals, restates the same code block three
times, and concedes that its own approach "fails" if `q` must read the model for every
intent. The same leak shows on `tool-decision`, where it answers correctly at both the
opening and closing line with five self-reversals in between.

This is the observation most relevant to routing. It is not a correctness failure and I
did not score it as one. It is a statement about what the output costs to consume: you
cannot apply that as a diff without a human or a judge in front of it. It argues *for*
the E1 rule's third clause (the orchestrator applies and judges) rather than against the
tier, and it argues against ever loosening the seat toward autonomy.

## Where the auto-flag and I disagree

One item, `tool-decision` on nvfp4, auto-flagged `REVIEW` because both marker sets fired.
The fail-markers matched because the model *named* `read_file` and `run_tests` while
explicitly declining to call them. The criterion asks whether it says no tool is needed
and does the rename; it does both, opening with "No tools are needed" and closing with
"No tools are called", with a correct rename. Marker matching cannot tell naming a tool
apart from calling one.

## UNSURE

Two items, both on nvfp4, both scored pass on the written criterion where my hesitation
is about something the criterion does not test.

- **`tool-decision`**: correct at both ends, incoherent in the middle. Passes as written.
  Whether a delegated worker that thinks out loud like this is acceptable is your call,
  not the item's.
- **`invariant-aware-edit`**: same shape, larger. It satisfies "reads it only when
  relevant" and addresses the invariant explicitly, which is the standard you applied to
  the bf16 answer, so consistency says pass. A stricter reading, that it never actually
  wires the field up and admits the design may not hold, would fail it. I followed your
  calibration rather than my own stricter instinct, and flag it here so you can flip it.

Nothing else was close. The remaining 22 live verdicts are clean reads of the criteria.

## What the evidence supports

Consistent with the E1 experiment's own scoping, and unchanged by this pass:

- **Cleared**: scoped worker, named files, mechanical judge written before dispatch,
  orchestrator applies and judges. The nine axes are all green on both live observations.
- **Not evidenced**: the autonomous tier. Nothing here tests decomposition, repo
  navigation, or fixture authorship, all of which the cloud orchestrator supplied.
- **Unchanged**: the 80B candidate is still not on disk, and per the complements-only
  ruling this whole lane is parked evidence-gathering rather than a default route.

Two clean observations on a nine-item synthetic battery is a weak base for a 50 GB pull.
If you want D11 satisfied, it needs the five real-task dispatches, not more probe runs.
