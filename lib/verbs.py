#!/usr/bin/env python3
"""Reads lib/verbs.toml and produces everything lm says about itself.

    verbs.py screen front|more|help [JOB]|capabilities [JOB] [--json] [--color]
    verbs.py how "what I want" [--go] [--json] [--no-model] [--color]
    verbs.py remedy CODE          JSON {remedy, next} for an error code
    verbs.py hint KEY [--n N] [--img PATH] [--color]
    verbs.py gen --out DIR | --root ROOT   completion, man pages, tldr pages, the docs block

Standard library only, so any python 3.11+ runs it.
"""
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REGISTRY = os.path.join(HERE, "verbs.toml")
HELP_W = 100


def load():
    with open(REGISTRY, "rb") as f:
        return tomllib.load(f)


class Pal:
    """The same palette bin/_lib.sh uses; empty strings when colour is off."""

    def __init__(self, on):
        if on:
            self.Y, self.C, self.G = "\033[1;33m", "\033[36m", "\033[32m"
            self.Dm, self.Rs, self.Bd = "\033[2m", "\033[0m", "\033[1m"
        else:
            self.Y = self.C = self.G = self.Dm = self.Rs = self.Bd = ""


def wrap(avail, text):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > avail:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}" if line else word
    lines.append(line)
    return lines


def row(p, col, w, label, desc):
    """One aligned help row, wrapped the way bin/_lib.sh's _help_row does."""
    avail = max(HELP_W - w - 3, 30)
    lines = wrap(avail, desc)
    lead = " " * (w + 3)
    out = []
    if len(label) > w:
        out.append(f"  {col}{label}{p.Rs}")
        out += [f"{lead}{p.Dm}{l}{p.Rs}" for l in lines]
    else:
        out.append(f"  {col}{label.ljust(w)}{p.Rs} {p.Dm}{lines[0]}{p.Rs}")
        out += [f"{lead}{p.Dm}{l}{p.Rs}" for l in lines[1:]]
    return out


def note(p, text):
    return [f"  {p.Dm}{l}{p.Rs}" for l in wrap(HELP_W - 2, text)]


def by_name(reg):
    return {j["name"]: j for j in reg["job"]}


def resolve(reg, token):
    for j in reg["job"]:
        if token == j["name"] or token in j.get("aliases", []):
            return j
    return None


def did_you_mean(word, cands):
    def lev(a, b):
        d = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            prev, d[0] = d[0], i
            for j, cb in enumerate(b, 1):
                cur = min(d[j] + 1, d[j - 1] + 1, prev + (ca != cb))
                prev, d[j] = d[j], cur
        return d[-1]
    lim = 2 if len(word) >= 7 else 1
    best = min(cands, key=lambda c: lev(word, c), default=None)
    return best if best is not None and lev(word, best) <= lim else ""


# screens


def screen_front(reg, p):
    s = reg["screens"]
    jobs = by_name(reg)
    out = [f"{p.Bd}{p.C}lm{p.Rs} {p.Dm}— {s['front_title']}{p.Rs}", "", f"{p.Y}JOBS{p.Rs}"]
    for n in s["front_jobs"]:
        out += row(p, p.C, 32, jobs[n]["front_label"], jobs[n]["front_says"])
    out += ["", f"{p.Y}KEEP IT HANDY{p.Rs}"]
    for n in s["front_handy"]:
        out += row(p, p.C, 32, jobs[n]["front_label"], jobs[n]["front_says"])
    out += ["", f"  {p.Dm}{s['front_footer']}{p.Rs}"]
    return out


def screen_more(reg, p):
    s = reg["screens"]
    jobs = by_name(reg)
    out = [f"{p.Bd}{p.C}lm{p.Rs} {p.Dm}— {s['more_title']}{p.Rs}", "", f"{p.Y}COMMANDS{p.Rs}"]
    for n in s["more_order"]:
        j = jobs[n]
        out.append(f"  {p.C}{j['more_label'].ljust(22)}{p.Rs} {p.Dm}{j['more_says']}{p.Rs}")
    out += ["", f"{p.Y}EXAMPLES{p.Rs}"]
    for e in s["more_examples"]:
        if e["says"]:
            out.append(f"  {p.Dm}${p.Rs} {e['cmd'].ljust(43)} {p.Dm}# {e['says']}{p.Rs}")
        else:
            out.append(f"  {p.Dm}${p.Rs} {e['cmd']}")
    out += ["", f"{p.Y}MORE{p.Rs}"]
    for line in s["more_footer"]:
        out.append("  " + line.replace("{c}", p.C).replace("{r}", p.Rs).replace("{d}", p.Dm))
    return out


