#!/usr/bin/env python3
"""cmdcheck: check a shell command someone (or a model) gave you, without running it.

For every program in the command it asks: is it installed? And for every long flag
(--like-this): does the program's own man page or --help mention it? A flag the program
never mentions is how a model's invented option shows up. The command itself never runs.
Only `<program> --help` (or `<program> <sub> --help`) is executed, and never for programs
on the DENY_HELP list. Output is read up to a cap and then the process is killed.

A flag after a subcommand (git log --oneline) is looked up in the subcommand's help; if it
is still not found it is reported as unverified ("?"), never as invented.

    cmdcheck.py "find . -name x --depth 3"   print the one-line verdict
    cmdcheck.py --json "..."                  the structured result

Exit 1 when any token is marked x (a program not installed, a flag not in the help), else 0.
Used by `q cmd` (the verdict rides under .checked in --json) and by `q check`.
"""
import json
import os
import re
import select
import shlex
import shutil
import signal
import subprocess
import sys
import time

# Shell builtins have no man page of their own to search; existence is all we can check.
BUILTINS = {"cd", "echo", "export", "test", "[", "[[", "source", ".", "alias", "set", "unset", "read",
            "printf", "exit", "true", "false", ":", "eval", "ulimit", "umask", "wait", "jobs", "pwd",
            "type", "hash", "shift", "return", "trap", "fg", "bg", "history", "local", "declare"}
# Programs that wrap another one: the next non-option word is the real program.
WRAPPERS = {"sudo", "env", "xargs", "nohup", "time", "command", "exec", "nice", "caffeinate", "watch", "timeout"}
# Wrapper options that take a separate value: `sudo -u root cmd`, `xargs -n 2 cmd`.
WRAP_VALUE_OPTS = {
    "sudo": {"-u", "-g", "-C", "-D", "-h", "-p", "-r", "-t", "-T", "-U", "--user", "--group"},
    "env": {"-u", "-C", "-S", "-P", "--unset", "--chdir"},
    "xargs": {"-n", "-I", "-P", "-L", "-s", "-d", "-E", "-a", "-J"},
    "timeout": {"-s", "-k", "--signal", "--kill-after"},
    "nice": {"-n", "--adjustment"},
    "watch": {"-n", "-d", "--interval"},
    "caffeinate": {"-t", "-w"},
    "exec": {"-a"},
}
# Shell grammar, never a program. LEAD words open a command that follows them (`then cmd`);
# SKIP words make the whole segment grammar (a loop header, a closer).
LEAD_WORDS = {"if", "then", "else", "elif", "do", "while", "until", "!", "{", "time"}
SKIP_WORDS = {"for", "select", "case", "esac", "in", "function", "fi", "done", "}", ";;"}
# Programs where even `--help` should not be run, because `--help` can act, read stdin or be
# taken as an operand (pbcopy empties the clipboard, open and say run their argument).
# Their man page is read instead; a flag it does not show comes back "cannot be checked".
DENY_HELP = {"reboot", "shutdown", "halt", "poweroff", "kill", "pkill", "killall", "launchctl", "diskutil",
             "fdisk", "dd", "mkfs", "newfs", "newfs_hfs", "newfs_apfs", "rm", "mv", "cp", "ln", "chmod",
             "chown", "srm", "shred", "truncate", "systemsetup", "pmset", "csrutil", "nvram", "tmutil",
             "pbcopy", "pbpaste", "open", "say", "osascript", "defaults", "security", "networksetup",
             "afplay", "screencapture", "hdiutil", "dscl", "softwareupdate", "scutil", "spctl", "mdutil",
             "pfctl", "passwd", "login", "su"}
# Launchers run a package by name (npx ccusage ...). If the package is not installed here its flags
# cannot be read without downloading and running it, which this check never does.
LAUNCHERS = {"npx", "bunx", "pnpx", "uvx"}
SEPARATORS = {"|", "||", "&&", ";", "&", "|&"}
EXEC_FLAGS = {"-exec", "-execdir", "-ok", "-okdir"}   # find: what follows is another program's command line
BUDGET_S = 2.0       # the whole check, however many lookups it needs
HELP_CAP = 256 * 1024  # bytes of help or man output read before the process is killed


