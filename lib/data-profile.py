#!/usr/bin/env python3
"""Deterministic table profile for q describe-data and input preflight."""

import argparse
import csv
from datetime import date
import io
import json
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path


def fail(code, message, mode, status=12):
    if mode == "json":
        print(json.dumps({"ok": False, "code": code, "message": message}))
    else:
        print(f"q: {message}", file=sys.stderr)
    raise SystemExit(status)


def workbook_sheets(path):
    try:
        with zipfile.ZipFile(path) as z:
            root = ET.fromstring(z.read("xl/workbook.xml"))
        ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        return [x.attrib["name"] for x in root.iter(ns + "sheet")]
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as e:
        raise ValueError(f"could not read XLSX sheet list: {e}") from e


def load_text(path, fmt, sheet, mode):
    if sheet and fmt != "xlsx":
        fail("invalid_args", "--sheet applies only to XLSX input", mode, 2)
    if path == "-":
        raw = sys.stdin.buffer.read()
        if not raw:
            fail("ctx_empty", "stdin is empty", mode)
        try:
            return raw.decode("utf-8-sig"), [], None
        except UnicodeDecodeError:
            fail("ctx_unsupported", "stdin must be UTF-8 CSV, TSV, or JSON", mode)
    p = Path(path).expanduser()
    if not p.is_file():
        fail("ctx_unreadable", f"no such file: {p}", mode)
    if fmt == "xlsx":
        try:
            sheets = workbook_sheets(p)
        except ValueError as e:
            fail("ctx_unsupported", str(e), mode)
        if not sheets:
            fail("ctx_empty", f"workbook has no sheets: {p}", mode)
        if sheet is None and len(sheets) > 1:
            fail("sheet_required", f"workbook has {len(sheets)} sheets: {', '.join(sheets)}. Pass --sheet NAME or 1-based number", mode)
        selected = sheet or sheets[0]
        if selected.isdigit():
            i = int(selected)
            if i < 1 or i > len(sheets):
                fail("sheet_missing", f"sheet number {i} is outside 1..{len(sheets)}", mode)
            selected = sheets[i - 1]
        if selected not in sheets:
            fail("sheet_missing", f"no sheet named {selected!r}; available: {', '.join(sheets)}", mode)
        with tempfile.TemporaryDirectory(prefix="lm-profile-") as tmp:
            out = Path(tmp) / "sheet.csv"
            try:
                run = subprocess.run(["zconvert", str(p), str(out), "--sheet", selected],
                                     capture_output=True, text=True)
            except FileNotFoundError:
                fail("converter_missing", "XLSX profiling needs zconvert on PATH", mode)
            if run.returncode:
                fail("ctx_unsupported", f"zconvert failed: {(run.stderr or run.stdout).strip()[:240]}", mode)
            return out.read_text(encoding="utf-8-sig"), sheets, selected
    try:
        return p.read_text(encoding="utf-8-sig"), [], None
    except (OSError, UnicodeDecodeError) as e:
        fail("ctx_unsupported", f"cannot read text from {p}: {e}", mode)


def table_from_text(text, fmt, mode):
    if not text.strip():
        fail("ctx_empty", "table is empty", mode)
    if fmt == "auto":
        fmt = "json" if text.lstrip().startswith(("[", "{")) else "tsv" if "\t" in text.splitlines()[0] else "csv"
    if fmt == "json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            fail("ctx_unsupported", f"invalid JSON: {e}", mode)
        if isinstance(data, dict):
            arrays = [(k, v) for k, v in data.items() if isinstance(v, list)]
            if len(arrays) != 1:
                fail("ctx_unsupported", "JSON table needs an array of records or one array-valued field", mode)
            data = arrays[0][1]
        if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
            fail("ctx_unsupported", "JSON table needs an array of objects", mode)
        columns = list(dict.fromkeys(k for row in data for k in row))
        return columns, [[row.get(k) for k in columns] for row in data], fmt
    if fmt not in ("csv", "tsv", "xlsx"):
        fail("ctx_unsupported", f".{fmt} is not a supported table format; use CSV, TSV, XLSX, or JSON", mode)
    delimiter = "\t" if fmt == "tsv" else ","
    try:
        rows = list(csv.reader(io.StringIO(text), delimiter=delimiter, strict=True))
    except csv.Error as e:
        fail("ctx_unsupported", f"invalid delimited table: {e}", mode)
    if not rows:
        fail("ctx_empty", "table has no header", mode)
    columns = rows[0]
    if not columns or any(not c.strip() for c in columns) or len(set(columns)) != len(columns):
        fail("ctx_unsupported", "table needs nonempty, unique column names", mode)
    for i, row in enumerate(rows[1:], 2):
        if len(row) != len(columns):
            fail("ctx_unsupported", f"row {i} has {len(row)} cells, expected {len(columns)}", mode)
    return columns, rows[1:], fmt