def screen_help(reg, p, token):
    s = reg["screens"]
    jobs = by_name(reg)
    if not token:
        out = [f"{p.Bd}{p.C}lm help <job>{p.Rs} {p.Dm}— say what you want to do, get the commands{p.Rs}", "", f"{p.Y}JOBS{p.Rs}"]
        for n in s["help_index"]:
            out += row(p, p.C, 44, f"lm help {n}", jobs[n]["help_says"] if jobs[n].get("help_says") else jobs[n]["summary"])
        out += ["", *note(p, s["help_index_note"])]
        return out, 0
    j = resolve(reg, token)
    if j is None:
        names = [x["name"] for x in reg["job"]]
        g = did_you_mean(token, names + [a for x in reg["job"] for a in x.get("aliases", [])])
        listed = set(s["help_index"])
        more = [x["name"] for x in reg["job"] if x["name"] not in listed and x["kind"] != "tool"]
        tools = [x["name"] for x in reg["job"] if x["kind"] == "tool"]
        msg = (f"lm help: unknown job '{token}'{f' (did you mean {chr(39)}{g}{chr(39)}?)' if g else ''}\n"
               f"  jobs: {' '.join(s['help_index'])}\n  more: {' '.join(more)}\n  tools: {' '.join(tools)}")
        return msg.split("\n"), 2
    out = [f"{p.Bd}{p.C}lm help {token}{p.Rs} {p.Dm}— {j['summary']}{p.Rs}"]
    seen = []
    for e in j["examples"]:
        sec = e.get("section", "START")
        if sec not in seen:
            seen.append(sec)
            out += ["", f"{p.Y}{sec}{p.Rs}"]
        out += row(p, p.C, 44, e["cmd"], e["says"])
    if j.get("note"):
        out += ["", *note(p, j["note"])]
    if j["leaves_mac"]:
        out += ["", *note(p, "☁ This leaves your Mac.")]
    return out, 0


# the agent menu


def capabilities_json(reg, job=None):
    jobs = reg["job"]
    if job:
        j = resolve(reg, job)
        return j
    return {"version": reg["version"], "jobs": jobs, "conventions": reg["conventions"]}


def cost_tag(j):
    cloud = " ☁" if j["leaves_mac"] else ""
    return f"{j['cost_tier']}, {j['cost_secs']} s{cloud}"


def screen_capabilities(reg, p, job=None):
    if job:
        j = resolve(reg, job)
        if j is None:
            return [f"lm --capabilities: no job '{job}' (lm --capabilities lists them)"], 2
        out = [f"{p.Bd}{p.C}lm {j['name']}{p.Rs} {p.Dm}— {j['summary']}{p.Rs}", ""]
        for k, label in (("usage", "usage"), ("inputs", "inputs"), ("output", "output"), ("exit_codes", "exit codes"),
                         ("cost_tier", "cost"), ("side_effects", "side effects")):
            v = j[k] if k != "cost_tier" else cost_tag(j)
            out.append(f"  {p.Y}{label.ljust(12)}{p.Rs} {v}")
        out.append(f"  {p.Y}{'leaves mac'.ljust(12)}{p.Rs} {'yes ☁' if j['leaves_mac'] else 'no'}")
        out.append(f"  {p.Y}{'see also'.ljust(12)}{p.Rs} {', '.join(j['see_also']) or '-'}")
        out += ["", f"{p.Y}EXAMPLES{p.Rs}"]
        for e in j["examples"]:
            out += row(p, p.C, 44, e["cmd"], e["says"])
        return out, 0
    out = [f"{p.Bd}{p.C}lm --capabilities{p.Rs} {p.Dm}— {len(reg['job'])} entries. --json is the machine form, lm --capabilities <job> shows one{p.Rs}"]
    for kind, title in (("job", "JOBS"), ("topic", "TOPICS (help pages over the tools)"), ("tool", "TOOLS")):
        out += ["", f"{p.Y}{title}{p.Rs}"]
        for j in reg["job"]:
            if j["kind"] == kind:
                out += row(p, p.C, 34, j["usage"], f"{j['summary']}  [{cost_tag(j)}]")
    out += ["", f"{p.Y}CONVENTIONS{p.Rs}"]
    c = reg["conventions"]
    out += row(p, p.G, 14, "json", c["json_flag"])
    out += row(p, p.G, 14, "history", c["history_scope"])
    out += row(p, p.G, 14, "no terminal", c["no_tty_behaviour"])
    out += row(p, p.G, 14, "exit codes", "; ".join(f"{k} {v}" for k, v in c["exit_codes"].items()))
    return out, 0


