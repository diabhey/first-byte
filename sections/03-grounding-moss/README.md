# Section 3: Grounding with Moss

## Goal

**Ground every answer in the supplied knowledge base without adding a separate hosted retrieval hop.**

`data/kb.json` contains the curated HeartByte course data. Students build the same documents into their own Moss index.

## Build and inspect the index

Complete the [root setup and pre-flight check](../../README.md#pre-class-setup) first, including the `MOSS_*` values in `.env`.

### 1. Build the index

```bash
uv run python sections/03-grounding-moss/build_index.py
```

The script creates the index named by `MOSS_INDEX_NAME` using `moss-minilm`. To deliberately replace an existing index:

```bash
uv run python sections/03-grounding-moss/build_index.py --replace
```

`--replace` deletes first. Index names beginning with `firstbyte-` are treated as course scratch indexes; other names require typed confirmation.

### 2. Inspect retrieval before adding it to voice

```bash
uv run python sections/03-grounding-moss/query_index.py "What is HeartByte?"
uv run python sections/03-grounding-moss/query_index.py "What is HeartByte?" --alpha 0.0
uv run python sections/03-grounding-moss/query_index.py "What is HeartByte?" --alpha 1.0
```

`query_index.py` is an inspection tool—the voice agent never launches it.

- `alpha=0.0`: keyword-only retrieval.
- `alpha=1.0`: semantic-only retrieval.
- The agent uses `top_k=5, alpha=0.8`.

## Key takeaway
>
> “For voice, retrieval runs on every turn. Asking an LLM whether to retrieve creates another decision round-trip. We retrieve first, then let the model decide what is relevant.”

## Exercise: wire the hook

Moss setup and index preloading already exist in [`agent.py`](./agent.py). The `on_user_turn_completed` method is commented out.

1. Run the ungrounded baseline:

   ```bash
   uv run python sections/03-grounding-moss/agent.py dev
   ```

2. Ask “Who’s Abhi?” The agent has no injected knowledge-base context, so it should say it does not have that information.
3. Stop the worker. Uncomment the complete `on_user_turn_completed` block (`Cmd + /` on macOS; `Ctrl + /` elsewhere).
4. Restart, ask the same question, and watch for `[moss] injected N results`.

```text
[timing] Moss retrieval: ...
[latency] perceived=...ms ... retrieval=...ms
```

> **Important:** index preloading does not ground an answer. The hook must query Moss and add its results to the temporary `turn_ctx`.

## The pattern

The hook:

1. Queries Moss from the completed user message.
2. Wraps up to five results, including each document’s source metadata.
3. Adds them as a **system message** to `turn_ctx`.
4. Calls `super().on_user_turn_completed(...)` so the framework generates the reply.

The prompt treats retrieved content as reference data, not instructions. Including metadata matters: the prompt can only attribute claims to sources it receives.

## Latency and correctness

This section carries forward semantic turn detection, barge-in tuning, and preemptive generation.

- Component timings may overlap; compare the separately measured `perceived` latency before and after grounding.
- Changing `turn_ctx` with the retrieval results invalidates speculative ungrounded output, so LiveKit regenerates the answer with the context. That preserves grounding but may spend extra inference.

## Concepts

- `on_user_turn_completed` for unconditional retrieval.
- `MossClient.query(..., QueryOptions(top_k, alpha))`.
- System-message context injection with `ChatContext.add_message`.
- **Retrieve always; let the LLM decide what to use.**
