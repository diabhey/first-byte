# Orb — visitor-facing companion to the agent

A minimal single-page voice client that visitors talk to. Pairs with the
deployed agent from `sections/04-ship-it/`. Same `LIVEKIT_URL`, same room,
two halves meeting at LiveKit Cloud:

```
browser <── WebRTC ──>  LiveKit Cloud  ── dispatch ──>  agent worker
(orb)                   room "heartbyte-orb"          (your deployed agent)
```

You'll run this locally during class to test against the agent you've just
deployed on LiveKit Cloud in Section 5. It's the same architecture that's
live on heartbyte.io, simplified for course use.

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
  lk token create \
    --room heartbyte-orb \
    --identity orb-visitor \
    --valid-for 24h
  ```

  Paste the printed `eyJ...` string.

- `ROOM`: leave as `heartbyte-orb` (must match what your agent dispatches
  to, which it does by default).

`config.js` is gitignored — never commit your token.

## Step 2 — serve the page

Any static server works. Easiest:

```bash
python3 -m http.server 8000
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
- `config.template.js` — the three values you need to fill in. Copy to
  `config.js` to use it.
- `.gitignore` — keeps `config.js` out of version control.

## Going further (out of scope for the in-class exercise)

The token-in-config.js pattern is fine for local testing but not for a
public website — anyone holding the token can join the room and your
secret has to ship to the browser when you generate it. Three things you
add for production, in increasing effort:

1. **Token endpoint.** Move the token-minting server-side. The lightest
   option is a Cloudflare Pages Function (~80 lines, no npm deps, signs
   with the Web Crypto API). The orb fetches `/api/token` on tap and the
   secret lives in Pages env vars, not in the browser.
2. **Per-visitor unique rooms.** Have the token endpoint return a
   `heartbyte-orb-<uuid>` room name per visitor so a bad actor in one
   room can't disrupt other visitors. LiveKit Cloud Agents auto-dispatch
   one worker job per new room.
3. **Edge rate limiting.** A Cloudflare WAF rule on the token endpoint
   (e.g., 10 requests per IP per minute → 429) blocks mass token
   harvesting before your Function runs.

The full reference implementation of all three layers is open source at
<https://github.com/heartbyte-io/homepage>.
