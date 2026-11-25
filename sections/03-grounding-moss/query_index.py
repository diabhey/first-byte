"""
Query the Moss index from the CLI to see what comes back for a given
question. Use this in Exercise 4 to inspect scores and tune `alpha`, `top_k`,
and `min_score` before wiring retrieval into the agent in Exercise 5.

Usage:
    uv run python sections/03-grounding-moss/query_index.py "What is HeartByte?"
    uv run python sections/03-grounding-moss/query_index.py "..." --top-k 3 --alpha 0.5 --min-score 0.6

Tip: re-run with different alpha values (0.0 keyword-only, 1.0 semantic-only,
0.8 course default) on the same query. The ordering of docs that come back is the
clearest demonstration of what alpha does.
"""

import argparse
import asyncio
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from moss import MossClient, QueryOptions

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
DEFAULT_MIN_SCORE = 0.5


async def main(
    query: str,
    top_k: int,
    alpha: float,
    min_score: float = DEFAULT_MIN_SCORE,
) -> None:
    project_id  = os.environ["MOSS_PROJECT_ID"]
    project_key = os.environ["MOSS_PROJECT_KEY"]
    index_name = os.environ["MOSS_INDEX_NAME"]

    print(
        f"index={index_name!r}  query={query!r}  top_k={top_k}  "
        f"alpha={alpha}  min_score={min_score}\n"
    )

    # Pre-load the index in-process, exactly like the agent does at startup.
    # Moss 1.24 queries only loaded local indexes; there is no cloud fallback.
    async with MossClient(project_id=project_id, project_key=project_key) as client:
        t0 = time.perf_counter()
        try:
            await client.load_index(index_name)
        except Exception as exc:
            raise RuntimeError(
                f"Could not load Moss index '{index_name}'. Run build_index.py "
                "and verify MOSS_PROJECT_ID, MOSS_PROJECT_KEY, and "
                "MOSS_INDEX_NAME before querying; there is no cloud fallback."
            ) from exc
        print(f"(index loaded in-process in {time.perf_counter() - t0:.2f}s)\n")

        t0 = time.perf_counter()
        results = await client.query(
            index_name,
            query,
            QueryOptions(top_k=top_k, alpha=alpha, min_score=min_score),
        )
        query_ms = (time.perf_counter() - t0) * 1000
    print(f"(query ran in {query_ms:.1f} ms in-process)\n")
    if not results.docs:
        print("(no results)")
        return

    for i, doc in enumerate(results.docs, 1):
        score = getattr(doc, "score", None)
        doc_id = getattr(doc, "id", None)
        head = f"[{i}]"
        if doc_id is not None:
            head += f" id={doc_id}"
        if score is not None:
            head += f" score={score:.4f}" if isinstance(score, float) else f" score={score}"
        print(head)
        print(f"    {doc.text}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="The user question, e.g. 'What is HeartByte?'")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--alpha", type=float, default=0.8)
    parser.add_argument(
        "--min-score",
        type=float,
        default=DEFAULT_MIN_SCORE,
        help="Drop results below this 0.0-1.0 relevance score (default: 0.5)",
    )
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be at least 1")
    if not 0.0 <= args.alpha <= 1.0:
        parser.error("--alpha must be between 0.0 and 1.0")
    if not 0.0 <= args.min_score <= 1.0:
        parser.error("--min-score must be between 0.0 and 1.0")
    asyncio.run(main(args.query, args.top_k, args.alpha, args.min_score))
