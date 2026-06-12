# Consolidation research — local-models toolkit

<!-- sessions: lm-research@2026-06-12 -->

Question: which facets of the toolkit (q / imagine / warm / lm / lm-serve, 564 lines total)
can be consolidated better, and how do mature local-LLM CLI tools do it. Grounded in a full
read of `bin/*` + `config.sh` + `docs/STATE.md` + `docs/GOALS.md` (2026-06-12) and online
research of simonw/llm, aichat, mods, ollama, llama.cpp, LM Studio, mlx-lm.

Constraints honored throughout: no daemons, no idle cost, bash-first, helpers only at ≥2
real callsites, user's anti-over-engineering stance.

---

## Facet 1 — History/logging layer

### Current state

Two near-identical JSONL implementations:

- `bin/q:67-88` — `LOG="$DIR/logs/q-history.jsonl"`, `show_history()` (tail+jq+nl with
  stable line numbers), `show_entry()` (sed -n Np + jq pretty-print). Write side: inline
  Python appends one JSON object (`bin/q:177-186`), best-effort (never breaks the answer).
- `bin/imagine:117-135` — same two functions, different jq format strings, different log
  path (`outputs/imagine-history.jsonl`); write side `bin/imagine:237-244`.

The duplicated part is ~20 lines per script; the *schemas differ* (q: ts/intent/model/
think/prompt/response/ms; imagine: ts/prompt/model/steps/seed/output/bytes/ms) and the
*display lines differ* (the jq `-r` format string is the per-tool part).

### What mature tools do

| Tool | Storage | Notes |
|---|---|---|
| **simonw/llm** | One SQLite `logs.db` (`io.datasette.llm/logs.db`), tables `responses`/`conversations`/`attachments`/`fragments` + FTS virtual table; `llm logs`, `llm logs -q term`, `--json` | https://llm.datasette.io/en/stable/logging.html |
| **aichat** | Per-session **YAML files** in a sessions dir (`AICHAT_SESSIONS_DIR`); `save: true` for message persistence, `save_session` for session save-on-exit; auto-compress past `compress_threshold` | https://github.com/sigoden/aichat/wiki/Configuration-Guide · https://github.com/sigoden/aichat/blob/main/config.example.yaml |
| **charmbracelet/mods** | **SQLite for metadata + cache files for message bodies**; SHA-1 conversation ids, `mods --list`, `-c <id>` continue | https://github.com/charmbracelet/mods · https://github.com/charmbracelet/mods/blob/main/db.go |
| **ollama CLI** | No conversation log at all — only a 100-entry readline **prompt** history (`~/.ollama/history`, ring buffer); users asking for chat saving is an open issue | https://docs.ollama.com/cli · https://github.com/ollama/ollama/issues/8576 |

Key observation: the tools that use SQLite (llm, mods) do so because they need
**cross-conversation features** — continue-by-id, full-text search, filtering by
model/conversation/fragment. None of q/imagine's subcommands need a join, an index, or
FTS. The tools whose history is "browse recent, inspect one" (which is exactly
`history`/`show N`) are fine with flat files; ollama itself stores *less* than this
toolkit does.

### Tradeoffs at hobby scale

- **One SQLite DB**: buys FTS, joins, `llm`-style filtering — at the cost of a Python/
  sqlite3 dependency in the read path, schema migrations, and losing `tail -f`/`jq`
  greppability. q's history write is currently "best-effort append, never fail the
  answer" (`bin/q:177`); SQLite locking semantics make that guarantee harder, not easier.
  **Wrong altitude for this toolkit.**
- **One shared JSONL** (both tools appending to a single file with a `tool` field):
  saves nothing — the schemas genuinely differ, and `q history` would need a `select(.tool=="q")`
  filter on every read. Merging the *files* creates work; only merging the *code* helps.
- **Status quo + shared functions**: the duplication is in the two ~20-line read-side
  function pairs, not the storage decision. The storage decision (JSONL-per-tool) is
  already the right one.

### Recommendation: **partial consolidate — share the code, keep the files**

