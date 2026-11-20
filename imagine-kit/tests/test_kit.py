#!/usr/bin/env python3
"""Checks for Imagine Kit that need no model and no network.

They run the real program with its stand-in engine, which draws a flat PNG in
place of a render, so every path around the model is exercised: planning a
request, the exact engine command, history, follow-ups, the web calls and the
command line. Run: python3 tests/test_kit.py
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

KIT = pathlib.Path(__file__).resolve().parents[1]
TMP = tempfile.mkdtemp(prefix="imagine-kit-test-")
os.environ.update(IMAGINE_KIT_FAKE="1", IMAGINE_KIT_DATA=TMP, IMAGINE_KIT_FAKE_STEP_S="0.01",
                  IMAGINE_KIT_FAKE_RAM_GB="64")
sys.path.insert(0, str(KIT))
import kit  # noqa: E402


def a_png(name="src.png", seed=7):
    path = pathlib.Path(TMP) / name
    kit.fake_png(path, seed, 320, 200)
    return path


class Planning(unittest.TestCase):
    def test_a_prompt_alone_is_a_new_image(self):
        p = kit.plan({"prompt": "a red bicycle"})
        self.assertEqual((p["mode"], p["sources"], p["width"], p["height"]), ("new", [], 1024, 1024))
        self.assertEqual(p["steps"], kit.MODELS["klein"]["steps"])

    def test_sources_make_it_an_edit_and_size_follows_the_source(self):
        p = kit.plan({"prompt": "make it blue", "sources": [str(a_png())]})
        self.assertEqual(p["mode"], "edit")
        self.assertEqual((p["width"], p["height"]), (1024, 640))

    def test_a_model_that_cannot_edit_starts_from_one_source(self):
        p = kit.plan({"prompt": "x", "model": "qwen", "sources": [str(a_png("a.png", 1)), str(a_png("b.png", 2))]})
        self.assertEqual((p["mode"], len(p["sources"])), ("start", 1))

    def test_an_empty_prompt_is_refused(self):
        with self.assertRaises(kit.KitError) as err:
            kit.plan({"prompt": "   "})
        self.assertEqual(err.exception.code, "empty_prompt")

    def test_a_style_is_added_to_the_prompt_the_model_sees(self):
        p = kit.plan({"prompt": "a cat", "style": "watercolor"})
        self.assertIn("watercolour", p["full_prompt"])
        self.assertEqual(p["prompt"], "a cat")

    def test_a_rework_instruction_gets_no_style_sentence(self):
        p = kit.plan({"prompt": "make the jacket red", "style": "photo", "sources": [str(a_png())]})
        self.assertEqual((p["mode"], p["full_prompt"], p["style"]), ("edit", "make the jacket red", ""))

    def test_a_loose_start_still_takes_a_style(self):
        p = kit.plan({"prompt": "a cat", "style": "photo", "sources": [str(a_png())], "use": "start"})
        self.assertIn("photorealistic", p["full_prompt"])


class EngineCommand(unittest.TestCase):
    def test_an_edit_uses_the_edit_program_and_passes_every_source(self):
        a, b = str(a_png("a.png", 1)), str(a_png("b.png", 2))
        p = kit.plan({"prompt": "combine", "sources": [a, b], "seed": 5})
        cmd = kit.command(p, "/tmp/out.png")
        self.assertTrue(cmd[0].endswith("mflux-generate-flux2-edit"))
        at = cmd.index("--image-paths")
        self.assertEqual(len(cmd[at + 1:at + 3]), 2)
        self.assertIn("--mlx-cache-limit-gb", cmd)

    def test_a_loose_start_uses_strength_not_the_edit_program(self):
        p = kit.plan({"prompt": "x", "sources": [str(a_png())], "use": "start", "strength": 0.3})
        cmd = kit.command(p, "/tmp/out.png")
        self.assertTrue(cmd[0].endswith("mflux-generate-flux2"))
        self.assertEqual(cmd[cmd.index("--image-strength") + 1], "0.3")

    def test_guidance_is_sent_only_to_a_model_that_takes_it(self):
        self.assertNotIn("--guidance", kit.command(kit.plan({"prompt": "x"}), "/tmp/o.png"))
        self.assertIn("--guidance", kit.command(kit.plan({"prompt": "x", "model": "qwen"}), "/tmp/o.png"))


class RenderAndFollowUps(unittest.TestCase):
    def test_a_render_writes_a_file_and_a_full_record(self):
        e = kit.render(kit.plan({"prompt": "first", "seed": 11}))
        self.assertTrue(pathlib.Path(e["output"]).is_file())
        self.assertEqual(kit.get_entry(e["id"])["seed"], 11)

    def test_again_keeps_the_request_and_changes_the_seed(self):
        e = kit.render(kit.plan({"prompt": "again me", "seed": 21}))
        p = kit.plan(kit.follow_up("again", e["id"]))
        self.assertEqual(p["prompt"], "again me")
        self.assertNotEqual(p["seed"], 21)
        self.assertEqual((p["parent"], p["kind"]), (e["id"], "again"))

    def test_refine_keeps_the_seed_and_adds_to_the_prompt(self):
        e = kit.render(kit.plan({"prompt": "a house", "seed": 31}))
        p = kit.plan(kit.follow_up("refine", e["id"], "at night"))
        self.assertEqual((p["seed"], p["prompt"]), (31, "a house. at night"))

    def test_rework_uses_the_past_image_as_the_source(self):
        e = kit.render(kit.plan({"prompt": "a chair", "seed": 41}))
        p = kit.plan(kit.follow_up("rework", e["id"], "paint it green"))
        self.assertEqual((p["mode"], p["sources"], p["prompt"]), ("edit", [e["output"]], "paint it green"))

    def test_a_missing_model_is_refused_before_anything_runs(self):
        p = kit.plan({"prompt": "x"})
        old = kit.Settings.fake_missing
        kit.Settings.fake_missing = ["klein"]
        try:
            with self.assertRaises(kit.KitError) as err:
                kit.render(p)
            self.assertEqual(err.exception.code, "model_missing")
        finally:
            kit.Settings.fake_missing = old

    def test_delete_hides_the_image_and_keeps_the_file_in_trash(self):
        e = kit.render(kit.plan({"prompt": "delete me", "seed": 51}))
        kit.remove_entry(e["id"])
        self.assertNotIn(e["id"], [r["id"] for r in kit.read_history()])
        self.assertTrue((kit.TRASH / pathlib.Path(e["output"]).name).is_file())

    def test_a_render_keeps_its_details_in_a_file_beside_the_image(self):
        e = kit.render(kit.plan({"prompt": "with details", "seed": 61}))
        details = json.loads(kit.details_path(e["output"]).read_text())
        self.assertEqual((details["prompt"], details["seed"], details["id"]), ("with details", 61, e["id"]))
        self.assertNotIn("--metadata", kit.command(kit.plan({"prompt": "x"}), "/tmp/o.png"))

    def test_delete_takes_the_details_file_to_trash_with_the_image(self):
        e = kit.render(kit.plan({"prompt": "delete us both", "seed": 71}))
        details = kit.details_path(e["output"])
        kit.remove_entry(e["id"])
        self.assertFalse(details.exists())
        self.assertTrue((kit.TRASH / details.name).is_file())


class MachineAndEngines(unittest.TestCase):
    """The kit asks the machine what it can run, and hands each render to the model's engine."""

    def with_ram(self, gb):
        old = kit.Settings.fake_ram_gb
        kit.Settings.fake_ram_gb = gb
        self.addCleanup(setattr, kit.Settings, "fake_ram_gb", old)

    def test_a_large_machine_gets_the_full_tier(self):
        self.with_ram(64)
        m = kit.machine()
        self.assertEqual((m["tier"], m["ram_gb"]), ("full", 64))
        p = kit.plan({"prompt": "x"})
        self.assertEqual((p["quant"], p["low_ram"]), (8, False))

    def test_a_16_gb_machine_gets_the_tight_tier_and_a_lighter_load(self):
        self.with_ram(16)
        self.assertEqual(kit.machine()["tier"], "tight")
        p = kit.plan({"prompt": "x"})
        self.assertEqual((p["quant"], p["low_ram"]), (4, True))

    def test_a_machine_too_small_for_any_local_model_is_told_so(self):
        self.with_ram(8)
        m = kit.machine()
        self.assertEqual(m["tier"], "none")
        self.assertIn("8 GB", m["why"])

    def test_the_machine_report_names_its_system_and_memory_without_a_mac_only_tool(self):
        self.with_ram(0)                       # ask the real machine
        m = kit.machine()
        self.assertGreater(m["ram_gb"], 0)
        self.assertIn(m["os"], ("mac", "linux", "windows"))

    def test_a_render_is_handed_to_the_engine_its_model_names(self):
        calls = []

        class Stub:
            name = "a stand-in engine"

            def ready(self):
                return True, ""

            def run(self, p, out, on_step, should_stop):
                calls.append(p["prompt"])
                kit.fake_png(out, 1)

        kit.ENGINES["stub"] = Stub()
        kit.MODELS["stubby"] = dict(kit.MODELS["klein"], name="Stubby", engine="stub")
        self.addCleanup(kit.ENGINES.pop, "stub")
        self.addCleanup(kit.MODELS.pop, "stubby")
        e = kit.render(kit.plan({"prompt": "through the seam", "model": "stubby"}))
        self.assertEqual(calls, ["through the seam"])
        self.assertTrue(pathlib.Path(e["output"]).is_file())

    def test_an_engine_that_is_not_installed_refuses_with_its_own_fix(self):
        class Missing:
            name = "an absent engine"

            def ready(self):
                return False, "Install the absent engine."

            def run(self, *a):
                raise AssertionError("must not run")

        kit.ENGINES["missing"] = Missing()
        kit.MODELS["ghost"] = dict(kit.MODELS["klein"], name="Ghost", engine="missing")
        self.addCleanup(kit.ENGINES.pop, "missing")
        self.addCleanup(kit.MODELS.pop, "ghost")
        with self.assertRaises(kit.KitError) as err:
            kit.render(kit.plan({"prompt": "x", "model": "ghost"}))
        self.assertEqual((err.exception.code, err.exception.fix), ("not_installed", "Install the absent engine."))

    def test_a_small_graphics_card_gets_a_lighter_model_and_smaller_sources(self):
        self.assertEqual(kit.card_plan(24, 2), (16, 1024))
        self.assertEqual(kit.card_plan(16, 1), (4, 768))
        self.assertEqual(kit.card_plan(16, 2), (4, 512))
        self.assertIsNone(kit.card_plan(8, 0))

    def test_the_second_engine_says_what_card_it_needs_when_there_is_none(self):
        old = kit.machine
        kit.machine = lambda: {"os": "linux", "chip": "x86_64", "ram_gb": 32, "gpu_gb": 0, "tier": "full", "why": ""}
        self.addCleanup(setattr, kit, "machine", old)
        ok, fix = kit.ENGINES["diffusers"].ready()
        self.assertFalse(ok)
        self.assertIn("12 GB", fix)
        self.assertIn("./imagine servers", fix)

    def test_the_second_engine_hands_its_program_the_whole_job(self):
        seen = {}
        old_run, old_machine = kit.run_engine_process, kit.machine
        kit.run_engine_process = lambda cmd, p, out, on_step, should_stop: seen.update(cmd=cmd)
        kit.machine = lambda: {"os": "linux", "chip": "x86_64", "ram_gb": 32, "gpu_gb": 16, "tier": "full", "why": ""}
        self.addCleanup(setattr, kit, "run_engine_process", old_run)
        self.addCleanup(setattr, kit, "machine", old_machine)
        p = kit.plan({"prompt": "make it blue", "sources": [str(a_png())], "seed": 3})
        kit.ENGINES["diffusers"].run(p, "/tmp/o.png", None, None)
        job = json.loads(seen["cmd"][2])
        self.assertTrue(seen["cmd"][1].endswith("engine_diffusers.py"))
        self.assertEqual((job["bits"], job["ref_side"], job["seed"], len(job["sources"])), (4, 768, 3, 1))
        self.assertEqual(p["quant"], 4)

    def test_an_image_size_is_read_without_a_mac_only_tool(self):
        self.assertEqual(kit.image_size(a_png("sized.png", 9)), (320, 200))


