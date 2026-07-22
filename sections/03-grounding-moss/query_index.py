"""
Query the Moss index from the CLI to see what comes back for a given
question. Use this in Exercise 5 to inspect scores and tune `alpha` and
`top_k` before wiring retrieval into the agent in Exercise 6.

Usage:
    uv run python sections/03-grounding-moss/query_index.py "What is HeartByte?"
    uv run python sections/03-grounding-moss/query_index.py "..." --top-k 3 --alpha 0.5

Tip: re-run with different alpha values (0.0 keyword-only, 1.0 semantic-only,
0.5 default) on the same query. The ordering of docs that come back is the
clearest demonstration of what alpha does.
"""

import argparse
import asyncio
import os
import time

from dotenv import load_dotenv
from moss import MossClient, QueryOptions

load_dotenv()


async def main(query: str, top_k: int, alpha: float) -> None:
    project_id  = os.environ["MOSS_PROJECT_ID"]
    project_key = os.environ["MOSS_PROJECT_KEY"]
    index_name  = os.environ.get("MOSS_INDEX_NAME", "firstbyte")

    client = MossClient(project_id=project_id, project_key=project_key)
    print(f"index={index_name!r}  query={query!r}  top_k={top_k}  alpha={alpha}\n")

    # Pre-load the index in-process, exactly like the agent does at startup.
    # Without this, query() falls back to a cloud lookup: slower, and a network
    # dependency this course exists to avoid.
    t0 = time.perf_counter()
    await client.load_index(index_name)
    print(f"(index loaded in-process in {time.perf_counter() - t0:.2f}s)\n")

    t0 = time.perf_counter()
    results = await client.query(index_name, query, QueryOptions(top_k=top_k, alpha=alpha))
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
    args = parser.parse_args()
    asyncio.run(main(args.query, args.top_k, args.alpha))
