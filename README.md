# Ghana Creative Industry Chatbot

A terminal-based chatbot that answers questions about Ghana's creative industry — music, film, fashion, visual arts, comedy, dance, digital content, and the creative economy.

Powered by OpenRouter API.

## Setup

### 1. Install dependencies

```bash
pip install openai
```

Or if using `pyproject.toml` with a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e .
```

### 2. Set your OpenRouter API key

Either set it as an environment variable:

```bash
set OPENROUTER_API_KEY=your_api_key_here    # Windows PowerShell
```

Or you'll be prompted to enter it when you run the chatbot.

### 3. Run the chatbot

```bash
python main.py
```

## Usage

Type your question about Ghana's creative industry and press Enter.

**Example questions:**
- "Who are the biggest Ghanaian musicians right now?"
- "Tell me about Ghallywood and its history"
- "What is Kente cloth and where is it made?"
- "How does GHAMRO work?"
- "What fashion designers are from Ghana?"
- "What is the Creative Arts Act 2020?"

Type `quit`, `exit`, or `q` to end the conversation.

## Model

By default the chatbot uses `openai/gpt-4o-mini`. You can change the model in `main.py` by modifying the `model` parameter in the `chat()` function call.
