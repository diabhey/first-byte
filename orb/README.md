# Orb — visitor-facing companion to the agent

A minimal single-page voice client that visitors talk to. Pairs with the
deployed agent from `sections/04-ship-it/`. Same `LIVEKIT_URL`, same room,
two halves meeting at LiveKit Cloud:

```text
browser <── WebRTC ──>  LiveKit Cloud  ── dispatch ──>  agent worker
(orb)                   room "heartbyte-orb"          (your deployed agent)
```

You'll run this locally during class to test against the agent you've just
deployed on LiveKit Cloud in Section 5.

## Step 1 — fill in `config.js`

```bash
cd orb/
cp config.template.js config.js
```

Then edit `config.js`:

- `URL`: your LiveKit Cloud project's `wss://...livekit.cloud` URL. Same
  one you used in `.env` for the agent. Grab it with:

  ```bash
  grep LIVEKIT_URL ../.env
  ```

- `TOKEN`: a short-lived access token for the orb's room. Generate one
  locally with the LiveKit CLI you installed in the course prep:

  ```bash
  lk token create --join \
    --room heartbyte-orb \
    --identity orb-visitor \
    --valid-for 1h
  ```

  Paste the printed `eyJ...` string.

`config.js` is gitignored — never commit your token.

## Step 2 — serve the page

Any static server works. Easiest:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open <http://localhost:8000>.

## Step 3 — tap and talk

Tap the orb, grant the mic permission, ask "What is HeartByte?" Your
voice goes over WebRTC to your LiveKit Cloud project; LiveKit dispatches
your agent worker to room `heartbyte-orb`; the agent does STT → Moss
retrieval → LLM → TTS and the response streams back. The orb's color and
state indicator should track listening → thinking → speaking.

Tap the orb again during a live session to disconnect cleanly.

## What's in here

- `index.html` — the orb page. Three.js sphere with a small shader, a
  state machine (idle / connecting / listening / thinking / speaking /
  error) wired to LiveKit's `ActiveSpeakersChanged` event, and an audio
  analyser tap on the local mic and the remote agent track for the rim
  glow reactivity.
- `config.template.js` — the two values you need to fill in. Copy to
  `config.js` to use it.
- `.gitignore` — keeps `config.js` out of version control.

## Going further (out of scope for the in-class exercise)

The token-in-config.js pattern is fine for local testing but not for a
public website. Mint short-lived tokens server-side, use a unique room per
visitor, and rate-limit the token endpoint.
