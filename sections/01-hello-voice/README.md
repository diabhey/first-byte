# Section 1: Hello voice

## Goal

Boot a voice agent in under 60 seconds and have your first conversation.

## Run

```bash
uv run python sections/01-hello-voice/agent.py dev
```

Open [agents-playground.livekit.io](https://agents-playground.livekit.io) in another tab. Connect to your local agent. Talk to it. Keep the terminal visible — after each turn it prints `[timing]` lines followed by a `TOTAL` in milliseconds:

```text
[timing] end-of-utterance delay: 0.55s (silence → turn committed)
[timing] transcription delay:    0.29s (speech end → final transcript)
[timing] LLM TTFT (first token): 0.61s
[timing] TTS TTFB (first byte):  0.33s
[timing] TOTAL end-to-end:       1490ms (speech end → first audio byte)
```

**TTFT** is time-to-first-token: how long the LLM takes to emit its first token,
not to finish the sentence. **TTFB** is time-to-first-byte: how long the TTS
takes to return its first chunk of audio, not to synthesize the whole reply.
Both measure when output *starts*, because in voice that is the moment the user
stops waiting. TTS TTFB is the metric this course is named after and the one the
800 ms target applies to.

`TOTAL` is the perceived wait from your last word to the agent's first audio. It
adds up the end-of-utterance delay, LLM TTFT, and TTS TTFB. Transcription delay
is not added: it starts from the same instant as the end-of-utterance delay and
already sits inside it, so counting both would double-count the same wait. The
greeting has no `TOTAL` because no user turn preceded it.

## What's happening under the hood

```bash
You speak  →  Silero VAD detects start of speech
           →  Deepgram nova-3 streams transcript          (via LiveKit Inference)
           →  OpenAI gpt-4o-mini generates reply          (via LiveKit Inference)
           →  Cartesia sonic-3 streams audio back         (via LiveKit Inference)
           →  You hear the reply
```

The `vad=silero.VAD.load()` line is the only thing not routed through Inference. VAD runs locally in your worker process for latency reasons.

## What's deliberately broken here

This agent sets `allow_interruptions=False`, so talking over it does nothing —
it finishes its reply no matter what. LiveKit's default is `True`; we switch it
off to give Section 2 something to fix.

`discard_audio_if_uninterruptible=True` (the default) makes it worse in a way
worth feeling: while the agent is speaking and cannot be interrupted, your audio
is dropped rather than buffered. So the agent doesn't just talk over you, it
never hears what you said, and you have to repeat yourself once it stops.

Interruption and turn detection are separate systems, which is easy to conflate.
Interruption decides when to stop the **agent**; turn detection decides when
**you** are finished. Section 2 improves both.

## A/B turn-taking script (run this first)

Run **only this agent**. Use headphones. In the Playground, connect, then work the script top to bottom. For each line: speak exactly as written, hold the pause silently (count in your head), then either finish the sentence or wait to see if the agent jumps in. Note whether the agent **replied during the pause** (too early) or **waited**.

| # | Say this | Pause | Then | What to watch (Section 1) |
|---|----------|-------|------|---------------------------|
| 1 | `What's two plus two?` | — | wait for reply | Control. The `TOTAL` line is that last word → first audio wait; it includes far more than TTS TTFB, so do not compare it with the course's 800 ms TTS target. |
| 2 | `Hmm, the thing I want to ask is` | **2 seconds** (do not continue) | wait | Often jumps in mid-thought — silence looked like end of turn. |
| 3 | `So my real question is` | **2 seconds** | `how does voice activity detection work?` | May cut in during the pause before you finish. |
| 4 | `What's the weather` | **2 seconds** | `in Lisbon?` | May answer after "weather" before "Lisbon". |
| 5 | `I was wondering` | **2 seconds** | `whether you can hear me clearly.` | Same: premature reply during the gap. |
| 6 | Speak over the agent mid-reply on any answer | — | — | Agent talks straight through you and never heard a word of it. `allow_interruptions=False` here — Section 2 fixes it. |
| 7 | Stay silent after a full reply | 30 seconds | — | Agent should not keep talking unprompted. |

Write down for #2–#5: **jumped in** / **waited**, plus the terminal's `[timing] end-of-utterance delay` value when a reply does fire. That number is how long after you stopped speaking before the turn was committed — on premature replies it often lands near your pause length.

Then stop this worker (`Ctrl+C`), run Section 2 with the **same script and same pause lengths**, and compare both the feel and those EOU delay lines.

Section 2 adds semantic turn detection so #2–#5 should wait more often. The gap can be subtle with short pauses — use the full **2 second** holds.

## Concepts introduced

- `AgentSession` orchestrates the STT → LLM → TTS pipeline
- `Agent` defines instructions and reasoning behavior
- `JobContext` is the per-room handle the worker gives your entrypoint
- `WorkerOptions` registers your entrypoint with the LiveKit dispatch
- LiveKit Inference: zero-config provider access via shorthand strings like `"deepgram/nova-3:en"`
