# Candidate suite gaps

- `see diff` cannot route to MLX. `bin/see` rejects `--mlx` or a model name
  beginning with `mlx:` in diff mode. Stage 0 therefore cannot evaluate the
  Qwen3-VL challenger. The build spec explicitly forbids changing `bin/see`.
- The four new Stage 1 Hugging Face repositories are verified, but none has a
  verified installed Ollama tag or a verified supported `see` backend mapping
  in this worktree. They are marked `needs a runner`; no HF repository is
  passed to Ollama and the harness never triggers an implicit HF download.
- The OCR fixture strings were transcribed by visually inspecting the source
  PNG. The Apple Vision `see --ocr --json` output was not captured because the
  user barred all `see` invocations in this build-and-dry-run task.
- Stage 2 has no `mflux` executable on `PATH`. It also lacks identified RMBG-2.0
  and Real-ESRGAN runners plus exact quantized model IDs. FLUX.1-Kontext-dev needs a specified
  4-bit artifact. These candidates have fixtures/truth descriptions but no
  execution stage yet.
- Stage 3 model IDs exist on Hugging Face, but the requested workflow needs
  Ollama tags for `q -m` / `lm probe`. No exact tag was verified. Nemotron 3.5
  Bolt resolves to the 74B-A9B 24GB variant, which does not match a small-model
  lane. `bin/probe` emits a report with heuristic marker flags and requires
  human verdicts; the stage cannot be reduced to the `lm fleet` envelope
  check alone. The existing probe directly calls Ollama internally, so use of
  that runner needs an explicit allowed route.
- Stage 4 is skipped: no archived RAG eval harness or dataset was found in the
  repository tree (`rg --files` search for RAG eval names and embedding model
  names returned no paths). The skip is represented by a fixture truth record.
- The `.venv/` directory is absent in this worktree. `build_fixtures.py` uses
  only the Python standard library, so fixture generation and dry-run checks
  do not require PIL.
