# Course orb — optional browser companion to the agent

A minimal single-page voice client for the course demo. It pairs with a **deployed** agent from `sections/04-ship-it/` using the same `LIVEKIT_URL` and room.

```text
browser <── WebRTC ──>  LiveKit Cloud  ── dispatch ──>  agent worker
(orb)                   room "heartbyte-orb"          (your deployed agent)
```

The orb is an optional private-deployment rehearsal after the local course flow works. It is not part of the low-memory classroom path: use `lk agent console` for that. The orb adds a browser, WebGL, Web Audio, and a second network client, so do not run it alongside a local worker or a Cloud build while screen sharing on a constrained laptop.

There is no pre-existing deployed course agent. Complete the local checks first, then create a private deployment before using this page. If you are not testing a deployment, skip the orb.

## Step 1 — fill in `config.js`

```bash
cd orb/
cp config.template.js config.js
```

Select the same course project in the CLI before creating the token (`lk project set-default "<your-course-project-name>"`). Stop local dev workers when testing the Cloud deployment, so automatic dispatch reaches the deployed worker.

Then edit `config.js`:

- `URL`: your LiveKit Cloud project's `wss://...livekit.cloud` URL. Same one you used in `.env` for the agent. Grab it with:

  ```bash
  grep LIVEKIT_URL ../.env
  ```

- `TOKEN`: a short-lived access token for the orb's room. Generate one locally with the LiveKit CLI you installed in the course prep:

  ```bash
  lk token create --join \
    --room heartbyte-orb \
    --identity orb-visitor \
    --valid-for 1h
  ```

  Paste the printed `eyJ...` string into `TOKEN`. The token expires after one hour; create another for the next rehearsal. Use a new room name and visitor identity for an independent test or another visitor.

`config.js` is gitignored — never commit your token.

## Step 2 — serve the page

Any static server works. Easiest:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open <http://localhost:8000>.

### Low-power display

For a constrained laptop, open <http://localhost:8000/?low-power=1>. This uses fewer geometry segments, limits the WebGL pixel ratio, turns off antialiasing, and redraws only when the window or connection state changes. Voice transport still works, but the orb no longer pulses with the audio level.

The page selects this static mode automatically when the browser reports the operating system's **Reduce motion** preference. Close other local workers and avoid starting a Docker or Cloud build during this rehearsal.

## Step 3 — tap and talk

Tap the orb, grant microphone permission, and ask “Who is Abhimanyu Selvan?” Your voice goes over WebRTC to your LiveKit Cloud project. LiveKit dispatches the course agent to room `heartbyte-orb`, and the agent runs STT → Moss retrieval → LLM → TTS before streaming its reply back. The orb’s color and state indicator use active-speaker activity to suggest listening, thinking, and speaking. These are visual cues, not proof of the worker’s internal state. A Build-plan worker that has scaled to zero can take noticeably longer to join on the first connection; that startup wait is separate from per-turn voice latency.

Tap the orb again during a live session to disconnect cleanly. The page disposes the one-use room, local microphone track, attached remote audio, analyser nodes, and audio context before a retry. Confirm that the microphone indicator turns off, then reconnect. Missing configuration and connection errors should show the setup/error message; inspect the browser console and token expiry if a connection fails.

This starter uses automatic dispatch from the unnamed course `AgentServer`. If you customize the worker with an explicit dispatch name, the browser token or a server-side dispatch request must target that name. Check the Cloud agent status and logs before assuming a connected room has an agent.

## What's in here

- `index.html` — the orb page. Three.js sphere with a small shader, a state machine (idle / connecting / listening / thinking / speaking / error) wired to the pinned LiveKit JS client 2.24.0 `ActiveSpeakersChanged` event, and an audio analyser tap on the local mic and the remote agent track for the rim glow reactivity. `?low-power=1` switches to state-change-only rendering.
- `config.template.js` — the two values you need to fill in. Copy to `config.js` to use it.
- `.gitignore` — keeps `config.js` out of version control.

## Going further (out of scope for the in-class exercise)

The token-in-config.js pattern is fine for local testing but not for a public website. Mint short-lived tokens server-side, use a unique room per visitor, and rate-limit the token endpoint.
