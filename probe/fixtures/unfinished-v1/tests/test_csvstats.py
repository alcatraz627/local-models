"""The Judge: this suite DEFINES done for the unfinished-v1 fixture.

Every stub in stats.py and report.py is covered, including the edge cases
that separate plausible code from correct code. Do not weaken assertions
to make a worker's output pass — fix the worker output.
"""

import math

import pytest

from csvstats import (
    parse_rows,
    numeric_summary,
    group_count,
    correlation,
    render_table,
    top_n,
)

CSV = """name,age,score,city
ana,34,91.5,lisbon
bo,28,77.0,osaka
cy,41,88.25,lisbon
dee,,59.5,osaka
eli,28,,lisbon
"""


@pytest.fixture()
def rows():
    return parse_rows(CSV)


# ── parser (already complete — pins the shapes workers depend on) ──

def test_parse_types(rows):
    assert rows[0]["age"] == 34 and isinstance(rows[0]["age"], int)
    assert rows[0]["score"] == 91.5 and isinstance(rows[0]["score"], float)
    assert rows[3]["age"] is None
    assert rows[4]["score"] is None


# ── stats.numeric_summary ──

def test_summary_basic(rows):
    s = numeric_summary(rows, "age")
    assert s["count"] == 4
    assert s["min"] == 28 and s["max"] == 41
    assert s["mean"] == pytest.approx((34 + 28 + 41 + 28) / 4)


def test_summary_median_even(rows):
    # ages 28, 28, 34, 41 -> (28 + 34) / 2
    assert numeric_summary(rows, "age")["median"] == pytest.approx(31.0)


def test_summary_median_odd(rows):
    # scores 59.5, 77.0, 88.25, 91.5 minus the None; drop one row for odd count
    s = numeric_summary(rows[:3], "score")
    assert s["median"] == pytest.approx(88.25)


def test_summary_no_numeric(rows):
    assert numeric_summary(rows, "name") is None


# ── stats.group_count ──

def test_group_count_values(rows):
    assert group_count(rows, "city") == {"lisbon": 3, "osaka": 2}


def test_group_count_missing(rows):
    assert group_count(rows, "age")["(missing)"] == 1


# ── stats.correlation ──

def test_correlation_perfect():
    rows = parse_rows("x,y\n1,2\n2,4\n3,6\n")
    assert correlation(rows, "x", "y") == pytest.approx(1.0)


def test_correlation_inverse():
    rows = parse_rows("x,y\n1,6\n2,4\n3,2\n")
    assert correlation(rows, "x", "y") == pytest.approx(-1.0)


def test_correlation_constant_column_is_none():
    rows = parse_rows("x,y\n1,5\n2,5\n3,5\n")
    assert correlation(rows, "x", "y") is None


def test_correlation_insufficient_rows(rows):
    assert correlation(rows[:1], "age", "score") is None


def test_correlation_skips_non_numeric_pairs(rows):
    # only rows where BOTH cells are numeric: ana, bo, cy (dee has no age,
    # eli has no score) — must not crash on the Nones
    r = correlation(rows, "age", "score")
    assert r is not None and -1.0 <= r <= 1.0


# ── report.render_table ──

def test_render_table_layout():
    s = {"count": 3, "min": 1, "max": 9, "mean": 4.0, "median": 3}
    text = render_table(s)
    lines = text.split("\n")
    assert lines[0] == "count   3"
    assert lines[1] == "min     1"
    assert lines[-1] == "median  3"
    assert not text.endswith("\n")


def test_render_table_none_raises():
    with pytest.raises(ValueError):
        render_table(None)


# ── report.top_n ──

def test_top_n_order_and_ties():
    counts = {"b": 2, "a": 2, "c": 5}
    assert top_n(counts, 3) == [("c", 5), ("a", 2), ("b", 2)]


def test_top_n_bounds():
    counts = {"a": 1, "b": 2}
    assert top_n(counts, 0) == []
    assert top_n(counts, 99) == [("b", 2), ("a", 1)]
