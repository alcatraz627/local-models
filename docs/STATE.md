---
reader: an agent or the owner picking this project up cold
---

# local-models: state

A toolkit of local language, vision, image and speech models on one Apple Silicon Mac (64 GB). It runs beside cloud agents and covers what they do poorly or should not see.

This file says what is true now. Check it against the live commands before relying on it:

```bash
lm status              # server, loaded models, disk
lm models              # tiers and what is installed
bash scripts/verify.sh # the smoke suite
```

History is in `docs/LEDGER.md`. The full command menu is in `docs/CAPABILITIES.md`. Every other doc is listed in `docs/README.md`.

## What works

| Area | Command | State |
|---|---|---|
| Quick answers | `lm ask`, `q` | in use |
| Shell commands | `lm cmd` | in use, checked against the tool's own help |
| Reading images | `lm read`, `see` | in use |
| Comparing images | `lm diff`, `see diff` | in use |
| Reading documents | `lm doc` | in use |
| Speech | `lm hear`, `lm hear live` | files tested on one real call; live tested with fed audio, not yet a real voice |
| Image generation | `lm imagine` | frozen, works |
| Image kit to share | `imagine-kit/` | a standalone app and command for making and reworking images; tested on this Mac only |
| Sharing models between devices | `lm net` | approved devices can use this machine's vision and image models; tested on this Mac only |
| Coding agent | `lm opencode` | works on the code, big, small and sweep models; guide in `docs/opencode.md` |
| Code review | `lm review` | in use |
| Batch runs | `lm fleet` | in use |
| Large context | `lm gemini` | in use, leaves the Mac |
| Retrieval | `lm rag` | built, optional |

`lm help <name>` explains any of them. `lm examples` shows worked commands.

Only `lm`, `q`, `see`, `warm` and `review` are on PATH. Newer tools are reached through `lm`.

## How it runs

- **Server.** Ollama, started by a LaunchAgent, on `127.0.0.1:11434`.
- **Nothing stays loaded.** A model loads for a request and unloads after it. `warm on` holds one for a set time.
- **Vision and speech run outside Ollama**, on MLX, from the repo's `.venv`.
- **Memory.** zrecover stops any process that grows too large. `lm imagine` and `lm hear` ask it for a grant for one run. Every command that loads the big or code model does the same through `lib/mem-room`, because both are over zrecover's 20 GB limit for a model server.
- **Every run is logged.** The history files under `logs/` and `outputs/` are what other tools read.

| Seat | Model | Size |
|---|---|---|
| small | `gemma4-e4b-warm` | 6 GB |
| big | `gemma4:26b` | 17 GB |
| code | `qwen3.6:35b-a3b` | 23 GB |
| sweep | `granite4:tiny-h` | 4 GB |
| vision | Qwen3-VL-8B, 4-bit | 6 GB |
| vision fallback | `minicpm-v4.6` | 1.6 GB |
| speech, words | Qwen3-ASR 0.6B | 2 GB |
| speech, speakers | VibeVoice-ASR, 4-bit | 5.7 GB |
| image | Qwen-Image | 50 GB |
| image kit | FLUX.2 klein 4B | 16 GB |

`config.sh` is the one place these are set.

## Disk

137 GB of models on disk. The target is under 150 GB and the hard stop is 200 GB. The rule is in `CLAUDE.md`.

## Open work

| Item | Next step |
|---|---|
| Speech on the owner's voice | Record 20 clips and score `lm hear` and `lm hear intent` on them. |
| Speech end state | Goal `9a93c78fcd48`. Requirements and order of work are in `docs/11-speech-lane.md` under "The end state". Steps 1 to 3 are done (past runs, voices, the two screens). The rest waits on the owner's three gates. |
| Long-call digest | One pass is thin. Take notes per ten minutes first. |
| Big seat | `qwen3.8:27b` was recommended for a probe and never run. |
| Model refresh | Follow `docs/model-refresh-guide.md` monthly. |
| Routing policy | Write down when work goes local, to Gemini, or to the cloud. |
| lm and the z- tool standard | Six steps are recommended in `docs/reviews/20261120-lm-and-the-z-tool-standard.md`. Two are in the zcmd repo and wait on the owner. |
| Image kit on a small Mac | `imagine-kit/` has not been run on a 16 GB Mac. Try it on one before sharing widely. |
| Image kit and opencode on Linux and Windows | Neither runs there yet. See "Cross-platform and shared use" below. |
| lm net between two real machines | Not yet tried. See "Cross-platform and shared use" below. |
| Server context size | Every model loads with a 262k context. A 64k default would save the code model 4.6 GB. Not changed, because it would cut off longer requests. |
| Speculative decoding | One measurement on the MLX path settles a disputed claim. |
| Pi and phone peer | Waiting on the csync agent and a Pi power fault. |
| Codex setup | Two acceptance checks remain. Codex is out of quota. |

The long form of each older item is in `docs/LEDGER.md` under "Open items".

### Cross-platform and shared use

The owner wants the image kit and `lm opencode` usable on Linux and Windows, and wants weaker machines to borrow a stronger one. How to set the kit up on each kind of computer is in `imagine-kit/README.md`.

