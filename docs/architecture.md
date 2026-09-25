# ServiceDesk-AI — Architecture Document

> **Status:** Phase 1 — Foundation (Under Development)  
> **Last updated:** September 2026

---

## 1. Project Objective

ServiceDesk-AI is an AI-powered IT support desk designed to help employees resolve common IT problems through a conversational interface. The system aims to reduce the load on human IT administrators by automatically handling routine queries, searching an organisational knowledge base, and escalating complex or sensitive issues to a human technician.

---

## 2. Current Architecture (Phase 1)

Phase 1 establishes a working end-to-end skeleton — a real HTTP request flows from the browser to the backend and a structured response is returned. No LLM or AI model is connected yet.

```
┌─────────────────────────────────────────────────────────────────┐
│                        User's Browser                          │
│                                                                 │
│   frontend/index.html                                           │
│   frontend/css/style.css    ──── static files (no server)       │
│   frontend/js/app.js                                            │
│          │                                                      │
│          │  HTTP  POST /api/chat                                │
│          │  HTTP  GET  /api/health                              │
└──────────┼──────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (Python)                       │
│                                                                 │
│   app/main.py          — app entry point, CORS, router include  │
│   app/routes/health.py — GET  /api/health                       │
│   app/routes/chat.py   — POST /api/chat                         │
│   app/models/chat.py   — Pydantic request/response models       │
│   app/services/        — business logic                         │
│     chat_service.py    — keyword-based response matching (stub) │
│   app/utils/           — shared utilities                       │
│     logger.py          — centralised logging                    │
│                                                                 │
│   [Phase 1 — no database, no LLM, no vector store]             │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 1 request flow

1. User types a message in the browser and clicks **Send**.
2. `app.js` sends `POST /api/chat` with `{ "message": "..." }`.
3. FastAPI validates the request with the `ChatRequest` Pydantic model.
4. `chat_service.process_message()` matches keywords to known IT topics and returns a canned reply.
5. The `ChatResponse` Pydantic model serialises the result to JSON.
6. `app.js` renders the reply with a category tag and status tag in the chat window.

---

## 3. Planned Architecture (Phase 2 and beyond)

The diagram below shows the full intended system. Components marked **[future]** are not yet implemented.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            User's Browser / Client App                       │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │ HTTPS
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          FastAPI Backend                                      │
│                                                                              │
│  ┌───────────────┐    ┌──────────────────────────────────────────────────┐  │
│  │  Auth Layer   │    │              Agent Orchestrator [future]          │  │
│  │  JWT / OAuth  │───▶│  Manages conversation state, tool calls,         │  │
│  │  [future]     │    │  multi-turn context, and escalation logic         │  │
│  └───────────────┘    └────────────────┬─────────────────────────────────┘  │
│                                        │                                     │
│              ┌─────────────────────────┼──────────────────────┐             │
│              ▼                         ▼                       ▼             │
│  ┌───────────────────┐   ┌─────────────────────┐  ┌────────────────────┐   │
│  │   LLM Service     │   │   RAG Service        │  │  Ticket Service    │   │
│  │   OpenAI / local  │   │   ChromaDB / FAISS   │  │  Create / Update   │   │
│  │   [future]        │   │   Embeddings [future]│  │  tickets [future]  │   │
│  └───────────────────┘   └─────────────────────┘  └────────────────────┘   │
│                                        │                                     │
│                           ┌────────────▼────────────┐                       │
│                           │   Knowledge Base         │                       │
│                           │   data/knowledge_base/   │                       │
│                           │   (plain text → Phase 1) │                       │
│                           │   (vector DB → Phase 2+) │                       │
│                           └─────────────────────────┘                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Main Components

| Component | Location | Status |
|---|---|---|
| Frontend chat UI | `frontend/` | Phase 1 — working |
| FastAPI application | `backend/app/main.py` | Phase 1 — working |
| Health check endpoint | `backend/app/routes/health.py` | Phase 1 — working |
| Chat endpoint | `backend/app/routes/chat.py` | Phase 1 — working (stub) |
| Request/response models | `backend/app/models/chat.py` | Phase 1 — working |
| Chat service (logic) | `backend/app/services/chat_service.py` | Phase 1 — keyword rules only |
| Logger utility | `backend/app/utils/logger.py` | Phase 1 — working |
| IT knowledge base | `data/knowledge_base/sample_it_faq.txt` | Phase 1 — plain text |
| LLM integration | — | **Phase 2 — not started** |
| RAG / vector store | — | **Phase 2 — not started** |
| Conversation memory | — | **Phase 2 — not started** |
| Ticket management | — | **Phase 3 — not started** |
| Authentication / JWT | — | **Phase 3 — not started** |
| Tool calling / IT actions | — | **Phase 4 — not started** |
| Human escalation workflow | — | **Phase 4 — not started** |

---

## 5. Future AI / RAG Components

### 5.1 LLM Integration (Phase 2)
`chat_service.py` will be updated to call an LLM API (e.g. OpenAI `gpt-4o`, or a locally hosted model via Ollama). The keyword-matching stub will be replaced with a proper prompt-engineering approach.

### 5.2 Retrieval-Augmented Generation — RAG (Phase 2)
The plain-text knowledge base will be:
1. Chunked into overlapping passages.
2. Converted to embeddings using a sentence-transformer model.
3. Stored in a vector database (ChromaDB or FAISS).
4. Queried at chat time — the top-k relevant passages will be injected into the LLM prompt as context.

This allows the system to give accurate, source-grounded answers without relying solely on the LLM's parametric knowledge.

### 5.3 Conversation Memory (Phase 2)
Multi-turn context will be maintained per session using an in-memory store (Phase 2) and later a persistent database (Phase 3). This allows follow-up questions like "Can you explain step 3?" to work correctly.

### 5.4 Agent Orchestration (Phase 4)
A LangChain or LlamaIndex agent loop will be introduced. The agent will decide when to:
- Answer directly from the LLM.
- Retrieve documents from the knowledge base (RAG tool).
- Create a support ticket (ticket tool).
- Perform an authorised IT action (e.g. unlock account via LDAP).
- Escalate to a human technician.

---

## 6. Security Considerations

| Concern | Phase 1 status | Planned mitigation |
|---|---|---|
| API keys / credentials | Not present | `.env` + secret manager (Phase 2+) |
| Authentication | Not implemented | JWT tokens (Phase 3) |
| Authorisation | Not implemented | Role-based access control (Phase 3) |
| Input validation | Pydantic models | Sanitisation + max-length checks (ongoing) |
| CORS | Open (`*`) in Phase 1 | Restrict to known origins (Phase 2) |
| HTTPS | Not configured | TLS termination via reverse proxy (Phase 3) |
| LLM prompt injection | N/A — no LLM yet | Input sanitisation + guardrails (Phase 2) |
| Sensitive IT actions | Not implemented | Approval workflow + audit log (Phase 4) |

---

## 7. Planned Development Phases

### Phase 1 — Foundation (current)
- Project structure, FastAPI backend, basic frontend, health and chat endpoints, sample knowledge base, documentation.

### Phase 2 — AI Core
- LLM integration (OpenAI API or local model).
- RAG pipeline: chunk knowledge base → embeddings → ChromaDB.
- Multi-turn conversation memory.
- Improved prompt engineering.

### Phase 3 — Ticketing and Persistence
- SQLite / PostgreSQL database.
- Ticket creation, status tracking, and assignment.
- User authentication (JWT).
- Conversation history persistence.

### Phase 4 — Agents and Automation
- LangChain / LlamaIndex agent loop.
- Tool calling: account unlock, password reset (with approval).
- Human escalation workflow with email/Slack notification.
- Audit logging for all automated actions.
- RBAC — role-based access control.

### Phase 5 — Production Hardening
- Containerisation (Docker, docker-compose).
- CI/CD pipeline (GitHub Actions).
- HTTPS, rate limiting, monitoring, and alerting.
- Load testing and performance optimisation.
