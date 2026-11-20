---
reader: agent
---

# Imagine Kit, for an agent

You are an AI agent that has been asked to make or change an image, or to set this kit up for a person. This file tells you how to drive the kit from a shell: which commands to run, what comes back, and how to check a result before you report it. People read `README.md` instead.

Every command below is run from this folder. On a machine that has the `lm` toolkit, `lm studio ...` is the same as `./imagine ...`.

## First, ask what this computer can do

Do not guess from the operating system. Ask:

```bash
./imagine doctor --json
```

| Field | Meaning |
|---|---|
| `can_draw` | True when at least one model can be used right now. |
| `default_model` | The model a request uses when you name none. |
| `machine.tier` | `full`, `tight` (a lighter copy is loaded), or `none` (no local model fits). |
| `machine.gpu_gb` | NVIDIA card memory on Linux and Windows; 0 on a Mac or with no card. |
| `models[].ready` | Downloaded, or for a cloud model, a key is present. |
| `models[].engine_ok` | This computer can run it at all. `engine_fix` says why when it cannot. |
| `models[].cloud` | Present when the model runs at a company and the request is sent there. |
| `servers` | Other machines this one may draw on. |

Then act on it:

| What you see | What to do |
|---|---|
| `can_draw` is true | Go to "Make an image". |
| A local model has `engine_ok` true and `ready` false | `./imagine download klein` (16 GB; ask the person first). |
| No `.venv` folder, or "not set up yet" | `./install.sh --no-model`, then ask before any download. |
| Every local model has `engine_ok` false | The computer cannot draw by itself. Use a cloud model or a server, with the person's say-so. Do not try to force a download. |

## Make an image

```bash
./imagine gen "a red bicycle leaning on a wet brick wall, early morning" --json
```

With `--json`, standard output is one JSON record and nothing else. The fields you will use:

| Field | Meaning |
|---|---|
| `id` | The image's number. Follow-ups name it. |
| `output` | The absolute path of the PNG. |
| `thread` | Images that grew from one idea share this. |
| `parent` | The image this one came from, or null. |
| `mode` | `new`, `edit` (reworked from sources) or `start` (loosely from one source). |
| `seed`, `steps`, `width`, `height`, `model` | What was actually used. Pass `--seed` to repeat a result. |
| `secs` | How long it took. |

Options for `gen`: `--from IMAGE` (repeat for up to four), `--model NAME`, `--style NAME`, `--size WxH`, `--steps N`, `--seed N`, `--loose [0.1-0.9]`, `--area X,Y,W,H`, `--on MACHINE`.

## Change an image

| Goal | Command |
|---|---|
| Rework a file | `./imagine gen "make the jacket red" --from photo.jpg --json` |
| Combine files | `./imagine gen "put the cup on the desk" --from cup.png --from desk.png --json` |
| Rework a past image | `./imagine rework 12 "warmer light" --json` |
| Same request, new roll | `./imagine again 12 --json` |
| Same start, prompt extended | `./imagine refine 12 "at night" --json` |

Write an edit instruction with three parts: what to change, where, and what must stay the same. One change per instruction. `PROMPTING.md` has the longer guidance.

## Change only part of an image

Use this when one part is wrong and the rest must not move.

```bash
./imagine rework 12 "Replace the front wheel with a sunflower." --area 0.52,0.45,0.42,0.45 --json
```

`--area` is left, top, width and height as shares of the image, each from 0 to 1. The kit cuts out that part with a margin, has the model rework only the cut-out, and blends it back. Pixels outside the cut-out are the original pixels.

Two limits follow from that:

- The model does not see the rest of the image, so describe the change in terms of what is inside the area.
- An effect that should spread past the area, such as a glow or a shadow, stops at its edge. Use a larger area for those.

## Check before you report

A file on disk only proves that something was drawn. Do both of these before you tell a person it worked.

1. **Measure it.** For anything made from a source:

```bash
./imagine check 13 --json
```

