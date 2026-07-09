#!/usr/bin/env bash
# Durable cross-session backstop for the see re-test coordination.
#
# Checks the lm-vision IPC mailbox for a reply from the claude-instances session
# (it was asked to re-test the updated `see` tooling vs native vision and relay
# results). When the reply lands: post a macOS notification so the user can open
# a local-models Claude session to grade it, then self-retire. No-op otherwise.
# Fired daily by launchd (gcc-schedule: vision-retest-check).
IPC="$HOME/.local/bin/claude-ipc"
SCHED="$HOME/.claude/scripts/schedule/schedule.sh"
"$IPC" register lm-vision >/dev/null 2>&1
if "$IPC" inbox lm-vision 2>/dev/null | grep -qi 'claude-instances'; then
  osascript -e 'display notification "claude-instances relayed the see re-test results — open a local-models Claude session to grade them (lm-vision inbox)" with title "local-models · vision re-test in"' >/dev/null 2>&1
  "$SCHED" rm vision-retest-check >/dev/null 2>&1   # self-retire once delivered
fi
