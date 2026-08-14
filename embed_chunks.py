"""
Embedding Generator — CreativeArts RAG Pipeline

Generates vector embeddings for chunked text and saves them as JSON.
Uses sentence-transformers (local, free) by default.

Usage:
    python embed_chunks.py

Output:
    ghana_creative_industry_embeddings.json
"""

import csv
import json
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent
CHUNKED_CSV = PROJECT_ROOT / "data" / "ghana_creative_industry_rag_chunked.csv"
OUTPUT_JSON = PROJECT_ROOT / "data" / "ghana_creative_industry_embeddings.json"
MODEL_NAME = "all-MiniLM-L6-v2"  # 384-dim, fast, local


# ---------------------------------------------------------------------------
# Load chunks
# ---------------------------------------------------------------------------
def load_chunks(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Generate embeddings
# ---------------------------------------------------------------------------
def generate_embeddings(chunks: list[dict], model_name: str = MODEL_NAME):
    """Generate embeddings using sentence-transformers.

    Returns:
        model_name, dimension, embeddings (list of lists)
    """
    from sentence_transformers import SentenceTransformer

    print(f"Loading model: {model_name}")
    model = SentenceTransformer(model_name)

    texts = [c["text"] for c in chunks]
    print(f"Encoding {len(texts)} chunks...")

    start = time.time()
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    elapsed = time.time() - start

    dim = embeddings.shape[1]
    print(f"Done in {elapsed:.1f}s — {dim}-dim vectors")

    return model_name, dim, embeddings.tolist()


# ---------------------------------------------------------------------------
# Build output
# ---------------------------------------------------------------------------
def build_output(chunks, model_name, dimension, embeddings):
    """Merge chunks with their embeddings into a JSON-serializable list."""
    results = []
    for chunk, emb in zip(chunks, embeddings):
        entry = {
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
        }
        results.append(entry)

    return {
        "model": model_name,
        "dimension": dimension,
        "total_chunks": len(results),
        "chunks": results,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    chunks = load_chunks(CHUNKED_CSV)
    print(f"Loaded {len(chunks)} chunks")

    model_name, dim, embeddings = generate_embeddings(chunks)
    output = build_output(chunks, model_name, dim, embeddings)

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved: {OUTPUT_JSON}")
    print(f"Model: {model_name}")
    print(f"Dimension: {dim}")
    print(f"Chunks: {output['total_chunks']}")

    # File size
    size_mb = OUTPUT_JSON.stat().st_size / (1024 * 1024)
    print(f"File size: {size_mb:.2f} MB")


if __name__ == "__main__":
    main()
