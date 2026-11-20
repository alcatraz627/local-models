---
reader: the owner, deciding how far the lm commands should follow the z- tool standard
---

# The lm commands and the z- tool standard, 2026-11-20

The z- tools follow one written standard, and a test enforces it. The lm commands follow their own, older conventions.

This report does three things:

- measures the gap between the two;
- names one place where they already collide;
- recommends what to align.

Nothing has been changed yet except where marked.

## Recommendation

Keep the names. Adopt the standard's visible rules on the five commands that are on PATH, and fix the two places where the registries disagree. Do not rename `lm` to a z- name and do not merge the two shared libraries.

| Step | What | Size | Why |
|---|---|---|---|
| 1 | Stop `zcmd tldr-sync` writing through a link it does not own. | one line in zcmd | It overwrites this repo's help pages today. See "The collision". |
| 2 | Correct three manifest rows: `see`, `lm`, and a missing `review`. | three lines in zcmd's manifest | `zcmd kit` describes `see` as a mail viewer. |
| 3 | Make `-h`, `--help` and `help` print the same text on all five commands, starting `name: purpose`. | small, in `bin/_lib.sh` and each command | Three of five fail this, and two of them treat `help` as input. |
| 4 | Add `-V` and an `examples` command to `q`, `see`, `warm` and `review`. | small | `q examples` is sent to the model as a question today. |
| 5 | Section titles in bold white, and `lm examples` cut to 50 lines with sections. | small | Both were already on this project's open list. |
| 6 | Add the five commands to the family test, so the rules stay kept. | one change in zcmd's test | A rule nothing checks drifts. |

Steps 1 and 2 are in another repo (`~/Code/Claude/its-my-config`). Steps 3 to 5 are here. Step 6 follows 3 to 5.

## What the standard is

It lives at `~/Code/Claude/its-my-config/shell/zcmd/docs/STANDARD.md`. `tests/standard.test.sh` checks it for every tool in zcmd's manifest: 230 checks, all passing on 2026-11-20. In short:

- Help answers `-h`, `--help` and `help` with the same text. It starts `name: purpose`, fits 40 lines, and points at `<tool> examples`.
- Fourteen flags mean one thing in every tool (`-n` is a count, `-q` is quiet, `-o` is an output file, `--json`, `--dry-run`, and so on).
- Data goes to stdout and everything else to stderr. Exit 0 is success, 1 a failure, 2 a typing mistake.
- A general tool is named `z` plus a plain word. State lives under `~/.local/state/zcmd/`.
- Shared code is `lib/z.sh`, a toolbox each tool takes pieces from.

## Measured: the five commands against the standard

Each cell is what the command did when run on 2026-11-20.

| Check | `lm` | `q` | `see` | `warm` | `review` |
|---|---|---|---|---|---|
| `-h`, `--help`, `help` all exit 0 | yes | yes | no, `help` exits 12 | yes | no, `help` exits 1 |
| The three print the same text | no, `help` is a different page | yes | no | yes | no |
| First line is `name: purpose` | no, uses a dash | no | no | no | no |
| Help fits 40 lines | 24 | 20 | 20 | 14 | 24 |
| Plain when piped | yes | yes | yes | yes | yes |
| Unknown flag exits 2 | yes | yes | yes | yes | yes |
| `-V` prints name and version | yes | no, exits 2 | no, exits 2 | no, exits 2 | no, exits 2 |
| `examples` command, at most 50 lines | 105 lines | no, sent to the model | no, read as an image path | no, unknown verb | no, read as a path |
| Help points at `examples` | no | no | no | no | no |

Not measured by running: section title colour (the code sets yellow at `bin/_lib.sh:90`, and the standard asks for bold white), and each reserved flag's meaning across every lm subcommand. One known clash: `lm imagine -q` is quantization, and `-q` is reserved for quiet.

## What lm has that the standard does not

These are worth keeping, and two are worth offering to the z- tools.

| lm has | The standard has |
|---|---|
| One table, `lib/verbs.toml`, that generates every help screen, the man pages, shell completion, tldr pages and the capability list, with a drift check. | Help written by hand in each tool. tldr pages generated from the manifest. |
| `--capabilities`, for people and as JSON, across the whole suite. | `--capabilities` on zconvert only, in its own shape. |
| Exit codes 10 to 13 for server down, model missing, input missing and timeout. | 0, 1 and 2. lm's codes are a superset and do not conflict. |
| A JSON error with a stable `code` to branch on. | `--json` is reserved, with no error shape defined. |
| A history file per tool, which other tools read. | Nothing on history. |

## The collision

zcmd's help-page sync overwrites help pages that this repo generates.

How it happens:

1. `zcmd tldr-sync` writes one page per command into tldr's custom pages folder (`zcmd:445`).
2. For `lm`, `q`, `see` and `warm`, the files in that folder are links into this repo's `share/tldr/`. They were put there so tldr shows this repo's pages.
3. The sync writes through each link and replaces the generated page with a three-line stub.

What it cost: on 2026-11-20 at about 02:50 the `lm`, `q` and `warm` pages were overwritten. The drift check here failed 6 of 669 until the pages were regenerated.

It will happen again on the next `zcmd tldr-sync` or `zcmd add`.

The fix: the sync skips a page that is a link, because a link means another project owns it. This repo has restored its pages. zcmd is not yet changed.

## Where the registries disagree

zcmd's manifest lists the lm commands as outside tools. Three rows are wrong:

| Row | Says | Should say |
|---|---|---|
| `see` | kind `cli`, "an alias of run-mailcap" | kind `ext`, source `~/Code/local-models/bin/see`, "Read an image into text with a local vision model" |
| `lm` | "Local-model chat / inference CLI" | "Local models on this Mac: answers, images, speech, documents" |
| `review` | missing, so `zcmd doctor` reports it unregistered | kind `ext`, source `~/Code/local-models/bin/review` |

## What not to align, and why

- **Names.** The standard names a general tool `z` plus a word. `lm` is the front door of a suite, and the owner's ruling is that new tools are reached through `lm`, not added to PATH. Renaming would break every script and habit for no gain in function.
- **State location.** The standard keeps state out of synced repos. The lm histories live in `logs/` and `outputs/` here, are not committed, and are the interface other tools read. Moving them is a large change with no present problem behind it.
- **One shared library.** `bin/_lib.sh` and `lib/z.sh` both gate colour and print help. Sharing one file would tie this repo to another repo's path. The family test is the cheaper way to keep them matching.
- **Environment names.** `LM_*` is consistent inside the suite and matches the standard's pattern in spirit.

## Open question for the owner

Should `q`, `see`, `warm` and `review` stay on PATH at all?

- The owner's ruling scopes new tools under `lm`, and each of the four already has an `lm` form.
- Keeping them means four more commands to hold to the standard.
- Removing them means retraining habits and updating every caller.

This report assumes they stay.

## Sources

| Fact | From |
|---|---|
| The standard | `~/Code/Claude/its-my-config/shell/zcmd/docs/STANDARD.md` |
| 230 checks passing | `bash tests/standard.test.sh` in zcmd, run 2026-11-20 |
| The measured table | each command run with `-h`, `--help`, `help`, `-V`, `examples` and an unknown flag, 2026-11-20 |
| The collision | `zcmd` line 445; `ls -l` of tldr's custom pages folder; `git diff share/tldr` before regeneration |
| Manifest rows | `manifest.tsv` in zcmd; `zcmd doctor` |
| Yellow titles | `bin/_lib.sh:90` |
| Scoped-under-lm ruling | owner, 2026-11-12 |
