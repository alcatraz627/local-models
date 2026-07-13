# findings-gate + review flag fix — adversarial validation

<!-- sessions: vis-ab-3c@2026-07-13 -->

**Under test:** lib/findings-gate.py, bin/review's `--json`/`--findings` clobber fix,
verify.sh wiring. **Validator:** sonnet, isolated worktree, mutation-testing mandated;
findings returned inline, persisted by the parent.

## VERDICT: ISSUES-FOUND

### CRITICAL — `--root` containment was not enforced (fixed, commit after this report)

`os.path.join(root, "/etc/hosts")` discards root entirely (Python semantics), and
nothing normalized `../` traversal. Both repros returned `{"ok": true, "kept": 1}` —
a finding pointing at any real file anywhere on disk validated as evidence, which is
precisely what the module exists to prevent.

```
$ python3 lib/findings-gate.py --root /tmp/gate-attack/root <<< '{"findings":[{"file":"/etc/hosts","line":1,...}]}'
{"ok": true, "kept": 1, "dropped": []}        # before
{"ok": false, "kept": 0, "why": ["file escapes --root: /etc/hosts"]}   # after
```

### HIGH — line bounds check was fail-OPEN (fixed)

`if isinstance(line, int) and line > 0:` meant any *other* type silently skipped the
bounds check: `"12"`, `99.0`, `Infinity`, `0`, `-5` all kept unconditionally against a
2-line file. Now a present `line` must be a positive int within bounds or the finding
is dropped.

### PASS — exit-code contract (all edges), the review flag-order fix (all four orders
traced via `bash -x`), verify.sh wiring (mutation flips suite exit 0→1), bare-python3
compat (3.14.5).

### PASS-WITH-NOTES — self-test quality

The shipped 3-case self-test never exercised a non-int `line`, which is *why* the HIGH
shipped. Now 13 cases covering every escape the validator found (absolute path,
traversal, string/float/inf/zero/negative line, empty + non-string file, plus the two
legitimate keeps).

### Context note (accepted, not a defect)

findings-gate had zero production callsites at review time — the bugs were latent, not
live-exploited. The /bloop Phase 4.0 pre-gate is its first consumer; it now consumes a
fail-closed gate.

## Resolution

Fixed in the follow-up commit: realpath + commonpath containment, fail-closed line
validation, self-test 3 → 13 cases. Both attack repros re-run and confirmed closed;
a legitimate in-bounds finding still passes.
