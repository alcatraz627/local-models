# Output-asset management & history integration for back-and-forth work

<!-- sessions: lm-research@2026-06-12 -->

Research for `~/Code/local-models` (`q`, `imagine`): how mature tools manage generated
assets and multi-turn state, and what's worth stealing at bash-first hobby scale.
Grounded against `bin/imagine`, `bin/q`, `docs/STATE.md` as of 2026-06-12.

**Current ground truth (what exists):**

- `imagine` logs `{ts, prompt, model, steps, seed, output, bytes, ms}` per line to
  `outputs/imagine-history.jsonl`; PNGs self-document via mflux `--metadata`
  (reproducible with `--config-from-metadata`). `history`/`show N` address entries by
  stable JSONL line number. `--from IMG --strength X` img2img already works.
  `critique IMG ["goal"]` works (gemma4:26b vision).
- `q` logs `{ts, intent, model, think, prompt, response, ms}` to
  `logs/q-history.jsonl`. Every call is stateless — one system + one user message.
  Warm model is `gemma4-e4b-warm` with `num_ctx 8192`.
- Gaps the JSONL has today: imagine entries do **not** record guidance, quant, W/H,
  style, neg, `--from` source, or the raw idea behind `--enhance`; neither log has
  any lineage/conversation linkage.

---

## 1. Image-gen asset management — prior art

### InvokeAI — boards, starring, embedded metadata

- Gallery is divided into **Boards** (user-created + always-present "Uncategorized");
  images land on the board selected at generation time. **Starring** pins an image to
  the top of the gallery. **Virtual boards** are computed read-only groupings (e.g.
  by-date) derived from metadata, not stored.
  - https://invoke.ai/features/gallery/
  - https://support.invoke.ai/support/solutions/articles/151000170653-creating-and-managing-boards
- Every image stores generation metadata (prompt, seed, models) **inside the file**;
  an Info button reads it back. Same philosophy as mflux `--metadata` — already done.

### ComfyUI — workflow-in-PNG, filename prefixes

- The whole workflow JSON is embedded in the PNG; dragging a PNG onto the canvas
  reloads the exact graph. The "asset IS the project file" idea.
  - https://civitai.com/articles/26592/the-workflow-in-a-png-trick-in-comfyui
- `filename_prefix` on the Save node, with extensions supporting dynamic tokens like
  `%date:yyMMdd-hhmmss%` — meaningful prefixes as the primary organization scheme.
  - https://github.com/nkchocoai/ComfyUI-SaveImageWithMetaData

### A1111 — PNG info tab, styles.csv, filename patterns

- Parameters written into the PNG; a **PNG Info tab** parses any dropped image and
  offers "send to txt2img/img2img" — the read-back half of the loop.
- **styles.csv** = named prompt presets `(name, prompt, negative_prompt)` injected at
  generation time. `imagine --style` is the same idea hardcoded in a `case`; a
  styles file would make it user-editable without touching the script.
  - https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Custom-Images-Filename-Name-and-Subdirectory
- Filename pattern defaults: `[number]-[seed]` or `[number]-[seed]-[prompt_spaces]` —
  seed in the filename makes reproduction discoverable from `ls` alone.

### Fooocus — per-day folders + per-folder HTML log

- Outputs go to **one folder per day**, each containing `log.html` — an
  auto-appended HTML log of every image with its parameters. The closest existing
  thing to "a gallery with zero resident service": the gallery is just a file the
  generator appends to.
  - https://github.com/lllyasviel/Fooocus/discussions/3092
  - https://github.com/lllyasviel/Fooocus/discussions/2410 (v2.2.0 metadata: embeds
    full params, can re-apply settings directly from an image)

### Draw Things — version history + branching, per-project DBs

- **Version History** panel: every generation is an undoable state; you can return to
  a previous state and **branch** into a different edit. Per-project database storing
  history + prompts + images; thumbnail scroll sidebar.
  - https://wiki.drawthings.ai/wiki/User_Interface
- The takeaway is the **lineage/branching model**, not the database: each generation
  knows its parent.

### What's worth stealing at CLI/hobby scale

| Steal | From | Hobby-scale shape |
|---|---|---|
| Starring + "unstarred is prunable" | InvokeAI | `imagine star N` / `imagine prune` |
| Parent lineage / branch-from | Draw Things | `parent` field in JSONL |
| Append-only HTML log as gallery | Fooocus | `imagine gallery` regenerates one `index.html` from the JSONL |
| Seed in filename | A1111 | `img-<epoch>-s<seed>.png` |
| Editable styles file | A1111 styles.csv | `styles.tsv` read by `style_suffix` with case-fallback |
| Boards | InvokeAI | **Skip** — `-o outputs/<project>/...` + a `--project` dir flag is enough; real boards are DB-shaped over-engineering here |

