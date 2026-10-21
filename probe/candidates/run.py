#!/usr/bin/env python3
"""Candidate suite runner. --dry-run validates fixture payloads without model calls."""
import argparse
import json
import re
import shlex
import struct
import subprocess
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIXTURES = HERE / "fixtures"

MODELS = {
    "see-diff": {
        "gemma4:26b": {"size": "17 GB (config comment)", "cli": "see"},
        "minicpm-v4.6": {"size": "1.6 GB (config comment)", "cli": "see"},
        "mlx:mlx-community/Qwen3-VL-8B-Instruct-4bit": {"size": "~6 GB (docs/STATE estimate)", "cli": "see", "gap": "see diff rejects MLX routing"},
    },
    "see-read": {
        "minicpm-v4.6": {"size": "1.6 GB (config comment)", "cli": "see"},
        "mlx:mlx-community/Qwen3-VL-8B-Instruct-4bit": {"size": "~6 GB (docs/STATE estimate)", "cli": "see", "option": "--ui", "only": [f"ui-f{n}-{side}" for n in range(2, 7) for side in ("a", "b")]},
        "XiaomiMiMo/MiMo-V2.6-Distill-Qwen-9B": {"size": "18.8 GB HF repository storage", "cli": "needs a runner"},
        "Qwen/Qwen2.5-VL-7B-Instruct": {"size": "16.6 GB HF repository storage", "cli": "needs a runner"},
        "mistralai/Pixtral-12B-2409": {"size": "25.4 GB HF repository storage", "cli": "needs a runner"},
        "ibm-granite/granite-docling-258M": {"size": "3.1 GB HF repository storage", "cli": "needs a runner"},
    },
    "text-small": {
        "granite4:tiny-h": {"size": "installed; disk size not measured", "cli": "lm probe"},
        "gemma4-e4b-warm": {"size": "~5.6 GB (docs/STATE)", "cli": "lm probe"},
        "Nemotron 3.5 Bolt": {"size": "24.1 GB HF repository storage (74B-A9B-24GB variant)", "cli": "needs a runner"},
        "openbmb/MiniCPM5-2B": {"size": "5.0 GB HF repository storage", "cli": "needs a runner"},
    },
    "image-tools": {
        "mflux qwen-edit": {"size": "UNCONFIRMED; local install/model not inspected", "cli": "needs a runner", "only": ["edit-region"]},
        "FLUX.1-Kontext-dev 4-bit": {"size": "UNCONFIRMED; quantized variant unspecified", "cli": "needs a runner", "only": ["edit-region"]},
        "RMBG-2.0": {"size": "UNCONFIRMED; exact repo/quantization unspecified", "cli": "needs a runner", "only": ["rmbg-shape"]},
        "Real-ESRGAN x4": {"size": "UNCONFIRMED; local install/model not inspected", "cli": "needs a runner", "only": ["upscale"]},
    },
}


def fixture_records():
    records = []
    for truth_path in sorted(FIXTURES.rglob("truth.json")):
        truth = json.loads(truth_path.read_text())
        base = truth_path.parent
        input_names = [k for k in ("a.png", "b.png", "image.png", "reference.png", "edited.png", "input.png", "foreground.png", "noisy-background.png", "rug.png", "items.toml") if (base / k).exists()]
        if truth.get("mask"):
            input_names.append(truth["mask"])
        files = [base / name for name in input_names]
        files.extend(base / name for name in truth.get("source_files", []))
        files = list(dict.fromkeys(files))
        for file in files:
            if not file.is_file():
                raise ValueError(f"missing fixture input: {file}")
            validate_payload(file)
        records.append((base.relative_to(FIXTURES).as_posix(), base, truth, files))
    if not records:
        raise ValueError("no fixture truth.json files found")
    return records


