#!/usr/bin/env python3
"""Model-free drift check: lib/verbs.toml is the one source for everything lm says about itself.

Fails when the registry, the screens, the agent menu, `lm how`, the generated completion, man,
tldr and doc files, or the JSON error envelopes disagree. No model runs and nothing leaves the Mac.
Exit 0 = every check passed.

    .venv/bin/python probe/fixtures/verbs-drift.py
"""
import json
import os
import pty
import re
import select
import shlex
import subprocess
import sys
import tempfile
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LM = os.path.join(ROOT, "bin", "lm")
Q = os.path.join(ROOT, "bin", "q")
SEE = os.path.join(ROOT, "bin", "see")
VERBS_PY = os.path.join(ROOT, "lib", "verbs.py")
REGISTRY = os.path.join(ROOT, "lib", "verbs.toml")
CHECKS = []

REQUIRED = ["name", "kind", "summary", "usage", "examples", "inputs", "output", "exit_codes",
            "cost_tier", "leaves_mac", "side_effects", "keywords", "see_also"]
SUITE_BINS = {"lm", "q", "see", "review", "warm", "imagine", "probe"}
EXTERNAL_OK = {"rg", "git", "cat", "pbpaste", "kubectl", "screencapture", "glow", "bash", "UI_DEFAULT_MLX=0",
               "LM_PROGRESS=1", ".venv/bin/python"}
SEE_SUBS = {"diff", "count", "odd", "latest", "paste", "more", "show", "history", "open", "reshoot", "help"}
Q_SUBS = {"show", "history", "intents", "check", "help"}


def check(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))


def run(argv, env_extra=None, timeout=60, stdin=None):
    env = dict(os.environ, NO_COLOR="1", LM_HINTS="0")
    env.update(env_extra or {})
    p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=env, stdin=stdin or subprocess.DEVNULL)
    return p.returncode, p.stdout, p.stderr


def run_pty(argv, timeout=30):
    """Run argv attached to a pseudo-terminal, colour allowed; return (rc, output)."""
    env = dict(os.environ, TERM="xterm-256color")
    env.pop("NO_COLOR", None)
    env["LM_HINTS"] = "0"
    m, s = pty.openpty()
    p = subprocess.Popen(argv, stdin=s, stdout=s, stderr=s, env=env, close_fds=True)
    os.close(s)
    out = b""
    while True:
        r, _, _ = select.select([m], [], [], timeout)
        if not r:
            break
        try:
            chunk = os.read(m, 4096)
        except OSError:
            break
        if not chunk:
            break
        out += chunk
    p.wait(timeout=timeout)
    os.close(m)
    return p.returncode, out.decode("utf-8", "replace")


# ── 1. the registry parses and every job is complete ─────────────────────────────────
reg = None
try:
    with open(REGISTRY, "rb") as f:
        reg = tomllib.load(f)
    check("registry parses", True)
except Exception as e:  # missing file counts as red
    check("registry parses", False, str(e))

jobs = {}
if reg:
    for j in reg.get("job", []):
        jobs[j.get("name", "?")] = j
    check("registry has jobs", len(jobs) >= 30, f"{len(jobs)} jobs")
    for name, j in jobs.items():
        miss = [k for k in REQUIRED if k not in j]
        check(f"job {name}: required fields", not miss, f"missing {miss}")
        check(f"job {name}: examples are {{cmd, says}}",
              j.get("examples") and all("cmd" in e and "says" in e for e in j["examples"]))
    for want in ("ask cmd read diff doc again find review status fast count web failed more gemini fleet rag "
                 "index imagine probe bench ui-verify timeline last models doctor examples").split():
        check(f"job {want} is registered", want in jobs)

names = set(jobs)
aliases = {a: n for n, j in jobs.items() for a in j.get("aliases", [])}
verbs_known = names | set(aliases) | {"q", "see", "warm", "how", "version", "opencode"}

# ── 2. the screens and the registry name the same jobs ──────────────────────────────
rc, front, _ = run([LM])
check("lm (no tty) exits 0", rc == 0, f"rc={rc}")
shown = set()
for line in front.splitlines():
    m = re.match(r'^  lm (\S+)', line)
    if m:
        w = m.group(1)
        shown.add("ask" if w.startswith('"') else w)
for w in shown:
    check(f"screen verb 'lm {w}' is in the registry", w in verbs_known)
if reg:
    scr = reg.get("screens", {})
    for n in scr.get("front_jobs", []) + scr.get("front_handy", []):
        check(f"registry job {n} is on the lm screen", n in shown or aliases.get(n) in shown)
    for n in scr.get("front_jobs", []) + scr.get("front_handy", []) + scr.get("more_order", []) + scr.get("help_index", []):
        check(f"screen list entry {n} exists", n in names)
