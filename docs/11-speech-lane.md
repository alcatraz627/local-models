---
reader: the owner, or an agent about to use or extend the speech tools
---

# Speech lane: `lm hear`

`lm hear` turns speech into text on this Mac. Nothing leaves the machine.

It also lets you check the text without listening to the audio again.

It is the first slice of two goals:

- understand a recorded call
- speak to the computer and have it work out what you meant

## What you can do today

```bash
lm hear memo.m4a                     # the words
lm hear call.mp4 --speakers          # who said what, with times
lm hear call call.mp4                # the same, plus a digest of what the call meant
lm hear intent memo.m4a              # what a spoken note is asking for (it runs nothing)
lm hear intent --text "open slack"   # the same, from text
lm hear check call.mp4               # two unrelated transcribers, and where they disagree
lm hear live                         # talk into the microphone, press Enter, get the words
lm hear live --intent                # the words, and what you were asking for
lm hear live --notes                 # keeps listening; prints each sentence as you finish it
```

| Add | To get |
|---|---|
| `--json` | one JSON object |
| `--context "Priya, Speedway, PIM"` | names and terms spelled right |

Input is any audio or video file macOS can open: mp4, mov, m4a, mp3, wav. mkv and webm need ffmpeg, which is not installed.

Each run is saved under `outputs/hear/<time>-<name>/` and logged to `logs/hear-history.jsonl`.

## Speaking to it live

`lm hear live` listens on the Mac's microphone.

| Mode | What happens |
|---|---|
| `lm hear live` | Records until you press Enter, then prints what you said. About 2 s after you stop. |
| `lm hear live --intent` | The same, plus what kind of request it was. |
| `lm hear live --notes` | Keeps listening until Ctrl-C. Prints each sentence a moment after you finish it. |

Notes mode cuts your speech at the pauses. A short command needs a real pause (0.8 s) to end, so it stays whole. Once you have been talking for six seconds, the gap between two sentences is enough.

Notes mode keeps the audio in the run folder. Afterwards, `lm hear call <that audio.wav>` adds speakers and a digest.

What it has been tested on:

- The cutting logic, on generated audio with known pauses (`probe/hear/check.py --unit`).
- The whole path after the microphone, by playing the scripted call into it in place of the mic. Nine lines came out, one per sentence, with one wrong word.
- The microphone itself delivers audio to the repo's Python.

Not yet tested: a real voice spoken into the microphone. The speakers were muted during the build, so the loop could not be closed.

It hears the microphone only. On a video call it hears you, and hears the others only if they play through the speakers.

## Which model does which job

| Job | Model | Why this one | Measured on the scripted call (65 s) |
|---|---|---|---|
| words | Qwen3-ASR 0.6B (MLX, bf16) | most exact, fastest | 1.1% word error, 2.6 s, 2 GB |
| who spoke | VibeVoice-ASR 4-bit (MLX, 5.7 GB on disk) | one model for words, speakers and times | 1.7% word error, 3 of 3 speakers, 12 of 12 turns, 15 s, 6 GB |
| second opinion | Parakeet TDT 0.6B v3 (MLX) | unrelated to the other two, has sentence times | one wrong word ("off" for "of") |
| digest | `gemma4:26b` through `q --intent call-digest` | long context, best local prose | kept every decision, owner and date; named nobody who was not named aloud |
| intent | `gemma4-e4b-warm` through `q --intent voice-intent`, schema-constrained | small and obeys the schema | 6 of 6 spoken notes |

Two speaker-splitting models were tried and dropped:

- Sortformer v2.1 found every turn boundary but merged the two male voices into one speaker.
- Sortformer v1 missed most of one speaker's words.

Both are still in the Hugging Face cache (0.5 GB together). `hf cache delete` removes them.

## How to know a transcript is right

A transcript nobody has listened to is a claim. These are the checks, cheapest first.

### 1. Audio with a known answer

`probe/hear/make-fixture.py` speaks a scripted three-person call and six voice notes with macOS voices. The true words, speakers and intents are in its `truth.json`.

| Command | What it tests | Time |
|---|---|---|
| `probe/hear/check.py` | the real models against the truth | about a minute |
| `probe/hear/check.py --unit` | the scoring code itself, no model; part of `scripts/verify.sh` | a second |