def validate_payload(path):
    if path.suffix.lower() == ".png":
        data = path.read_bytes()
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError(f"invalid PNG signature: {path}")
        pos = 8
        idat = bytearray()
        ended = False
        width = height = color = depth = interlace = None
        while pos + 12 <= len(data):
            size = struct.unpack(">I", data[pos:pos + 4])[0]
            kind = data[pos + 4:pos + 8]
            end = pos + 12 + size
            if end > len(data):
                raise ValueError(f"truncated PNG chunk: {path}")
            payload = data[pos + 8:pos + 8 + size]
            crc = struct.unpack(">I", data[pos + 8 + size:end])[0]
            if zlib.crc32(kind + payload) & 0xffffffff != crc:
                raise ValueError(f"bad PNG chunk CRC: {path}")
            if kind == b"IHDR":
                width, height, depth, color, comp, filt, interlace = struct.unpack(">IIBBBBB", payload)
                if not width or not height or comp or filt or interlace not in (0, 1):
                    raise ValueError(f"invalid PNG header: {path}")
            elif kind == b"IDAT":
                idat.extend(payload)
            elif kind == b"IEND":
                ended = True
                pos = end
                break
            pos = end
        if not ended or width is None or not idat:
            raise ValueError(f"incomplete PNG: {path}")
        try:
            zlib.decompress(bytes(idat))
        except zlib.error as exc:
            raise ValueError(f"invalid PNG image data: {path}: {exc}") from exc
    elif path.suffix.lower() == ".json":
        json.loads(path.read_text())
    elif path.suffix.lower() == ".toml":
        parsed = subprocess.run(["yq", "-p", "toml", "-o", "json", str(path)], capture_output=True, text=True)
        if parsed.returncode:
            raise ValueError(f"could not parse TOML fixture {path}: {parsed.stderr.strip()}")
        json.loads(parsed.stdout)


def validate_fixtures():
    records = fixture_records()
    for rel, base, truth, files in records:
        if not isinstance(truth, dict) or "kind" not in truth:
            raise ValueError(f"invalid truth object: {base / 'truth.json'}")
        print(f"FIXTURE OK {rel}: truth.json parses; {len(files)} input file(s)")
    return records


def command_for(stage, model, fixture_name, base):
    item = MODELS[stage][model]
    if item["cli"] == "needs a runner":
        return None
    if stage == "see-diff":
        return ["see", "diff", str(base / "a.png"), str(base / "b.png"), "--json", "-m", model]
    if stage == "see-read":
        if fixture_name == "ocr":
            question = "Read and reproduce the visible text exactly."
        else:
            question = "Identify the key visible content and answer the fixture's checkable question."
        if fixture_name == "rug-border-twelve-motifs":
            question = "Which numbered motif is the odd one, and where is it in the row?"
        elif fixture_name == "rug-crescents-match-bottom":
            question = "Compare the point counts of the two top crescents with the clean bottom pair."
        elif fixture_name == "rug-rim-scallops-new-points":
            question = "How many straight rim pieces are shown, and how many points does each have?"
        elif fixture_name == "rug-brick-column-fanning":
            question = "How many bricks and gap lines are on each side of the column?"
        elif fixture_name == "rug-smooth-pink-stripe":
            question = "How many overlapping pink pieces and purple slivers are visible?"
        elif fixture_name == "rug-sync-to-copy":
            question = "How many shapes are in total, and how many are unique to each side?"
        return ["see", str(base / "image.png"), question, "--json"] + ([item["option"]] if item.get("option") else []) + ["-m", model]
    if stage == "text-small" and item["cli"] == "lm probe":
        report = HERE / "results" / stage / f"{slug(model)}.md"
        return ["lm", "probe", model, "--out", str(report)]
    return None


def slug(model):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", model).strip("_")


