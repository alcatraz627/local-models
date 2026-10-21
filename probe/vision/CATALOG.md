# Vision model comparison: test case catalog

<!-- sessions: vision-cases@2026-10-22 -->

This catalog is for comparing local vision models (minicpm-v4.6 on Ollama, gemma4:26b on Ollama, Qwen3-VL-8B on MLX, plus candidates) on the jobs `see` does every day. It holds 42 cases; 20 are marked core and form the first build. Every case has truth computed from the generator's own parameters or from an existing repo fixture, so no answer depends on a person's or a model's guess. Machine-readable copy: `cases.json` in this folder.

The design goal is discrimination. A case that every model passes, or that every model fails for transport reasons, tells us nothing. Each case names the failure a small VLM is expected to show, so a pass or fail is evidence of a specific capability.

## 1. How a case is scored (applies to every case)

Earlier keyword scorers failed correct answers on wording. These rules score meaning instead.

### 1.1 The answer contract

Every question prompt ends with one fixed sentence:

```
End your reply with exactly one line of the form: ANSWER: <...>
```

The scorer reads the **last** line matching `^\W*ANSWER\W*[:：]\s*(.+)$` (case-insensitive, markdown stars and backticks stripped). Prose above it is ignored for scoring but kept for review.

If no ANSWER line exists, the scorer falls back to the whole reply and accepts it only when exactly one candidate of the right type appears (one integer, one color name, one cell id). Two or more distinct candidates means `format_fail`. The report shows `pass`, `fail` and `format_fail` as separate columns, so a model that knows the answer but breaks the contract is visible as such and not counted as blind.

### 1.2 Shared normalisers (one module, `score_lib.py`)

| Helper | What it does |
|---|---|
| `norm_str(s)` | NFKC, uppercase, collapse whitespace, strip wrapping quotes, backticks and trailing punctuation. Used for exact text truths. |
| `to_int(s)` | Digits (`1,240` → 1240) or number words zero to fifty. Returns the set of distinct integers found. |
| `to_num(s)` | Same for decimals, with currency symbols and units stripped. |
| `color_of(s)` | Maps words to canonical colors through a synonym table: red {red, crimson, scarlet}, green {green, lime green, emerald}, blue {blue, royal blue, azure, cobalt}, yellow {yellow, gold, golden}, orange {orange, amber}, purple {purple, violet}, gray {gray, grey, silver}, black, white. Generators only use saturated canonical RGB so the table stays small. |
| `pos_of(s)` | Maps {upper left, top left, top-left, NW} → `top-left`, and so on for the nine positions. |
| `cell_of(s)` | Parses `r3c2`, `row 3 column 2`, `(3,2)`, `third row, second column` → (3,2), 1-based. |
| `mentions(text, term)` | Negation-aware: a term inside a 4-token window after no, not, without, none, absent, never does not count as a mention. Used only by must-NOT lists. |
| `absent_answer(s)` | True when the ANSWER is one of NONE, ABSENT, N/A, NO SUCH, NOT PRESENT, NOTHING, or a sentence of the form "there is no …", AND the answer contains no number and no quoted string. |

### 1.3 Must-NOT lists carry a positive partner

A prohibition alone passes an empty or truncated reply. Every hallucination trap therefore also has a positive assertion (an ANSWER line that equals NONE or ABSENT, or a required correct fact), so a blank output scores `format_fail`, never `pass`.

### 1.4 Seeds and the priors problem

Every generator takes a `seed`. Run 3 seeds per case and report the pass rate. Seeds vary the thing a model could guess from a prior: which side the circle is on, which tab is selected, which grid cell differs, where the maximum bar sits. A model that answers "left" every time scores about 50 percent on S01, which is the signal.

### 1.5 Script baselines and routing

Cases tagged `script_beats_model` carry a deterministic baseline (connected-component count, pixel mean per cell, `see diff --no-read` E5 top cell, `see --ocr`). The report prints the baseline's answer next to the models'. When the script is right and every model is wrong, that is a routing finding: `see` should call the script for that job, and the case documents why.

### 1.6 How modes map to commands

| Mode tag | Command | Varies by model? |
|---|---|---|
| `read` | `see IMG --json -m M` (default structured read prompt), score `.text` | yes |
| `qa` | `see IMG "PROMPT" --json -m M`, score `.text` | yes |
| `ui-json` | `see IMG --ui --json -m M`, score `.data` | yes. `--ui` defaults to MLX Qwen3-VL; pass `-m` explicitly for every model |
| `crop` / `region` | `see IMG --crop WxH+X+Y "PROMPT" --json -m M` or `--region NAME` | yes. Each crop case runs the full image too, so the lift is measured |
| `ocr` | `see IMG --ocr --json` (Apple Vision) | **no**. These cases rank the OCR lane against model reads, not models against each other |
| `diff` | `see diff A B "FOCUS" --json -m M`, score `.text` | yes, Ollama models only. `bin/see` refuses MLX in diff mode (`probe/candidates/GAPS.md`), so Qwen3-VL cannot run these until that is wired |
| `odd` | `see IMG "PROMPT" --json -m M` (proposed new lane; today it is a `qa` call with a fixed prompt shape) | yes |

