# Vision comparison report

Cells are passes over seeds. A dash means that model has no run for that case. `format_fail` is a reply that broke the ANSWER contract, counted apart from wrong answers.

| Case | Core | Capability | Script | apple-vision | gemma4:26b | gemma4-e4b-warm | measure | minicpm-v4.6 | mlx:mlx-community/Qwen3.5-9B-MLX-4bit | mlx:mlx-community/Qwen3-VL-4B-Instruct-4bit | mlx:mlx-community/Qwen3-VL-8B-Instruct-4bit | qwen3.6:35b-a3b |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C01 | yes | counting | - | - | 2/3 | 0/3 | 3/3 | 3/3 | 3/3 | 2/3 | 3/3 | 2/3 |
| C02 | yes | counting | 3/3 | - | 0/3 | 0/3 | 3/3 | 0/3 | 0/3 | 1/3 | 3/3 | 0/3 |
| C03 | yes | counting, color | - | - | 2/3 | 1/3 | 3/3 | 3/3 | 3/3 | 2/3 | 2/3 | 2/3 |
| C04 |  | counting, table | - | - | 3/3 | 1/3 | - | 3/3 | 3/3 | 0/3 | 3/3 | 3/3 |
| T01 | yes | reading small text | - | - | 3/3 | 0/3 | - | 1/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| T02 |  | reading small text | - | - | 3/3 | 2/3 | - | 2/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| T03 | yes | reading, no language prior | - | - | 0/3 | 1/3 | - | 3/3 | 3/3 | 0/3 | 3/3 | 3/3 |
| T04 |  | rotated text | - | - | 3/3 | 3/3 | - | 2/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| T05 | yes | low-contrast text | - | - | 3/3 | 3/3 | - | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| T06 |  | reading, dense text | 1/1 | 1/1 | 1/1 | 1/1 | - | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| S01 |  | spatial relations | - | - | 3/3 | 3/3 | - | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| S02 | yes | spatial relations | - | - | 3/3 | 3/3 | - | 3/3 | 3/3 | 3/3 | 3/3 | 2/3 |
| S03 |  | spatial relations | - | - | 3/3 | 3/3 | - | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| S04 |  | spatial relations, color | - | - | 3/3 | 3/3 | - | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| K03 | yes | color, text binding | - | - | 3/3 | 3/3 | - | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| G01 | yes | chart values | - | - | 3/3 | 3/3 | - | 1/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| G03 |  | chart values | - | - | 3/3 | 1/3 | - | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| G04 |  | chart values, reading | - | - | 1/1 | 1/1 | - | 0/1 | 1/1 | 0/1 | 1/1 | 1/1 |
| B01 | yes | table cells | - | - | 3/3 | 3/3 | - | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| B02 |  | table cells, dense layout | - | - | 3/3 | 1/3 | - | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| U01 | yes | UI state, checked | - | - | 3/3 | 3/3 | - | 2/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| U02 | yes | UI state, disabled | - | - | 3/3 | 3/3 | - | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| U03 |  | UI state, selected | - | - | 3/3 | 3/3 | - | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| U04 |  | UI state, on/off | - | - | 3/3 | 3/3 | - | 0/3 | 3/3 | 0/3 | 3/3 | 2/3 |
| U06 | yes | dense layout, UI inventory, UI state | - | - | 3/3 | 3/3 | - | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| U07 |  | reading small text, UI | - | - | 3/3 | 3/3 | - | 3/3 | 2/3 | 3/3 | 3/3 | 2/3 |
| R01 | yes | crop lift, reading small text | - | - | 3/3 | 3/3 | - | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| D01 | yes | hallucination trap, diff | - | - | 1/1 | 0/1 | - | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| D02 | yes | diff localization | 3/3 | - | 3/3 | 2/3 | - | 0/3 | 3/3 | 0/3 | 2/3 | 3/3 |
| D03 | yes | diff, reading | - | - | 3/3 | 3/3 | - | 0/3 | 3/3 | 3/3 | 3/3 | 2/3 |
| D04 |  | diff localization, chart | - | - | 0/1 | 0/1 | - | 0/1 | 0/1 | 0/1 | 0/1 | 1/1 |
| D05 |  | hallucination trap, diff | - | - | 1/1 | 1/1 | - | 0/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| D06 |  | hallucination trap, diff | - | - | 1/1 | 0/1 | - | 0/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| D07 |  | diff localization | 3/3 | - | 0/3 | 0/3 | - | 0/3 | 0/3 | 0/3 | 0/3 | 1/3 |
| H01 | yes | hallucination trap, absence | - | - | 3/3 | 3/3 | - | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| H02 | yes | hallucination trap, false premise | - | - | 3/3 | 3/3 | - | 0/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| H03 |  | hallucination trap, absence | - | - | 3/3 | 3/3 | - | 2/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| H04 |  | hallucination trap, false premise | - | - | 3/3 | 3/3 | - | 1/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| O01 |  | odd-one-out | - | - | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| O02 |  | odd-one-out, rotation | - | - | 3/3 | 0/3 | 3/3 | 1/3 | 3/3 | 1/3 | 2/3 | 3/3 |
| O03 |  | odd-one-out, color | 3/3 | - | 0/3 | 0/3 | 3/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| O04 | yes | odd-one-out, real art | - | - | 1/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 1/1 |

