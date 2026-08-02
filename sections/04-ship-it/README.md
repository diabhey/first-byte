# Section 4: Ship it

## Goal

**Observe the grounded agent locally, deploy the same worker, then call it from a browser.**

## 1. Observe a real session

Complete the [root setup and pre-flight check](../../README.md#pre-class-setup), and build the Moss index in [Section 3](../03-grounding-moss/README.md), before running this worker.

Stop any earlier worker and run:

```bash
uv run python sections/04-ship-it/agent.py dev
```

Connect through [Agents Playground](https://agents-playground.livekit.io), ask two or three HeartByte questions, then inspect the terminal.

```text
[metrics] STT  audio=...
[metrics] EOU  delay=... transcription=...
[metrics] LLM  ttft=... prompt=... completion=...
[metrics] TTS  ttfb=... audio=... chars=...
[latency] perceived=... response=COMPLETE preemptive=on | ...
[usage]   session summary: ...
```

## Key takeaway
>
> “Observability comes before deployment. `perceived` tells us the user’s wait; the individual stages tell us where that wait came from.”

- **`perceived`** is LiveKit’s speech-end → first-server-audio measurement.
- **EOU, STT, retrieval, LLM TTFT, and TTS TTFB** diagnose the stages behind it.
- Do **not** add the stage durations: they can overlap.
- `[usage]` is emitted on disconnect or shutdown. It rolls up LLM tokens, STT/TTS audio duration, and TTS characters with `metrics.UsageCollector`.
- An interrupted answer is marked `CANCELLED`; an answer cancelled before first audio has no first-audio latency.

> **Important:** this is a breakdown, not a pass/fail score. Compare repeatable runs and find the dominant stage before tuning.

The agent carries forward semantic end-of-turn detection, tuned barge-in, preemptive generation, and Moss grounding. Those settings are production configuration—re-test them against real visitor audio.

## 2. Deploy

Stop the local worker, authenticate once, then create the Cloud agent:

```bash
lk cloud auth
cd sections/04-ship-it
lk agent create --secrets-file=../../.env
```

The command builds the worker and injects the `MOSS_*` values from `.env`; LiveKit supplies the project credentials. Then:

1. Run `lk agent secrets` to verify secret names.
2. Confirm the agent becomes healthy in [LiveKit Cloud](https://cloud.livekit.io).
3. Keep the generated `livekit.toml`; later releases use:

   ```bash
   lk agent deploy
   ```

This directory is self-contained for deployment: its `pyproject.toml` and lockfile pin the validated dependencies, and its Dockerfile uses Debian Trixie so the Moss native wheel can install.

## 3. Call the deployed agent from the orb

```bash
cd ../../orb
cp config.template.js config.js
```

Set `URL` to the Cloud `wss://...livekit.cloud` address and generate a short-lived room token:

```bash
lk token create --join --room heartbyte-orb --identity orb-visitor --valid-for 1h
```

Paste it into `TOKEN`, then serve the page:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Open [http://localhost:8000](http://localhost:8000), tap the orb, grant microphone access, and ask “What is HeartByte?”

```text
browser ── WebRTC ──> LiveKit Cloud ── dispatch ──> deployed worker
```

> **Production rule:** `config.js` is only for local testing. A public page needs a server-side endpoint that mints short-lived, per-visitor tokens; never expose API secrets or a long-lived token in the browser.

## Concepts

- Per-turn metrics via `metrics_collected`.
- Session rollup via `metrics.UsageCollector` and `ctx.add_shutdown_callback`.
- One-command deployment with `lk agent create`.
- **Observe first, then deploy.**