Fonts used below all exist on this machine: `/System/Library/Fonts/Supplemental/Arial.ttf`, `/System/Library/Fonts/Supplemental/Arial Bold.ttf`, `/System/Library/Fonts/Menlo.ttc`, `/System/Library/Fonts/Supplemental/Courier New.ttf`, `/System/Library/Fonts/Supplemental/Verdana.ttf`. "Arial N" below means Arial at N px.

## 2. Core 20 at a glance

| id | mode | capability | diff | why it discriminates |
|---|---|---|---|---|
| C01 | qa | counting | easy | floor: a model that fails 7 big dots is out |
| C02 | qa | counting, script-beats-model | hard | 23 small dots plus hollow decoys; models drift, script is exact |
| C03 | qa | counting + color binding | med | count one color among three |
| T01 | qa | small text | med | 14 px mixed-case ID, character-exact |
| T03 | read | reading, no language prior | med | pseudo-words punish autocorrect |
| T05 | qa | low-contrast text | hard | faint target, loud decoy |
| S02 | qa | spatial relations | med | nearest labeled box to a marker |
| K03 | qa | color + text binding | med | Stroop words: ink color vs word meaning |
| G01 | qa | chart values | med | read a bar value against gridlines, tolerance 3 |
| B01 | qa | table cells | med | row lookup by key, column by header |
| U01 | qa | UI state checked | med | which checkboxes are ticked |
| U02 | qa | UI state disabled | med | grayed-out button among live ones |
| U06 | ui-json | dense layout inventory | hard | recall and precision of 12 known elements |
| R01 | crop | crop lift, small text | hard | same question, full frame vs crop |
| D01 | diff | hallucination trap | easy | identical pair must report NONE |
| D02 | diff | diff localization | med | which grid cell changed |
| D03 | diff | diff text | med | old and new value of one changed line |
| H01 | qa | hallucination trap | easy | blank image, "any text?" must be NONE |
| H02 | qa | hallucination trap | med | question about a series that is not there |
| O04 | odd | odd-one-out | hard | the real Affinity rug, motif 9 |

O01 (labeled odd-one-out floor) and T04 (rotated text) are the first two to promote if a core case proves non-discriminating after the first run.

## 3. The catalog

Each case lists: tags, generator sketch, exact prompt, truth, scoring pseudo-code, and the failure a small VLM is expected to show. `CONTRACT` stands for the answer-contract sentence in 1.1.

### 3.1 Counting

**C01 · count-big-dots** · qa · counting · easy · **core**
- Generator: 640x400 white canvas. N filled circles, r=22, color (15,23,42). Centers by seeded rejection sampling inside [30,610]x[30,370] with minimum center distance 2r+12. N per seed from {5,7,9}.
- Prompt: `How many filled circles are in this image? CONTRACT ANSWER: <integer>`
- Truth: `{"count": N}`
- Score: `ints = to_int(answer); pass = ints == {N}`
- Failure mode: off-by-one on 9; some small models round to "several".

**C02 · count-small-dots-with-decoys** · qa · counting · hard · **core** · script_beats_model
- Generator: 800x600 white. 23 filled circles r=7 color (30,30,30), plus 4 hollow rings r=7 width 2 same color, min distance 22 px, seeded positions.
- Prompt: `Count only the FILLED dots. Hollow rings do not count. CONTRACT ANSWER: <integer>`
- Truth: `{"count": 23, "decoys": 4}`
- Score: `pass = to_int(answer) == {23}`; also record `abs_err = |n-23|` and `decoy_counted = n == 27`.
- Baseline: threshold to mask, connected components, keep components whose fill ratio (pixels / bbox area) > 0.6. Must return 23.
- Failure mode: estimates near 20 or 25; counts decoys. Expected result is the script winning, which justifies routing counts above ~12 to a script.

**C03 · count-one-color** · qa · counting, color · med · **core**
- Generator: 720x480 white. 6 red (220,38,38), 4 blue (37,99,235), 5 green (22,163,74) squares of 36 px, seeded positions, min gap 14 px. Per seed rotate which color is asked and the counts among {3,4,5,6}.
- Prompt: `How many BLUE squares are there? CONTRACT ANSWER: <integer>`
- Truth: `{"color": "blue", "count": 4, "total": 15}`
- Score: `pass = to_int(answer) == {4}`; flag `answered_total` if 15.
- Failure mode: counts all squares, or the most salient color.

**C04 · count-table-rows** · qa · counting, table · easy
- Generator: the B01 table with 7 data rows plus a header.
- Prompt: `How many data rows does the table have, not counting the header row? CONTRACT ANSWER: <integer>`
- Truth: `{"rows": 7}`
- Score: `pass = to_int(answer) == {7}`; flag 8 as `counted_header`.
- Failure mode: includes the header.

### 3.2 Reading text

