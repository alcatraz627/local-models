# LM follow-up: implementation and trial results

This records the work authorized after the [behavior audit](20260926-lm-followup-audit.md). The CLI fixes are in the working tree. The model trials are evidence for narrower decisions, not model replacements.

## CLI behavior now exercised

| Job | Change | Exercise | Limit |
|---|---|---|---|
| Describe a table | `q describe-data` profiles CSV, TSV, JSON, and XLSX before optional model prose. It reports rows, missing values, distinct source values, types, numeric extrema, and workbook sheets. | The September 27 contract passed eight cases, including 3,000 rows, malformed input, padded IDs, mixed JSON types, invalid dates, and multi-sheet discovery. A separate 100,000-row CSV returned exact counts and extrema in 130 ms of profiler time. A live `--prose` call kept model wording separate from exact facts. | Model prose is labeled unverified. XLSX requires an explicit sheet when a workbook has multiple sheets. Large files are still loaded in memory; the 100,000-row check does not establish a safe upper bound. |
| Inspect input | `q --preflight --json` reports format, sheet, extracted size, estimated tokens, active context cap, and truncation. | The table contract exercised an input that would exceed the model context and listed two sheets without calling the converter. | Token count is an estimate. A multi-sheet workbook needs `--sheet` before size can be measured. |
| Judge a batch | `lm fleet sample`, `verdict`, and `audit` separate envelope, judge, and human checks. Verdicts bind to result, source, and index-row hashes. New run records use absolute source paths. | A one-item offline deterministic profile run received a human verdict. A later test from another working directory accepted a source, then marked the verdict stale after that source changed. | Older verdicts with only a result hash become stale until reviewed again. A human verdict is a recorded decision, not an automatic quality score. |
| Find a command | `lm help <job>` gives colored short task routes; `lm examples` contains the new table, batch, retrieval, and benchmark commands. | All 13 help routes returned successfully without ANSI when piped; a TTY check showed color. | Examples still need inputs from the caller's project. |
| Compare performance | `lm bench quick` runs a fixed table, short-answer, and visual-evidence workload. | The earlier two repeats passed all three cases, with medians of 56 ms, 181 ms, and 589 ms. The September 27 review found that two cases checked only `ok:true`; their fixtures now check answer text and measured visual evidence. A fresh host run passed 3/3 with 50 ms, 260 ms, and 650 ms wall times, and wrong-content mutations fail. | The earlier pass count was an envelope result for two cases. Peak RSS is the command process, not Ollama. Resident models are recorded, but this does not force a cold start. |
| Retrieve chunks | `lm rag` derives vector dimensions from the actual embedding and stages index rebuilds before replacement. | A ten-query comparison ran with independent indexes. | Ten repository queries do not qualify a new default for personal documents. |

`bash scripts/verify.sh` returned `42 checks passed, 0 failed` after the September 27 review fixes. It includes the new benchmark and RAG contract, eight table cases, and 53 deterministic image-comparison assertions. It does not exercise a full live `ui-verify` gate or generated image quality.

## Retrieval trial

The saved result is `/private/tmp/lm-retrieval-trial-20260926/report.json`. The expected answer-bearing heading appeared in the top five for 6/10 queries with `nomic-embed-text` and 7/10 with `qwen3-embedding:0.6b`. Qwen missed one heading Nomic found. Index times were 2,627 ms and 6,402 ms; median query times were 360.5 ms and 640.5 ms. Database sizes were 3.3 MB and 4.4 MB.

The replacement gate remains a held-out set of personal-document questions with at least ten percentage points more top-five answer-bearing recall and no material increase in unsupported citations. The small trial gives no reason to replace the default today. Exact names and paths should still use `rg` first.

## Speech trial

A Mac-only MLX trial used `mlx-community/Qwen3-ASR-0.6B-bf16`. A first run used an empty generated WAV and returned an empty transcript; inspecting its frame count identified the fixture error. A nonempty 4.2565-second synthetic command then produced: “Pause the video on The Raspberry Pi. Then send the playback status to my phone.” Loading took 618 ms, transcription 1,868 ms, and peak RSS was about 1.76 GB. The 8-bit community conversion failed to load in this environment due to a weight-layout mismatch, so it is not the tested runtime.

