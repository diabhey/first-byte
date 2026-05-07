"""
Build the Moss index for Section 3.

Reads sections/03-grounding-moss/data/kb.json and creates (or replaces) a
Moss index with the documents inside. Run once before Exercise 5:

    uv run python sections/03-grounding-moss/build_index.py

Re-runnable: deletes the existing index first.
"""

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from moss import DocumentInfo, MossClient

load_dotenv()


DATA_PATH = Path(__file__).parent / "data" / "kb.json"


async def main() -> None:
    project_id = os.environ["MOSS_PROJECT_ID"]
    project_key = os.environ["MOSS_PROJECT_KEY"]
    index_name = os.environ.get("MOSS_INDEX_NAME", "firstbyte")

    raw_docs = json.loads(DATA_PATH.read_text())
    docs = [
        DocumentInfo(id=d["id"], text=d["text"], metadata=d.get("metadata", {}))
        for d in raw_docs
    ]

    client = MossClient(project_id=project_id, project_key=project_key)

    # Delete existing index if it exists, then recreate.
    try:
        await client.delete_index(index_name)
        print(f"Deleted existing index '{index_name}'")
    except Exception:
        pass

    print(f"Creating index '{index_name}' with {len(docs)} documents...")
    result = await client.create_index(index_name, docs, model_id="moss-minilm")
    print(
        f"Done: job={result.job_id}, index={result.index_name}, "
        f"docs={result.doc_count}"
    )


if __name__ == "__main__":
    asyncio.run(main())
