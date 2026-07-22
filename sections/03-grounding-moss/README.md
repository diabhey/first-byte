# Section 3: Grounding with Moss

## Goal

Make the agent answer from real data. The agent in `agent.py` is the HeartByte orb: the same voice agent running live at [heartbyte.io](https://heartbyte.io). The knowledge base in `data/kb.json` mirrors the production data file. You are literally building the production agent.

## Step 1: Build the index

```bash
uv run python sections/03-grounding-moss/build_index.py
```

This creates a Moss index named `MOSS_INDEX_NAME` (from your `.env`) with the documents in `data/kb.json`. Re-runnable; it deletes the existing index first.

The script calls `client.create_index(name, docs, model_id="moss-minilm")`. The `model_id` argument selects the embedding model and is required by the Moss SDK. `moss-minilm` is the standard choice and what we use throughout this course. If you fork this script and drop the kwarg, the call will fail at runtime with a missing-argument error, not a typo: this is the most common gotcha students hit when they start tweaking.

## Step 2: Inspect the index from the CLI (Exercise 5)

Before wiring retrieval into the agent, see what Moss returns for a given question:

```bash
uv run python sections/03-grounding-moss/query_index.py "What is HeartByte?"
uv run python sections/03-grounding-moss/query_index.py "What is HeartByte?" --alpha 0.0
uv run python sections/03-grounding-moss/query_index.py "What is HeartByte?" --alpha 1.0
```

Re-run with `--alpha 0.0` (keyword-only) vs `--alpha 1.0` (semantic-only) on the same query — the doc ordering tells you what `alpha` does. The agent code uses `alpha=0.8` and `top_k=5` (see [`agent.py`](./agent.py)); experiment with smaller `top_k` to see how much context is enough.

## Step 3: Wire retrieval into the agent (Exercise 6)

Open [`agent_start.py`](./agent_start.py). The Moss client is already set up; `on_user_turn_completed` is your TODO. Implement it, then run:

```bash
uv run python sections/03-grounding-moss/agent_start.py dev
```

Connect via the [Agents Playground](https://agents-playground.livekit.io). Try:

- "What is HeartByte?"
- "Tell me about Abhi's three-phase method."
- "What's Abhi's background?"
- "How do I get in touch?"
- "What's the orb itself built on?"

Watch your terminal for `[moss] injected N results` lines. Each user turn triggers a Moss query before the LLM sees anything.

The finished reference is in [`agent.py`](./agent.py). Compare your implementation when done.

## What's the pattern

```python
async def on_user_turn_completed(self, turn_ctx, new_message):
    query = new_message.text_content
    results = await self._moss.query(self._index_name, query, QueryOptions(top_k=5, alpha=0.8))
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
