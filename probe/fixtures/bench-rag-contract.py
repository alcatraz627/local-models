#!/usr/bin/env python3
"""Guard the quick benchmark's content checks and RAG chunk boundaries."""

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    bench = load("bench", ROOT / "scripts/bench.py")
    cases = json.loads((ROOT / "probe/bench/quick.json").read_text())["cases"]
    short, visual = cases[1:]
    assert "text" in bench.response_failures(short, {"ok": True, "text": "banana"})
    assert not bench.response_failures(short, {"ok": True, "text": "OK."})
    wrong_visual = {"ok": True, "evidence": {"meta": {"modality": "iconlike", "comparable": "good"},
                                             "scores": {"dhash": 0, "grid_delta_pct": 56.2}}}
    assert "evidence.scores.dhash" in bench.response_failures(visual, wrong_visual)

    rag = load("rag", ROOT / "lib/rag.py")
    with tempfile.TemporaryDirectory(prefix="lm-rag-contract-") as tmp:
        source = Path(tmp) / "long.md"
        source.write_text("# H\n" + "x" * 2500 + "\n")
        chunks = list(rag.chunk_file(source))
    assert len(chunks) == 2, chunks
    assert all(len(text) <= rag.MAX_CHARS for _, _, text in chunks)
    assert sum(text.count("x") for _, _, text in chunks) == 2500
    print("benchmark and RAG contract: 4 behavior cases passed")


if __name__ == "__main__":
    main()
