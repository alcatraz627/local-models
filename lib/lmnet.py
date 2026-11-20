#!/usr/bin/env python3
"""lm net: let other devices on your network use this machine's models, and use theirs.

One machine offers its models (it "serves"); other devices ask it to do work.
The person who owns the serving machine approves each device once, and that one
approval covers everything the machine offers until they switch the device off.
Every request, allowed or refused, is written to a log.

It needs only the Python standard library, so it runs the same on macOS, Linux
and Windows. Run `lm net help` for the commands.
"""
import base64
import hashlib
import json
import os
import pathlib
import platform
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO = pathlib.Path(__file__).resolve().parent.parent
SERVICES = ("see", "imagine")   # what this machine can do for an approved device
MAX_WAITING, MIN_FREE_GB, JOB_TIMEOUT_S, MAX_BODY = 3, 2, 180, 60 * 1024 * 1024
RENDER_TIMEOUT_S = 900          # the largest image model takes minutes, not seconds


class Settings:
    """Everything lm net reads from the environment, in one place. The defaults mirror config.sh."""

    env = os.environ
    home = pathlib.Path(env.get("LM_NET_HOME") or pathlib.Path.home() / ".config" / "lm" / "net")
    port = int(env.get("LM_NET_PORT") or 5119)
    log = pathlib.Path(env.get("LM_NET_LOG") or REPO / "logs" / "net-history.jsonl")
    see = env.get("LM_NET_SEE") or str(REPO / "bin" / "see")
    imagine = env.get("LM_NET_IMAGINE") or str(REPO / "imagine-kit" / "imagine")
    name = env.get("LM_NET_NAME") or ""


class NetError(Exception):
    """A refusal or failure with a stable `code`, an HTTP status and words for a person."""

    def __init__(self, code, plain, status=400):
        super().__init__(plain)
        self.code, self.plain, self.status = code, plain, status


def read_json(path, default):
    try:
        return json.loads(pathlib.Path(path).read_text())
    except (OSError, ValueError):
        return default


def write_json(path, data):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    tmp.replace(path)


def this_name():
    return Settings.name or socket.gethostname().split(".")[0]


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def free_gb():
    """Memory this machine can hand out now, in GB. A large number when it cannot be read."""
    try:
        if platform.system() == "Darwin":
            vm = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
            page = int(vm.split("page size of ")[1].split()[0])
            count = lambda key: int(vm.split(key + ":")[1].split(".")[0])
            pages = sum(count(k) for k in ("Pages free", "Pages inactive", "Pages purgeable", "Pages speculative"))
            return pages * page / 2**30
        for line in pathlib.Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) / 2**20
    except (OSError, ValueError, IndexError):
        pass
    return 999.0


def tailnet_name(ip):
    """The name Tailscale vouches for at this address, or "" when it cannot vouch for one."""
    if not shutil.which("tailscale"):
        return ""
    try:
        out = subprocess.run(["tailscale", "whois", "--json", ip], capture_output=True, text=True, timeout=5)
        node = json.loads(out.stdout).get("Node", {})
        return (node.get("ComputedName") or node.get("Hostinfo", {}).get("Hostname") or "").lower()
    except (OSError, ValueError, subprocess.SubprocessError):
        return ""


# The device list: who has asked to use this machine, and what the owner said.

