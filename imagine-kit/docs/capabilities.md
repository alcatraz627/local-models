---
reader: agent
---

# What the studio can do today

A list of every surface the kit has, so a rebuild can be checked against it. A row leaves this list only with the owner's say-so. Each row names the check that would catch its loss.

## The page

| Surface | What a person can do | Check |
|---|---|---|
| Model picker | A button beside the main button names the model and where it draws; its panel lists every model with its state | screen check, shots 01, 10 and 12 |
| Help button | Read one paragraph on how the page works | screen check, shot 01 |
| Theme button | Switch light and dark; the choice is remembered | screen check, shots 01 and 02 |
| Setup notice | See that the engine is missing, the model is too large, or the model needs a download, with a download button | screen check, shots 10 and 11 |
| Source box | Add up to four images by drop, paste or file choice; remove one | `test_upload_then_generate_then_the_image_is_in_history` |
| Rework or start loosely | Choose how sources are used; a slider sets how much of the source to keep | `test_a_loose_start_uses_strength_not_the_edit_program` |
| Prompt box | Write a prompt; Cmd or Ctrl plus Enter makes the image | screen check, shot 03 |
| Improve my prompt | Rewrite a short idea as a fuller prompt, by a local model or a template | `test_the_template_keeps_the_idea_and_says_who_wrote_it` |
| Style picker | Add one of seven styles; hidden while reworking | `test_a_rework_instruction_gets_no_style_sentence`, shot 06b |
| Size, steps and seed | Set width, height, steps and seed, or leave them automatic | `test_a_prompt_alone_is_a_new_image` |
| Make image and Stop | Start a render and stop one in progress | screen check, shot 07 |
| Progress line | See loading, the step count, download progress, elapsed time | screen check, shot 07 |
| Failure notice | See what went wrong and what to do | screen check, shots 08 and 09 |
| Result stage | See the chosen image large | screen check, shot 03 |
| Result details | See number, model, how it was made, size, steps, seed, time, prompt and source thumbnails | screen check, shot 03 |
| Try again | Repeat the request with a new seed | `test_again_keeps_the_request_and_changes_the_seed` |
| Use as source | Put the image in the source box | screen check, shot 06b |
| Star | Mark and unmark an image | `test_star_flips_and_delete_removes` |
| Save | Download the image file | screen check, shot 03 |
| Delete | Remove an image after a second press to confirm; files go to the trash folder | `test_delete_takes_the_details_file_to_trash_with_the_image` |
| Change it | Rework the shown image from one line of text | `test_rework_uses_the_past_image_as_the_source` |
| Shelf | See every past image, newest first, numbered, with stars; choose one | screen check, shot 03 |
| Narrow and tablet layouts | Use the page at 390 and 820 wide with no sideways scroll | screen check, measure rows |
| Open with a source | `?from=N` opens with image N in the source box | screen check, shot 06b |

## Added in the rebuild

| Surface | What a person can do | Check |
|---|---|---|
| Threads rail | Each thread's newest image down the left; open one; start one. Names: hover, header, and beside the picture under 860 wide | `test_a_follow_up_stays_in_its_images_thread_and_a_new_request_starts_one`, shot 06d |
| Thread name | Rename the open thread | `test_a_thread_can_be_named`, shot 06d |
| Delete a thread | Delete the open thread and all its images; the second press names how many | `test_deleting_a_thread_removes_its_images_and_no_others` |
| Thread strip | See only the open thread's images, oldest first | shot 06d |
| Runs on | Choose which computer draws; shown when another machine is known | net-contract render test, shots 12 to 14 |
| Tries | Ask for one to four tries of a request at once | shot 07b |
| Queue | See each waiting and running request, with progress, and stop any one | `test_requests_wait_in_line_and_each_finishes`, shot 07b |
| Images you added before | Pick an earlier upload as a source | shot 06b |
| Draft kept | The prompt, style and sources survive a reload | none yet |
| Undo for Improve | Get your own words back | none yet |
| Mark an area | Drag a box on any image and keep a change to it | `test_a_change_to_a_marked_area_leaves_every_other_pixel_alone`, shots 06d and 06i |
| Open a source | Show a source image on the stage, to mark or change it | shot 06g |
| Compare | Switch between an image and the one it was made from | shot 06f |
| Check | Measure how much changed from the source, inside and outside a marked area | the marked-area test |
| 3 more tries | Three more tries of the same request | shot 06d |
| Same start, new words | Keep the seed and starting point and add to the prompt | `test_refine_keeps_the_seed_and_adds_to_the_prompt` |

Changed on purpose: a second request used to be refused as busy. It now waits in the queue, up to twelve.

## Changed in the move to one writing box

The page has one writing box. A line above it says what the words are about, and its button is named for what it will do. No surface above was removed; these rows say where each one now lives. "Walk" is `tests/ui_walk.js`, run in a browser against the stand-in engine.

