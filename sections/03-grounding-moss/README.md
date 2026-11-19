# Course Section 4: Grounding with Moss

[← Production UX](../02-production-ux/README.md) · [Course README](../../README.md) · Next: [Ship It →](../04-ship-it/README.md)

Folder `03-grounding-moss`. Answer from the knowledge base on every turn, without a network hop to a hosted search.

The documents are [`data/kb.json`](./data/kb.json). You build them into your own Moss index.

## Build the index

You need the `MOSS_*` values in `.env` from the [pre-class setup](../../README.md#pre-class-setup).

```bash
uv run python sections/03-grounding-moss/build_index.py
```

[`build_index.py`](./build_index.py) creates the index named by `MOSS_INDEX_NAME`. It refuses to overwrite one that exists. To rebuild on purpose:

```bash
uv run python sections/03-grounding-moss/build_index.py --replace
```

`--replace` deletes first. A name that does not start with `firstbyte-` asks you to type it to confirm.

## Exercise 4: inspect retrieval

```bash
uv run python sections/03-grounding-moss/query_index.py "What is HeartByte?"
uv run python sections/03-grounding-moss/query_index.py "What is HeartByte?" --alpha 0.0
uv run python sections/03-grounding-moss/query_index.py "What is HeartByte?" --alpha 1.0
```

[`query_index.py`](./query_index.py) only inspects results. The agent never runs it.

- `alpha 0.0` is keywords only. `alpha 1.0` is meaning only.
- The agent uses `top_k=5, alpha=0.8`.

## Exercise 5: wire the hook

> For voice, search every turn. Asking the model whether to search is another round trip. Search first, then let the model decide what is relevant.

Moss is already loaded in [`agent.py`](./agent.py). The `on_user_turn_completed` method is commented out.

1. Run it:

   ```bash
   lk agent console sections/03-grounding-moss/agent.py
   ```

2. **Say** “Who’s Abhi?” out loud. It should say it does not have that information. A typed turn (`ctrl+t`) never runs the hook.
3. Quit with `q`. Uncomment the whole `on_user_turn_completed` method (`Cmd + /` on macOS, `Ctrl + /` elsewhere).
4. Run it again, ask the same question, and watch for `[moss] injected N results`.

Loading the index does not ground anything. The hook does. It:

1. Queries Moss with what you just said.
2. Wraps up to five results with their source.
3. Adds them to `turn_ctx` as a system message.
4. Calls `super().on_user_turn_completed(...)` so the reply is generated.

The prompt treats retrieved text as reference data, never as instructions.

## Latency

The box is the same as [Hello Voice](../01-hello-voice/README.md#read-the-timing). When the hook runs, Moss time shows as a note on the handoff row. It is already inside that gap, so do not add it again.

Adding documents changes the context, so any reply that preemptive generation started early is thrown away and generated again with the documents.

## Concepts

- `on_user_turn_completed` for retrieval on every turn.
- `MossClient.query(..., QueryOptions(top_k, alpha))`.
- `ChatContext.add_message` to inject context.
- **Always search. Let the model decide what to use.**

---

[← Production UX](../02-production-ux/README.md) · [Course README](../../README.md) · Next: [Ship It →](../04-ship-it/README.md)