class Devices:
    """The serving machine's list of devices and the owner's answer for each.

    A device is `approved`, `pending` (it asked and the owner has not answered),
    `off` (approved once, switched off for now) or `expected` (the owner named it
    before it ever connected). One answer covers every service.
    """

    def __init__(self, home):
        self.path = pathlib.Path(home) / "devices.json"
        self.lock = threading.Lock()

    def all(self):
        return read_json(self.path, [])

    def find(self, name):
        return next((d for d in self.all() if d["name"].lower() == name.lower()), None)

    def _save(self, rows):
        write_json(self.path, rows)

    def meet(self, name, secret, ip, vouched=""):
        """Record a request from a device and return its row. Decides nothing the owner has not decided."""
        key = hashlib.sha256(secret.encode()).hexdigest()
        with self.lock:
            rows = self.all()
            row = next((d for d in rows if d.get("key") == key), None)
            if row is None:
                expected = next((d for d in rows if d["state"] == "expected" and d["name"].lower() == name.lower()), None)
                if expected and vouched == name.lower():
                    # The owner named this device ahead of time and the network confirms who it is.
                    row = expected
                    row.update(key=key, state="approved", note="approved ahead of time, confirmed by Tailscale")
                else:
                    taken = any(d["name"].lower() == name.lower() and d.get("key") for d in rows)
                    row = {"name": name + ("-2" if taken else ""), "key": key, "state": "pending", "first_seen": now(),
                           "note": "uses a name another device already has" if taken else
                                   ("named ahead of time, but the network could not confirm it" if expected else "")}
                    rows.append(row)
            row.update(last_seen=now(), ip=ip)
            self._save(rows)
            return dict(row)

    def decide(self, name, state):
        """The owner's answer for a device: approved or off. Naming an unknown device expects it."""
        with self.lock:
            rows = self.all()
            row = next((d for d in rows if d["name"].lower() == name.lower()), None)
            if row is None:
                if state != "approved":
                    raise NetError("no_such_device", f"There is no device called {name}.")
                row = {"name": name, "key": "", "state": "expected", "first_seen": now(), "note": "named ahead of time"}
                rows.append(row)
            elif row["state"] != "expected":
                row["state"] = state
            row["decided"] = now()
            self._save(rows)
            return dict(row)

    def forget(self, name):
        with self.lock:
            rows = self.all()
            kept = [d for d in rows if d["name"].lower() != name.lower()]
            if len(kept) == len(rows):
                raise NetError("no_such_device", f"There is no device called {name}.")
            self._save(kept)


def log_request(device, service, verdict, secs=0, detail=""):
    """One line per request, allowed or refused, so the owner can see who used what."""
    Settings.log.parent.mkdir(parents=True, exist_ok=True)
    row = {"ts": now(), "device": device, "service": service, "verdict": verdict, "secs": secs}
    if detail:
        row["detail"] = detail[:200]
    with open(Settings.log, "a") as f:
        f.write(json.dumps(row) + "\n")


# The serving side.