rc, more, _ = run([LM, "more"])
check("lm more (no tty) exits 0", rc == 0)
for line in more.splitlines():
    m = re.match(r'^  lm (\S+)', line)
    if m:
        check(f"more verb 'lm {m.group(1)}' is in the registry", m.group(1) in verbs_known)

# ── 3. every example starts with a real verb ──────────────────────────────────────────
intents = {f[:-5] for f in os.listdir(os.path.join(ROOT, "intents")) if f.endswith(".toml")}
for name, j in jobs.items():
    for e in j.get("examples", []):
        cmd = e["cmd"]
        try:
            toks = shlex.split(cmd)
        except ValueError:
            check(f"example parses: {cmd}", False, "unbalanced quotes")
            continue
        first = toks[0] if toks else ""
        ok = first in SUITE_BINS or first in EXTERNAL_OK
        if ok and first == "lm" and len(toks) > 1:
            t2 = toks[1]
            ok = t2 in verbs_known or t2.startswith("-") or " " in t2 or not re.match(r"^[a-z][a-z-]*$", t2)
            # a bare lowercase word after lm must be a verb, never a typo
        if ok and first == "see" and len(toks) > 1 and re.match(r"^[a-z][a-z-]*$", toks[1]):
            ok = toks[1] in SEE_SUBS
        if ok and first == "q" and len(toks) > 1 and re.match(r"^[a-z][a-z-]*$", toks[1]):
            ok = toks[1] in intents or toks[1] in Q_SUBS
        check(f"example verb ok: {cmd}", ok)

# ── 4. every verb answers -h with exit 0 and writes no history ──────────────────────
def snapshot():
    out = {}
    for d in ("logs", "outputs"):
        base = os.path.join(ROOT, d)
        if os.path.isdir(base):
            for fn in os.listdir(base):
                p = os.path.join(base, fn)
                if os.path.isfile(p):
                    st = os.stat(p)
                    out[p] = (st.st_size, st.st_mtime_ns)
    return out


before = snapshot()
for name, j in jobs.items():
    kind = j.get("kind")
    if kind == "topic":
        argv = [LM, "help", name]
    else:
        argv = [LM, name, "-h"]
    rc, _, err = run(argv, timeout=30)
    check(f"{' '.join(argv[1:])} exits 0", rc == 0, f"rc={rc} {err[:120]}")
after = snapshot()
check("-h left logs/ and outputs/ untouched", before == after,
      str([k for k in set(before) | set(after) if before.get(k) != after.get(k)][:3]))

# ── 5. generated files equal a fresh generation ─────────────────────────────────────
with tempfile.TemporaryDirectory(prefix="verbs-gen.") as tmp:
    rc, _, err = run([sys.executable, VERBS_PY, "gen", "--out", tmp])
    check("gen --out succeeds", rc == 0, err[:200])
    wanted = []
    for dp, _, fns in os.walk(tmp):
        for fn in fns:
            wanted.append(os.path.relpath(os.path.join(dp, fn), tmp))
    check("gen writes completion, man, tldr and a doc block",
          sum(w.startswith("share/zsh/_") for w in wanted) == 4
          and sum(w.startswith("share/man/man1/") for w in wanted) == 4
          and sum(w.startswith("share/tldr/") for w in wanted) == 4
          and "_docblock.md" in wanted, str(sorted(wanted))[:200])
    for rel in wanted:
        fresh = open(os.path.join(tmp, rel), encoding="utf-8").read()
        if rel == "_docblock.md":
            doc = open(os.path.join(ROOT, "docs", "CAPABILITIES.md"), encoding="utf-8").read()
            m = re.search(r"<!-- verbs:begin -->\n(.*?)<!-- verbs:end -->", doc, re.S)
            check("docs/CAPABILITIES.md block equals a fresh generation", m and m.group(1) == fresh,
                  "run scripts/gen-verbs.sh")
            continue
        p = os.path.join(ROOT, rel)
        disk = open(p, encoding="utf-8").read() if os.path.exists(p) else None
        check(f"{rel} equals a fresh generation", disk == fresh, "run scripts/gen-verbs.sh")

# ── 6. the agent menu validates against the registry ────────────────────────────────
rc, out, err = run([LM, "--capabilities", "--json"])
try:
    cap = json.loads(out)
except Exception:
    cap = None
