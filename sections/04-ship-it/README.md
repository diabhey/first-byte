# Section 4: Ship it

## Goal

Wire production observability, then deploy the agent to LiveKit Cloud Agents with a single command. By the end of this section your agent runs on the public internet against LiveKit's global network and infrastructure.

## Step 1: Wire production metrics (Exercise 7)

Open [`agent_start.py`](./agent_start.py). The §3 grounded agent is in place; the three event handlers and shutdown callback are your TODOs. Implement them inside `entrypoint()`, then run:

```bash
uv run python sections/04-ship-it/agent_start.py dev
```

The finished reference is in [`agent.py`](./agent.py). Connect via the [Agents Playground](https://agents-playground.livekit.io) and have a conversation. Watch your terminal:

- **`[metrics] turn e2e_latency=...`** logs fire once per assistant turn, sourced from `ChatMessage.metrics` on the `conversation_item_added` event. STT first byte, LLM time-to-first-token, TTS first audio chunk, and end-to-end are all here. This is your latency budget audit in real time.
- **`[usage] ...`** logs fire whenever `session_usage_updated` ticks, and once more on shutdown via `add_shutdown_callback` for the final cumulative tally. Tokens in/out per provider and audio durations.

```python
@session.on("conversation_item_added")
def _on_item(ev: ConversationItemAddedEvent) -> None:
    if not isinstance(ev.item, ChatMessage):
        return
    m = ev.item.metrics
    if not m:
        return
    e2e = m.get("e2e_latency")
    if ev.item.role == "assistant" and e2e is not None:
        print(f"[metrics] turn e2e_latency={e2e:.3f}s metrics={m}")

@session.on("session_usage_updated")
def _on_usage(ev: SessionUsageUpdatedEvent) -> None:
    for usage in ev.usage.model_usage:
        print(f"[usage] {usage.provider}/{usage.model}: {usage}")

ctx.add_shutdown_callback(_log_session_summary)
```

> Earlier versions of `livekit-agents` exposed a session-level `metrics_collected` event for this. That event is deprecated. The current pattern is `conversation_item_added` for per-turn latency and `session_usage_updated` for usage rollup.

## Step 2: Deploy

```bash
cd sections/04-ship-it
lk agent create
```

`lk agent create` builds a container image, registers it as a LiveKit Cloud Agent worker, and starts dispatching it to rooms in your project.

After deploy:

1. Open [cloud.livekit.io](https://cloud.livekit.io) and find your new agent.
2. Set environment variables in the agent's settings: `MOSS_PROJECT_ID`, `MOSS_PROJECT_KEY`, `MOSS_INDEX_NAME`. (The LiveKit and OpenAI/Deepgram/Cartesia credentials are handled by LiveKit Inference automatically.)
3. Note the agent ID. `lk agent create` writes it to a new `livekit.toml` in this directory. That file is gitignored; copy `livekit.toml.example` as a reference for the shape.

For redeploys, `lk agent deploy` reads `livekit.toml` and rolls a new container without touching dashboard secrets.

That's it. No Kubernetes manifest, no SSL cert wrangling.

### What's pre-staged

This directory ships as a self-contained deployable Python project so `lk agent create` works without surprises:

- `agent.py` / `agent_start.py` — the worker.
- `pyproject.toml` + `uv.lock` — pinned deps. Section-local, intentionally separate from the repo-root `pyproject.toml` (which is for the course's dev environment).
- `Dockerfile` — uses `python:3.13-slim-trixie` (glibc 2.38) with `uv` from astral's image. The default `lk agent create` Dockerfile uses Bookworm (glibc 2.36), which silently fails to install `inferedge-moss-core` because the wheel is `manylinux_2_38_x86_64`. Pre-staging Trixie avoids that 5-minute live debug.
- `.dockerignore` — keeps `.env`, `.git`, editor files, and coding-agent dotfiles out of the build context.
- `livekit.toml.example` — template for the auto-generated `livekit.toml`.

## Step 3: Talk to your deployed agent from a local orb page

The Agents Playground is fine for poking the worker, but the course ships a small visitor-facing front end you can run locally to feel what production looks like. It's at the repo root in [`../../orb/`](../../orb/).

```bash
cd ../../orb
cp config.template.js config.js
```

Edit `config.js` and fill in three values:

- `URL`: your LiveKit Cloud `wss://...livekit.cloud` (same one in your `.env`)
- `TOKEN`: a 24h LiveKit access token for room `heartbyte-orb`:
  ```bash
  lk token create --room heartbyte-orb --identity orb-visitor --valid-for 24h
  ```
- `ROOM`: leave as `heartbyte-orb` (default)

Then serve the page:

```bash
python3 -m http.server 8000
```

Open <http://localhost:8000> → tap the orb → grant the mic → ask "What is HeartByte?" Your browser connects over WebRTC to your LiveKit Cloud project; LiveKit dispatches your deployed worker to the room; the agent does STT → Moss retrieval → LLM → TTS and the reply streams back. The orb's color and state indicator track listening → thinking → speaking. Tap the orb during a live session to disconnect.

That's the full architecture in three pieces: static webpage (front end), LiveKit Cloud (signaling + dispatch), your agent worker (the brain). All three meet at the room name in your token. The agent you just deployed runs the same KB as [heartbyte.io](https://heartbyte.io) — you are literally talking to the production HeartByte orb running on your own LiveKit project.

When you ship this for real visitors, you replace the hard-coded token in `config.js` with a server-side token endpoint that mints per-visitor tokens — see Going further below.

## Going further

- **Custom visitor-facing frontend** — three concrete pieces you'll need, with the patterns I run in production:

  1. **Token endpoint.** Mint short-lived LiveKit JWTs server-side so the secret never reaches the browser. A Cloudflare Pages Function at `/api/token` is the lightest option: ~80 lines of JS, no npm deps, signs the JWT with the Web Crypto API (`crypto.subtle.sign` is native to the Workers runtime). Set `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` / `LIVEKIT_URL` as Pages env vars (`wrangler pages secret put`) and your endpoint returns `{ url, token, room }` per request. 15-minute TTL on the token.

  2. **Browser client.** Drop in the [LiveKit JS SDK](https://docs.livekit.io/reference/client-sdk-js/) (`livekit-client` via CDN, no build pipeline needed) and an audio-reactive UI. The agent dispatch happens whenever a room is created, so the orb just calls `room.connect(url, token)`. For the orb itself: a state machine (`idle → connecting → listening → thinking → speaking → error`) wired to LiveKit's `ActiveSpeakersChanged` event, plus a Web Audio `AnalyserNode` reading volume from both the local mic and the remote agent track. Per-frame `getByteFrequencyData()` into a normalized volume drives a canvas / Three.js animation. A `setTimeout` fallback covers the "user stopped, agent hasn't started" thinking state.

  3. **Three security layers, in order of effort.** A public talk-to-me endpoint is wide open by default. Add them as soon as you have real visitors:
     - **Origin / Sec-Fetch-Site check** inside the Pages Function. Reject anything without `Sec-Fetch-Site: same-origin` or a whitelisted `Origin`. Stops `curl` from anywhere.
     - **Per-visitor unique rooms.** Instead of one shared room name, generate `<prefix>-<uuid>` per token. A bot in their own room can't disrupt a real visitor in another room. LiveKit Cloud Agents auto-dispatch one worker per new room, no agent code change.
     - **Cloudflare WAF rate limiting.** Dashboard rule on `/api/token`: e.g. 10 req/min/IP → 429. Stops mass token harvesting before the Pages Function even runs.

  Once these are in place, `lk agent deploy` (the update equivalent of `lk agent create`) lets you ship new agent code without rebuilding the front end or rotating secrets. Same architecture I shipped at [heartbyte.io](https://heartbyte.io) — three repos (static site on CF Pages, Python agent on LiveKit Cloud, Moss for retrieval) meeting at the LiveKit project.
- **Telephony**: `lk sip` to wire a phone number. Buy a DID via LiveKit Phone Numbers in the Cloud dashboard, set up a dispatch rule, your agent picks up real calls. See [docs.livekit.io/sip](https://docs.livekit.io/sip/).
- **Vision**: Gemini Live and OpenAI's realtime models support video input. Pass a video track and ask the agent what it sees.
- **Avatars**: Tavus and Anam render a photorealistic talking head. Plug in via the avatar plugins.
- **Self-host**: if compliance requires it, run LiveKit Server yourself with the [self-hosting guide](https://docs.livekit.io/home/self-hosting/).

## Concepts introduced

- `conversation_item_added` event + `ChatMessage.metrics` for per-turn latency observability
- `session_usage_updated` event + `session.usage` for cumulative model-usage rollup
- `ctx.add_shutdown_callback` for end-of-session reporting
- `lk agent create` for one-command deploy to LiveKit Cloud Agents
- The pattern: observability before deploy, not after
