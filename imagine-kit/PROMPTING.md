# Writing prompts that work

A short guide for Imagine Kit. Read the first section, try it, and come back for the rest when a result disappoints.

## The one habit

Write sentences, the way you would describe a photo to a friend. These models read prose. A comma list of keywords, the habit from older image tools, gives worse results here.

| Weak | Strong |
|---|---|
| `bicycle, red, wall, rain, 8k, masterpiece, trending` | A red bicycle leaning on a wet brick wall in the early morning. Low sun from the right, puddles on the ground, shot at eye level on a 35mm lens. |

Words like "8k" and "masterpiece" do nothing. Leave them out.

## What to say, in order

Put the important things first. The model weighs the start of a prompt most.

1. **The subject.** Who or what, and what it is doing. "An old fisherman mending a net."
2. **The setting.** Where and when. "On a stone quay at dawn."
3. **The framing.** How close, from where. "A close portrait from slightly below."
4. **The light.** Its direction and quality. "Soft light from a window on the left."
5. **The look.** Photo, painting, illustration. "A watercolour with loose washes."
6. **The mood.** One or two words. "Quiet and cold."

You do not need all six. A prompt of 30 to 70 words is usually enough. The **Style** menu adds the look for you, so leave it out of the prompt when you use the menu.

## Say what you want, not what you do not

The default model ignores "no" and "without". Asking for "no people" can add people.

| In place of | Write |
|---|---|
| no people | an empty street |
| not blurry | sharp focus |
| no extra fingers | a hand with five fingers, clearly visible |

## Reworking a source image

An instruction has three parts. Name all three and the model changes far less than you fear.

1. **What to change.** "Make the jacket red."
2. **Where.** "The jacket on the woman on the left."
3. **What to keep.** "Keep her face, her pose, the background and the light exactly the same."

One change per instruction. For three changes, make three passes with **Change it**, each one starting from the last result.

When you use two or more source images, say which is which by order: "the cat from the second image", "the room in the first image".

## Text inside an image

- Use the Qwen-Image model. The default model cannot draw reliable lettering.
- Put the exact words in double quotes: a shop sign that reads "OPEN".
- Keep it short. One to three words per line works. A paragraph does not.
- Say where the text goes and what it looks like: "white capital letters on a dark green board".

## When the result is wrong

| Problem | Try |
|---|---|
| The idea is right, the image is not | **Try again**. The same request gives a different image each time. |
| It is close | **Change it**, with one small instruction. |
| It ignored part of the prompt | Move that part to the first sentence. Cut everything that matters less. |
| Two subjects merged or doubled | Describe one subject. Add the second in a later pass, from a source image. |
| Hands or faces look wrong | Frame wider so they are smaller, or describe them plainly: "both hands resting on the table". |
| The style is muddy | Name one look. Two styles in one prompt fight each other. |
| It looks plastic or too smooth | Ask for texture: "visible skin texture", "film grain", "rough paper". |
| You liked an image and want small variants | Open **Size, steps and seed**, enter that image's seed, and change only a few words. |

## A way of working

1. Start with one plain sentence and press Make image.
2. Look at what is wrong and fix the biggest thing only.
3. When the composition is right, switch to **Change it** for details.
4. Star the keepers as you go. The history holds every prompt, so nothing is lost.
