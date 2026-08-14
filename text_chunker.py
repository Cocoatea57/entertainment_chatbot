"""
text_chunker.py — Reusable text chunking for RAG pipelines.

Usage:
    from text_chunker import chunk_text, chunk_csv

    # Chunk a single text
    chunks = chunk_text("Long text here...", chunk_size=500, overlap=100)

    # Chunk an entire CSV
    chunks = chunk_csv("cleaned.csv", text_column="context", id_column="id")
"""

import csv
import re
from pathlib import Path


def split_into_sentences(text: str) -> list[str]:
    """Split text on sentence boundaries (. ! ? followed by space or end)."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap_pct: float = 0.15,
    min_chunk_size: int = 50,
) -> list[str]:
    """Split text into overlapping chunks, respecting sentence boundaries.

    Args:
        text: Input text to chunk.
        chunk_size: Target characters per chunk.
        overlap_pct: Overlap as a fraction of chunk_size (0.0–1.0).
                     e.g. 0.15 means 15% of chunk_size.
        min_chunk_size: Discard chunks shorter than this.

    Returns:
        List of text chunks.
    """
    overlap = int(chunk_size * overlap_pct)

    sentences = split_into_sentences(text)
    if not sentences:
        return []

    chunks: list[str] = []
    current_sentences: list[str] = []
    current_len = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        if current_len + sentence_len > chunk_size and current_sentences:
            chunks.append(" ".join(current_sentences))

            # Keep overlap from the end of current chunk
            overlap_sentences: list[str] = []
            overlap_len = 0
            for s in reversed(current_sentences):
                if overlap_len + len(s) > overlap:
                    break
                overlap_sentences.insert(0, s)
                overlap_len += len(s)

            current_sentences = overlap_sentences
            current_len = overlap_len

        current_sentences.append(sentence)
        current_len += sentence_len

    # Final chunk
    if current_sentences:
        final = " ".join(current_sentences)
        if len(final) >= min_chunk_size:
            chunks.append(final)

    return chunks


def chunk_csv(
    csv_path: str | Path,
    text_column: str = "context",
    id_column: str = "id",
    extra_columns: list[str] | None = None,
    chunk_size: int = 500,
    overlap_pct: float = 0.15,
) -> list[dict]:
    """Read a CSV and chunk the specified text column.

    Each chunk inherits metadata from its source row.

    Args:
        csv_path: Path to the cleaned CSV file.
        text_column: Column containing text to chunk.
        id_column: Column to use as source identifier.
        extra_columns: Additional columns to carry forward as metadata.
        chunk_size: Target characters per chunk.
        overlap_pct: Overlap as a fraction of chunk_size (0.0–1.0).

    Returns:
        List of dicts, each with chunk_id, source_id, metadata, and text.
    """
    if extra_columns is None:
        extra_columns = ["category", "sub_category", "topic", "question",
                         "tags", "source_confidence"]

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    all_chunks: list[dict] = []
    chunk_id = 0

    for row in rows:
        text = row.get(text_column, "")
        if not text.strip():
            continue

        chunks = chunk_text(text, chunk_size=chunk_size, overlap_pct=overlap_pct)

        for i, chunk in enumerate(chunks):
            chunk_id += 1
            entry = {
                "chunk_id": chunk_id,
                "source_id": row.get(id_column, ""),
                "chunk_index": i,
                "chunk_total": len(chunks),
                "text": chunk,
            }
            for col in extra_columns:
                if col in row:
                    entry[col] = row[col]
            all_chunks.append(entry)

    return all_chunks