---

## 2. Iteration / refinement UX

### Prior art

- **Midjourney** factored iteration into exactly four verbs, which is the cleanest
  taxonomy in the space: **Reroll** (same prompt, new seed), **Vary Subtle / Vary
  Strong** (img2img at low/high strength from a result), **Upscale**, plus **Remix**
  (vary + edit the prompt while doing it).
  - https://docs.midjourney.com/hc/en-us/articles/32692978437005-Variations
  - https://docs.midjourney.com/hc/en-us/articles/33329329805581-Modifying-Your-Creations
- **SD-world "vary"** is implemented as img2img with denoise ~0.3 (subtle) / ~0.7
  (strong) on the previous output — i.e. your existing `--from OUT --strength X`.
  - https://civitai.com/articles/1688/basic-things-you-might-not-know-do-you-know-sd-has-vary-function-just-like-midjourney
- **Seed-locked prompt delta** (same seed + edited prompt) is the other axis: keeps
  composition, changes attributes. Cheap and already fully supported by recorded
  seeds — it's purely a UX gap.

### Proposed CLI (fits existing `imagine <verb>` conventions)

All verbs resolve N via the JSONL exactly like `imagine show N`; `N` omitted = last
entry. Every flag after the verb passes through to normal generation (so `-s`, `-m`,
`--style` all still work as overrides).

```
imagine redo N [overrides]            # exact re-run: same prompt+seed+model+steps,
                                      #   apply overrides (e.g. -s 8, -m flux2)
imagine vary N [--n 4] [--strong]     # same prompt, NEW random seed(s);
                                      #   --strong = also img2img from N at 0.7
imagine refine N "make it warmer"     # seed-locked: same seed/model/steps,
                                      #   prompt = recorded prompt + ", make it warmer"
imagine remix N "full new prompt"     # img2img: --from <output of N> --strength 0.5,
                                      #   new prompt (Midjourney Remix)
```

Implementation is small: a `load_entry N` helper (`sed -n Np | jq`) populating
`MODEL/STEPS/SEED/PROMPT/OUT_SRC` before the existing arg loop, ~30 lines total.
Two prerequisites:

1. **Log everything you'd need to re-run** — extend the Python log block to include
   `guidance, quant, width, height, style, neg, from, strength, raw_idea, kind,
   parent`. Old lines stay valid (jq `// empty` handles missing keys).
2. **`parent`** = the JSONL line number (or output path) of N for `vary/refine/remix`,
   `kind` ∈ `gen|redo|vary|refine|remix`. This gives Draw-Things-style lineage for
   free; `imagine show N` can then print "derived from #parent".

A `imagine tree [N]` that walks `parent` links is a nice-to-have, not v1.

---

## 3. Conversation continuation for `q`

### Prior art

- **simonw/llm**: `-c/--continue` (most recent) and `--cid ID` (specific). SQLite
  (`responses` rows keyed by `conversation_id`); continuation **re-sends all prior
  prompt/response pairs** as messages; the same model is reused automatically; no
  automatic truncation — docs just warn about token growth.
  - https://llm.datasette.io/en/stable/usage.html
  - https://deepwiki.com/simonw/llm/6.1-logging-configuration
- **charmbracelet/mods**: conversations saved by default with a **SHA-1 + title**
  (deliberately git-like); `-c/--continue <id-or-title>`, `--show <id-or-title>`,
  `--title` enables **branching** (`mods --continue=naturals --title=naturals.json`).
  - https://github.com/charmbracelet/mods
- **sigoden/aichat**: named sessions in YAML files; auto-**compress** (summarize)
  when history exceeds `compress_threshold` (default 4000 tokens), plus a manual
  `.compress` command — the only tool of the set with a built-in context-budget
  answer.
  - https://github.com/sigoden/aichat/wiki/Configuration-Guide
- **gptme**: full agent persistence (git-tracked workspace) — instructive but the
  wrong weight class for `q`. https://gptme.org/

### Minimal mechanism for `q` (no SQLite, the JSONL is already the store)

The llm model maps 1:1 onto what exists: a JSONL line **is** an exchange; the only
missing piece is a conversation id linking lines.

1. **Add `cid` to each logged entry.** Fresh call → `cid = ts` of that entry.
   Continued call → copy the `cid` of the entry being continued. Old lines without
   `cid` are treated as singletons.
2. **`q -c "follow-up"`** — continue the **last** entry's conversation.
   **`q -c N "follow-up"`** — continue from entry N (numbers already meaningful via
   `q history`). Reconstruction: select all lines with that `cid` (in order), build
   `messages = [system] + Σ[{user: prompt},{assistant: response}] + [{user: new}]`.
   One `jq -c 'select(.cid==$c)'` pass — no new storage, no daemon, llm-style
   full-replay semantics.
