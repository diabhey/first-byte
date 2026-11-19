# Course Section 2: Hello voice

Directory 1 of 4: `01-hello-voice`.

## Goal

**Start a voice agent, measure the wait to first audio, then feel the broken baseline.**

## Run

Complete the [root setup and pre-flight check](../../README.md#pre-class-setup) first. Use LiveKit CLI 2.19.3+ with the same project as `.env`.

```bash
lk agent console sections/01-hello-voice/agent.py
```

`lk agent console` runs this agent on your machine and connects it to your microphone and speakers. Talk in the terminal. The terminal shows the transcript and the pipeline box. Use headphones. Press `m` to mute, `ctrl+t` to type a turn, `?` for shortcuts, and `q` to quit.

## Key takeaway
>
> “This is the standard chained voice pipeline: speech recognition, an LLM, then speech synthesis. We are measuring the wait the user actually feels, not just one model call.”

```text
You speak → Deepgram STT → GPT-4o-mini → Cartesia TTS → you hear audio
```

LiveKit Inference supplies STT, LLM, and TTS from the shorthand model names. Silero VAD runs locally in the worker.

## Read the timing

```text
END OF TURN (+ transcript …)          … ms
LLM FIRST TOKEN                       … ms
    └ handoff to TTS                      … ms
TTS FIRST BYTE                        … ms
    └ handoffs between clocks             … ms
… + … + … = … ms
… ms                          measured pause
```

- **End of turn** already includes the time until the final transcript. That note is not a separate stage.
- **LLM first token** and **TTS first byte** are the two model clocks after the turn is committed.
- The indented handoff rows are the gaps between those clocks. They are part of the sum, so the sum matches the measured pause.
- The measured pause is `ChatMessage.metrics["e2e_latency"]`: speech end to the first audio frame. The greeting has no box, because no user turn preceded it.

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

1. “What’s two plus two?” — record the measured pause.
2. “Hmm, the thing I want to ask is” — pause silently for **2 seconds**.
3. “What’s the weather” — pause **2 seconds**, then finish: “in Lisbon?”
4. Talk over the agent during any reply.

The silence-only baseline may reply mid-thought. When you talk over it, it keeps speaking and drops your audio. Quit with `q`, then repeat the same script in [course Section 3](../02-production-ux/README.md).

## Concepts

- `AgentSession` runs the STT → LLM → TTS pipeline.
- `Agent` contains instructions and response behavior.
- `JobContext` is the room handle; `AgentServer` registers the entrypoint with `@server.rtc_session()`; `cli.run_app(server)` starts it.
