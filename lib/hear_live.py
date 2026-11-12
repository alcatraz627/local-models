"""Speak into this Mac's microphone and get the words back.

Two ways to use it. `lm hear live` records until you press Enter, then prints
what you said (add --intent to also say what you were asking for). `lm hear live
--notes` keeps listening, cuts your speech at each pause and prints every
sentence a moment after you finish it, until you press Ctrl-C. The notes mode
also keeps the audio, so `lm hear call` can add speakers and a digest afterwards.

Only the microphone is heard. The other side of a video call is heard only if
it plays through the speakers; capturing it properly needs a system-audio
device, which is a separate setup (docs/11-speech-lane.md).
"""
import json
import queue
import signal
import sys
import tempfile
import time
import wave
from pathlib import Path

import numpy as np

# Use the module that is already running as `lm hear`, so its error type is the one
# its own handler catches. A second import would give a look-alike class that slips past.
hear = sys.modules["__main__"] if hasattr(sys.modules["__main__"], "HearError") else __import__("hear")

RATE = 16000


class Cutter:
    """Cuts a stream of microphone audio into utterances at the pauses.

    Feed it audio as it arrives; it hands back each stretch of speech once the
    speaker has been quiet for `end_silence_s`. Loudness is judged against the
    room: the quiet level is tracked while nobody talks, and speech is anything
    well above it. A stretch longer than `max_s` is cut anyway so text keeps
    coming during a monologue.
    """

    def __init__(self, rate=RATE, frame_ms=30, loud_factor=3.0, floor=0.004,
                 end_silence_s=0.8, max_s=28.0, min_s=0.35, lead_in_s=0.3,
                 settle_s=6.0, short_silence_s=0.33):
        self.rate, self.n = rate, int(rate * frame_ms / 1000)
        self.loud_factor, self.floor = loud_factor, floor
        self.end_frames = int(end_silence_s * 1000 / frame_ms)
        # A short command should stay whole, so it needs a real pause to end. Once
        # someone has been talking a while, the gap between two sentences is enough.
        self.settle_frames = int(settle_s * 1000 / frame_ms)
        self.short_end_frames = int(short_silence_s * 1000 / frame_ms)
        self.levels = []
        self.max_frames = int(max_s * 1000 / frame_ms)
        self.min_frames = int(min_s * 1000 / frame_ms)
        self.lead_frames = int(lead_in_s * 1000 / frame_ms)
        self.rest = np.zeros(0, dtype=np.float32)
        self.quiet = floor            # running estimate of the room's quiet level
        self.lead, self.cur, self.loud, self.silent = [], [], 0, 0
        self.t = 0.0                  # seconds of audio seen so far
        self.start = 0.0

    def push(self, samples: np.ndarray):
        """Take more audio; return the (start_second, audio) utterances that just ended."""
        done = []
        buf = np.concatenate([self.rest, samples.astype(np.float32)])
        while len(buf) >= self.n:
            frame, buf = buf[:self.n], buf[self.n:]
            level = float(np.sqrt(np.mean(frame * frame)))
            is_loud = level > max(self.floor, self.quiet * self.loud_factor)
            if not self.cur:
                if is_loud:
                    self.start = self.t - len(self.lead) * self.n / self.rate
                    self.cur, self.loud, self.silent = self.lead + [frame], 1, 0
                    self.levels = [0.0] * len(self.lead) + [level]
                    self.lead = []
                else:
                    self.quiet = 0.95 * self.quiet + 0.05 * level
                    self.lead = (self.lead + [frame])[-self.lead_frames:]
            else:
                self.cur.append(frame)
                self.levels.append(level)
                self.loud += is_loud
                self.silent = 0 if is_loud else self.silent + 1
                need = self.end_frames if len(self.cur) < self.settle_frames else self.short_end_frames
                if self.silent >= need:
                    out = self._end()
                    if out:
                        done.append(out)
                elif len(self.cur) >= self.max_frames:
                    # No pause came. Cut at the quietest moment of the last third
                    # instead of mid-word, and carry what follows into the next one.
                    third = len(self.cur) // 3
                    at = len(self.cur) - third + int(np.argmin(self.levels[-third:]))
                    tail, tail_levels = self.cur[at:], self.levels[at:]
                    self.cur, self.levels = self.cur[:at], self.levels[:at]
                    began = self.start
                    out = self._end()
                    if out:
                        done.append(out)
                    self.start = began + at * self.n / self.rate
                    self.cur, self.levels = tail, tail_levels
                    self.loud = sum(lv > max(self.floor, self.quiet * self.loud_factor) for lv in tail_levels)
                    self.silent = 0
            self.t += self.n / self.rate
        self.rest = buf
        return done

    def _end(self):
        cur, loud = self.cur, self.loud
        self.cur, self.loud, self.silent, self.levels = [], 0, 0, []
        # A cough or a key click is loud for a moment; real speech is loud for longer.
        return (self.start, np.concatenate(cur)) if loud >= self.min_frames else None

    def flush(self):
        """The utterance still open when the stream stops, if there is one."""
        return self._end() if self.cur else None


