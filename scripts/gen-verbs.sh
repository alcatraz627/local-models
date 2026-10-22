#!/usr/bin/env bash
# Regenerate everything derived from lib/verbs.toml: zsh completion, man pages, tldr pages and
# the front-door block in docs/CAPABILITIES.md. The lm screens render live, so they need no step.
# Run this after any edit to lib/verbs.toml; probe/fixtures/verbs-drift.py fails until you do.
set -eo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$DIR/.venv/bin/python"; [ -x "$PY" ] || PY=python3
"$PY" "$DIR/lib/verbs.py" gen --root "$DIR"
echo "generated: share/zsh/_{lm,q,see,warm}  share/man/man1/{lm,q,see,warm}.1  share/tldr/*.page.md  docs/CAPABILITIES.md (verbs block)"