## Model totals

| Model | Pass | Fail | format_fail | Median wall (s) |
|---|---:|---:|---:|---:|
| apple-vision | 1/1 | 0 | 0 | 0.2 |
| gemma4:26b | 97/112 | 12 | 3 | 1.5 |
| gemma4-e4b-warm | 78/112 | 34 | 0 | 2.2 |
| measure | 18/19 | 1 | 0 | 0.3 |
| minicpm-v4.6 | 74/112 | 34 | 4 | 1.8 |
| mlx:mlx-community/Qwen3.5-9B-MLX-4bit | 100/112 | 9 | 3 | 5.5 |
| mlx:mlx-community/Qwen3-VL-4B-Instruct-4bit | 85/112 | 26 | 1 | 3.4 |
| mlx:mlx-community/Qwen3-VL-8B-Instruct-4bit | 101/112 | 11 | 0 | 3.5 |
| qwen3.6:35b-a3b | 98/112 | 14 | 0 | 2.0 |

## Capability rollup

Mean of per-case pass rates, over the cases that have a run.

| Capability | apple-vision | gemma4:26b | gemma4-e4b-warm | measure | minicpm-v4.6 | mlx:mlx-community/Qwen3.5-9B-MLX-4bit | mlx:mlx-community/Qwen3-VL-4B-Instruct-4bit | mlx:mlx-community/Qwen3-VL-8B-Instruct-4bit | qwen3.6:35b-a3b |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| UI | - | 100% (1) | 100% (1) | - | 100% (1) | 67% (1) | 100% (1) | 100% (1) | 67% (1) |
| UI inventory | - | 100% (1) | 100% (1) | - | 100% (1) | 100% (1) | 100% (1) | 100% (1) | 100% (1) |
| UI state | - | 100% (5) | 100% (5) | - | 73% (5) | 100% (5) | 80% (5) | 100% (5) | 93% (5) |
| absence | - | 100% (2) | 100% (2) | - | 83% (2) | 100% (2) | 100% (2) | 100% (2) | 100% (2) |
| chart | - | 0% (1) | 0% (1) | - | 0% (1) | 0% (1) | 0% (1) | 0% (1) | 100% (1) |
| chart values | - | 100% (3) | 78% (3) | - | 44% (3) | 100% (3) | 67% (3) | 100% (3) | 100% (3) |
| checked | - | 100% (1) | 100% (1) | - | 67% (1) | 100% (1) | 100% (1) | 100% (1) | 100% (1) |
| color | - | 67% (4) | 58% (4) | 100% (2) | 75% (4) | 75% (4) | 67% (4) | 67% (4) | 67% (4) |
| counting | - | 58% (4) | 17% (4) | 100% (3) | 75% (4) | 75% (4) | 42% (4) | 92% (4) | 58% (4) |
| crop lift | - | 100% (1) | 100% (1) | - | 100% (1) | 100% (1) | 100% (1) | 100% (1) | 100% (1) |
| dense layout | - | 100% (2) | 67% (2) | - | 100% (2) | 100% (2) | 100% (2) | 100% (2) | 100% (2) |
| dense text | 100% (1) | 100% (1) | 100% (1) | - | 100% (1) | 100% (1) | 100% (1) | 100% (1) | 100% (1) |
| diff | - | 100% (4) | 50% (4) | - | 25% (4) | 100% (4) | 100% (4) | 100% (4) | 92% (4) |
| diff localization | - | 33% (3) | 22% (3) | - | 0% (3) | 33% (3) | 0% (3) | 22% (3) | 78% (3) |
| disabled | - | 100% (1) | 100% (1) | - | 100% (1) | 100% (1) | 100% (1) | 100% (1) | 100% (1) |
| false premise | - | 100% (2) | 100% (2) | - | 17% (2) | 100% (2) | 100% (2) | 100% (2) | 100% (2) |
| hallucination trap | - | 100% (7) | 71% (7) | - | 43% (7) | 100% (7) | 100% (7) | 100% (7) | 100% (7) |
| low-contrast text | - | 100% (1) | 100% (1) | - | 100% (1) | 100% (1) | 100% (1) | 100% (1) | 100% (1) |
| no language prior | - | 0% (1) | 33% (1) | - | 100% (1) | 100% (1) | 0% (1) | 100% (1) | 100% (1) |
| odd-one-out | - | 75% (4) | 25% (4) | 75% (4) | 33% (4) | 50% (4) | 33% (4) | 42% (4) | 75% (4) |
| on/off | - | 100% (1) | 100% (1) | - | 0% (1) | 100% (1) | 0% (1) | 100% (1) | 67% (1) |
| reading | 100% (1) | 75% (4) | 83% (4) | - | 50% (4) | 100% (4) | 50% (4) | 100% (4) | 92% (4) |
| reading small text | - | 100% (4) | 67% (4) | - | 75% (4) | 92% (4) | 100% (4) | 100% (4) | 92% (4) |
| real art | - | 100% (1) | 0% (1) | 0% (1) | 0% (1) | 0% (1) | 0% (1) | 0% (1) | 100% (1) |
| rotated text | - | 100% (1) | 100% (1) | - | 67% (1) | 100% (1) | 100% (1) | 100% (1) | 100% (1) |
| rotation | - | 100% (1) | 0% (1) | 100% (1) | 33% (1) | 100% (1) | 33% (1) | 67% (1) | 100% (1) |
| selected | - | 100% (1) | 100% (1) | - | 100% (1) | 100% (1) | 100% (1) | 100% (1) | 100% (1) |
| spatial relations | - | 100% (4) | 100% (4) | - | 100% (4) | 100% (4) | 100% (4) | 100% (4) | 92% (4) |
| table | - | 100% (1) | 33% (1) | - | 100% (1) | 100% (1) | 0% (1) | 100% (1) | 100% (1) |
| table cells | - | 100% (2) | 67% (2) | - | 100% (2) | 100% (2) | 100% (2) | 100% (2) | 100% (2) |
| text binding | - | 100% (1) | 100% (1) | - | 100% (1) | 100% (1) | 100% (1) | 100% (1) | 100% (1) |

