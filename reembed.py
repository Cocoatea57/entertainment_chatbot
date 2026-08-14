"""
Re-Embed Dataset — CreativeArts RAG Pipeline

Re-embeds the chunked CSV using OpenAI's text-embedding-3-small model.
Run once after setup to generate the embeddings JSON.

Usage:
    python reembed.py

Requires:
    OPENAI_API_KEY environment variable
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
CHUNKED_CSV = PROJECT_ROOT / "data" / "ghana_creative_industry_rag_chunked.csv"
OUTPUT_JSON = PROJECT_ROOT / "data" / "ghana_creative_industry_openai_embeddings.json"
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 50  # OpenAI allows up to 2048 per request


def load_chunks(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def embed_chunks(chunks: list[dict], client: OpenAI) -> list[list[float]]:
    """Embed all chunks in batches."""
    texts = [c["text"] for c in chunks]
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        all_embeddings.extend([item.embedding for item in response.data])
        print(f"  Embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)} chunks")
        if i + BATCH_SIZE < len(texts):
            time.sleep(0.5)  # respect rate limits

    return all_embeddings


def build_output(chunks, dimension, embeddings):
    results = []
    for chunk, emb in zip(chunks, embeddings):
        results.append({
            "chunk_id": int(chunk["chunk_id"]),
            "source_id": chunk["source_id"],
            "category": chunk.get("category", ""),
            "sub_category": chunk.get("sub_category", ""),
            "topic": chunk.get("topic", ""),
            "question": chunk.get("question", ""),
            "tags": chunk.get("tags", ""),
            "source_confidence": chunk.get("source_confidence", ""),
            "chunk_index": int(chunk.get("chunk_index", 0)),
            "chunk_total": int(chunk.get("chunk_total", 1)),
            "text": chunk["text"],
            "embedding": emb,
        })

    return {
        "model": EMBEDDING_MODEL,
        "dimension": dimension,
        "total_chunks": len(results),
        "chunks": results,
    }


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set. Add it to your .env file.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    chunks = load_chunks(CHUNKED_CSV)
    print(f"Loaded {len(chunks)} chunks from {CHUNKED_CSV}")

    print(f"Embedding with {EMBEDDING_MODEL}...")
    embeddings = embed_chunks(chunks, client)

    dimension = len(embeddings[0])
    output = build_output(chunks, dimension, embeddings)

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    size_mb = OUTPUT_JSON.stat().st_size / (1024 * 1024)
    print(f"\nSaved: {OUTPUT_JSON}")
    print(f"Model: {EMBEDDING_MODEL}")
    print(f"Dimension: {dimension}")
    print(f"Chunks: {output['total_chunks']}")
    print(f"File size: {size_mb:.2f} MB")


if __name__ == "__main__":
    main()
