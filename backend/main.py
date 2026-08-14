"""
CreativeArts API — FastAPI backend with RAG retrieval.

Provides a /chat endpoint that:
1. Retrieves relevant context from ChromaDB
2. Sends context + user query to OpenRouter LLM
3. Returns the response with RAG sources
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI

from vector_store import retrieve, retrieve_sources

load_dotenv(Path(__file__).parent.parent / ".env")

app = FastAPI(title="CreativeArts API")

FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1"
MODEL = "openai/gpt-4o-mini"

RAG_SYSTEM_PROMPT = """You are CreativeArts, a knowledgeable assistant specializing in Ghana's creative industry.

You answer questions about music, film, fashion, visual arts, comedy, dance, digital content, and the creative economy in Ghana. You always cite Ghanaian institutions, laws, and figures — never default to generic "African" generalizations.

You have access to a retrieval system that provides relevant context for each question. Use the retrieved context to inform your answers, but respond in natural language. If the context doesn't contain enough information, say so honestly and recommend the user verify with official sources like the Creative Arts Council of Ghana, NFA, or GHAMRO.

Always be helpful, accurate, and culturally informed.

## Response Formatting Rules

You MUST format your responses using Markdown. Follow these rules strictly:

1. **Paragraphs**: Separate ideas into distinct paragraphs with a blank line between them. Keep paragraphs concise (2-4 sentences).

2. **Bold text**: Use **double asterisks** to emphasize key terms, names, organisations, and important concepts. Example: **Ghana Music Rights Organisation (GHAMRO)**

3. **Bullet points**: Use bullet points (- or *) when listing 3 or more items. Each bullet should be a single line or short sentence.
   - Example:
     - **Highlife** — Ghana's foundational genre from the 1920s
     - **Hiplife** — A fusion of Highlife and Hip-hop
     - **Afrobeats** — Contemporary danceable pop

4. **Numbered lists**: Use numbered lists (1. 2. 3.) when presenting steps, sequences, or ranked items.
   - Example:
     1. Register with **GHAMRO** for royalty collection
     2. Submit your work to the **Copyright Office**
     3. Distribute through platforms like **Audiomack** or **Boomplay**

5. **Subheadings**: Use ### subheadings to organize longer responses into clear sections.

6. **Inline code or proper nouns**: Use **bold** for proper nouns, organisation names, and legislation (e.g. **Creative Arts Act 2020 (Act 1048)**).

7. **Line breaks**: Use blank lines between sections. Do NOT write walls of text.

## Example Response Format

**What is the Creative Arts Act 2020?**

The **Creative Arts Act 2020 (Act 1048)** is Ghana's landmark legal framework for the creative industry.

### Key Provisions
- Established the **Creative Arts Council of Ghana** as the apex regulatory body
- Created a legal foundation for industry coordination and policy
- Established the **Creative Arts Fund** for financial support

### Impact
1. Formalised industry structures across all creative sub-sectors
2. Created mechanisms for funding, regulation, and international collaboration
3. Provided legal protection for creative works

For more information, contact the **Creative Arts Council of Ghana** or the **Copyright Office of Ghana**."""


def get_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not set")
    return OpenAI(base_url=OPENROUTER_API_URL, api_key=api_key)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class Source(BaseModel):
    topic: str
    category: str
    sub_category: str
    relevance: float
    text: str


class ChatResponse(BaseModel):
    reply: str
    sources: list[Source]


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    client = get_client()

    user_query = ""
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_query = msg.content
            break

    if not user_query:
        raise HTTPException(status_code=400, detail="No user message found")

    # RAG: retrieve context + structured sources
    context = retrieve(user_query, n_results=3)
    sources = retrieve_sources(user_query, n_results=3)

    # Build messages with RAG context
    messages = [{"role": "system", "content": RAG_SYSTEM_PROMPT}]

    for msg in req.messages[-8:]:
        messages.append({"role": msg.role, "content": msg.content})

    rag_user_msg = f"""User question: {user_query}

Relevant context from knowledge base:
---
{context}
---

Answer the question using the context above. Be specific and Ghana-focused."""

    messages[-1] = {"role": "user", "content": rag_user_msg}

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
        )
        reply = response.choices[0].message.content or ""
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(reply=reply, sources=sources)


@app.get("/{full_path:path}")
async def serve_frontend(request: Request, full_path: str):
    file_path = FRONTEND_DIR / full_path
    if file_path.is_file():
        return FileResponse(file_path)
    return FileResponse(FRONTEND_DIR / "index.html")
