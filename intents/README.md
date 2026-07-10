# intents/ — the `q` intent registry

Each `<name>.toml` defines one `q` intent: a named *(system-prompt + ctx requirement)*. `bin/q`
loads these at call time, so **adding an intent is dropping a file here — no code change.**

## Schema
```toml
name = "explain-code"            # the verb (matches the filename)
summary = "what the code does"   # one line, shown by `q intents`
needs_ctx = true                 # true → requires a document (--ctx/--file/stdin) or it's refused
system_prompt = "Explain ..."    # the system prompt sent to the model
```

**Reserved** (documented, not yet consumed — wired when the Governor / intent-graduation use them):
`default_tier` (`small|big|code`) · `ctx_glob` (the file pattern an auto-graduated intent targets).

## Adding an intent
Drop `intents/<verb>.toml` with the four fields. It's immediately usable as `q <verb> "..."` and
shows up in `q intents`. Document-grounded verbs set `needs_ctx = true`.

Graduated automatically: the weekly self-audit proposes candidates from your usage
(`topics/intent-candidates-*.md`); you approve one by dropping its file here. *(See `docs/07 §6`.)*
