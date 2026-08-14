"""
RAG Text Chunker — CreativeArts Chatbot

Splits cleaned Q&A data into overlapping chunks suitable for embedding.
Uses text_chunker module for the core chunking logic.
"""

import csv
from pathlib import Path

from text_chunker import chunk_text

PROJECT_ROOT = Path(__file__).parent
INPUT_PATH = PROJECT_ROOT / "data" / "ghana_creative_industry_rag_cleaned.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "ghana_creative_industry_rag_chunked.csv"

CHUNK_SIZE = 500
CHUNK_OVERLAP_PCT = 0.15

# ---------------------------------------------------------------------------
# Load cleaned CSV
# ---------------------------------------------------------------------------
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Loaded {len(rows)} rows from cleaned CSV")

# ---------------------------------------------------------------------------
# Chunk each row
# ---------------------------------------------------------------------------
all_chunks: list[dict] = []
chunk_id = 0

for row in rows:
    text_to_chunk = row.get("context", "") or row.get("answer", "")
    if not text_to_chunk.strip():
        continue

    chunks = chunk_text(text_to_chunk, chunk_size=CHUNK_SIZE, overlap_pct=CHUNK_OVERLAP_PCT)

    for i, chunk in enumerate(chunks):
        chunk_id += 1
        all_chunks.append({
            "chunk_id": chunk_id,
            "source_id": row.get("id", ""),
            "category": row.get("category", ""),
            "sub_category": row.get("sub_category", ""),
            "topic": row.get("topic", ""),
            "question": row.get("question", ""),
            "tags": row.get("tags", ""),
            "source_confidence": row.get("source_confidence", ""),
            "chunk_index": i,
            "chunk_total": len(chunks),
            "text": chunk,
        })

print(f"Created {len(all_chunks)} chunks from {len(rows)} rows")

# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------
lengths = [c["text"] for c in all_chunks]
avg_len = sum(len(s) for s in lengths) / len(lengths) if lengths else 0
min_len = min(len(s) for s in lengths) if lengths else 0
max_len = max(len(s) for s in lengths) if lengths else 0
print(f"Chunk length — avg: {avg_len:.0f}, min: {min_len}, max: {max_len} chars")

# ---------------------------------------------------------------------------
# Save chunked CSV
# ---------------------------------------------------------------------------
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
fieldnames = [
    "chunk_id", "source_id", "category", "sub_category", "topic",
    "question", "tags", "source_confidence", "chunk_index",
    "chunk_total", "text",
]

with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(all_chunks)

print(f"\nSaved: {OUTPUT_PATH}")
print(f"Final: {len(all_chunks)} chunks, {len(fieldnames)} columns")