3. **Model/intent stickiness** (llm steals this): `-c` reuses the model and intent
   recorded on the continued entry unless overridden with `-m`/an intent word.
4. **Context budget at num_ctx 8192**: budget ≈ chars/4. Reserve ~700 tokens for
   system + new prompt + answer headroom → cap history at ~6,000 tokens
   (~24,000 chars). Walk exchanges **newest-first**, accumulate until the cap,
   drop the oldest whole exchanges (never split a pair), print a dim
   `(context: kept last K of M exchanges)` notice. Skip aichat-style LLM
   summarization/compression — it's a quality gamble on a 4B model and adds a
   hidden extra call; plain truncation is honest and predictable at `q`'s scale
   (≤2-sentence answers mean histories stay tiny anyway).
5. `q show N` gains one line: `cid` + count of sibling exchanges. Optional later:
   `q history --cid <id>` filter.

Deliberately **not** stealing: SQLite (JSONL+jq is sufficient and greppable),
titles/branching (mods' branching is elegant but `q` conversations are ephemeral —
revisit only if real use shows long-lived threads), aichat sessions-as-named-files.

---

## 4. Cross-tool flows

### critique → refine loop (all-local art direction)

The pieces exist: `critique` produces a "FIXES" section; `refine` (above) re-runs.
The join:

```
imagine refine N --from-critique          # run critique(output N, recorded prompt),
                                          #   feed FIXES + original prompt through
                                          #   enhance_prompt(), generate as refine
imagine critique N                        # accept history numbers, not just paths
                                          #   (resolve via JSONL; record critique in
                                          #   the entry? no — keep critiques stdout-only)
```

Keep it one hop, human-in-the-loop by default (print the critique-derived prompt
before generating, same as `--enhance` prints `idea`/`enhanced`). A fully automatic
multi-round loop (`--rounds 3`) is tempting and is the over-engineering line — skip
until manual `refine --from-critique` proves itself.

### One timeline across q + imagine

Worth a thin read-only merge, not a shared store:

```
lm timeline [N]      # merge tail of logs/q-history.jsonl + outputs/imagine-history.jsonl
                     #   by ts, prefix each line with tool glyph: [q]/[img]
```

~10 lines of `jq -s 'sort_by(.ts)'` over both files with a `tool` tag injected at
read time. Don't unify the schemas or move the files — the per-tool logs are each
tool's source of truth; the timeline is a view.

### Claude Code reading the histories

The JSONLs are already ideal agent food (greppable, line-addressable, stable
numbering shared with `show N`). Three cheap enablers:

1. **Document the contract** in `docs/STATE.md` (one paragraph: file paths, schema
   fields, "line number == `show N` number"). An agent doing art direction can then
   `tail outputs/imagine-history.jsonl | jq` and issue `imagine refine 12 ...`
   commands — no API needed; the CLI *is* the integration surface.
