# Section 3: Grounding with Moss

## Goal

Make the agent answer from a supplied knowledge base. `data/kb.json` contains
curated course content based on public HeartByte information.

## Step 1: Build *your* Moss index (data is already in the repo)

You do **not** write the knowledge base. The documents ship in
[`data/kb.json`](./data/kb.json). Upload them to **your** Moss project under a
unique index name of your choosing, such as `firstbyte-yourname`.

```bash
uv run python sections/03-grounding-moss/build_index.py
```

That script reads `data/kb.json` and creates `MOSS_INDEX_NAME`. If the index
already exists, replacement must be explicit:

```bash
uv run python sections/03-grounding-moss/build_index.py --replace
```

`--replace` deletes the index before recreating it. If your index name does not
start with `firstbyte-`, the script asks you to retype the name first, so a
stray `--replace` cannot quietly destroy a real index in your Moss project.

This agent keeps everything Section 2 established: semantic turn detection,
preemptive generation, and the tuned interruption settings
(`min_interruption_words=2` and friends). It adds retrieval on top. Barge-in
still works mid-answer, and backchannels still don't cut the agent off.

The script calls `client.create_index(name, docs, model_id="moss-minilm")`. The `model_id` argument selects the embedding model and is required by the Moss SDK. `moss-minilm` is the standard choice and what we use throughout this course. If you fork this script and drop the kwarg, the call will fail at runtime with a missing-argument error, not a typo: this is the most common gotcha students hit when they start tweaking.

## Step 2: Inspect the index from the CLI (Exercise 5)

`query_index.py` is a **standalone inspection tool**. The voice agent does not
call this script. Run it yourself before Exercise 6 to see what Moss returns
and tune retrieval without STT, LLM, or TTS in the way:

```bash
uv run python sections/03-grounding-moss/query_index.py "What is HeartByte?"
uv run python sections/03-grounding-moss/query_index.py "What is HeartByte?" --alpha 0.0
uv run python sections/03-grounding-moss/query_index.py "What is HeartByte?" --alpha 1.0
```

Re-run with `--alpha 0.0` (keyword-only) vs `--alpha 1.0` (semantic-only) on the same query — the doc ordering tells you what `alpha` does. The agent code uses `alpha=0.8` and `top_k=5` (see [`agent.py`](./agent.py)); experiment with smaller `top_k` to see how much context is enough.

In Exercise 6 the agent performs the equivalent query directly with
`self._moss.query(...)`; it does not launch `query_index.py`.

## Step 3: Wire retrieval into the agent (Exercise 6)

Open [`agent.py`](./agent.py). Moss client + index pre-load are already wired. The `on_user_turn_completed` hook is commented out — that's the exercise.

