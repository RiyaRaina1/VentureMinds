/* ==========================================================================
   VENTUREMIND AI - REAL AI CHAT STUDIO (PHASE 2)
   Powered by Groq LPU Engine, FastAPI SSE Streaming, and MySQL Chat Persistence
   ========================================================================== */

class AIChatStudio {
  constructor() {
    this.apiBase = `${window.location.protocol}//${window.location.hostname}:8000/api/chat`;
    this.messagesContainer = document.getElementById('chat-messages');
    this.inputField = document.getElementById('chat-input');
    this.sendBtn = document.getElementById('chat-send-btn');
    this.voiceBtn = document.getElementById('chat-voice-btn');
    this.modelSelect = document.getElementById('chat-model-select');
    this.newChatBtn = document.getElementById('btn-new-chat');
    this.sessionsListContainer = document.getElementById('chat-sessions-list');
    this.startupBadge = document.getElementById('chat-active-startup-badge');
    this.startupNameDisplay = document.getElementById('chat-startup-name-display');

    this.currentSessionId = null;
    this.currentStartupId = null;
    this.isStreaming = false;

    this.init();
  }

  async init() {
    this.bindEvents();
    await this.loadSessions();
  }

  bindEvents() {
    if (this.sendBtn) {
      this.sendBtn.addEventListener('click', () => this.sendMessage());
    }

    if (this.inputField) {
      this.inputField.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });
    }

    if (this.voiceBtn) {
      this.voiceBtn.addEventListener('click', () => this.toggleVoiceSimulation());
    }

    if (this.newChatBtn) {
      this.newChatBtn.addEventListener('click', () => this.createNewSession());
    }

    // Suggested prompt click handlers
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('prompt-chip')) {
        const promptText = e.target.textContent.trim();
        if (this.inputField) {
          this.inputField.value = promptText;
          this.sendMessage();
        }
      }
    });
  }

  toggleVoiceSimulation() {
    if (window.VentureMindApp) {
      window.VentureMindApp.showToast('Voice transcription service will be enabled in future audio updates.', 'info');
    }
  }

  setStartupContext(startupId, startupName) {
    this.currentStartupId = startupId;
    if (this.startupBadge && this.startupNameDisplay) {
      if (startupId && startupName) {
        this.startupNameDisplay.textContent = startupName;
        this.startupBadge.style.display = 'inline-flex';
      } else {
        this.startupBadge.style.display = 'none';
      }
    }
  }

  async loadSessions() {
    try {
      const res = await fetch(`${this.apiBase}/sessions`);
      if (res.ok) {
        const sessions = await res.json();
        this.renderSessionsList(sessions);
        if (sessions.length > 0 && !this.currentSessionId) {
          await this.selectSession(sessions[0].id);
        } else if (sessions.length === 0 && !this.currentSessionId) {
          await this.createNewSession(false);
        }
      }
    } catch (err) {
      console.warn('Could not load chat sessions from backend:', err);
    }
  }

  renderSessionsList(sessions) {
    if (!this.sessionsListContainer) return;
    this.sessionsListContainer.innerHTML = '';

    if (!sessions || sessions.length === 0) {
      this.sessionsListContainer.innerHTML = `
        <div style="font-size: 0.75rem; color: var(--text-muted); padding: 6px;">No saved conversations</div>
      `;
      return;
    }

    sessions.forEach(sess => {
      const item = document.createElement('div');
      item.className = `chat-session-item ${sess.id === this.currentSessionId ? 'active' : ''}`;
      item.id = `session-item-${sess.id}`;

      const title = sess.title || 'New VentureMind Chat';
      item.innerHTML = `
        <span class="session-title" title="${this.escapeHtml(title)}">
          <i class="fas fa-comment-dots" style="margin-right: 6px; font-size: 0.75rem; color: var(--accent-cyan);"></i>
          ${this.escapeHtml(title)}
        </span>
        <button class="session-del-btn" title="Delete conversation" data-session-id="${sess.id}">
          <i class="fas fa-trash-alt"></i>
        </button>
      `;

      item.addEventListener('click', (e) => {
        if (e.target.closest('.session-del-btn')) {
          e.stopPropagation();
          this.deleteSession(sess.id);
          return;
        }
        this.selectSession(sess.id);
      });

      this.sessionsListContainer.appendChild(item);
    });
  }

  async selectSession(sessionId) {
    if (this.isStreaming) return;
    this.currentSessionId = sessionId;

    // Update active class in sidebar
    document.querySelectorAll('.chat-session-item').forEach(el => {
      el.classList.remove('active');
    });
    const currentEl = document.getElementById(`session-item-${sessionId}`);
    if (currentEl) currentEl.classList.add('active');

    // Fetch and render messages
    try {
      const res = await fetch(`${this.apiBase}/sessions/${sessionId}/messages`);
      if (res.ok) {
        const messages = await res.json();
        this.renderMessages(messages);
      }
    } catch (err) {
      console.error('Failed to load session messages:', err);
    }
  }

  async createNewSession(autoFocus = true) {
    if (this.isStreaming) return;

    try {
      const payload = {
        title: 'New VentureMind Chat',
        startup_id: this.currentStartupId || null
      };
      const res = await fetch(`${this.apiBase}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const session = await res.json();
        this.currentSessionId = session.id;
        await this.loadSessions();
        this.renderDefaultGreeting();
        if (autoFocus && this.inputField) this.inputField.focus();
      }
    } catch (err) {
      console.error('Failed to create new chat session:', err);
    }
  }

  async deleteSession(sessionId) {
    if (this.isStreaming) return;

    try {
      const res = await fetch(`${this.apiBase}/sessions/${sessionId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        if (this.currentSessionId === sessionId) {
          this.currentSessionId = null;
        }
        await this.loadSessions();
        if (!this.currentSessionId) {
          await this.createNewSession(false);
        }
      }
    } catch (err) {
      console.error('Failed to delete chat session:', err);
    }
  }

  renderDefaultGreeting() {
    if (!this.messagesContainer) return;
    this.messagesContainer.innerHTML = `
      <div class="chat-msg ai">
        <div class="chat-avatar">VM</div>
        <div class="chat-bubble">
          Hello Founder! I am your <strong>Autonomous AI Co-Founder</strong> powered by <strong>Groq LPU Engine</strong>. Ask me anything about startup validation, competitive moats, financial modeling, unit economics, or pitch decks.
        </div>
      </div>
    `;
    this.scrollToBottom();
  }

  renderMessages(messages) {
    if (!this.messagesContainer) return;
    this.messagesContainer.innerHTML = '';

    if (!messages || messages.length === 0) {
      this.renderDefaultGreeting();
      return;
    }

    messages.forEach(msg => {
      if (msg.role === 'user') {
        this.appendUserMessage(msg.content, false);
      } else if (msg.role === 'assistant') {
        this.appendAssistantBubble(this.parseMarkdown(msg.content));
      }
    });

    this.scrollToBottom();
  }

  appendUserMessage(text, shouldScroll = true) {
    if (!this.messagesContainer) return;

    const msgHtml = `
      <div class="chat-msg user">
        <div class="chat-avatar">YOU</div>
        <div class="chat-bubble">${this.escapeHtml(text)}</div>
      </div>
    `;

    this.messagesContainer.insertAdjacentHTML('beforeend', msgHtml);
    if (shouldScroll) this.scrollToBottom();
  }

  appendAssistantBubble(htmlContent = '') {
    if (!this.messagesContainer) return;

    const msgHtml = `
      <div class="chat-msg ai">
        <div class="chat-avatar">VM</div>
        <div class="chat-bubble">${htmlContent}</div>
      </div>
    `;

    this.messagesContainer.insertAdjacentHTML('beforeend', msgHtml);
  }

  createStreamingBubble() {
    if (!this.messagesContainer) return null;

    const bubbleId = `stream-bubble-${Date.now()}`;
    const msgHtml = `
      <div class="chat-msg ai">
        <div class="chat-avatar">VM</div>
        <div class="chat-bubble" id="${bubbleId}">
          <span class="streaming-cursor"></span>
        </div>
      </div>
    `;

    this.messagesContainer.insertAdjacentHTML('beforeend', msgHtml);
    this.scrollToBottom();
    return document.getElementById(bubbleId);
  }

  async sendMessage() {
    if (this.isStreaming) return;

    const text = this.inputField?.value.trim();
    if (!text) return;

    // Ensure session exists
    if (!this.currentSessionId) {
      await this.createNewSession(false);
    }

    // 1. Render User Message
    this.appendUserMessage(text);
    if (this.inputField) this.inputField.value = '';

    // 2. Prepare streaming bubble
    const bubble = this.createStreamingBubble();
    if (!bubble) return;

    this.isStreaming = true;
    if (this.sendBtn) this.sendBtn.disabled = true;

    const selectedModel = this.modelSelect?.value || 'openai/gpt-oss-120b';
    let accumulatedContent = '';

    try {
      const response = await fetch(`${this.apiBase}/sessions/${this.currentSessionId}/messages/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: text,
          model: selectedModel
        })
      });

      if (!response.ok) {
        const errorJson = await response.json().catch(() => ({ detail: 'HTTP ' + response.status }));
        throw new Error(errorJson.detail || `Server returned error status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const block of lines) {
          const blockLines = block.split('\n');
          let eventType = 'message';
          let eventData = '';

          for (const line of blockLines) {
            if (line.startsWith('event: ')) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              eventData = line.slice(6).trim();
            }
          }

          if (eventType === 'token' && eventData) {
            try {
              const parsed = JSON.parse(eventData);
              if (parsed.content) {
                accumulatedContent += parsed.content;
                bubble.innerHTML = this.parseMarkdown(accumulatedContent) + '<span class="streaming-cursor"></span>';
                this.scrollToBottom();
              }
            } catch (e) { }
          } else if (eventType === 'done') {
            bubble.innerHTML = this.parseMarkdown(accumulatedContent);
            this.scrollToBottom();
            await this.loadSessions();
          } else if (eventType === 'error' && eventData) {
            try {
              const errParsed = JSON.parse(eventData);
              bubble.classList.add('error-bubble');
              bubble.innerHTML = `
                <div style="color: var(--accent-pink); font-weight: 700; margin-bottom: 6px;">
                  <i class="fas fa-exclamation-triangle"></i> AI Generation Notice
                </div>
                <p style="color: var(--text-muted); margin: 0;">${this.escapeHtml(errParsed.detail || 'An error occurred during AI processing.')}</p>
              `;
            } catch (e) { }
          }
        }
      }

      // Finalize display if not already error
      if (!bubble.classList.contains('error-bubble')) {
        bubble.innerHTML = this.parseMarkdown(accumulatedContent);
      }

    } catch (fetchErr) {
      bubble.classList.add('error-bubble');
      bubble.innerHTML = `
        <div style="color: var(--accent-pink); font-weight: 700; margin-bottom: 6px;">
          <i class="fas fa-exclamation-circle"></i> Service Notice
        </div>
        <p style="color: var(--text-muted); margin: 0;">${this.escapeHtml(fetchErr.message || 'Unable to connect to AI server.')}</p>
      `;
    } finally {
      this.isStreaming = false;
      if (this.sendBtn) this.sendBtn.disabled = false;
      this.scrollToBottom();
    }
  }

  scrollToBottom() {
    if (this.messagesContainer) {
      this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
  }

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  parseMarkdown(rawText) {
    if (!rawText) return '';

    let text = this.escapeHtml(rawText);

    // Code blocks ```code```
    text = text.replace(/```([\s\S]*?)```/g, (match, code) => {
      return `<pre><code>${code.trim()}</code></pre>`;
    });

    // Inline code `code`
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Headers
    text = text.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    text = text.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    text = text.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Bold **text**
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Italic *text*
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Unordered lists (- item or * item)
    text = text.replace(/(?:^|\n)[-*]\s+(.*)/g, '\n<li>$1</li>');
    text = text.replace(/(<li>.*<\/li>(\n<li>.*<\/li>)*)/g, '<ul>$1</ul>');

    // Numbered lists (1. item)
    text = text.replace(/(?:^|\n)\d+\.\s+(.*)/g, '\n<ol-item>$1</ol-item>');
    text = text.replace(/(<ol-item>.*<\/ol-item>(\n<ol-item>.*<\/ol-item>)*)/g, (match) => {
      const items = match.replace(/<\/?ol-item>/g, (m) => m === '<ol-item>' ? '<li>' : '</li>');
      return `<ol>${items}</ol>`;
    });

    // Paragraphs
    const paragraphs = text.split(/\n{2,}/);
    return paragraphs
      .map(p => {
        p = p.trim();
        if (!p) return '';
        if (p.startsWith('<h1>') || p.startsWith('<h2>') || p.startsWith('<h3>') ||
          p.startsWith('<ul>') || p.startsWith('<ol>') || p.startsWith('<pre>')) {
          return p;
        }
        return `<p>${p.replace(/\n/g, '<br>')}</p>`;
      })
      .join('');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.VentureMindChat = new AIChatStudio();
});

