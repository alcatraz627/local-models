#!/usr/bin/python3
"""Everything the two `lm hear` screens know and do, one word per step, so each step runs without a screen.

There are two screens. `browse` lists past runs with the transcript of the
highlighted one beside it. `live` shows a listening session as it happens: each
line as it is heard, who said it, and the controls. The shell script
`hear-screen` only draws and asks; this holds the rows, the panes and the
questions.

  browse-rows | browse-header | browse-keys | browse-detail KEY | browse-flow STEP KEY
  live-rows DIR | live-header DIR | live-keys | live-detail DIR KEY | live-flow DIR STEP | live-tick DIR
"""
from __future__ import annotations

import calendar
import json
import os
import sys
import textwrap
import time
from pathlib import Path

HOME = Path.home()
ROOT = Path(__file__).resolve().parent.parent
# Tests point these at temporary files, so they never touch the real history.
LOG = Path(os.environ.get("HEAR_SCREEN_LOG") or ROOT / "logs" / "hear-history.jsonl")

sys.path.insert(0, str(HOME / ".claude" / "scripts" / "tui"))
from tuikit import AMBER, BLUE, CYAN, DIM, GREEN, MAGENTA, PLAIN, RED  # noqa: E402
from tuikit import PANE, choice, dialog, legend, notice, section, title  # noqa: E402

HEADING = "day:"
VOICE_TONES = [CYAN, MAGENTA, GREEN, BLUE, AMBER]
KIND_WORDS = {"words": "words", "call": "call", "intent": "intent", "check": "check", "live": "spoken",
              "live-notes": "notes", "voices": "voices"}


