# Course Section 4: Grounding with Moss

Directory 3 of 4: `03-grounding-moss`.

## Goal

Inspect relevant and irrelevant retrieval before injecting context, then transfer the pattern to one piece of your own data.

`data/kb.json` is a curated teaching corpus about the instructor, selected projects, and the course demo. Build or reuse a course-owned Moss index from that file.

## Retrieval design boundary

This exercise uses ambient retrieval because the agent is a narrow knowledge agent and most turns may benefit from the same data. A model-selected retrieval tool can be better when only occasional turns need search; it avoids an unnecessary query but adds a model decision when retrieval is needed.

Moss reports low in-process query latency after an index is loaded. Treat that as a vendor result, not a universal benchmark. Index management, authentication, and SDK telemetry involve Moss services even though the query critical path runs against the loaded index.

## Build or reuse the index

Complete [root setup](../../README.md#setup), including `MOSS_*` values in `.env`.

```bash
uv run --frozen python sections/03-grounding-moss/build_index.py
```

The script creates `MOSS_INDEX_NAME` using `moss-minilm`. It is a remote write and can take unpredictable time, so do it during setup/rehearsal rather than while screen sharing.

If the script reports that the index already exists, run the first query in [Exercise 4](#exercise-4-inspect-relevance-and-rejection) and compare the result with the current `data/kb.json`. If the index has older or different data, choose a new `MOSS_INDEX_NAME` and build a fresh course index.

## Exercise 4: inspect relevance and rejection

The default retrieval settings are `top_k=5`, `alpha=0.8`, and `min_score=0.5`. If you set `MOSS_MIN_SCORE` for the agent, pass the same value to the query tool with `--min-score`.

```bash
uv run --frozen python sections/03-grounding-moss/query_index.py "Who is Abhimanyu Selvan?"
uv run --frozen python sections/03-grounding-moss/query_index.py "Who is Abhimanyu Selvan?" --alpha 0.0
uv run --frozen python sections/03-grounding-moss/query_index.py "Who is Abhimanyu Selvan?" --alpha 1.0
uv run --frozen python sections/03-grounding-moss/query_index.py "How do I tune a bicycle derailleur?" --min-score 0.5
```

- `alpha=0.0` is keyword-only retrieval.
- `alpha=1.0` is semantic-only retrieval.
- `min_score` filters weak matches; `(no results)` is a valid outcome.
- A top-ranked result is not necessarily relevant. Calibrate the threshold with known questions, paraphrases, and unrelated questions.

Record result count, top score/source, query time, and whether the outcome is acceptable in the [learner worksheet](../../LEARNER_WORKSHEET.md). Do not tune a threshold from one query.

## Exercise 5: hear a grounded answer

The live demo uses an agent with retrieval already enabled. Start it in voice mode.

```bash
lk agent console sections/03-grounding-moss/agent.py
```

1. Check for `[moss] retrieval on`. If a fresh checkout shows `[moss] retrieval off`, quit and either enable the hook in the optional exercise below or run the [completed Section 5 agent](../04-ship-it/README.md#exercise-6-observe-one-local-worker) against the same index.
2. Say “Who is Abhimanyu Selvan?” Check the transcript, look for `[moss] injected`, and compare the answer with the source found in Exercise 4. Speech recognition is biased toward Abhimanyu, Abhi, diabhey, and HeartByte.
3. Say “Tell me more about his work.” Check `[moss] searching` for the previous turn and `[moss] injected` for the retrieved context. Check the reply against the course documents.

```text
[moss] searching: ...
[timing] Moss retrieval hook: ...
[moss] injected N results
[latency] server_e2e=...ms response=COMPLETE preemptive=off | ...
```

The standalone bicycle query in Exercise 4 tests the no-match path. You can also ask it aloud to check whether the agent declines to answer an unsupported question. Inspect `[moss] searching` if the voice agent still finds documents: the previous turn can bring in matches about Abhimanyu.

If the index cannot load, startup fails with an actionable error. Moss 1.24 queries require a loaded local index; there is no cloud-query fallback. Check `MOSS_PROJECT_ID`, `MOSS_PROJECT_KEY`, `MOSS_INDEX_NAME`, and the build command.

Use the standalone Exercise 4 queries to check retrieval if audio is unavailable. Typed Console turns bypass this hook.

## Optional exercise: compare retrieval off and on

1. Start from a checkout with the exercise hook commented out. Verify `[moss] retrieval off`, say “Who is Abhimanyu Selvan?”, and press `q` after the reply.
2. Open [`agent.py`](./agent.py) and find `EXERCISE 5`. Uncomment the entire `on_user_turn_completed` method, from `async def` through its final `return`. Save the file.
3. Restart with the same command. Verify `[moss] retrieval on` and ask the same question aloud. Compare the injection log and the answer with the first run.

## The grounding pattern

The hook:

1. queries Moss with the completed user message plus the previous turn, so a follow-up such as “Tell me more about his work” still names the subject;
2. passes `MOSS_MIN_SCORE` to `QueryOptions` so Moss drops weaker matches;
3. formats accepted documents with source metadata;
4. adds them as a temporary system message to `turn_ctx`;
5. calls the base hook so the framework generates the reply.

Retrieved text is untrusted reference data, not instructions. Source metadata supports attribution, but the application still needs content governance and prompt-injection evaluation.

Grounded sections disable preemptive generation. Because the hook modifies `turn_ctx` on every turn, speculative ungrounded output would be discarded and generated again, increasing inference usage.

## Transfer task

Add or replace one document in `data/kb.json` with a small piece of your own domain data. Before rebuilding, write:

- one query that should retrieve it;
- one paraphrase;
- one unrelated query that should be rejected;
- the source label you expect to see.

Create a fresh scratch index with a new `MOSS_INDEX_NAME`, then run the three queries and record the evidence. To deliberately rebuild a scratch index you own under the same name, add `--replace` to the build command. It deletes the existing index first. If the service write would consume class time, finish this task after class.

## Concepts

- Ambient retrieval versus model-selected retrieval tools.
- `MossClient.query` with `QueryOptions(top_k, alpha, min_score)` for score-threshold filtering.
- Retrieval rejection and the no-result path.
- Temporary system context with source metadata.
- Grounding evidence comes from retrieval/injection logs and supplied data, not answer fluency.
