# Course Section 5: Ship it

Directory 4 of 4: `04-ship-it`.

## Goal

**Observe the grounded agent locally, deploy the same worker, then call it from a browser.**

## 1. Observe a real session

Complete the [root setup and pre-flight check](../../README.md#pre-class-setup), and build the Moss index in [course Section 4](../03-grounding-moss/README.md), before running this worker.

Quit any earlier console with `q`, then run:

```bash
lk agent console sections/04-ship-it/agent.py
```

Talk in the terminal. Ask two or three HeartByte questions out loud, then read the pipeline box and the usage lines. A typed turn does not run `on_user_turn_completed`, so the box will not show a Moss note.

If this directory already contains a `livekit.toml` from an earlier deploy, the console reads `sections/04-ship-it/.env.local` and does not walk up to the repo-root `.env`. Copy the `LIVEKIT_*` and `MOSS_*` lines into that file. It is gitignored. A key saved earlier in the CLI can be rejected; this file is the one the command uses.

```text
END OF TURN (+ transcript …)          … ms
LLM FIRST TOKEN                       … ms
    └ handoff to TTS                      … ms
TTS FIRST BYTE                        … ms
    └ handoffs between clocks (+ moss …)  … ms
[usage] cumulative: ...
[usage] session summary: ...
```

## Key takeaway
>
> “Observability comes before deployment. The measured pause is the wait after you stop speaking, and the rows above it show where that wait came from.”

- The measured pause is LiveKit’s speech-end to first-audio-frame clock from `ChatMessage.metrics["e2e_latency"]`.
- End of turn already includes the transcript. Moss retrieval is a note on the handoff row. The printed sum adds the stage clocks and the handoff gaps, and that sum matches the measured pause.
- Do **not** add the transcript note or the Moss note on top of those rows.
- `[usage] cumulative` prints on `session_usage_updated`: each event is an updated total, so do not add snapshots together. The shutdown callback prints the final `session.usage` summary with LLM tokens, STT/TTS audio duration, and TTS characters.
- An interrupted answer is marked `Reply cancelled`. An answer cancelled before the first audio frame has no measured pause.

> **Important:** this is a breakdown, not a pass/fail score. Compare repeatable runs and find the dominant stage before tuning.

The agent carries forward semantic end-of-turn detection, tuned barge-in, preemptive generation, and Moss grounding. Those settings are production configuration—re-test them against real visitor audio.

For Exercise 6, trace the active handlers in `agent.py`, inspect several turns, then disconnect and read the final summary. The shipped worker is complete; no separate `agent_start.py` is required.

## 2. Deploy

Quit the console with `q`, authenticate once, then create the Cloud agent:

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
3. Keep the generated `livekit.toml`. The next local console reads credentials from `.env.local` in this directory, so copy the repo-root `LIVEKIT_*` and `MOSS_*` lines there before you run it again. Later releases use:

   ```bash
   lk agent deploy
   ```

This directory is self-contained for deployment: its `pyproject.toml` and lockfile pin the validated dependencies. The Debian Trixie Dockerfile prepares plugin assets and initializes the bundled local audio turn detector during the build, then copies the installed environment into the runtime image. A first Cloud build can exceed the demo slot; rehearse it before class.

If a previous agent was deleted, `lk agent deploy` cannot restore that ID. A sleeping agent still exists, so check before you create another one:

```bash
lk project list
lk project set-default "<your-course-project-name>"
lk agent list
```

If your agent is still listed, inspect it with `lk agent status --id "<existing-agent-id>"` and deploy a new version. If it is gone, move the old `livekit.toml` out of this directory and run `lk agent create` again. Do not reuse the placeholder IDs in `livekit.toml.example`.

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