### 2. Two unrelated transcribers

`lm hear check FILE` runs Qwen3-ASR and Parakeet over the same audio. It reports the share of words they agree on and shows samples of where they differ.

Two different models rarely make the same mistake. A disagreement marks a spot where one of them is wrong.

`--against result.json` judges an earlier transcript, such as the speakers one, against both.

### 3. Digest citations

Every digest point must end with the transcript time it rests on. The tool reports points with no time, and times that are not in the transcript.

This proves a point is anchored. It does not prove the point is fair.

### 4. Digest evidence page

`digest-evidence.md` in the run folder prints each digest point with the transcript lines it cites underneath. Judging a point then takes a few seconds of reading.

### What none of these cover

- Whether a speaker label is the right person on real voices. The test voices are synthetic.
- Anything the digest left out. A digest can be accurate in every line and still miss the thing you cared about.

## Long recordings and the memory guard

The speakers model uses more memory the longer the audio is. A 41-minute call in one pass went past 29 GB, and zrecover stopped it. That is zrecover doing its job.

So `lm hear` reads long audio in 10-minute windows that overlap by one minute.

| Question | Answer |
|---|---|
| What does one window cost? | About 11.4 GB at peak and 145 s, when nothing else is using the GPU. |
| How do speakers stay the same person? | Numbers restart in every window. A new label is matched to the earlier label it shares the most talking time with in the shared minute. |
| What if someone is silent in the shared minute? | They cannot be matched. They get a new label, and the run says how many times that happened. |
| What if the run is killed? | Each finished window is already in `outputs/hear/.partial/`. Run the same command again and it starts at the first unfinished window. |
| What if the digest fails? | The transcript is saved anyway. |

`lm hear` asks zrecover for a 16 GB grant for its own process and hands it back on exit. The grant lifts the size cap only. zrecover still stops the process if the Mac runs short of memory, which is the intended order of things.

## What a spoken note is asking for

`lm hear intent` sorts a spoken note into one of six kinds.

| Kind | Example |
|---|---|
| `agent_command` | "Claude, run the test suite and tell me what fails." |
| `app_action` | "Open Slack and mute the general channel for one hour." |
| `note` | "Note to self. The rug border needs twelve motifs." |
| `reminder` | "Remind me to call the bank tomorrow at ten." |
| `question` | "What is the capital of Australia?" |
| `none` | "Hmm, okay, one second." |

It also returns the target it heard (`claude`, `slack`), the request with the filler removed, and the time for a reminder. When it is unsure between acting and not acting, it is told to choose `note` or `none`.

It never acts. Local models do not drive tools here (`docs/03-tool-orchestration-decision.md`). The classifier has to earn trust on your own voice before anything is wired to it.

## The end state

Set by the owner on 2026-11-12, after trying `lm hear live`. The basics work. This is what it has to become.

| Wanted | Today |
|---|---|
| A transcript that groups what was said by voice. Names are not needed. | Partly. Recordings get speaker labels, and people who speak little split into several. Live notes get no labels until `lm hear call` is run on the saved audio. |
| Approximate timestamps. They need not be exact. | Yes. |
| The full raw recording kept as a backup. | Yes. Every run folder holds `audio.wav`, the 16 kHz copy, about 115 MB an hour. The original file is not copied. |
| The same everyday controls as every `lm` tool: history, show a past run. | Yes. `lm hear history`, `lm hear show N`, and rows in `lm timeline`. |
| Re-run a past run with different options, without recording again. | Yes. `lm hear again N --speakers` or `--as call`. |
| A better screen: clearer visuals, real controls, and no waiting. | No. Output is plain lines. |
| Works like Granola: sits through a meeting and writes it up. | Partly. It hears the microphone only, and does not start by itself. |
| Works like Wispr Flow: speak anywhere and the words land where the cursor is. | No. There is no hotkey and no paste. |
| Clanky in Slack can use it for calls. | No. Nothing calls it yet. |

### The layering rule

The local meeting app and Clanky's call feature are layers on top of the `lm` suite. They are not separate builds.

