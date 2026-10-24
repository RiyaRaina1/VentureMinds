# VentureMind AI — Autonomous AI Co-Founder Platform
## Phase 2: Real AI Chat Studio + Groq LPU Integration + MySQL Persistence

VentureMind AI is an autonomous AI co-founder platform designed to help founders validate startup concepts, analyze competitive moats, project 36-month financials, optimize unit economics, and brainstorm strategy in real-time with an elite AI advisor.

> **Phase 2 Implementation**: Real AI Chat Studio powered by **Groq LPU Engine** (`openai/gpt-oss-120b`), asynchronous Server-Sent Events (SSE) streaming, local MySQL chat session and message persistence (`chat_sessions`, `chat_messages`), founder/startup context integration, and strict error handling.

---

## 🏗️ Architecture Overview

```
                      ┌──────────────────────────────────────────┐
                      │            Frontend (Vanilla)            │
                      │  - index.html (Modern HUD layout)        │
                      │  - css/styles.css (Neon Glassmorphism)   │
                      │  - js/ai-chat.js (Real SSE Streaming UI) │
                      │  - js/app.js, charts.js, wizard.js       │
                      └─────────────────────┬────────────────────┘
                                            │ HTTP / SSE Stream
                                            │ (CORS Allowed)
                                            ▼
                      ┌──────────────────────────────────────────┐
                      │          Backend (FastAPI Engine)        │
                      │  - main.py (App & Middleware Gateway)    │
                      │  - routes/health.py (Health Check API)   │
                      │  - routes/startups.py (Project CRUD)     │
                      │  - routes/simulation.py (Deterministic)  │
                      │  - routes/chat.py (AI Studio & SSE)      │
                      │  - services/ai_service.py (Groq Engine)  │
                      │  - services/chat_service.py (MySQL Sync) │
                      └─────────────┬────────────────┬───────────┘
                                    │                │
                     SQLAlchemy ORM │                │ Async HTTP Stream
                                    ▼                ▼
       ┌──────────────────────────────┐    ┌───────────────────────────┐
       │   MySQL 8.0 (venturemind)    │    │      Groq LPU API         │
       │  - startups                  │    │  (openai/gpt-oss-120b /   │
       │  - chat_sessions             │    │   llama-3.3-70b-versatile)│
       │  - chat_messages             │    └───────────────────────────┘
       └──────────────────────────────┘
```

---

## 📡 AI Chat Studio API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat/sessions` | Initialize a new persistent chat session (optional startup ID & title) |
| `GET` | `/api/chat/sessions` | Retrieve all chat sessions sorted by recent activity |
| `GET` | `/api/chat/sessions/{id}` | Retrieve specific chat session metadata |
| `GET` | `/api/chat/sessions/{id}/messages` | Retrieve full chronological message history for a session |
| `DELETE` | `/api/chat/sessions/{id}` | Delete a chat session and cascade delete all messages |
| `POST` | `/api/chat/sessions/{id}/messages/stream` | Stream real-time Groq response tokens via SSE and persist to MySQL |

---

## 🔑 Environment Configuration (`backend/.env`)

```env
# Database Configuration (Local MySQL Server)
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/venturemind

# Frontend CORS Origin
FRONTEND_URL=http://127.0.0.1:5500

# Groq AI Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```
*(Notice: Never commit your real `.env` file — it is strictly gitignored).*

---

## 🧪 Testing Suite

### 1. Run Complete Backend Automated Tests (Phase 1 + Phase 2)
```powershell
cd backend
.\venv\Scripts\activate
python test_backend.py
```
This tests:
- Health API (`GET /api/health`)
- Startup Project CRUD (`POST`, `GET`, `PUT`, `DELETE`)
- Deterministic SaaS financial simulation calculations
- Chat session creation and retrieval
- Chat message history retrieval
- SSE streaming execution with Groq models and assistant message persistence
- AI configuration and runtime error handling
- Chat session deletion and message cascade
- Direct MySQL queries and Foreign Key verification

### 2. Run MySQL Database Persistence Test
```powershell
python test_persistence.py
```
Validates that `Startup`, `ChatSession`, and `ChatMessage` records survive complete engine shutdown and simulated backend restarts.

### 3. Run Headless Browser Automation Audit
```powershell
node browser_audit.js
```
Automates Headless Chrome via Chrome DevTools Protocol to verify navigation, theme switching, Command Palette, and AI Chat Studio functionality with 0 JavaScript errors.