**T01 · small-id** · qa · small text · med · **core**
- Generator: 900x220 white. Heading "Release notes" Arial Bold 32 at (40,24). Body line "Build ID: K7Q-48XZ-2093" Menlo 14 at (40,120). A decoy line "Ref: K7Q-48XZ" Menlo 14 at (40,160). Seeds draw the ID from `[A-Z0-9]{3}-[A-Z0-9]{4}-[0-9]{4}` excluding O, I, L.
- Prompt: `What is the full Build ID? CONTRACT ANSWER: <id>`
- Truth: `{"text": "K7Q-48XZ-2093"}`
- Score: `pass = norm_str(answer).replace(" ","") == truth`; record Levenshtein distance for the report.
- Failure mode: one swapped character, or returns the shorter decoy.

**T02 · tiny-text-ladder** · qa · small text · hard
- Generator: 1200x300 white, one string "Invoice 55-0193 due 14 Mar" rendered at Arial 9. Variants at 7 and 12 px as separate sub-cases so the report shows each model's legibility floor.
- Prompt: `Transcribe the line of text exactly. CONTRACT ANSWER: <text>`
- Truth: `{"text": "Invoice 55-0193 due 14 Mar", "px": 9}`
- Score: `pass = norm_str(answer) == norm_str(truth)`; report the smallest px that passes per model.
- Failure mode: invents a plausible invoice number.

**T03 · pseudo-words-read** · read · reading, no language prior · med · **core**
- Generator: 800x260 white. Four lines Arial 26 at y=30,85,140,195, x=40: "vorplex trindle", "quaso maffin", "glent 4417 drubb", "ostrawe nym". Seeds pick from a fixed pseudo-word list.
- Prompt: default structured read (no question).
- Truth: `{"tokens": ["VORPLEX","TRINDLE","QUASO","MAFFIN","GLENT","4417","DRUBB","OSTRAWE","NYM"], "autocorrect_traps": {"MAFFIN":"MUFFIN","GLENT":"GLINT","NYM":"NYMPH"}}`
- Score: `toks = set(re.findall(r"[A-Z0-9]+", norm_str(text))); recall = |truth ∩ toks| / 9; pass = recall == 1.0`; flag every autocorrect trap word that appears.
- Failure mode: the language prior turns "maffin" into "muffin". This is the cleanest test that a model reads glyphs instead of predicting words.

**T04 · rotated-text** · qa · rotated text · hard
- Generator: 600x600 white. "ORBIT 7731" Arial Bold 34 drawn on a transparent layer, rotated 90 degrees, pasted at the left edge; a second string "LUMEN 2208" rotated 30 degrees in the center. Seeds vary the strings.
- Prompt: `What does the vertical text along the left edge say? CONTRACT ANSWER: <text>`
- Truth: `{"text": "ORBIT 7731", "decoy": "LUMEN 2208"}`
- Score: `pass = norm_str(answer) == "ORBIT 7731"`; flag `answered_decoy`.
- Failure mode: reads the reversed string or returns the 30-degree decoy.

**T05 · low-contrast-target** · qa · low-contrast text · hard · **core**
- Generator: 800x300 background (210,210,210). Target "delta 5508" Arial 30 in (196,196,196) at (60,180). Decoy "alpha 1234" Arial 30 in (20,20,20) at (60,60).
- Prompt: `There are two lines of text. What does the faint, light-gray line say? CONTRACT ANSWER: <text>`
- Truth: `{"text": "DELTA 5508", "decoy": "ALPHA 1234"}`
- Score: `pass = norm_str(answer) == "DELTA 5508"`; flag decoy.
- Failure mode: cannot see the target, returns the decoy or invents.

**T06 · paragraph-ocr-vs-model** · ocr + read · reading, dense text · med · script_beats_model
- Generator: 900x300 white, Verdana 16, three fixed lines: "Shipment 7 of 12 left Rotterdam on 03/09.", "Net weight 1,482.6 kg; tare 212 kg.", "Contact: ops-desk@example.test, ext. 4471."
- Prompt: model lane `Transcribe all text exactly, line by line. CONTRACT ANSWER: DONE`; OCR lane `see IMG --ocr --json`.
- Truth: `{"lines": [the three strings]}`
- Score: `cer = levenshtein(norm(joined_reply_lines), norm(joined_truth)) / len(truth)`; `pass = cer <= 0.01`. OCR lane expected cer 0.
- Failure mode: model drops punctuation, rounds 1,482.6. The case exists to document that exact text routes to `--ocr`.

### 3.3 Spatial relations

**S01 · left-of** · qa · spatial · easy
- Generator: 600x400 white. Red circle r=50 and blue square 100 px, centers at (150,200) and (450,200); the seed decides which is left.
- Prompt: `Which shape is further left: the circle or the square? CONTRACT ANSWER: circle or square`
- Truth: `{"left": "circle"}` per seed.
- Score: `pass = answer contains exactly one of {circle, square} and it equals truth`
- Failure mode: position bias. Run 4 seeds (2 each way); a model at 50 percent is guessing.

**S02 · nearest-labeled-box** · qa · spatial · med · **core**
- Generator: 800x500 white. Five 70x50 outlined boxes labeled A to E (Arial Bold 26 centered) at seeded positions; one green 5-point star r=18. Truth is the box with minimum center distance to the star, accepted only if the runner-up is at least 60 px farther (regenerate otherwise).
- Prompt: `Which lettered box is closest to the green star? CONTRACT ANSWER: <letter>`
- Truth: `{"letter": "C", "margin_px": >=60}`
- Score: `letters = set(re.findall(r"\b[A-E]\b", norm_str(answer))); pass = letters == {truth}`
- Failure mode: picks the box nearest in reading order or the largest letter.

