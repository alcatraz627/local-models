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

History is in `docs/LEDGER.md`. The full command menu is in `docs/CAPABILITIES.md`.

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
- **Memory.** zrecover stops any process that grows too large. `lm imagine` and `lm hear` ask it for a grant for one run.
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

`config.sh` is the one place these are set.

## Disk

122 GB of models on disk. The target is under 150 GB and the hard stop is 200 GB. The rule is in `CLAUDE.md`.

## Open work

| Item | Next step |
|---|---|
| Speech on the owner's voice | Record 20 clips and score `lm hear` and `lm hear intent` on them. |
| Speech end state | Goal `9a93c78fcd48`. Requirements and order of work are in `docs/11-speech-lane.md` under "The end state". Steps 1 to 3 are done (past runs, voices, the two screens). The rest waits on the owner's three gates. |
| Long-call digest | One pass is thin. Take notes per ten minutes first. |
| Big seat | `qwen3.8:27b` was recommended for a probe and never run. |
| Model refresh | Follow `docs/model-refresh-guide.md` monthly. |
| Routing policy | Write down when work goes local, to Gemini, or to the cloud. |
| Speculative decoding | One measurement on the MLX path settles a disputed claim. |
| Pi and phone peer | Waiting on the csync agent and a Pi power fault. |
| Codex setup | Two acceptance checks remain. Codex is out of quota. |

The long form of each older item is in `docs/LEDGER.md` under "Open items".

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
| `docs/` | design docs, numbered |
| `logs/`, `outputs/` | run histories and artifacts |

## Sources

| Fact | From |
|---|---|
| Disk figure | `du -sh ~/.ollama/models ~/.cache/huggingface` |
| Seats and models | `config.sh`, `lib/hear.py` |
| Speech results | `docs/11-speech-lane.md` |
| Vision and text comparison | `docs/20261022-model-comparison.md` |
| Smoke suite result | `bash scripts/verify.sh` |
| Cold-by-default ruling | owner |
| Scoped-under-lm ruling | owner |

Reviewed 2026-11-12.
