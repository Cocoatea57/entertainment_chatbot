"""
CreativeArts CLI Chatbot — RAG-enabled

Uses ChromaDB to retrieve relevant context before generating responses.
"""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from vector_store import retrieve

load_dotenv()

OPENROUTER_API_URL = "https://openrouter.ai/api/v1"
MODEL = "openai/gpt-4o-mini"

RAG_SYSTEM_PROMPT = """You are CreativeArts, a knowledgeable assistant specializing in Ghana's creative industry.

You answer questions about music, film, fashion, visual arts, comedy, dance, digital content, and the creative economy in Ghana. You always cite Ghanaian institutions, laws, and figures — never default to generic "African" generalizations.

You have access to a retrieval system that provides relevant context for each question. Use the retrieved context to inform your answers, but respond in natural language. If the context doesn't contain enough information, say so honestly and recommend the user verify with official sources like the Creative Arts Council of Ghana, NFA, or GHAMRO.

Always be helpful, accurate, and culturally informed."""

WELCOME_MSG = """
╔══════════════════════════════════════════════════════════════╗
║            CreativeArts                                     ║
║  Ask me about music, film, fashion, arts, comedy,           ║
║  dance, digital content, and the creative economy           ║
║  in Ghana.                                                  ║
║                                                             ║
║  Type 'quit' or 'exit' to end the conversation.             ║
╚══════════════════════════════════════════════════════════════╝
"""


def get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        key = input("Enter your OpenRouter API key: ").strip()
        if not key:
            print("Error: No API key provided.")
            sys.exit(1)
    return key


def create_client(api_key: str) -> OpenAI:
    return OpenAI(base_url=OPENROUTER_API_URL, api_key=api_key)


def chat(client: OpenAI, messages: list[dict]) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=2048,
    )
    return response.choices[0].message.content or ""


def build_rag_prompt(user_query: str) -> list[dict]:
    """Retrieve context and build the message list for the LLM."""
    context = retrieve(user_query, n_results=3)

    user_message = f"""User question: {user_query}

Relevant context from knowledge base:
---
{context}
---

Answer the question using the context above. Be specific and Ghana-focused."""

    return [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


def main() -> None:
    print(WELCOME_MSG)

    api_key = get_api_key()
    client = create_client(api_key)

    conversation: list[dict] = []

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        # RAG: retrieve context and build prompt
        messages = build_rag_prompt(user_input)

        # Add conversation history (last 4 exchanges)
        for msg in conversation[-8:]:
            messages.insert(1, msg)

        try:
            print("\nBot: ", end="", flush=True)
            response = chat(client, messages)
            print(response)

            # Track conversation
            conversation.append({"role": "user", "content": user_input})
            conversation.append({"role": "assistant", "content": response})
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
