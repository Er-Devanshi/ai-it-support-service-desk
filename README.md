# ServiceDesk-AI

> **⚠️ This project is currently under active development — Phase 1 Foundation.**

An AI-powered IT Support Desk built as a college mini-project. ServiceDesk-AI aims to help employees resolve common IT problems through a conversational interface, backed by an organisational knowledge base and (in later phases) an LLM-powered AI agent.

---

## Problem Statement

IT support desks in organisations are overwhelmed with repetitive, routine queries — password resets, VPN issues, printer problems — that consume significant technician time. Employees often wait hours for a response to problems they could solve themselves with the right guidance.

ServiceDesk-AI addresses this by providing an intelligent first-line support agent that can:
- Understand natural language IT problems.
- Search an organisational knowledge base for relevant solutions.
- Walk employees through step-by-step troubleshooting.
- Create and track support tickets automatically.
- Escalate unresolved or sensitive issues to a human technician.

---

## Objectives

- Build a working conversational IT support interface.
- Integrate an LLM with Retrieval-Augmented Generation (RAG) over a structured knowledge base.
- Maintain multi-turn conversation context per session.
- Implement tool-calling for authorised IT actions (account unlock, password reset).
- Apply security boundaries and permission controls.
- Provide a clean, modular codebase that can be extended across development phases.

---

## Current Features (Phase 1)

| Feature | Status |
|---|---|
| FastAPI backend | ✅ Working |
| `GET /api/health` endpoint | ✅ Working |
| `POST /api/chat` endpoint | ✅ Working (rule-based stub) |
| Chat frontend (browser) | ✅ Working |
| Frontend ↔ backend communication | ✅ Working |
| Typing indicator and status badge | ✅ Working |
| Quick-topic sidebar | ✅ Working |
| Sample IT knowledge base (plain text) | ✅ Created |
| LLM integration | ❌ Phase 2 |
| RAG / vector database | ❌ Phase 2 |
| Multi-turn conversation memory | ❌ Phase 2 |
| Ticket management | ❌ Phase 3 |
| Authentication | ❌ Phase 3 |
| Autonomous IT actions / tool calling | ❌ Phase 4 |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Data validation | Pydantic v2 |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Knowledge base (Phase 1) | Plain text |
| Vector database (Phase 2) | ChromaDB / FAISS (planned) |
| LLM (Phase 2) | OpenAI API / Ollama (planned) |
| Database (Phase 3) | SQLite → PostgreSQL (planned) |
| Agent framework (Phase 4) | LangChain / LlamaIndex (planned) |

---

## Project Structure

```
ai-it-support-service-desk/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, CORS, router registration
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py        # GET /api/health
│   │   │   └── chat.py          # POST /api/chat
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── chat_service.py  # Chat logic (keyword rules → LLM in Phase 2)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── chat.py          # Pydantic request/response models
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── logger.py        # Centralised logging
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── index.html               # Chat UI
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js               # API calls, chat rendering
│
├── data/
│   └── knowledge_base/
│       └── sample_it_faq.txt    # 10 IT support FAQs (seed data for RAG)
│
├── docs/
│   └── architecture.md          # Architecture, components, roadmap
│
├── tests/                       # Test directory (Phase 2+)
│
├── .env.example                 # Environment variable template
├── .gitignore
├── README.md
└── LICENSE
```

---

## How to Run the Project Locally

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- A modern web browser

### Step 1 — Clone the repository

```bash
git clone https://github.com/your-username/ai-it-support-service-desk.git
cd ai-it-support-service-desk
```

### Step 2 — Set up the Python environment

```bash
# Create a virtual environment
python -m venv .venv

# Activate it
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On macOS / Linux:
source .venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r backend/requirements.txt
```

### Step 4 — Start the backend server

```bash
uvicorn app.main:app --reload
```

Run this command from the `backend/` directory:

```bash
cd backend
uvicorn app.main:app --reload
```

The API will be available at: `http://127.0.0.1:8000`

You can explore the auto-generated API docs at: `http://127.0.0.1:8000/docs`

### Step 5 — Open the frontend

Open `frontend/index.html` directly in your browser:

```
# Option A — just double-click the file in your file explorer

# Option B — from the terminal (Windows PowerShell):
Start-Process "frontend\index.html"
```

> The frontend connects to `http://127.0.0.1:8000` by default. Make sure the backend is running before opening the page.

### Step 6 — Test it

1. The status badge in the top-right should turn **green** (Backend online).
2. Type a message like `"My Wi-Fi is not working"` and click **Send**.
3. The backend returns a structured troubleshooting reply.
4. Click any item in the **Quick Topics** sidebar to pre-fill the input.

---

## API Reference

### `GET /api/health`

Returns the current running status of the backend.

**Response:**
```json
{
  "status": "running",
  "service": "ServiceDesk-AI",
  "version": "0.1.0",
  "phase": "Phase 1 — Foundation"
}
```

### `POST /api/chat`

Accepts a user message and returns a structured IT support response.

**Request body:**
```json
{
  "message": "My Wi-Fi is not working"
}
```

**Response body:**
```json
{
  "reply": "Try the following steps for Wi-Fi issues:\n1. Restart your device...",
  "category": "network",
  "status": "answered",
  "note": "Phase 1 — rule-based response. LLM/RAG not yet connected."
}
```

---

## Future Scope

- **Phase 2:** LLM integration (OpenAI / local model), RAG pipeline with ChromaDB, multi-turn conversation memory.
- **Phase 3:** SQLite/PostgreSQL database, ticket creation and tracking, user authentication (JWT).
- **Phase 4:** LangChain agent loop, tool calling (account unlock, password reset), human escalation workflow, audit logging.
- **Phase 5:** Dockerisation, CI/CD with GitHub Actions, HTTPS, rate limiting, production monitoring.

---

## Contributing

This is a college mini-project in active development. Contributions, suggestions, and feedback are welcome.

---

## License

MIT License — see `LICENSE` for details.
