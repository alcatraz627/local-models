# Codex i-dream bounded live pass, 2026-09-27

## Result

The first approved Codex-only pass selected 20 of 136 pending events from
`codex-sessions`. The original run stored five malformed insights because the
model used fields the parser silently defaulted to empty. That append-only
record remains in
`/Users/alcatraz627/.claude/adapters/codex/i-dream/dream/insights.jsonl` as
an audit trail. Two retries failed parsing and left the restored Codex cursor
unchanged. The final replay returned five schema-valid insights using 3,513
reported model tokens. The cursor now points to
`01a0a4cf-5d5d-7e62-9c29-c19d4d055ee3`, the twentieth selected event.
No other domain was selected, and the cross-domain pass did not run.

The first two failed retries reported zero tokens despite making model calls.
The receipt code now retains `tokens_used` for failures after a model response;
that fix passed tests but has not been exercised on another live failure. The
actual total cost of the three retries cannot be recovered from those old
receipts.

## What the insights support

| Insight | Evidence check | Decision |
| --- | --- | --- |
| Guardian subagents carry output from launcher sessions | Three cited guardian events exist and have outcomes/handbacks. The claimed pairing to exec parents was not cited. | Plausible operational hint. Verify parent mapping before making a rule. |
| UI builds need a standing two-pass structure | One cited prompt explicitly resumes work left about 80% done. | Evidence of one stalled build, not a general process rule. |
| Pre-PR review is a recurring Codex route | Three cited review prompts exist across separate repos. | Useful descriptive pattern. A new brief template needs a demonstrated gap beyond prompt variation. |
| File-based audit briefs improve claim count | One cited file-brief audit shows 27 `verified_claims` lines. That field counts handback lines, not verified correctness. | Reject the claimed causal benefit. |
| Codex meta-work should be excluded from product metrics | The association has no evidence IDs in the current schema. | Keep as a question for metric design, not a finding. |

No insight was promoted into gcc guidance. A successful parse and real event
IDs are necessary, but they do not establish the interpretation. Future dream
passes should avoid causal or standing-rule claims from one example and should
give associations their own evidence IDs. An output reviewer can then sample
only the cited records instead of re-reading the corpus.

## Code and checks

`i-dream dream-pass --domain NAME --dry-run` previews the bounded delta and
prompt size. Real passes select at most 20 events per domain, validate parsed
fields and batch evidence before storing insights, and advance only through
selected events. Codex and two older domain prompts now use the parser's
field names. The latest `cargo test` run in
`/Users/alcatraz627/Code/Claude/i-dream` reported 548 unit tests passed,
12 ignored, then 20 CLI and 5 restoration tests passed. `cargo build --bin
i-dream` rebuilt the local debug binary. These checks do not prove future
model output quality.