try:
    from PIL import Image
except ImportError:
    Image = None


class CloudModels(unittest.TestCase):
    """Two models run at a company. They need its key, and the kit says plainly where a request goes."""

    def test_a_cloud_model_says_where_it_runs_and_where_to_get_a_key(self):
        s = kit.model_status("gemini")
        self.assertEqual((s["cloud"], s["who"]), ("gemini", "Google"))
        self.assertIn("sent there", s["blurb"])
        self.assertTrue(s["key_page"].startswith("https://"))

    def test_a_cloud_model_without_a_key_is_refused_with_the_way_to_get_one(self):
        old = kit.Settings.fake_missing
        kit.Settings.fake_missing = ["gpt"]
        self.addCleanup(setattr, kit.Settings, "fake_missing", old)
        with self.assertRaises(kit.KitError) as err:
            kit.render(kit.plan({"prompt": "x", "model": "gpt"}))
        self.assertEqual(err.exception.code, "needs_key")
        self.assertIn("platform.openai.com", err.exception.fix)

    def test_a_computer_that_cannot_run_a_model_is_not_offered_its_download(self):
        """A small graphics card: the local model is marked as unable to run, and a cloud model becomes the default."""
        old = kit.Settings.fake_no_engine
        kit.Settings.fake_no_engine = True
        self.addCleanup(setattr, kit.Settings, "fake_no_engine", old)
        s = kit.model_status("klein")
        self.assertFalse(s["engine_ok"])
        self.assertIn("12 GB", s["engine_fix"])
        self.assertEqual(kit.default_model(), "gemini")
        self.assertFalse(kit.app_state()["installed"])

    def test_a_saved_key_is_private_and_can_be_forgotten(self):
        kit.save_key("gemini", "  k" + "x" * 30 + " \n")
        self.addCleanup(kit.save_key, "gemini", "")
        if not os.environ.get("GEMINI_API_KEY"):
            self.assertEqual(kit.api_key("gemini"), "k" + "x" * 30)
        if os.name == "posix":
            self.assertEqual((kit.DATA / "keys.json").stat().st_mode & 0o777, 0o600)
        kit.save_key("gemini", "")
        self.assertNotIn("gemini", kit._saved_keys())

    def test_a_scrap_of_a_key_is_refused(self):
        with self.assertRaises(kit.KitError) as err:
            kit.save_key("openai", "sk-short")
        self.assertEqual(err.exception.code, "bad_key")

    def test_a_request_to_google_carries_the_prompt_and_every_source(self):
        p = kit.plan({"prompt": "combine these", "model": "gemini",
                      "sources": [str(a_png("g1.png", 1)), str(a_png("g2.png", 2))]})
        parts = kit.GeminiEngine().request(p)["contents"][0]["parts"]
        self.assertEqual(parts[0]["text"], "combine these")
        self.assertEqual([part["inline_data"]["mime_type"] for part in parts[1:]], ["image/png", "image/png"])

    def test_a_request_to_openai_sends_each_source_as_a_file(self):
        body, kind = kit.OpenAIEngine().form({"model": "m", "prompt": "make it blue"}, [str(a_png("o1.png", 3))])
        self.assertIn("multipart/form-data; boundary=", kind)
        self.assertIn(b'name="image[]"; filename="o1.png"', body)
        self.assertIn(b"make it blue", body)
        self.assertTrue(body.rstrip().endswith(b"--"))

    def test_the_newest_settled_image_model_is_picked_from_what_the_service_lists(self):
        kit._picked.clear()
        self.addCleanup(kit._picked.clear)
        got = kit.cloud_model("openai", lambda: ["gpt-image-1", "gpt-image-2", "gpt-image-3-preview"])
        self.assertEqual(got, "gpt-image-2")