It returns `changed_pct`, and for an area also `inside_changed_pct` and `outside_changed_pct`. No model is involved, so these numbers cannot be invented. For an area change, `outside_changed_pct` must be 0. A whole-image rework that reports a very low `changed_pct` probably ignored the instruction.

2. **Look at it.** Open `output` with whatever lets you see an image, and say what is in it. If you cannot see images, say that you did not look, and report only the measurement.

Never describe an image you have not looked at.

## Models that run at a company

`gemini` and `gpt` run at Google and OpenAI. Choosing one sends the prompt and every source image there, and costs the key's owner a few cents an image.

- Ask the person before you send their images to a company, unless they already told you to use that model.
- A key comes from `GEMINI_API_KEY` or `OPENAI_API_KEY`, or from the app's key box. Never print a key, and never write one into a command you show.
- The exact model the company used is in the record's `cloud_model` field.

## Drawing on another machine

`./imagine servers` lists machines this computer may use. Add `--on NAME` to any `gen` or follow-up. The first request to a new machine is refused with the code `waiting` until its owner approves this computer once. Tell the person the command the message names. Do not retry in a loop.

## When a command fails

The exit code is 0 for success, 2 for bad usage, 1 for anything else, and 130 when interrupted. With `--json`, a failure prints `{"ok": false, "code": ..., "message": ..., "fix": ...}` on standard output. Branch on `code`, which is stable. Show the person `message` and `fix`, which are written for them.

| `code` | Meaning | What to do |
|---|---|---|
| `model_missing` | The local model is not downloaded. | Ask, then `./imagine download klein`. |
| `not_installed` | The engine is missing or cannot run here. | Read `fix`. It is `./install.sh` or "use another model". |
| `needs_key` | A cloud model has no key. | Tell the person where to get one. Do not look for keys elsewhere. |
| `bad_key` | The company refused the key. | Tell the person. Do not retry. |
| `cloud_failed` | The company declined or failed. | Read `fix`. A declined prompt needs different words. |
| `render_failed` | The model stopped, often for memory. | A smaller `--size`, or fewer sources. |
| `source_missing`, `not_an_image` | A source path is wrong or unreadable. | Fix the path. |
| `bad_region`, `region_needs_source` | The area is not a box inside one existing image. | Fix `--area`. |
| `waiting`, `switched_off` | Another machine has not let this computer in. | Tell the person. |
| `unreachable` | Another machine or a company did not answer. | Try once more later, then say so. |
| `no_such_image` | That image number does not exist. | `./imagine history`. |

## Where things are

| Path | Holds |
|---|---|
| `data/images/` | Each image, with `NAME.metadata.json` beside it holding the same record. |
| `data/history.jsonl` | One JSON line per image. Read this to find past work. Do not edit it. |
| `data/sources/` | Copies of source images, named by their content. |
| `data/trash/` | Deleted images. The kit never removes a file outright. |

Set `IMAGINE_KIT_DATA` to keep your own work apart from the person's images. Do that for anything exploratory.

## Rules

- Ask before a download. The model is 16 GB and the Linux engine is 5 GB more.
- Ask before sending a person's images to a company or to another machine.
- One render runs at a time. Do not start several `gen` commands at once on one machine. Each loads the model again and they compete for memory.
- Do not delete from `data/`. Tell the person what you made and where.
- Report what you measured and what you saw. Say which of the two you did not do.

## A running app

A person may have the app open (`./imagine`, usually at `http://127.0.0.1:7717/`). The command line and the app share `data/`, so an image you make appears in their app. If you need the app's own calls, they are in `kit.py` under `do_POST`: `/api/generate`, `/api/check`, `/api/stop`, and `GET /api/state`. They accept requests from this computer only. Prefer the command line.

## What has not been tested

Read this before you promise anything on these: any Windows computer, a 16 GB Mac, an NVIDIA card with 20 GB or more, the model download on Linux, GPT image against OpenAI, and drawing between two separate computers. `README.md` lists what was tested and the times measured.
