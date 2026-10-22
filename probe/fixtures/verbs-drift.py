#!/usr/bin/env python3
"""Model-free drift check: lib/verbs.toml is the one source for everything lm says about itself.

Fails when the registry, the screens, the agent menu, `lm how`, the generated completion, man,
tldr and doc files, or the JSON error envelopes disagree. No model runs and nothing leaves the Mac.
Exit 0 = every check passed.

    .venv/bin/python probe/fixtures/verbs-drift.py
"""
import contextlib
import importlib.util
import io
import json
import os
import pty
import re
import select
import shlex
import subprocess
import sys
import tempfile
import time
import tomllib

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LM = os.path.join(ROOT, "bin", "lm")
Q = os.path.join(ROOT, "bin", "q")
SEE = os.path.join(ROOT, "bin", "see")
WARM = os.path.join(ROOT, "bin", "warm")
IMAGINE = os.path.join(ROOT, "bin", "imagine")
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


def run(argv, env_extra=None, timeout=60, stdin=None, keep_colour=False):
    env = dict(os.environ, NO_COLOR="1", LM_HINTS="0")
    if keep_colour:
        env.pop("NO_COLOR", None)
        env["TERM"] = "xterm-256color"
    env.update(env_extra or {})
    p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=env, stdin=stdin or subprocess.DEVNULL)
    return p.returncode, p.stdout, p.stderr


def run_pty(argv, timeout=30, env_extra=None):
    """Run argv attached to a pseudo-terminal, colour allowed; return (rc, output)."""
    env = dict(os.environ, TERM="xterm-256color")
    env.pop("NO_COLOR", None)
    env["LM_HINTS"] = "0"
    env.update(env_extra or {})
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


