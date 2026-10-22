#!/usr/bin/env python3
"""cmdcheck: check a shell command someone (or a model) gave you, without running it.

For every program in the command it asks: is it installed? And for every long flag
(--like-this): does the program's own man page or --help mention it? A flag the program
never mentions is how a model's invented option shows up. The command itself never runs.
Only `<program> --help` is executed, and never for programs on the DENY_HELP list.

    cmdcheck.py "find . -name x --depth 3"   print the one-line verdict
    cmdcheck.py --json "..."                  the structured result

Used by `q cmd` (the verdict rides under .checked in --json) and by `q check`.
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time

# Shell builtins have no man page of their own to search; existence is all we can check.
BUILTINS = {"cd", "echo", "export", "test", "[", "[[", "source", ".", "alias", "set", "unset", "read",
            "printf", "exit", "true", "false", ":", "eval", "ulimit", "umask", "wait", "jobs", "pwd",
            "type", "hash", "shift", "return", "trap", "fg", "bg", "history", "local", "declare"}
# Programs that wrap another one: the next non-option word is the real program.
WRAPPERS = {"sudo", "env", "xargs", "nohup", "time", "command", "exec", "nice", "caffeinate", "watch", "timeout"}
# Programs where even `--help` should not be run; their man page is read instead.
DENY_HELP = {"reboot", "shutdown", "halt", "poweroff", "kill", "pkill", "killall", "launchctl", "diskutil",
             "fdisk", "dd", "mkfs", "newfs", "newfs_hfs", "newfs_apfs", "rm", "mv", "cp", "ln", "chmod",
             "chown", "srm", "shred", "truncate", "systemsetup", "pmset", "csrutil", "nvram", "tmutil"}
# Launchers run a package by name (npx ccusage ...). If the package is not installed here its flags
# cannot be read without downloading and running it, which this check never does.
LAUNCHERS = {"npx", "bunx", "pnpx", "uvx"}
SEPARATORS = {"|", "||", "&&", ";", "&", "|&"}
BUDGET_S = 2.0   # the whole check, however many lookups it needs


def segments(text):
    """Yield each simple command in TEXT as a list of words."""
    for raw in text.splitlines():
        line = raw.strip().strip("`").strip()
        if line.startswith("$ "):
            line = line[2:]
        if not line or line.startswith("#"):
            continue
        try:
            lex = shlex.shlex(line, posix=True, punctuation_chars=True)
            lex.whitespace_split = True
            words = list(lex)
        except ValueError:
            continue
        cur = []
        for w in words:
            if w in SEPARATORS:
                if cur:
                    yield cur
                cur = []
            elif re.fullmatch(r"[0-9]*[<>][<>&]*[0-9-]*|[()]+", w):
                continue   # a redirection or a subshell paren, not an argument
            else:
                cur.append(w)
        if cur:
            yield cur


def program_and_flags(words):
    """The program a segment runs, its long flags, and whether a launcher named it: (None, [], False) if none."""
    i, launched = 0, False
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
            while i < len(words) and (words[i].startswith("-") or re.fullmatch(r"[0-9.]+[smhd]?", words[i])):
                i += 1
        else:
            break
    if i >= len(words):
        return None, [], False
    prog = words[i]
    if prog.startswith(("$", "~")) and "/" not in prog:
        return None, [], False
    flags = []
    for w in words[i + 1:]:
        m = re.match(r"(--[A-Za-z][A-Za-z0-9-]*)", w)
        if m and m.group(1) not in flags:
            flags.append(m.group(1))
    return prog, flags, launched


def man_text(prog, deadline):
    left = deadline - time.time()
    if left <= 0.05:
        return ""
    env = dict(os.environ, MANPAGER="cat", PAGER="cat", MANWIDTH="200")
    try:
        out = subprocess.run(["man", prog], capture_output=True, text=True, timeout=min(left, 1.0), env=env).stdout
    except (subprocess.TimeoutExpired, OSError):
        return ""
    return re.sub(r".\x08", "", out)   # man underlines with backspaces


def help_text(prog, deadline):
    left = deadline - time.time()
    if left <= 0.05:
        return ""
    try:
        r = subprocess.run([prog, "--help"], capture_output=True, text=True, timeout=min(left, 1.0),
                           stdin=subprocess.DEVNULL)
        return (r.stdout or "") + (r.stderr or "")
    except (subprocess.TimeoutExpired, OSError):
        return ""


def mentions(text, flag):
    return re.search(r"(?<![A-Za-z0-9-])" + re.escape(flag) + r"(?![A-Za-z0-9-])", text) is not None


def check(text, budget=BUDGET_S):
    """Check every program and long flag in TEXT. Never runs the command itself."""
    deadline = time.time() + budget
    bins, seen = [], {}
    for words in segments(text):
        prog, flags, launched = program_and_flags(words)
        if not prog:
            continue
        name = os.path.basename(prog)
        entry = seen.get(name)
        if entry is None:
            if "/" in prog:
                found = os.access(prog, os.X_OK)
            else:
                found = prog in BUILTINS or shutil.which(prog) is not None
            if launched and not found:
                found = None   # may exist in the package registry; we will not fetch it to find out
            entry = {"name": name, "found": found, "flags": []}
            seen[name] = entry
            bins.append(entry)
        for f in flags:
            if all(x["flag"] != f for x in entry["flags"]):
                entry["flags"].append({"flag": f, "found": None})
    helps = {}
    for b in bins:
        if not b["found"] or b["name"] in BUILTINS or not b["flags"]:
            continue   # (None = launcher package not installed; its flags stay unchecked)
        txt = man_text(b["name"], deadline)
        pending = [f for f in b["flags"] if not mentions(txt, f["flag"])]
        if pending and b["name"] not in DENY_HELP:
            txt = txt + "\n" + help_text(b["name"], deadline)
        helps[b["name"]] = txt
        for f in b["flags"]:
            if not txt.strip():
                f["found"] = None   # no man page and no help output: cannot tell
            else:
                f["found"] = mentions(txt, f["flag"])
    bad = any((b["found"] is False) or any(f["found"] is False for f in b["flags"]) for b in bins)
    return {"ok": not bad, "bins": bins, "checked": len(bins) > 0}


def line(result):
    """The one-line verdict, e.g. '· checked: ccusage ✓ · --per-model ✗ not in ccusage --help → q again --web'."""
    if not result["bins"]:
        return ""
    parts = []
    for b in result["bins"]:
        if b["found"] is None:
            parts.append("%s ? not installed here, so its flags cannot be checked" % b["name"])
            continue
        if not b["found"]:
            parts.append("%s ✗ not installed" % b["name"])
            continue
        parts.append("%s ✓" % b["name"])
        for f in b["flags"]:
            if f["found"] is True:
                parts.append("%s ✓" % f["flag"])
            elif f["found"] is False:
                parts.append("%s ✗ not in %s --help" % (f["flag"], b["name"]))
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
        print("usage: cmdcheck.py [--json] \"<shell command>\"   (checks the programs and long flags; never runs it)")
        return 0 if args else 2
    res = check(" ".join(args))
    print(json.dumps(res) if as_json else line(res))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