def segments(text):
    """Yield each simple command in TEXT as a list of words (quotes kept, so a quoted word is not a flag)."""
    heredoc = None
    for raw in text.splitlines():
        if heredoc is not None:
            if raw.strip() == heredoc:
                heredoc = None
            continue
        line = raw.strip()
        if line.startswith("```"):
            continue   # a markdown fence, with or without a language tag
        line = line.strip("`").strip()
        if line.startswith("$ "):
            line = line[2:]
        if not line or line.startswith("#"):
            continue
        hm = re.search(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1", line)
        if hm:
            heredoc = hm.group(2)
        try:
            lex = shlex.shlex(line, posix=False, punctuation_chars=True)
            lex.whitespace_split = True
            words = list(lex)
        except ValueError:
            continue
        cur, drop_next, k = [], False, 0
        while k < len(words):
            w = words[k]
            k += 1
            if w == "\\" and k < len(words) and words[k] in SEPARATORS:
                w, k = "\\" + words[k], k + 1   # an escaped ; (find -exec ... \;) is an argument
            if w in SEPARATORS:
                if cur:
                    yield cur
                cur, drop_next = [], False
            elif re.fullmatch(r"[0-9]*[<>][<>&]*[0-9-]*", w):
                drop_next = True   # a redirection: the next word is a file or a heredoc tag
            elif re.fullmatch(r"[()]+", w):
                continue
            elif drop_next:
                drop_next = False
            else:
                cur.append(w)
        if cur:
            yield cur


def unquote(w):
    return w[1:-1] if len(w) >= 2 and w[0] == w[-1] and w[0] in "'\"" else w


def program_and_flags(words):
    """(program, sub-word, long flags, launcher used) for one segment; (None, None, [], False) if it runs no program."""
    none = (None, None, [], False)
    i, launched = 0, False
    while i < len(words) and words[i] in LEAD_WORDS:
        i += 1
    if i >= len(words) or words[i] in SKIP_WORDS:
        return none
    while i < len(words):
        w = words[i]
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", w):
            i += 1
        elif w in LAUNCHERS:
            launched = True
            i += 1
            while i < len(words) and words[i].startswith("-"):
                i += 1
            break
        elif w in WRAPPERS:
            i += 1
            valopts, seen_dur = WRAP_VALUE_OPTS.get(w, set()), False
            while i < len(words):
                t = words[i]
                if t == "--":
                    i += 1
                    break
                if t.startswith("-"):
                    i += 2 if t in valopts else 1
                elif w == "env" and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", t):
                    i += 1
                elif w == "timeout" and not seen_dur and re.fullmatch(r"[0-9.]+[smhd]?", t):
                    seen_dur = True
                    i += 1
                elif w == "nice" and re.fullmatch(r"[0-9]+", t):
                    i += 1
                else:
                    break
        else:
            break
    if i >= len(words):
        return none
    prog = unquote(words[i])
    if prog.startswith(("$", "~", "-")) and "/" not in prog:
        return none
    if prog in LEAD_WORDS or prog in SKIP_WORDS:
        return none
    rest = words[i + 1:]
    sub = rest[0] if rest and re.fullmatch(r"[a-z][a-z0-9_-]*", rest[0]) else None   # git log, docker run
    flags = []
    for w in rest:
        if w == "--" or w in EXEC_FLAGS:
            break   # everything after belongs to another program, or is plain data
        m = re.match(r"(--[A-Za-z][A-Za-z0-9-]*)", w)
        if m and m.group(1) not in flags:
            flags.append(m.group(1))
    return prog, sub, flags, launched


def run_capped(argv, wait, env=None, merge=False):
    """Output of ARGV, at most HELP_CAP bytes, then the process is killed (`yes` prints forever)."""
    try:
        p = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT if merge else subprocess.DEVNULL,
                             env=env, start_new_session=True)
    except OSError:
        return ""
    chunks, total, end = [], 0, time.time() + wait
    fd = p.stdout.fileno()
    try:
        while total < HELP_CAP:
            left = end - time.time()
            if left <= 0:
                break
            ready, _, _ = select.select([fd], [], [], left)
            if not ready:
                break
            data = os.read(fd, 65536)
            if not data:
                break
            chunks.append(data)
            total += len(data)
    finally:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            pass
        p.stdout.close()
        try:
            p.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
    return b"".join(chunks)[:HELP_CAP].decode("utf-8", "replace")