class Host:
    """This machine as a server: the device list, one job at a time, and the work it offers."""

    def __init__(self, home=None, vouch=tailnet_name):
        self.devices = Devices(home or Settings.home)
        self.name = this_name()
        self.vouch = vouch
        self.busy = threading.Lock()
        self.waiting = 0
        self.count = threading.Lock()

    def admit(self, name, secret, ip, service):
        """Return the device's row when it may use this machine; raise a refusal a person can act on otherwise."""
        if not name or len(secret) < 16:
            raise NetError("no_identity", "This request did not say which device it is from.", 401)
        known = self.devices.find(name)
        vouched = self.vouch(ip) if (known and known["state"] == "expected") else ""
        row = self.devices.meet(name, secret, ip, vouched)
        if row["state"] == "approved":
            return row
        host = self.name
        if row["state"] == "off":
            log_request(row["name"], service, "refused: switched off")
            raise NetError("switched_off", f"{host} has switched this device off for now.", 403)
        log_request(row["name"], service, "refused: waiting for approval")
        raise NetError("waiting", f"This device is waiting for approval on {host}. "
                       f"Its owner approves it once with: lm net approve {row['name']}", 403)

    def run(self, job):
        """Run one piece of work now, or wait behind a few others; refuse when too many wait or memory is short."""
        with self.count:
            if self.waiting >= MAX_WAITING:
                raise NetError("busy", f"{self.name} is busy with other work. Try again in a minute.", 503)
            self.waiting += 1
        try:
            with self.busy:
                if free_gb() < MIN_FREE_GB:
                    raise NetError("low_memory", f"{self.name} is short on memory right now, so it did not start.", 503)
                return job()
        finally:
            with self.count:
                self.waiting -= 1

    def see(self, args):
        try:
            out = subprocess.run([Settings.see, *args], capture_output=True, text=True, timeout=JOB_TIMEOUT_S,
                                 env=dict(os.environ, NO_COLOR="1"))
        except subprocess.TimeoutExpired:
            raise NetError("timeout", "The vision model took too long on this picture and was stopped.", 502)
        except OSError:
            raise NetError("not_installed", f"{self.name} has no vision tool to run.", 502)
        if out.returncode != 0:
            raise NetError("see_failed", "The vision model could not read this picture.", 502)
        try:
            return json.loads(out.stdout)
        except ValueError:
            return {"text": out.stdout.strip()}

    def see_read(self, body, folder):
        picture = save_picture(body.get("image"), body.get("name"), folder)
        if body.get("text"):
            return {"text": self.see([picture, "--ocr"]).get("text", "")}
        got = self.see([picture, body.get("question") or "Describe this picture.", "--json"])
        return {"answer": got.get("read") or got.get("answer") or got.get("text") or got}

    def see_diff(self, body, folder):
        a = save_picture(body.get("a"), body.get("a_name"), folder)
        b = save_picture(body.get("b"), body.get("b_name"), folder)
        got = self.see(["diff", a, b, body.get("focus") or "What changed between the first and the second picture?",
                        "--json"])
        return {"answer": got.get("read") or got.get("judged") or got.get("prose") or got.get("text") or got,
                "evidence_summary": got.get("summary")}

    def imagine_render(self, body, folder):
        """Draw one image for another device with this machine's image kit, and send the picture back."""
        req = body.get("request") or {}
        prompt = " ".join(str(req.get("prompt", "")).split())
        if not prompt:
            raise NetError("empty_prompt", "The request had no prompt.")
        args = ["gen", prompt, "--json"]
        for src in (body.get("sources") or [])[:4]:
            args += ["--from", save_picture(src.get("image"), src.get("name"), folder)]
        if req.get("use") == "start":
            args += ["--loose", str(float(req.get("strength") or 0.5))]
        for flag, key in (("--model", "model"), ("--style", "style"), ("--steps", "steps"), ("--seed", "seed")):
            if req.get(key) not in (None, ""):
                args += [flag, str(req[key])]
        if req.get("width") and req.get("height"):
            args += ["--size", f"{int(req['width'])}x{int(req['height'])}"]
        try:
            out = subprocess.run([Settings.imagine, *args], capture_output=True, text=True, timeout=RENDER_TIMEOUT_S,
                                 env=dict(os.environ, IMAGINE_KIT_DATA=str(self.devices.path.parent / "imagine")))
        except subprocess.TimeoutExpired:
            raise NetError("timeout", f"{self.name} took too long on this image and stopped.", 502)
        except OSError:
            raise NetError("not_installed", f"{self.name} has no image kit to run.", 502)
        if out.returncode != 0:
            words = out.stderr.strip().splitlines()
            raise NetError("render_failed", (words[0].replace("imagine: ", "", 1) if words else "The render failed.")
                           + (" " + words[1].strip() if len(words) > 1 else ""), 502)
        record = json.loads(out.stdout.strip().splitlines()[-1])
        picture = pathlib.Path(record["output"])
        keep = ("model", "mode", "steps", "guidance", "width", "height", "quant", "seed", "secs", "full_prompt")
        return {"image": base64.b64encode(picture.read_bytes()).decode(), "record": {k: record.get(k) for k in keep}}

    ROUTES = {"/v1/see/read": ("see", "see_read"), "/v1/see/diff": ("see", "see_diff"),
              "/v1/imagine/render": ("imagine", "imagine_render")}


def save_picture(b64, name, folder):
    ext = (pathlib.Path(name or "").suffix or ".png").lower()
    if ext not in (".png", ".jpg", ".jpeg", ".heic", ".webp", ".tiff", ".gif"):
        raise NetError("not_a_picture", "That file is not a picture.")
    path = pathlib.Path(folder) / (secrets.token_hex(4) + ext)
    try:
        path.write_bytes(base64.b64decode(b64 or ""))
    except (ValueError, TypeError):
        raise NetError("not_a_picture", "The picture could not be read.")
    if path.stat().st_size < 100:
        raise NetError("empty_picture", "The picture arrived empty.")
    return str(path)