class ThreadsQueueAndAreas(unittest.TestCase):
    """Images belong to threads, requests wait in a queue, and a change can be kept to a marked area."""

    def test_a_follow_up_stays_in_its_images_thread_and_a_new_request_starts_one(self):
        first = kit.render(kit.plan({"prompt": "thread root", "seed": 1}))
        again = kit.render(kit.plan(kit.follow_up("again", first["id"])))
        rework = kit.render(kit.plan(kit.follow_up("rework", again["id"], "greener")))
        other = kit.render(kit.plan({"prompt": "another idea", "seed": 2}))
        self.assertEqual({first["thread"], again["thread"], rework["thread"]}, {first["thread"]})
        self.assertNotEqual(other["thread"], first["thread"])

    def test_using_a_past_image_as_a_source_joins_its_thread(self):
        first = kit.render(kit.plan({"prompt": "a base", "seed": 3}))
        built = kit.render(kit.plan({"prompt": "add a hat", "sources": [f"#{first['id']}"]}))
        self.assertEqual((built["thread"], built["parent"]), (first["thread"], first["id"]))

    def test_an_image_made_before_threads_existed_is_grouped_with_its_parent(self):
        kit.render(kit.plan({"prompt": "so the history file exists", "seed": 9}))
        with open(kit.HISTORY, "a") as f:       # two rows as the first version of the kit wrote them: no thread
            f.write(json.dumps({"id": 9001, "prompt": "old root", "output": "/nowhere/a.png", "sources": [],
                                "parent": None}) + "\n")
            f.write(json.dumps({"id": 9002, "prompt": "old child", "output": "/nowhere/b.png", "sources": [],
                                "parent": 9001}) + "\n")
        rows = {r["id"]: r for r in kit.read_history()}
        self.assertEqual(rows[9002]["thread"], rows[9001]["thread"])
        self.assertTrue(rows[9001]["thread"])
        kit.remove_entry(9001)
        kit.remove_entry(9002)

    def test_requests_wait_in_line_and_each_finishes(self):
        queue = kit.Queue()
        jobs = [queue.add("render", f"job {n}", lambda step, stop, n=n: kit.render(kit.plan({"prompt": f"queued {n}"})))
                for n in range(3)]
        self.assertEqual(len({j["id"] for j in jobs}), 3)
        for _ in range(400):
            if all(j["state"] == "done" for j in jobs):
                break
            time.sleep(0.01)
        self.assertEqual([j["state"] for j in jobs], ["done"] * 3)
        self.assertEqual(len({j["entry"] for j in jobs}), 3)

    def test_a_waiting_request_can_be_taken_out_of_the_line(self):
        queue = kit.Queue()
        gate = threading.Event()
        first = queue.add("render", "slow", lambda step, stop: gate.wait(5) and {})
        second = queue.add("render", "never runs", lambda step, stop: self.fail("a removed job ran"))
        queue.stop(second["id"])
        gate.set()
        for _ in range(300):
            if first["state"] != "running" and first["state"] != "queued":
                break
            time.sleep(0.01)
        self.assertEqual(second["state"], "stopped")

    def test_the_line_has_a_limit(self):
        queue = kit.Queue()
        gate = threading.Event()
        self.addCleanup(gate.set)
        for n in range(kit.Queue.LIMIT):
            queue.add("render", str(n), lambda step, stop: gate.wait(5) and {})
        with self.assertRaises(kit.KitError) as err:
            queue.add("render", "one too many", lambda step, stop: {})
        self.assertEqual(err.exception.code, "queue_full")

    def test_a_marked_area_must_be_a_sensible_box_on_one_source(self):
        with self.assertRaises(kit.KitError) as err:
            kit.plan({"prompt": "x", "region": [0.1, 0.1, 0.5, 0.5]})
        self.assertEqual(err.exception.code, "region_needs_source")
        with self.assertRaises(kit.KitError) as err:
            kit.plan({"prompt": "x", "sources": [str(a_png())], "region": [0.9, 0.9, 0.5, 0.5]})
        self.assertEqual(err.exception.code, "bad_region")

    @unittest.skipIf(Image is None, "needs Pillow, which the kit's own environment has")
    def test_a_change_to_a_marked_area_leaves_every_other_pixel_alone(self):
        base = pathlib.Path(TMP) / "striped.png"
        im = Image.new("RGB", (640, 480))
        for x in range(640):
            for y in range(0, 480, 8):
                im.paste((x % 256, y % 256, 90), (x, y, x + 1, y + 8))
        im.save(base)
        e = kit.render(kit.plan({"prompt": "change this bit", "sources": [str(base)], "region": [0.25, 0.25, 0.25, 0.25],
                                 "seed": 8}))
        out, before = Image.open(e["output"]).convert("RGB"), Image.open(base).convert("RGB")
        self.assertEqual(out.size, before.size)
        self.assertEqual(e["region"], [0.25, 0.25, 0.25, 0.25])
        for point in ((5, 5), (630, 470), (40, 400), (600, 30)):            # well outside the box and its margin
            self.assertEqual(out.getpixel(point), before.getpixel(point), point)
        self.assertNotEqual(out.getpixel((240, 180)), before.getpixel((240, 180)))      # the middle of the box
        report = kit.check_change(e["id"])
        self.assertEqual(report["outside_changed_pct"], 0)
        self.assertGreater(report["inside_changed_pct"], 50)

    def test_a_thread_can_be_named(self):
        first = kit.render(kit.plan({"prompt": "name me", "seed": 4}))
        kit.name_thread(first["thread"], "Bicycle poster")
        self.assertEqual(kit.thread_names()[first["thread"]], "Bicycle poster")


