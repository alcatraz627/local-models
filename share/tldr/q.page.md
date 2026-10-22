# q

> Quick local LLM companion: answers, shell commands, commit messages, file Q&A.
> More information: `man q` or `lm --capabilities`.

- Terse answer:

`q "how do I check disk usage"`

- One macOS command, checked against its --help:

`q cmd "kill everything on port 3001"`

- Commit message from the diff:

`git diff | q commit`

- PDF, Word and the like extracted locally:

`q summarize --file report.pdf`

- The heavier model, on demand:

`q --big "reason through this tradeoff"`

- List the available intents:

`q intents`

- Your latest call, in full:

`q show -1`

