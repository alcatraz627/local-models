#!/usr/bin/env python3
"""Answer one gemini prompt over Google's API directly, without gemini-cli.

The gemini lane uses this when the piped context is large: gemini-cli once sat
16 minutes on a 1.9 MB stdin pack without sending it, while the API answered the
same pack in under two minutes. It also names the model that really served the
call, which gemini-cli sometimes does not honor.

Usage: gemini-direct.py <model> <prompt>   (context, if any, on stdin)

Writes gemini-cli-shaped stream-json events to stdout (init, thought, message,
result, error), so lib/gemini-stream.py renders, follows and reads it unchanged.
Exit codes: 0 answered, 10 API or network error, 11 auth refused.
The key comes from GEMINI_API_KEY, else ~/.gemini/.env; it is never printed.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request


def emit(ev):
    sys.stdout.write(json.dumps(ev, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def api_key():
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    try:
        with open(os.path.expanduser("~/.gemini/.env")) as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    return ""


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: gemini-direct.py <model> <prompt>  (context on stdin)")
    model, prompt = sys.argv[1], sys.argv[2]
    context = "" if sys.stdin.isatty() else sys.stdin.read()
    key = api_key()
    if not key:
        emit({"type": "error", "message": "auth: no GEMINI_API_KEY in the environment or ~/.gemini/.env"})
        return 11
    text = f"{context}\n\n{prompt}" if context else prompt
    body = {
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {"thinkingConfig": {"includeThoughts": True}, "maxOutputTokens": 32768},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse"
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    emit({"type": "init", "model": model, "session_id": "", "transport": "direct"})
    t0 = time.time()
    usage, served, finish = {}, "", ""
    try:
        with urllib.request.urlopen(req, timeout=1800) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                chunk = json.loads(line[5:])
                usage = chunk.get("usageMetadata", usage)
                served = chunk.get("modelVersion", served)
                cand = (chunk.get("candidates") or [{}])[0]
                finish = cand.get("finishReason", finish)
                for part in cand.get("content", {}).get("parts", []):
                    if part.get("thought"):
                        emit({"type": "thought", "content": part.get("text", "")})
                    elif part.get("text"):
                        emit({"type": "message", "role": "assistant", "content": part["text"], "delta": True})
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e).get("error", {}).get("message", f"HTTP {e.code}")
        except Exception:
            msg = f"HTTP {e.code}"
        auth = e.code in (401, 403)
        emit({"type": "error", "message": f"{'auth: ' if auth else ''}HTTP {e.code}: {msg}"})
        emit({"type": "result", "status": "error", "stats": {}})
        return 11 if auth else 10
    except (OSError, ValueError) as e:
        emit({"type": "error", "message": f"network or stream error: {e}"})
        emit({"type": "result", "status": "error", "stats": {}})
        return 10
    ok = finish in ("", "STOP")
    emit({"type": "result", "status": "success" if ok else f"finish:{finish}",
          # the API's modelVersion names the serving model; without it, say so
          "stats": {"models": {served or f"{model} (unreported)": {}}, "tool_calls": 0,
                    "input_tokens": usage.get("promptTokenCount"),
                    "output_tokens": usage.get("candidatesTokenCount"),
                    "thought_tokens": usage.get("thoughtsTokenCount"),
                    "duration_ms": int((time.time() - t0) * 1000), "transport": "direct"}})
    return 0


if __name__ == "__main__":
    sys.exit(main())
