"""CSV text → typed rows. The one COMPLETE module — workers see this as
surrounding context and must match its conventions and shapes."""

import csv
import io


def _coerce(value):
    """Best-effort typing for a CSV cell: int, then float, else stripped str.

    Empty cells become None so numeric code can skip them explicitly.
    """
    s = value.strip()
    if s == "":
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        return s


def parse_rows(text):
    """Parse CSV text (header row required) into a list of dicts.

    Each row maps header name -> typed cell (int | float | str | None).
    Blank lines are skipped. Raises ValueError on empty input or a
    row with more cells than the header.
    """
    reader = csv.reader(io.StringIO(text))
    rows = [r for r in reader if any(cell.strip() for cell in r)]
    if not rows:
        raise ValueError("empty CSV")
    header, data = rows[0], rows[1:]
    out = []
    for r in data:
        if len(r) > len(header):
            raise ValueError(f"row has {len(r)} cells, header has {len(header)}")
        row = {h: _coerce(r[i]) if i < len(r) else None for i, h in enumerate(header)}
        out.append(row)
    return out
