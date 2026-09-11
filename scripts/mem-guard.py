#!/usr/bin/env python3
"""mem-guard — preemptive memory watchdog for the local-model suite.

The problem it solves: a model load (mlx-vlm, or two ollama models at once) can
exhaust unified memory on this 64 GB machine and trip the kernel's jetsam killer,
which takes down UNRELATED processes — every Claude agent on the box included.
This watchdog watches memory PRESSURE and, before the kernel does anything, kills
the largest MODEL process (mlx-vlm / the ollama llama-server runner) to relieve it.

Trigger signal (fixed after adversarial review 2026-09-12): the primary signal is
the kernel's own memory-pressure level (kern.memorystatus_vm_pressure_level: 1
normal, 2 warn, 4 critical), because raw free+inactive pages LAG real pressure on
macOS — the OS compresses and swaps to keep "free" looking healthy right up to
jetsam. A low free-page floor is kept as a coarse secondary trigger.

It never targets agent processes: the kill-set is model-loader commands only, and
the never-list is matched against process IDENTITY (each token's basename) so a
model launched from a path that merely CONTAINS "claude"/"node" is not spared.
Every action is logged to logs/mem-guard.jsonl.

Usage:
  mem-guard.py --once                 print current memory/pressure + would-kill target
  mem-guard.py [--threshold-gb 8] [--pressure-level 2] [--interval 3]
      [--max-runtime 7200] [--stop-file PATH]    run the daemon

Stop: touch the stop-file (default /tmp/mem-guard.stop) or kill the pid in
/tmp/mem-guard.pid. A second daemon refuses to start while one is already live.
"""
import json, os, re, signal, subprocess, sys, time

PAGE = 16384  # Apple Silicon page size (bytes)
# llama-server is the ollama runner that actually HOLDS model memory (verified: model
# RSS lives there, not in `ollama serve`). mlx_* cover the mlx-vlm path. The old
# ollama.*runn / ollama_llama branches matched nothing on this build and were dropped;
# if ollama renames its runner, add the new name here.
KILLSET = re.compile(r"(mlx_vlm|mlx\.launch|mlx_lm|llama[-_]server)", re.I)
# Agent processes to never kill. Matched against IDENTITY, not the full command path.
NEVER = re.compile(r"(claude|node|Cursor|Electron|Code Helper|com\.apple)", re.I)
LOG = os.path.expanduser("~/Code/local-models/logs/mem-guard.jsonl")
PID_FILE = "/tmp/mem-guard.pid"


def total_bytes():
    out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True)
    return int(out.stdout.strip() or 0)


def pressure_level():
    """Kernel memory-pressure level: 1 normal, 2 warn, 4 critical. None if unreadable.

    This is the jetsam-predictive signal — it rises as the compressor/swap saturate,
    which free-page counts do not reflect until much later.
    """
    out = subprocess.run(["sysctl", "-n", "kern.memorystatus_vm_pressure_level"],
                         capture_output=True, text=True)
    try:
        return int(out.stdout.strip())
    except ValueError:
        return None


def swap_used_mb():
    out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True)
    m = re.search(r"used\s*=\s*([\d.]+)M", out.stdout)
    return float(m.group(1)) if m else 0.0


def available_bytes():
    """Coarse secondary signal: reclaimable pages. Inflated (counts inactive), so it
    is only a floor backstop; pressure_level() is the real trigger."""
    out = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
    def pages(label):
        m = re.search(rf"{label}:\s+(\d+)\.", out)
        return int(m.group(1)) if m else 0
    free = pages("Pages free") + pages("Pages inactive") + \
        pages("Pages speculative") + pages("Pages purgeable")
    return free * PAGE


def identity(cmd):
    """The command with each path token reduced to its basename, so the never-list
    matches a process's real identity and not a coincidental substring in its launch
    path (e.g. a model venv living under ~/Code/Claude)."""
    return " ".join(os.path.basename(t) if "/" in t else t for t in cmd.split())


def model_procs():
    """Model-loader processes only, as (pid, rss_bytes, command), largest first."""
    out = subprocess.run(["ps", "-axo", "pid=,rss=,command="], capture_output=True, text=True).stdout
    procs = []
    for line in out.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) < 3:
            continue
        pid, rss, cmd = parts
        if not KILLSET.search(cmd) or NEVER.search(identity(cmd)):
            continue
        if int(pid) == os.getpid():
            continue
        procs.append((int(pid), int(rss) * 1024, cmd))
    return sorted(procs, key=lambda p: -p[1])


