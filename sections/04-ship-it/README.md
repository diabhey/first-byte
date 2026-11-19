# Course Section 5: Ship It

[← Grounding with Moss](../03-grounding-moss/README.md) · [Course README](../../README.md) · Next: [Orb →](../../orb/README.md)

Folder `04-ship-it`. Deploy the grounded agent, call it from a browser, then inspect the call in LiveKit Cloud.

You need the Moss index from [Grounding with Moss](../03-grounding-moss/README.md#build-the-index).

## 1. Turn on Agent observability

In [LiveKit Cloud](https://cloud.livekit.io), open your project's **Settings → Observability** and enable **Agent observability**. Only sessions that start after this are recorded, so do it before you call the agent.

## 2. Deploy

Quit any console, then:

```bash
lk cloud auth
lk project set-default "<your-course-project-name>"
cd sections/04-ship-it
lk agent create --secrets-file=../../.env
```

`create` builds the worker, sends the `MOSS_*` values as secrets, and writes `livekit.toml`. LiveKit supplies its own credentials. The first build can take several minutes.

Check it:

```bash
lk agent secrets
lk agent status
lk agent logs
```

Later releases from this folder:

```bash
lk agent deploy
```

This folder deploys on its own, with its own [`pyproject.toml`](./pyproject.toml), lockfile, and [`Dockerfile`](./Dockerfile).

### If `deploy` fails

`deploy` updates the agent named in `livekit.toml`. If that agent was deleted, or belongs to another project, it cannot work. Check what exists:

```bash
lk agent list
```

If your agent is gone, move `livekit.toml` out of this folder and run `lk agent create` again. Do not copy the IDs from [`livekit.toml.example`](./livekit.toml.example).

## 3. Call it from the orb

Follow the [orb README](../../orb/README.md). In short: copy `config.template.js` to `config.js`, paste your Cloud URL and a fresh token, serve the folder, and tap the orb.

```text
browser ── WebRTC ──> LiveKit Cloud ── dispatch ──> deployed worker
```

Ask two or three HeartByte questions, then hang up. The transcript and audio upload when the call ends.

## 4. Inspect the call

### Exercise 6

In LiveKit Cloud, open **Sessions**, pick your call, and select the **Agent insights** tab.

- **Metrics** shows the latency of each turn and what the call used: LLM tokens, STT and TTS audio, and TTS characters. Select the slowest turn and the recording jumps to it.
- **Traces** splits that turn into the same stages as the terminal box: end of turn, STT, LLM, and TTS.
- **Session logs** shows the agent's own lines, including `[moss] injected`.

Then open **Agents** and select your agent. It shows how an average reply splits between stages, across every call.

Look for the stage that costs the most, and watch the prompt tokens jump on grounded turns. The five Moss results are cheap in time, but they are most of the prompt.

The dashboard's stage bars overlap in time, so they do not add up to the total the way the terminal box does. Use them to find the biggest stage, and the box to see the exact sum.

## 5. Make it faster

Fix the biggest stage first. Change one setting, redeploy, make the same calls, and compare. LiveKit's own advice is to check the metrics after every change, because some settings do not always help.

### End of turn is the biggest row

How long the agent waits after you stop talking.

- **Lower the minimum wait.** `endpointing.min_delay` defaults to 0.5 seconds. Lower it a little at a time. Too low, and the agent cuts people off.
- **Let it adapt.** `endpointing.mode = "dynamic"` learns how long this caller usually pauses, within `min_delay` and `max_delay`.
- **Keep the turn detector.** It is what lets a low wait stay safe. Silence alone would cut people off.

```python
turn_handling=TurnHandlingOptions(
    turn_detection=inference.TurnDetector(version="v1-mini"),
    endpointing={"mode": "dynamic", "min_delay": 0.3, "max_delay": 3.0},
)
```

### LLM first token is the biggest row

- **Keep preemptive generation on.** It is on in this agent. The model starts on a stable transcript before your turn is confirmed.
- **Send a shorter prompt.** Every grounded turn adds five Moss results. Try `top_k=3`, and watch both `llm_prompt` and the answers.
- **Try a faster model.** LiveKit recommends its hosted `google/gemma-4-31b-it` as the default LLM for voice. It is one string to change: `llm="google/gemma-4-31b-it"`.
- **Ask for short replies.** A one- or two-sentence answer reaches its first sentence sooner.

### TTS first byte is the biggest row

- **Start speech early.** `preemptive_generation={"preemptive_tts": True}` also starts TTS before the turn is confirmed. It is faster, but a cancelled reply wastes the synthesis.

### A handoff is the biggest row

- **Handoff to TTS** is the wait for the model's first full sentence, because TTS starts on a sentence. Tell the agent to open with a short sentence.
- **Deploy near your callers.** An agent runs in one region, chosen at `lk agent create --region …`, and you cannot change it later. For callers in several places, deploy once per region.
- **Keep retrieval in-process.** Moss already searches in the worker, so it adds no network hop.

### Not faster, but steadier

`interruption.mode = "adaptive"` uses an audio model to tell a real interruption from an “uh-huh”. Noise cancellation cleans the audio before VAD and the turn detector hear it. Neither one cuts the wait. They stop a lower wait from turning into the agent cutting people off.

All of these are in LiveKit's [turn-taking tuning guide](https://docs.livekit.io/agents/logic/turns/tuning/), [agent deployment regions](https://docs.livekit.io/deploy/admin/regions/agent-deployment/), and [LiveKit-hosted LLM](https://docs.livekit.io/agents/models/llm/livekit/) docs.

## Local fallback

The same worker prints the [Hello Voice box](../01-hello-voice/README.md#read-the-timing) and the usage in the terminal:

```bash
lk agent console sections/04-ship-it/agent.py
```

```text
END OF TURN (+ transcript …)          … ms
    …
[usage] running total: ...
[usage] session summary: ...
```

- `[usage] running total` prints under each box: everything the call has used so far. Do not add the lines together.
- `[usage] session summary` prints when you quit.

Speak your questions. A typed turn skips the Moss hook. The three handlers are in [`agent.py`](./agent.py): `conversation_item_added`, `session_usage_updated`, and the shutdown callback.

Once this folder has a `livekit.toml`, the console reads `sections/04-ship-it/.env.local` instead of the repo-root `.env`. Copy the `LIVEKIT_*` and `MOSS_*` lines into it. The file is gitignored.

## Concepts

- One-command deploy with `lk agent create`.
- Agent insights: transcripts, traces, metrics, and audio for every session.
- In code: `conversation_item_added`, `ChatMessage.metrics`, `session_usage_updated`, and `ctx.add_shutdown_callback`.
- **Ship it, then watch real calls.**

---

[← Grounding with Moss](../03-grounding-moss/README.md) · [Course README](../../README.md) · Next: [Orb →](../../orb/README.md)
