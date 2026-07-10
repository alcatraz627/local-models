"""Text rendering of stats results. UNFINISHED — every function below is a
specified stub; the test suite in tests/test_csvstats.py defines done."""


def render_table(summary):
    """Render a numeric_summary dict as a two-column fixed-width table.

    One line per key in the order count, min, max, mean, median:
      key padded right to 8 chars, then the value via str().
    Example line: "count   3". Lines are joined with "\\n" (no trailing
    newline). Raises ValueError if summary is None.
    """
    raise NotImplementedError("TODO")


def top_n(counts, n):
    """Top-n groups from a group_count dict.

    Returns a list of (value, count) tuples, sorted by count descending;
    ties break by str(value) ascending so output is deterministic.
    n <= 0 returns []. n larger than the dict returns everything.
    """
    raise NotImplementedError("TODO")
