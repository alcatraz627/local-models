# Lane 2: the `lm gemini` gateway

Read-only research pass on `~/Code/local-models`'s gemini lane: what it is, how it is
actually used, where it falls short of its own design, and what the outside world says
about the backend it wraps. Every local claim below cites a file:line or a runnable
`jq`/`rg` command; external claims cite two sources with dates (today: 2026-08-30).

## 1. Actual usage (from `logs/gem-history.jsonl`, 197 rows)

```
jq -r '.kind' logs/gem-history.jsonl | sort | uniq -c
   120 oneshot   16 ask   10 ask+reset   5 ingest   1 ingest+reset   45 error
```

- **Stateless one-shot dominates.** 120/197 rows (61%) are `oneshot`, with no session
  and no ingest. The `ingest`/`ask` session model the design centers on (`lib/gemini:1-16`,
  the doc-comment contract) accounts for only 32/197 rows (16%), and only two projects
  ever called `ingest` at all: `local-models` (5 rows) and `vb-guidebook` (1 row):
  `jq -r 'select(.kind|test("ingest")) | .session' logs/gem-history.jsonl | sort | uniq -c`.
  The lane is used as a cheap one-off text generator, not as the "ingest a corpus, ask
  it questions" pairing tool it was built to be.
- **By month:** 164 rows in 2026-07 (the harness's launch month), 33 in 2026-08:
  `jq -r '.ts[0:7]' logs/gem-history.jsonl | sort | uniq -c`. Usage dropped about 5x
  after launch month, consistent with no skill ever wiring it in (§3).
- **By session** (`jq -r '.session // "null"' … | sort | uniq -c`): `local-models` 100,
  `neutral` 41, `.claude` 17, `speedway` 13, `versable-builder` 8,
  `studio_search_jul_26-fable` 5, `vb-guidebook` 3, `automation` 3, others 1 each. Three
  distinct real workloads show up:
  - **`local-models` (100 rows):** the harness's own dogfooding/testing traffic.
  - **`neutral` (41) and `.claude` (17):** large one-shot **batch classification** calls.
    Each `oneshot` call embeds a big prompt (a transcript-window classifier schema,
    roughly 40 lines of instructions plus inline JSONL rows) and asks for structured
    JSONL back. This is `pyramid-sweep`-shaped work (mine a big corpus, judge with a
    cheap/fast model), but **no skill drives it**: `rg -l "lm gemini" ~/.claude/skills`
    returns nothing. These calls were typed by hand into the CLI.
  - **`studio_search_jul_26-fable` (5) and a `sa-1` row:** real-world **web-grounded
    lookup** work, finding official websites/careers pages for named companies and
    returning structured JSON with nulls for unknowns. This is the "breadth research"
    use the brief flagged, distinct from ingestion.
- **The 2026-08 error cluster.** 11/33 August rows are errors (33%, not the 26% the
  brief estimated; recompute: `jq -c 'select(.ts[0:7]=="2026-08" and .kind=="error")'
  logs/gem-history.jsonl | wc -l` gives 11; `jq -c 'select(.ts[0:7]=="2026-08")' … | wc -l`
  gives 33). 8 of those 11 are `timeout` (the wrapper's `--timeout`, default 180s,
  killed via the process-group SIGALRM in `lib/gemini:73-80`). They cluster in two
  sessions:
  - `studio_search_jul_26-fable`, 2026-08-12: 4 consecutive timeouts running the
    web-lookup prompt above, interleaved with one 76s success
    (`jq -r 'select(.session=="studio_search_jul_26-fable")' logs/gem-history.jsonl`).
    These are agentic web-browsing calls (find and verify a URL), inherently slower and
    more variable than pure-text generation; the fixed 180s cap is a bad fit for that
    workload shape.
  - `.claude`, 2026-08-20: 4/17 calls timed out running the transcript-classifier
    one-shot; the 13 that succeeded took 56 to 89s each
    (`jq -r 'select(.session==".claude") | "\(.kind) \(.ms)"' logs/gem-history.jsonl`).
  - One `item_missing` (empty prompt, `vb-guidebook`, 2026-08-16), and no retry logic
    beyond the wrapper's one session-reset retry (`lib/gemini:172-183`, which only
    fires for `--list-sessions`-style vanished-session errors, not for timeouts).