def load_verbs():
    spec = importlib.util.spec_from_file_location("verbs_under_test", VERBS_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def inproc(fn, *args):
    """Call fn with stdout and stderr captured; returns (result, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        res = fn(*args)
    return res, out.getvalue(), err.getvalue()


# 1. the registry parses and every job is complete
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

# 2. the screens and the registry name the same jobs
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

# 3. every example starts with a real verb
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

# 4. every verb answers -h with exit 0 and writes no history
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
for argv in ([WARM, "on", "-h"], [Q, "show", "-h"], [IMAGINE, "refine", "-h"], [LM, "warm", "on", "-h"]):
    rc, _, err = run(argv, timeout=30)
    check(f"{' '.join(os.path.basename(a) for a in argv[:3])} -h exits 0", rc == 0, f"rc={rc} {err[:120]}")
after = snapshot()
check("-h left logs/ and outputs/ untouched", before == after,
      str([k for k in set(before) | set(after) if before.get(k) != after.get(k)][:3]))

# 5. generated files equal a fresh generation
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

# 6. the agent menu validates against the registry
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

# 7. lm how finds the job without a model
def how(q, *extra, **kw):
    rc, out, err = run([LM, "how", "--json", "--no-model", *extra, q], **kw)
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

# natural phrasings: (words, the jobs that are right or None for "no job matches", the exact command or None)
HOW_TABLE = [('read the text in my last screenshot', ('read',), 'lm read latest'), ('whats on my clipbaord image', ('read',), 'lm read paste'), ('ocr this', ('read',), 'see shot.png --ocr'), ('what is eating my RAM', ('status',), None), ('my mac is slow', ('status',), None), ('redo that with a better model', ('again',), 'lm again --big'), ('try again but smarter', ('again',), None), ('compare two screenshots', ('diff',), None), ('what changed between these two images', ('diff',), None), ('summarize this pdf', ('doc',), None), ('search my files for the invoice', None, None), ('review my git diff', ('review',), 'lm review'), ('how many tokens is this file', ('doc',), 'q --preflight --ctx report.pdf'), ('how many tokens is this file but not on the web', ('doc',), 'q --preflight --ctx report.pdf'), ('explain this error', ('ask', 'failed'), None), ('delete all my files', None, None), ('generate an image of a cat', ('imagine',), 'imagine "a cozy reading nook"'), ('send an email to bob', None, None), ('run a shell command for me', ('cmd',), None), ('unload all models', ('fast',), 'warm off all'), ('free up memory by stopping models', ('fast',), 'lm fast off'), ('search the web for rust news', ('web',), None), ('do not use the web, tell me what 2+2 is', ('ask',), None), ('without gemini, summarize this big folder', ('doc', 'fleet', 'rag'), None), ('sumarize my clipbord', ('ask',), None), ('screnshot text', ('read',), None), ('read screenshot and then redo it bigger', ('read',), None), ('what did the last call say', ('last',), 'lm last'), ('why did my last command fail', ('failed',), None), ('-rf /', None, None), ('; rm -rf ~ #', None, None), ('$(touch /private/tmp/claude-501/pwned1)', None, None), ('how fast is the model', ('bench',), None), ('benchmark the models', ('bench',), 'lm bench quick'), ('check the ui against the design', ('ui-verify',), None), ('timeline of my calls', ('timeline',), None), ('which models are installed', ('models',), 'lm models'), ('is everything healthy', ('doctor',), 'lm doctor'), ('ask a question', ('ask',), None), ('make a command line for listing big files', ('cmd',), None), ('use gemini to read my whole repo', ('gemini',), None), ('run many prompts in parallel', ('fleet',), None), ('index my notes for search', ('rag',), None), ('ask my notes', ('rag',), None), ('tell me a joke', ('ask',), None), ('translate to french', None, None), ('review my uncommitted changes', ('review',), 'lm review'), ('build a search by meaning index of my docs', ('rag',), 'lm rag index docs/'), ('start opencode', ('opencode',), 'lm opencode'), ('what is installed and what is running and is it healthy', ('status', 'doctor', 'models'), None), ('commit message from my diff', ('ask',), 'git diff | q commit'), ('keep the model warm for an hour', ('fast',), 'lm fast 1h'), ('how many red squares are in this image', ('count',), None), ('the odd one out in this grid', ('count',), None), ('whats the newest node version', ('ask',), None), ('tell me the latest news but keep it local', ('ask',), None), ('read this image offline', ('read',), None), ('internet', ('web',), None), ('online ocr of my screenshot', ('read',), None), ('show errors', ('failed',), None), ('quick summary of the last thing I ran', ('last',), None), ('why is it so slow today', None, None), ('RM -RF EVERYTHING', None, None), ('find where fleet_worker is defined in the repo', ('index',), 'lm index find fleet_worker'), ('weather today', ('ask',), None), ('text from my last screenshot', ('read',), 'lm read latest'), ('redo that on a bigger model', ('again',), 'lm again --big'), ('what is using memory', ('status',), None), ('find the answer I got yesterday about docker', ('find',), None), ('keep the model loaded so answers are instant', ('fast',), None)]
for phrase, want, cmd in HOW_TABLE:
    rc, r = how(phrase)
    if want is None:
        ok = rc == 12 and r.get("code") == "no_match"
    else:
        ok = rc == 0 and r.get("job") in want and (cmd is None or r.get("command") == cmd) and r.get("matched_by") == "keywords"
    check(f"how '{phrase}' -> {'/'.join(want) if want else 'no match'}", ok, str(r)[:200])

# a cloud job needs a cloud word that is not negated
cloud_jobs = {n for n, j in jobs.items() if j.get("leaves_mac")}
for n in sorted(cloud_jobs):
    check(f"every example of the cloud job {n} is marked cloud, so the example filter alone keeps it out", all(e.get("cloud") for e in jobs[n]["examples"]))
NEGATED = ['how many tokens is this file but not on the web', 'do not use the web, tell me what 2+2 is', 'without gemini, summarize this big folder', 'tell me the latest news but keep it local']
for phrase in NEGATED:
    rc, r = how(phrase)
    check(f"how never picks a cloud lane against the words: '{phrase}'",
          rc == 0 and r.get("job") not in cloud_jobs and "--web" not in r.get("command", "") and "gemini" not in r.get("command", ""),
          str(r)[:200])
rc, r = how("search the web for the current node version")
check("how: a cloud lane when the words ask for it", rc == 0 and r.get("job") == "web", str(r)[:160])
rc, r = how("use gemini to read my whole repo")
check("how: gemini when the words ask for it", rc == 0 and r.get("job") == "gemini", str(r)[:160])
rc, r = how("redo that with a stronger answer")
check("how: never a cloud lane unprompted", rc == 0 and "--web" not in r.get("command", ""), str(r)[:160])
rc, r = how("zzz qqq xxyzzy")
check("how --no-model with no match exits 12 with code no_match", rc == 12 and r.get("code") == "no_match", str(r)[:160])
rc, r = how("whats the newest node version")
alt_cloud = [a for a in r.get("alternatives", []) if a.get("leaves_mac")]
check("how: fresh facts keep the top answer local and mark the web as an alternative",
      rc == 0 and r.get("job") == "ask" and len(alt_cloud) == 1 and "--web" in alt_cloud[0]["command"], str(r)[:240])
# every cloud job's own keywords, minus the cloud word itself, must not reach it
if reg:
    for n in sorted(cloud_jobs):
        for kw in jobs[n]["keywords"]:
            if set(re.findall(r"[a-z]+", kw.lower())) & set(reg["how"]["cloud_words"]):
                continue
            rc, r = how(kw)
            check(f"how '{kw}' (a {n} keyword without a cloud word) stays off the cloud lane", r.get("job") != n, str(r)[:160])
# unknown flags and empty requests are usage errors
for argv, label in (([LM, "how", "--jsno", "x"], "unknown flag"), ([LM, "how"], "empty request")):
    rc, out, err = run(argv)
    check(f"lm how: {label} exits 2", rc == 2, f"rc={rc}")
rc, out, err = run([LM, "how", "--json"])
check("lm how --json with no request prints the envelope", rc == 2 and json.loads(out or "{}").get("code") == "invalid_args", out[:120])

# --go runs only what the registry lists in a job's go field, as an argument list, never a shell string
V = load_verbs()
regV = V.load()
jobsV = {j["name"]: j for j in regV["job"]}
for n, j in jobsV.items():
    for g in V.go_list(j):
        try:
            argv0 = shlex.split(g)[0]
        except ValueError:
            argv0 = ""
        check(f"go command for {n} is a plain command from the suite: {g}",
              argv0 in SUITE_BINS and not re.search(r"[<>|;&$`\"']", g) and not re.search(r"\.(png|pdf|csv|xlsx)\b", g), g)
        check(f"go command for {n} is one of its examples: {g}", g in [e["cmd"] for e in j["examples"]])
calls = []


class Done:
    returncode = 0


real_run = V.subprocess.run
V.subprocess.run = lambda argv, **kw: (calls.append((argv, kw)) or Done())
try:
    calls.clear()
    rc, o, e = inproc(V.cmd_how, regV, ["--go", "--no-model", "what is using memory"])
    check("--go runs a go command as an argument list, without a shell",
          rc == 0 and len(calls) == 1 and isinstance(calls[0][0], list) and not calls[0][1].get("shell")
          and calls[0][0][-1:] == ["status"], str(calls)[:200])
    refused = 0
    for n, j in jobsV.items():
        if j["kind"] == "tool" or V.go_list(j):
            continue
        phrase = j["keywords"][0]
        ans = V.how_answer(regV, phrase)
        if not ans or ans["job"] != n:
            continue
        calls.clear()
        rc, o, e = inproc(V.cmd_how, regV, ["--go", "--no-model", phrase])
        refused += 1
        check(f"--go never runs {n}, which has no go field", rc == 2 and not calls and "lm how:" in e, f"rc={rc} calls={calls} {e[:100]}")
    check("--go refusal was checked for at least 10 jobs", refused >= 10, str(refused))
    calls.clear()
    rc, o, e = inproc(V.cmd_how, regV, ["--go", "--no-model", "summarize this pdf"])
    check("--go on a command that needs input says what to fill in", rc == 2 and "fill in the file path and run it" in e and not calls, e[:160])
    rc, o, e = inproc(V.cmd_how, regV, ["--go", "--json", "--no-model", "summarize this pdf"])
    check("--go with --json is a usage error with the envelope on stdout",
          rc == 2 and json.loads(o).get("code") == "invalid_args" and not calls, o[:160])
finally:
    V.subprocess.run = real_run

# the model fallback names a job; the command is always the registry's
asked = []


def stub(reply):
    def fake(prompt, schema):
        asked.append(schema)
        return reply
    return fake


real_ask = V.ask_small
try:
    cases = (
        ("a shell string instead of a job name", {"ok": True, "data": {"job": "status; touch /private/tmp/claude-501/pwned-fixture"}}),
        ("a cloud job nobody asked for", {"ok": True, "data": {"job": "gemini"}}),
        ("a job that does not exist", {"ok": True, "data": {"job": "nosuchjob"}}),
        ("no data at all", {"ok": True, "text": "status"}),
        ("a tool, not a job", {"ok": True, "data": {"job": "q"}}),
    )
    for label, reply in cases:
        V.ask_small = stub(reply)
        try:
            res = V.how_model(regV, "my laptop fan is loud")[0]
        except Exception as ex:
            res = f"raised {type(ex).__name__}"
        check(f"model path rejects {label}", res is None, str(res)[:160])
    V.ask_small = stub({"ok": True, "data": {"job": "status", "command": "evil-command --now"}})
    res = V.how_model(regV, "my laptop fan is loud")[0]
    check("model path shows the registry command, never the model's text",
          res and res["command"] == "lm status" and res["matched_by"] == "model", str(res)[:160])
    check("model path asks with an enum of job names that holds no cloud job",
          asked and set(asked[-1]["properties"]["job"]["enum"]) == {j["name"] for j in regV["job"] if j["kind"] != "tool" and not j["leaves_mac"]},
          str(asked[-1])[:160] if asked else "no call")
    V.ask_small = stub({"ok": True, "data": {"job": "web"}})
    res = V.how_model(regV, "search the web for my laptop fan")[0]
    check("model path may pick a cloud job when the words ask for the web", res and res["job"] == "web", str(res)[:120])
finally:
    V.ask_small = real_ask

# lm how is plain when piped, whatever the environment says
for env_extra, label in (({}, "piped"), ({"CLICOLOR_FORCE": "1"}, "piped with CLICOLOR_FORCE=1")):
    rc, out, err = run([LM, "how", "--no-model", "text from my last screenshot"], env_extra=env_extra, keep_colour=True)
    check(f"lm how {label}: no escape codes", rc == 0 and "\033" not in out and "\033" not in err, repr(out[:80]))
rc, out = run_pty([LM, "how", "--no-model", "text from my last screenshot"])
check("lm how on a terminal: coloured", rc == 0 and out.count("\033[") >= 3, f"{out.count(chr(27))} escapes")
rc, out = run_pty([LM, "how", "--no-model", "--go", "summarize this pdf"])
check("lm how --go refusal on a terminal picks out the part to fill in", rc == 2 and "\033[1;33mreport.pdf" in out, repr(out[:200]))

# 8. a --json error carries the fix
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

libtext = open(os.path.join(ROOT, "bin", "_lib.sh"), encoding="utf-8").read()
timeline = re.findall(r'^\s{6}(\w+): "(.*?)",?$', libtext.split("JQ_REMEDY='def remedy")[1].split("}[$c]")[0], re.M)
check("timeline remedy table is readable", len(timeline) >= 10, str(len(timeline)))
if reg:
    for code, text in timeline:
        check(f"timeline remedy for {code} matches the registry", reg["remedies"].get(code, {}).get("remedy") == text,
              str(reg["remedies"].get(code, {}).get("remedy")))

# 9. the hint table lives in the registry, and a hint is never written to stdout
rc, out, err = run([sys.executable, VERBS_PY, "hint", "small_answer"])
check("hint small_answer is lm again --big, on stderr", rc == 0 and "lm again --big" in err and out == "", f"out={out[:40]!r} err={err[:60]!r}")
for key in regV["hints"]:
    _, o, e = inproc(lambda: V.emit_hint(regV, key, False, img="shot.png"))
    check(f"emit_hint {key}: stderr only", o == "" and e.startswith("next: ") and e.endswith("\n"), f"out={o[:40]!r} err={e[:60]!r}")
check("emit_hint with an unknown key prints nothing", inproc(V.emit_hint, regV, "nosuchhint")[1:] == ("", ""))
qtext = open(Q, encoding="utf-8").read()
qseg = qtext.split("hint_key = None")[1].split("# The lease nudge")[0]
check("q writes its hint through the emitter, not to stdout",
      "verbs.emit_hint(" in qseg and "sys.stdout" not in qseg and "print(" not in qseg, qseg[-200:])
check("q does not repeat the exact --max-ctx line it already prints", 'hint_key = "truncated"' not in qseg)
seetext = open(SEE, encoding="utf-8").read()
check("see sends its hint to stderr",
      any("lm_verbs hint low_confidence" in l and l.rstrip().endswith(">&2 || true") for l in seetext.splitlines()))

# 10. colour is kept on a terminal and absent when piped
for argv in ([LM], [LM, "help", "read"], [LM, "more"]):
    rc, out = run_pty(argv)
    check(f"{' '.join(argv[1:]) or 'lm'}: coloured on a terminal", rc == 0 and out.count("\033[") >= 8, f"{out.count(chr(27))} escapes")
rc, out, _ = run([LM], env_extra={"NO_COLOR": "1"})
check("lm piped: no escape codes", "\033" not in out)

with tempfile.TemporaryDirectory(prefix="verbs-shots.") as shots:
    open(os.path.join(shots, "Screenshot test.png"), "w").close()
    rc, out = run_pty([LM], env_extra={"LM_HINTS": "1", "SEE_SCREENSHOT_DIR": shots})
    check("bare lm on a terminal suggests lm read latest after a fresh screenshot",
          "suggest:" in out and "lm read latest" in out.split("JOBS")[0], out[:160])
    rc, out = run_pty([LM], env_extra={"LM_HINTS": "0", "SEE_SCREENSHOT_DIR": shots})
    check("LM_HINTS=0 silences the suggestion", "suggest:" not in out)
    rc, out, _ = run([LM], env_extra={"LM_HINTS": "1", "SEE_SCREENSHOT_DIR": shots})
    check("lm piped never suggests", "suggest:" not in out)

# 11. every exit code the registry promises is the one the command gives (only cases that need no model)
def codes_of(text):
    return {int(c) for grp in re.findall(r"\b(\d+(?:/\d+)*)\b", text) for c in grp.split("/")}


DEAD = {"OLLAMA_HOST": "127.0.0.1:1"}
EXIT_CASES = [
    ("last", [LM, "last"], {}, 12),
    ("help", [LM, "help", "nosuchjob"], {}, 2),
    ("how", [LM, "how", "--no-model", "zzz qqq xxyzzy"], {}, 12),
    ("timeline", [LM, "timeline", "--bogus"], {}, 2),
    ("read", [LM, "read", "/nonexistent/zz.png"], {}, 12),
    ("diff", [LM, "diff", "/nonexistent/a.png", "/nonexistent/b.png"], {}, 12),
    ("see", [SEE, "/nonexistent/zz.png"], {}, 12),
    ("models", [LM, "models"], DEAD, 10),
    ("status", [LM, "status"], DEAD, 0),
    ("doctor", [LM, "doctor"], DEAD, 1),
    ("index", [LM, "index", "find"], {}, 2),
    ("probe", [LM, "probe"], {}, 2),
    ("bench", [LM, "bench", "nosuchset"], {}, 1),
    ("gemini", [LM, "gemini"], {}, 0),
    ("gemini", [LM, "gemini", "--json"], {}, 2),
    ("find", [LM, "find"], {}, 2),
]
for name, argv, env_extra, want in EXIT_CASES:
    rc, _, _ = run(argv, env_extra=env_extra, timeout=60)
    shown = " ".join(os.path.basename(a) for a in argv[:4])
    check(f"exit code of {shown} is {want}", rc == want, f"rc={rc}")
    if reg:
        check(f"registry lists exit code {want} for {name}", want in codes_of(jobs[name]["exit_codes"]), jobs[name]["exit_codes"][:80])
rc, _, _ = run([LM, "zzzverb"])
check("one unknown word is a usage error (exit 2) and the registry says so", rc == 2 and reg and "single unknown word" in reg["conventions"]["exit_codes"]["2"], f"rc={rc}")

# 12. the verbs bin/lm dispatches are the verbs the registry lists, no more and no fewer
lmtext = open(LM, encoding="utf-8").read()
body = lmtext.split('case "$verb" in')[1]
dispatched = set()
for line in body.splitlines():
    m = re.match(r"^  ([^\s()]+)\)", line)
    if m:
        dispatched |= {w for w in m.group(1).split("|") if w}
dispatched -= {"*", "-h", "--help", "--version", "-V", "version", "--capabilities", "capabilities"}
dispatched.discard("''")
if reg:
    verbs_reg = {n for n, j in jobs.items() if j["kind"] != "topic"}
    check("every verb bin/lm dispatches is in the registry", dispatched <= verbs_reg, f"not in the registry: {sorted(dispatched - verbs_reg)}")
    check("every registry verb is dispatched by bin/lm", verbs_reg <= dispatched, f"not dispatched: {sorted(verbs_reg - dispatched)}")

# 13. --json errors keep to the envelope on every path, not only the main ones
ENVELOPES = [
    ("lm models --bogus --json", [LM, "models", "--bogus", "--json"], {}),
    ("lm status --bogus --json", [LM, "status", "--bogus", "--json"], {}),
    ("lm timeline --bogus --json", [LM, "timeline", "--bogus", "--json"], {}),
    ("lm last --json with no history", [LM, "last", "--json"], {}),
    ("lm how --json with no request", [LM, "how", "--json"], {}),
    ("lm rag --json", [LM, "rag", "--json"], {}),
    ("lm fleet --json", [LM, "fleet", "--json"], {}),
    ("lm gemini --json", [LM, "gemini", "--json"], {}),
    ("lm models --json with the server down", [LM, "models", "--json"], DEAD),
]
for label, argv, env_extra in ENVELOPES:
    rc, out, _ = run(argv, env_extra=env_extra)
    try:
        e = json.loads(out.strip().splitlines()[-1])
    except Exception:
        e = {}
    check(f"{label}: the envelope is on stdout",
          rc != 0 and e.get("ok") is False and e.get("code") and isinstance(e.get("remedy"), str) and "next" in e, f"rc={rc} out={out[:100]!r}")

# 14. next is a complete, local, harmless command or null
def runnable_next(cmd):
    try:
        parts = shlex.split(cmd)
    except ValueError:
        return False
    return (parts and parts[0] in SUITE_BINS and not re.search(r"[<>]|\b[A-Z]{3,}\b|\.\.\.", cmd)
            and not re.search(r"install|npm|cargo|brew|--web|lm gemini (?!show\b|models\b|history\b)|docs/", cmd))


if reg:
    for code, r in reg["remedies"].items():
        if r.get("next"):
            check(f"remedy next for {code} is a complete local command: {r['next']}", runnable_next(r["next"]))
    for code in ("ctx_too_large", "sheet_missing", "ocr_missing", "repomix_missing", "img_unreadable", "clipboard_empty", "no_index"):
        check(f"remedy next for {code} is null", not reg["remedies"][code].get("next"))
rc, out, _ = run([SEE, "--json", "/nonexistent/zz.png"])
e = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
check("see on a missing image: next is null and the remedy names lm read latest",
      e.get("code") == "img_unreadable" and e.get("next") is None and "lm read latest" in e.get("remedy", ""), str(e)[:200])
rc, out, _ = run([LM, "models", "--json"], env_extra=DEAD)
e = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
check("server_down remedy names OLLAMA_HOST when it is not the default, and next is null", "OLLAMA_HOST" in e.get("remedy", "") and "127.0.0.1:1" in e.get("remedy", "") and e.get("next") is None, str(e)[:200])
rc, out, _ = run([sys.executable, VERBS_PY, "remedy", "server_down"], env_extra={"OLLAMA_HOST": "http://127.0.0.1:11434"})
check("server_down remedy keeps the restart advice for the default host", "OLLAMA_HOST" not in out and "restarts" in out, out[:160])

# 15. smaller promises
with tempfile.TemporaryDirectory(prefix="verbs-file.") as scratch:
    shotfile = os.path.join(scratch, "fresh.png")
    open(shotfile, "w").close()
    rc, out = run_pty([LM], env_extra={"LM_HINTS": "1", "SEE_SCREENSHOT_DIR": shotfile})
    check("a SEE_SCREENSHOT_DIR that is a file suggests nothing", rc == 0 and "suggest:" not in out and "JOBS" in out, out[:120])
    stubdir = os.path.join(scratch, "stub")
    os.makedirs(stubdir)
    empty = os.path.join(scratch, "noshots")
    os.makedirs(empty, exist_ok=True)
    for secs, label in (("0.03", "a clipboard probe that answers in 30 ms"), ("8", "a clipboard probe that never answers")):
        with open(os.path.join(stubdir, "osascript"), "w") as f:
            f.write(f"#!/bin/sh\nsleep {secs}\necho 'class PNGf, 100'\n")
        os.chmod(os.path.join(stubdir, "osascript"), 0o755)
        ok, took, out, rc = False, 0.0, "", 0
        for _attempt in range(3):   # a busy machine may need a second go; a wrong result fails all three
            t0 = time.time()
            rc, out = run_pty([LM], env_extra={"LM_HINTS": "1", "SEE_SCREENSHOT_DIR": empty, "PATH": stubdir + os.pathsep + os.environ["PATH"]})
            took = time.time() - t0
            ok = ("an image is on your clipboard" in out) if secs == "0.03" else (rc == 0 and "JOBS" in out and took < 0.5)
            if ok:
                break
        if secs == "0.03":
            check(f"bare lm sees an image on the clipboard with {label}", ok, out[:160])
        else:
            check(f"bare lm still draws the screen and finishes under 0.5 s with {label}", ok, f"{took:.2f}s")

# the generated man pages carry a date and short lines; the completion text is cut at a clause
for n in ("lm", "q", "see", "warm"):
    man = open(os.path.join(ROOT, "share", "man", "man1", f"{n}.1"), encoding="utf-8").read()
    check(f"{n}.1 has a date in .TH", re.search(r'^\.TH \S+ 1 "\d{4}-\d\d-\d\d" ', man, re.M) is not None)
    check(f"{n}.1 has no line over 80 bytes", max(len(l.encode("utf-8")) for l in man.splitlines()) <= 80,
          str(max(man.splitlines(), key=lambda l: len(l.encode("utf-8")))[:60]))
descs = []
for n in ("_q", "_see", "_lm", "_warm"):
    ztext = open(os.path.join(ROOT, "share", "zsh", n), encoding="utf-8").read()
    descs += re.findall(r"\[((?:[^\]\\]|\\.)*)\]", ztext)
check("completion descriptions have balanced parentheses",
      all(d.count("(") == d.count(")") for d in descs), str([d for d in descs if d.count("(") != d.count(")")][:2]))
check("completion descriptions do not end on a dangling article",
      not [d for d in descs if re.search(r"\b(the|a|an|of|and|or|to|from|with|after|before)$", d)],
      str([d for d in descs if re.search(r"\b(the|a|an|of|and|or|to|from|with|after|before)$", d)][:2]))
ztext_q = open(os.path.join(ROOT, "share", "zsh", "_q"), encoding="utf-8").read()
ztext_see = open(os.path.join(ROOT, "share", "zsh", "_see"), encoding="utf-8").read()
big = re.search(r"'--big\[([^\]]*)\]", ztext_q)
code_ = re.search(r"'--code\[([^\]]*)\]", ztext_q)
check("--big and --code each get their own description", big and code_ and big.group(1) != code_.group(1) and "code" in code_.group(1), str((big and big.group(1), code_ and code_.group(1))))
check("see completes a value after -m and --model", "'-m[" in ztext_see and re.search(r"'-m\[[^\]]*\]:model:", ztext_see) and re.search(r"'--model\[[^\]]*\]:model:", ztext_see))
check("screenshot names with spaces are offered as single candidates",
      'compadd -- "${shots[@]}"' in ztext_see and "(${shots})" not in ztext_see)

fails = [c for c in CHECKS if not c[1]]
for name, ok, detail in CHECKS:
    if ok and "-v" not in sys.argv:
        continue
    print(("PASS " if ok else "FAIL ") + name + ("" if ok or not detail else f"  [{detail}]"))
print(f"{len(CHECKS) - len(fails)}/{len(CHECKS)} checks passed")
sys.exit(1 if fails else 0)
