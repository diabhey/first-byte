# Section 2: Turn detection that doesn't cut people off

## Goal

Fix the one thing every voice demo gets wrong: the agent talking over you when you pause mid-thought.

## Run

```bash
uv run python sections/02-production-ux/agent.py dev
```

Same `[timing]` logs as Section 1 — compare `end-of-utterance delay` on the A/B phrases.

## What changed from Section 1

Two things, aimed at the two halves of a conversation.

**1. When *you* are finished — semantic turn detection:**

```python
turn_detection=MultilingualModel(),
```

This is LiveKit's open-weights end-of-turn model. Instead of "stop after N ms of silence" (VAD-only), it uses the STT transcript to predict whether you've actually finished your thought. On unfinished phrases with a long pause, Section 1 often jumps in; this agent should wait.

**Stop the Section 1 worker first** (`Ctrl+C`). Only one `dev` agent should be running, or both will fight for the same room.

## A/B turn-taking script (same as Section 1)

Reconnect in the Playground, then repeat the **exact** script and **2 second** pauses from [`../01-hello-voice/README.md`](../01-hello-voice/README.md). Compare your notes.

| # | Say this | Pause | Then | What to watch (Section 2) |
|---|----------|-------|------|---------------------------|
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
[timing] end-of-utterance delay: 0.84s (silence → turn committed)
[timing] transcription delay:    0.31s (speech end → final transcript)
[timing] LLM TTFT (first token): 0.22s
[timing] TTS TTFB (first byte):  0.18s
[timing] TOTAL end-to-end:       1240ms (speech end → first audio byte)
```

`TOTAL` is what the user actually feels: the wait between their last word and
your first audio. It sums end-of-utterance delay, LLM TTFT, and TTS TTFB.
Transcription delay is deliberately **not** added, because it is measured from
the same instant as the end-of-utterance delay and is already contained inside
it — adding both would double-count the same waiting. Compare `TOTAL` against
Section 1 alongside the EOU delay; the 800 ms course target applies to TTS TTFB
only, not to this number.

## Concepts introduced

- `MultilingualModel` from `livekit-plugins-turn-detector`
- The semantic end-of-turn principle: stop guessing from acoustic silence, listen to what was said
- Interruption tuning: `allow_interruptions`, `min_interruption_duration`,
  `min_interruption_words`, and false-interruption recovery
- Turn detection and interruption are independent systems — one decides when
  the user is done, the other when the agent must stop

## What this section deliberately doesn't cover

The original §3 included function tools, `ToolError`, `disallow_interruptions`, and the `agent_false_interruption` event. They're all real LiveKit features, but the production agent this course builds toward (the HeartByte orb at [heartbyte.io](https://heartbyte.io)) is read-only — no state-mutating actions, no backchannel handler. Cutting them keeps the course focused on what students will actually use. If you do need function tools later, the LiveKit docs cover them well: [Tool definition](https://docs.livekit.io/agents/logic/tools/definition).
