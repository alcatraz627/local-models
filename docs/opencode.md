---
reader: the owner, or anyone setting up opencode against this suite's local models
---

# opencode on the local models

opencode is a terminal coding agent. This page explains how to run it on the models in this suite, which model to pick, and what to do when it fails.

## Start it

```bash
lm opencode                                  # the code model, interactive
lm opencode -m big                           # another tier: small, big, code, sweep
lm opencode run --auto "fix the failing test" # one task, no screen
lm opencode -m google/gemini-3.8-flash       # a cloud model; nothing local is loaded
```

Use `lm opencode`, not bare `opencode`. The launcher does three things a bare run does not:

1. It starts the model server. The server stops itself when idle, so a bare `opencode` usually finds nothing listening and fails with `ECONNREFUSED`.
2. It holds the model you chose for the session (four hours at most, set by `LM_OPENCODE_LEASE`). Without that the model unloads after every turn and reloads on the next one.
3. It asks zrecover for memory room. zrecover stops a model server that grows past 20 GB, and the big and code models are larger than that once loaded. The launcher takes a grant for those models for the session and gives it back on exit.

Everything after `lm opencode` is passed to opencode unchanged, apart from `-m`, where a tier word is turned into the model's name.

## Which model

Each model was given the same task through opencode: read a file, write a second file with the lines reversed.

| `-m` | Model | Loaded size | Result | Use it for |
|---|---|---|---|---|
| `code` (default) | `qwen3.6:35b-a3b` | 28 GB | passed, 41 s | real coding work, multi-step tasks |
| `big` | `gemma4:26b` | 21 GB or more | passed, 25 s | explaining code, writing prose and docs |
| `small` | `gemma4:e4b-it-qat` | under the 20 GB limit | passed, 20 s | quick single-file edits and questions |
| `sweep` | `granite4:tiny-h` | 8 GB | passed, 9 s | simple mechanical edits |
| | `qwen2.5-coder:3b` | 3 GB | failed | nothing here: it prints tool calls as text and never edits a file |

The code model's size is zrecover's reading at full load. The big model's is the 21.4 GB at which zrecover once stopped it, and it grows with use, so the real peak is not known. The small model's was not measured.

One short task is a floor, not a ranking. It shows that a model can call tools through opencode. It does not show how a model holds up over a long session.

`small` means `gemma4:e4b-it-qat`, not the `gemma4-e4b-warm` model that `q` uses. The warm one is built with an 8k context, which is smaller than opencode's own instructions.

## Images, speech and large documents

The chat models cannot read a recording or a very large file, and they read images less well than the vision model. opencode reaches those through `lm`, in its shell. The file `share/opencode/lm-tools.md` tells the agent which command does what, and the opencode config loads it into every session.

Tested: an agent on the code model was asked for the text in an image. It ran `lm read` on the file and wrote the right text.

`lm imagine` is left out on purpose. It needs about 44 GB, and a session already holds its own model.

## Setup on a new Mac

1. Install opencode: `brew install opencode`.
2. Put this in `~/.config/opencode/opencode.jsonc`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Ollama (local)",
      "options": { "baseURL": "http://127.0.0.1:11434/v1", "apiKey": "ollama" },
      "models": {
        "qwen3.6:35b-a3b":   { "name": "Qwen3.6 35B-A3B (code tier)", "limit": { "context": 262144, "output": 32768 } },
        "gemma4:26b":        { "name": "Gemma4 26B (big tier)",       "limit": { "context": 262144, "output": 16384 } },
        "gemma4:e4b-it-qat": { "name": "Gemma4 E4B (small tier)",     "limit": { "context": 131072, "output": 8192 } },
        "granite4:tiny-h":   { "name": "Granite4 Tiny (sweep tier)",  "limit": { "context": 262144, "output": 8192 } }
      }
    }
  },
  "instructions": ["~/Code/local-models/share/opencode/lm-tools.md"],
  "model": "ollama/qwen3.6:35b-a3b"
}
```

3. Check it: `opencode models` lists four `ollama/` names, and `lm opencode run --auto "say ok"` answers.

The key is a placeholder. The local server needs none, and the client library refuses an empty one.

opencode also lists every other model Ollama has installed. Those work if you name them in full (`-m ollama/<name>`), with no display name or size limit set.

## When it fails

| What you see | Cause | Fix |
|---|---|---|
| `ECONNREFUSED` | The server is not running. | Start through `lm opencode`. |
| The model answers once, then every turn takes 30 s | Nothing is holding the model. | Start through `lm opencode`, or run `warm on code 4h` first. |
| Long silence, then a connection error, on `big` or `code` | zrecover stopped the load. `zrecover log 10 --kind kill` shows it. | Start through `lm opencode`. For a bare run: `warm on code 4h`, which takes the grant too. |
| You switched model inside opencode and it is slow | Only the model named at launch is held. | Quit and start again with `-m`. A switch to `big` or `code` still has its memory grant, so it is slow but not killed. |
| The model prints JSON instead of editing | That model cannot call tools. | Pick one from the table above. |

## Memory

A granted model can still be shed. The grant lifts the size limit for that one model only. If the Mac itself runs short of memory, zrecover acts as it always does, so a session cannot freeze the machine.

The server gives every model a 262k context, and the memory for it is reserved at load. The code model takes 28.0 GB that way and 23.4 GB with a 64k context. Lowering the server default would save that on every load, at the cost of cutting off any request longer than the new limit. It is not changed today.

## Where the pieces are

| Piece | Path |
|---|---|
| The launcher | `bin/lm`, under `opencode)` |
| The memory grant | `lib/mem-room` |
| The agent's tool list | `share/opencode/lm-tools.md` |
| Session records | `logs/opencode-history.jsonl` |
| opencode's config | `~/.config/opencode/opencode.jsonc` |

Reviewed 2026-11-20.
