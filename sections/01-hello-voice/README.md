# Course Section 2: Hello voice

Directory 1 of 4: `01-hello-voice`.

## Goal

**Start a voice agent, measure the wait to first audio, then feel the broken baseline.**

## Run

Complete the [root setup and pre-flight check](../../README.md#pre-class-setup) first. Use LiveKit CLI 2.19.3+ with the same project as `.env`, and stop the earlier section’s local worker.

```bash
lk agent dev sections/01-hello-voice/agent.py
```

Open the Agent Console link printed by the CLI, or launch [Agent Console](https://docs.livekit.io/testing/agent-console/) from the same project’s dashboard. Select the exact `dev-...` development deployment printed in the terminal before starting the session. Keep the terminal visible and use headphones. Default production/older Playground dispatch will not target this dev worker.

## Key takeaway
>
> “This is the standard chained voice pipeline: speech recognition, an LLM, then speech synthesis. We are measuring the wait the user actually feels, not just one model call.”

```text
You speak → Deepgram STT → GPT-4o-mini → Cartesia TTS → you hear audio
```

LiveKit Inference supplies STT, LLM, and TTS from the shorthand model names. Silero VAD runs locally in the worker.

## Read the timing

```text
[timing] end-of-turn delay: ...
[timing] transcription delay:    ...
[timing] LLM TTFT (first token): ...
[timing] TTS TTFB (first byte):  ...
[timing] TOTAL end-to-end:       ...ms
```

- **TTFT** is when the LLM starts responding.
- **TTFB** is when TTS returns its first audio chunk.
- **`TOTAL`** comes directly from `ChatMessage.metrics["e2e_latency"]`: speech-end → first server audio. It excludes network delivery and browser playback. Compare it with the wait you hear; do not add overlapping component timings.
- The greeting has no `TOTAL`, because no user turn preceded it.

## Feel the broken baseline

This worker deliberately sets:

```python
turn_handling=TurnHandlingOptions(
    turn_detection="vad",
    interruption={"enabled": False, "discard_audio_if_uninterruptible": True},
    preemptive_generation={"enabled": False},
)
```

> **Key point:** turn detection decides when the *user* is done; interruption decides when the *agent* stops. They are separate problems.

Try these, and note **jumped in** or **waited**:

1. “What’s two plus two?” — record the `TOTAL`.
2. “Hmm, the thing I want to ask is” — pause silently for **2 seconds**.
3. “What’s the weather” — pause **2 seconds**, then finish: “in Lisbon?”
4. Talk over the agent during any reply.

The silence-only baseline may reply mid-thought. When you talk over it, it keeps speaking and drops your audio. Stop it with `Ctrl+C`, then repeat the same script in [course Section 3](../02-production-ux/README.md).

## Concepts

- `AgentSession` runs the STT → LLM → TTS pipeline.
- `Agent` contains instructions and response behavior.
- `JobContext` is the room handle; `AgentServer` registers the entrypoint with `@server.rtc_session()`; `cli.run_app(server)` starts it.