def check_answer(result, truth):
    if not isinstance(result, dict):
        result = {"text": str(result)}
    text = str(result.get("text", ""))
    normalized = " ".join(text.casefold().split())
    kind = truth["kind"]
    if kind == "contains_all":
        expected = truth.get("expected", [])
        return all(term.casefold() in normalized for term in expected), f"required={expected}"
    if kind == "absence":
        required = truth.get("required", [])
        forbidden = truth.get("forbidden", [])
        good = any(term.casefold() in normalized for term in required) and not any(term.casefold() in normalized for term in forbidden)
        return good, f"required_any={required}; forbidden={forbidden}"
    if kind == "item_position":
        item = truth["expected_item"].casefold()
        position = truth["position"].casefold()
        return item in normalized and position in normalized, f"item={item}; position={position}"
    if kind == "grid_cells_changed_only":
        got = result.get(truth.get("result_field", "changed_cells"))
        expected = truth["expected_cells"]
        try:
            good = sorted([list(map(int, cell)) for cell in got]) == sorted([list(map(int, cell)) for cell in expected])
        except (TypeError, ValueError):
            good = False
        return good, f"changed_cells={got}; expected_only={expected}"
    if kind == "alpha_mae_percent":
        got = result.get(truth.get("result_field", "alpha_mismatch_percent"))
        good = isinstance(got, (int, float)) and got <= truth["max_percent"]
        return good, f"alpha mismatch={got}; maximum={truth['max_percent']}%"
    if kind == "psnr_beats_lanczos":
        candidate = result.get(truth["candidate_field"])
        baseline = result.get(truth["baseline_field"])
        good = isinstance(candidate, (int, float)) and isinstance(baseline, (int, float)) and candidate > baseline
        return good, f"candidate PSNR={candidate}; Lanczos PSNR={baseline}"
    if kind == "envelope":
        good = result.get("ok") is True and bool(str(result.get("text", "")).strip())
        return good, "requires ok=true and nonempty text"
    if kind == "reuse_probe_markers":
        rows = result.get("probe_items")
        good = isinstance(rows, list) and bool(rows) and all(row.get("human_verdict") in ("pass", "fail") for row in rows)
        return good, "requires existing probe marker rows and a recorded human verdict for each"
    return False, f"unsupported mechanical check kind: {kind}"