- **Timeouts are silently swallowed by hand-retry, not by the wrapper.** Every
  timed-out prompt in the two clusters above was followed minutes later by a plain
  re-run of the same or a trimmed prompt that succeeded; the human/agent noticed and
  retried. The wrapper itself does not retry on timeout (`lib/gemini:169-183` only
  retries the vanished-session class).
- **Latency, successes only** (146 `oneshot`/`ask` rows,
  `jq -r 'select(.kind|test("oneshot|ask")) | .ms' logs/gem-history.jsonl | sort -n | …`):
  min 3s, median 27s, mean 41s, max 289s. Two calls (205s, 289s) exceeded the 180s
  default, meaning `--timeout` was overridden for them; nothing in the history log
  records the override value used, only elapsed `ms`.
- **Who calls it:** never the CLI itself autonomously, always Claude (agent or main
  session) typing `lm gemini …` by hand, or the user directly. No skill, hook, or
  script in `~/.claude` invokes `lm gemini` programmatically
  (`rg -l "lm gemini" ~/.claude/skills` returns empty; the four hits outside skills are
  all doc/rule files: `rules/model-tier-routing.md`, `features/model-tier-harness.md`,
  `features/local-models.md`, `features/kanban.md`).

## 2. What was attempted (the design)

`lib/gemini` (401 lines, read in full) implements:
- A single stable wrapper. "Claude never calls the gemini binary directly"
  (`lib/gemini:3-6`), the explicit goal being backend-swap insulation ahead of the
  Homebrew formula's 2026-12-18 EOL.
- Model pinned to `gemini-3.5-flash` via `GEMINI_MODEL` env (`lib/gemini:14`). The
  routing rule says other gemini models were unreliable (comment, same line).
- Four verbs: bare prompt (`oneshot`, stdin becomes context), `ingest <files>` (feed a
  corpus into a **per-project** persistent session), `ask "question"` (query that
  session, `--session NAME` for cross-project), `ingest-repo [dir]` (repomix-pack a
  whole tree, gitignore-aware, `--compress` cutting roughly 70% of tokens, then ingest
  the pack).
- Sessions are **UUID-backed files** under `logs/gemini-sessions/<name>.id`
  (`lib/gemini:150-160`). gemini-cli semantics required the wrapper to pick
  `--session-id` (create) vs `-r <uuid>` (resume) itself, since the backend errors on
  the wrong verb (comment, `lib/gemini:147-149`).
- **Self-heal on a vanished session.** gemini-cli's own chat store
  (`~/.gemini/tmp/<project>/chats`) is cleaned on its own schedule; a resume that
  errors gets one fresh-session retry, surfaced (never silent) as `session_reset:true`
  or a stderr note (`lib/gemini:169-215`).
- **Hard wall-clock cap** via a perl fork/alarm that kills the whole process group,
  because gemini-cli can hang on an interactive prompt it wasn't told to skip
  (`lib/gemini:66-80`).