def write_wav(path: Path, audio: np.ndarray) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())


class FileFeed:
    """Stands in for the microphone in tests: plays a recording into the same queue.

    Everything after the microphone (cutting, transcribing, saving) then runs
    exactly as it does live, with audio whose words are known.
    """

    def __init__(self, wav_path: str, q: "queue.Queue", speed: float = 25.0):
        import threading
        with wave.open(wav_path, "rb") as w:
            assert w.getframerate() == RATE and w.getnchannels() == 1, "feed needs 16 kHz mono"
            self.audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        self.q, self.speed, self.done = q, speed, False
        self.thread = threading.Thread(target=self._play, daemon=True)

    def _play(self):
        step = RATE // 10
        for i in range(0, len(self.audio), step):
            self.q.put(self.audio[i:i + step])
            time.sleep(0.1 / self.speed)
        self.done = True

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread.join(timeout=5)

    def close(self):
        pass


def open_mic(q: "queue.Queue", feed: str = "", speed: float = 25.0):
    """Start the microphone; every block of audio it hears goes onto the queue."""
    if feed:
        source = FileFeed(feed, q, speed)
        source.start()
        return source
    try:
        import sounddevice as sd
    except ImportError:
        raise hear.HearError("no_recorder", "the sounddevice library is missing from the repo's Python",
                             "uv pip install sounddevice --python .venv/bin/python")

    def on_audio(block, frames, when, status):
        q.put(block[:, 0].copy())

    try:
        stream = sd.InputStream(samplerate=RATE, channels=1, dtype="float32", blocksize=RATE // 10, callback=on_audio)
        stream.start()
    except Exception as e:   # PortAudio raises its own error type for a missing or busy device
        raise hear.HearError("no_microphone", f"could not open the microphone: {e}",
                             "check System Settings, Sound, Input")
    return stream


def mic_silent_error():
    return hear.HearError("mic_silent", "the microphone returned pure silence, which is what macOS gives an app with no permission",
                          "System Settings, Privacy & Security, Microphone: allow your terminal, then run again")


def once(a, tmp: Path) -> dict:
    """Record one clip (until Enter, or for --seconds), then transcribe it."""
    q = queue.Queue()
    stream = open_mic(q, a.feed, getattr(a, "feed_speed", 25.0))
    try:
        if a.feed:
            while not stream.done:
                time.sleep(0.05)
        elif a.seconds:
            print(f"hear: listening for {a.seconds:g} s", file=sys.stderr)
            time.sleep(a.seconds)
        elif sys.stdin.isatty():
            print("hear: listening. Press Enter when you are done.", file=sys.stderr)
            sys.stdin.readline()
        else:
            raise hear.HearError("needs_seconds", "with no terminal there is no Enter key to stop on", "add --seconds 10")
    finally:
        stream.stop()
        stream.close()
    blocks = []
    while not q.empty():
        blocks.append(q.get())
    audio = np.concatenate(blocks) if blocks else np.zeros(0, dtype=np.float32)
    if not len(audio) or float(np.abs(audio).max()) < 1e-5:
        raise mic_silent_error()
    wav = tmp / "audio.wav"   # the caller keeps this with the run, so it can be done over later
    write_wav(wav, audio)
    model = hear.load_model("words")
    segs, _ = hear.run_model(model, "words", wav, a.context)
    hear.unload(model)
    text = " ".join(s["text"] for s in segs).strip()
    if not text:
        raise hear.HearError("no_speech", "nothing was said in that clip")
    payload = {"ok": True, "verb": "live", "text": text, "seconds": round(len(audio) / RATE, 1)}
    if a.intent:
        payload["intent"] = hear.ask_q("voice-intent", text, "small", "voice-intent.schema.json", 120).get("data")
    return payload


class Panel:
    """The live screen's side of a session: what the screen reads, and the keys it sends back.

    The listening process and the screen are two programs. They meet in one
    folder: this writes the lines heard and a one-line state there, and reads
    the words the screen leaves when a key is pressed (pause, mark, stop). With
    no folder, every method does nothing, which is the plain no-screen mode.
    """

    def __init__(self, folder: str = ""):
        self.folder = Path(folder) if folder else None
        self.paused, self.follow, self.seen = False, True, 0

    def line(self, row: dict) -> None:
        if self.folder:
            with (self.folder / "lines.jsonl").open("a") as f:
                f.write(json.dumps(row) + "\n")

    def show(self, status: str, t: float, interim: str = "") -> None:
        if not self.folder:
            return
        staged = self.folder / "state.tmp"
        staged.write_text(json.dumps({"status": status, "t": round(t, 1), "paused": self.paused,
                                      "follow": self.follow, "interim": interim}))
        staged.replace(self.folder / "state.json")   # the screen must never read half a file

    def commands(self):
        """The words the screen has left since the last look, oldest first."""
        if not self.folder:
            return []
        try:
            words = (self.folder / "control").read_text().split()
        except OSError:
            return []
        new, self.seen = words[self.seen:], len(words)
        return new


def notes(a) -> dict:
    """Listen until stopped, printing each utterance as it ends and keeping the audio."""
    out = hear.OUT / f"{time.strftime('%Y%m%dT%H%M%S')}-live"
    out.mkdir(parents=True, exist_ok=True)
    panel = Panel(getattr(a, "state", ""))
    panel.show("starting", 0)
    q = queue.Queue()
    model = hear.load_model("words")
    stream = open_mic(q, a.feed, getattr(a, "feed_speed", 25.0))
    cutter, lines, heard_sound = Cutter(), [], False
    import voiceprint
    voices = voiceprint.LiveVoices()
    voiceprint.net()   # load it now, so the first sentence is not the slow one
    full = wave.open(str(out / "audio.wav"), "wb")
    full.setnchannels(1)
    full.setsampwidth(2)
    full.setframerate(RATE)
    stop = {"now": False}

    def ask_stop(signum, frame):
        stop["now"] = True
    signal.signal(signal.SIGINT, ask_stop)
    signal.signal(signal.SIGTERM, ask_stop)   # a kill still closes the audio file properly

    def take(utterance):
        # A quick exchange arrives as one stretch; give each speaker in it a line of their own.
        start, audio = utterance
        for offset, piece in voiceprint.split_at_voice_change(audio):
            take_one(start + offset, piece)

    def take_one(start, audio):
        with tempfile.NamedTemporaryFile(suffix=".wav") as f:
            write_wav(Path(f.name), audio)
            segs, _ = hear.run_model(model, "words", Path(f.name), a.context)
        text = " ".join(s["text"] for s in segs).strip()
        if text:
            # A first guess at who is talking, from this sentence's voice alone. The pass
            # that `lm hear call` runs afterwards over the whole recording is the firm one.
            who = voices.label(audio)
            line = f"[{hear.stamp(start)}] " + (f"Speaker {who}: " if who is not None else "") + text
            lines.append({"start": round(start, 2), "end": round(start + len(audio) / RATE, 2), "text": text,
                          **({"speaker": who} if who is not None else {})})
            panel.line(lines[-1])
            print(line, file=sys.stderr if a.json else sys.stdout, flush=True)   # --json keeps stdout for the one object
            with (out / "transcript.md").open("a") as f:   # every line is on disk the moment it exists
                f.write(line + "\n")

    print(f"hear: listening. Ctrl-C to stop. Saving to {out}", file=sys.stderr)
    t0 = time.time()
    interim, interim_at = "", 0.0

    def hearing_now():
        """The words of the sentence still being spoken, for the screen to show before it ends."""
        if len(cutter.cur) * cutter.n < RATE:
            return ""
        with tempfile.NamedTemporaryFile(suffix=".wav") as f:
            write_wav(Path(f.name), np.concatenate(cutter.cur))
            segs, _ = hear.run_model(model, "words", Path(f.name), a.context)
        return " ".join(s["text"] for s in segs).strip().rstrip(".")   # the model ends every guess with a full stop

    try:
        while not stop["now"] and not (a.seconds and time.time() - t0 >= a.seconds):
            for word in panel.commands():
                if word == "stop":
                    stop["now"] = True
                elif word in ("pause", "resume"):
                    panel.paused = word == "pause"
                    if panel.paused:
                        held = cutter.flush()      # what was being said when pause was pressed still counts
                        if held:
                            take(held)
                        interim = ""
                elif word == "follow":
                    panel.follow = not panel.follow
                elif word == "mark":
                    panel.line({"mark": True, "start": round(cutter.t, 2)})
                    with (out / "transcript.md").open("a") as f:
                        f.write(f"[{hear.stamp(cutter.t)}] (marked here)\n")
            try:
                block = q.get(timeout=0.2)
            except queue.Empty:
                if a.feed and stream.done:
                    break
                panel.show("listening", cutter.t, interim)
                continue
            if panel.paused:
                panel.show("listening", cutter.t)
                continue                            # a paused session hears nothing and records nothing
            heard_sound = heard_sound or float(np.abs(block).max()) >= 1e-5
            full.writeframes((np.clip(block, -1, 1) * 32767).astype(np.int16).tobytes())
            ended = cutter.push(block)
            for u in ended:
                take(u)
            if ended or not cutter.cur:
                interim = ""
            elif panel.folder and time.time() - interim_at >= 1.0:
                interim, interim_at = hearing_now(), time.time()
            panel.show("listening", cutter.t, interim)
    finally:
        stream.stop()
        stream.close()
        full.close()
    last = cutter.flush()
    if last:
        take(last)
    panel.show("stopped", cutter.t)
    hear.unload(model)
    if not heard_sound:
        raise mic_silent_error()
    payload = {"ok": True, "verb": "live-notes", "seconds": round(cutter.t, 1), "segments": lines,
               "text": " ".join(s["text"] for s in lines), "artifact": str(out)}
    (out / "result.json").write_text(json.dumps(payload, indent=1))
    print(f"hear: stopped after {hear.stamp(cutter.t)}. For speakers and a digest: lm hear call {out / 'audio.wav'}", file=sys.stderr)
    return payload


def run(a, tmp: Path) -> dict:
    return notes(a) if a.notes else once(a, tmp)
