# Section 2: Production voice UX

## Goal

Take the Section 1 agent from "demo" to "I can ship this." Two upgrades:

1. **Semantic turn detection** so the agent only speaks when you're actually done.
2. **Function tools** the LLM can call mid-conversation with production-grade error handling.

## Run

```bash
uv run python sections/02-production-ux/agent.py dev
```

## What changed from Section 1

### Turn detection

```python
turn_detection=MultilingualModel(),
```

This is LiveKit's open-weights end-of-utterance model. Instead of "stop after 800 ms of silence" (VAD-only), it uses the STT transcript to predict whether you've actually finished speaking. The difference is dramatic on phrases with natural pauses, like "Hmm, I think the order ID is... A100."

### Function tools

```python
@function_tool()
async def get_order_status(self, context: RunContext, order_id: str) -> dict:
    """Look up the current status of an order."""
    if order_id not in ORDERS:
        raise ToolError(f"I could not find order {order_id}.")
    return ORDERS[order_id]
```

Three things to notice:

- **Docstring is the LLM-facing description.** Keep it terse and accurate.
- **`ToolError`** speaks a graceful failure instead of crashing. The LLM gets the error text and explains it to the user.
- **`context.disallow_interruptions()`** in `place_order` blocks barge-in while a state-mutating call is in flight. Users won't accidentally double-submit by saying "uh huh" mid-call.

### False interruption tracking

```python
@session.on("agent_false_interruption")
def _on_false_interruption(ev) -> None:
    print("[false interruption] backchannel detected, agent continues")
```

When the user says "uh-huh" or "right" mid-reply, LiveKit detects the false interruption and the agent continues. You see this fire in your terminal logs.

## Things to try

- Test order IDs `A100`, `A101`, `A102` (work) and `Z999` (not found, gracefully spoken)
- Pause mid-sentence: "The order ID is... A100." Does the agent wait?
- Say "uh-huh" while the agent is talking. Does it keep going?
- Try `place_order` and try to interrupt it. You can't, by design.

## Concepts introduced

- `MultilingualModel` from `livekit-plugins-turn-detector`
- `@function_tool()` decorator and `RunContext`
- `ToolError` for spoken graceful failure
- `context.disallow_interruptions()` for state-mutating tools
- `agent_false_interruption` event for backchannel detection
