# Build notes: vision comparison harness

Built on branch `vision-harness` from Codex's first drafts, which had never been run. No model, `ollama run/pull` or `imagine` was used; `see` was called only with `--ocr`, and `lib/vis-compare.py` directly for the diff baselines. All 42 cases are implemented, so there is no GAPS.md.

## What changed from the drafts

The draft crash (`D07 has no script baseline`) was real: D07 is tagged `script_beats_model` and had no baseline function. Reading the rest critically turned up more, all fixed:

- D02's prompt had the true cell filled into `r<row>c<col>`, which leaked the answer. The placeholder stays now and selftest checks it.
- `to_int` missed "twenty-three" (hyphen) and "5." (trailing period), and treated "1,2" as 12. `pos_of("top-left")` returned top, left and top-left at once, so S03 could never pass cleanly. All rewritten, with tests.
- G03's drafted series crossed in June while the truth said May. Series are now built from the crossing month, with a gap of at least 6 units on both sides.
- B01 and C04 drew header text across a gridline; B02 labelled rows `R-401` instead of `R-0412`; U06's coordinates did not match the catalog layout; S02 and K03 were hard-coded, so seeds changed nothing.
- No-ANSWER-line fallback and `format_fail` were not implemented per scorer. Each scorer now names its candidate finder, and the multi-field cases (S04, U01, G04, D04) require the ANSWER line.
- Scoring uses candidate sets, not keyword bags: T01/T02/T04/T05 find one text candidate by pattern, S02 finds one letter, and so on.

## Where the harness differs from the catalog (read before trusting a number)

- **D07's script baseline is not the one the catalog names.** The catalog expected vis-compare E1 to report the move (`delta_xy` x=+24). It does not: E1 lists a move only when the 3x3 position label of the text changes, and 20 to 30 px shifts stay inside one label. `baselines.json` records `e1_moved: false` for all three seeds. The baseline here compares the centre of the non-white content in A and B and reads the element name from `see --ocr`. It hits truth on every seed. Whether `see diff` should say direction itself is a routing question for you.
- **O03's colour was far too close.** (52,99,235) against (37,99,235) is delta E 1.5, not the "about 6" the catalog states. The odd cell now uses (37,106,235) (delta E 5.7, seed 1 and 2 use 107 and 105) and `truth.json` records the measured delta E. D02's hard variant (seed 2) uses (37,118,235), delta E 15.4. The script baselines still hit both.
- Seeds that need meaning: T02 uses seed 0/1/2 for 9, 12 and 7 px with different invoice strings (so the legibility floor is read from the three seeds); D07 uses right 24, down 20, left 30; U06 varies which checkbox is ticked; S01 has three seeds, not four (pass `--seeds 0,1,2,3` to `gen.py` for the fourth); T06 has one seed because its three lines are fixed.
- D06's `b.png` is the JPEG q85 round trip saved back as PNG, so `see diff` gets the lossy pixels but not a `.jpg` file.
- T06 is an `ocr+read` case: the model lane is a normal `qa` run, and the OCR lane runs once under `apple-vision`. `see diff` is run for every model including `mlx:`, per your correction.
- No-ANSWER-line replies for T03, T06, U04 and U06 are not a thing (they are scored on the whole reply or on `.data`), so their canned `format_fail` rows are empty or structureless replies.

## Not verified (UNCONFIRMED)

- The shape of a real `see --ui --json` `.data`. U04 and U06 assume `regions[].elements[]` with `type`, `text`, `state` (from the prompt in `bin/see`). Expect to tune the state vocabulary after the first real output.
- `run.py` against a real model reply: the envelope parse (`.text`, `.data`), the 420 s timeout and the result rows were only exercised on faked rows through `report.py`. The commands themselves are shown in the dry run below.
- The MLX guard's parsing was tested against fake `ollama ps` text (a 17 GB line blocks, 5 GB and MB lines do not); a live resident model was not available.
- `scripts/verify.sh` was syntax-checked (`bash -n`) but not run in full; the worktree has no `.venv`, so selftest was run with the main checkout's venv python.

