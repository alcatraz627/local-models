# Mac capability peer for the Pi assistant

## Current route

The phone sends chat to the Pi assistant at `/chat?stream=1` on port 8791
([Android client](/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MeshClient.java:92)).
The Pi assistant currently dispatches only Gemini chat
([assistant](/Users/alcatraz627/Code/Claude/csync/assist/main.go:125)); its
`/capabilities` response lists declared tools, not live backends
([assistant](/Users/alcatraz627/Code/Claude/csync/assist/main.go:106)). The
Pi camera tool calls the existing media service and returns a media URL
([camera tool](/Users/alcatraz627/Code/Claude/csync/assist/tools_extra.go:62)).

The mesh peer on port 8790 has `/whoami`, `/peers`, and `/send`
([mesh server](/Users/alcatraz627/Code/Claude/csync/agent/server.go:69)).
`/send` writes incoming bytes into the inbox and may copy text to the Mac
clipboard and raise a notification. It has no request deadline, size limit,
or capability result. Do not use it for inference calls. The Mac mesh peer
already binds to its Tailscale IP and checks the shared mesh token for
protected endpoints ([mesh server](/Users/alcatraz627/Code/Claude/csync/agent/server.go:58)).

## Proposed first useful route

Use `speech.transcribe` only after the Mac ASR gate passes on owner-spoken
clips. The Pi has a camera and media service, so `image.describe` is the next
candidate after a Pi-camera image gate. A transport with only `ping` or
generic shell execution would not add a useful owner action. The first user
flow should be: ask the Pi assistant to transcribe an owned audio clip; it
fetches the file from its media area, sends bounded bytes to the Mac peer,
receives transcript plus model/version/latency, and returns it through the
existing chat stream. The phone keeps the Pi as its chat endpoint.

The Mac peer is a capability host, not an LM-specific service. Add a typed
`GET /v1/capabilities` and `POST /v1/invoke/<name>` to the existing mesh
agent. A capability record names the operation, version, input MIME and byte
limit, timeout, health, privacy class, and whether it is currently available.
The invocation carries a request ID and deadline. The response returns the
same ID, structured result or error, actual model/version if used, and
elapsed time. Keep an allowlist of registered operations. Never dispatch an
arbitrary command string from the network.

## Trust and failure behavior

The current shared mesh token is sufficient to preserve existing peer auth,
but invocation needs a narrower capability token before any write or agent
action is exposed. Body limits apply before reading bytes. Limit concurrent
model jobs so a Pi request cannot exhaust Mac memory or collide with an
interactive local-model session. A duplicate request ID must return the
previous result or a clear in-progress state without starting a second job.
The Pi client uses a deadline shorter than the phone chat deadline and
reports `mac-asleep`, `capability-unavailable`, `too-large`, and
`model-failed` distinctly. It must not silently send a private clip or
image to Gemini after Mac failure.

Mac capabilities remain separate from the Pi media service on 8792. A camera
photo is captured once by that service; the Pi assistant sends a copy to the
Mac if the owner asks for analysis. The Mac peer does not start a competing
Pi camera process. A sleeping Mac is absent from live capability discovery,
not advertised as ready because the model is installed.

## Acceptance sequence

1. Qualify ASR on held-out owner speech: short/long clips, background noise,
   accents and names, with manual word-error and task-usefulness review.
   Compare Mac latency and output with the current practical alternative.
   Keep the storage quota under 150 GB steady and 200 GB hard.
2. Add a Mac handler and Pi client with fake deterministic transcription,
   then exercise auth, byte limits, duplicate IDs, timeout, Mac sleep, tailnet
   reconnect, and concurrent requests. The response must appear through the
   unchanged `/chat?stream=1` NDJSON path on the phone.
3. Register the qualified Mac ASR implementation and repeat the route with a
   real clip. Verify the version and transcript shown on the phone match the
   Mac result. Keep Gemini chat available as its own explicit choice.
4. Repeat the efficacy and transport tests for `image.describe` using real
   Pi-camera stills before adding that capability. Then consider retrieval or
   bounded owned-device actions using the same transport and their own
   acceptance gates.

`go test ./...` currently passes for the Pi assistant. The mesh agent has no
test files; its baseline command exits successfully. Neither result tests a
new capability route. No csync or Android implementation was changed for
this plan.
