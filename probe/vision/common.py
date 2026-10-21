"""Paths, the case catalog and seed rules shared by every script in this folder."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
CATALOG = ROOT / "cases.json"
SEE = REPO / "bin" / "see"
FIXTURES = ROOT / "fixtures"

# Cases built from a fixed repo image, or with no randomness worth a second look.
# They get one seed (0); everything else gets seeds 0, 1, 2.
FIXED_SEED_CASES = {"G04", "D01", "D04", "D05", "D06", "O04", "T06"}
DEFAULT_SEEDS = (0, 1, 2)


def load_cases(path=None):
    return json.loads(Path(path or CATALOG).read_text())


def case_map(path=None):
    return {c["id"]: c for c in load_cases(path)}


def seeds_for(case_id, wanted=DEFAULT_SEEDS):
    return (0,) if case_id in FIXED_SEED_CASES else tuple(wanted)


def case_dir(case_id, seed, root=None):
    return Path(root or FIXTURES) / case_id / f"s{seed}"


def load_truth(case_id, seed, root=None):
    return json.loads((case_dir(case_id, seed, root) / "truth.json").read_text())


def result_dir():
    path = ROOT / "results"
    path.mkdir(parents=True, exist_ok=True)
    return path


def slug(value):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value.lower())).strip("-")
