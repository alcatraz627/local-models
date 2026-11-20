#!/usr/bin/env python3
"""Checks that lm net lets in only the devices its owner approved, and logs every request.

It starts a real lm net server on a spare port with a scratch settings folder
and a stand-in for the vision tool, then talks to it as several devices. No
model is loaded and nothing outside the scratch folder is touched.

What it does not cover: a real Tailscale lookup (a stand-in vouches for names),
a real vision read, and two machines on a real network.

Run: python3 probe/fixtures/net-contract.py
"""
import base64
import json
import os
import pathlib
import stat
import sys
import tempfile
import threading
import unittest

TMP = pathlib.Path(tempfile.mkdtemp(prefix="lm-net-test-"))
STAND_IN = TMP / "see"
STAND_IN.write_text('#!/bin/sh\necho \'{"read": "a flat red square"}\'\n')
STAND_IN.chmod(STAND_IN.stat().st_mode | stat.S_IEXEC)
REPO = pathlib.Path(__file__).resolve().parents[2]
os.environ.update(LM_NET_HOME=str(TMP / "host"), LM_NET_LOG=str(TMP / "net.jsonl"), LM_NET_SEE=str(STAND_IN),
                  LM_NET_NAME="testhost", IMAGINE_KIT_FAKE="1", IMAGINE_KIT_FAKE_STEP_S="0",
                  IMAGINE_KIT_FAKE_RAM_GB="64", IMAGINE_KIT_DATA=str(TMP / "kit-data"))
sys.path.insert(0, str(REPO / "lib"))
sys.path.insert(0, str(REPO / "imagine-kit"))
import kit    # noqa: E402
import lmnet  # noqa: E402

