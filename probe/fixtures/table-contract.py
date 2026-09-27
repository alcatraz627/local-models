#!/usr/bin/env python3
"""Exercise table jobs against cases where partial or guessed arithmetic fails."""

import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
Q = ROOT / "bin/q"


def call(*args, input_text=None):
    return subprocess.run([str(Q), *args], cwd=ROOT, input=input_text,
                          text=True, capture_output=True)


def main():
    with tempfile.TemporaryDirectory(prefix="lm-table-test-") as tmp:
        p = Path(tmp) / "long.csv"
        p.write_text("name,quantity\n" + "".join(f"item{i},{i}\n" for i in range(3000)))
        result = call("describe-data", "--file", str(p), "--json")
        data = json.loads(result.stdout)
        assert result.returncode == 0, result.stderr
        assert data["data"]["rows"] == 3000
        assert data["data"]["fields"]["quantity"]["min"] == "0"
        assert data["data"]["fields"]["quantity"]["max"] == "2999"
        assert data["truncated"] is False

        result = call("--preflight", "--file", str(p), "--json")
        data = json.loads(result.stdout)
        assert data["would_truncate"] is True
        assert data["extracted_chars"] > data["max_ctx_chars"]

        bad = Path(tmp) / "bad.csv"
        bad.write_text("name,count\nA,1\nB\n")
        result = call("describe-data", "--file", str(bad), "--json")
        assert result.returncode == 12
        assert json.loads(result.stdout)["code"] == "ctx_unsupported"

        result = call("describe-data", "--json", input_text="x,y\na,1\nb,2\n")
        assert json.loads(result.stdout)["data"]["rows"] == 2

        result = call("describe-data", "--json", input_text="id,amount\n001,4\n002,5\n1,6\n")
        ids = json.loads(result.stdout)["data"]["fields"]["id"]
        assert ids["type"] == "text" and ids["distinct"] == 3, ids

        result = call("describe-data", "--json", input_text="day,value\n2026-02-28,1\n2026-02-31,2\n")
        assert json.loads(result.stdout)["data"]["fields"]["day"]["type"] == "text"

        result = call("describe-data", "--json", input_text='[{"value":1},{"value":"1"}]')
        mixed = json.loads(result.stdout)["data"]["fields"]["value"]
        assert mixed["type"] == "text" and mixed["distinct"] == 2, mixed

        book = Path(tmp) / "two.xlsx"
        with zipfile.ZipFile(book, "w") as z:
            z.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="First"/><sheet name="Second"/></sheets></workbook>')
        result = call("--preflight", "--json", "--ctx", str(book))
        info = json.loads(result.stdout)
        assert result.returncode == 0 and info["sheets"] == ["First", "Second"], result.stderr
        assert info["sheet_required"] is True and info["extracted_chars"] is None

    print("table contract: 8 behavior cases passed")


if __name__ == "__main__":
    main()
