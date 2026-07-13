#!/usr/bin/env python3
"""The convergence ledger for visual-compare loops: tracks how a recreated image's
divergences evolve across fix rounds and says when the loop should stop.

    vis-ledger.py add <loop-dir> <verdict.json> [--pack <evidence.json>]
    vis-ledger.py status <loop-dir>

JSON in/out, no model, no PIL (bare python3). Status words (new/persisting/
regressed/fixed) are set comparisons over divergence ids — script territory, the
judge never assigns them. Adds are sequential by design (one controlling agent
per loop); there is no file lock, so concurrent adds would lose an update.
Semantics + loop protocol: docs/10 §2 L3, §5.6–5.7.
"""
import argparse
import json
import os
import sys
import time


def die(msg, fix):
    print(json.dumps({"ok": False, "error": msg, "fix": fix}))
    sys.exit(2)


def expect(cond, msg, fix):
    """Shape gate: valid JSON of the wrong structure must die structured, never
    reach a .get()/[...] that tracebacks (adversarial validation 2026-07-12)."""
    if not cond:
        die(msg, fix)


def validate_ledger(ledger, path):
    ok = (isinstance(ledger, dict) and isinstance(ledger.get("rounds"), list)
          and all(isinstance(r, dict) and isinstance(r.get("divergences", {}), dict)
                  for r in ledger.get("rounds", [])))
    expect(ok, "ledger at %s is corrupted or an unexpected shape" % path,
           "move it aside and restart the loop (trash %s), or restore it from a backup" % path)


def load_json(path, what):
    try:
        with open(path) as f:
            return json.load(f)
    except OSError as e:
        die("%s unreadable: %s" % (what, e),
            "check the path — expected a %s file at %s" % (what, path))
    except ValueError as e:
        die("%s is not valid JSON: %s" % (what, e),
            "re-generate it; a truncated write is the usual cause")


def ledger_path(loopdir):
    return os.path.join(loopdir, "ledger.json")


def load_ledger(loopdir):
    p = ledger_path(loopdir)
    if not os.path.exists(p):
        return {"loop": os.path.basename(os.path.abspath(loopdir)), "rounds": []}
    ledger = load_json(p, "ledger")
    validate_ledger(ledger, p)
    return ledger


def write_atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1)
    os.replace(tmp, path)


def round_ids(rnd):
    return set(rnd.get("divergences", {}).keys())


def signals_for(rounds):
    """Recompute the convergence signals from the recorded rounds — `status`
    reads them the same way `add` produced them, so the two never disagree.

    Progress is stated IN-BAND, and only from transitions. The scores in each
    round are recorded but are NOT a convergence signal: region/pixel metrics
    saturate the moment composition moves, so they go sideways (or backwards)
    while the candidate is genuinely converging — measured live on the imagegen
    loop, where a round fixed 3 of 5 divergences as grid-delta rose 93.8% ->
    100.0%. A loop that stopped on 'scores plateaued' would quit exactly when it
    was working, so the tool says so rather than leaving it to be misread."""
    if not rounds:
        return {"stop": None, "stall": False, "stall_rounds": 0, "next": [],
                "progress": None}
    last = rounds[-1]
    streak = last.get("stall_streak", 0)
    stall = streak >= 2
    stop = "policy-pass" if last.get("overall") == "pass" else None
    t = last.get("transitions", {})
    progress = {
        "fixed_this_round": len(t.get("fixed", [])),
        "open": len(last.get("divergences", {})),
        "source": "ledger transitions — the round's scores are recorded but are "
                  "NOT a convergence signal (they saturate on any composition change)",
    }
    nudges = []
    if stop:
        nudges.append({"reason": "judge ruled pass — loop converged",
                       "cmd": "stop; ledger is the acceptance record"})
    elif last.get("overall") == "pass-with-notes":
        nudges.append({"reason": "pass-with-notes — divergences remain but none the "
                                 "policy chases; converged is the user's call",
                       "cmd": "stop, or /vis-compare --revisit all --feedback '<what still bothers you>'"})
    if stall:
        nudges.append({"reason": "loop stalled — %d consecutive rounds with zero fixed" % streak,
                       "cmd": "/vis-compare %s %s  # full native judgment, or stop and rethink the fixes"
                              % (last.get("a", "<A>"), last.get("b", "<B>"))})
    return {"stop": stop, "stall": stall, "stall_rounds": streak, "next": nudges,
            "progress": progress}


