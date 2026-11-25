# Course Section 5: Observe locally, then ship

Directory 4 of 4: `04-ship-it`.

## Goal

Inspect the complete grounded worker locally, explain the first-deployment lifecycle, and leave Cloud creation for a gated rehearsal or post-class lab.

The result is a production-oriented prototype. It still needs product-specific evaluation, security and privacy review, abuse controls, capacity/load work, failure handling, and operations before a public launch.

## Exercise 6: observe one local worker

Complete [root setup](../../README.md#setup), build/inspect the Moss index in [Course Section 4](../03-grounding-moss/README.md), and stop every earlier worker.

```bash
lk agent console sections/04-ship-it/agent.py
```

This runs the worker on the laptop without a browser/room. It is not offline: STT, LLM, and TTS still use LiveKit Inference, and the preloaded Moss index must be available.

Retrieval is enabled in this agent. Speech recognition is biased toward Abhimanyu, Abhi, diabhey, and HeartByte. Ask “Who is Abhimanyu Selvan?” and then “Tell me more about his work.” Check `[moss] searching` to see how the second query includes the previous turn, and `[moss] injected` to confirm context reached the model. Disconnect and inspect the timing and usage logs.

```text
[metrics] EOU  delay=...
[metrics] STT  final_transcript=...
[metrics] RAG  hook=...
[metrics] LLM  ttft=...
[metrics] TTS  ttfb=...
[latency] server_e2e=... response=COMPLETE preemptive=off
[usage] cumulative: ... eot_requests=... interruption_requests=...
[usage] session summary: ...
```

- Final-transcript delay is when STT produces the final transcript; it is not STT first-byte latency.
- `server_e2e` comes from `ChatMessage.metrics["e2e_latency"]` and covers speech end to first server audio. It excludes client delivery/playback.
- EOU, final transcript, retrieval, LLM TTFT, and TTS TTFB diagnose stages. They can overlap, so do not add them.
- `session_usage_updated` reports a cumulative snapshot. Do not add snapshots together.
- `EOTModelUsage.total_requests` and `InterruptionModelUsage.total_requests` expose inference used by turn/interruption decisions.
- The shutdown callback prints final session usage. A greeting has no preceding user turn; cancelled replies need separate interpretation.

The completed grounded worker uses semantic end-of-turn detection, adaptive interruption, `MOSS_MIN_SCORE` filtering, and a fail-fast index load. Preemptive generation is off because the retrieval hook changes turn context on every reply.

Use the [learner worksheet](../../LEARNER_WORKSHEET.md) to identify the dominant observed stage and the next experiment. You can use text mode to check a reply when audio is unavailable.

```bash
lk agent console --text sections/04-ship-it/agent.py
```

Use voice mode for the retrieval and timing exercise. Typed replies in Console can bypass the retrieval hook.

## Instructor walkthrough: deployment lifecycle

There is no assumed existing course deployment. Do not run a Cloud build while presenting. Walk through this first-time sequence from the repository, then perform it after the local gates pass:

```bash
lk cloud auth
lk project list
lk project set-default "<your-course-project-name>"
cd sections/04-ship-it
lk agent create --secrets-file=../../.env
lk agent secrets
lk agent status
lk agent logs
```

`create` performs a remote image build and registers the first agent identity. It injects the `MOSS_*` values; LiveKit supplies its own project credentials. Confirm secret **names**, never display values.

Keep the generated, gitignored `livekit.toml`. After the first successful create, later code versions use:

```bash
lk agent deploy
```

This directory is self-contained. Its lockfile matches the root LiveKit/Moss dependency baseline, and the Dockerfile pins its uv tool image, compiles bytecode, prepares plugin assets, and initializes the local turn model during the build.

A first build can outlast a classroom segment. A Build-plan agent that scaled to zero can also take 10–20 seconds to join its first session. Record worker join/startup separately from per-turn `server_e2e` latency.

For an instructor demo, create and validate the private deployment after local testing, then warm it 15–20 minutes before class. If any Cloud gate is open, demonstrate with local Console and state that deployment remains unverified.

## Optional post-class browser gate

After the private worker is healthy, follow [the orb README](../../orb/README.md) with a fresh, short-lived token from the same LiveKit project. The browser test is optional and separate from the core low-memory flow.

`config.js` is suitable only for local testing. A public page needs server-minted per-visitor tokens, isolated room/identity design, origin protection, rate limits/abuse controls, and monitoring. Never put API secrets or a long-lived reusable token in a browser.

## Optional post-class: inspect a Cloud call

Before you call the deployed agent, open your project's **Settings → Observability** in [LiveKit Cloud](https://cloud.livekit.io) and enable **Agent observability**. Only sessions that start after this are recorded. The transcript and audio upload when the call ends.

Open **Sessions**, pick your call, and select the **Agent insights** tab.

- **Metrics** shows the latency of each turn and what the call used: LLM tokens, STT and TTS audio, and TTS characters. Select the slowest turn and the recording jumps to it.
- **Traces** splits that turn into the same stages as the terminal box: end of turn, STT, LLM, and TTS.
- **Session logs** shows the agent's own lines, including `[moss] injected`.

Then open **Agents** and select your agent. It shows how an average reply splits between stages, across every call.

The dashboard's stage bars overlap in time, so they do not add up to the total the way the terminal box does. Use them to find the biggest stage, and the box to see the exact sum.

## Make it faster

Fix the biggest stage first. Change one setting, make the same calls, and compare. LiveKit's advice is to check the metrics after every change, because some settings do not always help.

### End of turn is the biggest row

- **Lower the minimum wait.** `endpointing.min_delay` defaults to 0.5 seconds. Lower it a little at a time. Too low, and the agent cuts people off.
- **Let it adapt.** `endpointing.mode = "dynamic"` learns how long this caller usually pauses, within `min_delay` and `max_delay`.
- **Keep the turn detector.** It is what lets a low wait stay safe.

```python
turn_handling=TurnHandlingOptions(
    turn_detection=inference.TurnDetector(version="v1-mini"),
    endpointing={"mode": "dynamic", "min_delay": 0.3, "max_delay": 3.0},
)
```

### LLM first token is the biggest row

- **Turn on preemptive generation.** It is off in this agent. With it on, the model starts on a stable transcript before your turn is confirmed.
- **Send a shorter prompt.** A grounded turn adds up to five Moss results. Try `top_k=3`, and watch both `llm_prompt` and the answers.
- **Ask for short replies.** A one- or two-sentence answer reaches its first sentence sooner.

### TTS first byte is the biggest row

- **Start speech early.** `preemptive_generation={"enabled": True, "preemptive_tts": True}` also starts TTS before the turn is confirmed. A cancelled reply wastes the synthesis.

### A handoff is the biggest row

- **Handoff to TTS** is the wait for the model's first full sentence. Tell the agent to open with a short sentence.
- **Deploy near your callers.** An agent runs in the region chosen at `lk agent create --region …`, and you cannot change it later.
- **Keep retrieval in-process.** Moss already searches in the worker, so it adds no network hop.

Sources: LiveKit's [turn-taking tuning guide](https://docs.livekit.io/agents/logic/turns/tuning/), [agent deployment regions](https://docs.livekit.io/deploy/admin/regions/agent-deployment/), and [LiveKit-hosted LLM](https://docs.livekit.io/agents/models/llm/livekit/) docs.

## Before calling it production

At minimum, add:

- an evaluation set with product audio, accents, noise, interruptions, relevant/irrelevant retrieval, and prompt-injection cases;
- explicit availability, privacy, retention, and data-governance decisions for every provider;
- token-service authentication, abuse limits, secret rotation, and least-privilege project access;
- load/capacity/cost tests plus alerts, runbooks, rollback, and incident ownership;
- failure behavior for model, retrieval, network, and regional outages;
- accessibility and non-audio interaction requirements.

## Concepts

- Per-turn diagnostics through `conversation_item_added` and `ChatMessage.metrics`.
- Cumulative session/model usage through `session_usage_updated` and final `session.usage`.
- Turn/interruption inference request counts.
- First-time `create` versus version update with `deploy`.
- Worker cold start versus per-turn response latency.
- Local validation before a private deployment; private deployment before a public release.
