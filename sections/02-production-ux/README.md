# Course Section 3: Semantic turns and interruption handling

Directory 2 of 4: `02-production-ux`.

## Goal

Repeat the baseline script with semantic end-of-turn detection and adaptive interruption handling, then compare evidence rather than impressions.

## Run

Stop the Hello Voice worker and run from the repository root:

```bash
lk agent console sections/02-production-ux/agent.py
```

This is the one-worker, low-memory path. It avoids a browser/room but still calls LiveKit Inference. Use `--text` only as a response-path fallback; text mode cannot test end-of-turn or interruption behavior.

## What changed

### 1. Semantic end-of-turn detection

```python
turn_detection=inference.TurnDetector(version="v1-mini")
```

The local audio model uses speech and conversational cues to estimate whether a thought is complete. It replaces the VAD-only endpointing baseline; VAD still contributes audio-activity information.

### 2. Adaptive interruption

```python
interruption={
    "enabled": True,
    "mode": "adaptive",
    "min_duration": 0.7,
    "min_words": 2,
    "false_interruption_timeout": 2.0,
    "resume_false_interruption": True,
}
```

Adaptive mode uses the interruption model to decide whether incoming audio should stop the agent. Duration/word thresholds and false-interruption recovery remain guardrails. A full spoken interruption should have a stronger signal than a cough or short backchannel, but audio and model behavior vary.

### 3. Preemptive generation for the ungrounded agent

```python
preemptive_generation={"enabled": True}
```

When an interim transcript is stable, LiveKit can start LLM generation before final turn commitment. By default this speculates on the LLM response, not the entire STT/TTS pipeline. If the user continues, the work can be discarded and regenerated from the completed turn.

This optimization stays enabled here because no retrieval hook modifies the turn context. It is disabled in the grounded sections, where always-on retrieval would invalidate speculative ungrounded output.

## Exercise 3: same script, new behavior

Repeat the exact prompts from Course Section 2:

1. Pause after “Hmm, the thing I want to ask is.”
2. Pause after “What’s the weather,” then add “in Lisbon?”
3. Speak a complete sentence over the agent.
4. Say only “mm-hm” while it speaks.
5. Collect at least three complete-turn `server_e2e` values for the same short prompt and calculate the median.

Record whether each attempt jumped in, waited, stopped, resumed, or continued. Natural speech is variable. A semantic model can still commit after a long pause, and an interruption model can still misclassify noise.

```text
[latency] server_e2e=...ms response=COMPLETE preemptive=on | ...
```

`server_e2e` is speech end to first server audio. It excludes client delivery/playback, and overlapping component timings must not be added.

## Compare

Complete the A/B table in the [learner worksheet](../../LEARNER_WORKSHEET.md):

- VAD-only versus semantic completion during the same unfinished pause;
- interruption-disabled versus adaptive interruption during the same barge-in;
- behavior median versus baseline median;
- one failure or ambiguous case worth evaluating with product audio.

Stop the worker before the break.

## Concepts

- User turn completion and agent interruption are independent decisions.
- `v1-mini` is a local audio end-of-turn model.
- Adaptive interruption consumes model inference; the final section reports its request count.
- Preemptive generation can reduce wait while spending speculative LLM work.
