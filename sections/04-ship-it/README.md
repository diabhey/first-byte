# Section 4: Ship it

## Goal

Wire production observability, then deploy the agent to LiveKit Cloud Agents with a single command. By the end of this section your agent runs on the public internet against LiveKit's global network and infrastructure.

## Step 1: Run locally with metrics

```bash
uv run python sections/04-ship-it/agent.py dev
```

Connect via the [Agents Playground](https://agents-playground.livekit.io) and have a conversation. Watch your terminal:

- **`[metrics] turn e2e_latency=...`** logs fire once per assistant turn, sourced from `ChatMessage.metrics` on the `conversation_item_added` event. STT first byte, LLM time-to-first-token, TTS first audio chunk, and end-to-end are all here. This is your latency budget audit in real time.
- **`[usage] ...`** logs fire whenever `session_usage_updated` ticks, and once more on shutdown via `add_shutdown_callback` for the final cumulative tally. Tokens in/out per provider and audio durations.

```python
@session.on("conversation_item_added")
def _on_item(ev: ConversationItemAddedEvent) -> None:
    if not isinstance(ev.item, ChatMessage):
        return
    m = ev.item.metrics
    if not m:
        return
    e2e = m.get("e2e_latency")
    if ev.item.role == "assistant" and e2e is not None:
        print(f"[metrics] turn e2e_latency={e2e:.3f}s metrics={m}")

@session.on("session_usage_updated")
def _on_usage(ev: SessionUsageUpdatedEvent) -> None:
    for usage in ev.usage.model_usage:
        print(f"[usage] {usage.provider}/{usage.model}: {usage}")

ctx.add_shutdown_callback(_log_session_summary)
```

> Earlier versions of `livekit-agents` exposed a session-level `metrics_collected` event for this. That event is deprecated. The current pattern is `conversation_item_added` for per-turn latency and `session_usage_updated` for usage rollup.

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

- **Custom visitor-facing frontend**: the Agents Playground is for development. To put a real user in front of your agent on your own site, you need three things: a token endpoint (Node, Python, or Edge function that mints a LiveKit access token), the [LiveKit JS SDK](https://docs.livekit.io/reference/client-sdk-js/) (`livekit-client`) to join a room from the browser, and a UI that handles mic permissions and the connecting/listening/speaking states. For a polished feel, drive a canvas or SVG animation from the agent's audio track using the Web Audio `AnalyserNode`: a simple state machine (`idle → connecting → listening → thinking → speaking`) plus per-frame RMS sampling gives you the audio-reactive orb pattern most production voice products ship.
- **Telephony**: `lk sip` to wire a phone number. Buy a DID via LiveKit Phone Numbers in the Cloud dashboard, set up a dispatch rule, your agent picks up real calls. See [docs.livekit.io/sip](https://docs.livekit.io/sip/).
- **Vision**: Gemini Live and OpenAI's realtime models support video input. Pass a video track and ask the agent what it sees.
- **Avatars**: Tavus and Anam render a photorealistic talking head. Plug in via the avatar plugins.
- **Self-host**: if compliance requires it, run LiveKit Server yourself with the [self-hosting guide](https://docs.livekit.io/home/self-hosting/).

## Concepts introduced

- `conversation_item_added` event + `ChatMessage.metrics` for per-turn latency observability
- `session_usage_updated` event + `session.usage` for cumulative model-usage rollup
- `ctx.add_shutdown_callback` for end-of-session reporting
- `lk agent create` for one-command deploy to LiveKit Cloud Agents
- The pattern: observability before deploy, not after
