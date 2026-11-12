#!/usr/bin/env python3
"""Build the speech test audio: a scripted three-person call and a set of short voice notes.

Every clip is spoken by a macOS voice from a script kept in this file, so the
true words, the true speaker of each turn and the true intent of each note are
known exactly. Output goes to probe/hear/fixtures/ with a truth.json beside it.
Needs only `say` and `afconvert`, both part of macOS.
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

OUT = Path(__file__).parent / "fixtures"
RATE = 16000

# (speaker, voice, line). Names, a number, a date and a decision are in there on
# purpose: they are what a meeting summary has to carry and what ASR gets wrong.
CALL = [
    ("Priya", "Samantha", "Okay, let's start. The export builder shipped on Tuesday, and we have two customer reports since then."),
    ("Marcus", "Daniel", "Both reports are about the same thing. The spreadsheet download times out when a catalog has more than forty thousand rows."),
    ("Dev", "Rishi", "I looked at it this morning. The query is fine. The slow part is building the file in memory before we send it."),
    ("Priya", "Samantha", "Can we stream it instead?"),
    ("Dev", "Rishi", "Yes. I think streaming the rows is two days of work, plus one day for testing."),
    ("Marcus", "Daniel", "I am not sure that is enough. Last time we changed the download path, we broke the audit log."),
    ("Priya", "Samantha", "Fair point. So the decision is, Dev builds the streaming download, and Marcus writes the audit log test first."),
    ("Marcus", "Daniel", "Agreed. I will have that test ready by Thursday."),
    ("Dev", "Rishi", "Then I will start on Friday, and we ship it next Wednesday."),
    ("Priya", "Samantha", "Good. One open question. Do we tell the two customers now, or after it ships?"),
    ("Marcus", "Daniel", "I would tell them now. They are waiting."),
    ("Priya", "Samantha", "Okay, I will email both of them today. Thanks, everyone."),
]

# (file stem, voice, line, true intent, the word the routed target must contain or "")
NOTES = [
    ("note-claude", "Rishi", "Claude, run the test suite in the local models repo and tell me what fails.", "agent_command", "claude"),
    ("note-note", "Rishi", "Note to self. The rug border needs twelve motifs, not eleven, and the corner piece is mirrored.", "note", ""),
    ("note-app", "Rishi", "Open Slack and mute the general channel for one hour.", "app_action", "slack"),
    ("note-question", "Rishi", "What is the capital of Australia?", "question", ""),
    ("note-reminder", "Rishi", "Remind me to call the bank tomorrow at ten in the morning.", "reminder", ""),
    ("note-chatter", "Rishi", "Hmm, okay, yeah, one second.", "none", ""),
]


def speak(voice: str, text: str, wav: Path) -> None:
    aiff = wav.with_suffix(".aiff")
    subprocess.run(["say", "-v", voice, "-o", str(aiff), text], check=True)
    subprocess.run(["afconvert", "-f", "WAVE", "-d", f"LEI16@{RATE}", "-c", "1", str(aiff), str(wav)], check=True)
    aiff.unlink()


def read_frames(wav: Path) -> bytes:
    with wave.open(str(wav), "rb") as w:
        assert w.getframerate() == RATE and w.getnchannels() == 1, wav
        return w.readframes(w.getnframes())


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    gap = b"\x00\x00" * int(RATE * 0.45)
    frames, turns, t = b"", [], 0.0
    for i, (speaker, voice, line) in enumerate(CALL):
        part = OUT / f"_turn{i}.wav"
        speak(voice, line, part)
        data = read_frames(part)
        part.unlink()
        dur = len(data) / 2 / RATE
        turns.append({"speaker": speaker, "start": round(t, 2), "end": round(t + dur, 2), "text": line})
        frames += data + gap
        t += dur + 0.45
    with wave.open(str(OUT / "call.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(frames)

    notes = []
    for stem, voice, line, intent, target in NOTES:
        speak(voice, line, OUT / f"{stem}.wav")
        notes.append({"file": f"{stem}.wav", "text": line, "intent": intent, "target": target})

    truth = {
        "call": {
            "file": "call.wav", "seconds": round(t, 1), "speakers": 3, "turns": turns,
            # Facts a faithful summary has to keep. Each is a list of words that must all appear.
            "digest_must_have": [["stream", "friday"], ["marcus", "audit", "test"], ["thursday"], ["wednesday"], ["email", "customers"]],
            # Nobody says this name aloud, so a digest that uses it made it up.
            "digest_must_not_have": ["priya"],
        },
        "notes": notes,
    }
    (OUT / "truth.json").write_text(json.dumps(truth, indent=1))
    print(f"wrote {OUT}/call.wav ({t:.0f}s, {len(turns)} turns), {len(notes)} notes, truth.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
