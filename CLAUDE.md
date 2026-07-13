# local-models — orientation for an agent with no context

A local LLM + vision + image-gen toolkit for one Apple Silicon Mac (M5 Pro, 64 GB). Every
tool runs **on this machine, $0, offline**, alongside cloud Claude. You are usually the
*user* of these tools, not just their maintainer.

**Read in this order:** `docs/STATE.md` (current state + what's pending, kept current) →
`docs/CAPABILITIES.md` (the full menu with copy-paste examples) → the design doc for
whatever you're touching (`docs/03`–`docs/10`).

## The two hard rules

1. **No idle penalty.** Nothing stays resident unless explicitly pinned or leased
   (`warm`). A tool that silently keeps 23 GB warm is a bug.
2. **Trust = a passing gate, never model confidence.** Every local-model output crosses a
   mechanical gate (a schema, a judge, a test) before anyone believes it. "The model said
   so" is not evidence anywhere in this repo.

## Layout

| Path | What |
|---|---|
| `bin/` | the CLIs on PATH — `q` `see` `review` `imagine` `warm` `lm` (front door) |
| `lib/` | the non-CLI machinery — extractors, ledgers, gates (`vis-compare.py`, `vis-ledger.py`, `asset-verify.py`, `findings-gate.py`, `e8-dom.py`) |
| `intents/` | intents-as-data — a `q` intent is a TOML (system prompt + tier + ctx need) |
| `probe/fixtures/` | the model-free battery (`vis-battery.py`) — the correctness contract |
| `scripts/verify.sh` | **the one command that says whether the suite works** (~30s) |
| `docs/` | numbered design docs; `STATE.md` is the live one |
| `logs/`, `outputs/` | JSONL histories + run artifacts — **these are the agent API** |
| `config.sh` | model tiers + defaults. Read it before assuming a model name |

## Verify before you believe

```bash
bash scripts/verify.sh                              # the whole suite (~37 checks)
.venv/bin/python probe/fixtures/vis-battery.py      # the model-free battery (50 assertions)
```

**Use `.venv/bin/python`, never bare `python3`** — PIL and the extractors live in the venv.
A green battery is the bar for any change to `lib/`.

## Gotchas that have bitten before

- **`imagine` refuses to run on a half-downloaded model.** That is deliberate: a partial HF
  cache silently re-enters a multi-GB fetch and looks exactly like a slow render (it once
  burned 38 minutes at 2% CPU). The preflight prints the exact `hf download` command. Note
  `hf --include` takes **one pattern per flag** — extras become positional filenames and
  silently override the filter.
- **Histories are the API.** `logs/{q,see,fleet,gem,compare}-history.jsonl` +
  `outputs/imagine-history.jsonl` record every run, successes *and* failures. Build on
  those, not on parsing prose.
- **Constrained decoding beats prose parsing** — `q --format SCHEMA`, `see --ui --json`,
  `review --findings` all return schema-valid `.data`. But **the 35b code tier ignores
  Ollama's format constraint** — pin `-m small` when you need schema compliance.
- **The judge never assigns status words.** In the visual-compare loop, `fixed` /
  `persisting` / `regressed` are set comparisons computed by `lib/vis-ledger.py`. A model
  is contractually barred from inventing them, exactly as it is barred from inventing a
  measurement.
- **Scores are not progress.** In a convergence loop, region/pixel metrics *saturate* the
  moment composition moves — a round once fixed 3 of 5 divergences while grid-delta rose
  93.8% → 100%. Read progress from the ledger's transitions. The tool says so in-band.

## The visual-compare stack (the newest, largest capability)

Answers **"does B faithfully imitate A?"** — for a rebuilt UI, a regenerated icon, a
re-rendered image. Three layers, strict roles: **scripts measure, models judge, the ledger
tracks.**

```
see diff A B --json     L1 · $0 evidence — text/colour/hash/shape. CANNOT fabricate.
   ↓
/vis-compare A B        L2 · Claude judges vs your taste policy (gcc skill) →
   ↓                         looks-worse | neutral | improvement | not-worth-chasing
/vis-compare --loop     L3 · fix → re-render → re-compare → ledger → converge or stall
```

Design + honest built-vs-deferred inventory: `docs/10-visual-compare-design.md`.
The taste policy is user-owned and lives in gcc: `~/.claude/skills/vis-compare/policy.md`.

## Working norms

- **Fixtures first.** A guard that would catch the capability failing lands *before* the
  capability — and you must watch it go **red** before you trust it green. Twice, a
  validator deleted a load-bearing mechanism and the suite stayed green because the fixture
  was blind to it by construction.
- **Adversarial validation is the gate.** Non-trivial work goes through `/bloop`, whose
  sub-agent tries to *break* the change. Across its first 8 runs it found a real defect
  every single time, always after a self-review that felt complete.
- Commits are fine on feature branches (this repo is unprotected). **Pushing `main` needs
  fresh user approval, every time.**