This is a feasibility smoke check. The adoption gate remains 20 owner-spoken clips with word error rate, proper-noun errors, and downstream command success compared with the existing route. Keep speech recognition on the Mac until that gate is met; no Pi speech runtime was installed.

## Raspberry Pi and phone contract

The live Pi had 3,791 MiB RAM, 2,856 MiB available, 46 GB disk free, no Node installation, and active `csync-agent`, `csync-assist`, and `csync-media` services. `vcgencmd get_throttled` returned `0x50005`: current undervoltage and throttling, plus historical flags. A second read on September 26 still returned `0x50005` with 2,849 MiB available and 46 GB free. A Pi latency or media-interference trial under that state would measure the power fault. Repair power and repeat the status check before installing whisper.cpp or SmolVLM2.

The existing assistant accepts authenticated chat on port 8791 and rejects a non-Gemini provider today (`/Users/alcatraz627/Code/Claude/csync/assist/main.go:125-155`). The Android client streams `/chat?stream=1` and reads `/capabilities` and `/providers` (`/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MeshClient.java:92-98,292-315`). The mesh peer separately handles trusted-device exchange on port 8790 (`/Users/alcatraz627/Code/Claude/csync/AGENTS.md:10-12`). Any new provider must preserve the chat stream, session, tool-turn, and capability contracts that the phone uses.

### Mac csync capability service plan

Build a Mac peer service as a general capability host. The first registered capability can be `transcribe`; later ones can cover local vision, retrieval, bounded file operations, and agent jobs without changing the transport each time. Its discovery response should state capability name, version, input limits, health, latency class, and privacy class. Requests need a scoped token, request ID, deadline, size cap, and structured result or error. The Pi assistant should treat the Mac as an explicit tool or provider and expose availability through its existing capability response. The Android client should retain the Pi as its chat endpoint.

Use csync's tailnet identity and token rules, with narrower per-capability permission where practical. Store only bounded job metadata by default; media payloads need explicit retention policy. Test Mac sleep, tailnet reconnect, duplicate IDs, cancellation, and service overload against the Pi's current media playback. A silent fallback from local media to Gemini would change privacy expectations, so the fallback must be visible to the owner.

### Pi harness plan