# lm how

STOP = None


def _norm(reg):
    h = reg["how"]
    canon = {}
    for grp in h["synonyms"]:
        for w in grp:
            canon[w] = grp[0]
    return set(h["stopwords"]), canon


def stem(w):
    for suf in ("ing", "ed", "es", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def toks(text, stop, canon):
    out = []
    for w in re.findall(r"[a-z0-9][a-z0-9+_-]*", text.lower()):
        if w in stop:
            continue
        w = canon.get(w, w)
        w = canon.get(stem(w), stem(w))
        out.append(canon.get(w, w))
    return out


def how_rank(reg, query):
    """Score every job against the words. Returns [(score, job, matched_phrase, example)] best first."""
    stop, canon = _norm(reg)
    q = set(toks(query, stop, canon))
    raw = set(re.findall(r"[a-z0-9][a-z0-9+_-]*", query.lower()))
    cloud_ok = any(t in raw for t in reg["how"]["cloud_triggers"])
    ranked = []
    for j in reg["job"]:
        if j["kind"] == "tool":
            continue
        if j["leaves_mac"] and not cloud_ok:
            continue
        score, phrase = 0.0, ""
        for k in j["keywords"]:
            kt = set(toks(k, stop, canon))
            if not kt:
                continue
            hit = len(kt & q)
            if hit == len(kt):
                s = 3.0 * len(kt) if len(kt) > 1 else 3.0
                if len(kt) == 1 and len(kt) < len(q):
                    s = 3.0
            elif len(kt) > 1 and hit:
                s = 0.8 * hit
            else:
                s = 0.0
            if s > score:
                score, phrase = s, k
        for t in toks(j["summary"], stop, canon):
            if t in q:
                score += 0.5
        if j["name"] in raw or j["name"] in q:
            score += 2.0
        bonus = 0.0
        best_ex, best_es = None, -1.0
        for e in j["examples"]:
            if e.get("cloud") and not cloud_ok:
                continue
            et = set(toks(e["says"] + " " + e["cmd"] + " " + " ".join(e.get("keywords", [])), stop, canon))
            es = len(et & q) + 2.0 * sum(1 for k in e.get("keywords", []) if set(toks(k, stop, canon)) <= q and toks(k, stop, canon))
            bonus = max(bonus, 0.3 * len(et & q))
            if es > best_es:
                best_ex, best_es = e, es
        score += min(bonus, 1.0)
        if best_ex is None:
            continue
        ranked.append((score, j, phrase, best_ex, best_es))
    ranked.sort(key=lambda r: -r[0])
    return ranked


def how_answer(reg, query):
    ranked = how_rank(reg, query)
    if not ranked or ranked[0][0] < reg["how"]["threshold"]:
        return None
    score, j, phrase, ex, _ = ranked[0]
    alts = []
    same = [e for e in j["examples"] if e is not ex and not (e.get("cloud") and "cloud" in ex)]
    stop, canon = _norm(reg)
    q = set(toks(query, stop, canon))
    same.sort(key=lambda e: -len(set(toks(e["says"] + " " + e["cmd"], stop, canon)) & q))
    for e in same[:1]:
        if not e.get("cloud") or any(t in query.lower() for t in reg["how"]["cloud_triggers"]):
            alts.append({"command": e["cmd"], "says": e["says"]})
    for r in ranked[1:3]:
        if len(alts) >= 2:
            break
        if r[0] >= 0.8 * reg["how"]["threshold"]:
            alts.append({"command": r[3]["cmd"], "says": r[3]["says"]})
    return {"command": ex["cmd"], "job": j["name"], "why": f"{j['summary']}" + (f" (matched \"{phrase}\")" if phrase else ""),
            "alternatives": alts[:2], "matched_by": "keywords"}


def how_model(reg, query):
    """Ask the small tier, constrained to a schema, when no job matched well."""
    lines = []
    for j in reg["job"]:
        if j["leaves_mac"]:
            continue
        lines.append(f"- {j['name']}: {j['summary']}. e.g. {j['examples'][0]['cmd']}")
    prompt = ("Pick the one job that does what the request asks and write the exact command to run it, "
              "using only these jobs. Never pick a job that leaves the Mac. Answer as JSON "
              '{"job": name, "command": command, "why": one short sentence}.\n\nJOBS\n' + "\n".join(lines) + f"\n\nREQUEST: {query}")
    schema = {"type": "object", "properties": {"job": {"type": "string"}, "command": {"type": "string"}, "why": {"type": "string"}},
              "required": ["job", "command", "why"]}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(schema, f)
        sp = f.name
    try:
        p = subprocess.run([os.path.join(ROOT, "bin", "q"), "--json", "-m", "small", "--format", sp, prompt],
                           capture_output=True, text=True, timeout=120)
        env = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception as e:
        return None, f"the small model could not be reached ({e})"
    finally:
        os.unlink(sp)
    if not env.get("ok", True) or "data" not in env:
        return None, env.get("message", "the small model gave no structured answer")
    d = env["data"]
    j = resolve(reg, d.get("job", ""))
    if j is None or j["leaves_mac"]:
        return None, "the model named a job that does not exist or leaves this Mac"
    cmd = d.get("command", "")
    try:
        first = shlex.split(cmd)[:2]
    except ValueError:
        first = []
    if not first or first[0] not in ("lm", "q", "see", "review", "warm", "imagine", "probe") or "cloud" in cmd:
        return None, "the model's command did not start with a known tool"
    return {"command": cmd, "job": j["name"], "why": d.get("why", j["summary"]), "alternatives": [], "matched_by": "model"}, ""


def cmd_how(reg, args):
    as_json = "--json" in args
    go = "--go" in args
    no_model = "--no-model" in args
    color = "--color" in args
    words = [a for a in args if a not in ("--json", "--go", "--no-model", "--color")]
    query = " ".join(words).strip()
    p = Pal(color and not as_json)
    if not query:
        print('lm how: say what you want, e.g. lm how "text from my last screenshot"', file=sys.stderr)
        return 2
    ans = how_answer(reg, query)
    if ans is None and not no_model:
        ans, err = how_model(reg, query)
        if ans is None:
            return fail_how(as_json, "model_failed", err, 10)
    if ans is None:
        return fail_how(as_json, "no_match", "no job matches those words well enough; lm help lists the jobs, lm --capabilities has the menu", 12)
    if as_json:
        print(json.dumps(ans, ensure_ascii=False))
    else:
        print(f"{p.Bd}{p.C}{ans['command']}{p.Rs}")
        print(f"{p.Dm}why: {ans['why']}{p.Rs}")
        for a in ans["alternatives"]:
            print(f"{p.Dm}or:  {p.Rs}{p.C}{a['command']}{p.Rs}  {p.Dm}{a['says']}{p.Rs}")
    if go:
        if re.search(r"[<>]|\.\.\.", ans["command"]) or re.search(r"\b(shot|before|after|a|b|report|file|data|grid|dots|squares)\.(png|pdf|md|csv|xlsx)\b", ans["command"]):
            print("lm how: that command has a placeholder that needs your input, so it was not run", file=sys.stderr)
            return 2
        env = dict(os.environ, PATH=os.path.join(ROOT, "bin") + os.pathsep + os.environ.get("PATH", ""))
        sys.stdout.flush()
        return subprocess.run(ans["command"], shell=True, env=env).returncode
    return 0


def fail_how(as_json, code, msg, rc):
    if as_json:
        print(json.dumps({"ok": False, "code": code, "message": msg, "remedy": msg, "next": "lm help"}))
    else:
        print(f"lm how: {msg}", file=sys.stderr)
    return rc


# errors and hints


def remedy_for(reg, code):
    r = reg["remedies"].get(code)
    if r is None:
        return {"remedy": "see the message above; -h lists the flags and examples", "next": None}
    return {"remedy": r["remedy"], "next": r["next"] or None}


def hint_line(reg, key, color=False, **kw):
    h = reg["hints"].get(key)
    if not h:
        return ""
    p = Pal(color)
    text = h["text"]
    for k, v in kw.items():
        text = text.replace("{" + k + "}", str(v))
    return f"{p.Dm}next: {text}  ({h['why']}){p.Rs}"


# generation


def tool_rows(tool):
    """USAGE and OPTIONS rows parsed from `<tool> -h --all`, in plain text."""
    env = dict(os.environ, NO_COLOR="1")
    try:
        out = subprocess.run([os.path.join(ROOT, "bin", tool), "-h", "--all"], capture_output=True, text=True, timeout=30, env=env).stdout
    except Exception:
        return {}
    sections, cur = {}, None
    for line in out.splitlines():
        if re.match(r"^[A-Z][A-Z ]+$", line):
            cur = line.strip()
            sections[cur] = []
        elif cur and line.startswith("  "):
            m = re.match(r"^  (\S.*?)\s{2,}(\S.*)$", line)
            if m and not line.startswith("  $ "):
                sections[cur].append([m.group(1), m.group(2)])
            elif sections[cur] and line.startswith("   " * 5) and sections[cur]:
                sections[cur][-1][1] += " " + line.strip()
            elif m is None and line.strip() and not line.startswith("  $ "):
                sections[cur].append([line.strip(), ""])
    return sections


def flags_of(label):
    return re.findall(r"(?<![\w-])(--?[A-Za-z][\w-]*)", label)


def zsh_escape(s):
    return s.replace("\\", "\\\\").replace("'", "'\\''").replace("[", "\\[").replace("]", "\\]").replace(":", "\\:")


def zsh_desc(s):
    return s.replace("'", "'\\''").replace(":", "\\:")


SHOT_FN = r"""
_lm_shots() {
  local dir="${SEE_SCREENSHOT_DIR:-$(defaults read com.apple.screencapture location 2>/dev/null)}"
  [[ -n $dir ]] || dir="$HOME/Desktop"
  dir="${~dir}"
  local -a shots
  shots=( ${dir}/Screen*.png(N.om[1,8]) )
  _alternative \
    'special:shortcut:((paste\:"the image on your clipboard" latest\:"your newest screenshot"))' \
    'shots:recent screenshot:(${shots})' \
    'files:image file:_files -g "*.(png|jpg|jpeg|webp|gif|heic)"'
}
"""


def intents(root=ROOT):
    d = os.path.join(root, "intents")
    out = []
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".toml"):
            with open(os.path.join(d, fn), "rb") as f:
                t = tomllib.load(f)
            out.append((t.get("name", fn[:-5]), t.get("summary", "")))
    return out


