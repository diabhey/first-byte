# Course Section 2: Hello Voice

[Course README](../../README.md) · Next: [Production UX →](../02-production-ux/README.md)

Folder `01-hello-voice`. Start a voice agent, measure the wait, then feel the broken baseline.

## Run

Finish the [pre-class setup](../../README.md#pre-class-setup) first.

```bash
lk agent console sections/01-hello-voice/agent.py
```

Talk in the terminal with headphones on. Press `q` to quit.

The pipeline is [`agent.py`](./agent.py):

```text
You speak → Deepgram STT → GPT-4o-mini → Cartesia TTS → you hear audio
```

LiveKit Inference runs the three models from their short names. Silero VAD runs on your machine.

## Read the timing

After each reply the terminal prints one box:

```text
END OF TURN (+ transcript …)          … ms
LLM FIRST TOKEN                       … ms
    └ handoff to TTS                      … ms
TTS FIRST BYTE                        … ms
    └ handoffs between clocks             … ms
… + … + … = … ms
… ms                          measured pause
```

- **End of turn** is how long after your sound stopped the agent decided you were done. The transcript time in brackets is already inside it.
- **LLM first token** and **TTS first byte** are the two model clocks.
- The indented **handoff** rows are the gaps between those clocks. They are part of the sum.
- The **measured pause** is speech end to the first audio frame. The sum matches it.

The greeting has no box, because nobody spoke before it.

## Exercises 1–2: feel the broken baseline

This file is wrong on purpose:

```python
turn_handling=TurnHandlingOptions(
    turn_detection="vad",
    interruption={"enabled": False, "discard_audio_if_uninterruptible": True},
    preemptive_generation={"enabled": False},
)
```

Silence ends your turn, and the agent cannot be interrupted. Say each line and note whether it **jumped in** or **waited**:

1. “What’s two plus two?” Write down the measured pause.
2. “Hmm, the thing I want to ask is” and stay silent for 2 seconds.
3. “What’s the weather”, wait 2 seconds, then “in Lisbon?”
4. Talk over the agent while it replies.

It will answer mid-thought, and it will ignore you when you talk over it.

> Turn detection decides when *you* are done. Interruption decides when the *agent* stops. They are separate problems.

## Concepts

- `AgentSession` runs the STT → LLM → TTS pipeline.
- `Agent` holds the instructions.
- `AgentServer` registers the entrypoint with `@server.rtc_session()`, and `JobContext` is the handle on the room.

---

[Course README](../../README.md) · Next: [Production UX →](../02-production-ux/README.md)
