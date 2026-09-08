import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

pdf_filename = "/Users/aakashtiru/Desktop/AI-Eng/AI_Chatbot_Architecture_Documentation.pdf"

doc = SimpleDocTemplate(
    pdf_filename,
    pagesize=letter,
    rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
)

styles = getSampleStyleSheet()

# Custom styles
primary_color = colors.HexColor("#1e293b")
accent_color = colors.HexColor("#0284c7")
dark_neutral = colors.HexColor("#334155")
light_bg = colors.HexColor("#f8fafc")
border_color = colors.HexColor("#e2e8f0")

title_style = ParagraphStyle(
    'DocTitle',
    parent=styles['Heading1'],
    fontName='Helvetica-Bold',
    fontSize=24,
    leading=28,
    textColor=primary_color,
    spaceAfter=6
)

subtitle_style = ParagraphStyle(
    'DocSubTitle',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=12,
    leading=16,
    textColor=accent_color,
    spaceAfter=15
)

h1_style = ParagraphStyle(
    'Heading1_Custom',
    parent=styles['Heading2'],
    fontName='Helvetica-Bold',
    fontSize=15,
    leading=19,
    textColor=primary_color,
    spaceBefore=14,
    spaceAfter=8
)

h2_style = ParagraphStyle(
    'Heading2_Custom',
    parent=styles['Heading3'],
    fontName='Helvetica-Bold',
    fontSize=11,
    leading=15,
    textColor=accent_color,
    spaceBefore=10,
    spaceAfter=4
)

body_style = ParagraphStyle(
    'Body_Custom',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=9.5,
    leading=14,
    textColor=dark_neutral,
    spaceAfter=6
)

bullet_style = ParagraphStyle(
    'Bullet_Custom',
    parent=body_style,
    leftIndent=15,
    bulletIndent=5,
    spaceAfter=4
)

code_style = ParagraphStyle(
    'Code_Custom',
    parent=styles['Normal'],
    fontName='Courier',
    fontSize=8.5,
    leading=11,
    textColor=colors.HexColor("#0f172a"),
    backColor=colors.HexColor("#f1f5f9"),
    borderColor=colors.HexColor("#cbd5e1"),
    borderWidth=0.5,
    borderPadding=6,
    spaceBefore=4,
    spaceAfter=6
)

story = []

# Title Banner
story.append(Paragraph("AI Chatbot System Architecture", title_style))
story.append(Paragraph("Full-Stack Technical Documentation & Implementation Guide", subtitle_style))
story.append(HRFlowable(width="100%", thickness=2, color=accent_color, spaceAfter=15))

# Executive Summary
story.append(Paragraph("1. Executive Summary", h1_style))
exec_summary = (
    "This document provides a comprehensive technical overview of the AI Chatbot application. "
    "The application is built on a high-performance Python backend powered by FastAPI, LangChain, and "
    "Google Gemini API (using the <b>gemini-flash-lite-latest</b> model), backed by persistent SQLite storage "
    "for chat history and session tracking. Real-time streaming is delivered via Server-Sent Events (SSE)."
)
story.append(Paragraph(exec_summary, body_style))

# Key Features Table
data_features = [
    [Paragraph("<b>Component</b>", body_style), Paragraph("<b>Technology</b>", body_style), Paragraph("<b>Description</b>", body_style)],
    [Paragraph("Backend Framework", body_style), Paragraph("FastAPI + Uvicorn", body_style), Paragraph("Asynchronous REST API and SSE EventStream provider.", body_style)],
    [Paragraph("AI Orchestration", body_style), Paragraph("LangChain Community", body_style), Paragraph("Message formatting, context windowing, and streaming LLM integration.", body_style)],
    [Paragraph("LLM Model", body_style), Paragraph("Google Gemini API", body_style), Paragraph("Primary: <i>gemini-flash-lite-latest</i> with auto-fallback loop.", body_style)],
    [Paragraph("Database", body_style), Paragraph("SQLite (chat_store.db)", body_style), Paragraph("Relational storage for sessions and raw message store.", body_style)],
    [Paragraph("Frontend UI", body_style), Paragraph("Vanilla HTML5 / CSS3 / JS", body_style), Paragraph("Single Page Application with SSE stream reader & SQL Inspector.", body_style)]
]
t_features = Table(data_features, colWidths=[1.4*inch, 1.6*inch, 3.8*inch])
t_features.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
    ('TEXTCOLOR', (0,0), (-1,0), primary_color),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('TOPPADDING', (0,0), (-1,-1), 5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
]))
story.append(t_features)
story.append(Spacer(1, 10))