def logrec(rec):
    rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


def gib(b):
    return round(b / 1024**3, 1)


def status():
    tot, avail = total_bytes(), available_bytes()
    lvl, swap = pressure_level(), swap_used_mb()
    procs = model_procs()
    lvln = {1: "normal", 2: "warn", 4: "critical"}.get(lvl, str(lvl))
    print(f"total={gib(tot)}G  available~={gib(avail)}G (inflated)  "
          f"pressure={lvln}  swap_used={swap:.0f}M")
    if procs:
        print("model processes (largest first):")
        for pid, rss, cmd in procs[:6]:
            print(f"  pid {pid}  rss {gib(rss)}G  {cmd[:90]}")
    else:
        print("no model-loader processes running")
    return lvl, avail, procs


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return pid_perm_error(pid)
    except OSError:
        return False


def pid_perm_error(pid):
    # EPERM means it exists but is another user's — treat as alive (and unkillable).
    return True


def kill_one(pid, rss, cmd, reason):
    logrec({"action": "kill", "pid": pid, "rss_gb": gib(rss), "cmd": cmd[:200], "reason": reason})
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)
        os.kill(pid, 0)
        os.kill(pid, signal.SIGKILL)
        time.sleep(1)
    except ProcessLookupError:
        return True          # gone
    except PermissionError:
        logrec({"action": "kill-blocked", "pid": pid, "reason": "EPERM (another user)"})
        return False
    except Exception as e:
        logrec({"action": "kill-error", "pid": pid, "err": str(e)})
        return False
    # SIGKILL was sent; report whether it is actually gone
    try:
        os.kill(pid, 0)
        return False
    except ProcessLookupError:
        return True


def other_guard_running():
    """True if another mem-guard.py process is alive. Uses pgrep on the SCRIPT name,
    not the pidfile's bare pid — a stale pidfile whose pid has been reused by an
    unrelated process would otherwise fool both this check and see's preflight."""
    out = subprocess.run(["pgrep", "-f", "scripts/mem-guard.py"], capture_output=True, text=True)
    pids = [int(x) for x in out.stdout.split() if x.strip().isdigit()]
    return any(p != os.getpid() for p in pids)


def daemon(threshold_gb, pressure_trigger, interval, max_runtime, stop_file):
    # Single-instance: refuse to start if another real daemon is already running.
    if other_guard_running():
        print("mem-guard: already running; not starting a second")
        return
    thr = threshold_gb * 1024**3
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    logrec({"action": "start", "pid": os.getpid(), "threshold_gb": threshold_gb,
            "pressure_trigger": pressure_trigger, "interval": interval, "max_runtime": max_runtime})
    t0 = time.time()
    unkillable = {}   # pid -> last-attempt time, so a survivor is not retried every tick
    while True:
        if os.path.exists(stop_file):
            logrec({"action": "stop", "reason": "stop-file"})
            os.remove(stop_file)
            break
        if time.time() - t0 > max_runtime:
            logrec({"action": "stop", "reason": "max-runtime"})
            break
        lvl = pressure_level()
        avail = available_bytes()
        fire = (lvl is not None and lvl >= pressure_trigger) or avail < thr
        if fire:
            procs = [p for p in model_procs()
                     if time.time() - unkillable.get(p[0], 0) > 30]
            if procs:
                pid, rss, cmd = procs[0]
                reason = f"pressure={lvl} avail={gib(avail)}G"
                if not kill_one(pid, rss, cmd, reason):
                    unkillable[pid] = time.time()   # skip it for 30s, don't tight-loop
            else:
                logrec({"action": "pressure-no-target", "level": lvl, "available_gb": gib(avail)})
        time.sleep(interval)
    try:
        if int(open(PID_FILE).read().strip()) == os.getpid():
            os.remove(PID_FILE)
    except (ValueError, OSError):
        pass


def main():
    a = sys.argv[1:]
    if "--once" in a:
        status()
        return
    def opt(name, default, cast=float):
        return cast(a[a.index(name) + 1]) if name in a else default
    daemon(threshold_gb=opt("--threshold-gb", 8.0),
           pressure_trigger=opt("--pressure-level", 2, int),
           interval=opt("--interval", 3.0),
           max_runtime=opt("--max-runtime", 7200, int),
           stop_file=(a[a.index("--stop-file") + 1] if "--stop-file" in a else "/tmp/mem-guard.stop"))


if __name__ == "__main__":
    main()
