# ServiceDesk-AI

> **Status: Phase 2 — Autonomous Multi-Agent IT Operations (Under Development)**

An AI-powered IT Support Desk built as a college mini-project.  
ServiceDesk-AI provides a conversational interface backed by LangGraph multi-agent orchestration, Google Gemini LLM integration, RAG knowledge retrieval, JWT authentication, ticket management, and a human-in-the-loop approval system.

---

## Problem Statement

IT support desks are overwhelmed with repetitive routine queries — password resets, VPN issues, printer problems — that consume significant technician time. Employees often wait hours for resolvable problems.

ServiceDesk-AI addresses this by providing an intelligent first-line support agent that:
- Understands natural language IT problems
- Applies ITIL-compliant triage and priority classification
- Searches an organisational IT knowledge base (RAG)
- Creates and tracks support tickets automatically
- Escalates security incidents and unresolvable issues to human technicians
- Enforces permission boundaries and approval workflows

---

## Current Features (Phase 2)

| Feature | Status |
|---|---|
| FastAPI backend with 7 REST API routers | ✅ Working |
| LangGraph 9-node multi-agent workflow | ✅ Working |
| JWT authentication + RBAC (3 roles) | ✅ Working |
| AI triage with ITIL priority matrix | ✅ Working |
| Chat-to-ticket integration (SQLite) | ✅ Working |
| Persistent conversation history (SQLite) | ✅ Working |
| Human-in-the-loop approval workflow | ✅ Working |
| Simulated IT action registry (5 actions) | ✅ Working |
| Gemini / OpenAI / Ollama / Mock LLM | ✅ Working |
| RAG retrieval interface (plug-in contract) | ✅ Interface ready |
| Audit logging | ✅ Working |
| Login modal + auth frontend | ✅ Working |
| Ticket / approval info panel (frontend) | ✅ Working |
| 40+ automated tests (no live API required) | ✅ Passing |
| ChromaDB / FAISS vector store | ⏳ Pending (Sanskriti Agarwal) |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI 0.115+, Uvicorn |
| AI Orchestration | LangGraph 1.x |
| LLM Providers | Google Gemini (primary), OpenAI, Ollama, Mock |
| Data Validation | Pydantic v2 |
| Database | SQLAlchemy 2.x + SQLite |
| Authentication | PyJWT + bcrypt |
| HTTP Client | httpx |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Testing | pytest + FastAPI TestClient |
| Knowledge Base (Phase 2) | Plain-text FAQ (RAG interface ready) |
| Vector DB (Phase 3) | ChromaDB / FAISS (planned — Sanskriti Agarwal) |

---

## Project Structure

```
ai-it-support-service-desk/
├── backend/
│   ├── app/
│   │   ├── config.py               Environment-based configuration
│   │   ├── main.py                 FastAPI app, CORS, router registration
│   │   ├── db/
│   │   │   ├── session.py          SQLAlchemy engine and session factory
│   │   │   └── init_db.py          Table creation and demo user seeding
│   │   ├── models/
│   │   │   ├── orm.py              SQLAlchemy ORM (6 tables)
│   │   │   ├── chat.py             Chat request/response Pydantic models
│   │   │   ├── auth_schemas.py     Auth Pydantic schemas
│   │   │   └── ticket_schemas.py   Ticket/approval Pydantic schemas
│   │   ├── routes/
│   │   │   ├── health.py           GET /api/health
│   │   │   ├── chat.py             POST /api/chat
│   │   │   ├── auth.py             POST /api/auth/register, /login, /me
│   │   │   ├── tickets.py          Full ticket CRUD lifecycle
│   │   │   ├── approvals.py        Approval workflow
│   │   │   ├── actions.py          Simulated IT action allowlist
│   │   │   └── audit.py            Audit log (admin only)
│   │   ├── services/
│   │   │   ├── auth_service.py     JWT, bcrypt, RBAC
│   │   │   ├── chat_service.py     Chat orchestration entry point
│   │   │   ├── conversation_service.py  Multi-turn conversation history
│   │   │   ├── ticket_service.py   Ticket lifecycle management
│   │   │   ├── approval_service.py Human-in-the-loop approvals
│   │   │   ├── audit_service.py    Audit event persistence
│   │   │   ├── triage_service.py   AI triage + ITIL priority matrix
│   │   │   ├── llm/                Provider abstraction (Gemini/OpenAI/Ollama/Mock)
│   │   │   ├── rag/                RAG retrieval interface contract
│   │   │   ├── actions/            Simulated IT action registry
│   │   │   └── workflow/           LangGraph StateGraph (9 nodes)
│   │   └── utils/
│   │       └── logger.py
│   └── requirements.txt
├── frontend/
│   ├── index.html                  Chat UI with login modal
│   ├── css/style.css
│   └── js/app.js                   Auth, chat, ticket panel, mode badge
├── data/knowledge_base/
│   └── sample_it_faq.txt           10 IT support FAQs (RAG seed data)
├── docs/
│   └── architecture.md             Architecture, components, roadmap
├── tests/                          40+ pytest tests
├── MENTOR_DEMO.md                  5-minute demo guide
├── pyproject.toml                  pytest configuration
├── .env.example                    Environment variable template
├── .gitignore
├── LICENSE
└── README.md
```