def man_text(prog, deadline):
    left = deadline - time.time()
    if left <= 0.05:
        return ""
    env = dict(os.environ, MANPAGER="cat", PAGER="cat", MANWIDTH="200")
    return re.sub(r".\x08", "", run_capped(["man", prog], min(left, 1.0), env))   # man underlines with backspaces


def help_text(prog, deadline, sub=None):
    left = deadline - time.time()
    if left <= 0.05:
        return ""
    return run_capped([prog] + ([sub] if sub else []) + ["--help"], min(left, 1.0), merge=True)


def mentions(text, flag):
    return re.search(r"(?<![A-Za-z0-9-])" + re.escape(flag) + r"(?![A-Za-z0-9-])", text) is not None


def check(text, budget=BUDGET_S):
    """Check every program and long flag in TEXT. Never runs the command itself."""
    deadline = time.time() + budget
    bins, seen = [], {}
    for words in segments(text):
        prog, sub, flags, launched = program_and_flags(words)
        if not prog:
            continue
        name = os.path.basename(prog)
        key = (name, sub if flags else None)
        entry = seen.get(key)
        if entry is None:
            if "/" in prog:
                found = os.access(prog, os.X_OK)
            else:
                found = prog in BUILTINS or shutil.which(prog) is not None
            if launched and not found:
                found = None   # may exist in the package registry; we will not fetch it to find out
            entry = {"name": name, "sub": key[1], "found": found, "flags": [], "denied": name in DENY_HELP}
            seen[key] = entry
            bins.append(entry)
        for f in flags:
            if all(x["flag"] != f for x in entry["flags"]):
                entry["flags"].append({"flag": f, "found": None})
    tops = {}
    for b in bins:
        if not b["found"] or b["name"] in BUILTINS or not b["flags"]:
            continue   # (None = launcher package not installed; its flags stay unchecked)
        name = b["name"]
        if name not in tops:
            txt = man_text(name, deadline)
            if not b["denied"] and any(not mentions(txt, f["flag"]) for f in b["flags"]):
                txt = txt + "\n" + help_text(name, deadline)
            tops[name] = txt
        txt = tops[name]
        if b["sub"] and not b["denied"] and any(not mentions(txt, f["flag"]) for f in b["flags"]):
            txt = txt + "\n" + man_text("%s-%s" % (name, b["sub"]), deadline) + "\n" + help_text(name, deadline, b["sub"])
        for f in b["flags"]:
            if mentions(txt, f["flag"]):
                f["found"] = True
            elif b["denied"] or b["sub"] or not txt.strip():
                f["found"] = None   # cannot tell: not run, a subcommand's own flag, or no help text at all
            else:
                f["found"] = False
    bad = any((b["found"] is False) or any(f["found"] is False for f in b["flags"]) for b in bins)
    return {"ok": not bad, "bins": bins, "checked": len(bins) > 0}


def line(result):
    """The one-line verdict, e.g. '· checked: ccusage ✓ · --per-model ✗ not in ccusage --help → q again --web'."""
    if not result["bins"]:
        return ""
    parts = []
    for b in result["bins"]:
        label = b["name"] + (" " + b["sub"] if b.get("sub") else "")
        if b["found"] is None:
            parts.append("%s ? not installed here, so its flags cannot be checked" % b["name"])
            continue
        if not b["found"]:
            parts.append("%s ✗ not installed" % b["name"])
            continue
        parts.append("%s ✓" % label)
        for f in b["flags"]:
            if f["found"] is True:
                parts.append("%s ✓" % f["flag"])
            elif f["found"] is False:
                parts.append("%s ✗ not in %s --help" % (f["flag"], label))
            elif b.get("denied"):
                parts.append("%s ? cannot be checked (%s is never run)" % (f["flag"], b["name"]))
            elif b.get("sub"):
                parts.append("%s ? not found in %s help; unverified" % (f["flag"], label))
            else:
                parts.append("%s ? no help text to check" % f["flag"])
    s = "· checked: " + " · ".join(parts)
    if not result["ok"]:
        s += " → q again --web"
    return s


def main(argv):
    as_json = "--json" in argv
    args = [a for a in argv if a != "--json"]
    if not args or args[0] in ("-h", "--help"):
        print("usage: cmdcheck.py [--json] \"<shell command>\"   (checks the programs and long flags; never runs it; exit 1 if any is marked x)")
        return 0 if args else 2
    res = check(" ".join(args))
    print(json.dumps(res) if as_json else line(res))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
