# Course Section 3: Turn detection that doesn't cut people off

Directory 2 of 4: `02-production-ux`.

## Goal

**Make the agent wait for a completed thought—and let a real interruption through without treating every sound as one.**

## Run

Complete the [root setup and pre-flight check](../../README.md#pre-class-setup) first. Quit the Hello Voice console with `q`, then run:

```bash
lk agent console sections/02-production-ux/agent.py
```

Talk in the terminal, the same way as Hello Voice. Use headphones. Press `q` to quit before you start the next section.

## Key takeaway
>
> “Silence is not the same as a finished thought. We need one system to decide when the user is done and another to decide when the agent should stop.”

## What changed

### 1. Semantic end-of-turn detection

```python
turn_handling=TurnHandlingOptions(
    turn_detection=inference.TurnDetector(version="v1-mini"),
)
```

The built-in audio model uses spoken meaning and acoustic cues to detect completed turns. `v1-mini` runs locally on CPU, keeping the same model choice in development and Cloud. This replaces the Hello Voice VAD-only baseline; no text turn-detector plugin is needed.

### 2. Tuned barge-in

```python
interruption={
    "enabled": True,
    "mode": "vad",
    "min_duration": 0.7,
    "min_words": 2,
    "false_interruption_timeout": 2.0,
    "resume_false_interruption": True,
}
```

- A real spoken interruption stops the agent.
- A cough or single “mm-hm” should not.
- Requiring words trades a little interruption speed for much better robustness.
- If an apparent interruption produces no transcript, LiveKit resumes the paused reply after `false_interruption_timeout=2.0`.

### 3. Preemptive generation

```python
preemptive_generation={"enabled": True}
```

The `interruption` and `preemptive_generation` values are passed inside `TurnHandlingOptions`. LiveKit can start LLM/TTS work from a stable interim transcript before final turn detection. If the user continues, it cancels that speculative work and regenerates from the completed turn.

> **Important:** preemptive generation means the stage clocks can overlap the turn decision. Read the measured pause in the pipeline box. The printed sum includes the handoff gaps, so it matches that pause. Do not add the transcript note on top of end of turn.

## Test the contrast

Repeat the Hello Voice script with the same words and **2-second** pauses:

1. Pause after “Hmm, the thing I want to ask is.”
2. Pause after “What’s the weather,” then add “in Lisbon?”
3. Speak a full sentence over the agent.
4. Say only “mm-hm” while it speaks.

Expected result: it is more likely to wait through unfinished phrases, stop for a full interruption, and continue through a backchannel. Repeat several turns: the model also has endpointing limits and can commit a turn during a long pause. Inspect the observed behavior instead of treating any phrase as a guaranteed test case.

The terminal prints one pipeline box per reply, the same layout as Hello Voice. A cancelled reply is marked on that box. Compare several complete turns with Hello Voice; a median is more useful than one lucky run.

## Concepts

- `inference.TurnDetector(version="v1-mini")` provides local audio-based semantic end-of-turn detection. The older transcript-based `MultilingualModel` plugin is deprecated.
- `preemptive_generation` overlaps inference with turn detection.
- Turn detection is about the **user’s** turn; barge-in is about the **agent’s** reply.

This course’s target agent is read-only, so function tools and state-mutating actions are intentionally out of scope.