Done so far:

- The kit's image engine sits behind a seam, so a second engine can be added beside the Mac one.
- The kit asks the machine what it can run, with no Mac-only tool.
- `lm net` lets a machine offer its vision and image models to devices its owner approves once. Every request is logged.
- The kit has a "Runs on" choice and can draw on a machine that runs `lm net serve`.

- The kit has a second engine for Linux with an NVIDIA card. `install.sh` sets it up, and a from-scratch install drew an image on a test VM.

What the Linux engine does on a 16 GB graphics card:

| Job | Time | How it is loaded |
|---|---|---|
| New image | about 93 s | 4-bit model |
| Rework of one image | about 150 s | 4-bit model, source shrunk to 768 |
| Combine of two images | about 120 s | 4-bit model, sources shrunk to 512 |

The same jobs take 11, 19 and 30 s on the M5 Pro. At full precision a rework did not fit on that card at any source size.

- The studio page was rebuilt around threads. It has a queue, several tries at once, a library of earlier uploads, and a way to mark an area so a change stays inside it.
- `lm studio` opens the studio, and `lm models` lists the image models.
- Two cloud image models can be chosen, from Google and from OpenAI. Each needs that company's key, and the page says the request is sent there.

What has run for real and what has not:

| Part | Run for real |
|---|---|
| Marked-area change on the M5 Pro | yes, 18 s, and nothing outside the area changed |
| Queue of three requests through the page's own calls | yes |
| Google's image model | yes, a rework in 6 s |
| OpenAI's image model | no, this machine has no key for it |

Still to do:

- The WSL setup for Windows, and a run on a real Windows machine.
- A run of OpenAI's image model with a real key.
- A model's reading of a change, through `lm see`. Today the Check button only measures.
- The kit's own guide, which does not yet describe threads, areas, cloud models or Linux.
- A run on a card with 20 GB or more, where the kit loads the full model. That path is written and has not run.
- The model download on Linux through the kit. The test VM already had the model.

To try `lm net` between two real machines:

1. Start Tailscale on both.
2. Run `lm net serve` on the M5 Pro.
3. Name the M5 Air with `lm net approve NAME`, so it is let in on first contact.

`lm net serve` runs as a background service named `lm-net`, started by `scripts/gcc-lm-net`. Switch it off and on in Switchboard or with `gcc-schedule disable lm-net`. The M5 Air is named ahead of time, so it is let in on first contact. claude-see still runs beside it, unchanged.

One stopped Linux test VM, `lm-linux-probe-2`, has a 16 GB graphics card, the driver, the engine and the model. A first VM with a 24 GB card could not be restarted, because its zone ran out of that card, and was deleted.

## Known failures in the smoke suite

| Check | Cause |
|---|---|
| guard-model-tier block path | A gcc hook outside this repo. |
| `logs/gem-history.jsonl` corrupt | Two parallel `lm gemini` calls wrote one row over another. |

## Lessons that still hold

- For a small local model, the prompt matters more than which model it is.
- Turn thinking off with the API flag. A prompt that says "no thinking" is ignored.
- A re-quantized model needs its gate run again.
- Trust a passing check. Never trust a spec sheet or a model's confidence.
- Hold a big model with a timed lease. A pin gets forgotten.
- A retry needs the evidence and the exact change wanted. Repeating the spec does not converge.
- Write pipelines in bash. zsh `echo` expands `\n` inside JSON.
- Replay the reporter's real workload before closing a bug. A synthetic repro can pass while the real one fails.
- Pick the evidence by surface: the accessibility tree for native apps, `see --ui` for pixels, `see --ocr` for exact text.
- Local vision checks facts well and judges looks badly.
- Speech models need more memory the longer the audio is. Read long audio in windows.

## Where things are

| Path | Holds |
|---|---|
| `bin/` | the commands |
| `lib/` | the machinery behind them |
| `lib/verbs.toml` | the one list every help screen is generated from |
| `intents/` | prompts as data, one file per job |
| `probe/` | checks with known answers |
| `scripts/verify.sh` | the smoke suite |
| `docs/` | every doc, indexed in `docs/README.md` |
| `imagine-kit/` | the standalone image kit, which uses nothing else in this repo |
| `logs/`, `outputs/` | run histories and artifacts |

## Sources

| Fact | From |
|---|---|
| Disk figure | `du -sh ~/.ollama/models ~/.cache/huggingface` |
| Seats and models | `config.sh`, `lib/hear.py` |
| Speech results | `docs/11-speech-lane.md` |
| Vision and text comparison | `docs/reviews/20261022-model-comparison.md` |
| Smoke suite result | `bash scripts/verify.sh` |
| Linux engine times | runs on the test VM on 2026-11-20; its 16 GB card is an NVIDIA T4, and the 24 GB one is an L4 |
| Test VM zone | `lm-linux-probe-2` is in us-central1-a |
| Cold-by-default ruling | owner |
| Scoped-under-lm ruling | owner |

Reviewed 2026-11-20.
