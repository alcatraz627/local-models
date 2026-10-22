#!/usr/bin/env python3
"""Model-free checks for lib/cmdcheck.py and the prompt-routing word filter (lm_file_ref in bin/_lib.sh).

Fake programs in a temp PATH stand in for real tools so nothing real is touched. No model runs.
Exit 0 = every check passed.

    .venv/bin/python probe/fixtures/cmdcheck-route.py
"""
import os
import resource
import stat
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "lib"))
CMDCHECK = os.path.join(ROOT, "lib", "cmdcheck.py")
LIB = os.path.join(ROOT, "bin", "_lib.sh")
CHECKS = []


def check(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))


tmp = tempfile.mkdtemp(prefix="cmdcheck-route.")
bindir = os.path.join(tmp, "bin")
os.mkdir(bindir)
marker = os.path.join(tmp, "ran-marker")


def script(name, body):
    p = os.path.join(bindir, name)
    with open(p, "w") as f:
        f.write("#!/bin/sh\n" + body)
    os.chmod(p, os.stat(p).st_mode | stat.S_IXUSR)


# ftool: a tool with a subcommand. `ftool --help` knows --global, `ftool sub --help` knows --real.
script("ftool", 'if [ "$1" = sub ] && [ "$2" = --help ]; then echo "usage: ftool sub [--real]"; '
                'elif [ "$1" = --help ]; then echo "usage: ftool [--global] <sub>"; else echo "usage: ftool"; fi\n')
for denied in ("pbcopy", "open", "say", "osascript"):
    script(denied, 'echo ran >> "%s"\n' % marker)
os.environ["PATH"] = bindir + os.pathsep + os.environ["PATH"]

import cmdcheck  # noqa: E402


def run(cmd):
    res = cmdcheck.check(cmd)
    return res, cmdcheck.line(res)


def flag_states(res):
    return {f["flag"]: f["found"] for b in res["bins"] for f in b["flags"]}


def names(res):
    return [b["name"] for b in res["bins"]]


def no_bad(res):
    return not any(b["found"] is False or any(f["found"] is False for f in b["flags"]) for b in res["bins"])


# F1: subcommand flags are unknown, never invented
for cmd in ("git log --oneline --graph", "git commit --amend --no-edit"):
    r, ln = run(cmd)
    check("F1 %s: no flag marked invented, no web nudge" % cmd, no_bad(r) and r["ok"] and "--web" not in ln, ln)
r, ln = run("ftool sub --real")
check("F1 subcommand flag found in `ftool sub --help` is verified", flag_states(r).get("--real") is True, ln)
r, ln = run("ftool sub --bogus")
check("F1 unknown subcommand flag is '?' not x, no web nudge", flag_states(r).get("--bogus") is None and r["ok"] and "--web" not in ln, ln)
r, ln = run("ftool --nope")
check("F1 control: a top-level flag the tool never mentions is still x", flag_states(r).get("--nope") is False and not r["ok"], ln)
r, ln = run("ftool --global")
check("F1 control: a real top-level flag is verified", flag_states(r).get("--global") is True, ln)

# F1: flags belong to the program they follow
r, ln = run("find . -name x -exec ftool --bogus {} \\;")
check("F1 flag after -exec is not charged to find", flag_states(r) == {}, str(flag_states(r)))
r, ln = run('echo "--hello" | grep -- --hello')
check("F1 quoted arg and flag after -- are not flags", flag_states(r) == {}, str(flag_states(r)))
r, ln = run("ftool --global | grep x --bogusgrep")
ft = [f["flag"] for b in r["bins"] if b["name"] == "ftool" for f in b["flags"]]
check("F1 a pipe ends the first program's flags", ft == ["--global"], str(ft))

# F4: shell grammar
for cmd in ("if ftool --global; then echo hi; fi",
            "for f in *; do ftool --global $f; done",
            "while true; do ftool --global; done",
            "! ftool --global",
            "cat <<EOF\nftool --bogus\nEOF",
            "sudo -u root ftool --global",
            "env -u X ftool --global",
            "timeout 5 ftool --global",
            "nice -n 5 ftool --global",
            "ls | xargs -n 1 ftool --global",
            "--foo",
            "```bash\nftool --global\n```"):
    r, ln = run(cmd)
    check("F4 %r: nothing reported as not installed" % cmd, no_bad(r) and r["ok"] and "not installed" not in ln, ln)
r, ln = run("```bash\nftool --global\n```")
check("F4 a markdown fence line adds no program", names(r) == ["ftool"], str(names(r)))
r, ln = run("--foo")
check("F4 a leading --foo is not a program", names(r) == [], str(names(r)))
r, ln = run("cat <<EOF\nftool --bogus\nEOF")
check("F4 heredoc body is not checked", "ftool" not in names(r), str(names(r)))


def cli(arg):
    return subprocess.run([sys.executable, CMDCHECK, arg], capture_output=True, text=True).returncode


check("F4 CLI exits 1 when a token is x", cli("ftool --nope") == 1)
check("F4 CLI exits 0 when all ok", cli("ftool --global") == 0)
check("F4 CLI exits 0 for '?' only", cli("ftool sub --bogus") == 0)
check("F4 CLI exits 1 for a program not installed", cli("zzz-not-a-program --x") == 1)

# F2: output cap
before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
subprocess.run([sys.executable, CMDCHECK, "yes --foo"], capture_output=True, text=True)
peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss   # bytes on macOS
check("F2 `yes --foo` stays under 200 MB peak", peak < 200 * 1024 * 1024, "peak %d MB" % (peak // 1048576))

# F3: programs that can act on --help are never run
for prog in ("pbcopy", "open", "say", "osascript"):
    r, ln = run("%s --nope" % prog)
    check("F3 %s: not run, flag not marked invented" % prog, not os.path.exists(marker) and no_bad(r), ln)
    if os.path.exists(marker):
        os.unlink(marker)
r, ln = run("pbcopy --nope")
check("F3 denied program says it cannot be checked", "cannot be checked" in ln, ln)

# F5: which prompt words count as a file reference
work = os.path.join(tmp, "work")
os.mkdir(work)
open(os.path.join(work, "notes.md"), "w").close()


def is_ref(word):
    rc = subprocess.run(["bash", "-c", 'source "$1"; lm_file_ref "$2"', "x", LIB, word], cwd=work,
                        capture_output=True).returncode
    return rc


for w in ("/etc/hosts", "~/missing-thing.txt", "./a", "../b", "notes.md"):
    check("F5 %s counts as a file reference" % w, is_ref(w) == 0, "rc %d" % is_ref(w))
for w in ("I/O", "TCP/IP", "yes/no", "km/h", "https://example.com/logo.png", "ftp://h/x.pdf", "ghost.txt", "e.g", "v1.2"):
    check("F5 %s passes through untouched" % w, is_ref(w) == 1, "rc %d" % is_ref(w))

failed = [c for c in CHECKS if not c[1]]
for name, good, detail in CHECKS:
    print(("ok   " if good else "FAIL ") + name + ("" if good or not detail else "  [" + detail + "]"))
print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} passed")
sys.exit(1 if failed else 0)
