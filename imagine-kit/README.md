# Imagine Kit

Make images from a written prompt, and rework images you already have: change one, combine up to four, or mark an area and change only that. It runs in your browser. Where the drawing happens depends on your computer, and the next section tells you which case is yours.

![The app: a source image, an instruction, and the result](docs/app.jpg)

## Which computer can do what

Find your computer in this table first. It decides how you set up.

| Your computer | Can it draw by itself? | Speed for one image | What to do |
|---|---|---|---|
| Mac, M-series chip, 24 GB memory or more | Yes | 10 to 30 seconds | Follow "Mac" below |
| Mac, M-series chip, 16 GB memory | Yes, with a lighter copy of the model | Slower; not yet measured | Follow "Mac" below |
| Linux or Windows, NVIDIA card with 20 GB or more | Yes | Not yet measured | Follow "Linux" or "Windows" below |
| Linux or Windows, NVIDIA card with 12 to 19 GB | Yes, with a lighter copy of the model | 90 to 150 seconds | Follow "Linux" or "Windows" below |
| Linux or Windows, NVIDIA card under 12 GB | No | | Use a cloud model, or another machine |
| No NVIDIA card, or an Intel Mac | No | | Use a cloud model, or another machine |

Three things to know when reading it:

- **The graphics card's own memory is what counts** on Linux and Windows, not the computer's memory. An RTX 3050 has 8 GB (some have 6), so it falls in the "under 12 GB" row even in a computer with 16 GB of memory.
- **"Cannot draw by itself" is not the end.** The app still installs and works. You pick a model that runs at Google or OpenAI with your own key, or you point the app at a friend's machine that can draw. Both are covered below.
- **Why 12 GB.** On a 16 GB card, the lightest copy of the model needed 7 GB to draw a new image and 9 to 13 GB to rework one. The kit refuses below 12 GB so it never starts a download it cannot use.

## Set it up

### Get the kit

```bash
git clone https://github.com/alcatraz627/local-models
cd local-models/imagine-kit
```

### Mac

You need an M-series chip (M1 or newer), 16 GB of memory or more, and about 20 GB of free disk.

```bash
./install.sh
./imagine
```

The installer builds a private environment in this folder, installs the image engine, and asks before downloading the 16 GB model. If it says Python 3.12 was not found, run `brew install uv` and then `./install.sh` again.

### Linux

You need Python 3 and, to draw on this computer, an NVIDIA card with 12 GB or more and its driver installed (`nvidia-smi` should print the card).

```bash
sudo apt install python3 python3-venv git
./install.sh
./imagine download klein
./imagine
```

The installer looks at the card. With 12 GB or more it installs the engine, which is a download of about 5 GB, and the model is another 16 GB. With a smaller card or none, it skips both and tells you to use a cloud model or another machine.

### Windows

The kit runs inside WSL, which is Windows' own way of running Linux. This path is written but has not been tried on a real Windows computer yet, so tell us what happens.

1. Open PowerShell as administrator and run `wsl --install`. Restart when it asks, then choose a user name and password for Ubuntu.
2. Open "Ubuntu" from the Start menu. Everything below is typed there.
3. Install what the kit needs, get it, and set it up:

```bash
sudo apt update
sudo apt install -y python3 python3-venv git
git clone https://github.com/alcatraz627/local-models
cd local-models/imagine-kit
./install.sh
./imagine
```

4. The last command prints an address such as `http://127.0.0.1:7717/`. Open it in your normal Windows browser. If the browser does not open by itself, copy the address in.

If your NVIDIA card has 12 GB or more, install NVIDIA's current Windows driver first. WSL uses it, and `nvidia-smi` typed in Ubuntu should then print the card.

### Check the setup

```bash
./imagine doctor
```

It says what this computer is, whether it can draw by itself, and how to fix anything missing.

## If your computer cannot draw by itself

You have two ways to make images. Both use the same app.

### Use a model that runs at Google or OpenAI

At the top right of the app, pick **Gemini image** or **GPT image**. The first time, the app shows three steps and a box:

1. Open the company's key page from the link in the app, and sign in.
2. Create a key and copy it.
3. Paste it into the box and press **Save key**.

Things to know:

- The company charges your account for each image, usually a few cents. Google's key page may ask you to turn on billing before image models work.
- Your prompt and your source images are sent to that company to be drawn. The app says so under the Make image button whenever such a model is chosen.
- The key is kept on your computer only, in `data/keys.json`.

### Draw on someone else's machine

A friend with a capable Mac can offer it to you. They run `lm net serve` and approve your computer once. You then run:

```bash
./imagine server add NAME ADDRESS
```

A **Runs on** choice appears at the top of the app. Pick their machine, and your prompt and source images are sent there to be drawn. Both computers have to be able to reach each other, for example on the same home network or through Tailscale.

## Make an image

Leave the terminal window open while you use the app, and press Ctrl-C there to stop.

1. Write what you want to see.
2. Press **Make image**. Set **Tries** to get up to four attempts at once.
3. The image appears on the right. Requests wait in a list under the button, and each can be stopped.

Each idea is a **thread**, listed on the left. A thread keeps every image made on the way, so you can go back to an earlier one. **New thread** starts a fresh idea, and **Rename** gives a thread a name.

## Rework images you already have

Drop one to four images into **Source images**, or paste one, then write an instruction. Images you added before can be picked again from the list under the box.

| You want | Do this |
|---|---|
| To change one thing in a photo | One source image. "Make the jacket red. Keep the face, the pose and the background the same." |
| To put a subject into a scene | Two source images. "Put the cat from the second image beside the bicycle in the first image." |
| A new picture loosely based on one | One source image, then choose **Start loosely** and describe the whole picture. |