**S03 · quadrant** · qa · spatial · easy
- Generator: 600x600 white, one yellow triangle (side 80) centered in one of 9 positions (thirds grid), seeded.
- Prompt: `Where in the image is the triangle? Use one of: top-left, top, top-right, left, center, right, bottom-left, bottom, bottom-right. CONTRACT ANSWER: <position>`
- Truth: `{"position": "bottom-right"}`
- Score: `pass = pos_of(answer) == truth`
- Failure mode: left/right mirror confusion.

**S04 · color-order** · qa · spatial, color · med
- Generator: 900x200 white. Five circles r=40 at x=110,280,450,620,790, y=100, colors a seeded permutation of red, blue, green, yellow, purple.
- Prompt: `List the circle colors from left to right. CONTRACT ANSWER: color, color, color, color, color`
- Truth: `{"order": ["green","red","purple","blue","yellow"]}`
- Score: `seq = [color_of(t) for t in answer.split(",")]; pass = seq == truth`
- Failure mode: right order of the first three, then drift; or reading-order of names from training.

### 3.4 Color

**K03 · stroop-ink** · qa · color, text binding · med · **core**
- Generator: 700x300 white, Arial Bold 48. "APPLE" in yellow (234,179,8) at (40,40), "LEMON" in red (220,38,38) at (40,120), "GRAPE" in green (22,163,74) at (40,200). Seeds permute ink colors so ink never equals the word's usual color.
- Prompt: `What color is the ink of the word LEMON? CONTRACT ANSWER: <color>`
- Truth: `{"word": "LEMON", "ink": "red", "prior": "yellow"}`
- Score: `pass = {color_of(answer)} == {"red"}`; flag `answered_prior` if yellow.
- Failure mode: answers the semantic prior. Strong discriminator between models that bind attributes and models that describe.

### 3.5 Charts

**G01 · bar-value** · qa · chart values · med · **core**
- Generator: 640x420 white. Y axis 0 to 80 with gridlines and tick labels every 10 (Arial 14) at x=60; plot area y=360 (value 0) to y=40 (value 80), so 4 px per unit. Five bars width 60 at x=100,200,300,400,500, labels Mon to Fri below. Values per seed, e.g. [23,47,35,62,18], all distinct by at least 8. No value labels on bars.
- Prompt: `What is Thursday's value? CONTRACT ANSWER: <number>`
- Truth: `{"label": "Thu", "value": 62, "tol": 3}`
- Score: `n = to_num(answer); pass = len(n)==1 and abs(n[0]-62) <= 3`
- Failure mode: reads the nearest gridline (60) is fine; reads the wrong bar or the y label is not.

**G03 · line-crossing** · qa · chart values · hard
- Generator: 720x420 white. Two polylines over x labels Jan to Aug: series A blue solid, B orange dashed, legend top-right "A" and "B". Values seeded so B crosses above A exactly once, at a known month, with a gap of at least 6 units on each side of the crossing.
- Prompt: `In which month does series B first rise above series A? CONTRACT ANSWER: <month>`
- Truth: `{"month": "May"}`
- Score: `pass = month_of(answer) == truth`
- Failure mode: picks a month where the lines are close but not crossed.

**G04 · existing-f6-chart** · qa · chart, reading · med
- Generator: existing `probe/fixtures/f6-a.png` (bars [80,120,60,100], labels Q1 to Q4, from `make-fixtures.py`).
- Prompt: `Which quarter has the tallest bar, and which the shortest? CONTRACT ANSWER: tallest=<label>, shortest=<label>`
- Truth: `{"tallest": "Q2", "shortest": "Q3"}`
- Score: parse `tallest=(Q\d)` and `shortest=(Q\d)`; both must match.
- Failure mode: swaps Q2 and Q4.

### 3.6 Tables

**B01 · table-lookup** · qa · table cells · med · **core**
- Generator: 900x420 white, Arial 18, 1 px gray grid. Header Name, Region, Units, Price. Seven rows of synthetic data: names from a fixed list (Halvorsen, Okafor, Brandt, Ivanova, Mendes, Tanaka, Novak), regions from {North, South, East, West}, Units distinct integers 10 to 99, Price $x.xx. Column x at 40, 280, 480, 640; row pitch 46.
- Prompt: `In the row whose Name is Halvorsen, what is the Units value? CONTRACT ANSWER: <integer>`
- Truth: `{"row": "Halvorsen", "col": "Units", "value": 57}`
- Score: `pass = to_int(answer) == {57}`; flag `row_off_by_one` if the answer equals the Units of the row above or below.
- Failure mode: row misalignment, the classic table failure.

