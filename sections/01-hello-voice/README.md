# Section 1: Hello voice

## Goal

**Start a voice agent, measure the wait to first audio, then feel the broken baseline.**

## Run

Complete the [root setup and pre-flight check](../../README.md#pre-class-setup) first. Use the same LiveKit Cloud project in the Playground as the one configured in `.env`, and stop any other local workers.

```bash
uv run python sections/01-hello-voice/agent.py dev
```

Open [Agents Playground](https://agents-playground.livekit.io), connect, and keep the terminal visible. Use headphones.

## Key takeaway
>
> “This is the standard chained voice pipeline: speech recognition, an LLM, then speech synthesis. We are measuring the wait the user actually feels, not just one model call.”

```text
You speak → Deepgram STT → GPT-4o-mini → Cartesia TTS → you hear audio
```

LiveKit Inference supplies STT, LLM, and TTS from the shorthand model names. Silero VAD runs locally in the worker.

## Read the timing

```text
[timing] end-of-utterance delay: ...
[timing] transcription delay:    ...
[timing] LLM TTFT (first token): ...
[timing] TTS TTFB (first byte):  ...
[timing] TOTAL end-to-end:       ...ms
```

- **TTFT** is when the LLM starts responding.
- **TTFB** is when TTS returns its first audio chunk.
- **`TOTAL`** is this agent's speech-end → first-audio estimate: EOU delay + LLM TTFT + first TTS TTFB. Do not add transcription delay too; it overlaps the EOU window.
- The greeting has no `TOTAL`, because no user turn preceded it.

## Feel the broken baseline

This worker deliberately sets:

```python
allow_interruptions=False
discard_audio_if_uninterruptible=True
```

> **Key point:** turn detection decides when the *user* is done; interruption decides when the *agent* stops. They are separate problems.

Try these, and note **jumped in** or **waited**:

1. “What’s two plus two?” — record the `TOTAL`.
2. “Hmm, the thing I want to ask is” — pause silently for **2 seconds**.
3. “What’s the weather” — pause **2 seconds**, then finish: “in Lisbon?”
4. Talk over the agent during any reply.

The silence-only baseline may reply mid-thought. When you talk over it, it keeps speaking and drops your audio. Stop it with `Ctrl+C`, then repeat the same script in [Section 2](../02-production-ux/README.md).

## Concepts

- `AgentSession` runs the STT → LLM → TTS pipeline.
- `Agent` contains instructions and response behavior.
- `JobContext` is the room handle; `WorkerOptions` registers the worker entrypoint.
