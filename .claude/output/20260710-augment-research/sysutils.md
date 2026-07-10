---
sessions: augment-research@2026-07-10
---

# macOS system utilities that give agents new senses or hands

Research scope: native macOS tooling and CLIs that extend what an AI agent can
perceive or actuate on the machine, beyond the baseline this user already runs
(screencapture+sips, launchd, osascript/Calendar, pbcopy/pbpaste, Ollama,
fzf/gum, ripgrep/fd, pm2, nginx .test). Ranked roughly by leverage per unit of
setup effort.

## 1. Peekaboo — vision + hands in one CLI/MCP server

**What it is:** a macOS CLI and MCP server (`openclaw/Peekaboo`, formerly
steipete's) that captures pixel-accurate screenshots via ScreenCaptureKit and
drives click/type/scroll/hotkey/menu/window/dock input, with an optional
natural-language `agent` subcommand that chains those primitives.

**New capability:** it's the closest thing to Anthropic/OpenAI "computer use"
running natively and locally — the agent can see an annotated screenshot with
element IDs (`see`), then click/type against those IDs, and critically can post
input to a background app (`--app`/`--pid`/`--window-id`) **without stealing
focus**, so it can drive Safari or Notes while the user keeps working in the
foreground app.

**Maturity/effort:** actively developed, 4.8k GitHub stars, 2,931 commits,
v3.8.0. Needs macOS 15+ (Sequoia), Swift 6.2, Node 22+ for the MCP server, and
Screen Recording + Accessibility permissions. `brew install
steipete/tap/peekaboo` is the fast path; permission grants are the only real
friction.

Source: https://github.com/openclaw/Peekaboo · https://peekaboo.sh/

## 2. ax-cli / AXorcist — read the UI as structured data, not pixels

**What it is:** terminal tools built on the AXUIElement Accessibility API.
`ax-cli` (Rust, `watzon/ax-cli`) exposes `tree`/`find`/`inspect`/`attrs`/`click`
/`type`/`watch`/`wait`/`diff` over any app's accessibility tree. `AXorcist`
(Swift, `steipete/AXorcist`) is the library-level equivalent with chainable,
fuzzy-matched queries.

**New capability:** where Peekaboo gives an agent eyes on pixels, this gives it
eyes on **semantics** — role, title, value, and a stable path for every UI
element, so it can find "the Save button" without OCR or coordinate guessing,
and `watch`/`wait` let it block on a state change instead of polling
screenshots. Cheaper and more reliable than vision-based clicking for apps that
expose a real accessibility tree.

**Maturity/effort:** early-stage (`ax-cli`: 0 stars, 3 releases, last shipped
April 2026 — functional but not widely battle-tested). Needs Accessibility TCC
permission granted to the calling terminal.

Source: https://github.com/watzon/ax-cli · https://github.com/steipete/AXorcist

## 3. Native Vision-framework OCR CLIs (mac-ocr / ocrit / apple-vision-utils)

**What it is:** thin CLI wrappers around Apple's on-device Vision text
recognizer. `mac-ocr` (`privatenumber/mac-ocr`) ships a prebuilt universal npm
binary and can emit searchable PDFs; `ocrit` (`insidegui/ocrit`) is the
original minimal Swift CLI; `apple-vision-utils` adds multi-language + batch +
positional JSON output.

**New capability:** turns any screenshot, PDF, or photo into machine-readable
text entirely on-device (no upload, no API key), with word-level bounding boxes
in the JSON-output variants — useful as a fallback sense for apps that have no
accessibility tree at all, or for reading text baked into images.

**Maturity/effort:** small, stable, single-purpose tools; `brew`/`npm`
installable, no permissions beyond normal file access. Low effort.

Source: https://github.com/privatenumber/mac-ocr · https://github.com/insidegui/ocrit/ · https://github.com/tddschn/apple-vision-utils

## 4. osquery — SQL over live system state

**What it is:** Facebook-originated, now Linux-Foundation-hosted daemon/CLI
(`osqueryi`) that exposes running processes, open sockets, mounted volumes,
installed packages, kernel extensions, login history, and hundreds of other OS
facts as queryable SQL tables.

**New capability:** a single structured query language for "what is this
machine doing right now" that replaces a pile of ad-hoc `ps`/`lsof`/`netstat`
parsing — an agent can ask `SELECT * FROM processes WHERE name LIKE '%node%'`
and get typed columns back instead of scraping text output. This is jq-grade
structure for the whole OS, not just one tool's output.

**Maturity/effort:** mature, widely deployed in enterprise security tooling.
`brew install osquery`. `osqueryd` (the always-on daemon) is heavier than most
agent use cases need — `osqueryi` (interactive/one-shot queries) is the right
entry point for on-demand agent lookups.

Source: https://github.com/osquery/osquery · https://osquery.readthedocs.io/

## 5. mdfind / Spotlight metadata queries

**What it is:** the command-line front end to the Spotlight index — the same
store Cmd-Space searches, covering 125+ built-in metadata attributes (content,
kind, author, EXIF, dates) across the whole indexed filesystem.

**New capability:** instant full-text + metadata search with zero index
maintenance (Spotlight stays current automatically), including an
`-interpret` flag for natural-language-ish queries and a `-live` mode that
keeps streaming new matches — a cheap way for an agent to answer "find that PDF
I downloaded last week about X" without grepping the whole disk.

**Maturity/effort:** built into every Mac, zero install. The gap versus
`rg`/`fd` is metadata (kind, author, screenshot vs. photo, date-taken) that
ripgrep can't see at all — complementary, not a replacement.

Source: https://ss64.com/mac/mdfind.html · https://metaredux.com/posts/2019/12/22/mdfind.html

## 6. fswatch — event-driven triggers instead of polling

**What it is:** a cross-platform file-change monitor that on macOS rides
native FSEvents, streaming changed paths to stdout for piping into other
commands.

**New capability:** lets an agent-adjacent script react the instant a file
changes (a screenshot lands, a log rotates, a build artifact appears) instead
of polling on a timer — pairs naturally with the existing launchd scheduling
setup for "fire when X appears" rather than "fire every N minutes and check."
Scales cleanly to large trees (tested to 500 GB with no degradation).

**Maturity/effort:** mature, stable, `brew install fswatch`. Zero special
permissions for normal user directories.

Source: https://github.com/emcrisostomo/fswatch · https://emcrisostomo.github.io/fswatch/

## 7. yabai / AeroSpace — queryable window/space state as JSON

**What it is:** tiling window managers that expose a CLI query interface.
`yabai` runs a Unix socket queryable for displays/spaces/windows; `AeroSpace`
ships JSON-friendly `list-windows`/`list-workspaces`/`list-monitors` commands
designed for piping into scripts.

**New capability:** structured window/space state (which app owns which
window, geometry, which space is active) that's otherwise only available
through slow/fragile AppleScript `System Events` calls — useful for an agent
that needs to reason about "what's currently visible" before deciding where to
click or capture.

**Maturity/effort — caveat:** yabai's full scripting-addition feature set
requires **partially disabling SIP** (`sudo yabai --load-sa`), which is a real
security tradeoff for a window-state query. AeroSpace gets most of the same
JSON query surface **without** touching SIP and is the safer default if the
only goal is read-only state, not tiling behavior.

Source: https://github.com/koekeishiya/yabai/wiki/Commands · https://doolpa.com/article/aerospace-window-manager

## 8. Hammerspoon — a general Lua actuator bridge

**What it is:** an open-source automation framework that bridges macOS APIs
(windows, mouse, keyboard, clipboard, wifi, battery, screens, low-level input
events, filesystem watchers) to a Lua scripting engine, controllable via IPC
(`hs -c "..."`) from shell scripts.

**New capability:** one persistent, always-running process that an agent can
poke via CLI to do almost anything short of full accessibility-tree reads —
useful as connective tissue when a task needs mouse/keyboard synthesis, wifi
state, or battery/display info and a purpose-built CLI doesn't exist for it.

**Maturity/effort:** very mature (long-running project), but higher setup
cost than the single-purpose tools above — requires writing/maintaining a
`init.lua` config and running a background app with Accessibility permission.
Worth it only if the agent will lean on it repeatedly, not for a one-off need.

Source: https://github.com/Hammerspoon/hammerspoon · https://www.hammerspoon.org/

## 9. Shortcuts CLI (`shortcuts run`) — a door into Apple Intelligence + system integrations

**What it is:** the built-in `shortcuts` CLI (`list`, `run`, `sign`) that
invokes any user-built Shortcuts workflow headlessly.

**New capability:** the cheapest bridge from shell to things that have no
other CLI at all — HomeKit, Reminders, Apple Intelligence's on-device/Private
Cloud Compute "Use Model" action, and any first-party app action exposed to
Shortcuts. An agent can have a human pre-build a Shortcut once, then trigger it
by name forever after.

**Maturity/effort:** built-in, zero install. The catch is indirection — the
actual logic lives in a GUI-built `.shortcut` file, not in a script the agent
can read/version, so it's best for stable, rarely-changing actions rather than
things the agent needs to iterate on.

Source: https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac

## 10. whisper.cpp — local speech-to-text (ears)

**What it is:** a C/C++ port of OpenAI's Whisper that runs fully offline, with
Metal acceleration on Apple Silicon (large-v3 at roughly 10x real-time on an
M5 Pro).

**New capability:** gives an agent an ear — spoken input transcribed on-device
with no network round-trip and no audio leaving the machine, feeding straight
into the existing local-model text pipeline.

**Maturity/effort:** mature, widely used, well documented. Setup is a `git
clone` + `cmake` build + one model download (`base`/`small` are enough for
command-style dictation); Metal acceleration is on by default on Apple Silicon.

Source: https://github.com/ggml-org/whisper.cpp

## 11. Piper / Kokoro — local high-quality TTS (a better voice than `say`)

**What it is:** local neural TTS engines. Piper (Open Home Foundation) runs
fast on CPU; Kokoro uses a CoreML model via FluidAudio with 50 voices across 8
languages, synthesized at 24kHz, using the Neural Engine.

**New capability:** materially more natural spoken output than the built-in
`say` command, still fully local/private — useful if the agent workflow ever
wants spoken status updates or accessibility-style narration instead of just
notification banners.

**Maturity/effort:** both are established open-source projects; Kokoro's
CoreML build is the better Apple Silicon fit (Neural Engine, no Python
runtime). Moderate setup (model download + a small wrapper script); `say` stays
fine for short, low-stakes prompts.

Source: https://www.thoughtasylum.com/2025/08/25/text-to-speech-on-macos-with-piper/ · https://github.com/dokterbob/macos-speech-server

## 12. SQLite FTS5 — instant full-text search over the agent's own corpus

**What it is:** SQLite's built-in full-text-search virtual table module —
tokenize once, get an inverted index with BM25 ranking, boolean/phrase
queries, no external server.

**New capability:** not a system-facing sense, but a cheap way for an agent to
build fast local search over its own accumulated data (WAL logs, memory files,
runtime-notes, transcripts) without standing up embeddings or a vector DB —
exact-terminology recall (error codes, function names) that embedding search
tends to miss.

**Maturity/effort:** built into SQLite (already on every Mac via `sqlite3`),
zero extra install. `CREATE VIRTUAL TABLE x USING fts5(...)` and go. Very low
effort, high payoff for anything that's already writing JSONL/markdown logs.

Source: https://www.sqlite.org/fts5.html

## 13. terminal-notifier + `dnd` — a notification hand and an interruptibility sense

**What it is:** `terminal-notifier` posts native banner notifications from a
script (message, icon, sound, click-to-open-URL); `joeyhoer/dnd` reads/toggles
Do Not Disturb state via AppleScript/System Events.

**New capability:** gives an agent a way to reach the human outside the
terminal (a real macOS notification, not just chat text) and — via `dnd` — the
ability to check whether the human is currently in Do Not Disturb before
deciding whether to interrupt at all.

**Maturity/effort:** both small and stable. `dnd` needs Accessibility
permission granted to the calling terminal (System Events control). Focus
Filters (the newer, more granular per-app modes) still have no clean official
CLI — third-party wrappers exist but shell out to a pre-built Shortcut under
the hood, which is a real limitation, not a solved problem.

Source: https://github.com/joeyhoer/dnd · (terminal-notifier is the long-standing `julienXX/terminal-notifier`)

## 14. cliclick — minimal, dependency-free input synthesis

**What it is:** a small Objective-C CLI (`BlueM/cliclick`) that emits raw
mouse and keyboard events (`c:x,y` to click, key presses, drags) with no
runtime dependencies.

**New capability:** the lightest possible "hand" — useful as a fallback when
Peekaboo/AXorcist are overkill for a single click-and-done interaction, or when
scripting something that needs to stay dependency-minimal.

**Maturity/effort:** mature, stable, tiny. `brew install cliclick`. Needs
Accessibility permission for the calling terminal. Coordinate-based only — no
semantic element targeting, so it's blind compared to AX-tree tools; best paired
with an OCR or AX read to find the coordinates first.

Source: https://github.com/BlueM/cliclick

---

## Skip these — and why

**GUI clipboard managers (Paste, Maccy-as-a-service, etc.) as an agent
interface.** Beyond what `pbcopy`/`pbpaste` already give (which the user's
workflow already uses), these menubar apps don't expose a stable public
CLI/API for clipboard *history* — scripting them means reverse-engineering a
private SQLite store or Apple Events interface that can break on any update.
If history matters, a five-line script that snapshots `pbpaste` into a local
SQLite/FTS5 table (item 12) on a `pbpaste`-diff loop is more durable than
depending on a third-party app's internals.

**yabai's full scripting-addition mode as the default window-query tool.**
Covered above under item 7, but worth repeating as a skip-by-default: don't
reach for `sudo yabai --load-sa` (partial SIP disable) just to read window
geometry. That's a standing security posture change for a read-only need.
AeroSpace's JSON `list-*` commands or plain `osascript`/System Events cover
the common case without touching SIP; escalate to yabai's full mode only if
the agent genuinely needs yabai-specific tiling actions, not queries.

**btop/mactop as the machine-readable process/resource layer.** These are
built as human-facing terminal dashboards first; mactop's headless JSON mode
exists but the whole category is solving a "look nice in a terminal" problem
an agent doesn't have. osquery (item 4) already gives typed, joinable,
scriptable access to the same process/resource facts — standing up a second
TUI-monitor tool just to scrape its output is duplicated effort for a worse
interface than the SQL table already provides.