check("lm --capabilities --json is JSON", cap is not None, err[:120])
if cap and reg:
    check("capabilities: version and conventions", "version" in cap and
          {"json_flag", "exit_codes", "history_scope", "no_tty_behaviour"} <= set(cap.get("conventions", {})))
    check("capabilities: jobs equal the registry", [j["name"] for j in cap["jobs"]] == [j["name"] for j in reg["job"]])
    check("capabilities: each job carries every registry field",
          all(all(k in cj for k in REQUIRED) for cj in cap["jobs"]))
rc, out, _ = run([LM, "--capabilities", "read", "--json"])
check("lm --capabilities <job> --json is one job", rc == 0 and json.loads(out).get("name") == "read" if rc == 0 else False)
rc, out, _ = run([LM, "--capabilities"])
check("lm --capabilities (text) lists jobs", rc == 0 and "read" in out and "\033" not in out)

# ── 7. lm how finds the job without a model ─────────────────────────────────────────
def how(q):
    rc, out, err = run([LM, "how", "--json", "--no-model", q])
    try:
        return rc, json.loads(out)
    except Exception:
        return rc, {"_raw": out + err}


# twelve phrasings taken from the registry's own first keywords
picked = 0
if reg:
    for n, j in jobs.items():
        if j.get("kind") == "topic" or not j.get("keywords") or n in ("more",):
            continue
        if picked >= 12:
            break
        q = j["keywords"][0]
        rc, r = how(q)
        check(f"how '{q}' -> {n}", rc == 0 and r.get("job") in (n, aliases.get(n)) and r.get("matched_by") == "keywords",
              str(r)[:160])
        picked += 1
    check("how: at least 12 keyword phrasings checked", picked >= 12, str(picked))
NATURAL = [
    ("text from my last screenshot", "read", "lm read latest"),
    ("redo that on a bigger model", "again", "lm again --big"),
    ("what is using memory", "status", None),
    ("what changed between these two screenshots", "diff", None),
    ("find the answer I got yesterday about docker", "find", None),
    ("keep the model loaded so answers are instant", "fast", None),
]
for phrase, want, cmd in NATURAL:
    rc, r = how(phrase)
    ok = rc == 0 and r.get("job") == want and (cmd is None or r.get("command") == cmd)
    check(f"how '{phrase}' -> {want}", ok, str(r)[:200])
rc, r = how("search the web for the current node version")
check("how: a cloud lane only when the words ask for it", rc == 0 and r.get("job") in ("web",), str(r)[:160])
rc, r = how("redo that with a stronger answer")
check("how: never a cloud lane unprompted", rc == 0 and "--web" not in r.get("command", ""), str(r)[:160])
rc, r = how("zzz qqq xxyzzy")
check("how --no-model with no match exits 12 with code no_match", rc == 12 and r.get("code") == "no_match", str(r)[:160])

# ── 8. a --json error carries the fix ───────────────────────────────────────────────
for label, argv in (("q", [Q, "--json", "--ctx", "/nonexistent/none.txt", "hi"]),
                    ("see", [SEE, "--json", "/nonexistent/none.png"])):
    rc, out, _ = run(argv)
    try:
        e = json.loads(out.strip().splitlines()[-1])
    except Exception:
        e = {}
    check(f"{label} --json error has remedy and next",
          e.get("ok") is False and isinstance(e.get("remedy"), str) and e["remedy"] and "next" in e, str(e)[:200])
    check(f"{label} --json error keeps code and message", "code" in e and "message" in e)

# ── 9. the hint table lives in the registry ─────────────────────────────────────────
rc, out, _ = run([sys.executable, VERBS_PY, "hint", "small_answer"])
check("hint small_answer is lm again --big", rc == 0 and "lm again --big" in out, out[:80])

# ── 10. colour is kept on a terminal and absent when piped ──────────────────────────
for argv in ([LM], [LM, "help", "read"], [LM, "more"]):
    rc, out = run_pty(argv)
    check(f"{' '.join(argv[1:]) or 'lm'}: coloured on a terminal", rc == 0 and out.count("\033[") >= 8, f"{out.count(chr(27))} escapes")
rc, out, _ = run([LM], env_extra={"NO_COLOR": "1"})
check("lm piped: no escape codes", "\033" not in out)

fails = [c for c in CHECKS if not c[1]]
for name, ok, detail in CHECKS:
    print(("PASS " if ok else "FAIL ") + name + ("" if ok or not detail else f"  [{detail}]"))
print(f"{len(CHECKS) - len(fails)}/{len(CHECKS)} checks passed")
sys.exit(1 if fails else 0)