**B02 · dense-table-crop** · qa + crop · table cells, dense layout · hard
- Generator: 1400x900 white, Arial 11, 15 rows x 6 columns (ID, Owner, Status, Qty, Updated, Note). IDs "R-0401" to "R-0415"; Status from {OPEN, HOLD, DONE, VOID}. Target row R-0412 Status HOLD; neighbours R-0411 and R-0413 have OPEN and DONE.
- Prompt: `What is the Status for ID R-0412? CONTRACT ANSWER: <status>`
- Truth: `{"value": "HOLD", "crop": "700x300+0+560"}`
- Score: `pass = norm_str(answer) == "HOLD"`. Run full and cropped; report both.
- Failure mode: neighbour-row answer at full size, correct after crop.

### 3.7 UI state and layout

**U01 · checkbox-states** · qa · UI state (checked) · med · **core**
- Generator: 600x360 white. Five rows at y=40+60i: an 18 px square outline (2 px, gray) at x=40 and a label Arial 20 at x=74. Checked boxes get a blue (37,99,235) fill and a white checkmark polyline. Labels: Email alerts, Dark mode, Auto-save, Beta features, Analytics. Seed picks 2 checked.
- Prompt: `Which options are checked? CONTRACT ANSWER: comma-separated labels`
- Truth: `{"checked": ["Email alerts","Dark mode"]}`
- Score: `got = {norm_str(t) for t in answer.split(",")}; pass = got == {norm_str(x) for x in truth}`
- Failure mode: lists all options, or marks the first ones checked by default.

**U02 · disabled-button** · qa · UI state (disabled) · med · **core**
- Generator: 700x200 white. Three 160x48 rounded buttons (radius 8) at x=40,240,440, y=76, labels Save, Export, Delete Arial 20. Enabled: fill (37,99,235), white text. Disabled: fill (229,231,235), text (156,163,175). Seed picks which one is disabled.
- Prompt: `Which button is disabled? CONTRACT ANSWER: <label>`
- Truth: `{"disabled": "Export"}`
- Score: `pass = norm_str(answer) == "EXPORT"`
- Failure mode: names Delete (destructive prior) or says none.

**U03 · selected-tab** · qa · UI state (selected) · easy
- Generator: 900x120 white. Tabs Overview, Logs, Metrics, Alerts, Settings in Arial 20 at x=30+170i, y=40. Selected tab: Arial Bold, blue text, and a 3 px blue underline at y=80 under that tab only. Seeded.
- Prompt: `Which tab is selected? CONTRACT ANSWER: <tab>`
- Truth: `{"selected": "Logs"}`
- Score: `pass = norm_str(answer) == "LOGS"`
- Failure mode: answers the first tab.

**U04 · toggle-states-json** · ui-json · UI state (on/off) · med
- Generator: 600x320 white. Four rows: label at x=40 (Wi-Fi, Bluetooth, AirDrop, Hotspot), toggle track 52x30 at x=480. On: green (52,199,89) track, white knob on the right. Off: gray (209,213,219) track, knob on the left. Seed picks 2 on.
- Prompt: `--ui --json` default.
- Truth: `{"on": ["Wi-Fi","AirDrop"], "off": ["Bluetooth","Hotspot"]}`
- Score: for each label, find elements in `.data.regions[*].elements` whose `norm_str(text)` contains the label; read `state`. `on` if state matches /on|enabled|checked|active|true/, `off` if /off|disabled|unchecked|inactive|false/. Pass when all four labels map to the right side. A missing label is a fail.
- Failure mode: reports all toggles with no state, or all "on".

**U06 · settings-inventory** · ui-json · dense layout, inventory · hard · **core**
- Generator: 900x640 white settings panel. Title "Account settings" Arial Bold 28. Four labeled empty inputs (label Arial 16 above a 360x36 outlined box): Full name, Email, Company, Phone. Two checkboxes: Send weekly digest (checked), Enable two-factor (unchecked). Three underlined blue links: Privacy policy, Terms, Help center. Three buttons at the bottom: Cancel (outlined), Save changes (blue filled), Delete account (red filled). Coordinates fixed in the generator; total 12 interactive elements.
- Prompt: `--ui --json` default.
- Truth: `{"elements": [{"text":"Full name","type":"input"}, … 12 items], "checked": ["Send weekly digest"]}`
- Score: `got = [e for r in data.regions for e in r.elements]`; match by `norm_str(text)` with exact or containment either way. `recall = matched_truth / 12`, `precision = matched_got / len(got_interactive)` where elements whose text matches the title or a known label-only string are neutral. `type_acc` over matched with type synonyms (input {input, text field, textbox, field}, link {link, hyperlink}, button {button}, checkbox {checkbox, check box}). `pass = recall >= 0.9 and precision >= 0.9 and checked-state right`. Report hallucinated element texts by name.
- Failure mode: invents a Submit button or a search bar; drops the links.

**U07 · badge-count** · qa · small text, UI · med
- Generator: 300x200 white. Bell glyph drawn as a polygon at (120,60), 60 px. Red circle r=13 at its top-right with "12" in white Arial Bold 14. Seeds pick from {3,9,12,27,99+}.
- Prompt: `What number is on the notification badge? CONTRACT ANSWER: <number>`
- Truth: `{"value": "12"}`
- Score: exact `norm_str` (keeps "99+" literal).
- Failure mode: misreads 12 as 2, or describes the icon only.

### 3.8 Crop and region

