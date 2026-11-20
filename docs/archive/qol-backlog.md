# QoL backlog — noticed, not yet built

Quality-of-life observations from real use. Captured so they're not lost; **NOT acted on until
they earn it** (propose-don't-build, kept lean). Living doc — append as things come up.

---

## Rendered output / "cached re-render" — noticed 2026-06-21

**Observation.** Some `q` answers are plain text, some are raw markdown. Sometimes you want to view
the markdown through `glow`/`bat` (aliased `cat`). Re-running to pipe it loses two things:
1. the response isn't cached, so temp-0 gives a *usually-but-not-identical* answer;
2. piping to a pager loses streaming (you still get tokens, just not the live render).

**Framing (user).** Not a problem — the price of simplicity + unix piping. Common enough to note.

**Works today.** `q show N | glow` re-renders the *cached* Nth response from history (no re-run, no
drift). The history log already stores every response.

**Possible directions (low priority — do NOT build speculatively):**
- `--render` / `--md` flag: stream raw tokens to the TTY live, *then* re-render the buffered
  response through `glow`/`bat` at the end — streaming AND rendered, no second model call.
- a thin `q render [N]` ( = `q show N | ${PAGER:-glow}` ) so the cached re-render is one verb.
- leave as-is; `q show N | glow` is the honest unix answer.
