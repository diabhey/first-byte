# Section 4: Ship it

## Goal

Wire production observability, then deploy the agent to LiveKit Cloud Agents with a single command. By the end of this section your agent runs on the public internet against a global edge.

## Step 1: Run locally with metrics

```bash
uv run python sections/04-ship-it/agent.py dev
```

Connect via the [Agents Playground](https://agents-playground.livekit.io) and have a conversation. Watch your terminal:

- **`metrics_collected`** logs fire on every measurable event: STT first byte, LLM time-to-first-token, TTS first audio chunk. This is your latency budget audit in real time.
- **`[usage] session summary`** logs once when the session ends, via the `add_shutdown_callback`. Token counts, audio durations, cost.

```python
usage_collector = metrics.UsageCollector()

@session.on("metrics_collected")
def _on_metrics(ev: MetricsCollectedEvent) -> None:
    metrics.log_metrics(ev.metrics)
    usage_collector.collect(ev.metrics)

ctx.add_shutdown_callback(_log_session_summary)
```

## Step 2: Deploy

```bash
cd sections/04-ship-it
lk agent create
```

`lk agent create` builds a container image, registers it as a LiveKit Cloud Agent worker, and starts dispatching it to rooms in your project.

After deploy:

1. Open [cloud.livekit.io](https://cloud.livekit.io) and find your new agent.
2. Set environment variables in the agent's settings: `MOSS_PROJECT_ID`, `MOSS_PROJECT_KEY`, `MOSS_INDEX_NAME`. (The LiveKit and OpenAI/Deepgram/Cartesia credentials are handled by LiveKit Inference automatically.)
3. Note the agent ID. Connect from the Agents Playground or any LiveKit room and your deployed agent will dispatch.

That's it. No Dockerfile, no Kubernetes manifest, no SSL cert wrangling.

## Multi-agent handoff (teaser, no exercise)

When one agent isn't enough:

```python
class TriageAgent(Agent):
    @function_tool()
    async def transfer_to_billing(self, context: RunContext):
        """Transfer to a billing specialist."""
        return BillingAgent(chat_ctx=self.chat_ctx), "Transferring to billing"

class BillingAgent(Agent):
    def __init__(self, chat_ctx: ChatContext):
        super().__init__(
            instructions="You are a billing specialist...",
            chat_ctx=chat_ctx,
        )
```

The triage agent's tool returns a new `Agent` instance plus a transition message. LiveKit handles the handoff. The `chat_ctx` propagates so the new agent sees what the user already said.

That's the entire pattern. 30 lines.

## Going further

- **Telephony**: `lk sip` to wire a phone number. Buy a DID via LiveKit Phone Numbers in the Cloud dashboard, set up a dispatch rule, your agent picks up real calls. See [docs.livekit.io/sip](https://docs.livekit.io/sip/).
- **Vision**: Gemini Live and OpenAI's realtime models support video input. Pass a video track and ask the agent what it sees.
- **Avatars**: Tavus and Anam render a photorealistic talking head. Plug in via the avatar plugins.
- **Self-host**: if compliance requires it, run LiveKit Server yourself with the [self-hosting guide](https://docs.livekit.io/home/self-hosting/).

## Concepts introduced

- `metrics_collected` event for per-turn latency observability
- `metrics.UsageCollector` for session-level usage rollup
- `metrics.log_metrics(ev.metrics)` for structured metric logging
- `ctx.add_shutdown_callback` for end-of-session reporting
- `lk agent create` for one-command deploy to LiveKit Cloud Agents
- The pattern: observability before deploy, not after