**R01 · crop-lift-dashboard** · crop · small text, crop lift · hard · **core**
- Generator: 2400x1500 light gray (245,245,247). Grid of 6 rows x 8 cols of white tiles 280x160 at x=20+295c, y=40+240r. Each tile: label Arial 11 at (+12,+12), value Arial 13 at (+12,+40). Labels and values from a seeded synthetic list. Target tile r=5, c=7: "Latency p99" / "412 ms". Neighbour r=5, c=6: "Latency p95" / "388 ms".
- Prompt: `What is the Latency p99 value? CONTRACT ANSWER: <number> ms`
- Runs: (a) full image, (b) `--crop 700x500+1700+1000`, (c) `--region right` (half width).
- Truth: `{"value": 412, "decoy": 388}`
- Score: per run `pass = to_num(answer) == [412]`; report `lift = pass(b) - pass(a)` per model. Flag decoy.
- Failure mode: full-frame read invents or swaps with p95; crop fixes it. This case tells us how much each model depends on crop-first, which drives `see`'s default advice.

### 3.9 Diff (`see diff A B`)

Truth for every diff case comes from the generator or from the vis-battery assertions; the evidence pack (`--no-read`) is the script baseline.

**D01 · identical-pair** · diff · hallucination trap · easy · **core**
- Generator: existing `probe/fixtures/f3-a.png` and `f3-b.png` (byte-identical, from `make-fixtures.py`).
- Focus prompt: `List every visible difference between A and B. If there are none, say so. CONTRACT ANSWER: NONE or ANSWER: <number of differences>`
- Truth: `{"differences": 0}`
- Score: `pass = absent_answer(answer) or to_int(answer) == {0}`. Any claimed difference fails.
- Baseline: battery F3 (all extractors zero).
- Failure mode: invents "slight color shift" to be helpful.

**D02 · grid-cell-changed** · diff · diff localization · med · **core** · script_beats_model
- Generator: two 512x512 white images. 4x4 grid of 128 px cells, each a blue (37,99,235) circle r=36. In B, one seeded cell's circle becomes (220,38,38). Hard variant: (37,140,235), ΔE about 15.
- Focus prompt: `Exactly one cell in this 4x4 grid differs. Which row and column (1-based, row 1 at top)? CONTRACT ANSWER: r<row>c<col>`
- Truth: `{"cell": [3,2]}`
- Score: `pass = cell_of(answer) == (3,2)`
- Baseline: `see diff --no-read --json --grid 4`, top E5 cell must equal the truth.
- Failure mode: right color change, wrong cell (off by one row or mirrored column).

**D03 · receipt-value-changed** · diff · diff text · med · **core**
- Generator: two 420x560 white receipts, Arial 22, lines "Corner Cafe", "Latte 4.50", "Bagel 3.20", "Tax 0.62", "Total 8.32". B changes only the total to "Total 8.82".
- Focus prompt: `One value changed between A and B. Give the old and the new value. CONTRACT ANSWER: <old> -> <new>`
- Truth: `{"old": 8.32, "new": 8.82, "line": "Total"}`
- Score: `m = re.search(r"([\d.]+)\s*(->|→|to)\s*([\d.]+)", answer); pass = m and float(m[1])==8.32 and float(m[3])==8.82`
- Failure mode: reports the change in the wrong line or swaps old and new.

**D04 · chart-two-changes** · diff · diff localization, chart · med
- Generator: existing `f6-a.png` and `f6-b.png`. Truth from `make-fixtures.py`: third label Q3 → Q5, third bar 60 → 140 px.
- Focus prompt: `List each difference as one line starting with "- ". CONTRACT ANSWER: <number of differences>`
- Truth: `{"count": 2, "facts": [{"label_old":"Q3","label_new":"Q5"}, {"bar_index":3, "direction":"taller"}]}`
- Score: `pass = to_int(answer)=={2} and reply mentions Q3 and Q5 together on one bullet and some bullet has (third|3rd|Q3|Q5) with (taller|higher|increased|grew)`. Order of bullets is free.
- Failure mode: finds the bar, misses the relabel, or claims a title change.

**D05 · theme-flip-text-same** · diff · hallucination trap, diff · med
- Generator: existing `f4-a.png` (light) and `f4-b.png` (dark), same text.
- Focus prompt: `Did any TEXT change between A and B (words or numbers, not colors)? CONTRACT ANSWER: YES or NO`
- Truth: `{"text_changed": false, "theme": "light to dark"}`
- Score: `pass = norm_str(answer) == "NO"`
- Baseline: battery F4, E1 text diff empty.
- Failure mode: reports text changes because the colors changed.

**D06 · jpeg-reencode-trap** · diff · hallucination trap · med
- Generator: `f4-a.png` versus the same image saved as JPEG quality 85 (as in battery F3b).
- Focus prompt: same as D01.
- Truth: `{"differences": 0}` (perceptually identical).
- Score: as D01.
- Failure mode: names compression noise as a design change.

