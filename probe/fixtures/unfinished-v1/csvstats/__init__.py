"""csvstats — tiny CSV statistics toolkit (probe fixture).

An intentionally unfinished codebase: parser.py is complete, stats.py and
report.py contain specified-but-unimplemented stubs. The test suite defines
done. Used by the finish-a-codebase procedure exercise.
"""

from .parser import parse_rows
from .stats import numeric_summary, group_count, correlation
from .report import render_table, top_n

__all__ = [
    "parse_rows",
    "numeric_summary",
    "group_count",
    "correlation",
    "render_table",
    "top_n",
]