Say what must stay the same. The model changes less when you tell it what to keep.

## Get from a first try to the image you wanted

| Control | What it does | Use it when |
|---|---|---|
| **Try again** | The same request, with a different random start. | The idea is right and this attempt is not. |
| **3 more tries** | Three more attempts to pick from. | You want a choice. |
| **Mark an area** | Drag a box on the image. Your change is kept to that area. | One part is wrong and the rest is right. |
| **Change it** | Reworks the image on screen as you describe. | It is close: "warmer light", "remove the sign". |
| **Same start, new words** | Keeps the starting point and adds your words to the prompt. | A small nudge. |
| **Compare** | Switches between the image and the one it was made from. | You want to see what changed. |
| **Check** | Measures how much of the image changed. No model is involved. | You want proof the rest stayed the same. |
| **Use as source** | Puts the image in the source box. | You want to combine it with another image. |
| **Star** and **Delete** | Mark a keeper, or remove an image after a second press. | Deleted files move to `data/trash`. |

Notes on marking an area:

- It works on any image: the newest, an earlier one in the thread, or a source image. Click a thumbnail beside "Made from" to open a source.
- Everything outside the area is left exactly as it was. The model only sees the piece around your box.
- For the same reason, an effect that should spread past the box, such as a glow, stops at its edge. Mark a larger area for those.

Change one thing at a time. Two changes in one instruction often means neither lands.

**Improve my prompt** rewrites a short idea as a fuller prompt, which you can edit or undo. If the Ollama app is running on your computer it uses a model from there. Without it, the kit uses a simple built-in template.

How to write prompts that work is in [PROMPTING.md](PROMPTING.md).

## The models

| Model | Runs | Good at | Needs |
|---|---|---|---|
| FLUX.2 klein 4B (default) | On your computer | Fast images, and reworking source images | A 16 GB download; see the first table |
| Qwen-Image | On a Mac | Readable text inside an image, such as a sign | A 50 GB download and 64 GB of memory |
| Gemini image | At Google | Reworking, and following instructions closely | A Google key |
| GPT image | At OpenAI | Not yet run through this kit | An OpenAI key |

Qwen-Image cannot rework source images. It can only start loosely from one. On Linux and Windows, "Start loosely" is not available yet and reworks instead.

## From the terminal

Everything the app does is also a command.

```bash
./imagine gen "a red bicycle in the rain"
./imagine gen "make the jacket red" --from photo.jpg
./imagine gen "put the cup on the desk" --from cup.png --from desk.png
./imagine gen "make it night" --from photo.jpg --model gemini
./imagine rework 12 "warmer light"
./imagine again 12
./imagine history
./imagine models
./imagine help
```

## Where your images are

| Path | Holds |
|---|---|
| `data/images/` | Every image the kit made, each with a details file beside it. |
| `data/sources/` | A copy of each source image you used. |
| `data/history.jsonl` | One line per image, with the prompt and every setting. |
| `data/trash/` | Images you deleted. |
| `data/keys.json` | Keys you saved for Google or OpenAI. |

Local models are kept in `~/.cache/huggingface`, shared with any other tool that uses the same ones.

## When something goes wrong

| What you see | Cause | What to do |
|---|---|---|
| "cannot run on this computer" | The graphics card is too small, or there is none. | Pick Gemini image or GPT image, or draw on another machine. |
| "needs a key from" | A cloud model is chosen and has no key yet. | Follow the three steps the app shows. |
| "did not accept the key" | The key is wrong, or billing is off for that account. | Make a new key, and check billing on the company's site. |
| "The image engine is not installed" | Setup has not run, or did not finish. | Run `./install.sh`. |
| "is not downloaded yet" | The model is missing or half downloaded. | Press the download button, or run `./imagine download klein`. |
| "stopped before it finished, most likely for memory" | The computer ran short of memory. | Close other large apps. Use a smaller size under **Size, steps and seed**. |
| "The kit is not running" | The terminal window was closed. | Run `./imagine` again and reload the page. |
| "waiting for approval" | The other machine's owner has not approved your computer. | Ask them to run the command the message shows. |
| The result ignores your source image | The instruction describes a whole new picture. | Say what to change and what to keep. |
| Text in the image is garbled | The default model is weak at lettering. | Use Qwen-Image or a cloud model, and put the words in quotes. |

## What it is built on

- [mflux](https://github.com/filipstrand/mflux) runs the image models on Apple Silicon, and [diffusers](https://github.com/huggingface/diffusers) runs them on NVIDIA cards.
- FLUX.2 klein 4B is by Black Forest Labs and Qwen-Image is by Alibaba. Both are released under the Apache 2.0 licence. Each model's own page states its terms of use.
- The kit is one Python file, `kit.py`, one page, `app.html`, and a small engine file for NVIDIA cards. `tests/test_kit.py` checks it without loading a model.

## What has been tested

Tested on 2026-11-20.

| Setup | Result |
|---|---|
| Mac, M5 Pro, 64 GB | Fresh install, new image 11 s, rework 19 s, two-image combine 30 s, marked-area change 18 s |
| Linux, Ubuntu 24.04, NVIDIA card with 16 GB | Fresh install, new image 93 s, rework 150 s, two-image combine 120 s |
| Gemini image, from the Mac | A rework in 6 s |
| Drawing on another machine | Worked with one Mac talking to itself; not yet between two computers |

Not yet tried: any Windows computer, a 16 GB Mac, an NVIDIA card with 20 GB or more, the model download on Linux, and GPT image.