**D07 · element-moved** · diff · diff localization · hard · script_beats_model
- Generator: 600x300 white, button 160x48 "Continue" Arial 20 at (220,126) in A, at (244,126) in B (24 px right). Everything else identical.
- Focus prompt: `What changed, and in which direction? CONTRACT ANSWER: <element> moved <direction>`
- Truth: `{"element": "Continue", "direction": "right", "px": 24}`
- Score: `pass = "CONTINUE" in norm_str(answer) and pos_of_dir(answer) == "right"`
- Baseline: E1 `moved` entry with `delta_xy` x=+24.
- Failure mode: says "resized" or gives no direction.

### 3.10 Hallucination traps on single images

**H01 · blank-image** · qa · hallucination trap · easy · **core**
- Generator: 800x600 solid (255,255,255). Sub-case H01b: solid (17,24,39).
- Prompt: `Is there any text in this image? If yes, transcribe it. CONTRACT ANSWER: NONE or the text`
- Truth: `{"text": null}`
- Score: `pass = absent_answer(answer)`. A plain-read companion run (`see IMG`) is scored with `must_not = [button, chart, logo, menu, icon, lorem, title]` via `mentions()` and reported but not gated, since the default read prompt asks for structure.
- Failure mode: describes a "minimal interface" or transcribes imaginary text.

**H02 · absent-series** · qa · hallucination trap · med · **core**
- Generator: the G01 bar chart (one blue series, no legend).
- Prompt: `What value does the orange series show for Wednesday? CONTRACT ANSWER: <number> or ABSENT if there is no such series`
- Truth: `{"absent": true}`
- Score: `pass = absent_answer(answer)`; a number fails even if it equals Wednesday's blue value.
- Failure mode: answers Wednesday's blue value. This is the false-premise compliance test.

**H03 · faint-noise** · qa · hallucination trap · hard
- Generator: 800x600, mid-gray (128,128,128) plus seeded Gaussian noise sigma 6, clipped.
- Prompt: as H01.
- Truth: `{"text": null}`
- Score: as H01.
- Failure mode: pareidolia; reads letters in the noise.

**H04 · absent-button-color** · qa · hallucination trap · med
- Generator: the U02 image (Save, Export, Delete).
- Prompt: `What color is the Cancel button? CONTRACT ANSWER: <color> or ABSENT if there is no Cancel button`
- Truth: `{"absent": true}`
- Score: `pass = absent_answer(answer)`
- Failure mode: answers "gray" because Cancel is usually gray.

### 3.11 Odd-one-out (proposed new lane)

The lane is a fixed prompt shape over a grid of near-identical items. Items are numbered in row-major order starting at 1. Labeled variants draw the index under each item (Arial 14), so an indexing slip is separated from a perception miss; unlabeled variants test both.

**O01 · odd-shape-labeled** · odd · odd-one-out · easy
- Generator: 640x480 white, 3x4 grid, cell 160x160. Eleven blue circles r=40 and one blue square side 80 at seeded index. Index labels under each item.
- Prompt: `These 12 items are numbered. Exactly one differs from the rest. Which number? CONTRACT ANSWER: <number>`
- Truth: `{"index": 7}`
- Score: `pass = to_int(answer) == {7}`
- Failure mode: none expected for a capable model; it is the lane's floor.

**O02 · odd-rotation-unlabeled** · odd · odd-one-out · hard
- Generator: 640x480 white, 3x4 grid of identical black arrows (polygon, 70 px long) pointing right; one rotated 12 degrees. No index labels.
- Prompt: `Exactly one of these 12 arrows differs. Counting left to right, top to bottom, starting at 1, which one? CONTRACT ANSWER: <number>`
- Truth: `{"index": 10, "rotation_deg": 12}`
- Score: `pass = to_int(answer) == {10}`; report the indexing error separately when the model names the right row.
- Failure mode: cannot see 12 degrees, or sees it and miscounts the index.

**O03 · odd-color-subtle** · odd · odd-one-out, color · hard · script_beats_model
- Generator: 640x480 white, 3x4 grid of 100 px squares in (37,99,235); one in (52,99,235) (ΔE about 6). Labeled.
- Prompt: as O01.
- Truth: `{"index": 4, "deltaE": 6}`
- Score: as O01.
- Baseline: per-cell mean RGB, argmax distance from the median; exact.
- Failure mode: picks at random. Justifies routing color-difference questions to the script.

**O04 · rug-motif-nine** · odd · odd-one-out, real art · hard · **core**
- Generator: existing Affinity fixture `/Users/alcatraz627/Code/Claude/Affinity/AffinityWork/guard/test/cases/rug-border-twelve-motifs/fixture.png`, copied read-only. Truth from its `case.json`: `numbers.off_motif_index_from_left = 9`; the pink band hides the base of motifs 3 to 5 (a trap).
- Prompt: `This rug border has twelve taupe bump motifs in a row. Counting from the left starting at 1, which motif has a different shape from the others? CONTRACT ANSWER: <number>`
- Truth: `{"index": 9}`
- Score: `pass = to_int(answer) == {9}`; flag 3, 4 or 5 as `band_trap`.
- Failure mode: picks a band-occluded motif or miscounts across the flipped half. This is real owner work, so a pass here matters most.

## 4. Build notes

