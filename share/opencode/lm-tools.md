# Local model tools on this Mac

You are running on a local model. This Mac also has models you cannot be, for images, speech and very large documents. Reach them by running `lm` in the shell. Each call loads its model, answers and unloads it.

| Need | Command |
|---|---|
| Text or an answer from an image or screenshot | `lm read <image> ["question"]` |
| What changed between two images | `lm diff A B` |
| A question about one file (PDF, Word, spreadsheet, text) | `lm doc <file> ["question"]` |
| Speech in a recording as text | `lm hear <recording> --json` |
| A second opinion from a stronger local model | `q --big "question"` |
| A document too large for your context, or web research | `lm gemini "question" --file <file>` (this sends the file off the Mac; ask the user first) |
| The command for anything else | `lm how "what I want"` |

Rules:

- Add `--json` when you will parse the answer. Exit code 0 means the call worked; `lm help <name>` explains the rest.
- Do not run `lm imagine` from a coding session. It needs about 44 GB and the model you are running on is already loaded.
- A tool's answer is evidence, not fact. Check anything you will act on against the file itself.