class Prompts(unittest.TestCase):
    def test_the_template_keeps_the_idea_and_says_who_wrote_it(self):
        got = kit.improve_prompt("a fox")
        self.assertTrue(got["prompt"].startswith("a fox"))
        self.assertIn("template", got["by"])

    def test_an_edit_instruction_says_what_to_keep(self):
        self.assertIn("Keep everything else", kit.improve_prompt("make the hat red", editing=True)["prompt"])


class WebCalls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = kit.ThreadingHTTPServer(("127.0.0.1", 0), kit.Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def call(self, path, body=None, raw=None, headers=None):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        req = urllib.request.Request(self.base + path, data=data, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read()) if "json" in r.headers.get("Content-Type", "") else r.read()
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read())

    def wait_done(self):
        for _ in range(300):
            job = self.call("/api/state")[1]["job"]
            if job and job["state"] != "running":
                return job
            time.sleep(0.02)
        self.fail("the job never finished")

    def test_the_page_is_served(self):
        status, body = self.call("/")
        self.assertEqual(status, 200)
        self.assertIn(b"Imagine Kit", body)

    def test_upload_then_generate_then_the_image_is_in_history(self):
        status, up = self.call("/api/upload", raw=a_png("up.png", 3).read_bytes(), headers={"X-Filename": "up.png"})
        self.assertEqual(status, 200)
        status, got = self.call("/api/generate", {"prompt": "from the web", "sources": [up["source"]]})
        self.assertEqual((status, got["plan"]["mode"]), (200, "edit"))
        job = self.wait_done()
        self.assertEqual(job["state"], "done")
        newest = self.call("/api/state")[1]["history"][0]
        self.assertEqual((newest["id"], newest["prompt"]), (job["entry"], "from the web"))
        self.assertEqual(self.call(newest["url"])[0], 200)
        self.assertEqual(self.call(newest["source_urls"][0])[0], 200)

    def test_a_file_that_is_not_an_image_is_refused(self):
        status, got = self.call("/api/upload", raw=b"hello", headers={"X-Filename": "notes.txt"})
        self.assertEqual((status, got["code"]), (400, "not_an_image"))

    def test_a_request_cannot_read_outside_the_image_folder(self):
        self.assertEqual(self.call("/img/..%2f..%2fkit.py")[0], 404)

    def test_a_request_from_another_host_name_is_refused(self):
        status, got = self.call("/api/generate", {"prompt": "x"}, headers={"Host": "evil.example"})
        self.assertEqual((status, got["code"]), (403, "forbidden"))

    def test_star_flips_and_delete_removes(self):
        self.call("/api/generate", {"prompt": "star me"})
        entry = self.wait_done()["entry"]
        self.assertTrue(self.call("/api/star", {"id": entry})[1]["star"])
        self.assertFalse(self.call("/api/star", {"id": entry})[1]["star"])
        self.call("/api/delete", {"id": entry})
        self.assertNotIn(entry, [r["id"] for r in self.call("/api/state")[1]["history"]])


