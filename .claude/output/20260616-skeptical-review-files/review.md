# Skeptical review — q/lm file-handling additions (uncommitted, 2026-06-16)

Scope: `git diff HEAD` of `bin/q`, `bin/lm`, `docs/q-spec.md`, `docs/STATE.md`,
plus new `docs/03-tool-orchestration-decision.md`. READ-ONLY; all logic tested
against `/tmp` copies and isolated `bash -c` repros on this machine's bash
3.2.57. No q/lm model output was generated.

## Ranked findings

| confidence | file:line | check | what's suspect | how to verify |
|---|---|---|---|---|
| **HIGH** | `bin/lm:117-121` | 4 / set-e | **Human-mode `lm models` crashes on any model with a null/missing `.size`.** `((.size/1073741824*10\|floor)/10)` does `null / number` → jq fatal error (exit 5). jq error short-circuits the *entire* stream (no per-line recovery): if the null-size model is first, the listing prints nothing. Under `set -eo pipefail`, the failing `jq\|sed` pipe is mid-function, so `set -e` **aborts `lm_models` before the "default" footer line (122)** and `lm models` exits nonzero with a raw `jq: error … null and number cannot be divided` on stderr. `--json` branch (112) is safe (no division). | `printf '{"models":[{"name":"a"},{"name":"b","size":1}]}' \| jq -r '.models[]?\|(.size/1073741824)'` → exits 5, no output for `a`. Repro of set-e abort: `bash -c 'set -eo pipefail; f(){ echo before; false\|sed s/a/b/; echo AFTER; }; f; echo end'` → `AFTER` never prints. Fix: `(.size // 0)`. |
| **MEDIUM** | `bin/lm:106-107,117` | 4 / set-e | **`curl -s` lacks `-f`, so HTTP 500/404 from a *running* server returns exit 0** and a non-JSON body. The `\|\| {server down; return 1}` guard passes; then the human-mode `jq` (117) hits a parse error (exit 5) → `set -e` aborts before the footer, leaking `jq: parse error`. The sibling `lm_status` (line ~50) mitigates with `\|\| echo '[]'`; the new human pipe has no such fallback. Empty body (true connection failure) is already caught by the curl guard and jq tolerates empty input (exit 0), so only the HTTP-error path bites. | `printf '<html>500</html>' \| jq -r '.models[]?'` → exit 5. Confirm `curl -s` doesn't fail on 5xx (it doesn't without `-f`). |
| **LOW-MED** | `bin/q:183-189,192-194` | 6 / edge | **Empty file misclassified as binary.** `file -b --mime-encoding` returns `binary` for a 0-byte file (verified, incl. empty `.txt` which routes through the catch-all). So `q summarize --file empty.txt` emits `ctx_binary` "'…' looks binary — extract text first" instead of the intended `ctx_empty`/`ctx_required`. The `[ -s "$CTX_FILE" ]` guard at 192 fires *after* the in-`case` binary check, so it never gets the chance. Misleading, not a crash. | `: > /tmp/x.txt; file -b --mime-encoding /tmp/x.txt` → `binary`. Fix: short-circuit `[ -s ]` before the mime sniff, or treat 0-byte as empty/required up front. |
| **LOW** | `bin/q:189` | 1 / consistency | **Catch-all `CTX="$(cat "$CTX_FILE")"` has no `\|\| emit_error`**, unlike every other extraction branch (pdf/textutil all guard). If `cat` fails on an existing-but-unreadable file (permission race after the `[ -f ]` check at 172), `set -e` aborts with bash's bare exit 1 — bypassing the structured `ctx_*` error and machine-mode JSON. Low probability (needs a TOCTOU permission flip), but it's the one branch that breaks the otherwise-consistent guard pattern. | `bash -c 'set -e; X="$(cat /root/protected 2>/dev/null)"; echo reached'` style; the `[ -f ]` at 172 covers nonexistence but not unreadable. Add `\|\| emit_error ctx_unreadable …`. |
| **INFO** | `bin/q:225-229` | 3 / nudge | Path-in-prompt nudge: `set -f … for w in $QUERY … set +f` is **correct** — `set -f` (noglob) is restored, and the unquoted split is the intended word-iteration. No glob/word-split hazard since globbing is disabled for the loop. **Documented limitation holds:** `[ -f "~/foo" ]` does NOT tilde-expand (verified), so a `~/...` path named in the prompt silently won't trigger the file-specific nudge — falls back to the generic hint. Acceptable and noted in the task; not in user-facing docs, but the generic hint still fires. | `[ -f "~/anything" ]` → false even if `$HOME/anything` exists. |

