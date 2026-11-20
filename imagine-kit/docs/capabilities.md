---
reader: agent
---

# What the studio can do today

A list of every surface the kit has, so a rebuild can be checked against it. A row leaves this list only with the owner's say-so. Each row names the check that would catch its loss.

## The page

| Surface | What a person can do | Check |
|---|---|---|
| Model picker | Choose a model; a dot shows whether it is ready | screen check, shots 01 and 10 |
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
| Threads rail | See each idea as a thread with its newest image and a count; open one; start a new one | `test_a_follow_up_stays_in_its_images_thread_and_a_new_request_starts_one`, shot 06d |
| Thread name | Rename the open thread | `test_a_thread_can_be_named`, shot 06d |
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
| On this Mac a new image takes about 11 s, a rework 19 s, a two-source combine 32 s | real renders, run by hand after each engine change |

## Not covered by any check

`refine` has no button on the page. `history`, `models`, `download` and `doctor` have no test of their own output. The light theme with real images has not been read.
