"""
ChromaDB Vector Store — CreativeArts RAG Pipeline

Uses OpenAI embeddings (text-embedding-3-small) for lightweight deployment.
Provides ingest, search, and retrieve functions for RAG.

Usage:
    python vector_store.py ingest
    python vector_store.py search "What is Ghallywood?"
"""

import json
import os
import sys
from pathlib import Path

import chromadb
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration (relative to project root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent
EMBEDDINGS_JSON = PROJECT_ROOT / "data" / "ghana_creative_industry_openai_embeddings.json"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "creative_arts"
EMBEDDING_MODEL = "text-embedding-3-small"

# ---------------------------------------------------------------------------
# Cached globals (loaded once)
# ---------------------------------------------------------------------------
_client = None
_collection = None
_openai_client = None


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set — needed for embeddings")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def _embed(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using OpenAI's embedding API."""
    client = _get_openai_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_collection(COLLECTION_NAME)
    return _collection


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------
def ingest():
    """Load pre-computed OpenAI embeddings from JSON and store in ChromaDB."""
    print(f"Loading embeddings from {EMBEDDINGS_JSON}")
    with open(EMBEDDINGS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = data["chunks"]
    print(f"Loaded {len(chunks)} chunks (dim={data['dimension']})")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    print(f"Created collection '{COLLECTION_NAME}'")

    ids, documents, embeddings, metadatas = [], [], [], []

    for chunk in chunks:
        ids.append(f"chunk_{chunk['chunk_id']}")
        documents.append(chunk["text"])
        embeddings.append(chunk["embedding"])
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
            embeddings=embeddings[i:end],
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

    query_embedding = _embed([query])

    results = collection.query(
        query_embeddings=query_embedding,
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

    query_embedding = _embed([query])

    results = collection.query(
        query_embeddings=query_embedding,
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

    query_embedding = _embed([query])

    results = collection.query(
        query_embeddings=query_embedding,
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
