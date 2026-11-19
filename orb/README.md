# Orb

[← Ship It](../sections/04-ship-it/README.md) · [Course README](../README.md) · Next: [Inspect the call →](../sections/04-ship-it/README.md#4-inspect-the-call)

A one-page voice client for the agent you deployed in [Ship It](../sections/04-ship-it/README.md). The page and the agent meet in the same LiveKit Cloud room:

```text
browser <── WebRTC ──>  LiveKit Cloud  ── dispatch ──>  agent worker
(orb)                   room "heartbyte-orb"          (your deployed agent)
```

## 1. Fill in `config.js`

```bash
cd orb
cp config.template.js config.js
```

Quit any local console first, so the call reaches the deployed agent. Use the same project as the deploy.

In `config.js`:

- `URL` is your `wss://...livekit.cloud` address. It is `LIVEKIT_URL` in `../.env`.
- `TOKEN` is a short-lived room token:

  ```bash
  lk token create --join \
    --room heartbyte-orb \
    --identity orb-visitor \
    --valid-for 1h
  ```

  Paste the `eyJ...` string. It expires in an hour.

`config.js` is gitignored. Never commit a token.

## 2. Serve the page

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Open <http://localhost:8000>.

## 3. Tap and talk

Tap the orb, allow the microphone, and ask “What is HeartByte?” Tap again to hang up, then go back to Ship It and [inspect the call](../sections/04-ship-it/README.md#4-inspect-the-call).

The colours follow who is speaking. They hint at listening, thinking, and speaking; they are not the agent's real state. If nothing answers, check the token's expiry, the browser console, and `lk agent status`.

## Files

- [`index.html`](./index.html): the orb, its state machine, and the LiveKit JS client 2.23.0.
- [`config.template.js`](./config.template.js): the two values to fill in.

## For a public site

A token in `config.js` is only for local testing. A public page needs a server that mints a short-lived token per visitor, a room per visitor, and a rate limit on that endpoint.
