# Vision batch report — `see --ui` vs `lm gemini` vision on 15 real screenshots

<!-- sessions: vision-see-4a@2026-07-08 -->

**TL;DR:** both lanes completed 15/15 with zero failures. Gemini vision is the
verbatim-fidelity winner (95% exact-token recall vs 77%); the local `see --ui`
is ~2× faster wall-clock, $0, private, and its structure/hierarchy reads are
now trustworthy after this session's fixes. Local misses are near-miss
substitutions ("Dropzone"→"Dropdown"), not inventions — the dangerous class
(fabricated elements) did not appear in any graded sample.

## What ran

- **Images:** the 15 most recent `~/Pictures/Screenshots` (2026-07-06 → 07-08),
  copied to `imgs/s01..s15.png` (`manifest.tsv` maps back to originals).
  Spread: two full-screen captures (3024×1964, 3440×1440), mid-size app
  windows, small panels, and tiny widget crops down to 151×114.
- **Local lane:** `see <img> --ui` — the new UI-inventory mode, auto-routed to
  `gemma4:26b` under a `warm on big 30m` lease (one load for the whole batch).
- **Gemini lane:** `lm gemini "<same rubric> @imgs/sNN.png"` — image attach via
  `@path` in the prompt, verified working through the wrapper (plan mode reads
  files fine). Model: pinned gemini-3.5-flash.
- **Grading:** 5 diverse samples (s02 retina full-screen browser, s04 dark
  chip-heavy app, s08 light dashboard with cluster viz, s09 modal, s12 tiny
  widget crop) ground-truthed by native Claude vision, scored on exact-token
  recall + fabrication. The other 10 ran clean but were not ground-truthed —
  the numbers below are for the graded 5 only.

## Numbers

| | see --ui (local) | lm gemini |
|---|---|---|
| Completion | 15/15 | 15/15 |
| Wall-clock, 15 images | 257s (mean 17s, min 8s, max 31s) | 503s (mean 34s, min 15s, max 68s) |
| Output size | 1.1–6.4 KB | 1.5–12.2 KB |
| Exact-token recall (43 tokens, 5 samples) | 33/43 (77%) | 41/43 (95%) |
| Fabricated elements in graded samples | 0 | 0 |
| Wrong-word substitutions | 2 ("Dropzone"→"Dropdown", "Branching"→"Printing") + spelling slips ("Aakarsh"→"Aakash", "(0)"→"[0]") | 0 observed |
| Cost | $0, image never leaves the box | gemini API budget (abundant), image uploaded |

Both lanes missed the same two tokens: menu-bar widget values (77%, 1.8MB) on
the full-screen s02 — tiny top-strip content gets deprioritized when the frame
is dominated by a window. The tiny-crop sample (s12) was read perfectly by
both, which is the practical answer for menu-bar/widget questions: crop first.

## Per-sample notes (graded set)

- **s02** (3024×1964 browser, component gallery): gemini near-perfect including
  small-text sidebar items and table cells; see got all structure + groups
  right, fumbled 4 small-text tokens. Neither read the macOS menu-bar widgets.
- **s04** (dark app, chip rows): tie. Both got every token and every
  selected-chip state right; gemini added a correct emphasis-system analysis
  (solid orange = active, grey border = inactive).
- **s08** (light dashboard, 30 cluster bubbles + rows): see transcribed bubble
  counts (×52/×28/×22…) and their truncated captions near-verbatim — its best
  read — but skipped the search input, footer buttons, and build hash, all of
  which gemini caught. Both correctly called the light theme (a June-audit
  failure mode, now gone on the big model).
- **s09** (modal): both essentially perfect.
- **s12** (151×114 crop): both perfect — status dots with colors, button, states.

## Knobs tuned this session (all shipped in `bin/see` / `config.sh`)

1. **Rubric moved from system prompt to user message.** gemma has no true
   system role (ollama folds system into the first user turn), and under that
   fold gemma4:26b deterministically stopped ~200 tokens in — reproduced twice,
   `done_reason:stop` at the same character. As a user message the same rubric
   runs to completion. This was the single biggest unlock.
2. **`--ui` auto-routes to the big tier** (`UI_VISION_MODEL=$BIG_MODEL`,
   `-m` still wins). Measured, not assumed: on the i-dream ground-truth image,
   gemma4:26b read the actually-selected nav item, region proportions, and
   per-element states that minicpm-v got wrong twice, while matching its
   verbatim recall. minicpm-v stays the default for plain `see` (OCR-strong,
   3× smaller load).
3. **`num_ctx: 8192, num_predict: -1`** on see's request — image tiles + the
   sectioned rubric overflow some models' 4096 default and truncate silently.
4. **`keep_alive` now honors residency** (the `_lib.sh` contract q already
   followed): resident → -1, cold → 0. Before this, every `see` call evicted
   an active `warm on` lease — a 15-image batch would have reloaded 17GB
   fifteen times. With the lease: one load, 8-31s per read.

## Knobs evaluated and deliberately NOT touched

- **Temperature > 0** — determinism is worth more than variety here.
- **A `--thorough` two-pass mode** — the 06-25 skeptic review killed it;
  calling `see` twice (or escalating to native/gemini) is strictly simpler.
- **Image pre-downscaling** — gemma handled 3440×1440 fine; ollama tiles
  internally. No evidence a knob is needed.
- **Spacing/pixel estimates in the rubric (the L3 remainder)** — fabrication
  bait per the June audit; palette stays coarse-and-flagged instead.
- **Per-lens registry** — still dead per the skeptic verdict; `--ui` is the
  one sanctioned specialized mode and one flag is holding well.

## How to pick a lane (recommendation)

| Situation | Lane |
|---|---|
| In-conversation read where exact strings are load-bearing | **Native Claude vision** (it graded both other lanes here) |
| Standalone/batch UI inventory, scripting, privacy, $0 | **`see <img> --ui`** — structure is trustworthy; verify exact strings before citing them |
| Dense small text where verbatim fidelity is the point, or huge context alongside the image | **`lm gemini "… @img.png"`** — best OCR of the three, but slowest wall-clock (CLI overhead) and the image leaves the box |
| Menu-bar / widget questions | **Crop the strip first**, then any lane — tiny focused crops read dramatically better than full-screen frames |

gcc's `rules/model-tier-routing.md` already encodes exactly this split
("vision → complementary lanes: `see` free-first for standalone reads, native
fine in-conversation, gemini abundant") — this batch confirms it empirically.

## Files

- `imgs/` + `manifest.tsv` — the batch inputs
- `see/sNN.md`, `gemini/sNN.md` — all 30 raw reads (`.err` files empty)
- `rubric.txt` — the shared prompt both lanes received
- `imgs/`, `see/`, `gemini/` are local-only (gitignored): the repo is public and
  they carry personal screen content verbatim