## Clean checks (verified, no issue)

- **Check 1 — emit_error parent scope (q:172-194).** `CTX="$(cmd)" || emit_error …`
  runs `emit_error` in the **parent** shell; its `exit` propagates and stops q
  (verified: `X="$(false)" || boom` → boom's `exit 12` ends the script, no line
  after reached). The `||` is load-bearing: a bare `X="$(false)"` under `set -e`
  aborts with default RC=1, bypassing the structured frame. The pdf branch (176-179)
  and textutil branch (180-182) both guard correctly. Comment at 163-167 is accurate.
- **Check 2 — set -e during extraction.** pdftotext/textutil failures are caught by
  `|| emit_error` (so a nonzero exit becomes a structured error, not a bare abort).
  The post-`case` `ctx_empty` guard (192) ordering is fine vs `set -e` (it's a simple
  `if`, no pipe). `head`/`wc` are not used in the new code.
- **Check 4 — `--json` purity.** `lm models --json` (110-114) does **not** divide
  size, tolerates null size (passes through as JSON `null`), and `--argjson resident
  "${resident:-[]}"` / `--argjson tags "$(… || echo '[]')"` give valid-JSON fallbacks
  when `/api/ps` is empty (`resident='[]'`) or tags is junk. Verified end-to-end on a
  payload with a null-size model + empty ps → valid JSON, exit 0.
- **Check 5 — machine-mode purity.** All new error paths (`ctx_unsupported`,
  `ctx_binary`, `ctx_empty`, `ctx_required`) route through MODE-aware `emit_error`
  (q:145-152), emitting one JSON object/line in json/stream mode. All extractor
  **stderr is `2>/dev/null`**; extractor **stdout is captured into `$CTX`**, never
  leaked to q's stdout. The `ctx_binary` message embeds `$(file -b …)` but jq `--arg`
  escapes it, so JSON stays well-formed.
- **Check 6 — 400k cap.** The cap (q:202) and MAX_CTX truncation (203) apply **after**
  truncation guards CTX size before it reaches the model. NOTE (not a bug, but worth
  flagging): extraction loads the **full** document into the `$CTX` bash variable
  *before* the 400k check — a 500-page PDF is fully `pdftotext`'d into memory, then
  refused. The cap protects the model/window, not q's own memory. Low risk for a local
  CLI, but the cap is a refusal-after-the-fact, not a streaming guard.
- **Check 7 — comments.** Strong, human-first WHY comments (q:163-167 emit_error
  rationale; q:184-186 `file --mime-encoding` vs NUL-sniff with the empirical "~46%
  have no NUL" justification; q:217-220 path-in-prompt trap; lm:102-103). No `[claude@]`
  tags, no Phase/Tier/Track plan refs, no archeology. The "200 random bytes slipped
  through in testing" note leans slightly anecdotal but legitimately justifies a
  non-obvious tool choice — acceptable.
- **Docs.** `q-spec.md` and `STATE.md` additions accurately describe the implemented
  behavior (intents, exit codes, extraction-by-type, no-cloud). Consistent with code.

## Suggested fixes (smallest-first)

1. `bin/lm:118` — `(.size // 0)` to defend the GB divide (kills the HIGH finding).
2. `bin/lm:117` — wrap the human pipe with a fallback or `set +e` around it, OR add
   `-f`/validate `$tags` is JSON before the pipe (kills the MEDIUM finding).
3. `bin/q` — move/`add` the `[ -s ]` empty-file check ahead of the binary sniff so a
   0-byte file reads as empty/required, not binary (LOW-MED).
4. `bin/q:189` — add `|| emit_error ctx_unreadable …` to the catch-all `cat` for
   guard-pattern consistency (LOW).