# System Architecture & Component Specifications
story.append(Paragraph("2. Core Codebase Modules", h1_style))

story.append(Paragraph("A. server.py (FastAPI Web Server)", h2_style))
server_desc = (
    "Acts as the primary application entry point. Serves static files and defines key REST endpoints: "
    "<br/>• <b>GET /api/sessions</b>: Retrieves existing user chat sessions."
    "<br/>• <b>POST /api/sessions</b>: Creates a new chat session."
    "<br/>• <b>POST /api/chat/stream</b>: SSE streaming endpoint that streams LLM tokens character by character."
    "<br/>• <b>GET /api/sql/inspect</b>: Queries database tables for the SQL Inspector modal."
)
story.append(Paragraph(server_desc, body_style))

story.append(Paragraph("B. langchain_bot.py (LangChain & Gemini Streaming)", h2_style))
bot_desc = (
    "Handles AI logic and Google Gemini API communication: "
    "<br/>• <b>build_messages_for_llm()</b>: Reads history from SQLite, trims to a 10-message sliding window, and formats into LangChain SystemMessage, HumanMessage, and AIMessage objects."
    "<br/>• <b>stream_chat_response()</b>: Async generator invoking <i>ChatGoogleGenerativeAI</i> with <b>max_retries=0</b> and <b>max_output_tokens=500</b>. Includes candidate fallback logic to guarantee immediate response time without quota hangs."
)
story.append(Paragraph(bot_desc, body_style))

story.append(Paragraph("C. db.py (SQLite Storage Layer)", h2_style))
db_desc = (
    "Manages SQLite database connections and transactions for <i>chat_store.db</i>: "
    "<br/>• <b>sessions table</b>: Stores session IDs, titles, timestamps, and model options."
    "<br/>• <b>message_store table</b>: Stores individual human/AI messages with role tags and tokens."
)
story.append(Paragraph(db_desc, body_style))

story.append(Spacer(1, 10))

# End-to-End Execution Flow
story.append(Paragraph("3. End-to-End User Prompt Execution Flow", h1_style))

steps = [
    "1. <b>User Input</b>: User types prompt in browser UI and clicks Send.",
    "2. <b>HTTP Connection</b>: JavaScript sends <i>POST /api/chat/stream</i> with session ID and prompt.",
    "3. <b>Persistence</b>: FastAPI calls <i>db.add_message()</i> to save user input in SQLite immediately.",
    "4. <b>Context Building</b>: <i>langchain_bot.py</i> loads past conversation history and constructs LangChain message stack.",
    "5. <b>Gemini Token Streaming</b>: LLM streams live tokens chunk by chunk. FastAPI yields SSE data events <i>data: {'event': 'token', 'token': '...'}</i>.",
    "6. <b>UI Live Render</b>: Frontend JS reads SSE stream buffer and appends text live on screen.",
    "7. <b>Completion & Storage</b>: Final output is saved to SQLite as an <i>ai</i> role message."
]

for s in steps:
    story.append(Paragraph(s, bullet_style))

story.append(Spacer(1, 10))

# Directory Structure
story.append(Paragraph("4. Repository Structure", h1_style))
repo_structure = (
    "AI-Eng/<br/>"
    "├── server.py             # FastAPI Server & Routes<br/>"
    "├── langchain_bot.py      # LangChain & Gemini Stream Handler<br/>"
    "├── db.py                 # SQLite Helper Functions & Schema<br/>"
    "├── requirements.txt      # Dependencies (fastapi, uvicorn, langchain-google-genai)<br/>"
    "├── chat_store.db         # Persistent SQLite Database<br/>"
    "└── static/<br/>"
    "    ├── index.html        # Main HTML Interface & SQL Modal<br/>"
    "    ├── styles.css        # Clean Dark Styling<br/>"
    "    └── app.js            # SSE Reader, Event Handlers & DOM Logic"
)
story.append(Paragraph(repo_structure, code_style))

doc.build(story)
print(f"PDF successfully created at: {pdf_filename}")