## Crop lift

Pass counts per lane. Lift is the crop lane minus the full-frame lane.

| Case | Model | Full | Crop | Region |
|---|---|---|---|---|
| B02 | gemma4:26b | 3/3 | 3/3 | - |
| B02 | gemma4-e4b-warm | 1/3 | 3/3 | - |
| B02 | minicpm-v4.6 | 3/3 | 3/3 | - |
| B02 | mlx:mlx-community/Qwen3.5-9B-MLX-4bit | 3/3 | 3/3 | - |
| B02 | mlx:mlx-community/Qwen3-VL-4B-Instruct-4bit | 3/3 | 3/3 | - |
| B02 | mlx:mlx-community/Qwen3-VL-8B-Instruct-4bit | 3/3 | 3/3 | - |
| B02 | qwen3.6:35b-a3b | 3/3 | 3/3 | - |
| R01 | gemma4:26b | 3/3 | 3/3 | 3/3 |
| R01 | gemma4-e4b-warm | 3/3 | 3/3 | 3/3 |
| R01 | minicpm-v4.6 | 3/3 | 3/3 | 3/3 |
| R01 | mlx:mlx-community/Qwen3.5-9B-MLX-4bit | 3/3 | 3/3 | 3/3 |
| R01 | mlx:mlx-community/Qwen3-VL-4B-Instruct-4bit | 3/3 | 3/3 | 3/3 |
| R01 | mlx:mlx-community/Qwen3-VL-8B-Instruct-4bit | 3/3 | 3/3 | 3/3 |
| R01 | qwen3.6:35b-a3b | 3/3 | 3/3 | 3/3 |

## Plain-read companion (not gated)

H01 asked with the default read prompt; pass means nothing invented.

| Model | Pass |
|---|---|
| gemma4:26b | 3/3 |
| gemma4-e4b-warm | 1/3 |
| minicpm-v4.6 | 3/3 |
| mlx:mlx-community/Qwen3.5-9B-MLX-4bit | 3/3 |
| mlx:mlx-community/Qwen3-VL-4B-Instruct-4bit | 3/3 |
| mlx:mlx-community/Qwen3-VL-8B-Instruct-4bit | 3/3 |
| qwen3.6:35b-a3b | 3/3 |

## Named failure shapes

Counts of flagged rows per model (answered_decoy, band_trap, and so on).

- gemma4-e4b-warm: autocorrected 1, band_trap 1
- mlx:mlx-community/Qwen3-VL-4B-Instruct-4bit: band_trap 1
