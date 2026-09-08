/* ==========================================================================
   AI Chatbot - Simple & Clean Application Logic
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {

  const DEFAULT_KEY = "";

  let sessions = [];
  let currentSessionId = null;
  let currentSession = null;
  let isStreaming = false;

  // DOM Elements
  const sessionListEl = document.getElementById('session-list');
  const btnNewChat = document.getElementById('btn-new-chat');
  const inputSearch = document.getElementById('input-search');
  const currentTitleEl = document.getElementById('current-title');
  const btnClearHistory = document.getElementById('btn-clear-history');
  const feedEl = document.getElementById('feed');
  const promptInput = document.getElementById('prompt-input');
  const btnSend = document.getElementById('btn-send');
  const inputKey = document.getElementById('input-key');
  
  const btnOpenSql = document.getElementById('btn-open-sql');
  const modalSql = document.getElementById('modal-sql');
  const btnCloseSql = document.getElementById('btn-close-sql');
  const tableMsgsBody = document.getElementById('table-msgs').querySelector('tbody');
  const tableSessBody = document.getElementById('table-sess').querySelector('tbody');
  const msgCountEl = document.getElementById('msg-count');
  const sessCountEl = document.getElementById('sess-count');

  // Load saved key if present
  if (localStorage.getItem('user_api_key')) {
    inputKey.value = localStorage.getItem('user_api_key');
  }

  inputKey.oninput = () => {
    localStorage.setItem('user_api_key', inputKey.value.trim());
  };

  // Marked setup
  marked.setOptions({
    highlight: function(code, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try { return hljs.highlight(code, { language: lang }).value; } catch (e) {}
      }
      return hljs.highlightAuto(code).value;
    },
    breaks: true
  });

  // Fetch Sessions
  async function fetchSessions() {
    try {
      const res = await fetch('/api/sessions');
      const data = await res.json();
      sessions = data.sessions || [];
      renderSessionsList();

      if (sessions.length > 0 && !currentSessionId) {
        switchSession(sessions[0].id);
      } else if (sessions.length === 0) {
        createNewSession();
      }
    } catch (e) {
      console.error('Error fetching sessions:', e);
    }
  }

  async function createNewSession(title = 'New Chat') {
    try {
      const res = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title })
      });
      const newSess = await res.json();
      sessions.unshift(newSess);
      renderSessionsList();
      switchSession(newSess.id);
    } catch (e) {
      console.error('Error creating session:', e);
    }
  }

  async function switchSession(sessionId) {
    currentSessionId = sessionId;
    currentSession = sessions.find(s => s.id === sessionId);
    renderSessionsList();

    if (currentSession) {
      currentTitleEl.textContent = currentSession.title;
    }

    try {
      const res = await fetch(`/api/sessions/${sessionId}/messages`);
      const data = await res.json();
      renderMessages(data.messages || []);
    } catch (e) {
      console.error('Error fetching messages:', e);
    }
  }

  async function deleteSession(sessionId) {
    try {
      await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
      sessions = sessions.filter(s => s.id !== sessionId);
      renderSessionsList();
      if (currentSessionId === sessionId) {
        currentSessionId = null;
        if (sessions.length > 0) switchSession(sessions[0].id);
        else createNewSession();
      }
    } catch (e) {
      console.error('Error deleting session:', e);
    }
  }

  async function clearCurrentChatHistory() {
    if (!currentSessionId) return;
    try {
      await fetch(`/api/sessions/${currentSessionId}/clear`, { method: 'POST' });
      feedEl.innerHTML = '';
    } catch (e) {
      console.error('Error clearing chat:', e);
    }
  }

  function renderSessionsList() {
    const filter = inputSearch.value.toLowerCase().trim();
    sessionListEl.innerHTML = '';

    const filtered = sessions.filter(s => s.title.toLowerCase().includes(filter));

    filtered.forEach(s => {
      const item = document.createElement('div');
      item.className = `session-item ${s.id === currentSessionId ? 'active' : ''}`;
      item.onclick = () => switchSession(s.id);

      item.innerHTML = `
        <span>${escapeHtml(s.title)}</span>
        <button class="btn-del-item" title="Delete"><i class="fa-solid fa-xmark"></i></button>
      `;

      item.querySelector('.btn-del-item').onclick = (e) => {
        e.stopPropagation();
        deleteSession(s.id);
      };

      sessionListEl.appendChild(item);
    });
  }

  function renderMessages(messages) {
    feedEl.innerHTML = '';
    if (!messages) return;

    messages.forEach(msg => {
      const card = createMessageElement(msg.message_type, msg.content);
      feedEl.appendChild(card);
    });

    scrollToBottom();
  }

  function createMessageElement(role, content) {
    const card = document.createElement('div');
    card.className = `msg-card ${role === 'human' ? 'user' : 'ai'}`;
    const isAi = role === 'ai';

    const renderedHtml = isAi ? marked.parse(content) : escapeHtml(content).replace(/\n/g, '<br>');

    card.innerHTML = `
      <div class="msg-avatar">
        <i class="${isAi ? 'fa-solid fa-robot' : 'fa-solid fa-user'}"></i>
      </div>
      <div class="msg-body">
        <div class="msg-content">${renderedHtml}</div>
        ${isAi ? `<button class="btn-copy"><i class="fa-solid fa-copy"></i> Copy</button>` : ''}
      </div>
    `;

    if (isAi) {
      card.querySelector('.btn-copy').onclick = () => {
        navigator.clipboard.writeText(content);
      };
    }

    return card;
  }

  async function handleSendPrompt() {
    const prompt = promptInput.value.trim();
    if (!prompt || isStreaming) return;

    if (!currentSessionId) {
      await createNewSession(prompt.substring(0, 30));
    }

    // Render User Message
    const userCard = createMessageElement('human', prompt);
    feedEl.appendChild(userCard);
    
    promptInput.value = '';
    autoResizeTextarea();
    scrollToBottom();

    // Prepare AI Streaming Message
    isStreaming = true;
    btnSend.disabled = true;

    const aiCard = document.createElement('div');
    aiCard.className = 'msg-card ai';
    aiCard.innerHTML = `
      <div class="msg-avatar">
        <i class="fa-solid fa-robot"></i>
      </div>
      <div class="msg-body">
        <div class="msg-content"><span class="stream-text"></span><span class="cursor"></span></div>
        <button class="btn-copy hidden"><i class="fa-solid fa-copy"></i> Copy</button>
      </div>
    `;
    feedEl.appendChild(aiCard);
    scrollToBottom();

    const streamTextSpan = aiCard.querySelector('.stream-text');
    const cursorEl = aiCard.querySelector('.cursor');
    const msgContentDiv = aiCard.querySelector('.msg-content');
    const btnCopy = aiCard.querySelector('.btn-copy');

    let accumulatedText = '';
    const keyToSend = inputKey.value.trim() || DEFAULT_KEY;

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Gemini-API-Key': keyToSend
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          prompt: prompt
        })
      });

      if (!response.ok) {
        const errJson = await response.json();
        throw new Error(errJson.detail || 'Streaming failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data: ')) {
            const rawData = trimmed.substring(6);
            try {
              const payload = JSON.parse(rawData);
              
              if (payload.event === 'token') {
                accumulatedText += payload.token;
                streamTextSpan.textContent = accumulatedText;
                scrollToBottom();
              } else if (payload.event === 'done') {
                cursorEl.remove();
                msgContentDiv.innerHTML = marked.parse(payload.full_content || accumulatedText);
                btnCopy.classList.remove('hidden');
                btnCopy.onclick = () => navigator.clipboard.writeText(payload.full_content || accumulatedText);
                fetchSessions();
              } else if (payload.event === 'error') {
                throw new Error(payload.error);
              }
            } catch (e) {
              console.error('SSE Error:', e);
            }
          }
        }
      }

    } catch (err) {
      cursorEl.remove();
      msgContentDiv.innerHTML = `<span style="color: #f85149;">Error: ${escapeHtml(err.message)}</span>`;
    } finally {
      isStreaming = false;
      btnSend.disabled = false;
      scrollToBottom();
    }
  }

  async function fetchSqlInspection() {
    try {
      const res = await fetch('/api/sql/inspect');
      const data = await res.json();

      tableMsgsBody.innerHTML = '';
      msgCountEl.textContent = data.message_store_table.length;
      data.message_store_table.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>#${r.id}</td>
          <td>${r.session_id}</td>
          <td>${r.message_type}</td>
          <td>${escapeHtml(r.content.substring(0, 50))}...</td>
          <td>${new Date(r.created_at).toLocaleTimeString()}</td>
        `;
        tableMsgsBody.appendChild(tr);
      });

      tableSessBody.innerHTML = '';
      sessCountEl.textContent = data.sessions_table.length;
      data.sessions_table.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${r.id}</td>
          <td>${escapeHtml(r.title)}</td>
          <td>${new Date(r.created_at).toLocaleTimeString()}</td>
        `;
        tableSessBody.appendChild(tr);
      });
    } catch (e) {
      console.error('Error inspecting SQL:', e);
    }
  }

  function autoResizeTextarea() {
    promptInput.style.height = 'auto';
    promptInput.style.height = Math.min(120, promptInput.scrollHeight) + 'px';
  }

  function scrollToBottom() {
    feedEl.scrollTop = feedEl.scrollHeight;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // Listeners
  btnNewChat.onclick = () => createNewSession('New Chat');
  inputSearch.oninput = renderSessionsList;
  btnClearHistory.onclick = clearCurrentChatHistory;

  btnOpenSql.onclick = () => {
    fetchSqlInspection();
    modalSql.classList.remove('hidden');
  };
  btnCloseSql.onclick = () => modalSql.classList.add('hidden');

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab).classList.add('active');
    };
  });

  promptInput.oninput = autoResizeTextarea;
  promptInput.onkeydown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendPrompt();
    }
  };

  btnSend.onclick = handleSendPrompt;

  fetchSessions();
});