2. `imagine history --json [N]` / `q history --json [N]` — raw tail without the
   human formatting, so agents don't parse the pretty output. (Trivial: `tail -n N
   "$LOG"`.)
3. Per the existing project pattern, a short note in the project `CLAUDE.md`/skills:
   "to continue art direction, read `imagine history`, inspect `show N`, iterate with
   `refine/vary/remix`." This matches the planned llm-mini→Claude fold direction in
   STATE.md without building any of it.

---

## 5. Lightweight gallery / browse (no resident service)

### Findings

- **`qlmanage -p outputs/*.png`** — zero-install Quick Look from terminal; arrow-key
  through the whole set. Best instant answer on macOS.
  https://osxdaily.com/2007/12/24/use-quick-look-from-the-command-line/
- `qlmanage -t -s 256 -o <dir> <files>` generates thumbnails if a thumbnail pass is
  ever wanted. https://alexwlchan.net/2020/using-qlmanage-to-create-thumbnails-on-macos/
- Static gallery generators: **thumbsup** (npm, heavy), **gallery_shell** (pure bash
  + ImageMagick + jhead, generates `index.html` + thumbs dir — proof the whole job
  is a ~300-line bash script), **simple-photo-gallery** (Python).
  - https://thumbsup.github.io/ · https://github.com/Cyclenerd/gallery_shell
  - https://pypi.org/project/simple-photo-gallery/
- None of them know about the JSONL — a generic generator shows pixels but loses
  prompt/seed/lineage. Since the metadata is the point, a tiny **bespoke generator
  driven by the JSONL** beats adopting any of these.

### Recommendation

```
imagine gallery [--open]    # regenerate outputs/index.html from imagine-history.jsonl
                            #   newest-first grid; each card: <img> (the PNG itself,
                            #   no thumbnails at hobby scale), prompt, model/steps/seed,
                            #   #N, ★ if starred, parent link; client-side text filter
```

One self-contained HTML file (inline CSS/JS, `file://`-openable, **dark default +
dark/light toggle per `conventions/html-output.md`**). Regenerated on demand —
Fooocus's append-log idea with the regeneration simplicity of a 60-line Python
block like the existing logger. No thumbnails until the folder is big enough that
load time hurts (hundreds of multi-MB PNGs → then add a `qlmanage -t` pass).

Interim/zero-build: alias-level `imagine browse` → `qlmanage -p "$DIR"/outputs/*.png`.

---

## Ranked recommendations (value ÷ effort, honest to hobby scale)

| # | Item | Effort | Why this rank |
|---|---|---|---|
| 1 | **Log the full config** (guidance/quant/W/H/style/neg/from/strength/raw_idea/kind/parent) in imagine's JSONL | ~15 lines | Prerequisite for everything below; costs nothing; fixes today's "can't re-run from history" gap |
| 2 | **`q -c` / `q -c N`** with `cid` field + newest-first truncation at ~6k tokens | ~40 lines (extend the Python block + jq select) | Removes the single biggest `q` limitation; llm-proven mechanism; zero new storage |
| 3 | **`imagine redo/vary/refine/remix N`** | ~30 lines + `load_entry` helper | The actual back-and-forth UX; Midjourney's verb set on top of recorded seeds + existing `--from` |
| 4 | **`imagine star N` + `imagine prune`** | ~20 lines (`outputs/starred.txt` of paths; prune = `trash` unstarred older than N days, dry-run first) | InvokeAI's keep/discard model; outputs/ will otherwise grow unbounded |
| 5 | **`imagine gallery`** (JSONL-driven single-file HTML, dark/light toggle) | ~80 lines | Big browse upgrade, still zero resident cost; do after 1–4 since it renders their fields. Interim: `qlmanage -p outputs/*.png` today |
| 6 | **`--json` history flags + STATE.md contract paragraph** for agent integration | ~10 lines + docs | Makes Claude Code a first-class consumer without building anything |
| 7 | **`refine N --from-critique`** | ~25 lines | Closes the all-local critique→refine loop; one hop, prompt shown before generating |
| 8 | **`lm timeline`** | ~10 lines | Cute unified view; cheap, but lowest pull — build last or on demand |
| — | Boards/projects, SQLite, aichat-style compression, auto multi-round refine loops, thumbnails | — | **Skip** — DB-shaped or daemon-shaped solutions to problems the flat files don't have yet |

### Naming note

Consider adding seed to new filenames (`img-<epoch>-s<seed>.png`, A1111-style) so
`ls` alone reveals reproducibility — but only for new files; never rename existing
ones (the JSONL `output` paths are load-bearing).

---

## Source index

- InvokeAI gallery/boards/starring: https://invoke.ai/features/gallery/ · https://support.invoke.ai/support/solutions/articles/151000170653-creating-and-managing-boards
- ComfyUI workflow-in-PNG / filename prefix: https://civitai.com/articles/26592/the-workflow-in-a-png-trick-in-comfyui · https://github.com/nkchocoai/ComfyUI-SaveImageWithMetaData
- A1111 filenames/PNG-info/styles.csv: https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Custom-Images-Filename-Name-and-Subdirectory
- Fooocus per-day folders + log.html + metadata: https://github.com/lllyasviel/Fooocus/discussions/3092 · https://github.com/lllyasviel/Fooocus/discussions/2410
- Draw Things version history/branching: https://wiki.drawthings.ai/wiki/User_Interface
- Midjourney variation verbs: https://docs.midjourney.com/hc/en-us/articles/32692978437005-Variations · https://docs.midjourney.com/hc/en-us/articles/33329329805581-Modifying-Your-Creations
- SD vary-as-img2img: https://civitai.com/articles/1688/basic-things-you-might-not-know-do-you-know-sd-has-vary-function-just-like-midjourney
- simonw/llm continuation: https://llm.datasette.io/en/stable/usage.html · https://deepwiki.com/simonw/llm/6.1-logging-configuration
- charmbracelet/mods (SHA-1+title, branching): https://github.com/charmbracelet/mods
- aichat sessions + compress_threshold: https://github.com/sigoden/aichat/wiki/Configuration-Guide
- gptme persistent agent: https://gptme.org/
- qlmanage: https://osxdaily.com/2007/12/24/use-quick-look-from-the-command-line/ · https://alexwlchan.net/2020/using-qlmanage-to-create-thumbnails-on-macos/
- Static galleries: https://thumbsup.github.io/ · https://github.com/Cyclenerd/gallery_shell · https://pypi.org/project/simple-photo-gallery/
