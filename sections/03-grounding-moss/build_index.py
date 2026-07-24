"""
Build the Moss index for Section 3.

Reads sections/03-grounding-moss/data/kb.json and creates (or replaces) a
Moss index with the documents inside. Run once before Exercise 5:

    uv run python sections/03-grounding-moss/build_index.py

Use --replace to explicitly delete and recreate an existing scratch index.
"""

import argparse
import asyncio
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from moss import DocumentInfo, MossClient

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = Path(__file__).parent / "data" / "kb.json"
MOSS_INDEX_PLACEHOLDER = "firstbyte-your-handle"
MOSS_INDEX_PATTERN = re.compile(r"firstbyte-[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?")

load_dotenv(REPO_ROOT / ".env")


def validate_index_name(index_name: str) -> str:
    """Allow this destructive course script to touch scratch indexes only."""
    index_name = index_name.strip()
    if (
        index_name == MOSS_INDEX_PLACEHOLDER
        or MOSS_INDEX_PATTERN.fullmatch(index_name) is None
    ):
        raise ValueError(
            "MOSS_INDEX_NAME must be a unique course index such as "
            "'firstbyte-yourname'."
        )
    return index_name


async def main(*, replace: bool = False) -> None:
    project_id = os.environ["MOSS_PROJECT_ID"]
    project_key = os.environ["MOSS_PROJECT_KEY"]
    index_name = validate_index_name(os.environ["MOSS_INDEX_NAME"])

    raw_docs = json.loads(DATA_PATH.read_text())
    docs = [
        DocumentInfo(id=d["id"], text=d["text"], metadata=d.get("metadata", {}))
        for d in raw_docs
    ]

    client = MossClient(project_id=project_id, project_key=project_key)

    existing_indexes = await client.list_indexes()
    index_exists = any(index.name == index_name for index in existing_indexes)
    if index_exists and not replace:
        raise RuntimeError(
            f"Index '{index_name}' already exists. Re-run with --replace "
            "only if you intend to delete and recreate it."
        )
    if index_exists:
        await client.delete_index(index_name)
        print(f"Deleted existing index '{index_name}'")

    print(f"Creating index '{index_name}' with {len(docs)} documents...")
    result = await client.create_index(index_name, docs, model_id="moss-minilm")
    print(
        f"Done: job={result.job_id}, index={result.index_name}, "
        f"docs={result.doc_count}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete and recreate the configured scratch index if it exists.",
    )
    args = parser.parse_args()
    asyncio.run(main(replace=args.replace))