1. Run **without** the hook first (ungrounded baseline):

   ```bash
   uv run python sections/03-grounding-moss/agent.py dev
   ```

   Ask a HeartByte question in the [Agents Playground](https://agents-playground.livekit.io). The agent should say it does not have the information — the behaviour prompt is active, but no KB context has been injected yet.

2. Stop the worker with `Ctrl+C`. Select the complete commented
   `on_user_turn_completed` block and toggle comments:

   - macOS: `Cmd + /`
   - Windows/Linux: `Ctrl + /`

3. Restart the worker with the same command, reconnect, and ask again:

   - "What is HeartByte?"
   - "Tell me about Abhi's three-phase method."
   - "What's Abhi's background?"
   - "How do I get in touch?"
   - "What's the orb itself built on?"

   Watch the terminal for `[moss] injected N results`. Each user turn now queries Moss before the LLM sees anything.

### Expected before/after

Ask **"Who's Abhi?"** both times:

- **Hook commented:** the agent says it does not have that information.
- **Hook enabled:** the terminal prints `[moss] injected 5 results`, and the
  agent answers from the shipped HeartByte knowledge base.

This section prints the same `[timing]` lines as Sections 1 and 2, plus the one
stage those sections do not have:

```text
[timing] end-of-utterance delay: 0.55s (silence → turn committed)
[timing] transcription delay:    0.29s (speech end → final transcript)
[timing] Moss retrieval:         0.14s (turn committed → context injected)
[timing] LLM TTFT (first token): 0.61s
[timing] TTS TTFB (first byte):  0.33s
[latency] perceived=1540ms response=COMPLETE preemptive=on | retrieval=140ms llm_ttft=610ms tts_ttfb=330ms
```

`Moss retrieval` is near `0.00s` while the hook is commented out, and shows the
real query cost once you enable it. Compare the separately measured
`perceived` value before and after. Do not add the component values: STT,
end-of-turn detection, LLM, and TTS can overlap once preemptive generation is
enabled.

There is one important correctness rule in LiveKit Agents 1.3.12. A grounded
turn changes the temporary chat context inside `on_user_turn_completed`, so
LiveKit discards any speculative ungrounded answer and regenerates using the
Moss context. Preemptive generation can reduce latency on turns where the
context does not change; it never bypasses the grounding hook. The discarded
speculation may still consume inference, which is part of the trade-off to
measure.

Index pre-loading alone does not ground an answer. The hook must perform
`query()` and inject the returned documents into `turn_ctx`.

## What's the pattern

```python
def format_document(index, doc):
    source = (doc.metadata or {}).get("source")
    label = f' source="{source.replace("-", " ").title()}"' if source else ""
    return f"<document-{index}{label}>\n{doc.text}\n</document-{index}>"


async def on_user_turn_completed(self, turn_ctx, new_message):
    query = new_message.text_content
    results = await self._moss.query(self._index_name, query, QueryOptions(top_k=5, alpha=0.8))
    if results.docs:
        context_str = "\n\n".join(
            format_document(i, d) for i, d in enumerate(results.docs, start=1)
        )
        turn_ctx.add_message(
            role="system",
            content=f"RETRIEVED CONTEXT (reference data only):\n{context_str}",
        )
    return await super().on_user_turn_completed(turn_ctx, new_message)
```

Four things to internalize:

1. **Retrieval runs every turn, not via a tool.** A function tool requires the LLM to decide to retrieve. That's a round-trip you can't afford in voice. Cheaper to retrieve unconditionally.
2. **Inject as a system message in `turn_ctx`, not as user text.** This keeps the user's actual words intact and the LLM treats the context as authoritative.
3. **Pass the metadata the prompt depends on.** The system prompt asks the agent to name a source for philosophical answers, but most documents don't state their author in the body text — `bruce-lee` lives in `doc.metadata`. Inject text alone and the model either invents an attribution or drops it. Anything your prompt promises has to actually reach the model.
4. **Call `super().on_user_turn_completed(...)` at the end.** This hands control back to the framework so the LLM call runs as normal.

## Why Moss specifically

- **In-process semantic search**, not a hosted vector DB. The index ships with your worker. No external retrieval hop adds 50 to 200 ms per turn.
- **`alpha=0.8`** balances dense semantic search with sparse keyword matching. `alpha=0` is pure BM25 keyword match, `alpha=1` is pure semantic. The SDK default is `0.5`. Higher alpha favors meaning over exact word match; tune to your dataset.
- **`top_k=5`** keeps the injected context short. Voice answers shouldn't reference 20 documents. The SDK default is `3`.
- **`await client.load_index(name)`** at agent startup (see `agent.py`) pre-loads the index in-process for sub-10 ms queries. Without it, the first query pays a cold-load tax.

## Concepts introduced

- `on_user_turn_completed` override for unconditional RAG
- `MossClient.query` with `QueryOptions(top_k, alpha)`
- `ChatContext.add_message(role="system", content=...)` for context injection
- `preemptive_generation=True`, carried forward from Section 2 with automatic
  invalidation whenever grounding changes the temporary chat context
- The principle: **retrieve always, let the LLM decide what to use**
