#!/usr/bin/env python3
"""Score the speech lane against audio whose true words, speakers and intents are known.

`check.py --unit` tests the scoring and audit code itself with no model (a second
or two, part of scripts/verify.sh). `check.py` runs the real models over
probe/hear/fixtures/ and prints one pass or fail line per capability (about a
minute). Build the fixtures first with make-fixture.py.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
FIX = HERE / "fixtures"

spec = importlib.util.spec_from_file_location("hear", ROOT / "lib" / "hear.py")
hear = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hear)

results = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    if ok and "--failures" in sys.argv:
        return
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  ({detail})" if detail else ""))


def word_error_rate(truth: str, got: str) -> float:
    """Share of the true words that were dropped, added or changed."""
    ag = hear.agreement(truth, got)
    return 1 - ag["agree"]


def unit() -> None:
    # The audit must report full agreement on identical text and catch a single changed word.
    same = hear.agreement("ship it next wednesday", "Ship it next Wednesday.")
    check("agreement: identical text agrees fully", same["agree"] == 1.0 and same["differing_spots"] == 0)
    one = hear.agreement("two days of work plus one day", "two days off work plus one day")
    check("agreement: one changed word is one differing spot", one["differing_spots"] == 1 and 0.8 < one["agree"] < 1.0, str(one["agree"]))
    check("agreement: unrelated text scores near zero", hear.agreement("alpha beta gamma", "one two three")["agree"] == 0.0)
    check("agreement: one number written three ways matches",
          hear.agreement("40,000 rows", "40000 rows")["agree"] == 1.0 and hear.agreement("40, 000 rows", "40000 rows")["agree"] == 1.0)
    check("agreement: two separate numbers stay separate", hear.words("rooms 12 and 300 seats") == ["rooms", "12", "and", "300", "seats"])

    tr = {"segments": [{"start": 0, "end": 5, "text": "a", "speaker": "0"}, {"start": 252.4, "end": 260, "text": "b", "speaker": "1"}]}
    good = hear.check_digest("## Decisions\n- Dev builds it [04:12]\n- Starts now [00:00]", tr)
    check("digest check: cited times that exist pass", good == {"points": 2, "uncited": [], "times_not_in_transcript": []}, str(good))
    two = hear.check_digest("- Shipped then fixed [00:00, 04:12]", tr)
    check("digest check: two times in one bracket both count", two["uncited"] == [] and two["times_not_in_transcript"] == [], str(two))
    bad = hear.check_digest("- Dev builds it [09:59]\n- Nobody said this", tr)
    check("digest check: an invented time is reported", bad["times_not_in_transcript"] == ["09:59"])
    check("digest check: a point with no time is reported", len(bad["uncited"]) == 1)

    # Two windows of one call. The second starts at 540 s and numbers the same two people
    # the other way round; both talk in the shared minute (540 to 600).
    def seg(a, b, who, text):
        return {"start": a, "end": b, "speaker": who, "text": text}
    w1 = [seg(0, 300, 0, "ann early"), seg(300, 550, 1, "bob middle"), seg(550, 568, 0, "ann join one"), seg(572, 598, 1, "bob join")]
    w2 = [seg(550, 568, 1, "ann join one"), seg(572, 598, 0, "bob join"), seg(600, 700, 1, "ann late"), seg(700, 800, 2, "cy new")]
    merged, unmatched = hear.stitch([(w1, 0), (w2, 540)])
    who = {s["text"]: s["speaker"] for s in merged}
    check("stitch: a person keeps one label across windows", who["ann early"] == who["ann late"] and who["bob middle"] == who["bob join"], str(who))
    check("stitch: different people keep different labels", len({who["ann early"], who["bob middle"], who["cy new"]}) == 3)
    check("stitch: someone first heard after the join is counted as unmatched", unmatched == 1, str(unmatched))
    texts = [s["text"] for s in merged]
    check("stitch: the shared minute is not transcribed twice", texts.count("ann join one") == 1 and texts.count("bob join") == 1, str(texts))
    check("stitch: turns stay in time order", [s["start"] for s in merged] == sorted(s["start"] for s in merged))

    # A run killed part way must leave its finished windows where the next run finds them.
    import tempfile
    calls = []

    def fake_model(model, kind, wav, context="", seconds=0.0):
        calls.append(Path(wav).name)
        if len(calls) == 2 and not resumed:
            raise KeyboardInterrupt   # stands in for the memory guard stopping the process
        return [{"start": 100.0, "end": 105.0, "text": f"said in {Path(wav).name}", "speaker": 0}], False

    with tempfile.TemporaryDirectory() as td:
        long_wav = Path(td) / "long.wav"
        import wave as _w
        with _w.open(str(long_wav), "wb") as o:
            o.setnchannels(1); o.setsampwidth(2); o.setframerate(hear.RATE)
            o.writeframes(b"\x00\x00" * hear.RATE * 1300)   # three windows
        keep = (hear.run_model, hear.load_model, hear.unload, hear.zrecover_grant, hear.to_wav, hear.OUT)
        kept_settle, settled = hear.settle_voices, []
        hear.settle_voices = lambda segs, wav: (settled.append(len(segs)) or segs, "voices stood in for the test")
        hear.run_model, hear.load_model, hear.unload = fake_model, (lambda k: None), (lambda m: None)
        hear.zrecover_grant, hear.to_wav, hear.OUT = (lambda *a: None), (lambda s, t: long_wav), Path(td) / "out"
        try:
            resumed = False
            try:
                hear.transcribe(long_wav, True, "", Path(td))
                died = False
            except KeyboardInterrupt:
                died = True
            left = sorted(p.name for p in (Path(td) / "out" / ".partial").glob("*/window-*.json"))
            check("resume: a killed run leaves its finished window on disk", died and left == ["window-0.json"], str(left))
            resumed, calls[:] = True, []
            tr = hear.transcribe(long_wav, True, "", Path(td))
            check("resume: the next run reads only the windows that were missing", calls == ["part1.wav", "part2.wav"], str(calls))
            check("resume: the finished transcript has all three windows", len(tr["segments"]) == 3, str(len(tr["segments"])))
            check("resume: nothing is left behind after success", not list((Path(td) / "out" / ".partial").glob("*")))
            check("long call: the voice check runs once, over the joined transcript", settled == [3] and "voices stood in" in " ".join(tr["notes"]), str(settled))
        finally:
            hear.run_model, hear.load_model, hear.unload, hear.zrecover_grant, hear.to_wav, hear.OUT = keep
            hear.settle_voices = kept_settle

    # The live cutter: quiet room, two spoken stretches with a pause between, one key click.
    import numpy as np
    sys.path.insert(0, str(ROOT / "lib"))
    import hear_live
    rate = hear_live.RATE
    rng = np.random.default_rng(7)

    def quiet(s):
        return (rng.standard_normal(int(rate * s)) * 0.001).astype(np.float32)

    def speech(s):
        return (rng.standard_normal(int(rate * s)) * 0.08).astype(np.float32)
    stream = np.concatenate([quiet(1.5), speech(2.0), quiet(1.2), speech(1.0), quiet(1.0), speech(0.06), quiet(1.5)])
    cutter, got = hear_live.Cutter(), []
    for i in range(0, len(stream), rate // 10):          # in 100 ms blocks, as the microphone delivers it
        got += cutter.push(stream[i:i + rate // 10])
    check("live cutter: two stretches of speech come out as two utterances", len(got) == 2, str(len(got)))
    check("live cutter: each starts where the speech started", len(got) == 2 and abs(got[0][0] - 1.5) < 0.4 and abs(got[1][0] - 4.7) < 0.4,
          str([round(g[0], 2) for g in got]))
    check("live cutter: an utterance holds its speech and little else", len(got) == 2 and 1.9 < len(got[0][1]) / rate < 3.3,
          str([round(len(g[1]) / rate, 2) for g in got]))
    check("live cutter: a key click is not an utterance", cutter.flush() is None and len(got) == 2)
    open_cut = hear_live.Cutter()
    open_cut.push(np.concatenate([quiet(1.0), speech(1.0)]))
    check("live cutter: speech still open when the stream stops is not lost", open_cut.flush() is not None)
    long_cut, pieces = hear_live.Cutter(max_s=5.0), []
    pieces += long_cut.push(np.concatenate([quiet(1.0), speech(12.0)]))
    check("live cutter: a long monologue is cut so text keeps coming", len(pieces) >= 2, str(len(pieces)))
    # Someone talking for a while, with a short gap between sentences and a dip mid-way.
    talk = np.concatenate([quiet(1.0), speech(7.0), quiet(0.45), speech(3.0), quiet(1.5)])
    sent, parts = hear_live.Cutter(), []
    for i in range(0, len(talk), rate // 10):
        parts += sent.push(talk[i:i + rate // 10])
    check("live cutter: after a while, the gap between sentences is enough to cut", len(parts) == 2, str(len(parts)))
    short = np.concatenate([quiet(1.0), speech(1.2), quiet(0.45), speech(1.2), quiet(1.5)])
    cmd, whole = hear_live.Cutter(), []
    for i in range(0, len(short), rate // 10):
        whole += cmd.push(short[i:i + rate // 10])
    check("live cutter: a short command with a breath in it stays whole", len(whole) == 1, str(len(whole)))
    dip = np.concatenate([quiet(1.0), speech(4.0), speech(0.2) * 0.2, speech(4.0)])
    quietest, cut = hear_live.Cutter(max_s=6.0, short_silence_s=5.0), []
    cut += quietest.push(dip)
    check("live cutter: with no pause, the forced cut lands on the quietest moment", len(cut) >= 1 and abs(len(cut[0][1]) / rate - 4.4) < 0.4,
          str([round(len(c[1]) / rate, 2) for c in cut]))

    # Joining labels by voice. Prints are built to sit at chosen distances from each other.
    import voiceprint as vp

    def near(base, other, alike):
        v = alike * base + np.sqrt(1 - alike * alike) * other
        return v / np.linalg.norm(v)
    e = np.eye(8, dtype=np.float32)
    ann, bob = e[0], near(e[0], e[1], 0.82)          # two people who sound alike on one line
    owner, sure, likely = vp.join_labels({"a": (ann, 300.0), "a2": (near(ann, e[2], 0.97), 80.0), "b": (bob, 200.0)})
    check("voices: one person split in two is joined", owner["a2"] == owner["a"] and sure == 1, f"{owner} sure={sure}")
    check("voices: two people who sound alike stay apart", owner["b"] != owner["a"], str(owner))
    owner, sure, likely = vp.join_labels({"a": (ann, 300.0), "c": (e[3], 200.0), "few": (near(ann, e[4], 0.76), 12.0)})
    check("voices: a brief label goes to the one voice it is close to", owner["few"] == owner["a"] and likely == 1 and sure == 0, f"{owner} likely={likely}")
    owner, sure, likely = vp.join_labels({"a": (ann, 300.0), "b": (bob, 200.0), "few": (near(near(ann, bob, 0.95), e[5], 0.80), 12.0)})
    check("voices: a brief label close to two voices is left alone", owner["few"] == "few" and likely == 0, f"{owner}")
    owner, sure, likely = vp.join_labels({"a": (ann, 300.0), "few": (near(ann, e[4], 0.55), 12.0)})
    check("voices: a brief label that is not close enough is left alone", owner["few"] == "few", str(owner))
    owner, sure, likely = vp.join_labels({"a": (ann, 300.0), "long": (near(ann, e[4], 0.76), 90.0)})
    check("voices: plenty of speech at 0.76 is a different person, not a join", owner["long"] == "long", str(owner))
    # One stretch of live audio: person A, a short pause, person B, a short pause, person B again.
    # The stand-in printer tells them apart by loudness, which is all the test needs.
    def loud(s, gain):
        return (rng.standard_normal(int(rate * s)) * gain).astype(np.float32)

    def by_gain(a):
        return e[0] if float(np.sqrt(np.mean(a * a))) < 0.07 else e[1]
    gap = np.zeros(int(rate * 0.45), dtype=np.float32)
    exchange = np.concatenate([loud(1.6, 0.05), gap, loud(1.6, 0.10), gap, loud(1.6, 0.10)])
    parts2 = vp.split_at_voice_change(exchange, printer=by_gain)
    check("voice change: a quick exchange is cut where the speaker changes", len(parts2) == 2 and abs(parts2[1][0] - 1.8) < 0.3,
          str([(round(p[0], 2), round(len(p[1]) / rate, 2)) for p in parts2]))
    check("voice change: nothing is lost in the cut", sum(len(p[1]) for p in parts2) == len(exchange))
    solo = np.concatenate([loud(1.6, 0.10), gap, loud(1.6, 0.10)])
    check("voice change: one speaker pausing stays whole", len(vp.split_at_voice_change(solo, printer=by_gain)) == 1)
    check("voice change: a stretch with no pause stays whole", len(vp.split_at_voice_change(loud(3.0, 0.1), printer=by_gain)) == 1)

    segs_in = [{"start": 0, "end": 0.5, "text": "x", "speaker": "7"}]
    out_segs, stats = vp.merge_voices(segs_in, np.zeros(16000, dtype=np.float32) + 0.0)
    check("voices: a label too short to print is kept and counted", out_segs[0]["speaker"] == "0" and stats["unchecked"] == 1, str(stats))

    # Past runs: numbering, the latest, a missing one, and where a run's audio is found.
    with tempfile.TemporaryDirectory() as td:
        kept_log, kept_out = hear.LOG, hear.OUT
        hear.LOG, hear.OUT = Path(td) / "h.jsonl", Path(td) / "out"
        try:
            src_file = Path(td) / "memo.wav"
            src_file.write_bytes(b"RIFF")
            folder = hear.save("memo", {"ok": True, "text": "hello there"}, {"transcript.md": "hello there\n"}, src_file)
            check("past runs: a run folder keeps the audio it heard", (folder / "audio.wav").read_bytes() == b"RIFF")
            hear.log({"verb": "words", "ok": True, "artifact": str(folder), "file": str(src_file), "snippet": "hello there", "seconds": 3})
            hear.log({"verb": "words", "ok": True, "artifact": None, "file": str(src_file), "snippet": "older style row", "seconds": 4})
            hear.log({"verb": "live", "ok": True, "artifact": None, "file": None, "snippet": "typed", "seconds": 0})
            check("past runs: a number is a line number", hear.pick_run("1")[1]["snippet"] == "hello there")
            check("past runs: no number means the latest", hear.pick_run("")[0] == 3 and hear.pick_run("-1")[0] == 3)
            check("past runs: a run's kept audio is used first", hear.audio_of(1, hear.pick_run("1")[1]) == folder / "audio.wav")
            check("past runs: with no kept audio, the original file is used", hear.audio_of(2, hear.pick_run("2")[1]) == src_file)
            for bad, code in (("9", "no_such_run"), ("x", "no_such_run")):
                try:
                    hear.pick_run(bad)
                    got_code = None
                except hear.HearError as e:
                    got_code = e.code
                check(f"past runs: asking for run {bad!r} is refused with a reason", got_code == code, str(got_code))
            try:
                hear.audio_of(3, hear.pick_run("3")[1])
                got_code = None
            except hear.HearError as e:
                got_code = e.code
            check("past runs: a run with no audio anywhere says so", got_code == "no_audio", str(got_code))
            check("past runs: a history line shows number, kind, length and first words",
                  "   1  " in hear.history_line(1, hear.pick_run("1")[1]) and "00:03" in hear.history_line(1, hear.pick_run("1")[1])
                  and "hello there" in hear.history_line(1, hear.pick_run("1")[1]))
        finally:
            hear.LOG, hear.OUT = kept_log, kept_out

    check("times past an hour keep the hour", hear.stamp(3725) == "1:02:05" and hear.stamp(65) == "01:05")
    md = hear.as_markdown({"text": "x", "segments": [{"start": 61, "end": 62, "text": "Hi.", "speaker": "A1"}]})
    check("transcript line carries time and speaker", md == "[01:01] Speaker A1: Hi.\n", repr(md))


SANDBOX = None


def run_hear(*args) -> dict:
    """Run the real command, with its history and run folders pointed at a throwaway place."""
    global SANDBOX
    if SANDBOX is None:
        import tempfile
        SANDBOX = tempfile.mkdtemp(prefix="hear-check-")
    r = subprocess.run([str(ROOT / "bin" / "hear"), *args, "--json"], capture_output=True, text=True,
                       env=dict(os.environ, LM_HEAR_SANDBOX=SANDBOX))
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {"ok": False, "error": "no_json", "message": (r.stderr or r.stdout)[-300:]}


def live() -> None:
    truth = json.loads((FIX / "truth.json").read_text())
    call, turns = truth["call"], truth["call"]["turns"]
    script = " ".join(t["text"] for t in turns)

    plain = run_hear(str(FIX / "call.wav"))
    wer = word_error_rate(script, plain.get("text", ""))
    check("words: call transcribed within 5% word error", plain.get("ok") and wer <= 0.05, f"{wer:.1%}")

    spk = run_hear(str(FIX / "call.wav"), "--speakers")
    segs = spk.get("segments", [])
    wer_s = word_error_rate(script, spk.get("text", ""))
    check("speakers: words within 5% word error", spk.get("ok") and wer_s <= 0.05, f"{wer_s:.1%}")
    check("speakers: found the right number of people", len({s.get("speaker") for s in segs}) == call["speakers"],
          f"{len({s.get('speaker') for s in segs})} of {call['speakers']}")
    # Each true turn goes to the label that overlaps it most; a label must then mean one person.
    label_of, right = {}, 0
    for t in turns:
        best = max(segs, key=lambda s: min(s["end"], t["end"]) - max(s["start"], t["start"]), default=None)
        if best is None:
            continue
        owner = label_of.setdefault(best["speaker"], t["speaker"])
        right += owner == t["speaker"]
    check("speakers: every turn given to the right person", right == len(turns), f"{right} of {len(turns)}")

    hits = 0
    for n in truth["notes"]:
        got = (run_hear("intent", str(FIX / n["file"])).get("intent") or {})
        ok = got.get("kind") == n["intent"] and n["target"] in (got.get("target") or "").lower()
        hits += ok
        if not ok:
            print(f"       {n['file']}: wanted {n['intent']}/{n['target'] or '-'}, got {got.get('kind')}/{got.get('target')}")
    check("intent: every spoken note routed to the right kind", hits == len(truth["notes"]), f"{hits} of {len(truth['notes'])}")

    # Live notes, with the scripted call played in place of the microphone.
    ln = run_hear("live", "--notes", "--__feed", str(FIX / "call.wav"))
    lines = ln.get("segments", [])
    wer_l = word_error_rate(script, ln.get("text", ""))
    check("live notes: words within 5% word error", ln.get("ok") and wer_l <= 0.05, f"{wer_l:.1%}")
    # Two of the three scripted voices sound alike, so a turn of one may share a line with the
    # other. The third is clearly different: each of her turns must start a line of its own.
    def line_at(t):
        return next((a for a in lines if abs(a["start"] - t["start"]) < 1.5), None)
    hers = [line_at(t) for t in turns if t["speaker"] == "Priya"]
    check("live notes: every turn of the clearly different voice starts its own line", all(hers), f"{sum(1 for h in hers if h)} of {len(hers)}")
    check("live notes: no sentence is cut into fragments", len(lines) <= len(turns), f"{len(lines)} lines for {len(turns)} turns")
    her_labels = {h.get("speaker") for h in hers if h}
    other_labels = {a.get("speaker") for a in lines if a not in hers}
    check("live notes: the clearly different voice keeps a label of its own", len(her_labels) == 1 and not (her_labels & other_labels),
          f"{her_labels} against {other_labels}")
    kept = Path(ln.get("artifact", "/nonexistent")) / "audio.wav"
    check("live notes: the recording is kept", kept.is_file() and kept.stat().st_size > 1_000_000)

    dg = run_hear("call", str(FIX / "call.wav"))
    digest = (dg.get("digest") or "").lower()
    missing = [ws for ws in call["digest_must_have"] if not all(w in digest for w in ws)]
    check("call digest: keeps the decision, owners and dates", dg.get("ok") and not missing, f"missing {missing}" if missing else "")
    invented = [w for w in call.get("digest_must_not_have", []) if w in digest]
    check("call digest: uses no name that was never spoken", dg.get("ok") and not invented, f"invented {invented}" if invented else "")
    dc = dg.get("digest_check") or {"uncited": ["?"], "times_not_in_transcript": ["?"]}
    check("call digest: every point cites a real moment", not dc["uncited"] and not dc["times_not_in_transcript"],
          f"{len(dc['uncited'])} uncited, {len(dc['times_not_in_transcript'])} bad times")


if __name__ == "__main__":
    unit() if "--unit" in sys.argv else live()
    print(f"hear check: {sum(results)}/{len(results)} passed")
    sys.exit(0 if all(results) else 1)
