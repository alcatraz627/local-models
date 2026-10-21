"""Send a prompt file to a Gemini model over the direct streaming API.

Streams thought summaries (when the model emits them) and the answer as they
arrive, to stderr and to <out>.live.md, and writes the final answer to <out>.
Usage: argon_direct.py <model> <prompt-file> <out.md>
"""
import json, os, sys, time, urllib.request

model, prompt_file, out = sys.argv[1], sys.argv[2], sys.argv[3]
key = next(l.split("=", 1)[1].strip().strip('"\'') for l in open(os.path.expanduser("~/.gemini/.env"))
           if l.startswith("GEMINI_API_KEY="))
body = {
    "contents": [{"role": "user", "parts": [{"text": open(prompt_file, encoding="utf-8").read()}]}],
    "generationConfig": {"thinkingConfig": {"includeThoughts": True}, "maxOutputTokens": 32768},
}
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse"
req = urllib.request.Request(url, data=json.dumps(body).encode(),
                             headers={"x-goog-api-key": key, "Content-Type": "application/json"})
t0 = time.time()
answer, usage, first = [], {}, None
with urllib.request.urlopen(req, timeout=1800) as resp, open(out + ".live.md", "w") as live:
    for raw in resp:
        line = raw.decode("utf-8", "replace").strip()
        if not line.startswith("data:"):
            continue
        chunk = json.loads(line[5:])
        usage = chunk.get("usageMetadata", usage)
        for part in (chunk.get("candidates") or [{}])[0].get("content", {}).get("parts", []):
            text = part.get("text", "")
            if first is None:
                first = time.time() - t0
                print(f"[first token after {first:.0f}s]", file=sys.stderr, flush=True)
            if part.get("thought"):
                live.write(f"\n> thinking: {text}\n"); print(f"\033[2m{text}\033[0m", file=sys.stderr, flush=True)
            else:
                answer.append(text); live.write(text)
            live.flush()
open(out, "w").write("".join(answer))
print(json.dumps({"seconds": round(time.time() - t0), "first_token_s": round(first or 0), "usage": usage}), flush=True)
