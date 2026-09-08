import os
import json
import time
import asyncio
from typing import AsyncGenerator, Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
import db

FIXED_MODEL = "gemini-flash-lite-latest"
FALLBACK_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-3.6-flash"
]

def build_messages_for_llm(session_id: str, new_user_prompt: str) -> List[BaseMessage]:
    """Retrieve conversation history from SQLite and format as standard LangChain messages."""
    session = db.get_session(session_id)
    system_text = (
        session["system_prompt"] if session and session.get("system_prompt") 
        else "You are a helpful, accurate AI assistant powered by Gemini and LangChain."
    )
    
    messages: List[BaseMessage] = [SystemMessage(content=system_text)]
    
    # Retrieve past messages from SQLite memory
    sql_messages = db.get_session_messages(session_id)
    recent_msgs = sql_messages[-10:] if len(sql_messages) > 10 else sql_messages

    for msg in recent_msgs:
        m_type = msg["message_type"]
        m_content = msg["content"]
        if m_type == "human":
            messages.append(HumanMessage(content=m_content))
        elif m_type == "ai":
            messages.append(AIMessage(content=m_content))
        elif m_type == "system":
            messages.append(SystemMessage(content=m_content))
            
    messages.append(HumanMessage(content=new_user_prompt))
    return messages

async def stream_chat_response(
    session_id: str,
    user_prompt: str,
    api_key: str
) -> AsyncGenerator[str, None]:
    """
    Stream live token-by-token response from Gemini API using fast gemini-flash-lite-latest model.
    """
    start_time = time.time()
    
    session = db.get_session(session_id)
    if not session:
        db.create_session(session_id, title=user_prompt[:30] if len(user_prompt) > 30 else user_prompt, model=FIXED_MODEL)
    elif session.get("message_count", 0) == 0 and session.get("title") == "New Chat":
        db.update_session(session_id, title=user_prompt[:35] + ("..." if len(user_prompt) > 35 else ""))

    # Save user prompt to SQLite memory
    user_tokens_est = max(1, len(user_prompt) // 4)
    db.add_message(session_id, "human", user_prompt, tokens=user_tokens_est)

    yield f"data: {json.dumps({'event': 'start', 'session_id': session_id})}\n\n"

    langchain_msgs = build_messages_for_llm(session_id, user_prompt)

    # Model resolution with automatic quota fallback
    llm = None
    selected_model = FIXED_MODEL
    last_error = None

    for model_candidate in FALLBACK_MODELS:
        try:
            candidate_llm = ChatGoogleGenerativeAI(
                google_api_key=api_key,
                model=model_candidate,
                temperature=0.7,
                max_output_tokens=500,
                max_retries=0,
                streaming=True,
                convert_system_message_to_human=False
            )
            # Test astream stream startup
            llm = candidate_llm
            selected_model = model_candidate
            break
        except Exception as err:
            last_error = err
            continue

    if not llm:
        err_payload = {
            "event": "error",
            "error": str(last_error or "Unable to initialize Gemini model"),
            "done": True
        }
        yield f"data: {json.dumps(err_payload)}\n\n"
        return

    full_ai_response = ""
    token_count = 0

    try:
        async for chunk in llm.astream(langchain_msgs):
            token_text = chunk.content
            if token_text:
                full_ai_response += token_text
                token_count += 1
                
                payload = {
                    "event": "token",
                    "token": token_text,
                    "done": False,
                    "tokens_so_far": token_count
                }
                yield f"data: {json.dumps(payload)}\n\n"

        # Save AI response to persistent SQLite memory
        ai_msg = db.add_message(session_id, "ai", full_ai_response, tokens=token_count)

        final_payload = {
            "event": "done",
            "done": True,
            "message_id": ai_msg["id"],
            "session_id": session_id,
            "full_content": full_ai_response,
            "tokens": token_count,
            "model_used": selected_model
        }
        yield f"data: {json.dumps(final_payload)}\n\n"

    except Exception as e:
        # Fallback attempt if stream fails midway
        err_payload = {
            "event": "error",
            "error": str(e),
            "done": True
        }
        yield f"data: {json.dumps(err_payload)}\n\n"