- Anything either of them needs is added to `lm hear` first, behind `--json` and a stable run folder.
- The layer on top holds only what is its own: a window, a hotkey, a Slack message.
- If a layer needs logic the suite lacks, the suite grows. The layer does not carry its own copy.

### Order of work

| Step | What | Why here |
|---|---|---|
| 1, done | History, show and re-run for `lm hear`, and its rows in `lm timeline`. Every run keeps its raw audio. | Everything later reads past runs. Re-run needs the audio. |
| 2 | Voices in live notes, and fewer split speakers on long calls. | The transcript is the product. |
| 3 | The live screen: a list-and-preview layout, running text, key controls. | Needs steps 1 and 2 to have something to show. |
| 4 | A hotkey, and paste at the cursor. | The Wispr Flow half. Needs the owner's choice of key. |
| 5 | The other side of a call, and starting by itself. | The Granola half. Needs a system-audio device on this Mac. |
| 6 | Clanky. | A thin caller over what steps 1 to 5 built. |

Latency is a rule for every step, not a step of its own. Keep the speech model loaded during a live session, and print text as soon as a sentence ends.

## Where this goes next

The order matters, because each step is only worth building once the one before it has been measured on real audio.

| Step | What it is | Why it comes here |
|---|---|---|
| 1. Your voice | 20 short clips in your own voice: commands, notes, names, code terms, a noisy room. Score `lm hear` and `lm hear intent` on them. | Every number in this doc except the real call is from synthetic voices. |
| 2. A hotkey | `lm hear live` exists. A key that starts it from anywhere is the missing piece. | Needs your call on which key and where the result goes. |
| 3. Acting on the result | A table from kind and target to a handler. | Only worth wiring once step 1 says the classifier is right. |
| 4. Screen share in calls | Sample a frame when the picture changes and read it with `see`. | Lets a digest say what was on screen when something was said. |
| 5. The other side of a call | `lm hear live --notes` hears the microphone only. Hearing the call itself needs a system-audio device. | A setup step of its own, and your decision. |

Handlers for step 3, each showing what it is about to do before doing it:

- an agent command goes to a Claude session over claude-ipc
- a note is appended to a notes file
- an app action becomes a shortcut or an AppleScript

For step 5, mlx-audio already ships streaming models: `voxtral_realtime`, a streaming VibeVoice build and streaming Sortformer.

## What the first real call showed

A 41-minute onboarding call with several people, recorded from a video meeting, run on 2026-11-12.

| Measure | Result |
|---|---|
| Time to transcribe with speakers | 12 minutes, in 5 windows, 16 GB grant never exceeded |
| Words | 6,710 in 386 turns; speech covers 92% of the recording |
| Agreement between the three transcribers | 92 to 93% pairwise; word counts within 1% |
| What they disagree on | fillers ("um"), number formats, domain terms ("ACES and PIES" heard as "Asus and PIs") |
| Speakers | the two main voices kept one label each for the whole call (28 of 41 minutes) |
| Digest | 20 points; the ones checked against the transcript held; one cited time was a second off |

Two weaknesses came out of it:

- **Minor speakers fragment.** People who spoke little got a new label in each window: 8 unmatched labels, 11 in all. Matching by the shared minute only works for someone who talks during it. Fewer, longer windows or a voice-print match would fix this.
- **The digest is thin for a long call.** One pass over 45,000 characters gives about 20 points. Notes per ten minutes, then a digest of the notes, would keep more.

Domain terms are the cheap win: pass them with `--context "ACES, PIES, OE number"`.

## Limits to keep in mind

- **English only, by choice.** The owner ruled on 2026-11-12 that nothing else is needed. Speech in another language stays in the raw recording, or is written out in Latin letters. No second language will be tested.
- **Crosstalk is untested.** The scripted call has clean turns. People talking over each other is uncommon and is version 2 work.
- **Speaker labels are numbers.** That is enough for now. A name appears in a digest only when the transcript shows who it belongs to.
- **Long calls are slow.** A call over about two hours takes roughly a quarter of its length and has not been run.

## Version 2, as ruled by the owner

| Item | What it means |
|---|---|
| Crosstalk | Handle two people talking at once, and test it. |
| Known voices | Save a label for a recognised voice and reuse it on a later call when the match is confident. Below that confidence, fall back to a number. |
