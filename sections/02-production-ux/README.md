# Section 2: Turn detection that doesn't cut people off

## Goal

**Make the agent wait for a completed thought—and let a real interruption through without treating every sound as one.**

## Run

Complete the [root setup and pre-flight check](../../README.md#pre-class-setup) first. Stop the Section 1 worker, then run:

```bash
uv run python sections/02-production-ux/agent.py dev
```

## Key takeaway
>
> “Silence is not the same as a finished thought. We need one system to decide when the user is done and another to decide when the agent should stop.”

## What changed

### 1. Semantic end-of-turn detection

```python
turn_detection=MultilingualModel()
```

The model uses the transcript as well as silence to decide whether the user has completed their thought. It replaces the Section 1 silence-only baseline.

### 2. Tuned barge-in

```python
allow_interruptions=True
min_interruption_duration=0.7
min_interruption_words=2
resume_false_interruption=True
```

- A real spoken interruption stops the agent.
- A cough or single “mm-hm” should not.
- Requiring words trades a little interruption speed for much better robustness.
- If an apparent interruption produces no transcript, LiveKit resumes the paused reply after `false_interruption_timeout=2.0`.

### 3. Preemptive generation

```python
preemptive_generation=True
```

LiveKit can start LLM/TTS work from a stable interim transcript before final turn detection. If the user continues, it cancels that speculative work and regenerates from the completed turn.

> **Important:** preemptive generation means component timings can overlap. Use `perceived`, not the sum of EOU, LLM, and TTS timings.

## Test the contrast

Repeat the Section 1 script with the same words and **2-second** pauses:

1. Pause after “Hmm, the thing I want to ask is.”
2. Pause after “What’s the weather,” then add “in Lisbon?”
3. Speak a full sentence over the agent.
4. Say only “mm-hm” while it speaks.

Expected result: it waits through the unfinished phrases, stops for the full interruption, and continues through the backchannel. If both versions wait, use a **3-second** pause.

```text
[latency] perceived=...ms response=COMPLETE preemptive=on | ...
```

`perceived` is LiveKit’s speech-end → first-server-audio measurement. Compare several complete turns with Section 1; a median is more useful than one lucky run.

## Concepts

- `MultilingualModel` provides semantic end-of-turn detection.
- `preemptive_generation` overlaps inference with turn detection.
- Turn detection is about the **user’s** turn; barge-in is about the **agent’s** reply.

This course’s target agent is read-only, so function tools and state-mutating actions are intentionally out of scope.