def run_one(command, item, stage, model, name, base):
    warm = subprocess.run(["warm", "off", "all"], check=False, capture_output=True, text=True)
    if warm.returncode:
        raise RuntimeError(f"warm off all failed ({warm.returncode}): {warm.stderr.strip()}")
    if model.startswith("mlx:"):
        state = subprocess.run(["lm", "models", "--json"], check=False, capture_output=True, text=True)
        if state.returncode:
            raise RuntimeError(f"cannot verify resident models before MLX run: {state.stderr.strip()}")
        try:
            payload = json.loads(state.stdout)
            resident = payload.get("resident", [])
            sizes = {row["name"]: int(row.get("size", 0)) for row in payload.get("available", [])}
        except (ValueError, TypeError, KeyError) as exc:
            raise RuntimeError(f"cannot parse lm models --json before MLX run: {exc}") from exc
        big = [name for name in resident if sizes.get(name, 0) >= 7_000_000_000]
        unknown = [name for name in resident if name not in sizes]
        if big or unknown:
            detail = ", ".join(big + unknown)
            raise RuntimeError(f"MLX run blocked; resident Ollama model size is >=7 GB or unknown: {detail}")
    if stage == "text-small":
        Path(command[-1]).parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if stage == "text-small" and item["cli"] == "lm probe":
        report = Path(command[-1])
        if not report.is_file():
            raise RuntimeError(f"lm probe did not write its report: {report}")
        rows = []
        current = None
        for line in report.read_text().splitlines():
            if line.startswith("## "):
                if current:
                    rows.append(current)
                current = {"fixture": line[3:].split(" — ", 1)[0], "pass": None, "human_verdict": None}
            elif current and "**Auto:**" in line:
                current["auto"] = line.split("`", 2)[1] if line.count("`") >= 2 else "REVIEW"
            elif current and "**Human verdict:**" in line:
                current["human_verdict"] = "pass" if "☒ pass" in line else "fail" if "☒ fail" in line else None
        if current:
            rows.append(current)
        text = report.read_text()
        if "model not found" in text.casefold() or "not installed" in text.casefold():
            print(f"MODEL MISSING {model}: ollama pull {shlex.quote(model)}", file=sys.stderr)
            return {"error": "model_missing", "probe_items": rows, "report": str(report)}
        for row in rows:
            row["pass"] = row["human_verdict"] == "pass" if row["human_verdict"] else None
        return {"probe_items": rows, "report": str(report)}
    raw = proc.stdout.strip()
    parsed = None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        pass
    text = parsed.get("text", "") if isinstance(parsed, dict) else raw
    if "visual read failed" in text.casefold() and item["cli"] == "see":
        print(f"MODEL MISSING {model}: ollama pull {shlex.quote(model)}", file=sys.stderr)
        return {"fixture": name, "pass": False, "error": "model_missing", "output": text[:400]}
    if proc.returncode != 0:
        if "model_missing" in raw or "not installed" in (raw + proc.stderr).casefold():
            if item["cli"] == "see":
                print(f"MODEL MISSING {model}: ollama pull {shlex.quote(model)}", file=sys.stderr)
            return {"fixture": name, "pass": False, "error": "model_missing", "output": raw[:400]}
        return {"fixture": name, "pass": False, "error": f"exit {proc.returncode}", "output": raw[:400]}
    truth = json.loads((base / "truth.json").read_text())
    passed, detail = check_answer(parsed if isinstance(parsed, dict) else {"text": text}, truth)
    print(f"{'PASS' if passed else 'FAIL'} {name}: {detail}")
    return {"fixture": name, "pass": passed, "detail": detail, "answer": text}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["see-diff", "see-read", "image-tools", "text-small", "embed"])
    parser.add_argument("--model")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    records = validate_fixtures()
    stage = args.stage
    model_group = "image-tools" if stage == "image-tools" else stage
    if stage == "embed":
        print("SKIPPED embed: archived RAG eval harness absent; see fixtures/embed/archived-rag/truth.json")
        return 0
    models = MODELS[model_group]
    chosen = [args.model] if args.model else list(models)
    unknown = [m for m in chosen if m not in models]
    if unknown:
        parser.error(f"unknown model for {stage}: {', '.join(unknown)}")
    pending = []
    for model in chosen:
        info = models[model]
        selected = [(rel.split("/", 1)[1], base, truth) for rel, base, truth, _ in records
                    if rel.startswith(model_group + "/") and (not info.get("only") or rel.split("/", 1)[1] in info["only"])]
        if not selected:
            print(f"SKIPPED {stage}/{model}: no fixtures")
            continue
        print(f"MODEL {model} | disk cost: {info['size']}")
        results = []
        for name, base, truth in selected:
            command = command_for(stage, model, name, base)
            if command is None:
                print(f"NEEDS RUNNER {model}: {name}")
                pending.append(model)
                continue
            if info.get("gap"):
                print(f"UNRUNNABLE {model}: {info['gap']}")
                print("WOULD-RUN " + shlex.join(command))
                pending.append(model)
                continue
            print("PREP warm off all")
            print("COMMAND " + shlex.join(command))
            if args.dry_run:
                continue
            result = run_one(command, info, stage, model, name, base)
            results.append(result)
            if result.get("error") == "model_missing":
                output = HERE / "results" / stage / f"{slug(model)}.json"
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps({"stage": stage, "model": model, "checks": results}, indent=2) + "\n")
                return 3
        if not args.dry_run and results:
            output = HERE / "results" / stage / f"{slug(model)}.json"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps({"stage": stage, "model": model, "checks": results}, indent=2) + "\n")
    if pending and not args.dry_run:
        print("No runner was invoked for candidates marked NEEDS RUNNER.", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"run.py: {exc}", file=sys.stderr)
        raise SystemExit(2)
