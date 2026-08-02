# Section 2: Turn detection that doesn't cut people off

## Goal

Fix the one thing every voice demo gets wrong: the agent talking over you when you pause mid-thought.

## Run

```bash
uv run python sections/02-production-ux/agent.py dev
```

Preemptive generation is enabled in this section. It starts LLM and
TTS work as soon as a stable transcript arrives, before the semantic
end-of-turn decision is final. If the transcript changes, LiveKit cancels the
speculative response and starts again with the completed turn.

Compare the `[latency] perceived=...` values with your Section 1 measurements,
using the same words, microphone, room, and pause length. That value is
LiveKit's direct measurement from the user's last detected speech to the first
server-side audio. Collect at least five complete turns and compare the median
rather than a single turn.

## What changed from Section 1

Two things, aimed at the two halves of a conversation.

**1. When *you* are finished — semantic turn detection:**

```python
turn_detection=MultilingualModel(),
```

This is LiveKit's open-weights end-of-turn model. Instead of "stop after N ms of silence" (VAD-only), it uses the STT transcript to predict whether you've actually finished your thought. On unfinished phrases with a long pause, Section 1 often jumps in; this agent should wait.

Concretely, it picks between two timeouts. The default wait is
`min_endpointing_delay` (0.5s); if the model's end-of-turn probability falls
below a per-language threshold (0.011 for English), it switches to
`max_endpointing_delay` (3.0s) and keeps listening.

**2. When the *agent* should stop — barge-in, off in Section 1:**

```python
allow_interruptions=True,
discard_audio_if_uninterruptible=False,
min_interruption_duration=0.7,
min_interruption_words=2,
false_interruption_timeout=2.0,
resume_false_interruption=True,
```

Section 1 sets `allow_interruptions=False`, so it steamrolls you. Turning it
back on is only half the job — LiveKit's defaults barge in on any 0.5s of sound
with no word requirement, so a cough or an encouraging "mm-hm" kills the reply.

`min_interruption_words=2` is the one that matters most: it requires two real
transcribed words before stopping the agent, so backchannels pass through while
genuine interruptions still land. `min_interruption_duration=0.7` filters
non-speech noise before STT is even consulted, and
`discard_audio_if_uninterruptible=False` keeps your audio instead of dropping
it, so an interrupted question doesn't have to be repeated.

The trade-off to name in class: requiring words means barge-in waits for a
transcript, so it is slightly slower than the default's instant acoustic
trigger. You are buying robustness with latency. If an interruption turns out
to be noise, `resume_false_interruption` restarts the paused reply after two
seconds rather than leaving the agent stuck mid-sentence — watch for
`resumed false interrupted speech` in the logs.

**Stop the Section 1 worker first** (`Ctrl+C`). Only one `dev` agent should be running, or both will fight for the same room.

## A/B turn-taking script (same as Section 1)

Reconnect in the Playground, then repeat the **exact** script and **2 second** pauses from [`../01-hello-voice/README.md`](../01-hello-voice/README.md). Compare your notes.

| # | Say this | Pause | Then | What to watch (Section 2) |
| --- | -------- | ----- | ---- | ------------------------- |
| 1 | `What's two plus two?` | — | wait for reply | Control — should feel similar to Section 1. |
| 2 | `Hmm, the thing I want to ask is` | **2 seconds** (do not continue) | wait | Should **wait**, not invent a reply mid-thought. |
| 3 | `So my real question is` | **2 seconds** | `how does voice activity detection work?` | Should let you finish after the pause. |
| 4 | `What's the weather` | **2 seconds** | `in Lisbon?` | Should not answer until after "Lisbon". |
| 5 | `I was wondering` | **2 seconds** | `whether you can hear me clearly.` | Should hold through the gap. |
| 6 | Speak over the agent mid-reply with a full sentence | — | — | Agent stops and listens. Section 1 ignored you completely. |
| 6b | Say just `mm-hm` or `yeah` while the agent talks | — | — | Agent keeps going — under the 2-word threshold, so backchannels don't cut it off. |
| 7 | Stay silent after a full reply | 30 seconds | — | Still quiet — turn detection doesn't make it chatty. |

**How to score:** for #2–#5, count how often Section 1 **jumped in** vs Section 2 **waited**, and compare `[timing] end-of-utterance delay` in the terminal. That delta is the lesson: silence ≠ end of turn. If both waited, lengthen the pause to ~3 seconds and retry #2 and #4 — short pauses often look the same on both agents.

Example terminal output after a turn:

```text
[config] preemptive_generation=on
[timing] end-of-utterance delay: 0.84s (silence → turn committed)
[timing] transcription delay:    0.31s (speech end → final transcript)
[timing] LLM TTFT (first token): 0.22s
[timing] TTS TTFB (first byte):  0.18s
[latency] perceived=920ms response=COMPLETE preemptive=on | llm_ttft=220ms tts_ttfb=180ms
```

The `[latency] perceived` value is what the user actually feels: the wait
between their last detected speech and the first server-side audio. Do not add
EOU, LLM TTFT, and TTS TTFB when preemptive generation is enabled because those
stages can overlap. The example values above illustrate the log shape; use your
own A/B measurements to evaluate the change.

The trade-off: preemptive generation can reduce silence, but it spends extra
inference when the user pauses, revises a sentence, or continues speaking after
an interim transcript. Judge it on both latency and behavior: the optimized
agent must still wait through unfinished thoughts.

## Concepts introduced

- `MultilingualModel` from `livekit-plugins-turn-detector`
- `preemptive_generation`: overlap model inference with turn detection, then
  cancel speculative work if the transcript changes
- The semantic end-of-turn principle: stop guessing from acoustic silence, listen to what was said
- Interruption tuning: `allow_interruptions`, `min_interruption_duration`,
  `min_interruption_words`, and false-interruption recovery
- Turn detection and interruption are independent systems — one decides when
  the user is done, the other when the agent must stop

## What this section deliberately doesn't cover

The original §3 included function tools, `ToolError`, `disallow_interruptions`, and the `agent_false_interruption` event. They're all real LiveKit features, but the production agent this course builds toward (the HeartByte orb at [heartbyte.io](https://heartbyte.io)) is read-only — no state-mutating actions, no backchannel handler. Cutting them keeps the course focused on what students will actually use. If you do need function tools later, the LiveKit docs cover them well: [Tool definition](https://docs.livekit.io/agents/logic/tools/definition).
