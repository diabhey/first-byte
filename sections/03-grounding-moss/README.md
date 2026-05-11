# Section 3: Grounding with Moss

## Goal

Make the agent answer from real data. The agent in `agent.py` plays the voice assistant for **Compass Coffee**, a fictional single-origin coffee subscription service. The knowledge base is in `data/kb.json`.

## Step 1: Build the index

```bash
uv run python sections/03-grounding-moss/build_index.py
```

This creates a Moss index named `MOSS_INDEX_NAME` (from your `.env`) with the 15 documents in `data/kb.json`. Re-runnable; it deletes the existing index first.

The script calls `client.create_index(name, docs, model_id="moss-minilm")`. The `model_id` argument selects the embedding model and is required by the Moss SDK. `moss-minilm` is the standard choice and what we use throughout this course. If you fork this script and drop the kwarg, the call will fail at runtime with a missing-argument error, not a typo: this is the most common gotcha students hit when they start tweaking.

## Step 2: Run the grounded agent

```bash
uv run python sections/03-grounding-moss/agent.py dev
```

Connect via the [Agents Playground](https://agents-playground.livekit.io). Try:

- "What's your refund policy?"
- "Tell me about your Ethiopian coffee."
- "Do you ship to the US?"
- "Can I pause my subscription?"
- "What's the difference between the Roaster and Cellar tiers?"

Watch your terminal for `[moss] injected N results` lines. Each user turn triggers a Moss query before the LLM sees anything.

## What's the pattern

```python
async def on_user_turn_completed(self, turn_ctx, new_message):
    query = new_message.text_content
    results = await self._moss.query(self._index_name, query, QueryOptions(top_k=5))
    if results.docs:
        context_str = "\n".join(f"- {d.text}" for d in results.docs)
        turn_ctx.add_message(
            role="system",
            content=f"Relevant context:\n{context_str}",
        )
    return await super().on_user_turn_completed(turn_ctx, new_message)
```

Three things to internalize:

1. **Retrieval runs every turn, not via a tool.** A function tool requires the LLM to decide to retrieve. That's a round-trip you can't afford in voice. Cheaper to retrieve unconditionally.
2. **Inject as a system message in `turn_ctx`, not as user text.** This keeps the user's actual words intact and the LLM treats the context as authoritative.
3. **Call `super().on_user_turn_completed(...)` at the end.** This hands control back to the framework so the LLM call runs as normal.

## Why Moss specifically

- **In-process semantic search**, not a hosted vector DB. The index ships with your worker. No external retrieval hop adds 50 to 200 ms per turn.
- **`alpha=0.8`** balances dense semantic search with sparse keyword matching. `alpha=0` is pure BM25 keyword match, `alpha=1` is pure semantic. The SDK default is `0.5`. Higher alpha favors meaning over exact word match; tune to your dataset.
- **`top_k=5`** keeps the injected context short. Voice answers shouldn't reference 20 documents. The SDK default is `3`.
- **`await client.load_index(name)`** at agent startup (see `agent.py`) pre-loads the index in-process for sub-10 ms queries. Without it, the first query pays a cold-load tax.

## Concepts introduced

- `on_user_turn_completed` override for unconditional RAG
- `MossClient.query` with `QueryOptions(top_k, alpha)`
- `ChatContext.add_message(role="system", content=...)` for context injection
- The principle: **retrieve always, let the LLM decide what to use**