PICTURE = base64.b64encode(b"\x89PNG" + b"0" * 200).decode()
VOUCHED = {}                    # address -> the name the stand-in network vouches for


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = lmnet.Host(TMP / "host", vouch=lambda ip: VOUCHED.get(ip, ""))
        cls.server = lmnet.ThreadingHTTPServer(("127.0.0.1", 0), lmnet.make_handler(cls.host))
        cls.url = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def as_device(self, name):
        """Become a device with its own key, as a second machine would be."""
        home = TMP / ("client-" + name)
        lmnet.Settings.home, lmnet.Settings.name = home, name
        self.addCleanup(setattr, lmnet.Settings, "home", TMP / "host")
        self.addCleanup(setattr, lmnet.Settings, "name", "testhost")

    def read(self):
        return lmnet.call(self.url, "/v1/see/read", {"image": PICTURE, "name": "a.png"})

    def refusal(self):
        with self.assertRaises(lmnet.NetError) as err:
            self.read()
        return err.exception

    def log_rows(self):
        return [json.loads(line) for line in (TMP / "net.jsonl").read_text().splitlines()]

    def test_a_new_device_is_refused_and_told_how_it_gets_approved(self):
        self.as_device("stranger")
        err = self.refusal()
        self.assertEqual((err.code, err.status), ("waiting", 403))
        self.assertIn("lm net approve stranger", err.plain)
        self.assertEqual(self.host.devices.find("stranger")["state"], "pending")

    def test_one_approval_covers_every_service_and_can_be_switched_off_and_on(self):
        self.as_device("laptop")
        self.assertEqual(self.refusal().code, "waiting")
        self.host.devices.decide("laptop", "approved")
        self.assertEqual(self.read()["answer"], "a flat red square")
        got = lmnet.call(self.url, "/v1/see/diff", {"a": PICTURE, "a_name": "a.png", "b": PICTURE, "b_name": "b.png"})
        self.assertTrue(got["ok"])
        self.host.devices.decide("laptop", "off")
        self.assertEqual(self.refusal().code, "switched_off")
        self.host.devices.decide("laptop", "approved")
        self.assertTrue(self.read()["ok"])

    def test_a_device_named_ahead_of_time_is_let_in_only_when_the_network_confirms_it(self):
        self.host.devices.decide("m5air", "approved")
        self.assertEqual(self.host.devices.find("m5air")["state"], "expected")
        self.as_device("m5air")
        self.assertEqual(self.refusal().code, "waiting")           # nobody vouches for this address yet
        self.host.devices.forget("m5air")
        self.host.devices.decide("m5air", "approved")
        VOUCHED["127.0.0.1"] = "m5air"
        self.addCleanup(VOUCHED.clear)
        self.assertTrue(self.read()["ok"])
        self.assertEqual(self.host.devices.find("m5air")["state"], "approved")

    def test_a_refusal_reaches_a_device_that_was_sending_a_large_picture(self):
        self.as_device("uploader")
        big = base64.b64encode(b"\x89PNG" + os.urandom(3 * 1024 * 1024)).decode()
        with self.assertRaises(lmnet.NetError) as err:
            lmnet.call(self.url, "/v1/see/read", {"image": big, "name": "big.png"})
        self.assertEqual(err.exception.code, "waiting")

    def test_a_second_device_cannot_borrow_an_approved_name(self):
        self.as_device("tablet")
        self.refusal()
        self.host.devices.decide("tablet", "approved")
        self.assertTrue(self.read()["ok"])
        lmnet.Settings.home = TMP / "client-impostor"                 # same name, a different key
        self.assertEqual(self.refusal().code, "waiting")
        self.assertEqual(self.host.devices.find("tablet-2")["state"], "pending")

    def test_a_request_with_no_identity_is_refused(self):
        with self.assertRaises(lmnet.NetError) as err:
            self.host.admit("", "", "127.0.0.1", "see")
        self.assertEqual(err.exception.status, 401)

    def test_every_request_is_logged_allowed_or_refused(self):
        self.as_device("logged")
        self.refusal()
        self.host.devices.decide("logged", "approved")
        self.read()
        mine = [r for r in self.log_rows() if r["device"] == "logged"]
        self.assertEqual([r["verdict"] for r in mine], ["refused: waiting for approval", "ok"])
        self.assertTrue(all(r["ts"] and r["service"] for r in mine))

    def test_hello_tells_a_device_where_it_stands_without_doing_any_work(self):
        self.as_device("greeter")
        hello = lmnet.call(self.url, "/v1/hello")
        self.assertEqual((hello["host"], hello["device"]["state"], hello["services"]), ("testhost", "pending", ["see", "imagine"]))

    def test_a_file_that_is_not_a_picture_is_refused(self):
        self.as_device("sender")
        self.refusal()
        self.host.devices.decide("sender", "approved")
        with self.assertRaises(lmnet.NetError) as err:
            lmnet.call(self.url, "/v1/see/read", {"image": PICTURE, "name": "notes.txt"})
        self.assertEqual(err.exception.code, "not_a_picture")

    def test_the_image_kit_draws_on_this_server_and_gets_the_picture_back(self):
        """The kit, as another device, sends a rework with a source image and saves what comes back."""
        self.as_device("studio-user")
        kit.Settings.net = TMP / "client-studio-user"
        self.assertEqual(kit.add_server("big", self.url)["device"]["state"], "pending")
        source = TMP / "src.png"
        kit.fake_png(source, 3, 320, 200)
        request = {"prompt": "make it blue", "sources": [str(source)], "server": "big", "seed": 12}
        with self.assertRaises(kit.KitError) as err:
            kit.render(kit.plan(request))
        self.assertEqual(err.exception.code, "waiting")
        me = kit.net_identity()["name"]                 # the kit names itself after the computer it is on
        self.host.devices.decide(me, "approved")
        entry = kit.render(kit.plan(request))
        self.assertEqual((entry["server"], entry["mode"], entry["seed"]), ("big", "edit", 12))
        self.assertTrue(pathlib.Path(entry["output"]).read_bytes().startswith(b"\x89PNG"))
        served = [r for r in self.log_rows() if r["device"] == me]
        self.assertEqual(served[-1]["service"], "/v1/imagine/render")
        self.assertEqual(served[-1]["verdict"], "ok")

    def test_the_kit_and_lm_net_read_the_same_identity_file(self):
        self.as_device("shared")
        kit.Settings.net = TMP / "client-shared"
        self.assertEqual(kit.net_identity(), lmnet.identity())

    def test_too_many_waiting_jobs_are_turned_away(self):
        self.host.waiting = lmnet.MAX_WAITING
        self.addCleanup(setattr, self.host, "waiting", 0)
        with self.assertRaises(lmnet.NetError) as err:
            self.host.run(lambda: 1)
        self.assertEqual(err.exception.code, "busy")

    def test_the_key_file_is_private_to_its_owner(self):
        self.as_device("keyed")
        lmnet.identity()
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE((TMP / "client-keyed" / "identity.json").stat().st_mode), 0o600)


if __name__ == "__main__":
    unittest.main(verbosity=1)