def gen_zsh(reg):
    jobs = by_name(reg)
    files = {}
    header = "# generated by scripts/gen-verbs.sh from lib/verbs.toml; do not edit\n"

    verbs = [j for j in reg["job"] if j["kind"] != "topic"]
    desc = " ".join(f"'{zsh_desc(j['name'])}:{zsh_desc(j['summary'])}'" for j in verbs)
    helptopics = " ".join(f"'{zsh_desc(j['name'])}:{zsh_desc(j['summary'])}'" for j in reg["job"])

    def tool_flags(tool):
        rows = tool_rows(tool).get("OPTIONS", [])
        specs = []
        for label, d in rows:
            fl = flags_of(label)
            if not fl:
                continue
            short = d if len(d) <= 62 else d[:62].rsplit(" ", 1)[0].rstrip(",;:( ")
            tail = ""
            rest = label
            for f in fl:
                rest = rest.replace(f, "")
            rest = rest.replace(",", " ").strip()
            if rest and not rest.startswith("/") and not rest.startswith("["):
                if "FILE" in rest:
                    tail = ":file:_files"
                elif rest.startswith("M") and "model" in label:
                    tail = ":model:(small big code sweep)"
                elif rest[0].isupper() or rest[0] in "<":
                    tail = ":value:"
            for f in fl:
                specs.append(f"'{zsh_escape(f)}[{zsh_escape(short)}]{tail}'")
        return specs

    lm = [f"#compdef lm\n{header}{SHOT_FN}", "_lm() {", "  local -a verbs", f"  verbs=( {desc} )",
          "  if (( CURRENT == 2 )); then", "    _describe -t verbs 'lm verb' verbs", "    return", "  fi", "  case $words[2] in"]
    lm.append("    read) _lm_shots ;;")
    lm.append("    diff) _arguments '*:image:_files -g \"*.(png|jpg|jpeg|webp|gif|heic)\"' ;;")
    lm.append("    doc) _arguments '1:file:_files' ;;")
    lm.append(f"    help) local -a topics; topics=( {helptopics} ); _describe -t topics 'lm help topic' topics ;;")
    lm.append("    again) _values 'lane' '--big[the bigger reasoning model]' '--code[the coding model]' '--web[search the web first (leaves this Mac)]' ;;")
    lm.append("    fast) _values 'duration' off 30m 1h 2h 4h ;;")
    lm.append("    status|models|doctor) _values 'option' '--json[machine-readable]' ;;")
    lm.append("    timeline) _arguments '--errors[only failed calls]' '--all[include agents and hooks]' '--json[as JSON]' '--tool[one tool]:tool:(q see imagine fleet gemini)' ;;")
    lm.append("    last) _values 'tool' q see imagine fleet gemini --all ;;")
    lm.append("    q) words=( q \"${(@)words[3,-1]}\" ); (( CURRENT-=1 )); _q ;;")
    lm.append("    see) words=( see \"${(@)words[3,-1]}\" ); (( CURRENT-=1 )); _see ;;")
    lm.append("    warm) words=( warm \"${(@)words[3,-1]}\" ); (( CURRENT-=1 )); _warm ;;")
    lm.append("    how) _arguments '--go[run the command it finds]' '--json[as JSON]' '--no-model[match by words only]' '*:what you want:' ;;")
    lm.append("    *) _files ;;")
    lm.append("  esac")
    lm.append("}")
    lm.append("_lm \"$@\"")
    files["share/zsh/_lm"] = "\n".join(lm) + "\n"

    ints = " ".join(f"'{zsh_desc(n)}:{zsh_desc(s)}'" for n, s in intents())
    q = [f"#compdef q\n{header}", "_q() {", "  local -a intents", f"  intents=( {ints} )", "  local -a opts", "  opts=("]
    q += ["    " + s for s in tool_flags("q")]
    q += ["  )", "  if (( CURRENT == 2 )); then", "    _alternative 'intents:intent:_describe -t intents intent intents' 'flags:flag:compadd -a opts'", "    return",
          "  fi", "  _arguments -s $opts '*:prompt or file:_files'", "}", "_q \"$@\""]
    files["share/zsh/_q"] = "\n".join(q) + "\n"

    s = [f"#compdef see\n{header}{SHOT_FN}", "_see() {", "  local -a subs", "  subs=( 'paste:the image on your clipboard' 'latest:your newest screenshot' 'count:count objects by measuring pixels' 'odd:find the one item that differs' 'diff:what changed between two images' 'more:follow up on the last image' 'history:past reads' 'show:one full read' 'open:the artifact folder of a read' 'note:add a note to a read' 'reshoot:replay a loop recipe' )",
         "  local -a opts", "  opts=("]
    s += ["    " + x for x in tool_flags("see")]
    s += ["  )", "  if (( CURRENT == 2 )); then", "    _lm_shots", "    _describe -t subs 'see subcommand' subs", "    return", "  fi",
          "  _arguments -s $opts '*:image:_files -g \"*.(png|jpg|jpeg|webp|gif|heic)\"'", "}", "_see \"$@\""]
    files["share/zsh/_see"] = "\n".join(s) + "\n"

    w = [f"#compdef warm\n{header}", "_warm() {", "  local -a subs tiers", "  subs=( 'on:load a model for a while' 'off:unload and free the memory' 'status:what is loaded' 'restart:off, then on' )",
         "  tiers=( small big code sweep all forever 30m 1h 2h 4h )",
         "  if (( CURRENT == 2 )); then", "    _describe -t subs 'warm subcommand' subs", "    return", "  fi",
         "  case $words[2] in", "    on|off) _values 'tier or time' $tiers ;;", "    status) _values 'option' '--json[machine view]' ;;", "  esac", "}", "_warm \"$@\""]
    files["share/zsh/_warm"] = "\n".join(w) + "\n"
    return files


