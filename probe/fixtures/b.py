"""String helpers. (multi-file probe: slugify gets added here.)"""


def truncate(s, n=80):
    return s if len(s) <= n else s[: n - 1] + "…"