def make_handler(host):
    class Handler(BaseHTTPRequestHandler):
        server_version = "lm-net/1"

        def log_message(self, *args):
            pass

        def reply(self, status, body):
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def who(self):
            secret = self.headers.get("Authorization", "").replace("Bearer ", "", 1).strip()
            return self.headers.get("X-LM-Device", "").strip(), secret, self.client_address[0]

        def do_GET(self):
            if self.path.split("?")[0] != "/v1/hello":
                return self.reply(404, {"ok": False, "code": "not_found", "plain": "No such call."})
            name, secret, ip = self.who()
            try:
                # Saying hello is how a new device asks for approval, so it is answered either way.
                known = host.devices.find(name) if name else None
                vouched = host.vouch(ip) if (known and known["state"] == "expected") else ""
                row = host.devices.meet(name, secret, ip, vouched) if name and len(secret) >= 16 else None
            except NetError as err:
                return self.reply(err.status, {"ok": False, "code": err.code, "plain": err.plain})
            self.reply(200, {"ok": True, "host": host.name, "services": list(SERVICES),
                             "device": {"name": row["name"], "state": row["state"]} if row else None,
                             "busy": host.busy.locked(), "free_gb": round(free_gb(), 1)})

        def do_POST(self):
            path = self.path.split("?")[0]
            name, secret, ip = self.who()
            started = time.time()
            route = host.ROUTES.get(path)
            try:
                if route is None:
                    raise NetError("not_found", "No such call.", 404)
                size = int(self.headers.get("Content-Length") or 0)
                if size > MAX_BODY:
                    raise NetError("too_big", "That picture is too big to send.", 413)
                # Take the whole request before answering: refusing mid-upload reaches the
                # sender as a dropped connection, and they never see why they were refused.
                raw = self.rfile.read(size)
                row = host.admit(name, secret, ip, path)
                body = json.loads(raw or b"{}")
                with tempfile.TemporaryDirectory(prefix="lm-net-") as folder:
                    out = host.run(lambda: getattr(host, route[1])(body, folder))
                secs = round(time.time() - started)
                log_request(row["name"], path, "ok", secs)
                self.reply(200, dict(out, ok=True, seconds=secs))
            except NetError as err:
                if err.code not in ("waiting", "switched_off"):          # those two are logged where they are decided
                    log_request(name or "unknown", path, "failed: " + err.code, round(time.time() - started))
                self.reply(err.status, {"ok": False, "code": err.code, "plain": err.plain})
            except (ValueError, KeyError, TypeError) as err:
                log_request(name or "unknown", path, "failed: bad_request", detail=str(err))
                self.reply(400, {"ok": False, "code": "bad_request", "plain": "The request could not be read."})

    return Handler


