"""
ChromaDB Vector Store — CreativeArts RAG Pipeline

Uses ChromaDB's built-in embedding function (onnxruntime + MiniLM).
Provides ingest, search, and retrieve functions for RAG.

Usage:
    python vector_store.py ingest
    python vector_store.py search "What is Ghallywood?"
"""

import csv
import json
import os
import sys
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

# ---------------------------------------------------------------------------
# Configuration (relative to project root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent
CHUNKED_CSV = PROJECT_ROOT / "data" / "ghana_creative_industry_rag_chunked.csv"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "creative_arts"

_default_ef = embedding_functions.DefaultEmbeddingFunction()

# ---------------------------------------------------------------------------
# Cached globals (loaded once)
# ---------------------------------------------------------------------------
_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        try:
            _collection = _client.get_collection(
                COLLECTION_NAME, embedding_function=_default_ef
            )
        except Exception:
            _collection = _client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
                embedding_function=_default_ef,
            )
    return _collection


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------
def ingest():
    """Load chunked CSV and store in ChromaDB using local embeddings."""
    print(f"Loading chunks from {CHUNKED_CSV}")
    with open(CHUNKED_CSV, "r", encoding="utf-8") as f:
        chunks = list(csv.DictReader(f))

    print(f"Loaded {len(chunks)} chunks")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
        embedding_function=_default_ef,
    )
    print(f"Created collection '{COLLECTION_NAME}'")

    ids, documents, metadatas = [], [], []

    for chunk in chunks:
        ids.append(f"chunk_{chunk['chunk_id']}")
        documents.append(chunk["text"])
        metadatas.append({
            "source_id": str(chunk.get("source_id", "")),
            "category": chunk.get("category", ""),
            "sub_category": chunk.get("sub_category", ""),
            "topic": chunk.get("topic", ""),
            "question": chunk.get("question", ""),
            "tags": chunk.get("tags", ""),
            "source_confidence": chunk.get("source_confidence", ""),
        })

    batch_size = 100
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        collection.upsert(
            ids=ids[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end],
        )
        print(f"  Upserted {end}/{len(ids)} chunks")

    print(f"\nDone. {len(ids)} chunks stored in {CHROMA_DIR}")


# ---------------------------------------------------------------------------
# Search (returns raw ChromaDB results)
# ---------------------------------------------------------------------------
def search(query: str, n_results: int = 5):
    """Search the vector store and print results."""
    collection = _get_collection()

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    print(f"\nQuery: {query}")
    print(f"Results ({len(results['ids'][0])}):\n")

    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    )):
        similarity = 1 - dist
        print(f"--- Result {i + 1} (similarity: {similarity:.4f}) ---")
        print(f"  Topic: {meta.get('topic', 'N/A')}")
        print(f"  Category: {meta.get('category', 'N/A')}")
        print(f"  Text: {doc[:200]}...")
        print()

    return results


# ---------------------------------------------------------------------------
# Retrieve (returns context string for LLM)
# ---------------------------------------------------------------------------
def retrieve(query: str, n_results: int = 3) -> str:
    """Retrieve relevant context for a query.

    Returns a formatted string of the top matching chunks,
    suitable for injection into an LLM prompt.
    """
    collection = _get_collection()

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    context_parts = []
    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    )):
        similarity = 1 - dist
        topic = meta.get("topic", "")
        category = meta.get("category", "")
        context_parts.append(
            f"[Source {i + 1}: {category} > {topic} | relevance: {similarity:.2f}]\n{doc}"
        )

    return "\n\n".join(context_parts)


# ---------------------------------------------------------------------------
# Retrieve sources (returns structured list for API/frontend)
# ---------------------------------------------------------------------------
def retrieve_sources(query: str, n_results: int = 3) -> list[dict]:
    """Retrieve relevant sources for a query.

    Returns a list of dicts with topic, category, relevance, and text,
    suitable for returning to the frontend.
    """
    collection = _get_collection()

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    sources = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        similarity = round(1 - dist, 4)
        sources.append({
            "topic": meta.get("topic", ""),
            "category": meta.get("category", ""),
            "sub_category": meta.get("sub_category", ""),
            "relevance": similarity,
            "text": doc[:300],
        })

    return sources


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python vector_store.py [ingest|search] [query]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "ingest":
        ingest()
    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: python vector_store.py search 'your query here'")
            sys.exit(1)
        search(sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
