"""
RAG Dataset Cleaner — Ghana Creative Industry Chatbot
Handles CSV with unquoted commas in tags/answer fields.
"""

import csv
import re
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
INPUT_PATH = PROJECT_ROOT / "data" / "ghana_creative_industry_rag.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "ghana_creative_industry_rag_cleaned.csv"

VALID_CONFIDENCE = {"high", "medium", "low"}

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fix_row(raw_fields: list[str]) -> dict | None:
    """Reconstruct a row from potentially split CSV fields.

    Strategy: source_confidence is always the last field and is one of
    High/Medium/Low. We scan from the end to find it, then figure out
    where the tags begin (also scanned from the end, before confidence).
    """
    if len(raw_fields) < 8:
        return None

    # Last field should be source_confidence
    confidence = raw_fields[-1].strip()
    if confidence.lower() not in VALID_CONFIDENCE:
        return None

    # Everything before the last field, we need to find where tags start.
    # Tags are lowercase comma-separated words. The last tag item is right
    # before the confidence field. We scan backwards from the second-to-last
    # field to find the first field that looks like a tag (lowercase, no
    # sentence structure, short).
    inner = raw_fields[1:-1]  # strip id (first) and confidence (last)
    # inner[0] = category, inner[1] = sub_category, inner[2] = topic,
    # inner[3] = question, inner[4..] = answer + tags

    # The question always ends with '?'
    question_idx = None
    for idx, val in enumerate(inner):
        if val.strip().endswith("?"):
            question_idx = idx
            break

    if question_idx is None:
        # Fallback: assume standard 8-column layout
        question_idx = 4

    # Fields after question: first part is answer, then tags, then confidence
    # (confidence already extracted). Tags are short lowercase tokens.
    after_question = inner[question_idx + 1:]

    # Find where tags start: scan from end backwards, tags are short lowercase
    tag_start = len(after_question)  # default: no tags found
    for idx in range(len(after_question) - 1, -1, -1):
        val = after_question[idx].strip()
        # If it looks like a tag (lowercase, short, no periods)
        if (
            val
            and val == val.lower()
            and len(val) < 40
            and "." not in val
            and not val.startswith("http")
        ):
            tag_start = idx
        else:
            break

    answer_parts = after_question[:tag_start]
    tag_parts = after_question[tag_start:]

    return {
        "id": raw_fields[0].strip(),
        "category": clean_text(inner[0]) if len(inner) > 0 else "",
        "sub_category": clean_text(inner[1]) if len(inner) > 1 else "",
        "topic": clean_text(inner[2]) if len(inner) > 2 else "",
        "question": clean_text(inner[3]) if len(inner) > 3 else "",
        "answer": clean_text(", ".join(answer_parts)) if answer_parts else "",
        "tags": ", ".join(t.strip().lower() for t in tag_parts if t.strip()),
        "source_confidence": confidence.title(),
    }


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    raw_rows = [row for row in reader]

print(f"Loaded {len(raw_rows)} rows")

# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------
cleaned = []
for i, fields in enumerate(raw_rows):
    row = fix_row(fields)
    if row is None:
        print(f"  Skipping row {i + 1}: cannot parse")
        continue
    if not row["answer"]:
        print(f"  Skipping row {i + 1}: empty answer")
        continue
    cleaned.append(row)

print(f"Cleaned: {len(cleaned)} rows")

# ---------------------------------------------------------------------------
# Deduplicate by question
# ---------------------------------------------------------------------------
seen = set()
deduped = []
for row in cleaned:
    q = row["question"].lower()
    if q not in seen:
        seen.add(q)
        deduped.append(row)
    else:
        print(f"  Dup removed: {row['question'][:50]}...")

cleaned = deduped
print(f"After dedup: {len(cleaned)} rows")

# ---------------------------------------------------------------------------
# Build context for RAG embedding
# ---------------------------------------------------------------------------
for row in cleaned:
    parts = []
    if row["category"]:
        parts.append(f"Category: {row['category']}")
    if row["sub_category"]:
        parts.append(f"Sub-category: {row['sub_category']}")
    if row["topic"]:
        parts.append(f"Topic: {row['topic']}")
    header_line = " | ".join(parts)
    row["context"] = f"{header_line}\n{row['answer']}"

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
fieldnames = ["id", "category", "sub_category", "topic", "question", "answer", "tags", "source_confidence", "context"]

with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(cleaned)

print(f"\nSaved: {OUTPUT_PATH}")
print(f"Final: {len(cleaned)} rows x {len(fieldnames)} columns")

# Verify
print("\n--- Sample rows ---")
for row in cleaned[:3]:
    print(f"\n  Q: {row['question']}")
    print(f"  A: {row['answer'][:120]}...")
    print(f"  Tags: {row['tags']}")
    print(f"  Confidence: {row['source_confidence']}")
