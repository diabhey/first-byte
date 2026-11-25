# Course Section 2: Hello Voice

Directory 1 of 4: `01-hello-voice`.

## Goal

Start one local voice worker, measure the wait to first server audio, and document the deliberately awkward baseline.

## Run with the low-memory path

Complete the [root setup](../../README.md#setup), stop any other agent worker, and run from the repository root:

```bash
lk agent console sections/01-hello-voice/agent.py
```

Terminal Agent Console connects the worker directly to your microphone and speakers. It avoids a browser and LiveKit room. The worker runs locally, but the pipeline is not offline: Deepgram STT, the configured LLM, and Cartesia TTS use LiveKit Inference.

Console controls:

- `m`: mute/unmute;
- `Ctrl+T`: switch between voice and text input;
- `q`: quit.

If audio is unavailable, start with:

```bash
lk agent console --text sections/01-hello-voice/agent.py
```

Text mode can confirm the LLM and response path, but it disables STT/TTS and cannot validate the timing or voice behavior in this exercise. Mark the fallback on the [learner worksheet](../../LEARNER_WORKSHEET.md).

## Pipeline

```text
speech → Deepgram nova-3 → LLM_MODEL → Cartesia sonic-3 → audio
```

The default `LLM_MODEL` is `google/gemma-4-31b-it`; `.env` can override it for a rehearsed model. Silero VAD runs in the worker.

## Read the timing

```text
[timing] end-of-turn delay:      ...
[timing] transcription delay:    ...
[timing] LLM TTFT (first token): ...
[timing] TTS TTFB (first byte):  ...
[timing] TOTAL pipeline:         ...ms — under 1370ms
```

Ask a question after the greeting. The greeting has no user turn, so the worker prints that it has no pipeline total yet.

- Transcription delay is the time until STT produces the final transcript. It is not STT “first byte.”
- LLM TTFT is time to first token.
- TTS TTFB is time to first audio chunk from synthesis.
- `TOTAL pipeline` comes from `ChatMessage.metrics["e2e_latency"]`: speech end to first server audio. It excludes playback on your laptop.
- The budget in this section is 1370 ms. The line says `under`, `at`, or `over` 1370 ms.
- The stages can overlap. Do not add them.

## Exercise 1: one complete reply

Ask a short factual question. Confirm the transcript, one complete response, and the configured model shown at startup.

## Exercise 2: feel and measure the baseline

This worker intentionally uses VAD-only turn detection, disables interruption, and disables preemptive generation.

Use the same script later in Course Section 3:

1. Ask “How’s it going?” at least three times. Record complete-turn `TOTAL pipeline` values and calculate the median.
2. Say “Hmm, the thing I want to ask is,” then pause for two seconds.
3. Say “What’s the weather,” pause for two seconds, then finish “in Lisbon?”
4. Speak a complete sentence over the agent during its reply.
5. Say only “mm-hm” during another reply.

Record observed outcomes, not guaranteed ones. The baseline may commit during an unfinished pause. Because interruption is disabled, speaking over it should not stop the reply.

> Turn detection decides when the user finished a turn. Interruption handling decides whether incoming speech stops the agent's reply. They are separate mechanisms.

Stop this worker with `q` or `Ctrl+C` before opening [Course Section 3](../02-production-ux/README.md).

## Concepts

- `AgentSession` owns the STT, LLM, and TTS pipeline.
- `Agent` contains instructions and response behavior.
- `JobContext` is the job/room handle when the worker runs in that environment.
- `AgentServer` registers the entrypoint with `@server.rtc_session()`.
- `LLM_MODEL` isolates a fast-changing model choice from the course code.