## Red and green proof

A selftest that cannot go red is worthless, so scorers were broken on purpose and restored:

| Break | Result |
|---|---|
| C01-C04 scorer `ints == {expected}` changed to `len(ints) == 1` (any single number passes) | selftest 23/26, exit 1; canned wrong answers 8, 27, 20, 15, 5 passed, and the truth-mutation check failed for C01 to C03 |
| D02 scorer compares the column only | first run stayed **green (26/26)**: the canned wrong answers all had a wrong column, and the mutation changed both coordinates. A real blind spot. Fixed by adding `r1c2` to the canned fails and mutating only the first coordinate |
| D02 break repeated after the fix | 24/26, exit 1 (`D02 'ANSWER: r1c2' expected fail got pass`, plus the mutation check) |
| U06 scorer stops gating on checkbox state | 24/26, exit 1 (`U06 '' expected fail got pass`, plus the mutation check) |

Each break was reverted by editing the line back, and selftest returned to 26/26.

## Images checked

Opened with the Read tool and compared with `truth.json`; none were clipped and all text was legible. Where the viewer cannot show it (the difference in O03, the exact dot count in C02) the generator parameters and the baseline stand in.

C02 s0 (4 hollow rings visible, 23 filled by baseline), C03 s1 (3 red, 5 blue, 4 green, truth red 3 of 12), T01 s1 (ID `T0M-2SDH-8118`, decoy line is its prefix), T03 s1 (draxil wemp / nuvor kessel / flarn 5824 brint / opali zenth), T04 s0 (ORBIT 7731 vertical on the left, LUMEN 2208 tilted), T05 s0 (faint DELTA 5508 readable, loud ALPHA 1234), S02 s1 (star nearest box B, margin 84.7), S03 s0 (triangle at centre), K03 s1 (APPLE yellow, LEMON green, GRAPE blue), G01 s1 (Thu bar at 27), G03 s0 (B first above A in May), B01 s0 (Halvorsen 57, neighbours 84 and 89), B02 s0 crop (R-0412 HOLD between OPEN and DONE), U01 s1 (Dark mode, Auto-save ticked), U04 s0 (Wi-Fi and AirDrop on), U06 s0 (12 elements, Send weekly digest ticked), U07 s1 (99+ badge fits its pill), R01 s0 crop (Latency p95 388 ms beside Latency p99 412 ms), D03 s1 b (Total 9.58, A has 9.18), D07 s1 b (button 20 px lower), O02 s0 (arrow 10 rotated), O03 s0 (cell 4 slightly lighter). That is 22 images across counting, text, spatial, colour, chart, table, UI, crop, diff and odd-one-out families.

## Selftest output

```
ok   gen: all 42 cases build
ok   gen deterministic: two full runs are byte-identical
ok   truth.json parses and matches the catalog schema for every case and seed
ok   prompts carry the ANSWER contract
ok   D02 prompt keeps the r<row>c<col> placeholder (truth is not leaked)
ok   seeds change the image and the truth (priors cannot score)
ok   baselines hit truth on every seed (13 runs over C02, T06, D02, D07, O03)
ok   every catalog case has a registered scorer
ok   canned.json: at least 4 replies per core case, 3 per other case
ok   canned.json: every case has a pass, a fail and a format_fail reply
ok   canned replies score as written (pass, fail, format_fail, synonyms, number words, cell forms)
ok   an empty reply never passes, for every scorer
ok   each scorer passes the correct reply built from every seed's truth
ok   mutation: corrupting the truth makes that same correct reply fail, for every scorer
ok   mutation (C01 spelled out): count+1 in memory fails the canned correct answer
ok   named failure flags fire on the near-miss answers
ok   to_int: digits, thousands separators, number words, compounds
ok   to_num: decimals, currency, units
ok   norm_str: case, quotes, backticks, trailing punctuation
ok   color_of: synonyms
ok   pos_of: compound names are not split into parts
ok   cell_of: r3c2, row 3 col 2, (3,2), ordinals, swapped order
ok   month_of: names and abbreviations
ok   negation: 'there is no circle' does not mention circle
ok   negation: affirmed and unrelated terms still count
ok   absent_answer: absence words and 'there is no ...'; numbers and quotes are not absence
26/26 passed
```

