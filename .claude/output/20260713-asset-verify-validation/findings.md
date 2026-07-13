# asset-verify — adversarial validation

<!-- sessions: vis-ab-3c@2026-07-13 -->

**Under test:** lib/asset-verify.py + battery F11. **Validator:** sonnet, mutation-testing
mandated; findings returned inline, persisted by the parent.

## VERDICT: ISSUES-FOUND (2 blockers, both fixed)

### BLOCKER 1 — truncated input tracebacks instead of the documented exit-2 error

PIL's `Image.open()` is lazy: it parses the header only. The real decode fired later,
unguarded, inside `flatten()` — so a truncated PNG (interrupted build, disk-full partial
write, flaky fetch: precisely this tool's job) exited 1 with an empty stdout and a raw
`OSError: image file is truncated`. RC=1 is indistinguishable from "a rung was flagged
soft," and no JSON reaches the caller at all.

**Fixed:** `img.load()` inside the existing try, forcing the decode into the structured
`die()` path. Guarded by F11b (truncated file → exit 2 + parseable `ok:false` + fix).

### BLOCKER 2 — F11's fixture was structurally blind to compositing

The fixture was `alpha=255` everywhere. Under full opacity, composite-on-white and a
bare alpha-drop produce byte-identical RGB — so the validator **deleted the compositing
step entirely and the battery stayed 33/33 green**. The guard could not see the defect
class it exists to catch (blind by construction, not by luck). Compositing itself was
confirmed correct against a separate alpha-varying fixture.

**Fixed:** the F11 source now carries real alpha variation (transparent field, opaque
mark) and F11b flags an alpha-faded rung. Re-running the validator's exact mutation now
goes **red**.

## What held (validator coverage)

Discrimination across 12 cases: gaussian blur, JPEG q10, recolor, 1px translation,
upscale-from-16px, wholly different image all flagged; LANCZOS, bicubic, JPEG q95,
palette-mode PNG all pass. No false positives or negatives. Compositing honesty: garbage
RGB under alpha=0 correctly ignored; 60%-opacity fade, half-transparent wash, and
premultiplied-under-straight all flagged. Malformed input (nonexistent, text file,
zero-byte, SVG, directory, no args) → clean exit-2 errors. Floors sane at 8/16/512px on a
detailed source. Aspect boundary 1.02 inclusive (intentional).

Net: the comparison logic was sound; both blockers lived in the **failure paths** — one
in the tool, one in its own guard.