def infer(values):
    present = [v for v in values if v is not None and str(v).strip() != ""]
    missing = len(values) - len(present)
    if not present:
        return {"type": "empty", "missing": missing, "distinct": 0}
    decimal_values = []
    for v in present:
        if isinstance(v, bool):
            break
        try:
            d = Decimal(str(v).strip())
            if not d.is_finite():
                break
            decimal_values.append(d)
        except InvalidOperation:
            break
    distinct = len({(type(v).__name__, json.dumps(v, sort_keys=True, ensure_ascii=False)) for v in present})
    padded_integer = any(isinstance(v, str) and re.fullmatch(r"[+-]?0\d+", v.strip()) for v in present)
    mixed_json_types = any(isinstance(v, str) for v in present) and any(
        isinstance(v, (int, float)) and not isinstance(v, bool) for v in present)
    if len(decimal_values) == len(present) and not padded_integer and not mixed_json_types:
        integer = all(v == v.to_integral_value() for v in decimal_values)
        return {"type": "integer" if integer else "number", "missing": missing,
                "distinct": distinct,
                "min": str(min(decimal_values)), "max": str(max(decimal_values))}
    if all(isinstance(v, bool) or str(v).lower() in ("true", "false") for v in present):
        kind = "boolean"
    elif all(valid_date(str(v)) for v in present):
        kind = "date"
    else:
        kind = "text"
    return {"type": kind, "missing": missing, "distinct": distinct}


def valid_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def render(profile):
    head = f"{profile['rows']} data rows × {len(profile['columns'])} columns"
    if profile["sheet"]:
        head += f"; sheet: {profile['sheet']}"
    lines = [head + "."]
    for c in profile["columns"]:
        stats = profile["fields"][c]
        s = f"{c}: {stats['type']}; {stats['missing']} missing; {stats['distinct']} distinct"
        if "min" in stats:
            s += f"; min {stats['min']}; max {stats['max']}"
        lines.append(s + ".")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--format", default="auto")
    ap.add_argument("--sheet")
    ap.add_argument("--mode", choices=("text", "json", "stream"), default="text")
    ap.add_argument("--query", default="")
    ap.add_argument("--log")
    ap.add_argument("--sheets-only", action="store_true")
    args = ap.parse_args()
    if args.sheets_only:
        try:
            sheets = workbook_sheets(Path(args.input).expanduser())
        except ValueError as e:
            fail("ctx_unsupported", str(e), "json")
        print(json.dumps({"ok": True, "sheets": sheets}))
        return
    t0 = time.monotonic()
    mode = "json" if args.mode != "text" else "text"
    fmt = args.format
    if fmt == "auto" and args.input != "-":
        fmt = Path(args.input).suffix.lower().lstrip(".")
    text, sheets, selected = load_text(args.input, fmt, args.sheet, mode)
    columns, rows, fmt = table_from_text(text, fmt, mode)
    fields = {c: infer([row[i] for row in rows]) for i, c in enumerate(columns)}
    profile = {"format": fmt, "source": args.input, "sheet": selected, "sheets": sheets,
               "rows": len(rows), "columns": columns, "fields": fields, "input_chars": len(text)}
    summary = render(profile)
    ms = int((time.monotonic() - t0) * 1000)
    if args.mode == "json":
        print(json.dumps({"ok": True, "text": summary, "data": profile,
                          "model": "deterministic:tabular", "ms": ms,
                          "tokens_in": 0, "tokens_out": 0, "truncated": False}))
    elif args.mode == "stream":
        print(json.dumps({"t": "chunk", "text": summary}))
        print(json.dumps({"t": "done", "model": "deterministic:tabular", "ms": ms,
                          "tokens_in": 0, "tokens_out": 0, "truncated": False}))
    else:
        print(summary)
    if args.log:
        try:
            from datetime import datetime, timezone
            stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            with open(args.log, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": stamp, "cid": stamp, "intent": "describe-data",
                                    "model": "deterministic:tabular", "think": False,
                                    "prompt": args.query, "response": summary, "ms": ms,
                                    "resident": False, "caller": str(Path.cwd())}) + "\n")
        except OSError:
            pass


if __name__ == "__main__":
    main()
