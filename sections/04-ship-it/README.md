# Course Section 5: Ship it

Directory 4 of 4: `04-ship-it`.

## Goal

**Observe the grounded agent locally, deploy the same worker, then call it from a browser.**

## 1. Observe a real session

Complete the [root setup and pre-flight check](../../README.md#pre-class-setup), and build the Moss index in [course Section 4](../03-grounding-moss/README.md), before running this worker.

Stop any earlier worker and run:

```bash
lk agent dev sections/04-ship-it/agent.py
```

Open the CLI’s Agent Console link, or launch [Agent Console](https://docs.livekit.io/testing/agent-console/) from the same project’s dashboard. Select the exact `dev-...` deployment printed by this worker, ask two or three HeartByte questions, then inspect the terminal. The default production target does not route to this dev worker.

```text
[metrics] EOU  delay=...
[metrics] STT  final_transcript=...
[metrics] RAG  hook=...
[metrics] LLM  ttft=...
[metrics] TTS  ttfb=...
[latency] server_e2e=... response=COMPLETE preemptive=on
[usage] cumulative: ...
[usage] session summary: ...
```

## Key takeaway
>
> “Observability comes before deployment. `server_e2e` measures the server portion of the wait; the individual stages tell us where that wait came from.”

- **`server_e2e`** is LiveKit’s speech-end → first-server-audio measurement from `ChatMessage.metrics["e2e_latency"]`. It excludes network delivery and browser playback.
- **EOU, STT, retrieval, LLM TTFT, and TTS TTFB** diagnose the stages behind it.
- Do **not** add the stage durations: they can overlap.
- `[usage] cumulative` prints on `session_usage_updated`: each event is an updated total, so do not add snapshots together. The shutdown callback prints the final `session.usage` summary with LLM tokens, STT/TTS audio duration, and TTS characters.
- An interrupted answer is marked `CANCELLED`; an answer cancelled before first audio has no first-audio latency.

> **Important:** this is a breakdown, not a pass/fail score. Compare repeatable runs and find the dominant stage before tuning.

The agent carries forward semantic end-of-turn detection, tuned barge-in, preemptive generation, and Moss grounding. Those settings are production configuration—re-test them against real visitor audio.

For Exercise 6, trace the active handlers in `agent.py`, inspect several turns, then disconnect and read the final summary. The shipped worker is complete; no separate `agent_start.py` is required.

## 2. Deploy

Stop the local worker, authenticate once, then create the Cloud agent:

```bash
lk cloud auth
lk project list
lk project set-default "<your-course-project-name>"
cd sections/04-ship-it
lk agent create --secrets-file=../../.env
```

The command builds the worker and injects the `MOSS_*` values from `.env`; LiveKit supplies the project credentials. Then:

1. Run `lk agent secrets` to verify secret names.
2. Run `lk agent status` and confirm the agent becomes healthy in [LiveKit Cloud](https://cloud.livekit.io). Use `lk agent logs` to inspect startup and calls.
3. Keep the generated `livekit.toml`; later releases use:

   ```bash
   lk agent deploy
   ```

This directory is self-contained for deployment: its `pyproject.toml` and lockfile pin the validated dependencies. The Debian Trixie Dockerfile prepares plugin assets and initializes the bundled local audio turn detector during the build, then copies the installed environment into the runtime image. A first Cloud build can exceed the demo slot; rehearse it before class.

If you deleted a previous agent, inspect the project and follow [the recovery runbook](../../COURSE_READINESS.md#rebuild-a-deleted-cloud-agent). A stale `livekit.toml` cannot recreate a deleted deployment.

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

- Per-turn metrics via `conversation_item_added` and `ChatMessage.metrics`.
- Cumulative model usage via `session_usage_updated`, final `session.usage`, and `ctx.add_shutdown_callback`.
- One-command deployment with `lk agent create`.
- **Observe first, then deploy.**
