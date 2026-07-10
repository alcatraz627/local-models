#!/usr/bin/env bash
# Fired by gcc-schedule (local-agent-resume) on Thu 2026-07-09 to prompt resuming the
# local-models local-agent work. Agenda: ~/Code/local-models/docs/NEXT-SESSION.md
osascript -e 'display notification "cd ~/Code/local-models && claude → /catchup. Agenda: docs/NEXT-SESSION.md (MLX #5 · fleet #9 · finish-a-codebase)" with title "local-models · resume local-agent work"' 2>/dev/null
echo "$(date '+%Y-%m-%d %H:%M') local-agent resume reminder fired" >> ~/Code/local-models/logs/reminders.log 2>/dev/null
exit 0
