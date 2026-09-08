import os
import uuid
import json
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

import db
import langchain_bot

load_dotenv()
db.init_db()

app = FastAPI(title="LangChain Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SessionCreateRequest(BaseModel):
    title: Optional[str] = "New Chat"

class ChatStreamRequest(BaseModel):
    session_id: str
    prompt: str
    api_key: Optional[str] = None

def get_effective_api_key(header_key: Optional[str] = None, body_key: Optional[str] = None) -> str:
    key = body_key or header_key or os.getenv("GEMINI_API_KEY")
    if not key or len(str(key).strip()) < 5:
        key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise HTTPException(status_code=400, detail="Gemini API Key missing.")
    return str(key).strip()

@app.get("/api/sessions")
def list_sessions():
    return {"sessions": db.get_sessions()}

@app.post("/api/sessions")
def create_session(req: SessionCreateRequest):
    session_id = f"session-{uuid.uuid4().hex[:8]}"
    return db.create_session(session_id=session_id, title=req.title)

@app.get("/api/sessions/{session_id}/messages")
def get_messages(session_id: str):
    return {"session_id": session_id, "messages": db.get_session_messages(session_id)}

@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    db.delete_session(session_id)
    return {"success": True}

@app.post("/api/sessions/{session_id}/clear")
def clear_messages(session_id: str):
    db.clear_session_messages(session_id)
    return {"success": True}

@app.post("/api/clear-all")
def clear_all_data():
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM message_store;")
        cursor.execute("DELETE FROM sessions;")
        conn.commit()
    return {"success": True, "message": "All history cleared"}

@app.post("/api/chat/stream")
async def chat_stream(req: ChatStreamRequest, x_gemini_api_key: Optional[str] = Header(None)):
    api_key = get_effective_api_key(header_key=x_gemini_api_key, body_key=req.api_key)
    
    generator = langchain_bot.stream_chat_response(
        session_id=req.session_id,
        user_prompt=req.prompt,
        api_key=api_key
    )
    return StreamingResponse(generator, media_type="text/event-stream")

@app.get("/api/sql/inspect")
def inspect_sql_tables():
    return db.get_sql_tables_inspection()

@app.get("/api/download/pdf")
def download_architecture_pdf():
    pdf_path = os.path.join(os.path.dirname(__file__), "AI_Chatbot_Architecture_Documentation.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF documentation not found.")
    return FileResponse(
        pdf_path, 
        media_type="application/pdf", 
        filename="AI_Chatbot_Architecture_Documentation.pdf"
    )

@app.get("/api/download/zip")
def download_windows_zip():
    zip_path = os.path.join(os.path.dirname(__file__), "AI-Chatbot-Windows.zip")
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="ZIP package not found.")
    return FileResponse(
        zip_path, 
        media_type="application/zip", 
        filename="AI-Chatbot-Windows.zip"
    )

@app.get("/api/stats")
def get_stats():
    return db.get_db_stats()

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_home():
    return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
