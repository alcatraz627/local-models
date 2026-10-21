#!/bin/bash
# Run the whole vision catalog (every case, seeds 0-2) on every candidate model.
# Ollama models above ~7 GB get a bounded lease so each call does not pay a cold
# load; everything is released before an MLX model runs, since an MLX load beside
# a big resident ollama model is the known way to run this machine out of memory.
R="$(cd "$(dirname "$0")/../.." && pwd)"
PY="$R/.venv/bin/python"
run() { "$PY" "$R/probe/vision/run.py" --model "$1" --seeds 0,1,2 "${@:2}"; }

"$PY" "$R/probe/vision/gen.py"
run apple-vision

for m in minicpm-v4.6 gemma4-e4b-warm; do run "$m"; done
for m in gemma4:26b qwen3.6:35b-a3b; do
  "$R/bin/warm" on "$m" 90m
  run "$m"
  "$R/bin/warm" off all
done

"$R/bin/warm" off all
for repo in Qwen3-VL-8B-Instruct-4bit Qwen3-VL-4B-Instruct-4bit Qwen3.5-9B-MLX-4bit Qwen3.6-27B-4bit; do
  # the two newest are still downloading when this starts; wait for them
  while pgrep -f "hf download mlx-community/$repo" >/dev/null; do sleep 30; done
  run "mlx:mlx-community/$repo"
done

"$PY" "$R/probe/vision/report.py"