def add_round(args):
    verdict = load_json(args.verdict, "verdict")
    expect(isinstance(verdict, dict),
           "verdict is not a JSON object (got %s)" % type(verdict).__name__,
           "re-run the judge — verdict.json must be the object docs/10 §5 describes")
    pack, meta = None, {}
    if args.pack:
        pack = load_json(args.pack, "evidence pack")
        expect(isinstance(pack, dict) and isinstance(pack.get("meta", {}), dict),
               "evidence pack is not a JSON object with an object `meta`",
               "pass the evidence.json that `see diff --json` writes (its .evidence)")
        meta = pack.get("meta", {})
        if meta.get("comparable") == "poor":
            die("pair is not comparable (%s) — a loop round against it would measure noise"
                % (meta.get("comparable_why") or "see pack meta"),
                "crop both sides to a shared region first: see diff <cropped-A> <cropped-B> --json")

    divs = verdict.get("divergences", [])
    expect(isinstance(divs, list) and all(isinstance(d, dict) for d in divs),
           "verdict.divergences must be a list of objects (got %s)" % type(divs).__name__,
           "re-run the judge — each divergence is an object with an id (docs/10 §5)")
    ids = [d.get("id") for d in divs]
    if any(not i for i in ids):
        die("a divergence has no id — the ledger keys every status on stable ids",
            "re-run the judge; verdict.json divergences[] must each carry an id")
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        die("duplicate divergence id(s): %s" % ", ".join(dupes),
            "ids must be unique per verdict; re-run the judge or fix the verdict file")

    ledger = load_ledger(args.loopdir)
    rounds = ledger["rounds"]
    prev = round_ids(rounds[-1]) if rounds else set()
    ever = set().union(*[round_ids(r) for r in rounds]) if rounds else set()
    now = set(ids)

    transitions = {
        "new": sorted(now - ever),
        "persisting": sorted(now & prev),
        "regressed": sorted((now & ever) - prev),
        "fixed": sorted(prev - now),
    }
    # the stall clock only ticks once there was a previous round to improve on
    streak = (rounds[-1].get("stall_streak", 0) + 1) if (rounds and not transitions["fixed"]) else 0

    iteration = len(rounds) + 1
    note = None
    if verdict.get("iteration") not in (None, iteration):
        note = ("verdict says iteration %s but this is round %s of the loop dir — "
                "recorded as %s" % (verdict.get("iteration"), iteration, iteration))

    rnd = {
        "iteration": iteration,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "overall": verdict.get("overall"),
        "policy_version": verdict.get("policy_version"),
        "stall_streak": streak,
        "divergences": {d["id"]: {"class": d.get("class"), "judgment": d.get("judgment"),
                                  "status": ("persisting" if d["id"] in transitions["persisting"]
                                             else "regressed" if d["id"] in transitions["regressed"]
                                             else "new")}
                        for d in divs},
        "transitions": transitions,
    }
    if pack is not None:
        rnd["scores"] = pack.get("scores", {})
        rnd["a"], rnd["b"] = meta.get("a"), meta.get("b")

    expect(not (os.path.exists(args.loopdir) and not os.path.isdir(args.loopdir)),
           "loop-dir %s exists and is a file, not a directory" % args.loopdir,
           "pick a directory path (convention: outputs/see/loops/<slug>/)")
    rounds.append(rnd)
    try:
        os.makedirs(args.loopdir, exist_ok=True)
        write_atomic(ledger_path(args.loopdir), ledger)
    except OSError as e:
        die("cannot write the ledger: %s" % e,
            "check permissions on %s (or choose a writable loop-dir)" % args.loopdir)

    out = {"ok": True, "iteration": iteration, "transitions": transitions,
           "signals": signals_for(rounds)}
    if note:
        out["note"] = note
    print(json.dumps(out, indent=1))


def show_status(args):
    p = ledger_path(args.loopdir)
    if not os.path.exists(p):
        die("no ledger at %s" % p,
            "start the loop: vis-ledger.py add %s <verdict.json>" % args.loopdir)
    ledger = load_json(p, "ledger")
    validate_ledger(ledger, p)
    rounds = ledger.get("rounds", [])
    last = rounds[-1] if rounds else {}
    print(json.dumps({"ok": True, "loop": ledger.get("loop"), "rounds": len(rounds),
                      "last": {k: last.get(k) for k in
                               ("iteration", "ts", "overall", "transitions")},
                      "signals": signals_for(rounds)}, indent=1))


def main():
    ap = argparse.ArgumentParser(description="visual-compare loop ledger (L3)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="ingest one round's verdict.json")
    a.add_argument("loopdir")
    a.add_argument("verdict")
    a.add_argument("--pack", help="the round's evidence-pack json (enables the "
                                  "comparable-poor hard block + score trend)")
    a.set_defaults(fn=add_round)
    s = sub.add_parser("status", help="current loop state + signals, read-only")
    s.add_argument("loopdir")
    s.set_defaults(fn=show_status)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
