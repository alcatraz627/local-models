# local-models

A local LLM subsystem for this machine (MacBook Pro M5 Pro, macOS / Apple Silicon),
running alongside cloud Claude. Goal: quick local work with **zero idle penalty** —
nothing heavy resident unless you ask for it.

## Components

- **Server** — self-hosted `ollama serve` via LaunchAgent `com.alcatraz.local-models-ollama`
  (`bin/lm-serve`). Resource policy baked in: `MAX_LOADED_MODELS=2`, `keep_alive=0` default,
  flash-attention + q8 KV cache. Owns `127.0.0.1:11434`. (The GUI Ollama.app is not used —
  it ignored env vars.)
- **`bin/warm`** — Tier W toggle. `warm on` keeps a small model resident for snappy use
  (~5.6 GB); `warm off` returns to ~0. You pay the warm cost only when you want it.
- **`bin/q`** — the quick companion (below).
- **`bin/imagine`** — local image generation (mflux/Flux on the GPU); see below.

## `q` — the quick companion

```
q "how do I check disk usage"      # terse answer (≤2 sentences)
q cmd "kill everything on 3001"    # ONE macOS command, no essay
q title "<text>"                   # 2-5 word title (tab titles, fire-and-forget)
q --think "harder question"        # allow the reasoning trace (off by default)
q -m qwen2.5-coder:3b cmd "..."    # swap the model per call
q on | off | status                # warm toggle (same as bin/warm)
```

**Smart defaults** (baked in, so you don't retype them): macOS/Apple-Silicon is assumed —
it only switches to Linux if you explicitly say "linux server/container"; the reasoning
trace is off; it never asks clarifying questions — it assumes the most likely intent.

Add `~/Code/local-models/bin` to your `PATH` to drop the path prefix.

## Models

| Model | Role |
|---|---|
| `gemma4-e4b-warm` | Tier W quick companion (num_ctx 8192, QAT 4-bit) |
| `gemma4:26b` / `:31b` | heavier reasoning, on-demand |
| `qwen2.5-coder:3b` | alternate for `cmd` via `-m` |

## `imagine` — local image generation

Runs 100% on your GPU (HuggingFace is only the one-time weight download). Observable: prints what
it will do, shows live step progress, reports path/size/time, auto-opens, and logs every run.

```bash
imagine "a neon city at night, rain"      # default model, model-aware steps, auto-opens
imagine --enhance "tired dev at 3am"      # gemma4 expands your idea into a rich prompt
imagine --from photo.png "make it 3d"     # img2img from an input image
imagine --style photo "a corgi"           # style preset (photo|cinematic|anime|watercolor|3d|cyberpunk)
imagine -m qwen "a sign that reads OPEN"  # swap model (qwen = legible text)
imagine history    ·    imagine show N     # browse past generations (seeds, sizes, prompts)
```

**Models** — registry lives in `bin/imagine` (`resolve_model`); add one = add a case line. Set the
default with `IMAGINE_MODEL` in `config.sh`, override per-call with `-m`:

| Name | Strength | Cost |
|---|---|---|
| `schnell` (default) | fast, great light | weak text/coherence |
| `flux2` | newer, better coherence | mid download |
| `qwen` | **legible text**, strongest overall | bigger download, ~1–2 min |
| `dev` | high quality | gated, slow, non-commercial |

First use of a model downloads its weights. **gemma4 can't generate images** (wrong architecture) —
but `--enhance` uses it as the prompt engineer, and gemma4-vision can critique results (future loop).

## Docs

- `docs/00-plan.md` — full plan + build log + V1 line.
- `docs/TODO.md` — checklist (live status lives in the Task tool).
- `docs/research/` — runtime / vision / image-gen research.