def roff(s):
    s = s.replace("\\", "\\e").replace("-", "\\-").replace('"', "\\(dq")
    return re.sub(r"^([.'])", r"\\&\1", s)


def cap(s):
    """Capitalise a sentence unless it opens with a command name, which stays as typed."""
    first = s.split()[0] if s.split() else ""
    return s if first in ("q", "see", "warm", "lm", "imagine", "opencode", "review") else s[:1].upper() + s[1:]


def man_page(reg, name):
    jobs = by_name(reg)
    j = jobs.get(name)
    title = name.upper()
    out = [f'.TH {title} 1 "" "local-models"', ".SH NAME"]
    if name == "lm":
        out.append(roff("lm - local models on this Mac: the front door to q, see, review, imagine and warm"))
    else:
        out.append(roff(f"{name} - {j['summary']}"))
    out += [".SH SYNOPSIS"]
    if name == "lm":
        out += [".B lm", roff('"question" | verb [args]'), ".br", ".B lm", ".RB [ \\-\\-capabilities ]", ".br", ".B lm how", roff('"what I want"')]
    else:
        out += [f".B {name}", roff(j["usage"][len(name):].strip())]
    out += [".SH DESCRIPTION"]
    if name == "lm":
        out += ["Local models on this Mac. Nothing leaves the machine unless a command is marked as leaving it",
                "(lm gemini, and q \\-\\-web).",
                ".PP", "Every command takes \\-h. This page is generated from lib/verbs.toml, the same registry",
                "that drives the lm screens, lm \\-\\-capabilities and lm how."]
    else:
        out += [roff(cap(j["summary"]) + "."), ".PP", roff("Input: " + j["inputs"] + "."), ".PP", roff("Output: " + j["output"] + ".")]
    if name == "lm":
        out += [".SH COMMANDS"]
        for jj in reg["job"]:
            if jj["kind"] == "topic":
                continue
            out += [".TP", f".B {roff(jj['usage'])}", roff(cap(jj["summary"]) + ("." if not jj["summary"].endswith(".") else "")
                                                               + (" Leaves this Mac." if jj["leaves_mac"] else ""))]
        out += [".SH AGENT MENU", ".TP", ".B lm \\-\\-capabilities [job] [\\-\\-json]", "Every job with its inputs, output shape, exit codes, cost and side effects.",
                ".TP", '.B lm how "what I want" [\\-\\-go] [\\-\\-json]', "Find the command for a request. Words first, the small model only when no job matches.", ]
    else:
        rows = tool_rows(name)
        if rows.get("OPTIONS"):
            out += [".SH OPTIONS"]
            for label, d in rows["OPTIONS"]:
                out += [".TP", f".B {roff(label)}", roff(d)]
    if name == "q":
        out += [".SH INTENTS"]
        for n, s in intents():
            out += [".TP", f".B {roff(n)}", roff(cap(s) + ".")]
    out += [".SH EXAMPLES"]
    exs = []
    if name == "lm":
        for jj in reg["job"]:
            if jj["kind"] == "job" and jj["examples"] and jj["examples"][0]["cmd"].startswith("lm"):
                exs.append(jj["examples"][0])
    else:
        exs = j["examples"]
    for e in exs:
        out += [".TP", f".B {roff(e['cmd'])}", roff(cap(e["says"]) + ".")]
    out += [".SH EXIT STATUS"]
    for k, v in reg["conventions"]["exit_codes"].items():
        out += [".TP", f".B {k}", roff(v[0].upper() + v[1:] + ".")]
    out += [".SH FILES", ".TP", ".B logs/*\\-history.jsonl", "One JSON line per call. History is per terminal by default; \\-\\-all or LM_ALL=1 reaches every caller.",
            ".SH SEE ALSO", roff(", ".join(f"{n}(1)" for n in ("lm", "q", "see", "warm") if n != name) + ", imagine, review"), ""]
    return "\n".join(out)


