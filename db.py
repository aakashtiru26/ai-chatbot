import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "chat_store.db")
FIXED_MODEL = "gemini-3.6-flash"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                system_prompt TEXT DEFAULT 'You are a helpful, accurate AI assistant powered by Gemini and LangChain.',
                model TEXT DEFAULT 'gemini-3.6-flash',
                temperature REAL DEFAULT 0.7,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_store (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                tokens INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()

def create_session(session_id: str, title: str = "New Chat", system_prompt: str = None, model: str = FIXED_MODEL) -> Dict[str, Any]:
    now = datetime.utcnow().isoformat() + "Z"
    if not system_prompt:
        system_prompt = "You are a helpful, accurate AI assistant powered by Gemini and LangChain."
        
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (id, title, system_prompt, model, temperature, created_at, updated_at)
            VALUES (?, ?, ?, ?, 0.7, ?, ?)
        """, (session_id, title, system_prompt, FIXED_MODEL, now, now))
        conn.commit()
    
    return get_session(session_id)

def get_sessions() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, 
                   COUNT(m.id) as message_count,
                   MAX(m.created_at) as last_message_at
            FROM sessions s
            LEFT JOIN message_store m ON s.id = m.session_id
            GROUP BY s.id
            ORDER BY s.updated_at DESC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        if row:
            session_dict = dict(row)
            cursor.execute("SELECT COUNT(*) as cnt FROM message_store WHERE session_id = ?", (session_id,))
            session_dict["message_count"] = cursor.fetchone()["cnt"]
            return session_dict
        return None

def update_session(session_id: str, title: Optional[str] = None) -> Optional[Dict[str, Any]]:
    current = get_session(session_id)
    if not current:
        return None
        
    new_title = title if title is not None else current["title"]
    now = datetime.utcnow().isoformat() + "Z"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sessions
            SET title = ?, updated_at = ?
            WHERE id = ?
        """, (new_title, now, session_id))
        conn.commit()
        
    return get_session(session_id)

def delete_session(session_id: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM message_store WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        return cursor.rowcount > 0

def add_message(session_id: str, message_type: str, content: str, tokens: int = 0) -> Dict[str, Any]:
    now = datetime.utcnow().isoformat() + "Z"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO message_store (session_id, message_type, content, tokens, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, message_type, content, tokens, now))
        
        cursor.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
        conn.commit()
        msg_id = cursor.lastrowid

    return {
        "id": msg_id,
        "session_id": session_id,
        "message_type": message_type,
        "content": content,
        "tokens": tokens,
        "created_at": now
    }

def get_session_messages(session_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM message_store 
            WHERE session_id = ? 
            ORDER BY id ASC
        """, (session_id,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def clear_session_messages(session_id: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM message_store WHERE session_id = ?", (session_id,))
        conn.commit()
        return True

def get_sql_tables_inspection() -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY updated_at DESC LIMIT 50")
        sessions = [dict(r) for r in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM message_store ORDER BY id DESC LIMIT 100")
        messages = [dict(r) for r in cursor.fetchall()]
        
        return {
            "sessions_table": sessions,
            "message_store_table": messages
        }

def get_db_stats() -> Dict[str, Any]:
    db_size = os.path.getsize(DB_FILE) if os.path.exists(DB_FILE) else 0
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM sessions")
        total_sessions = cursor.fetchone()["cnt"]
        
        cursor.execute("SELECT COUNT(*) as cnt, COALESCE(SUM(tokens), 0) as total_tokens FROM message_store")
        msg_stats = cursor.fetchone()
        
        return {
            "total_sessions": total_sessions,
            "total_messages": msg_stats["cnt"],
            "total_tokens": msg_stats["total_tokens"],
            "db_size_kb": round(db_size / 1024, 2)
        }

if __name__ == "__main__":
    init_db()