| Surface | Where it is now | Check |
|---|---|---|
| Prompt box and Change it | One box with two mode buttons above it (see "The writing box" below) | walk: "the box is now about the image on screen", "a change made one new image from the open one" |
| Source box | "Add a photo" opens a panel with the file chooser and earlier uploads; a file can also be dropped or pasted anywhere on the page | walk: "a click outside an open panel closes it"; drop and paste have no check |
| Size, steps and seed | A panel above its button, offered for a new image only | walk: "size, steps and seed reach the image" |
| Try again, Mark an area, Compare, Star, Save | A row of icons at the top right of the canvas, each named in its tooltip | walk rows of the same names |
| 3 more tries, Same start new words, Check, Use as source, Delete | In the More menu at the end of that row | walk: check, delete and use as source rows |
| Same start, new words | Now has a button (More menu). It turns the box into "The same start as image N" | none yet |
| Result details | Top left of the canvas; opens into the full list and stays open | walk: "an opened section stays open after another press" |
| Requests in progress and a failure | Cards in the strip at the foot (see "The foot strip" below) | `tests/ui_landing.js` "a drag held across a landing is kept whole"; screen check shots 07 and 09 |
| Stop | Takes two presses: the second reads "Confirm stop" | walk: "one press on stop cancels nothing and asks again" |
| Where the image is drawn | On the model button, with the full sentence in its tooltip, for every model: this computer, another computer, or the company a cloud model runs at | screen check, shots 03, 10b and 12 |
| Text size and theme | One View menu in the header; the choices are remembered | screen check, shots 06n to 06q; walk measures at five widths |
| Words after a failed render | Put back in the box when the request they were sent with fails | walk: "the words stay in the box after a refusal" |
| Mark an area on a source | The box reads "The marked area of a source of image N", and the result starts from that source | walk: "the change to a source starts from that source and joins the thread" |

### The writing box

With an image open, two buttons sit above the box:

- "About image N": the words change the open image. The main button reads "Change image N".
- "New image": the words make a new image. The main button reads "Make image".

The box has two rows. The first holds the two mode buttons, any source images, and at its right end Add an image, Improve my words and Options. The second holds the words, the model button and the main button.

| Text size | Image height on a 1440 by 800 window | With two source images in the box |
|---|---|---|
| Small | 467 px | 436 px |
| Medium | 429 px | 398 px |
| Large | 387 px | 355 px |

`tests/ui_room.js` fails any row under 350 px. Enlarging the source thumbnails by 12 px turns its last row red.

### Result details

The words that made the image sit at the top left of the canvas. Under them, "Image N · how · seconds" opens into the full list.

### The foot strip

The thread's images come first, then one card per request in progress, then a failure if there is one.

- Each card is one tile high. The request's words are in its tooltip.
- A render starting or ending never moves or covers the image.

## The command line

| Command | What it does | Check |
|---|---|---|
| `app` | Start the page; `--port`, `--no-open` | `test_the_page_is_served` |
| `gen` | One image; `--from`, `--loose`, `--model`, `--style`, `--size`, `--steps`, `--seed`, `--json` | `test_gen_prints_the_file_and_json_gives_the_record` |
| `again`, `refine`, `rework` | Follow-ups on a past image | the three follow-up tests |
| `improve` | Print a fuller prompt; `--edit` | the two prompt tests |
| `history`, `models`, `download`, `doctor` | List images, list models, fetch a model, check the install | `test_an_unknown_command_exits_2` covers the dispatcher only |
| `help`, `-h`, `--help`, `-V` | Help three ways and the version | `test_help_three_ways_is_the_same_and_starts_with_the_name` |

## Behaviour that must hold

| Behaviour | Check |
|---|---|
| A half-downloaded model is refused before anything loads | `test_a_missing_model_is_refused_before_anything_runs` |
| One image at a time; further requests wait in line, up to twelve | `test_the_line_has_a_limit` |
| A change to a marked area leaves every pixel outside its cut-out untouched | `test_a_change_to_a_marked_area_leaves_every_other_pixel_alone` |
| Only the machine's own page may ask for work | `test_a_request_from_another_host_name_is_refused` |
| A request cannot read outside the image folders | `test_a_request_cannot_read_outside_the_image_folder` |
| Every image has a details file beside it holding its full record | `test_a_render_keeps_its_details_in_a_file_beside_the_image` |
| On this Mac a new image takes about 11 s, a rework 19 s, a two-source combine 32 s, with nothing else running | real renders, run by hand after each engine change |
| Render time follows machine load, not the page. The page and the command line send the same request for a combine (klein, 4 steps, 1024 by 1024, 8-bit, two sources) | 2026-11-21 through the page: 37 s. 2026-11-23 through `gen --from A --from B` at load average 16: 47 and 49 s |
| A finished render never moves the reader (see "Landing rule" below) | `tests/ui_landing.js`, 16 rows; seven planted breakages each turn their rows red |
| A thread deleted while it draws does not come back | `test_a_thread_deleted_while_it_draws_does_not_come_back`, red before the fix |
| Deleting a thread leaves nothing of it on the page or in the box; its delete disarms when the reader moves away | `tests/ui_panels.js`, red before the fix |
| One panel or menu is open at a time, and Escape hands focus back to the button that opened it | `tests/ui_panels.js`, red before the fix |
| The words in the box keep 240 px or more at 880, 960 and 1024 wide with large text | `tests/ui_panels.js`, red before the fix |
| A failure in the foot strip is one tile high and does not move the image | `tests/ui_panels.js`, red before the fix |
| The model button, the View panel, the text sizes and thread delete work when pressed with a real mouse | `tests/ui_panels.js`, 18 rows in all |

### Landing rule

When a render finishes, these stay put:

- the open thread and the image on the stage
- what the box is about, and a marked area
- a drag, and a thread name being typed
- an open More menu, a Check result, and Compare

The image the reader was waiting for, or one from another thread, shows as "Image N is ready" with Show it.

The test uses real mouse and keyboard input. The seven planted breakages were: always follow, rebuild the title while renaming, rebuild the stage while dragging, and removing each of rename, More, Check and Compare from the rule.

## Not covered by any check

These have no check:

- `history`, `models`, `download` and `doctor` output.
- Undo for Improve, the Same start button, and dropping or pasting a file.
- Covering: no script measures whether something lies over the image. That was checked by reading screenshots on 2026-11-21.

The walk and `tests/ui_landing.js` need a browser driver (the Playwright MCP) and are not part of `tests/test_kit.py`.

Both themes were read with 8 real renders (portrait, landscape, square) on 2026-11-21. No real render has yet been run through the page itself.
