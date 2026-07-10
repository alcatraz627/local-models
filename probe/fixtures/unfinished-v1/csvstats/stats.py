"""Column statistics over parsed rows. UNFINISHED — every function below is
a specified stub; the test suite in tests/test_csvstats.py defines done."""


def numeric_summary(rows, col):
    """Summarize the numeric values of one column.

    Considers only int/float cells (skip None and str). Returns a dict:
      {"count": int, "min": x, "max": x, "mean": x, "median": x}
    Median of an even count is the mean of the two middle values.
    If the column has no numeric values, returns None.
    """
    raise NotImplementedError("TODO")


def group_count(rows, col):
    """Count rows per distinct value of a column.

    Returns a dict value -> count. None cells are counted under the
    key "(missing)". Values are used as-is (an int 3 and a str "3"
    are different groups).
    """
    raise NotImplementedError("TODO")


def correlation(rows, col_a, col_b):
    """Pearson correlation between two columns.

    Uses only rows where BOTH cells are numeric (int/float). Returns a
    float in [-1.0, 1.0]. Returns None when fewer than 2 such rows
    exist, or when either column is constant (zero variance).
    """
    raise NotImplementedError("TODO")