- **Structured failure classes**, not raw stderr: `gemini_unavailable` (exit 11,
  auth/tier/quota/not-installed, the class routing.md's table names as "flag to the
  user, fall back"), `timeout` (13), `invalid_args`/`item_missing` (2/12),
  `gemini_error` (10, everything else, first 200 chars of the last two output lines).
  Every call, success or failure, logs one JSONL line to `gem-history.jsonl`
  (`lib/gemini:52-58`, mirrors the `q` history contract).
- **Read-only posture by construction:** `--approval-mode plan --skip-trust`
  (`lib/gemini:76-80`). Gemini can generate text, never edit or execute.
- **Auth isolated to the wrapper's process tree.** The key lives in `~/.gemini/.env`
  (mode 600, verified: `ls -la ~/.gemini/.env` shows `-rw-------`), sourced only
  inside `lib/gemini:22-26`, never exported to the parent shell.
- **Output cleanup.** The wrapper strips known gemini-cli housekeeping noise (a
  ripgrep-missing warning, `[STARTUP]` phase lines, node deprecation notices, a
  plan-mode file-read-error leak) and, for `ingest` replies specifically, trims back
  to the contractually-required numbered digest if the model echoed the corpus first
  (`lib/gemini:216-231`), a real observed failure mode the wrapper works around rather
  than trusts the model to avoid.
- **Trust posture is explicit and honest.** routing.md calls gemini output "untrusted
  content, Claude verifies before load-bearing use"
  (`~/.claude/rules/model-tier-routing.md:34`); `lib/gemini`'s own comment says the same
  thing ("the wrapper guarantees structure, not truth", `lib/gemini:218-219`). Nothing
  in the repo implements how that verification happens; it is a norm stated in prose,
  not a mechanism (contrast with `lib/findings-gate.py` and `lib/vis-ledger.py`, which
  are mechanical gates for other lanes per this repo's CLAUDE.md rule that trust is a
  passing gate, never model confidence).

Session auth: `~/.gemini/settings.json` reads
`{"security":{"auth":{"selectedType":"gemini-api-key"}}}`. (Own read, not printed:
`.env` mode 600 confirmed present, not opened.) This is a paid, token-billed API key,
not the free consumer OAuth path; material for §6/§9.

## 3. Gaps

1. **The routing rule's stated role does not match how the lane is used.** The rule
   says "large-context ingestion / mass ideation -> lm gemini session, digest back".
   Ingestion is 16% of calls, across two projects ever. The two real workloads, batch
   transcript classification and web-grounded company lookups, both run as repeated
   stateless `oneshot` calls with the full prompt re-embedded every time, which is
   exactly what the session/ingest machinery exists to avoid paying for repeatedly.
2. **Zero skill wiring.** `pyramid-sweep` (the skill whose own description matches the
   `.claude`/`neutral` transcript-classification workload almost verbatim: "mine a
   large transcript corpus through progressively smarter model tiers") does not call
   `lm gemini` anywhere in its own files, per `rg`. An agent in another project has no
   discoverable path from "I have a big corpus, I want a cheap model to sift it" to
   `lm gemini` except reading `docs/CAPABILITIES.md` or the routing rule by hand and
   typing the CLI itself, which is exactly what happened in every one of the 197 rows.
3. **Reliability: the fixed 180s cap is a bad fit for the workload that actually needs
   the lane most.** The web-lookup workload (agentic browsing plus verification) times
   out repeatedly (4 straight timeouts in one session); the batch-classification
   workload also clips at 180s on about 24% of its calls even though most of its own
   successful calls run 56 to 89s. There is no retry-with-backoff, no adaptive timeout,
   and no `--timeout` guidance surfaced to the caller before they hit the wall once.
   Two calls in the whole history ran past 180s only because someone thought to pass
   `--timeout` manually; nothing in `-h` text or CAPABILITIES.md tells a caller when to.
4. **No verification plumbing for the "untrusted, Claude verifies" contract.** The rule
   states the posture; nothing enforces or even scaffolds it. Compare
   `lib/findings-gate.py` (fails loud on degenerate structured output) or
   `lib/vis-ledger.py` (computed set diffs, never model-asserted) elsewhere in this
   same repo: the gemini lane has no equivalent. A digest gemini writes ("what the repo
   is, its main components") is handed straight back to the calling agent as fact,
   with only a code comment as a reminder to check it.
5. **No cost/quota visibility.** `gem-history.jsonl` records `ms` (latency) but not
   token counts, so there is no way to answer "how much of the abundant gemini budget
   has been used this month" from the history alone, the one artifact the routing rule
   calls the API for.
6. **The backend itself is now genuinely at risk, not just Homebrew-deprecated.**
   See §6: the open-source gemini-cli is fine on API-key auth, but Google shut down
   the hosted, consumer-OAuth Gemini CLI service entirely on 2026-06-18, a harder
   deadline than the Homebrew formula's 2026-12-18 disable date the repo's own comments
   cite. The wrapper's comment (`lib/gemini:3-6`) only mentions the Homebrew EOL; it
   should also flag that the product this CLI talks to (not just the packaging) has
   already had one shutdown event, and that the fix (already applied: API-key auth,
   `~/.gemini/settings.json.bak-20260707` shows a same-day switch away from
   `oauth-personal`) is load-bearing and worth a comment explaining why it's pinned.
7. **`ingest-repo`'s exclusion list is hand-maintained and narrow.** It excludes
   `.claude/output/**`, `outputs/**`, and a few binary extensions
   (`lib/gemini:135-136`) but not, for example, `node_modules`, `.venv`,
   `logs/*.jsonl` (which can be large), or `.git`. repomix itself is gitignore-aware so
   most of this is covered already, but the explicit list is a second, weaker filter
   layered on top with no test proving it stays in sync with what actually bloats a
   pack.

## 4. Ideal workflow

**For ingestion (the design's stated purpose, barely used today):**
1. An agent with a large corpus (a repo, N transcripts, a doc set) should not hand-type
   `lm gemini ingest <files>`. A verb, say `lm gemini digest <target> --schema
   <intent-name>`, should exist that packs the target (reusing `ingest-repo`'s repomix
   path, or a new transcript-batcher for the pyramid-sweep case), calls gemini once
   with a schema-constrained ask (gemini-cli supports `--output-format json`; the
   wrapper currently never passes it, see §6), and returns `{claims: [...], sources:
   [...]}` rather than free prose.
2. The calling agent (or a cheap local judge, per this repo's own "trust is a passing
   gate" doctrine) spot-checks a sample of the claims against the actual corpus before
   using them as load-bearing. For example, for a repo digest, grep for two or three
   named functions/files gemini claimed exist; for a transcript classification batch,
   re-run a handful of rows through the local `warm`/`small` tier as a second opinion
   and diff. This closes gap #4: today "Claude verifies" is a sentence in a rule file,
   not a step anything actually performs.
3. This is exactly the `pyramid-sweep` skill's own shape (mine cheap, refine through
   progressively smarter and costlier tiers, gate each phase, land on a human decision
   surface). The fix for gap #2 is not a new skill; it is wiring `pyramid-sweep`'s
   mining phase to call `lm gemini digest` when the corpus exceeds what a local tier's
   context window or cost profile can handle economically. `pyramid-sweep`'s own
   SKILL.md is the natural home for "here's when to reach for gemini instead of
   `lm fleet`".

**For breadth research and web lookups (the actual second real use, unaddressed by the
routing rule's own framing):**
1. This is closer to `q --web` (`lib/websearch`, DDG-lite, cited, offline-degrade, per
   `docs/STATE.md:158-159`) than to `ingest`/`ask`: a single grounded query, not a
   corpus. A `lm gemini research "question"` verb (or extending `q --web` to have a
   gemini-backed tier) should: set a workload-appropriate timeout (300s or more, not
   180s; the web-lookup cluster's own timeout pattern shows 180s is too tight for
   "find and verify N companies' websites"), request structured JSON output with an
   explicit null-when-unsure contract (the studio_search prompts already do this by
   hand, in-prompt; promote it to the wrapper), and log a confidence/verification note
   per claim the way `q --format` schemas do elsewhere in this suite.
2. Because this workload is inherently slower and more variable (agentic browsing, not
   pure generation), it should get its own timeout default distinct from `oneshot`'s
   180s, or the wrapper should accept `--timeout` and the CAPABILITIES.md example
   should show when to raise it. Right now no documentation anywhere tells a caller
   "web-lookup work times out at 180s by default, raise it."

## 5. Bridge: smallest changes ranked by benefit

1. **Fix the timeout mismatch for the two real workloads (cheap, high win).** Bump the
   `oneshot`/`ask` default from 180s to something nearer the observed p95 (about 90s
   for successes, but the two real-world workloads that timeout most need 300s or
   more), or better, make the default workload-aware: `ingest-repo`/large-context/
   web-lookup-shaped prompts get a longer cap than a short one-shot. Minimal version:
   just raise the default to 300s and document when to override; this alone would
   likely have eliminated about 8 of the 13 recorded timeouts.
2. **Add `--output-format json` passthrough to `run_gemini` and use it for
   `ingest`/`ingest-repo`'s digest contract**, instead of prompt-engineering "reply
   ONLY with a numbered digest" and post-hoc `awk`-trimming echoed content
   (`lib/gemini:216-231` exists because prose-contract compliance is unreliable;
   structured output sidesteps the whole workaround).
3. **Wire `pyramid-sweep` (or a new thin skill) to call `lm gemini` for its
   mining/breadth phase**, so the two real workloads (transcript classification, web
   lookups) stop being hand-typed CLI sessions and start being one command with
   built-in chunking, retry, and a place to log the eventual verification step. This is
   the single highest-leverage fix for gap #2: it converts "an agent has to already
   know this lane exists and type it by hand" into "the tool that already fits this
   shape of work reaches for it automatically."
4. **Add a lightweight verification step to the digest/ingest path.** Even a stub that
   greps two or three named claims back against the source corpus and flags mismatches
   would close the biggest doctrine-vs-practice gap (§3.4) at low cost.
5. **Log approximate token counts (or at least prompt/response byte length) in
   `gem-history.jsonl`**, so cost/quota visibility (§3.5) is derivable from the history
   the way `ms` already is, without needing to hit Google's billing console.
6. **Update the wrapper's own header comment** to name the 2026-06-18 hosted-CLI
   shutdown alongside the 2026-12-18 Homebrew EOL, and note that the API-key auth
   switch (already made, `~/.gemini/settings.json.bak-20260707`) is the reason this
   still works, so the next person reading `lib/gemini:3-6` understands why auth mode
   is what it is, not just that an EOL date is coming.

## 6. External research: Gemini CLI state, Aug 2026

- **The open-source `gemini-cli` this wrapper drives is not the same thing Google shut
  down.** Google stopped serving the hosted, consumer-OAuth Gemini CLI (free Gemini
  Code Assist for individuals, Google AI Pro/Ultra consumer accounts) on 2026-06-18:
  [aibuilderclub.com, "Is Gemini CLI Deprecated? Shutdown Date and What to Use Now"](https://www.aibuilderclub.com/blog/google-kills-gemini-cli-june-18-2026),
  corroborated by [thevibelog.dev, "Gemini CLI Deprecated 2026"](https://thevibelog.dev/blog/gemini-cli-deprecated-2026/).
  The open-source gemini-cli project itself continues to work against your own paid
  API key; the same source set confirms this, and Homebrew's own formula page
  independently confirms the packaging (not the product) sunset is a separate, later
  date: 2026-12-18 disable, replacement `antigravity-cli`
  ([formulae.brew.sh/formula/gemini-cli](https://formulae.brew.sh/formula/gemini-cli),
  cross-checked against [Homebrew/homebrew-core#289444](https://github.com/Homebrew/homebrew-core/issues/289444)).
  This repo's auth mode (`gemini-api-key`, confirmed live) is the unaffected path; the
  header comment undersells this by naming only the Homebrew date.
- **Separately, June 19 2026 also brought an unrelated API-key hardening deadline.**
  Google stopped accepting unrestricted Standard API keys on 2026-06-19, moving
  everyone to scoped "auth keys" tied to a service account, with a further cutover of
  remaining Standard keys around September 2026:
  [Google AI Developers Forum, "Action Required: Restrict Gemini API keys by June 19"](https://discuss.ai.google.dev/t/action-required-restrict-gemini-api-keys-by-june-19-to-avoid-service-disruption/171786),
  cross-checked with [cybernews.com, "Google ends unrestricted API keys"](https://cybernews.com/security/google-gemini-reject-unrestricted-standard-keys/).
  Unverified: whether the key in `~/.gemini/.env` (mode 600, not opened per secret
  policy) is a Standard key or already migrated to an auth key; worth a `curl`/`gemini`
  auth-mode check by someone with access, since a Standard key could start failing
  before September 2026 without warning.
- **Model and context.** `gemini-3.5-flash` (launched 2026-05-19) is priced $1.50/$9.00
  per million input/output tokens with a 1M-token context window:
  [pricepertoken.com, "Gemini 3.5 Flash API Pricing 2026"](https://pricepertoken.com/pricing-page/model/google-gemini-3.5-flash),
  cross-checked with [cloudzero.com, "Gemini pricing in 2026"](https://www.cloudzero.com/blog/gemini-pricing/).
  This is well above what `ingest-repo`'s repomix-compressed packs need for any repo
  this suite's size, so context ceiling is not the binding constraint; reliability and
  ergonomics are (§3).
- **Cost levers unused by this wrapper.** Context caching (implicit, on by default on
  paid projects, cutting cached-token cost up to 90%) and the async Batch API (50% off
  for work that can tolerate up to 24h turnaround) both exist and both apply cleanly to
  the batch-classification workload this lane already serves:
  [aifreeapi.com, "Gemini API Context Caching"](https://www.aifreeapi.com/en/posts/gemini-api-context-caching-reduce-cost),
  cross-checked with [yingtu.ai, "Gemini API Batch vs Context Caching"](https://yingtu.ai/en/blog/gemini-api-batch-vs-caching).
  The wrapper's per-call one-shot pattern (§1) pays full synchronous price on every
  repeated classification call; batching the `.claude`/`neutral`-style transcript
  windows into one Batch API job would plausibly beat both cost and the 180s timeout
  problem at once, at the cost of losing interactivity. Unverified: whether gemini-cli
  itself exposes Batch API access, or whether this would require a direct Gemini API
  HTTP call bypassing the cli binary entirely; the searches above describe the
  API-level feature, not gemini-cli's own flag surface for it.
- **Headless/structured output the wrapper doesn't use.** gemini-cli's non-interactive
  mode supports `--output-format {text,json,stream-json}`: JSON emits once at session
  end, stream-json emits one JSONL event per line in real time:
  [geminicli.com, "Headless mode reference"](https://geminicli.com/docs/cli/headless/),
  cross-checked with [inventivehq.com, "How to Use Gemini CLI Headless Mode for CI/CD"](https://inventivehq.com/knowledge-base/gemini/how-to-use-headless-mode).
  `lib/gemini`'s `run_gemini` (line 66-80) never passes `-o`/`--output-format`; it
  always takes plain text and hand-parses/strips it (§2, §3.2). This directly supports
  bridge item #2.
- **How others wire a cheap huge-context model as a Claude sidecar.** The pattern this
  repo already half-implements ("digest first, verify claims independently before
  load-bearing use") matches general RAG/multi-agent practice (cheap-reader-feeds-
  expensive-judge), but the specific "gemini as Claude Code sidecar" pairing is niche
  enough that targeted search returned only pricing/deprecation coverage, not a
  documented reference architecture. Flagging as unverified, no strong external
  precedent found, rather than asserting one exists.
- **Local long-context alternatives already on this machine** (from `ollama list` and
  `config.sh`): `gemma4:26b` (17GB, already `BIG_MODEL`/`UI_VISION_MODEL` in
  `config.sh:10,40`, described in-repo as "best prose + long-ctx") and
  `qwen3.6:35b-a3b` (23GB, `CODE_MODEL`). External research on the wider Qwen3.6/3.8
  family: Qwen3.6-27B ships Apache-2.0 with a 256K-token context window, and runs at
  about 17GB VRAM (Q4_K_M):
  [promptquorum.com, "Qwen 3.6 27B Local Setup Guide 2026"](https://www.promptquorum.com/local-llms/qwen-local-deployment-guide-2026);
  Qwen3.8-27B (shipped 2026-08-14, likely too new to be the model already on this
  machine) adds native vision and a 262,144-token window at a similar 17-18GB
  footprint:
  [orcarouter.ai, "Qwen3.8-27B on Apple Silicon"](https://www.orcarouter.ai/blog/qwen-3-8-27b-mlx),
  cross-checked with [kingy.ai, "Qwen3.8-27B Local Hardware Guide"](https://kingy.ai/blog/qwen3-8-27b-local-hardware-requirements/).
  Either is a real $0/offline fallback for corpora that fit under about 250K tokens
  when gemini is unavailable, or a caller wants to stay off the network entirely.
  Worth a `lm gemini`-unavailable fallback path pointing at `gemma4:26b` rather than
  just failing structured.

## 7. Uncertainties

- Whether the `~/.gemini/.env` API key is a Standard key (at risk of a Sept-2026
  cutover) or already an auth key; not checked, per secret-handling instructions.
- Whether gemini-cli's flag surface exposes the Batch API or explicit context caching,
  or whether those require calling the Gemini HTTP API directly, bypassing this
  wrapper's backend entirely.
- Whether the two >180s successful calls (205s, 289s in the history) used a manually
  passed `--timeout`, or some other path; the JSONL doesn't record the flag used, only
  elapsed `ms`.
- No external documented reference architecture found for "cheap huge-context model as
  a coding-agent sidecar with a verify-before-trust loop" specifically; this repo's own
  design may be more novel than the brief's framing assumed, or the right search terms
  weren't found.

## 8. Source table

| Source | URL/path | Date | Reliability |
|---|---|---|---|
| `lib/gemini` (full file, read) | `/Users/alcatraz627/Code/local-models/lib/gemini` | last touched 2026-07-10 (script header) | primary, direct read |
| `logs/gem-history.jsonl` (197 rows) | same repo | 2026-07-07 to 2026-08-20 | primary, direct read |
| `~/.gemini/settings.json`, `.env` (existence/mode only) | local | settings mtime 2026-07-07 | primary, direct read |
| `~/.claude/rules/model-tier-routing.md` | local | -- | primary |
| `~/.claude/features/model-tier-harness.md` | local | updated 2026-07-10 | primary |
| `docs/STATE.md`, `docs/CAPABILITIES.md` | local | -- | primary |
| `.claude/output/20260707-model-tier-harness/recon-gemini.md` | local | 2026-07-07 | primary, original design recon |
| aibuilderclub.com, Gemini CLI shutdown | https://www.aibuilderclub.com/blog/google-kills-gemini-cli-june-18-2026 | 2026 | secondary, cross-checked |
| thevibelog.dev, Gemini CLI Deprecated 2026 | https://thevibelog.dev/blog/gemini-cli-deprecated-2026/ | 2026 | secondary, cross-checked |
| formulae.brew.sh, gemini-cli formula | https://formulae.brew.sh/formula/gemini-cli | live page | primary (Homebrew's own page) |
| Homebrew/homebrew-core#289444 | https://github.com/Homebrew/homebrew-core/issues/289444 | 2026 | primary (GitHub issue) |
| discuss.ai.google.dev, API key restriction | https://discuss.ai.google.dev/t/action-required-restrict-gemini-api-keys-by-june-19-to-avoid-service-disruption/171786 | 2026-06 | primary (Google forum) |
| cybernews.com, unrestricted key end | https://cybernews.com/security/google-gemini-reject-unrestricted-standard-keys/ | 2026 | secondary, cross-checked |
| pricepertoken.com, 3.5 Flash pricing | https://pricepertoken.com/pricing-page/model/google-gemini-3.5-flash | 2026 | secondary |
| cloudzero.com, Gemini pricing 2026 | https://www.cloudzero.com/blog/gemini-pricing/ | 2026 | secondary, cross-checked |
| aifreeapi.com, context caching | https://www.aifreeapi.com/en/posts/gemini-api-context-caching-reduce-cost | 2026 | secondary |
| yingtu.ai, batch vs caching | https://yingtu.ai/en/blog/gemini-api-batch-vs-caching | 2026 | secondary, cross-checked |
| geminicli.com, headless mode reference | https://geminicli.com/docs/cli/headless/ | live docs | primary (official docs) |
| inventivehq.com, headless mode CI/CD | https://inventivehq.com/knowledge-base/gemini/how-to-use-headless-mode | 2026 | secondary, cross-checked |
| promptquorum.com, Qwen 3.6 27B guide | https://www.promptquorum.com/local-llms/qwen-local-deployment-guide-2026 | 2026 | secondary |
| orcarouter.ai, Qwen3.8-27B on Apple Silicon | https://www.orcarouter.ai/blog/qwen-3-8-27b-mlx | 2026-08 | secondary, cross-checked |
| kingy.ai, Qwen3.8-27B hardware guide | https://kingy.ai/blog/qwen3-8-27b-local-hardware-requirements/ | 2026-08 | secondary, cross-checked |
| local `ollama list`, `config.sh` | local | live | primary, direct read |