## Dry-run output: run.py --model minicpm-v4.6 --core --dry-run

No model ran. Lines are long because the full prompt is part of each command.

```
[C01 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/C01/s0/image.png 'How many filled circles are in this image? End your reply with exactly one line of the form: ANSWER: <integer>' --json -m minicpm-v4.6
[C01 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/C01/s1/image.png 'How many filled circles are in this image? End your reply with exactly one line of the form: ANSWER: <integer>' --json -m minicpm-v4.6
[C01 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/C01/s2/image.png 'How many filled circles are in this image? End your reply with exactly one line of the form: ANSWER: <integer>' --json -m minicpm-v4.6
[C02 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/C02/s0/image.png 'Count only the FILLED dots. Hollow rings do not count. End your reply with exactly one line of the form: ANSWER: <integer>' --json -m minicpm-v4.6
[C02 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/C02/s1/image.png 'Count only the FILLED dots. Hollow rings do not count. End your reply with exactly one line of the form: ANSWER: <integer>' --json -m minicpm-v4.6
[C02 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/C02/s2/image.png 'Count only the FILLED dots. Hollow rings do not count. End your reply with exactly one line of the form: ANSWER: <integer>' --json -m minicpm-v4.6
[C03 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/C03/s0/image.png 'How many BLUE squares are there? End your reply with exactly one line of the form: ANSWER: <integer>' --json -m minicpm-v4.6
[C03 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/C03/s1/image.png 'How many RED squares are there? End your reply with exactly one line of the form: ANSWER: <integer>' --json -m minicpm-v4.6
[C03 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/C03/s2/image.png 'How many GREEN squares are there? End your reply with exactly one line of the form: ANSWER: <integer>' --json -m minicpm-v4.6
[T01 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/T01/s0/image.png 'What is the full Build ID? End your reply with exactly one line of the form: ANSWER: <id>' --json -m minicpm-v4.6
[T01 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/T01/s1/image.png 'What is the full Build ID? End your reply with exactly one line of the form: ANSWER: <id>' --json -m minicpm-v4.6
[T01 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/T01/s2/image.png 'What is the full Build ID? End your reply with exactly one line of the form: ANSWER: <id>' --json -m minicpm-v4.6
[T03 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/T03/s0/image.png --json -m minicpm-v4.6
[T03 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/T03/s1/image.png --json -m minicpm-v4.6
[T03 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/T03/s2/image.png --json -m minicpm-v4.6
[T05 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/T05/s0/image.png 'There are two lines of text. What does the faint, light-gray line say? End your reply with exactly one line of the form: ANSWER: <text>' --json -m minicpm-v4.6
[T05 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/T05/s1/image.png 'There are two lines of text. What does the faint, light-gray line say? End your reply with exactly one line of the form: ANSWER: <text>' --json -m minicpm-v4.6
[T05 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/T05/s2/image.png 'There are two lines of text. What does the faint, light-gray line say? End your reply with exactly one line of the form: ANSWER: <text>' --json -m minicpm-v4.6
[S02 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/S02/s0/image.png 'Which lettered box is closest to the green star? End your reply with exactly one line of the form: ANSWER: <letter>' --json -m minicpm-v4.6
[S02 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/S02/s1/image.png 'Which lettered box is closest to the green star? End your reply with exactly one line of the form: ANSWER: <letter>' --json -m minicpm-v4.6
[S02 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/S02/s2/image.png 'Which lettered box is closest to the green star? End your reply with exactly one line of the form: ANSWER: <letter>' --json -m minicpm-v4.6
[K03 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/K03/s0/image.png 'What color is the ink of the word LEMON? End your reply with exactly one line of the form: ANSWER: <color>' --json -m minicpm-v4.6
[K03 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/K03/s1/image.png 'What color is the ink of the word LEMON? End your reply with exactly one line of the form: ANSWER: <color>' --json -m minicpm-v4.6
[K03 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/K03/s2/image.png 'What color is the ink of the word LEMON? End your reply with exactly one line of the form: ANSWER: <color>' --json -m minicpm-v4.6
[G01 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/G01/s0/image.png 'What is Thursday'"'"'s value? End your reply with exactly one line of the form: ANSWER: <number>' --json -m minicpm-v4.6
[G01 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/G01/s1/image.png 'What is Thursday'"'"'s value? End your reply with exactly one line of the form: ANSWER: <number>' --json -m minicpm-v4.6
[G01 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/G01/s2/image.png 'What is Thursday'"'"'s value? End your reply with exactly one line of the form: ANSWER: <number>' --json -m minicpm-v4.6
[B01 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/B01/s0/image.png 'In the row whose Name is Halvorsen, what is the Units value? End your reply with exactly one line of the form: ANSWER: <integer>' --json -m minicpm-v4.6
[B01 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/B01/s1/image.png 'In the row whose Name is Halvorsen, what is the Units value? End your reply with exactly one line of the form: ANSWER: <integer>' --json -m minicpm-v4.6
[B01 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/B01/s2/image.png 'In the row whose Name is Halvorsen, what is the Units value? End your reply with exactly one line of the form: ANSWER: <integer>' --json -m minicpm-v4.6
[U01 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/U01/s0/image.png 'Which options are checked? End your reply with exactly one line of the form: ANSWER: comma-separated labels' --json -m minicpm-v4.6
[U01 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/U01/s1/image.png 'Which options are checked? End your reply with exactly one line of the form: ANSWER: comma-separated labels' --json -m minicpm-v4.6
[U01 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/U01/s2/image.png 'Which options are checked? End your reply with exactly one line of the form: ANSWER: comma-separated labels' --json -m minicpm-v4.6
[U02 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/U02/s0/image.png 'Which button is disabled? End your reply with exactly one line of the form: ANSWER: <label>' --json -m minicpm-v4.6
[U02 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/U02/s1/image.png 'Which button is disabled? End your reply with exactly one line of the form: ANSWER: <label>' --json -m minicpm-v4.6
[U02 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/U02/s2/image.png 'Which button is disabled? End your reply with exactly one line of the form: ANSWER: <label>' --json -m minicpm-v4.6
[U06 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/U06/s0/image.png --ui --json -m minicpm-v4.6
[U06 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/U06/s1/image.png --ui --json -m minicpm-v4.6
[U06 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/U06/s2/image.png --ui --json -m minicpm-v4.6
[R01 s0 full] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/R01/s0/image.png 'What is the Latency p99 value? End your reply with exactly one line of the form: ANSWER: <number> ms' --json -m minicpm-v4.6
[R01 s0 crop] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/R01/s0/image.png --crop 700x500+1700+1000 'What is the Latency p99 value? End your reply with exactly one line of the form: ANSWER: <number> ms' --json -m minicpm-v4.6
[R01 s0 region] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/R01/s0/image.png --region right 'What is the Latency p99 value? End your reply with exactly one line of the form: ANSWER: <number> ms' --json -m minicpm-v4.6
[R01 s1 full] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/R01/s1/image.png 'What is the Latency p99 value? End your reply with exactly one line of the form: ANSWER: <number> ms' --json -m minicpm-v4.6
[R01 s1 crop] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/R01/s1/image.png --crop 700x500+1700+1000 'What is the Latency p99 value? End your reply with exactly one line of the form: ANSWER: <number> ms' --json -m minicpm-v4.6
[R01 s1 region] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/R01/s1/image.png --region right 'What is the Latency p99 value? End your reply with exactly one line of the form: ANSWER: <number> ms' --json -m minicpm-v4.6
[R01 s2 full] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/R01/s2/image.png 'What is the Latency p99 value? End your reply with exactly one line of the form: ANSWER: <number> ms' --json -m minicpm-v4.6
[R01 s2 crop] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/R01/s2/image.png --crop 700x500+1700+1000 'What is the Latency p99 value? End your reply with exactly one line of the form: ANSWER: <number> ms' --json -m minicpm-v4.6
[R01 s2 region] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/R01/s2/image.png --region right 'What is the Latency p99 value? End your reply with exactly one line of the form: ANSWER: <number> ms' --json -m minicpm-v4.6
[D01 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see diff /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/D01/s0/a.png /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/D01/s0/b.png 'List every visible difference between A and B. If there are none, say so. End your reply with exactly one line of the form: ANSWER: NONE or ANSWER: <number of differences>' --json -m minicpm-v4.6
[D02 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see diff /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/D02/s0/a.png /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/D02/s0/b.png 'Exactly one cell in this 4x4 grid differs. Which row and column (1-based, row 1 at top)? End your reply with exactly one line of the form: ANSWER: r<row>c<col>' --json -m minicpm-v4.6
[D02 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see diff /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/D02/s1/a.png /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/D02/s1/b.png 'Exactly one cell in this 4x4 grid differs. Which row and column (1-based, row 1 at top)? End your reply with exactly one line of the form: ANSWER: r<row>c<col>' --json -m minicpm-v4.6
[D02 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see diff /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/D02/s2/a.png /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/D02/s2/b.png 'Exactly one cell in this 4x4 grid differs. Which row and column (1-based, row 1 at top)? End your reply with exactly one line of the form: ANSWER: r<row>c<col>' --json -m minicpm-v4.6
[D03 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see diff /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/D03/s0/a.png /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/D03/s0/b.png 'One value changed between A and B. Give the old and the new value. End your reply with exactly one line of the form: ANSWER: <old> -> <new>' --json -m minicpm-v4.6
[D03 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see diff /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/D03/s1/a.png /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/D03/s1/b.png 'One value changed between A and B. Give the old and the new value. End your reply with exactly one line of the form: ANSWER: <old> -> <new>' --json -m minicpm-v4.6
[D03 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see diff /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/D03/s2/a.png /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/D03/s2/b.png 'One value changed between A and B. Give the old and the new value. End your reply with exactly one line of the form: ANSWER: <old> -> <new>' --json -m minicpm-v4.6
[H01 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/H01/s0/image.png 'Is there any text in this image? If yes, transcribe it. End your reply with exactly one line of the form: ANSWER: NONE or the text' --json -m minicpm-v4.6
[H01 s0 read] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/H01/s0/image.png --json -m minicpm-v4.6
[H01 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/H01/s1/image.png 'Is there any text in this image? If yes, transcribe it. End your reply with exactly one line of the form: ANSWER: NONE or the text' --json -m minicpm-v4.6
[H01 s1 read] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/H01/s1/image.png --json -m minicpm-v4.6
[H01 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/H01/s2/image.png 'Is there any text in this image? If yes, transcribe it. End your reply with exactly one line of the form: ANSWER: NONE or the text' --json -m minicpm-v4.6
[H01 s2 read] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/H01/s2/image.png --json -m minicpm-v4.6
[H02 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/H02/s0/image.png 'What value does the orange series show for Wednesday? End your reply with exactly one line of the form: ANSWER: <number> or ABSENT if there is no such series' --json -m minicpm-v4.6
[H02 s1 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/H02/s1/image.png 'What value does the orange series show for Wednesday? End your reply with exactly one line of the form: ANSWER: <number> or ABSENT if there is no such series' --json -m minicpm-v4.6
[H02 s2 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/H02/s2/image.png 'What value does the orange series show for Wednesday? End your reply with exactly one line of the form: ANSWER: <number> or ABSENT if there is no such series' --json -m minicpm-v4.6
[O04 s0 main] /Users/alcatraz627/Code/local-models-vision/bin/see /Users/alcatraz627/Code/local-models-vision/probe/vision/fixtures/O04/s0/image.png 'This rug border has twelve taupe bump motifs in a row. Counting from the left starting at 1, which motif has a different shape from the others? End your reply with exactly one line of the form: ANSWER: <number>' --json -m minicpm-v4.6
```