class Install(unittest.TestCase):
    def test_the_installer_and_the_pin_list_name_the_same_engine_version(self):
        installer = (KIT / "install.sh").read_text()
        pins = (KIT / "constraints.txt").read_text()
        version = installer.split('MFLUX_VERSION="')[1].split('"')[0]
        self.assertIn(f"mflux=={version}\n", pins)
        self.assertIn("--constraint", installer)

    def test_the_pin_list_holds_the_package_that_once_broke_a_fresh_install(self):
        self.assertRegex((KIT / "constraints.txt").read_text(), r"(?m)^pillow==12\.")


class CommandLine(unittest.TestCase):
    def run_kit(self, *args):
        return subprocess.run([str(KIT / "imagine"), *args], capture_output=True, text=True, env=os.environ)

    def test_help_three_ways_is_the_same_and_starts_with_the_name(self):
        outs = [self.run_kit(flag).stdout for flag in ("-h", "--help", "help")]
        self.assertEqual(len(set(outs)), 1)
        self.assertTrue(outs[0].startswith("imagine: "))
        self.assertLessEqual(len(outs[0].splitlines()), 40)

    def test_gen_prints_the_file_and_json_gives_the_record(self):
        r = self.run_kit("gen", "a cli image", "--seed", "77", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["seed"], 77)

    def test_a_refusal_is_json_with_a_stable_code_when_json_was_asked_for(self):
        r = self.run_kit("gen", "x", "--from", "/no/such/file.png", "--json")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(json.loads(r.stdout)["code"], "source_missing")

    def test_doctor_as_json_says_what_this_computer_can_use(self):
        got = json.loads(self.run_kit("doctor", "--json").stdout)
        self.assertTrue(got["can_draw"])
        self.assertIn(got["default_model"], [m["id"] for m in got["models"]])
        self.assertIn("tier", got["machine"])

    def test_an_area_on_the_command_line_must_be_four_numbers(self):
        r = self.run_kit("rework", "1", "greener", "--area", "0.2,0.2")
        self.assertEqual(r.returncode, 2)
        self.assertIn("left,top,width,height", r.stderr)

    def test_a_follow_up_can_name_the_machine_that_draws_it(self):
        self.run_kit("gen", "a base for a follow-up", "--seed", "5")
        newest = kit.read_history()[-1]["id"]
        r = self.run_kit("again", str(newest), "--on", "nowhere", "--json")
        self.assertEqual(json.loads(r.stdout)["code"], "no_such_server")

    def test_an_unknown_command_exits_2(self):
        self.assertEqual(self.run_kit("frobnicate").returncode, 2)

    def test_a_bad_size_exits_2_and_says_the_shape(self):
        r = self.run_kit("gen", "x", "--size", "big")
        self.assertEqual(r.returncode, 2)
        self.assertIn("WIDTHxHEIGHT", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