def tldr_page(reg, name):
    jobs = by_name(reg)
    if name == "lm":
        picks = []
        for n in ("ask", "cmd", "read", "doc", "again", "find"):
            j = jobs[n]
            e = next(x for x in j["examples"] if x["cmd"].startswith("lm") and not x.get("cloud"))
            picks.append((cap(j["summary"]), e["cmd"]))
        picks[2] = ("Read the text or an answer out of an image", jobs["read"]["examples"][0]["cmd"])
        picks.insert(3, ("Read your newest screenshot", jobs["read"]["examples"][3]["cmd"]))
        picks.append(("Find the command for what you want, without running it", jobs["how"]["examples"][0]["cmd"]))
        head = "Local models on this Mac: answers, shell commands, image reads. Nothing leaves the machine unless marked."
    else:
        picks = [(cap(e["says"]), e["cmd"]) for e in jobs[name]["examples"][:8]]
        head = cap(jobs[name]["summary"]) + "."
    out = [f"# {name}", "", f"> {head}", f"> More information: `man {name}` or `lm --capabilities`.", ""]
    for d, cmd in picks:
        out += [f"- {d.rstrip('.')}:", "", f"`{re.sub(r'<([a-z|]+)>', r'{{\\1}}', cmd)}`", ""]
    return "\n".join(out)


