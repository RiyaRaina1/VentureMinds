<div align="center">

# ⚡ VentureMind AI

### YOUR AI CO-FOUNDER. YOUR STRATEGIC ADVANTAGE.

**Turn ambitious startup ideas into validated, data-driven business strategies.**

An autonomous AI co-founder platform built for founders who want to think deeper, move faster, and build smarter.

<br>

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Groq](https://img.shields.io/badge/Groq_AI-F55036?style=for-the-badge)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)

<br>

**VALIDATE · ANALYZE · SIMULATE · STRATEGIZE · BUILD**

</div>

---

## ◈ The Vision

Building a startup means making hundreds of high-stakes decisions with limited time, incomplete information, and constrained resources.

**VentureMind AI** is designed to give founders an intelligent strategic workspace to evaluate ideas, understand competitive positioning, explore financial scenarios, and brainstorm their next move with an AI advisor.

Instead of scattering research, calculations, and strategic discussions across different tools, VentureMind brings core founder workflows into one platform.

> **Our mission:** Make sophisticated startup thinking more accessible, structured, and actionable.

---

## ✦ What You Can Do

<table>
<tr>
<td width="50%" valign="top">

### 🧠 AI Co-Founder

Brainstorm startup concepts, challenge assumptions, explore strategic decisions, and work through difficult founder questions with an AI advisor powered by Groq.

### 🚀 Startup Validation

Structure startup ideas, examine business assumptions, and identify questions that deserve validation before investing significant resources.

### 🏰 Competitive Moat Analysis

Explore differentiation, competitive positioning, defensibility, and potential sources of sustainable business advantage.

</td>
<td width="50%" valign="top">

### 📊 Financial Intelligence

Model SaaS business scenarios using deterministic financial calculations and examine the unit economics behind potential growth.

### 💬 AI Chat Studio

Interact with streamed AI responses, maintain persistent conversations, and revisit previous discussions.

### 💾 Persistent Startup Workspace

Store startup records, chat sessions, and messages in MySQL so important context can survive beyond an individual interaction.

</td>
</tr>
</table>

---

## ⚡ AI Chat Studio — Phase 2

VentureMind's Phase 2 introduces a real AI Chat Studio integrated with the Groq inference API and MySQL persistence.

### Key capabilities

- **Real AI inference:** Connects to Groq using a configurable language model.
- **Streaming responses:** Uses Server-Sent Events (SSE) to deliver responses incrementally.
- **Persistent conversations:** Saves chat sessions and messages in MySQL.
- **Conversation history:** Retrieves messages in chronological order.
- **Startup context:** Supports associating a chat session with a startup.
- **Session management:** Supports creating, listing, retrieving, and deleting chat sessions.
- **Error handling:** Includes handling for AI configuration and runtime failures.

### AI model configuration

| Setting | Value |
|---|---|
| AI provider | Groq API |
| Default documented model | `openai/gpt-oss-120b` |
| Alternative documented model | `llama-3.3-70b-versatile` |
| Streaming protocol | Server-Sent Events (SSE) |
| Conversation persistence | MySQL |

The model can be configured through the backend environment, subject to availability and access in your Groq account.

---

## 🏗️ System Architecture

VentureMind uses a lightweight frontend connected to a Python API backend. The backend coordinates business logic, AI inference, and persistent storage.

```text
┌───────────────────────────────────────────────────────────┐
│                    FRONTEND                               │
│                                                           │
│     HTML5 · CSS3 · Vanilla JavaScript                     │
│                                                           │
│     Application UI · Charts · Wizard · AI Chat Studio     │
└──────────────────────────┬────────────────────────────────┘
                           │
                     HTTP / SSE
                           │
                           ▼
┌───────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                         │
│                                                           │
│     Health API · Startup CRUD · Simulations · Chat        │
│                                                           │
│     Python Services · SQLAlchemy ORM · Error Handling     │
└──────────────────────┬───────────────────┬────────────────┘
                       │                   │
                       ▼                   ▼
┌────────────────────────────┐  ┌───────────────────────────┐
│        MYSQL DATABASE      │  │       GROQ AI API         │
│                            │  │                           │
│  startups                  │  │  Language Model Inference │
│  chat_sessions             │  │  Streaming AI Responses   │
│  chat_messages             │  │                           │
└────────────────────────────┘  └───────────────────────────┘
```

### How it works

1. A founder interacts with the web interface.
2. The frontend sends requests to the FastAPI backend.
3. The backend routes the request to the relevant application service.
4. AI-related requests use the configured Groq model.
5. SQLAlchemy manages database interactions with MySQL.
6. Chat responses can stream to the frontend using SSE.
7. Startup data and conversation records are persisted in the database.

---

## 🧰 Technology Stack

<table>
<tr>
<th>Layer</th>
<th>Technology</th>
<th>Purpose</th>
</tr>
<tr>
<td>Frontend</td>
<td>HTML5</td>
<td>Application structure</td>
</tr>
<tr>
<td>Frontend</td>
<td>CSS3</td>
<td>Visual design, layouts, and styling</td>
</tr>
<tr>
<td>Frontend</td>
<td>Vanilla JavaScript</td>
<td>Interactions, charts, wizard, and chat UI</td>
</tr>
<tr>
<td>Backend</td>
<td>Python</td>
<td>Application logic and services</td>
</tr>
<tr>
<td>API Framework</td>
<td>FastAPI</td>
<td>HTTP APIs and request handling</td>
</tr>
<tr>
<td>AI Inference</td>
<td>Groq API / LPU</td>
<td>Language model inference</td>
</tr>
<tr>
<td>Streaming</td>
<td>Server-Sent Events</td>
<td>Incremental AI response delivery</td>
</tr>
<tr>
<td>ORM</td>
<td>SQLAlchemy</td>
<td>Database models and sessions</td>
</tr>
<tr>
<td>Database</td>
<td>MySQL 8.x</td>
<td>Persistent application data</td>
</tr>
<tr>
<td>Database Driver</td>
<td>PyMySQL</td>
<td>Python-to-MySQL connectivity</td>
</tr>
<tr>
<td>Configuration</td>
<td>python-dotenv</td>
<td>Local environment configuration</td>
</tr>
<tr>
<td>Deployment</td>
<td>Vercel</td>
<td>Deployment target for the backend project</td>
</tr>
<tr>
<td>Database Hosting</td>
<td>Aiven MySQL</td>
<td>Managed MySQL database service</td>
</tr>
</table>

---

## 📡 API Reference

The backend exposes API areas for health checks, startup management, financial simulations, and AI conversations.

### Health and startup APIs

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Check backend health |
| `POST` | Startup routes | Create a startup record |
| `GET` | Startup routes | Retrieve startup records |
| `PUT` | Startup routes | Update a startup record |
| `DELETE` | Startup routes | Delete a startup record |

The exact startup route paths depend on the route definitions in the backend.

### Financial simulations

The simulation module provides deterministic SaaS financial calculations for exploring business scenarios and unit economics.

### AI Chat Studio

Base path: `/api/chat`

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/chat/sessions` | Create a persistent chat session |
| `GET` | `/api/chat/sessions` | List recent chat sessions |
| `GET` | `/api/chat/sessions/{id}` | Retrieve session metadata |
| `GET` | `/api/chat/sessions/{id}/messages` | Retrieve message history |
| `DELETE` | `/api/chat/sessions/{id}` | Delete a session and its messages |
| `POST` | `/api/chat/sessions/{id}/messages/stream` | Stream an AI response using SSE |

For exact request schemas, response formats, and available endpoints, consult the running FastAPI OpenAPI documentation, commonly available at `/docs`.

---

## 🗂️ Project Structure

The following is a representative overview of the project modules documented for VentureMind AI.

```text
VentureMinds/
│
├── index.html
│
├── css/
│   └── styles.css
│
├── js/
│   ├── app.js
│   ├── ai-chat.js
│   ├── charts.js
│   └── wizard.js
│
├── backend/
│   ├── main.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py
│   │
│   ├── routes/
│   │   ├── health.py
│   │   ├── startups.py
│   │   ├── simulation.py
│   │   └── chat.py
│   │
│   ├── services/
│   │   ├── ai_service.py
│   │   └── chat_service.py
│   │
│   ├── models/
│   │   ├── startup.py
│   │   ├── chat.py
│   │   └── validation.py
│   │
│   ├── .env.example
│   └── requirements.txt
│
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
└── README.md
```

The structure above summarizes the documented modules; confirm the actual repository for the complete and current file tree.

---

## ⚙️ Environment Configuration

VentureMind uses environment variables to configure database connectivity, AI inference, and frontend access.

Create a local `backend/.env` file for development.

```dotenv
# Database connection
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:PORT/DATABASE

# Frontend origin allowed by backend CORS configuration
FRONTEND_URL=http://127.0.0.1:5500

# Groq API
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

### Environment variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy connection string for MySQL |
| `GROQ_API_KEY` | Secret key used to authenticate with Groq |
| `GROQ_MODEL` | Model identifier for AI inference |
| `FRONTEND_URL` | Frontend origin used by the backend's CORS configuration |

### Production configuration

For a Vercel backend deployment:

1. Open the Vercel project.
2. Navigate to **Settings → Environment Variables**.
3. Add the required environment variables.
4. Select the intended deployment environments.
5. Redeploy after changing environment variables.

For managed MySQL, use the connection details provided by your database host and follow its TLS requirements.

**Never put database credentials or AI API keys in frontend JavaScript.**

The browser frontend must use the deployed backend API URL rather than `localhost` when running in production.

---

## 🚀 Getting Started

### Prerequisites

Before running the application locally, install:

- Python
- MySQL 8.x or a compatible MySQL service
- Node.js if running the browser audit script
- A Groq API key for AI-powered features
- A Git client

### 1. Clone the repository

```bash
git clone https://github.com/RiyaRaina1/VentureMinds.git
cd VentureMinds
```

### 2. Set up the backend environment

**Windows PowerShell**

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux**

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Create `backend/.env` and fill in valid values for your MySQL database and Groq API credentials.

Make sure the database exists and the configured user has permission to create the tables required by the application.

### 4. Start the FastAPI backend

If `backend/main.py` exposes a FastAPI instance named `app`, run from the `backend` directory:

```bash
uvicorn main:app --reload
```

Use the actual ASGI import path defined by your repository if it differs.

### 5. Launch the frontend

Open the repository root in a static web server, such as VS Code Live Server.

Make sure the frontend's API base URL points to your local backend and that the backend CORS configuration permits the frontend origin.

---

## 🧪 Testing & Quality Assurance

The project documentation describes a backend test suite, database persistence tests, and a browser automation audit.

### Backend tests

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python test_backend.py
```

The suite is intended to test:

- Health endpoint responses
- Startup project CRUD operations
- Deterministic financial simulations
- Chat session creation and retrieval
- Chat message history
- SSE streaming and AI message persistence
- AI configuration and runtime error handling
- Chat session deletion and message cascading
- MySQL persistence and foreign-key behavior

### Database persistence test

```bash
python test_persistence.py
```

This test is intended to validate persistence of startup and chat records across simulated engine shutdowns and backend restarts.

### Browser automation audit

```bash
node browser_audit.js
```

The audit is intended to exercise:

- Application navigation
- Theme switching
- Command Palette interactions
- AI Chat Studio behavior
- Browser-side JavaScript error detection

Run each command from the directory where the corresponding script exists, and verify that the required test dependencies are installed.

---

## 🔐 Security & Reliability

Security is a core requirement for any application handling founder information and AI credentials.

- Keep real `.env` files out of version control.
- Commit only sanitized configuration examples.
- Store secrets in the deployment platform's environment variables.
- Never expose API keys, database passwords, or full connection URLs in screenshots or logs.
- Use TLS when required by the database provider.
- Restrict CORS to the frontend origins that need access.
- Validate incoming requests and handle external API errors safely.
- Rotate credentials if they are accidentally exposed.
- Review database permissions and backup policies before production use.

---

## 🛣️ Roadmap

Potential next steps toward a more production-ready platform:

- [ ] Complete and verify the deployed backend.
- [ ] Deploy the static frontend and configure its production API URL.
- [ ] Verify MySQL connectivity and table initialization in the hosted environment.
- [ ] Add automated CI checks for backend and frontend tests.
- [ ] Improve observability for database, API, and streaming failures.
- [ ] Expand API documentation and deployment troubleshooting guidance.
- [ ] Continue refining startup validation and founder strategy workflows.

---

## 🤝 Contributing

Contributions, bug reports, and ideas are welcome.

1. Keep changes focused and explain the problem they solve.
2. Never commit secrets or production data.
3. Run relevant tests before submitting changes.
4. Update documentation when configuration or API behavior changes.
5. Include clear reproduction steps when reporting bugs.

---

## 📄 License

A license has not yet been specified in the provided project details.

Add a `LICENSE` file before representing this project as open source or granting explicit reuse rights.

---

<div align="center">

### Build boldly. Validate rigorously. Think strategically.

**VentureMind AI**

*Your next big idea deserves a sharper mind.*

</div>