Keep JSONL-per-tool (it matches or exceeds what ollama itself does, and `jq` on a flat
file is the bash-native query language). If/when the history functions are touched again
(GOALS.md item 7 already states the "only if touched again" gate), extract a single
`history_list <log> <jq-fmt>` / `history_show <log> <N> <jq-fmt>` pair into a shared lib
(see Facet 2) — the per-tool jq format string is the only real difference, so it
parameterizes cleanly to 2 real callsites each. Do **not** move to SQLite; revisit only
if a real "search all my old prompts" pull appears (then `llm`'s design is the reference).

---

## Facet 2 — Shared bash lib vs status quo

### Current state (exact duplication census)

- **TTY/NO_COLOR color init** (3×, byte-identical condition): `bin/q:24-26`,
  `bin/imagine:20-22`, `bin/lm:13-15` (lm has a smaller palette). `bin/warm` has no
  colors (plain echo help) — so it's 3 scripts, not 4.
- **Help helpers `_sec`/`_cmd`/`_opt`** (2×, only the `%-30s` vs `%-32s` column width
  differs): `bin/q:27-30`, `bin/imagine:23-26`.
- **history/show pair** (2×): `bin/q:69-88`, `bin/imagine:117-135` (Facet 1).
- **Warm-resident keep_alive guard** (2×, identical awk): `bin/q:133-137`,
  `bin/imagine:62-66`. Notably this is the duplication that already *bit*: imagine
  originally skipped the guard and silently un-pinned the warm model (GOALS.md item 1,
  fixed 2026-06-12 by copying q's block). That's the textbook "fix applied to one
  instance" failure mode of duplication.
- **`DIR=` self-locate + `source config.sh`** (4×): q:19-21, imagine:14-18, lm:10-11,
  warm:11-13. Two lines each; not worth touching.

### What small bash tool suites do

The community norm for a *suite* (multiple scripts shipped together from one repo) is a
sourced `lib.sh` resolved relative to `BASH_SOURCE` — exactly the pattern these scripts
already use for `config.sh`:

- Pattern guides: https://gabrielstaples.com/bash-libraries/ ·
  https://www.lost-in-it.com/posts/designing-modular-bash-functions-namespaces-library-patterns/
- Example libs: https://github.com/juan131/bash-libraries · https://github.com/aks/bash-lib
- Conventions that recur: source via `BASH_SOURCE`-relative path (works from any CWD —
  already satisfied here since all scripts compute `$DIR`); prefix "private" helpers with
  `_`; keep one lib per concern, not a kitchen sink; avoid command-substitution-heavy
  helpers in hot paths (irrelevant here — these run once per invocation).
- The counter-argument (from the duplication literature, e.g.
  https://solidsourceit.wordpress.com/2012/08/03/does-source-code-duplication-matter/):
  duplication's real cost is *fixes applied to one copy* — which is precisely what
  happened with the keep_alive guard. The cost of a sourced lib is coupling + losing
  single-file readability ("each script readable in one sitting" is a stated virtue in
  GOALS.md).

### Recommendation: **partial — one small `bin/_lib.sh`, only proven blocks**

The ≥2-real-callsites bar is *met today* for four blocks: color init (3×), help helpers
(2×), history/show (2×), keep_alive guard (2× — and one production bug already traced to
the copy diverging). A single ~40-line `_lib.sh` sourced right after `config.sh`
(same mechanism, zero new concepts) containing exactly:

1. color init + `_sec`/`_cmd`/`_opt`/`_ex`/`_kv` (pass column width or standardize on 32)
2. `ollama_resident <model>` → the awk check (the guard collapses to
   `keep=$(ollama_resident "$model" && echo -1 || echo 0)`)
3. `history_list` / `history_show` parameterized by log path + jq format

Stop there. Do **not** lib-ify arg parsing, the Python streamer, config loading, or
anything with one callsite. Net effect: ~60 duplicated lines deleted, each script still
readable top-to-bottom, and the next keep_alive-class fix lands once. This is consistent
with GOALS.md item 7's own gate ("only if touched again") — the research finding is just
that the keep_alive guard incident means the gate has effectively already fired for that
block; the rest can ride along whenever any of them is next touched.

---

## Facet 3 — Warm/residency engine

### Current state

- Server policy: `bin/lm-serve:13-19` — `OLLAMA_KEEP_ALIVE=0`, `MAX_LOADED_MODELS=2`,
  flash-attn, q8 KV; LaunchAgent-owned.
- Pin: `bin/warm:20-22` — 1-token `/api/generate` with `keep_alive=-1`; unpin =
  `ollama stop`; **no state file** — `ollama ps` is the registry.
- Per-request half: `bin/q:131-137` and `bin/imagine:59-66` — resident → `-1`, else `0`.

### Is per-request keep_alive idiomatic in 2026? **Yes — it's the documented mechanism.**

- Ollama FAQ: per-request `keep_alive` on `/api/generate`/`/api/chat` **overrides**
  `OLLAMA_KEEP_ALIVE`; `-1` pins, `0` unloads immediately; expiry is tracked
  **per loaded model independently** — exactly the two-tier design here.
  https://docs.ollama.com/faq · https://ollama.readthedocs.io/en/api/
- Community guidance (2025–2026) frames the recommended pattern as: env var for the
  default policy, per-request override for warm-up (`-1`) and batch-release (`0`) —
  i.e., precisely lm-serve + warm + q's guard.
  https://markaicode.com/ollama-keep-alive-memory-management/ ·
  https://mljourney.com/ollama-keep-alive-and-model-preloading-eliminate-cold-start-latency/ ·
  https://sumguy.com/ollama-memory-management/
- One known sharp edge tracked upstream: any client that sends its own `keep_alive`
  wins (last-writer-wins) — the reason imagine's missing guard could un-pin warm, and
  the subject of ollama issue #11002 (asking for a server-side override).
  https://github.com/ollama/ollama/issues/11002

### Newer primitives surveyed — none beat this design under "no idle cost, no daemon"

| Primitive | What it offers | Why not here |
|---|---|---|
| **LM Studio JIT + idle TTL / auto-evict** | TTL-based auto-unload (default 60 min), per-request `ttl` field | It's a **timer**, the exact thing GOALS.md's non-goals reject ("residency is a human choice, never a timer"); also a GUI-app-resident server. https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict |
| **llama.cpp router mode** (new, 2026) | Auto-discovers models, loads on demand, **LRU eviction** at `--models-max`, `/models/load`/`/models/unload` endpoints | Equivalent power to `MAX_LOADED_MODELS=2` + keep_alive, but trades Ollama's model registry/Modelfile ecosystem for manual GGUF management. Worth knowing it exists; not worth migrating. https://huggingface.co/blog/ggml-org/model-management-in-llamacpp |
| **llama-swap proxy** | YAML model→command map, TTL countdown per model, hot-swap any backend (llama.cpp, vllm, even stable-diffusion.cpp) | A **resident Go proxy daemon** — fails the no-daemon rule; its TTL is again a timer. Interesting only if the toolkit ever needs one front door over ollama+mflux simultaneously. https://github.com/mostlygeek/llama-swap |
| **mlx-lm server** | Native MLX, wired memory | Server is documented as not production-ready for long sessions (memory-management issues as of mid-2026), no residency policy primitives comparable to keep_alive. https://github.com/ml-explore/mlx-lm |

### Recommendation: **leave alone (it's the idiom), consolidate the *thinking* into the lib**

The architecture is validated by the 2026 ecosystem — everyone else converged on the
same three knobs (default policy env, per-request override, max-loaded cap), and the
alternatives that "consolidate warm thinking" do it with timers or daemons, both
explicit non-goals. The only consolidation worth doing is code-level: the resident-check
awk is the single piece of "warm thinking" that lives in two places (`bin/q:133`,
`bin/imagine:62`) — move it to `_lib.sh` as `ollama_resident` (Facet 2) so the contract
"never disturb the pin" has exactly one implementation. Optionally fix the GOALS.md item-8
nit while there: `WARM_KEEP_ALIVE` hardcoded at `config.sh:11` vs the `${VAR:-}` pattern
of its siblings.

---

## Facet 4 — Config + model registry

### Current state — a new imagine model touches 3 places

1. Registry: `resolve_model()` case, `bin/imagine:31-40` (name → binary + args + default
   steps/guidance).
2. Help: MODELS section, `bin/imagine:105-110` (name + one-line tradeoff blurb).
3. Config comment: `config.sh:16` ("Registry names: schnell · flux2 · qwen · dev").

GOALS.md already flags this ("acceptable at this scale; just know it") and Task 13 will
add `ideogram4` + `z-image-turbo`, i.e., the 3-touch cost is about to be paid twice.
On the LLM side there is no registry at all — `WARM_MODEL` in `config.sh:7` plus `-m`
pass-through — which is correct (ollama *is* the registry; `ollama list` enumerates it).

### What comparable tools do

- **simonw/llm**: models come from plugins; user-level naming is a flat
  **`aliases.json`** (`llm aliases set/list/path`) — data file, not code.
  https://llm.datasette.io/en/stable/aliases.html
- **aichat**: declarative **`config.yaml`** `clients:` list — each model is a data entry
  with per-model capability overrides (`max_input_tokens`, `supports_vision`, …); default
  model is one `model:` key. https://github.com/sigoden/aichat/blob/main/config.example.yaml
- **llama-swap**: YAML map model-name → launch command + per-model `ttl` — the purest
  "registry as data" example. https://github.com/mostlygeek/llama-swap
- **ollama**: the store itself is the registry; tools just pass names through.

The pattern across all four: **model registry = data, not code**, and help text/UI is
*derived* from the data, not hand-maintained in parallel.

### Recommendation: **partial — derive the help from the registry; don't add a config format**

A YAML/JSON registry file would be over-engineering here (a new parse dependency for 4–6
entries; aichat needs it because it federates 20+ providers — imagine has one backend
family). The hobby-scale move that gets the same "one place to update" property without
new machinery:

- Keep `resolve_model()` as the single source of truth, but **add the blurb to it** —
  e.g. each case line also sets `DESC="fast ~25s · great light · weak text"`, and a tiny
  `list_models()` iterates the known names calling `resolve_model` to print the MODELS
  help section. New model = one case line again, genuinely.
- Drop the name list from `config.sh:16`'s comment in favor of "see `imagine -h` MODELS"
  (comments that enumerate code facts drift — same rot class as help text).
- If even that feels heavy, the minimal version: move the model list into a single
  `MODELS_HELP` heredoc adjacent to `resolve_model` so the two places to touch are at
  least *on the same screen*. But since Task 13 is about to add two models, doing the
  derive-help version *as part of Task 13* (not speculatively before it) is the
  right sequencing — it then has a real caller the day it's written.

---

## Facet 5 — Other consolidation facets spotted

### 5a. Server health check / error path (consolidate — small, real win)

Three different behaviors for "is the server up":

- `bin/lm:38` — `curl -s -m 3 /api/version` with a friendly DOWN message naming the
  LaunchAgent.
- `bin/q` — **no check**; connection-refused = raw Python traceback (GOALS.md item 3,
  still open).
- `bin/imagine` (enhance/critique) — `curl --max-time`, silently falls back to the raw
  idea (`bin/imagine:72`) — correct behavior, but the down-server is invisible.

One `ollama_up()` in `_lib.sh` (the lm:38 curl) + a one-line
`server down — launchctl kickstart gui/$UID/com.alcatraz.local-models-ollama` hint fixes
GOALS.md item 3 and gives `imagine --enhance` an optional dim notice, with one
implementation. This is also the natural seed of the proposed `lm doctor` (item 6):
doctor = `ollama_up` + warm-model-built + mflux-venv + wrappers-on-PATH, all checks the
lib already half-owns.

### 5b. Output/log directory conventions (leave alone, one nit)

`logs/` (q history) vs `outputs/` (images + imagine history + steps/). The asymmetry —
imagine's *history* living under `outputs/` next to the images rather than under `logs/`
— is mildly surprising, but moving it breaks `imagine show N`'s stable line numbers and
existing muscle memory for zero functional gain. Leave it; the README/STATE.md already
documents both paths.

### 5c. Help conventions (already consolidated — protect it)

All commands follow `conventions/cli-help-design.md` (colored, TTY/NO_COLOR-aware,
sections, examples) — GOALS.md correctly calls consistency a feature. The lib extraction
in Facet 2 *protects* this (one palette, one column width) rather than changing it.
`warm`'s plain-echo help is the one outlier; harmonizing it is a 5-minute ride-along
the next time warm is touched, not a task.

### 5d. The two inline Python blocks (leave alone)

q's streamer (`bin/q:141-187`) and imagine's logger (`bin/imagine:237-244`) are both
Python-in-bash but share nothing meaningful (streaming chat vs one-line append). A shared
Python module would be a framework smell. The JSONL-append could become a `jq`-based
`history_append` in the lib *if* Facet 1's extraction happens anyway — optional.

---

## Summary table

| # | Facet | Verdict | Trigger/sequencing |
|---|---|---|---|
| 1 | History storage | **Keep JSONL-per-tool**; share read-side code only | with Facet 2 lib |
| 2 | Shared bash lib | **Yes — one small `_lib.sh`**, 4 proven blocks only | the keep_alive-guard bug already fired the "touched again" gate |
| 3 | Warm engine | **Leave alone** — per-request keep_alive IS the 2026 idiom; alternatives are timers/daemons (non-goals) | extract `ollama_resident` into lib |
| 4 | Model registry | **Partial** — derive MODELS help from `resolve_model`; no config-file format | do it inside Task 13 (real caller) |
| 5a | Health check | **Consolidate** — one `ollama_up()`; fixes q traceback (GOALS item 3), seeds `lm doctor` (item 6) | with lib |
| 5b | Output dirs | Leave alone | — |
| 5c | Help conventions | Already consolidated; lib protects it | — |

## All sources

- https://llm.datasette.io/en/stable/logging.html — llm SQLite logs.db, schema, `llm logs`
- https://llm.datasette.io/en/stable/aliases.html — llm aliases.json
- https://github.com/sigoden/aichat/wiki/Configuration-Guide — aichat sessions/config
- https://github.com/sigoden/aichat/blob/main/config.example.yaml — aichat clients/model declarations
- https://github.com/charmbracelet/mods — mods conversation saves
- https://github.com/charmbracelet/mods/blob/main/db.go — mods SQLite metadata
- https://docs.ollama.com/cli · https://github.com/ollama/ollama/issues/8576 — ollama CLI history (readline-only)
- https://docs.ollama.com/faq — keep_alive semantics, per-request override
- https://ollama.readthedocs.io/en/api/ — API reference
- https://github.com/ollama/ollama/issues/11002 — last-writer-wins keep_alive sharp edge
- https://markaicode.com/ollama-keep-alive-memory-management/ · https://mljourney.com/ollama-keep-alive-and-model-preloading-eliminate-cold-start-latency/ · https://sumguy.com/ollama-memory-management/ — 2025-26 keep_alive practice
- https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict — LM Studio JIT/TTL/auto-evict
- https://huggingface.co/blog/ggml-org/model-management-in-llamacpp — llama.cpp router mode
- https://github.com/mostlygeek/llama-swap — llama-swap proxy
- https://github.com/ml-explore/mlx-lm — mlx-lm server state
- https://gabrielstaples.com/bash-libraries/ · https://www.lost-in-it.com/posts/designing-modular-bash-functions-namespaces-library-patterns/ · https://github.com/juan131/bash-libraries · https://github.com/aks/bash-lib — bash lib norms
- https://solidsourceit.wordpress.com/2012/08/03/does-source-code-duplication-matter/ — duplication cost (fix-one-copy failure mode)