def doc_block(reg):
    plain = "\n".join(screen_front(reg, Pal(False)))
    out = ["<!-- generated by scripts/gen-verbs.sh from lib/verbs.toml; edit the registry, not this block -->", "",
           "```text", plain, "```", "",
           "| Command | What it does | Cost | Leaves the Mac |", "|---|---|---|---|"]
    for j in reg["job"]:
        out.append(f"| `{j['usage']}` | {j['summary']} | {j['cost_tier']}, {j['cost_secs']} s | {'yes' if j['leaves_mac'] else 'no'} |")
    out += ["", "`lm --capabilities --json` is the same table for an agent, and `lm how \"what I want\"` finds the command for a request.", ""]
    return "\n".join(out)


def generate(reg):
    files = gen_zsh(reg)
    for n in ("lm", "q", "see", "warm"):
        files[f"share/man/man1/{n}.1"] = man_page(reg, n)
        files[f"share/tldr/{n}.page.md"] = tldr_page(reg, n) + "\n"
    files["_docblock.md"] = doc_block(reg)
    return files


def cmd_gen(reg, args):
    out = root = None
    if "--out" in args:
        out = args[args.index("--out") + 1]
    if "--root" in args:
        root = args[args.index("--root") + 1]
    files = generate(reg)
    base = out or root
    if not base:
        print("verbs.py gen: give --out DIR or --root ROOT", file=sys.stderr)
        return 2
    for rel, body in files.items():
        if rel == "_docblock.md" and root:
            continue
        path = os.path.join(base, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
    if root:
        doc = os.path.join(root, "docs", "CAPABILITIES.md")
        with open(doc, encoding="utf-8") as f:
            text = f.read()
        new, n = re.subn(r"(<!-- verbs:begin -->\n).*?(<!-- verbs:end -->)", lambda m: m.group(1) + files["_docblock.md"] + m.group(2), text, flags=re.S)
        if n != 1:
            print("verbs.py gen: docs/CAPABILITIES.md has no verbs:begin / verbs:end markers", file=sys.stderr)
            return 2
        with open(doc, "w", encoding="utf-8") as f:
            f.write(new)
    return 0


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    reg = load()
    cmd, args = argv[0], argv[1:]
    color = "--color" in args
    args_nc = [a for a in args if a != "--color"]
    if cmd == "screen":
        which = args_nc[0] if args_nc else "front"
        rest = args_nc[1:]
        if which == "capabilities":
            job = next((a for a in rest if not a.startswith("--")), None)
            if "--json" in rest:
                j = capabilities_json(reg, job)
                if j is None:
                    print(json.dumps({"ok": False, "code": "unknown_job", "message": f"no job '{job}'", "remedy": "lm --capabilities lists them", "next": "lm --capabilities"}))
                    return 2
                print(json.dumps(j, ensure_ascii=False))
                return 0
            lines, rc = screen_capabilities(reg, Pal(color), job)
        elif which == "front":
            lines, rc = screen_front(reg, Pal(color)), 0
        elif which == "more":
            lines, rc = screen_more(reg, Pal(color)), 0
        elif which == "help":
            lines, rc = screen_help(reg, Pal(color), rest[0] if rest else "")
        else:
            print(f"verbs.py screen: unknown screen {which}", file=sys.stderr)
            return 2
        print("\n".join(lines), file=sys.stderr if rc else sys.stdout)
        return rc
    if cmd == "how":
        return cmd_how(reg, args)
    if cmd == "remedy":
        print(json.dumps(remedy_for(reg, args_nc[0] if args_nc else ""), ensure_ascii=False))
        return 0
    if cmd == "hint":
        kw = {}
        if "--n" in args_nc:
            kw["n"] = args_nc[args_nc.index("--n") + 1]
        if "--img" in args_nc:
            kw["img"] = shlex.quote(args_nc[args_nc.index("--img") + 1])
        line = hint_line(reg, args_nc[0], color, **kw)
        if not line:
            return 1
        print(line)
        return 0
    if cmd == "gen":
        return cmd_gen(reg, args_nc)
    print(f"verbs.py: unknown command {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
