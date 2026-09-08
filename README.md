# AI Chatbot (FastAPI + LangChain + SQLite)

A lightweight full-stack AI chat application built with Python (FastAPI), LangChain, Google Gemini API, and SQLite for persistent conversation memory.

It supports real-time token streaming using Server-Sent Events (SSE), multi-session management, and a built-in SQL memory inspector modal to view stored messages directly from SQLite.

---

## What's Inside

- **FastAPI Server (`server.py`)**: Handles API routing, session management, and streams AI tokens directly to the browser over SSE.
- **LangChain Integration (`langchain_bot.py`)**: Formats chat history, connects to Google Gemini API (`gemini-flash-lite-latest`), and streams responses chunk by chunk.
- **Persistent SQLite Database (`db.py`)**: Stores all chat sessions and message logs locally in `chat_store.db`.
- **Vanilla Frontend (`static/`)**: Clean dark UI with sidebar session management, auto-resizing input box, markdown syntax highlighting (Marked.js + Highlight.js), and an interactive SQL Inspector.

---

## Project Structure

```text
.
├── server.py             # FastAPI app & SSE streaming endpoints
├── langchain_bot.py      # LangChain chain & Gemini streaming handler
├── db.py                 # SQLite database helper (sessions & message tables)
├── requirements.txt      # Python package dependencies
├── .env                  # Environment configuration (API key)
└── static/               # Client-side web app
    ├── index.html        # Main HTML layout & SQL inspector modal
    ├── styles.css        # Clean dark mode CSS
    └── app.js            # SSE parser, DOM logic, & session switching
```

---

## Quick Start

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/aakashtiru26/ai-chatbot.git
cd ai-chatbot

python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

*(Note: You can also pass your API key directly in the top-right header input field in the web UI).*

### 4. Run the Application

```bash
uvicorn server:app --reload --port 8000
```

Open your browser and navigate to:  
👉 **`http://127.0.0.1:8000`**

---

## How It Works

1. **Session & Message Storage**: When you start a chat, `db.py` initializes a new session entry in `chat_store.db`. Every user prompt and AI response is appended to the `message_store` table.
2. **Context Windowing**: Before calling Gemini, `langchain_bot.py` fetches the last 10 messages from SQLite for that session and wraps them into standard LangChain `SystemMessage`, `HumanMessage`, and `AIMessage` objects.
3. **Live Streaming**: The client sends a `POST` request to `/api/chat/stream`. FastAPI reads chunks from `llm.astream()` and forwards them via Server-Sent Events (`data: {"event": "token", "token": "..."}`).
4. **SQL Inspector**: Click the **SQL Inspector** button in the sidebar to inspect raw messages and session records stored in SQLite in real time.