def clock(seconds) -> str:
    t = int(seconds or 0)
    return "%d:%02d:%02d" % (t // 3600, t % 3600 // 60, t % 60) if t >= 3600 else "%02d:%02d" % (t // 60, t % 60)


def fit(text: str, width: int) -> str:
    """Cut text to a width at a word, so a row never wraps and never ends mid-word."""
    text = " ".join((text or "").split())
    if len(text) <= width:
        return text
    cut = text[:width + 1].rsplit(" ", 1)[0]
    return cut if cut else text[:width]


def wrap(text: str, width: int = PANE - 2):
    return textwrap.wrap(" ".join((text or "").split()), width) or [""]


# ── past runs ──

def runs():
    """Every run that left something to open, newest first, each with its number."""
    if not LOG.is_file():
        return []
    out = []
    for n, line in enumerate(LOG.read_text().splitlines(), 1):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("ok") and r.get("artifact") and Path(r["artifact"]).is_dir():
            out.append((n, r))
    return out[::-1]


def local(ts: str):
    return time.localtime(calendar.timegm(time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")))


def day_word(ts: str) -> str:
    then, now = local(ts), time.localtime()
    if (then.tm_year, then.tm_yday) == (now.tm_year, now.tm_yday):
        return "today"
    return time.strftime("%a %d %b", then).lower()


def browse_rows():
    out, last_day = [], None
    for n, r in runs():
        day = day_word(r["ts"])
        if day != last_day:
            out.append("%s%s\t%s%s%s" % (HEADING, day, DIM, day.upper(), PLAIN))
            last_day = day
        what = r.get("snippet") or (Path(r["file"]).name if r.get("file") else "")
        out.append("%d\t  %s%-4s%s %s %-6s %s%5s%s %s" % (
            n, CYAN, "#%d" % n, PLAIN, time.strftime("%H:%M", local(r["ts"])), KIND_WORDS.get(r.get("verb"), r.get("verb") or ""),
            DIM, clock(r.get("seconds")), PLAIN, fit(what, 24)))
    return out or ["%snone\t%sNo runs yet. Try: lm hear live%s" % (HEADING, DIM, PLAIN)]


def browse_header():
    listed = runs()
    today = sum(1 for _n, r in listed if day_word(r["ts"]) == "today")
    return "%d past run%s, %d from today." % (len(listed), "" if len(listed) == 1 else "s", today)


def browse_keys():
    return legend([[("enter", "read it", CYAN), ("s", "speakers", GREEN), ("c", "as a call", GREEN)],
                   [("v", "voices", GREEN), ("o", "open folder", CYAN), ("q", "quit", CYAN)]])


def run_of(key: str):
    for n, r in runs():
        if str(n) == key:
            return n, r
    return None, None


def result_of(r: dict) -> dict:
    try:
        return json.loads((Path(r["artifact"]) / "result.json").read_text())
    except (OSError, ValueError):
        return {}


def voices_of(res: dict) -> str:
    who = {s.get("speaker") for s in res.get("segments", []) if s.get("speaker") is not None}
    return "%d" % len(who) if who else "not labelled"


def transcript_lines(res: dict, most: int):
    out = []
    for s in res.get("segments", [])[:most]:
        who = s.get("speaker")
        tone = VOICE_TONES[int(who) % len(VOICE_TONES)] if str(who).isdigit() else DIM
        head = "%s%s%s %s" % (DIM, clock(s.get("start")), PLAIN, "%sS%s%s " % (tone, who, PLAIN) if who is not None else "")
        body = wrap(s.get("text", ""), PANE - 12)
        out.append(head + body[0])
        out += ["         " + more for more in body[1:]]
    if not out and res.get("text"):
        out = wrap(res["text"])
    return out


def browse_detail(key: str):
    """The right-hand pane: the same three lines for every run, then sections in the same order."""
    if key.startswith(HEADING):
        day = key[len(HEADING):]
        listed = [(n, r) for n, r in runs() if day_word(r["ts"]) == day]
        return title(day.upper()) + ["%d run%s" % (len(listed), "" if len(listed) == 1 else "s")]
    n, r = run_of(key)
    if r is None:
        return title("run %s" % key) + ["That run is no longer in the history."]
    res = result_of(r)
    out = title("run %d, %s" % (n, KIND_WORDS.get(r.get("verb"), r.get("verb") or ""))) + [
        "when      %s" % time.strftime("%a %d %b, %H:%M", local(r["ts"])),
        "length    %s" % clock(r.get("seconds")),
        "voices    %s" % voices_of(res)]
    if res.get("intent"):
        it = res["intent"]
        out += section("what was asked") + ["%s%s%s %s" % (GREEN, it.get("kind", ""), PLAIN, it.get("target", ""))] + wrap(it.get("text", ""))
    if res.get("digest"):
        out += section("digest")
        # The digest is stored as markdown. In the pane its headings and bullets are drawn, not shown as marks.
        for line in res["digest"].splitlines()[:16]:
            line = line.strip()
            if line.startswith("#"):
                out.append("%s%s%s" % (CYAN, line.lstrip("# "), PLAIN))
            elif line[:2] in ("* ", "- "):
                body = wrap(line[2:], PANE - 4)
                out += ["- " + body[0]] + ["  " + more for more in body[1:]]
            elif line:
                out += wrap(line)
    out += section("transcript") + transcript_lines(res, 14)
    if res.get("notes"):
        out += section("notes")
        for note in res["notes"]:
            out += wrap(note)
    return out


def minutes_for(r: dict, what: str) -> str:
    secs = float(r.get("seconds") or 0)
    need = {"speakers": secs / 4, "call": secs / 4 + 60, "voices": 5}[what]
    return "a few seconds" if need < 20 else "about %d minute%s" % (max(1, round(need / 60)), "" if round(need / 60) <= 1 else "s")


def browse_flow(step: str, key: str = ""):
    """One question the browse screen asks. Answers with what the screen does next.

    read FILE | again N ARGS | folder DIR | redraw | abort
    """
    if step == "quit":
        return "abort"
    n, r = run_of(key)
    if r is None:
        return "redraw"
    folder = Path(r["artifact"])
    if step == "enter":
        for name in ("digest.md", "transcript.md"):
            if (folder / name).is_file():
                return "read %s" % (folder / name)
        notice("Nothing to read", ["Run %d kept no transcript file." % n])
        return "redraw"
    if step == "folder":
        return "folder %s" % folder
    asks = {"speakers": ("Do run %d over with speaker labels?", "--speakers"),
            "call": ("Do run %d over as a call, with a digest?", "--as call"),
            "voices": ("Recheck who is who in run %d?", "--as voices")}
    if step in asks:
        if step == "voices" and voices_of(result_of(r)) == "not labelled":
            notice("No voices to recheck", ["Run %d has no speaker labels yet." % n, "Press s to add them first."])
            return "redraw"
        heading, args = asks[step]
        lines = ["It uses the audio kept with the run.", "It takes %s and makes a new run." % minutes_for(r, step), "Run %d stays as it is." % n]
        if dialog(heading % n, lines, choice(("y", "do it", GREEN), ("n", "leave it", CYAN))) in ("y", "Y"):
            return "again %d %s" % (n, args)
    return "redraw"


# ── a live session ──

def live_state(folder: str) -> dict:
    try:
        return json.loads((Path(folder) / "state.json").read_text())
    except (OSError, ValueError):
        return {}


def live_lines(folder: str):
    try:
        raw = (Path(folder) / "lines.jsonl").read_text().splitlines()
    except OSError:
        return []
    out = []
    for i, line in enumerate(raw):
        try:
            out.append((i, json.loads(line)))
        except ValueError:
            continue
    return out


def live_rows(folder: str, room: int = 44):
    out = []
    # A mark is written the moment m is pressed, which can be before the sentence around it ends.
    for i, ln in sorted(live_lines(folder), key=lambda pair: (float(pair[1].get("start") or 0), pair[0])):
        if ln.get("mark"):
            out.append("%d\t%s%s  marked here%s" % (i, AMBER, clock(ln.get("start")), PLAIN))
            continue
        who = ln.get("speaker")
        tone = VOICE_TONES[int(who) % len(VOICE_TONES)] if str(who).isdigit() else DIM
        out.append("%d\t%s%s%s  %s%-3s%s %s" % (i, DIM, clock(ln.get("start")), PLAIN, tone, "S%s" % who if who is not None else "", PLAIN,
                                             fit(ln.get("text", ""), room)))
    st = live_state(folder)
    if st.get("interim"):
        out.append("now\t%s%s  now %s%s" % (DIM, clock(st.get("t")), fit(st["interim"], room - 4), PLAIN))
    return out or ["now\t%sNothing heard yet.%s" % (DIM, PLAIN)]


def live_header(folder: str):
    st = live_state(folder)
    spoken = [ln for _i, ln in live_lines(folder) if not ln.get("mark")]
    who = {ln.get("speaker") for ln in spoken if ln.get("speaker") is not None}
    counts = "%d line%s, %d voice%s." % (len(spoken), "" if len(spoken) == 1 else "s", len(who), "" if len(who) == 1 else "s")
    status = st.get("status", "starting")
    if status == "starting":
        return "Getting ready to listen."
    if status == "stopped":
        return "%sStopped at %s.%s %s" % (AMBER, clock(st.get("t")), PLAIN, counts)
    if st.get("paused"):
        return "%sPaused at %s.%s %s" % (AMBER, clock(st.get("t")), PLAIN, counts)
    return "%sListening%s for %s. %s" % (GREEN, PLAIN, clock(st.get("t")), counts)


def live_keys():
    return legend([[("space", "pause", AMBER), ("m", "mark here", CYAN), ("f", "follow", CYAN)],
                   [("s", "stop, save", GREEN), ("d", "digest", GREEN), ("q", "quit", CYAN)]], key_width=6)


def live_detail(folder: str, key: str):
    lines = dict(live_lines(folder))
    st = live_state(folder)
    if key == "now" or not key.isdigit() or int(key) not in lines:
        out = title("now") + ["state     %s" % ("paused" if st.get("paused") else st.get("status", "starting")),
                              "length    %s" % clock(st.get("t")),
                              "follow    %s" % ("on" if st.get("follow", True) else "off")]
        return out + section("being said") + wrap(st.get("interim") or "Nothing right now.")
    i = int(key)
    ln = lines[i]
    if ln.get("mark"):
        return title("a mark at %s" % clock(ln.get("start"))) + ["You pressed m here.", "", ""]
    who = ln.get("speaker")
    out = title("%s at %s" % ("Speaker %s" % who if who is not None else "A short line", clock(ln.get("start")))) + [
        "voice     %s" % ("a first guess, firmed up after you stop" if who is not None else "too short to tell"),
        "length    %.0f s" % max(0.0, float(ln.get("end", ln.get("start", 0))) - float(ln.get("start", 0))),
        "line      %d of %d" % (i + 1, len(lines))]
    out += section("the line") + wrap(ln.get("text", ""))
    before = [lines[j] for j in range(max(0, i - 2), i) if j in lines and not lines[j].get("mark")]
    after = [lines[j] for j in range(i + 1, i + 3) if j in lines and not lines[j].get("mark")]
    if before:
        out += section("before")
        for b in before:
            out += wrap(b.get("text", ""))
    if after:
        out += section("after")
        for a in after:
            out += wrap(a.get("text", ""))
    return out


def tell(folder: str, word: str) -> None:
    """Pass one word to the listening process, which reads this file as it runs."""
    with (Path(folder) / "control").open("a") as f:
        f.write(word + "\n")


def live_flow(folder: str, step: str):
    """One key on the live screen. Answers with what the screen does next: refresh, redraw, abort or digest."""
    st = live_state(folder)
    if step == "pause":
        tell(folder, "resume" if st.get("paused") else "pause")
        return "refresh"
    if step == "mark":
        tell(folder, "mark")
        return "refresh"
    if step == "follow":
        tell(folder, "follow")
        return "refresh"
    if step in ("stop", "digest", "quit"):
        if st.get("status") == "stopped":
            return "digest" if step == "digest" else "abort"
        heading = {"stop": "Stop listening and save?", "digest": "Stop listening and write a digest?", "quit": "Stop listening?"}[step]
        lines = ["%s heard so far. The recording and" % clock(st.get("t")), "the transcript are kept either way."]
        if step == "quit":
            pressed = dialog(heading, lines, choice(("y", "stop and save", GREEN), ("d", "digest", GREEN), ("n", "keep listening", CYAN)))
        else:
            pressed = dialog(heading, lines, choice(("y", "stop", GREEN), ("n", "keep listening", CYAN)))
        if pressed in ("y", "Y", "d", "D"):
            tell(folder, "stop")
            return "digest" if (step == "digest" or pressed in ("d", "D")) else "abort"
    return "redraw"


def live_tick(folder: str):
    """What the live screen does each time its list has loaded: keep up with the newest line, then look again."""
    st = live_state(folder)
    return "follow" if st.get("follow", True) else "stay"


def main(argv):
    word, rest = (argv[0] if argv else ""), argv[1:]
    plain = {"browse-rows": browse_rows, "browse-header": lambda: [browse_header()], "browse-keys": lambda: [browse_keys()],
             "live-keys": lambda: [live_keys()]}
    if word in plain:
        print("\n".join(plain[word]()))
        return 0
    if word == "browse-detail" and rest:
        print("\n".join(browse_detail(rest[0])))
        return 0
    if word == "browse-flow" and rest:
        print(browse_flow(rest[0], rest[1] if len(rest) > 1 else ""))
        return 0
    if word in ("live-rows", "live-header", "live-tick") and rest:
        got = {"live-rows": live_rows, "live-header": live_header, "live-tick": live_tick}[word](rest[0], *([max(20, int(rest[1]))] if word == "live-rows" and len(rest) > 1 and rest[1].isdigit() else []))
        print("\n".join(got) if isinstance(got, list) else got)
        return 0
    if word == "live-detail" and len(rest) >= 2:
        print("\n".join(live_detail(rest[0], rest[1])))
        return 0
    if word == "live-flow" and len(rest) >= 2:
        print(live_flow(rest[0], rest[1]))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