def serve(port):
    host = Host()
    try:
        server = ThreadingHTTPServer(("0.0.0.0", port), make_handler(host))
    except OSError:
        raise NetError("port_busy", f"Port {port} is already in use. Pass another: lm net serve --port N")
    print(f"{this_name()} is offering its models to approved devices on port {port}.\n"
          "Leave this window open. Press Ctrl-C to stop. See who is asking: lm net devices", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


# The asking side: this device's identity, and the servers it knows.

def identity():
    """This device's name and its private key, made the first time it is needed."""
    path = Settings.home / "identity.json"
    me = read_json(path, None)
    if not me or not me.get("secret"):
        me = {"name": this_name(), "secret": secrets.token_hex(24)}
        write_json(path, me)
    return me


def servers():
    return read_json(Settings.home / "servers.json", [])


def call(url, path, body=None, timeout=RENDER_TIMEOUT_S + 30):
    """Ask a server to do something as this device. Returns its answer, or raises with its words."""
    me = identity()
    req = urllib.request.Request(url.rstrip("/") + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "Bearer " + me["secret"], "X-LM-Device": me["name"],
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as err:
        got = read_body(err)
        raise NetError(got.get("code", "refused"), got.get("plain", f"The server refused ({err.code})."), err.code)
    except (OSError, ValueError):
        raise NetError("unreachable", f"{url} did not answer. It may be asleep, off, or not serving.", 502)


def read_body(err):
    try:
        return json.loads(err.read())
    except (ValueError, OSError):
        return {}


def add_server(name, url):
    if "://" not in url:
        url = "http://" + url
    if url.count(":") < 2:
        url = f"{url}:{Settings.port}"
    hello = call(url, "/v1/hello", timeout=8)
    rows = [s for s in servers() if s["name"].lower() != name.lower()]
    rows.append({"name": name, "url": url, "host": hello.get("host", ""), "services": hello.get("services", []),
                 "added": now()})
    write_json(Settings.home / "servers.json", rows)
    return hello


# The command line.

HELP = """lm net: let other devices use this machine's models, and use theirs

USAGE
  lm net [command]

EXAMPLES
  lm net                         this device, the servers it knows, the devices that asked
  lm net serve                   offer this machine's models to approved devices
  lm net approve m5air           approve a device once, for everything; works before it first asks
  lm net off m5air               switch a device off; lm net on m5air brings it back
  lm net add studio 100.64.0.7   remember another machine as a server, and ask it for approval
  lm net log                     who used what, most recent last

COMMANDS
  status                 the default: identity, servers and devices
  serve [--port N]       offer this machine (default port 5119)
  devices                devices that asked to use this machine, and your answer for each
  approve NAME           yes for this device, for every service
  off NAME | on NAME     switch an approved device off or back on
  forget NAME            remove a device from the list
  servers                the machines this device can ask
  add NAME ADDRESS       remember a server and say hello to it
  remove NAME            forget a server
  ping [NAME]            ask each server, or one, whether it is up and whether you are approved
  read SERVER IMAGE ["question"]       have a server's vision model read a picture
  diff SERVER IMAGE_A IMAGE_B ["..."]  have a server say what changed between two pictures
  log [N]                the last N requests (default 20)

OPTIONS
  --json                 with status, devices, servers, ping or log: print JSON"""


def print_devices(rows):
    if not rows:
        return print("No device has asked to use this machine yet.")
    for d in rows:
        note = f"  ({d['note']})" if d.get("note") else ""
        print(f"  {d['state']:<9} {d['name']:<20} last seen {d.get('last_seen', 'never')}{note}")
    if any(d["state"] == "pending" for d in rows):
        print("Approve one with: lm net approve NAME")


def cli(argv):
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    cmd, rest = (argv[0], argv[1:]) if argv else ("status", [])
    devices = Devices(Settings.home)
    if cmd in ("-h", "--help", "help"):
        return print(HELP)
    if cmd == "status":
        me, known, asked = identity(), servers(), devices.all()
        if as_json:
            return print(json.dumps({"name": me["name"], "servers": known, "devices": asked}))
        print(f"This device is {me['name']}.")
        print("Servers it can ask:" if known else "It knows no servers yet. Add one: lm net add NAME ADDRESS")
        for s in known:
            print(f"  {s['name']:<20} {s['url']}  offers {', '.join(s.get('services', [])) or 'nothing yet'}")
        print("Devices that asked to use this machine:")
        return print_devices(asked)
    if cmd == "serve":
        port = int(rest[rest.index("--port") + 1]) if "--port" in rest else Settings.port
        return serve(port)
    if cmd == "devices":
        return print(json.dumps(devices.all())) if as_json else print_devices(devices.all())
    if cmd in ("approve", "on", "off"):
        if not rest:
            raise NetError("bad_usage", f"Usage: lm net {cmd} NAME")
        row = devices.decide(rest[0], "off" if cmd == "off" else "approved")
        words = {"approved": "is approved for everything this machine offers",
                 "off": "is switched off; bring it back with: lm net on " + row["name"],
                 "expected": "will be approved the first time it connects over Tailscale"}[row["state"]]
        return print(f"{row['name']} {words}.")
    if cmd == "forget":
        if not rest:
            raise NetError("bad_usage", "Usage: lm net forget NAME")
        devices.forget(rest[0])
        return print(f"{rest[0]} is forgotten.")
    if cmd == "servers":
        known = servers()
        if as_json:
            return print(json.dumps(known))
        if not known:
            return print("No servers yet. Add one: lm net add NAME ADDRESS")
        for s in known:
            print(f"  {s['name']:<20} {s['url']}  offers {', '.join(s.get('services', [])) or 'nothing yet'}")
        return None
    if cmd == "add":
        if len(rest) < 2:
            raise NetError("bad_usage", "Usage: lm net add NAME ADDRESS")
        hello = add_server(rest[0], rest[1])
        state = (hello.get("device") or {}).get("state", "pending")
        print(f"{rest[0]} is remembered ({hello.get('host')}, offers {', '.join(hello.get('services', []))}).")
        if state != "approved":
            print(f"This device is waiting for approval there. Its owner runs: lm net approve {identity()['name']}")
        return None
    if cmd == "remove":
        if not rest:
            raise NetError("bad_usage", "Usage: lm net remove NAME")
        write_json(Settings.home / "servers.json", [s for s in servers() if s["name"].lower() != rest[0].lower()])
        return print(f"{rest[0]} is removed.")
    if cmd == "ping":
        out = []
        for s in servers():
            if rest and s["name"].lower() != rest[0].lower():
                continue
            try:
                hello = call(s["url"], "/v1/hello", timeout=8)
                out.append({"name": s["name"], "up": True, "state": (hello.get("device") or {}).get("state"),
                            "busy": hello.get("busy"), "free_gb": hello.get("free_gb")})
            except NetError as err:
                out.append({"name": s["name"], "up": False, "why": err.plain})
        if as_json:
            return print(json.dumps(out))
        for o in out:
            print(f"  {o['name']:<20} " + (f"up, this device is {o['state']}" + (", busy" if o["busy"] else "")
                                           if o["up"] else "no answer: " + o["why"]))
        return None
    if cmd in ("read", "diff"):
        need = 2 if cmd == "read" else 3
        if len(rest) < need:
            raise NetError("bad_usage", "Usage: lm net read SERVER IMAGE [\"question\"]" if cmd == "read"
                           else "Usage: lm net diff SERVER IMAGE_A IMAGE_B [\"what to look at\"]")
        server = next((s for s in servers() if s["name"].lower() == rest[0].lower()), None)
        if server is None:
            raise NetError("no_such_server", f"There is no server called {rest[0]}. See them with: lm net servers")
        pack = lambda p: base64.b64encode(pathlib.Path(p).expanduser().read_bytes()).decode()
        try:
            if cmd == "read":
                body = {"image": pack(rest[1]), "name": rest[1], "question": " ".join(rest[2:])}
            else:
                body = {"a": pack(rest[1]), "a_name": rest[1], "b": pack(rest[2]), "b_name": rest[2],
                        "focus": " ".join(rest[3:])}
        except OSError as err:
            raise NetError("no_such_file", f"That picture could not be opened: {err.filename}")
        got = call(server["url"], f"/v1/see/{cmd}", body)
        if as_json:
            return print(json.dumps(got))
        answer = got.get("answer")
        return print(answer if isinstance(answer, str) else json.dumps(answer, indent=2))
    if cmd == "log":
        rows = Settings.log.read_text().splitlines() if Settings.log.is_file() else []
        rows = rows[-(int(rest[0]) if rest and rest[0].isdigit() else 20):]
        if as_json:
            return print("[" + ",".join(rows) + "]")
        if not rows:
            return print("No requests yet.")
        for r in map(json.loads, rows):
            print(f"  {r['ts']}  {r['device']:<16} {r['service']:<16} {r['verdict']}" + (f"  {r['secs']} s" if r.get("secs") else ""))
        return None
    raise NetError("bad_usage", f"There is no command called {cmd}. Run: lm net help")


def main():
    try:
        cli(sys.argv[1:])
    except NetError as err:
        print(f"lm net: {err.plain}", file=sys.stderr)
        sys.exit(2 if err.code == "bad_usage" else 1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
