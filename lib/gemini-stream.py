#!/usr/bin/env python3
"""Turns gemini-cli's stream-json events into something a person can follow.

The gemini lane runs gemini-cli with `-o stream-json`, which emits one JSON event
per line: the tools it calls, their results, and the answer as it is written.
This script reads that stream and does one of three jobs:

  render  print each step as a short line while the call runs (for a terminal,
          or for `lm gemini watch` following a call started elsewhere)
  text    print only the final answer text
  meta    print one JSON object: the model that actually served the call,
          token counts, tool-call count, and the result status

gemini-cli does not put the model's private reasoning in the stream, so "render"
shows what the agent did (tools, files, searches) and the answer as it arrives,
not its thoughts. Lines that are not JSON (startup noise, errors) are passed
through by render and ignored by text and meta.
"""
import json
import os
import sys

DIM, CYAN, YEL, RED, RST = "\033[2m", "\033[36m", "\033[33m", "\033[31m", "\033[0m"
TICK = "\x00tick "   # a heartbeat line from follow(), never written by gemini-cli


def events(stream):
    for line in stream:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
            if isinstance(ev, dict) and "type" in ev:
                yield ev, line
                continue
        except ValueError:
            pass
        yield None, line


def short(value, n=90):
    s = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def render(stream, color):
    c = (lambda code, s: f"{code}{s}{RST}") if color else (lambda code, s: s)
    writing = False
    ticking = False
    for ev, raw in events(stream):
        if raw.startswith(TICK):
            secs = int(raw[len(TICK):])
            if color:   # one line, rewritten in place
                print(c(DIM, f"\r  … waiting on the model, {secs // 60}m{secs % 60:02d}s since the last event "), end="", flush=True)
                ticking = True
            elif secs % 60 == 0:
                print(f"  … waiting on the model, {secs // 60}m since the last event", flush=True)
            continue
        if ticking:
            print(flush=True)
            ticking = False
        if ev is None:
            if raw.startswith("[STARTUP]") or raw.startswith("Ripgrep is not available"):
                continue
            print(c(DIM, f"  · {short(raw)}"), flush=True)
            continue
        t = ev["type"]
        if t == "init":
            where = "direct API" if ev.get("transport") == "direct" else f"session {str(ev.get('session_id', ''))[:8]}"
            print(c(DIM, f"▸ {ev.get('model', '?')} · {where}"), flush=True)
        elif t == "tool_use":
            params = ev.get("parameters") or {}
            arg = next((params[k] for k in ("file_path", "dir_path", "path", "query", "url", "pattern", "command") if k in params), params)
            if writing:
                print(flush=True)
                writing = False
            print(c(CYAN, f"  → {ev.get('tool_name', 'tool')}  {short(arg)}"), flush=True)
        elif t == "thought":
            # only the direct-API transport sends these (thought summaries)
            if writing:
                print(flush=True)
                writing = False
            print(c(DIM, f"  … {short(ev.get('content', ''), 160)}"), flush=True)
        elif t == "tool_result":
            status = ev.get("status", "?")
            mark = c(DIM, "    ✓") if status == "success" else c(RED, f"    ✗ {status} {short(ev.get('error') or '')}")
            print(mark, flush=True)
        elif t == "message" and ev.get("role") == "assistant":
            if not writing:
                print(c(YEL, "  ✎ answer: "), end="", flush=True)
                writing = True
            print(c(DIM, ev.get("content", "").replace("\n", " ")), end="", flush=True)
        elif t == "result":
            if writing:
                print(flush=True)
                writing = False
            st = ev.get("stats") or {}
            served = ", ".join((st.get("models") or {}).keys()) or "?"
            print(c(DIM, f"■ {ev.get('status', '?')} · {st.get('tool_calls', 0)} tool calls · "
                         f"{st.get('input_tokens', '?')} in / {st.get('output_tokens', '?')} out · served by {served}"), flush=True)
        elif t == "error":
            print(c(RED, f"  ✗ {short(ev.get('message') or ev)}"), flush=True)


def text(stream):
    parts = []
    for ev, _ in events(stream):
        if ev and ev["type"] == "message" and ev.get("role") == "assistant":
            parts.append(ev.get("content", ""))
    sys.stdout.write("".join(parts).strip() + "\n" if parts else "")


def meta(stream):
    out = {"status": None, "served_by": [], "tool_calls": 0, "input_tokens": None, "output_tokens": None, "events": 0}
    for ev, _ in events(stream):
        if not ev:
            continue
        out["events"] += 1
        if ev["type"] == "result":
            st = ev.get("stats") or {}
            out.update(status=ev.get("status"), served_by=list((st.get("models") or {}).keys()),
                       tool_calls=st.get("tool_calls", 0), input_tokens=st.get("input_tokens"),
                       output_tokens=st.get("output_tokens"))
    print(json.dumps(out))


def follow(path, pid):
    """Yield a growing stream file's lines until the call ends (a result event, or
    the writing process is gone and nothing new has arrived)."""
    import os, time
    def alive():
        try:
            os.kill(pid, 0)
            return True
        except (OSError, TypeError):
            return False
    with open(path, encoding="utf-8", errors="replace") as f:
        idle = 0.0
        last_event = os.path.getmtime(path)   # watch may start long after the last event
        caught_up = False
        while True:
            line = f.readline()
            if line:
                idle = 0.0
                if caught_up:   # lines replayed at start are not new events
                    last_event = time.time()
                yield line
                if '"type":"result"' in line.replace(" ", ""):
                    return
                continue
            caught_up = True
            if not alive() and idle > 1.0:
                return
            time.sleep(0.25)
            idle += 0.25
            # The model sends nothing while it thinks; a tick every 5s shows
            # the call is alive and how long it has been quiet.
            if idle % 5 == 0:
                yield f"{TICK}{int(time.time() - last_event)}"


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "render"
    if mode == "follow":
        # follow FILE PID: render a call that is still running elsewhere.
        # Ctrl-C stops watching; the call itself keeps running.
        try:
            render(follow(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None),
                   color=sys.stdout.isatty() and not os.environ.get("NO_COLOR"))
        except KeyboardInterrupt:
            print("\n  · stopped watching; the call is still running", flush=True)
            sys.exit(130)
        sys.exit(0)
    src = open(sys.argv[2], encoding="utf-8", errors="replace") if len(sys.argv) > 2 else sys.stdin
    if mode == "render":
        render(src, color=(sys.stdout.isatty() and not os.environ.get("NO_COLOR")) or "--color" in sys.argv)
    elif mode == "text":
        text(src)
    elif mode == "meta":
        meta(src)
    else:
        sys.exit(f"usage: gemini-stream.py render|text|meta [file]")
