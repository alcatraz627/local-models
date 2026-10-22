# warm

> Keep a model loaded so q answers instantly, and say when it unloads.
> More information: `man warm` or `lm --capabilities`.

- Keep the small model loaded for an hour:

`warm on 1h`

- Keep the coding model loaded for a long session:

`warm on code 4h`

- What is loaded and when it unloads:

`warm status`

- The machine view: what is loaded and when each model expires:

`warm status --json`

- Unload the small model and give the memory back:

`warm off`

- Back to zero memory:

`warm off all`

