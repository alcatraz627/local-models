---
reader: agent
---

# Imagine Kit: agent reference

Shell interface for generating and editing images. Run from this folder. `lm studio ...` is an alias for `./imagine ...` where `lm` is installed. Human docs: `README.md`.

## Probe

```bash
./imagine doctor --json
```

| Field | Meaning |
|---|---|
| `can_draw` | At least one model is usable now |
| `default_model` | Model used when none is named |
| `machine.tier` | `full`, `tight` (4-bit load), `none` (no local model fits) |
| `machine.gpu_gb` | NVIDIA VRAM; 0 on Mac or with no card |
| `models[].ready` | Downloaded, or for a cloud model, key present |
| `models[].engine_ok` | Runnable on this machine; `engine_fix` gives the reason if not |
| `models[].cloud` | Set when the request leaves the machine |
| `servers` | Remote machines available via `--on` |

| State | Action |
|---|---|
| `can_draw: true` | Generate |
| local model `engine_ok: true`, `ready: false` | `./imagine download klein` (16 GB, ask first) |
| "not set up yet" | `./install.sh --no-model` |
| every local model `engine_ok: false` | Cloud model or `--on`; never force a download |

## Commands

| Task | Command |
|---|---|
| Text to image | `./imagine gen "PROMPT" --json` |
| Edit a file | `./imagine gen "INSTRUCTION" --from a.png --json` |
| Combine files (max 4) | `./imagine gen "INSTRUCTION" --from a.png --from b.png --json` |
| Edit a past image | `./imagine rework N "INSTRUCTION" --json` |
| Edit a region | `./imagine rework N "INSTRUCTION" --area X,Y,W,H --json` |
| Same request, new seed | `./imagine again N --json` |
| Same seed, prompt extended | `./imagine refine N "ADDITION" --json` |
| Measure a change | `./imagine check N --json` |
| List | `./imagine history [N]`, `./imagine models --json` |

`gen` flags: `--from`, `--model klein|qwen|gemini|gpt`, `--style`, `--size WxH`, `--steps N`, `--seed N`, `--loose [0.1-0.9]`, `--area X,Y,W,H`, `--on MACHINE`. Follow-ups accept `--area`, `--on`, `--json`.

`--area`: left, top, width, height as fractions of the image, 0 to 1. The region plus a 25% margin is cropped, edited alone, blended back. The model sees only the crop. Effects extending past the box are clipped.

## Output record (`--json`)

| Field | Meaning |
|---|---|
| `id` | Image number, used by follow-ups |
| `output` | Absolute PNG path |
| `thread`, `parent` | Lineage |
| `mode` | `new`, `edit`, `start` |
| `model`, `seed`, `steps`, `width`, `height`, `quant` | Settings actually used |
| `region` | The area, if one was given |
| `server`, `cloud_model` | Where it ran, if not local |
| `secs` | Wall time |

## Verify

1. `./imagine check N --json` returns `changed_pct`, and for a region `inside_changed_pct` and `outside_changed_pct`. Deterministic pixel diff against the first source. Region edit: `outside_changed_pct` must be 0. Whole-image edit with a very low `changed_pct`: the instruction was probably ignored.
2. Read `output` as an image and describe it. If you cannot view images, report the measurement only and say the image was not viewed.

A file existing proves only that a render ran.

## Errors

Exit 0 success, 2 usage, 1 other, 130 interrupted. With `--json`, stdout carries `{"ok": false, "code", "message", "fix"}`. Branch on `code`; relay `message` and `fix`.

| `code` | Action |
|---|---|
| `model_missing` | Ask, then `./imagine download klein` |
| `not_installed` | Follow `fix`: `./install.sh` or another model |
| `needs_key` | Report the key page; do not search for keys |
| `bad_key` | Report; do not retry |
| `cloud_failed` | Follow `fix`; a declined prompt needs rewording |
| `render_failed` | Smaller `--size` or fewer sources |
| `source_missing`, `not_an_image` | Fix the path |
| `bad_region`, `region_needs_source` | Fix `--area`; it needs exactly one source |
| `waiting`, `switched_off` | Report; the remote owner must approve. No retry loop |
| `unreachable` | One retry, then report |
| `no_such_image`, `no_such_server` | `./imagine history`, `./imagine servers` |
| `queue_full` | Wait |

## Constraints

- Ask before any download (16 GB model, 5 GB NVIDIA engine).
- Ask before sending a person's images to a cloud model or a remote machine, unless already instructed.
- Never print or echo an API key. Sources: `GEMINI_API_KEY`, `OPENAI_API_KEY`, `data/keys.json`.
- One render at a time per machine. Parallel `gen` calls each load the model.
- Do not edit or delete under `data/`. Set `IMAGINE_KIT_DATA` for scratch work.
- Report measured and viewed separately; state which was not done.

## Files

| Path | Contents |
|---|---|
| `data/history.jsonl` | One record per image, append-only |
| `data/images/NAME.png`, `NAME.metadata.json` | Output and its record |
| `data/sources/` | Source copies, content-addressed |
| `data/trash/` | Deleted images |

## HTTP (running app, loopback only)

`GET /api/state`, `POST /api/generate`, `/api/check`, `/api/stop`, `/api/upload`. Default `http://127.0.0.1:7717/`. Shares `data/` with the CLI. Prefer the CLI.

## Untested

Windows, 16 GB Mac, NVIDIA 20 GB+, model download on Linux, GPT image against the live API, remote render between two machines.