Pi 0.87.1 first ran in `/private/tmp/pi-trial` on the Mac. The tested package is now retained under `/Users/alcatraz627/.local/share/pi-lab` (424 MB), with a launcher at `/Users/alcatraz627/.local/bin/pi-lab`. It uses an isolated agent directory and session store, local Ollama, offline startup, disabled telemetry, a scratch working directory, and read-only tools by default. `pi-lab --version` returned `0.87.1`; a no-tools prompt returned `PI_LAB_READY`, and a saved session appeared in the dedicated session directory. One first read-tool prompt produced unrelated anagram code. A fresh JSON-mode read trial then showed a `read` tool call on the scratch `README.md` and the correct `COBALT-42` sentinel. This variation is a warning about the tiny local model, not proof that Pi tool routing is reliable. The persistent launcher also received successful RPC `state` and `prompt` responses followed by `agent_settled`. The [official RPC contract](https://pi.dev/docs/latest/rpc) makes a small adapter feasible. [Pi's security model](https://pi.dev/docs/latest/security) gives tools the process's OS permissions; a Pi service therefore needs an OS user and tool policy with narrow access before it may act autonomously.

After the Pi's power state is healthy, install Node 22.19+ and the pinned Pi package in an isolated prefix. Keep `csync-assist` as the stable phone API. Pi can run behind it for a named agent mode, with its RPC session ID mapped to the existing chat session, streamed tool events translated into the current NDJSON shape, and explicit scopes for media, file, and remote Mac capabilities. Begin with read and media-control tools. Add writing or command execution only through named, logged actions and the owner's chosen approval policy. Compare a multi-turn local or Gemini job with the current Go assistant before making Pi the default backend. Pi is useful if session continuity, tool composition, and inspectable action history save owner effort that the existing assistant cannot.

## Codex and gcc

Codex-specific adapters now cover `deep-research`, `pyramid-sweep`, `gcc-map`, `improve-skill`, `tag`, `preference-graduation`, `atone`, `affirm`, `gcc-proposal`, `pin-for-dream`, and `i-dream`. The installer reported `56 ok, 0 failed` after selecting Codex adapters for the two existing gcc skill names. The local-model skill keeps Gemini for a broad, low-judgment sweep with a prompt contract and targeted sample check. Ordinary coding stays with Codex or its direct subagents when that is the better lane.

The `tag` and `preference-graduation` adapters now use `gcc canon check|apply` for owner-reviewed global placement. The bridge accepts only authored Markdown homes, pins the manifest and each base file by SHA-256, previews a diff, refuses symlinks and derived files, makes backups, and records the Codex session. Apply is deliberately excluded from the writable outbox and needs filesystem escalation after the owner reviews the exact manifest. Three behavior tests covered apply, stale bases, changed manifests, traversal, symlinks, and derived-file refusal. `gcc canon check` also ran against an unchanged real rule. A sandboxed apply returned `Operation not permitted` without queueing; a forged outbox apply received exit 126. No actual owner-approved tag or preference placement was available to exercise a live canonical write; that acceptance remains open.

The `pin` bridge now adds the Codex session ID and current directory and accepts `--file` and `--framing` as normal CLI arguments. Pin `pin-20260926124155-ab` was queued, applied, and inspected; it retained the session, directory, and manifest line range. JSON-only pin fields still require stdin, which the queued bridge does not carry. The normal evidence fields now work without that path.

## i-dream integration

The registered `codex-sessions` manifest pointed at a missing `extract-events.sh`. A wrapper was installed and the source and registered manifests were synchronized. The extractor self-test passed. The extractor now reads delegated `<task>` prompts while skipping injected environment blocks. A live extraction produced 198 session events with unique IDs; 154 had a usable first prompt. `i-dream domain list --json` showed 127 new Codex events pending the next dream pass. A repeated extract saw new sessions and one existing event gain a handback; IDs remained stable.

Codex SessionStart now reads the same atone and optional dream guidance as Claude. The first substantive Codex prompt uses Claude's shared query-ranked dream hook when the owner's `.inject-on` flag is enabled. With that flag absent, the existing atone reminder remains. Synthetic hook payloads with `INJECT_DREAM=1 INJECT_TEST=1` produced atone guidance, a digest, session-ranked lessons, and prompt-ranked lessons. A second prompt for the same session emitted no repeated lesson. The hook scripts passed `bash -n` and the adapter install's behavior canaries. A live future Codex start with the opt-in flag enabled and a completed dream pass is still needed to observe the whole path.

No full `i-dream dream-pass` was run: the CLI would consume pending deltas from nine domains at once, with no per-domain selector. A low-budget pass would advance all cursors on thin analysis. A useful i-dream improvement is a scoped dry-run and per-domain pass so a new integration can be tested without consuming unrelated work. The Codex domain also needs an explicit return-channel decision: record grounded graduation candidates with event IDs, then route only owner-reviewed changes into gcc canon.

## Next checks

1. Fix Pi undervoltage, then measure whisper.cpp tiny/base on 30 owner-spoken commands and SmolVLM2 on ten real Pi camera questions while media is active. Keep the current services running during the trial.
2. Record 20 owner-spoken Mac clips for ASR and a held-out personal-document retrieval set. Apply the efficacy thresholds from the audit before changing defaults.
3. Build the Mac capability host and a Pi client behind the existing csync phone API in a coordinated csync worktree. Exercise sleep, reconnect, payload limits, and media isolation before deployment.
4. Exercise `tag` and `preference-graduation` on real owner-selected candidate records through the new bridge, then verify a fresh Codex session discovers the adapters and reads the resulting guidance.
5. Add a scoped i-dream pass, run it for `codex-sessions`, inspect the produced insight against event IDs, and verify the Codex prompt injection with the owner's opt-in enabled.
