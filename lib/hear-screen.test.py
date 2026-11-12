#!/usr/bin/python3
"""What the lm hear screens promise: rows that fit, a pane that opens the same way for every row,
keys that are all bound, questions that do nothing when nobody answers, and a tool that works as installed.

Every test runs against a temporary history and a temporary session folder.
Run: /usr/bin/python3 hear-screen.test.py
"""
import json
import os
import re
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL, HELPER = HERE / "hear-screen", HERE / "hear-screen-helper.py"
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def bare(text):
    return ANSI.sub("", text)


class Screens(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.log, self.live = root / "history.jsonl", root / "live"
        self.live.mkdir()
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rows = []
        for i, (verb, secs, segs, extra) in enumerate([
                ("call", 2465.0, [{"start": 0, "end": 4, "text": "Okay, let's start.", "speaker": "0"},
                                  {"start": 5, "end": 9, "text": "Both reports are about the same thing.", "speaker": "1"}],
                 {"digest": "## Decisions\n- Ship it next Wednesday [00:05]", "notes": ["11 labels came down to 5"]}),
                ("live", 6.5, [{"start": 0, "end": 6, "text": "Note to self, the border needs twelve motifs."}], {}),
                ("intent", 3.7, [], {"intent": {"kind": "app_action", "target": "slack", "text": "mute general"}})]):
            folder = root / f"run{i}"
            folder.mkdir()
            text = " ".join(s["text"] for s in segs) or "Open Slack and mute general."
            (folder / "result.json").write_text(json.dumps({"ok": True, "segments": segs, "text": text, **extra}))
            (folder / "transcript.md").write_text(text + "\n")
            rows.append({"ts": "2026-11-11T10:00:00Z" if i == 0 else now, "verb": verb, "seconds": secs, "ok": True,
                         "artifact": str(folder), "snippet": text[:80], "file": None})
        rows.append({"ts": now, "verb": "words", "ok": False, "error": "no_speech", "artifact": None})
        self.log.write_text("".join(json.dumps(r) + "\n" for r in rows))
        self.env = dict(os.environ, HEAR_SCREEN_LOG=str(self.log))

    def tearDown(self):
        self.tmp.cleanup()

    def helper(self, *args, **kwargs):
        return subprocess.run(["/usr/bin/python3", str(HELPER)] + list(args), capture_output=True, text=True, timeout=60, env=self.env, **kwargs)

    def run_keys(self):
        return [r.split("\t")[0] for r in self.helper("browse-rows").stdout.splitlines() if not r.startswith("day:")]

    def say(self, lines, **state):
        (self.live / "lines.jsonl").write_text("".join(json.dumps(ln) + "\n" for ln in lines))
        (self.live / "state.json").write_text(json.dumps({"status": "listening", "t": 75.0, "paused": False, "follow": True, "interim": "", **state}))

    # ── past runs ──

    def test_runs_are_listed_newest_first_under_their_day(self):
        rows = self.helper("browse-rows").stdout.splitlines()
        self.assertEqual(rows[0].split("\t")[0], "day:today")
        self.assertEqual(self.run_keys(), ["3", "2", "1"])
        self.assertTrue(any(r.startswith("day:") and "nov" in bare(r).lower() for r in rows[1:]), rows)

    def test_a_failed_run_is_not_offered(self):
        self.assertNotIn("4", self.run_keys())

    def test_every_row_header_and_legend_fits_the_list_column(self):
        lines = (self.helper("browse-rows").stdout.splitlines() + self.helper("browse-header").stdout.splitlines()
                 + self.helper("browse-keys").stdout.splitlines())
        self.assertLessEqual(max(len(bare(line.split("\t")[-1])) for line in lines), 56)

    def test_the_pane_opens_with_the_same_three_lines_for_every_run(self):
        for key in self.run_keys():
            top = bare(self.helper("browse-detail", key).stdout).splitlines()[:5]
            self.assertRegex(top[1], r"^─{50,}$", key)
            self.assertEqual([line.split()[0] for line in top[2:]], ["when", "length", "voices"], key)

    def test_the_pane_shows_what_the_run_holds(self):
        call = bare(self.helper("browse-detail", "1").stdout)
        self.assertIn("voices    2", call)
        self.assertIn("Ship it next Wednesday", call)
        self.assertIn("Both reports are about the same thing.", call)
        self.assertIn("11 labels came down to 5", call)
        self.assertIn("voices    not labelled", bare(self.helper("browse-detail", "2").stdout))
        self.assertIn("app_action slack", bare(self.helper("browse-detail", "3").stdout))

    def test_no_pane_line_is_wider_than_the_pane(self):
        for key in self.run_keys():
            widest = max(len(line) for line in bare(self.helper("browse-detail", key).stdout).splitlines())
            self.assertLessEqual(widest, 58, key)

    def test_enter_opens_the_digest_when_there_is_one_and_the_transcript_otherwise(self):
        (Path(json.loads(self.log.read_text().splitlines()[0])["artifact"]) / "digest.md").write_text("d\n")
        self.assertTrue(self.helper("browse-flow", "enter", "1").stdout.strip().endswith("digest.md"))
        self.assertTrue(self.helper("browse-flow", "enter", "2").stdout.strip().endswith("transcript.md"))

    def test_a_redo_with_nobody_to_answer_does_nothing(self):
        for step in ("speakers", "call", "voices"):
            asked = self.helper("browse-flow", step, "1", stdin=subprocess.DEVNULL, start_new_session=True)
            self.assertEqual(asked.stdout.strip(), "redraw", step)

    def test_an_empty_history_says_so_instead_of_opening_empty(self):
        self.log.write_text("")
        self.assertIn("No runs yet", self.helper("browse-rows").stdout)

    # ── a live session ──

    def test_live_rows_show_time_voice_and_words_and_a_mark(self):
        self.say([{"start": 21.0, "end": 23.0, "text": "Can we stream it instead?", "speaker": "0"},
                  {"mark": True, "start": 24.0},
                  {"start": 25.0, "end": 26.0, "text": "Yes."}], interim="I think streaming the rows")
        rows = [bare(r.split("\t")[1]) for r in self.helper("live-rows", str(self.live)).stdout.splitlines()]
        self.assertRegex(rows[0], r"^00:21  S0\s+Can we stream it instead\?$")
        self.assertIn("marked here", rows[1])
        self.assertRegex(rows[2], r"^00:25\s+Yes\.$")
        self.assertIn("now I think streaming the rows", rows[3])

    def test_the_live_header_says_the_state_in_one_short_sentence(self):
        self.say([{"start": 1, "end": 2, "text": "a", "speaker": "0"}, {"start": 3, "end": 4, "text": "b", "speaker": "1"}])
        self.assertEqual(bare(self.helper("live-header", str(self.live)).stdout.strip()), "Listening for 01:15. 2 lines, 2 voices.")
        self.say([], paused=True)
        self.assertTrue(bare(self.helper("live-header", str(self.live)).stdout).startswith("Paused at 01:15."))
        self.say([], status="stopped")
        self.assertTrue(bare(self.helper("live-header", str(self.live)).stdout).startswith("Stopped at 01:15."))
        (self.live / "state.json").unlink()
        self.assertEqual(self.helper("live-header", str(self.live)).stdout.strip(), "Getting ready to listen.")

    def test_live_rows_and_header_fit_their_column(self):
        self.say([{"start": 3599.0, "end": 3605.0, "text": "word " * 60, "speaker": "3"}], interim="word " * 60)
        lines = (self.helper("live-rows", str(self.live)).stdout.splitlines() + self.helper("live-header", str(self.live)).stdout.splitlines()
                 + self.helper("live-keys").stdout.splitlines())
        self.assertLessEqual(max(len(bare(line.split("\t")[-1])) for line in lines), 58)

    def test_the_live_pane_opens_with_three_lines_then_the_line_and_its_neighbours(self):
        self.say([{"start": 1, "end": 2, "text": "first", "speaker": "0"}, {"start": 3, "end": 5, "text": "second", "speaker": "1"},
                  {"start": 6, "end": 7, "text": "third", "speaker": "0"}])
        pane = bare(self.helper("live-detail", str(self.live), "1").stdout)
        top = pane.splitlines()[:5]
        self.assertEqual(top[0].strip(), "Speaker 1 at 00:03")
        self.assertEqual([line.split()[0] for line in top[2:]], ["voice", "length", "line"])
        for word in ("second", "first", "third"):
            self.assertIn(word, pane)
        now = bare(self.helper("live-detail", str(self.live), "now").stdout).splitlines()
        self.assertEqual([line.split()[0] for line in now[2:5]], ["state", "length", "follow"])

    def test_keys_reach_the_listener_as_words(self):
        self.say([])
        for step, word in (("pause", "pause"), ("mark", "mark"), ("follow", "follow")):
            self.assertEqual(self.helper("live-flow", str(self.live), step).stdout.strip(), "refresh")
        self.say([], paused=True)
        self.helper("live-flow", str(self.live), "pause")
        self.assertEqual((self.live / "control").read_text().split(), ["pause", "mark", "follow", "resume"])

    def test_stopping_with_nobody_to_answer_keeps_listening(self):
        self.say([])
        for step in ("stop", "digest", "quit"):
            asked = self.helper("live-flow", str(self.live), step, stdin=subprocess.DEVNULL, start_new_session=True)
            self.assertEqual(asked.stdout.strip(), "redraw", step)
        self.assertFalse((self.live / "control").exists())

    def test_quitting_a_session_that_already_stopped_asks_nothing(self):
        self.say([], status="stopped")
        self.assertEqual(self.helper("live-flow", str(self.live), "quit").stdout.strip(), "abort")
        self.assertEqual(self.helper("live-flow", str(self.live), "digest").stdout.strip(), "digest")

    def test_follow_decides_whether_the_screen_keeps_up(self):
        self.say([])
        self.assertEqual(self.helper("live-tick", str(self.live)).stdout.strip(), "follow")
        self.say([], follow=False)
        self.assertEqual(self.helper("live-tick", str(self.live)).stdout.strip(), "stay")

    # ── both ──

    def test_every_key_in_a_legend_is_bound_and_every_bound_key_is_in_a_legend(self):
        source = TOOL.read_text()
        for screen, keys_word in (("browse", "browse-keys"), ("live", "live-keys")):
            body = source[source.index("%s() {" % screen):]
            body = body[:body.index("\n}\n")]
            bound = set(re.findall(r'--bind "([a-z]+):transform', body))
            legend = set(re.findall(r"\x1b\[1m\x1b\[\d+m(\S+)\s*\x1b\[0m", self.helper(keys_word).stdout))   # a key is the bold word
            self.assertEqual(bound - {"load"}, legend, screen)

    def test_it_works_through_a_link_in_another_folder(self):
        link = Path(self.tmp.name) / "elsewhere" / "hear-screen"
        link.parent.mkdir()
        link.symlink_to(TOOL)
        got = subprocess.run([str(link), "browse"], capture_output=True, text=True, timeout=60, env=self.env, stdin=subprocess.DEVNULL)
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertIn("past runs", got.stdout)

    def test_the_live_screen_refuses_plainly_without_a_terminal(self):
        got = subprocess.run([str(TOOL), "live"], capture_output=True, text=True, timeout=60, env=self.env, stdin=subprocess.DEVNULL)
        self.assertEqual(got.returncode, 2)
        self.assertIn("--plain", got.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
