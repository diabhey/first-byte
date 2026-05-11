# Section 2: Turn detection that doesn't cut people off

## Goal

Fix the one thing every voice demo gets wrong: the agent talking over you when you pause mid-thought.

## Run

```bash
uv run python sections/02-production-ux/agent.py dev
```

## What changed from Section 1

One line:

```python
turn_detection=MultilingualModel(),
```

This is LiveKit's open-weights end-of-turn model. Instead of "stop after N ms of silence" (VAD-only), it uses the STT transcript to predict whether you've actually finished your thought. The difference is dramatic on phrases with natural pauses.

## Things to try

- Say: "Hmm, the thing I want to ask is..." then pause for a beat. With Section 1's agent, you'd already be interrupted. With this one, the agent waits.
- Say: "What's the weather... in Lisbon?" The pause in the middle no longer triggers a premature reply.
- Compare back-to-back: run `sections/01-hello-voice/agent.py dev` in one terminal and this one in another, and switch between them in the Playground.

## Concepts introduced

- `MultilingualModel` from `livekit-plugins-turn-detector`
- The semantic end-of-turn principle: stop guessing from acoustic silence, listen to what was said

## What this section deliberately doesn't cover

The original §3 included function tools, `ToolError`, `disallow_interruptions`, and the `agent_false_interruption` event. They're all real LiveKit features, but the production agent this course builds toward (the HeartByte orb at [heartbyte.io](https://heartbyte.io)) is read-only — no state-mutating actions, no backchannel handler. Cutting them keeps the course focused on what students will actually use. If you do need function tools later, the LiveKit docs cover them well: [Tool definition](https://docs.livekit.io/agents/logic/tools/definition).
