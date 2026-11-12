---
reader: the owner, or an agent asked "is there a better local model now?"
---

# Model refresh guide: the cheap check

This is the 30 to 45 minute version of a model survey. It answers one question: has anything come out since the last check that could beat what a tier runs today, on this Mac? It does not redo the research. A full survey (September 2026) cost a day; this costs a few searches and, at most, one probe.

Run it when a month has passed, when a release you have heard of looks relevant, or before building on a tier you have not touched in a while.

## Step 1: read what is running (2 minutes)

```bash
lm models                                  # tiers and what is on disk
du -sh ~/.ollama/models ~/.cache/huggingface   # the disk budget, CLAUDE.md hard rule 3
```

Then read the last row of the log at the bottom of this file. It lists the candidates that were seen and not probed, so you do not rediscover them.

## Step 2: search once per seat (10 minutes)

One search per row. Put the month and year in the query, and ask for releases since the date of the last log row. Most hits are aggregator blogs that disagree with each other, so treat every number as a lead and nothing more.

| Seat | Runs today | A challenger has to | Search for |
|---|---|---|---|
| small (warm companion) | `gemma4-e4b-warm`, 6 GB | match it at 8 GB or less, with schema-constrained output working | new open-weight models under 10B |
| big (prose, long context) | `gemma4:26b`, 17 GB | beat it at 20 GB or less | new open-weight models, 20 to 35B |
| code | `qwen3.6:35b-a3b`, 23 GB | pass the 9-item probe and stay fast. Sparse (MoE) models win here because this Mac is limited by memory bandwidth | Qwen, DeepSeek, Mistral coder releases |
| vision | Qwen3-VL-8B 4-bit on MLX, 6 GB | beat 101 of 112 on the vision harness | new VLM releases with an MLX conversion |
| sweep | `granite4:tiny-h`, 4 GB | be faster at the same textcmp score | models under 3B |
| speech | see `docs/11-speech-lane.md` | beat the default on the clip set | Open ASR Leaderboard, mlx-audio release notes |
| image | Qwen-Image through mflux | nothing: this lane is frozen | skip |

Places that answer most of it in one look: the Ollama library sorted by newest, the `mlx-community` organisation on Hugging Face sorted by recently updated, and the Hugging Face Open ASR Leaderboard.

## Step 3: drop what cannot run here (5 minutes)

Cross a candidate off, and write down why, when any of these is true:

- Its 4-bit build is over about 30 GB. It will not share 64 GB with the desktop.
- It has no Ollama tag and no MLX conversion. Converting it yourself is survey work, not a cheap check.
- It only has cloud tags on Ollama.
- Its licence forbids the use you have in mind.
- An earlier round already rejected it. Search `.claude/output/` and `docs/model-notes.md` for its name first.

What survives is usually zero or one model. Zero is a normal result: write the log row and stop.

## Step 4: probe at most one survivor (20 minutes)

Check the disk band before pulling. Then run the gate for its seat, and compare against the incumbent's saved result instead of re-running the incumbent.

```bash
ollama pull <model>
lm probe <model>                                      # code seat: 9-item judgment gate
python3 probe/textcmp/run.py <model>                  # any text seat: 14 exact-answer questions
.venv/bin/python probe/vision/run.py --model <model>  # vision seat: 42 cases, 3 seeds
python3 probe/vision/dominance.py <incumbent> <model> # which cases it wins and loses
```

Read the failing answers before counting them. Twice a scorer has failed a correct answer on format alone.

The swap rule is the owner's: a challenger replaces an incumbent when it is at least as good on every case and better on some. A model that wins three cases and loses three is not an upgrade. Swapping a default is the owner's call, so bring the dominance output, not a recommendation alone.

## Step 5: prune and log (3 minutes)

Delete the loser the same day (`ollama rm <model>`, or `hf cache delete` for an MLX repo). Add a row below. If you probed, add a row to `docs/model-notes.md` as well.

## Log

Newest first. "Seen, not probed" is the list the next check starts from.

| Date | New and runnable here | Too big or not local | Seen, not probed | Probed | Outcome |
|---|---|---|---|---|---|
| 2026-11-12 | LightOnOCR-3 (Oct 8, 0.8B and 4B, MLX conversion exists). An OCR specialist; `see --ocr` already reads exact text through Apple Vision, so it would only matter for scanned documents. | Kimi K3.1 Pro (2.8T), LongCat-2.5 (1.6T, about 48B active), Ripple-65B Preview. Kimi K3, GLM-5.3, MiniMax-M3 and DeepSeek-V4.1-Flash are cloud-only tags on Ollama. | `qwen3.8:27b` for the big seat (18 GB, dense, about 43 tok/s against 143 for the code tier). Recommended as a big-seat probe on 2026-10-21 and never run. `gemma4:12b` as a smaller big seat (Google claims it matches the 26B). A Qwen3.8-35B-A3B was spotted in a ModelScope commit and has not shipped; it is the release most likely to move the code seat. No Gemma 5, no new Mistral. | none | No default changed. Speech got its own lane this day. |