- Put generators in one script with a `--seed` flag and write `truth.json` beside each PNG, matching the candidate suite's `fixture(name, truth, files)` layout in `probe/candidates/build_fixtures.py`. That file builds PNGs with the standard library only; these cases need PIL, so run with `.venv/bin/python`.
- Fixtures first: before any model runs, a model-free check must prove each scorer goes red on a wrong answer and green on the truth. Feed it the truth, a near-miss (off by one, the decoy, the prior) and an empty reply. A scorer that passes the empty reply is broken by construction.
- `score.py` in the candidate suite reads `pass` per fixture; add `format_fail` and `answered_decoy`-style flags so the report shows why a model failed, not only that it did.
- The incumbent rule in `SPEC.md` (a challenger must pass every fixture the incumbent passes) should apply per seed-averaged pass rate, with core cases gating and non-core cases informing.
- `see diff` cases cannot run Qwen3-VL until `bin/see` accepts MLX in diff mode. Report them as `not runnable` for that model rather than as fails.

## 5. Reserve cases (not in the 42, not in cases.json)

These eight were cut to keep the active set at 42. Each is either low-discrimination or overlaps a stronger case; promote one if a sibling proves weak.

**C05 · count-overlapping-rings** · qa · counting · hard · script_beats_model
- Generator: 600x400 white. 8 outline circles r=40, width 3, color (37,99,235), placed so 5 pairs overlap (center distance 50 to 70). Seeded.
- Prompt: `How many circles are drawn, including ones that overlap? CONTRACT ANSWER: <integer>`
- Truth: `{"count": 8}`
- Score: `pass = to_int(answer) == {8}`
- Baseline: Hough circle transform with known radius 40 returns 8.
- Failure mode: counts overlapping clusters as one.

**T07 · price-list-binding** · qa · reading, binding · med
- Generator: 600x320 white, Arial 22. Rows at y=40,90,140,190: "Espresso  €2.40", "Flat white  €3.85", "Matcha  €4.10", "Bagel  €3.20", labels at x=40, prices right-aligned at x=520.
- Prompt: `What is the price of the Matcha? CONTRACT ANSWER: <number>`
- Truth: `{"value": 4.10}`
- Score: `pass = 4.10 in to_num(answer) and len(to_num(answer)) == 1`
- Failure mode: reads the neighbouring row (row misalignment across wide whitespace).

**S05 · inside-the-frame** · qa · spatial · med
- Generator: 700x450 white. One outlined rectangle [200,100,500,350] width 3. Three dots r=14: one inside, two outside near its edges (8 to 20 px from the border). Colors red, blue, orange, seeded assignment.
- Prompt: `Which colored dot is inside the rectangle? CONTRACT ANSWER: <color>`
- Truth: `{"color": "blue"}`
- Score: `pass = {color_of(answer)} == {truth}`
- Failure mode: near-border dots read as inside.

**K01 · color-set** · qa · color · easy
- Generator: 600x200 white, four 100 px squares at x=40,180,320,460 in red, green, blue, yellow (seed shuffles order and may swap yellow for orange or purple).
- Prompt: `Which colors are the squares? CONTRACT ANSWER: comma-separated colors`
- Truth: `{"colors": ["red","green","blue","yellow"]}`
- Score: `got = {color_of(t) for t in answer.split(",")}; pass = got == set(truth)` (an extra color fails).
- Failure mode: adds "white" for the background. Low discrimination; kept as a floor.

**G02 · bar-argmin** · qa · chart values · easy
- Generator: the G01 chart, seeds place the minimum anywhere.
- Prompt: `Which day has the lowest bar? CONTRACT ANSWER: <day>`
- Truth: `{"day": "Fri"}`
- Score: day synonyms {Fri, Friday}; `pass = day_of(answer) == truth`
- Failure mode: answers the last or first bar.

**U05 · radio-selected** · qa · UI state · med
- Generator: 500x260 white, title "Shipping" Arial Bold 22, three radio options Standard, Express, Overnight. Selected radio: 18 px ring with an 8 px filled center. Seeded.
- Prompt: `Which shipping option is selected? CONTRACT ANSWER: <option>`
- Truth: `{"selected": "Overnight"}`
- Score: exact `norm_str`.
- Failure mode: answers the first option.

**R02 · region-containment** · region · spatial, harness sanity · easy
- Generator: 900x900 white. "TOPWORD 11" Arial 40 centered in the top third, "MIDWORD 22" in the middle third, "BOTWORD 33" in the bottom third.
- Prompt: `--region top`, `What text is visible? CONTRACT ANSWER: <text>`
- Truth: `{"text": "TOPWORD 11", "must_not": ["MIDWORD","BOTWORD"]}`
- Score: `pass = norm_str(answer) == "TOPWORD 11" and not any(mentions(text, w) for w in must_not)`
- Failure mode: a model claims text it was not shown. Doubles as a check that the crop path is wired for each backend.

**O05 · odd-size-strip** · odd · odd-one-out · med
- Generator: 1000x200 white, eight circles in a row, r=36, one r=40 (11 percent larger). Unlabeled.
- Prompt: `One of these 8 circles is a different size. Counting from the left starting at 1, which one? CONTRACT ANSWER: <number>`
- Truth: `{"index": 6}`
- Score: `pass = to_int(answer) == {6}`
- Failure mode: chance-level (12.5 percent) answers.