---

## Prerequisites

- Python 3.11 or higher (3.13 tested)
- pip

---

## Installation

```powershell
# 1. Clone the repository
git clone https://github.com/your-username/ai-it-support-service-desk.git
cd ai-it-support-service-desk

# 2. Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r backend/requirements.txt
```

---

## Environment Configuration

```powershell
# Copy the example and edit
copy .env.example .env
```

Key settings in `.env`:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | Active LLM: `gemini`, `mock`, `openai`, `ollama` |
| `DEMO_MODE` | `false` | Set `true` to always use mock responses |
| `GEMINI_API_KEY` | _(empty)_ | Your Google AI Studio key (falls back to mock if unset) |
| `DATABASE_URL` | SQLite | Path to the SQLite database file |
| `JWT_SECRET_KEY` | dev default | Change in production |
| `RAG_ENABLED` | `true` | Set `false` to disable knowledge base retrieval |

### Gemini API Setup (optional)

1. Visit https://aistudio.google.com/ and create a free API key
2. Add to `.env`: `GEMINI_API_KEY=AIza...`
3. Set `DEMO_MODE=false`
4. Restart the backend

Without a key, the system runs in **Mock/Demo mode** — fully functional for testing and demonstration.

---

## Running the Backend

```powershell
cd backend
uvicorn app.main:app --reload
```

- API base: `http://127.0.0.1:8000`
- Interactive docs: `http://127.0.0.1:8000/docs`

On first start, three demo users are seeded into the database automatically.

---

## Running the Frontend

Open `frontend/index.html` directly in your browser:

```powershell
Start-Process "frontend\index.html"
```

The login modal will appear. Use any of the demo accounts.

---

## Demo Accounts

| Username | Password | Role |
|---|---|---|
| `employee` | `employee123` | Employee |
| `support_agent` | `agent123` | Support Agent |
| `admin` | `admin123` | Administrator |

---

## Running Tests

```powershell
# From the repository root
python -m pytest tests/ -v
```

All tests run **without a live API key** using the MockLLMProvider and in-memory SQLite.

---

## API Endpoints

| Method | Path | Description | Auth required |
|---|---|---|---|
| GET | `/api/health` | Service status and LLM mode | No |
| POST | `/api/chat` | Chat with the AI support agent | Optional |
| POST | `/api/auth/register` | Register a new user | No |
| POST | `/api/auth/login` | Login and receive JWT | No |
| GET | `/api/auth/me` | Current user profile | Yes |
| GET | `/api/tickets` | List tickets (RBAC-filtered) | Optional |
| POST | `/api/tickets` | Create a new ticket | Optional |
| GET | `/api/tickets/{id}` | Get ticket + history | Optional |
| POST | `/api/tickets/{id}/status` | Update ticket status | Yes |
| POST | `/api/tickets/{id}/resolve` | Resolve ticket | Agent/Admin |
| POST | `/api/tickets/{id}/escalate` | Escalate ticket | Optional |
| GET | `/api/approvals` | List pending approvals | Agent/Admin |
| POST | `/api/approvals/{id}/decision` | Approve or reject | Agent/Admin |
| GET | `/api/actions` | List permitted IT actions | No |
| POST | `/api/actions/{name}/execute` | Execute low-risk action | Optional |
| GET | `/api/audit` | Audit log | Admin only |

---

## RAG Integration (for Sanskriti Agarwal)

The RAG retrieval interface is defined in:
```
backend/app/services/rag/retrieval_interface.py
```

To plug in your ChromaDB/FAISS implementation:

```python
from app.services.rag.retrieval_interface import register_custom_retriever, BaseRetriever

class MyChromaRetriever(BaseRetriever):
    def retrieve(self, query, context=None, top_k=3):
        # your ChromaDB implementation here
        ...

register_custom_retriever(MyChromaRetriever())
```

Call `register_custom_retriever()` at application startup (e.g. in `main.py`'s lifespan handler).

To disable retrieval: set `RAG_ENABLED=false` in `.env`.

---

## Known Limitations

- IT actions (account unlock, password reset, access grant) are **simulated** against a synthetic in-memory directory. No real enterprise systems are connected.
- Conversation history is loaded per-request (no real-time streaming).
- No summarisation of long conversation history yet.
- JWT is stored in `sessionStorage` — cleared when the browser tab closes.
- The vector database (ChromaDB/FAISS) implementation is pending and will be delivered by a separate team member.
- Not production-ready: no HTTPS, no rate limiting, no containerisation.

---

## Future Scope

- **Sanskriti's RAG pipeline**: ChromaDB/FAISS for semantic knowledge search
- Password reset email notifications
- Docker + docker-compose for deployment
- CI/CD with GitHub Actions
- Production HTTPS + rate limiting
- Real-time ticket updates with WebSockets
- Agent-based assignment and routing UI

---

## License

MIT License — see `LICENSE` for details.
