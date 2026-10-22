# see

> Read an image into text with a local vision model (the image never leaves this Mac).
> More information: `man see` or `lm --capabilities`.

- Exact text is read first, then the model:

`see ~/Desktop/shot.png "what is the build id?"`

- Straight from the clipboard:

`see paste "what does the error say?"`

- Your newest screenshot:

`see latest`

- The exact text, no model, about a second:

`see shot.png --ocr`

- A sectioned inventory of a website or app UI:

`see dashboard.png --ui`

- Only the red objects:

`see count squares.png --color red`

- The measured evidence only, no model:

`see diff a.png b.png --no-read --json`

