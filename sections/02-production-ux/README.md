# Course Section 3: Production UX

[← Hello Voice](../01-hello-voice/README.md) · [Course README](../../README.md) · Next: [Grounding with Moss →](../03-grounding-moss/README.md)

Folder `02-production-ux`. Make the agent wait for a finished thought, and let a real interruption through.

## Run

Quit Hello Voice with `q`, then:

```bash
lk agent console sections/02-production-ux/agent.py
```

The box is the same as [Hello Voice](../01-hello-voice/README.md#read-the-timing).

## What changed in [`agent.py`](./agent.py)

### 1. Semantic end of turn

```python
turn_detection=inference.TurnDetector(version="v1-mini"),
```

A local audio model listens to meaning and tone, not just silence. It runs on CPU here and in Cloud.

### 2. Tuned interruptions

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

A real sentence stops the agent. A cough or a single “mm-hm” should not. If an interruption produces no words, the agent resumes after 2 seconds.

### 3. Preemptive generation

```python
preemptive_generation={"enabled": True}
```

The model starts from a stable partial transcript before your turn is final. If you keep talking, that reply is thrown away and generated again.

Because the model can start early, the box may show the clocks overlapping. Read the measured pause.

## Exercise 3: run the same script

Use the same words and 2-second pauses as Hello Voice:

1. Pause after “Hmm, the thing I want to ask is.”
2. Pause after “What’s the weather,” then add “in Lisbon?”
3. Say a full sentence over the agent.
4. Say only “mm-hm” while it speaks.

It should wait through unfinished phrases, stop for a real interruption, and keep going through a backchannel. It is not perfect: a long pause can still end your turn. Compare several turns with Hello Voice, not one lucky run.

## Concepts

- Turn detection is about **your** turn. Interruption is about the **agent's** reply.
- `inference.TurnDetector(version="v1-mini")` replaces the deprecated `MultilingualModel` plugin.
- This agent is read-only, so function tools are out of scope.

---

[← Hello Voice](../01-hello-voice/README.md) · [Course README](../../README.md) · Next: [Grounding with Moss →](../03-grounding-moss/README.md)
