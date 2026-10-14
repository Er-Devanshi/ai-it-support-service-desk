# ServiceDesk-AI — Architecture Document

> **Status:** Phase 2 — Autonomous Multi-Agent IT Operations  
> **Last updated:** September 2026

---

## 1. Project Objective

ServiceDesk-AI is an AI-powered IT support desk designed to help employees resolve common IT problems through a conversational interface. It reduces the load on human IT administrators by:
- Classifying issues and applying ITIL-compliant priority triage
- Providing step-by-step troubleshooting guidance
- Searching an organisational IT knowledge base (RAG)
- Creating and tracking persistent support tickets
- Enforcing human-in-the-loop approval for sensitive IT actions
- Escalating security incidents and unresolved issues to human technicians

---

## 2. Current Architecture (Phase 2)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                  Browser — frontend/index.html                               │
│  Login modal · Chat interface · Ticket/approval info panel · Mode badge      │
│                         │ JWT Bearer token (sessionStorage)                  │
│              HTTP   POST /api/chat   GET /api/health                         │
│                         │  GET|POST /api/auth/* /api/tickets/*               │
│                         │  GET|POST /api/approvals/* /api/actions/*          │
└─────────────────────────┼────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (Python)                                  │
│                                                                              │
│  app/main.py — app entry point, CORS, lifespan (DB init), 7 routers         │
│  app/config.py — environment-based configuration                             │
│                                                                              │
│  Routers:                                                                    │
│    /api/health   → health.py                                                 │
│    /api/chat     → chat.py → chat_service.py → LangGraph workflow           │
│    /api/auth/*   → auth.py → auth_service.py (JWT + bcrypt)                 │
│    /api/tickets/*→ tickets.py → ticket_service.py                           │
│    /api/approvals/* → approvals.py → approval_service.py                    │
│    /api/actions/* → actions.py → action_registry.py                         │
│    /api/audit    → audit.py → audit_service.py                              │
│                                                                              │
│  Database: SQLAlchemy 2.x + SQLite                                           │
│    Tables: users, tickets, ticket_status_history,                            │
│            approval_requests, audit_events, conversation_messages            │
└──────────────────────────────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    LangGraph Multi-Agent Workflow (9 nodes)                  │
│                                                                              │
│  START → intake → triage → [security_escalation | rag_retrieval]            │
│       → action_decision → [action_execution | response_generation]          │
│       → response_generation → ticket_creation → verification → END          │
│                                                                              │
│  Node responsibilities:                                                      │
│  1. intake           — load conversation history, save user message          │
│  2. triage           — ITIL category/priority, security detection            │
│  3. security_escalation — P1 SecOps escalation (deterministic rule)         │
│  4. rag_retrieval    — query knowledge base retriever                        │
│  5. action_decision  — detect IT action intent (unlock, check, grant)       │
│  6. action_execution — run low-risk action or create approval request        │
│  7. response_generation — LLM + history + RAG context → reply               │
│  8. ticket_creation  — persist ticket for explicit requests / escalations   │
│  9. verification     — save assistant reply, mark terminal                  │
└──────────────────────────────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Supporting Services                                   │
│                                                                              │
│  LLM Providers (provider-independent):                                       │
│    GeminiProvider  — Google Generative Language API (primary live provider)  │
│    OpenAIProvider  — OpenAI Chat Completions API                             │
│    OllamaProvider  — Local model server (llama3, mistral, gemma, etc.)      │
│    MockLLMProvider — Offline demo/test mode, clearly labelled                │
│    LLMFactory      — selects provider from LLM_PROVIDER env var             │
│                                                                              │
│  RAG Retrieval (plug-in contract):                                           │
│    BaseRetriever interface  — abstract contract for any vector store         │
│    SampleFAQRetriever       — keyword-based reference implementation         │
│    register_custom_retriever() — hook for Sanskriti's ChromaDB pipeline      │
│                                                                              │
│  IT Action Registry (simulated, allowlist-enforced):                         │
│    check_account_status   — LOW risk, no approval                           │
│    check_service_health   — LOW risk, no approval                           │
│    unlock_account         — MEDIUM risk, approval required                  │
│    reset_password         — MEDIUM risk, approval required                  │
│    grant_resource_access  — HIGH risk, approval required                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. LLM Provider Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | Active provider: `gemini`, `openai`, `ollama`, `mock` |
| `DEMO_MODE` | `false` | Force mock mode regardless of API keys |
| `GEMINI_API_KEY` | _(empty)_ | Falls back to mock if unset |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Model name |

When no API key is configured or `DEMO_MODE=true`, the system transparently falls back to `MockLLMProvider` and labels all responses accordingly. A mock response is **never** labelled as a live Gemini response.

---

## 4. RAG Integration Boundary (Sanskriti Agarwal)

The retrieval interface is in `backend/app/services/rag/retrieval_interface.py`.

```python
# Register your vector store retriever at startup:
from app.services.rag.retrieval_interface import register_custom_retriever

class MyChromaDBRetriever(BaseRetriever):
    def retrieve(self, query: str, context=None, top_k: int = 3) -> RetrievalResult:
        # Your ChromaDB/FAISS implementation here
        ...

register_custom_retriever(MyChromaDBRetriever())
```

Call `register_custom_retriever()` in `app/main.py`'s lifespan handler.

Set `RAG_ENABLED=false` in `.env` to disable retrieval entirely.

The workflow will always call `get_retriever()` — if no custom retriever is registered and `RAG_ENABLED=true`, it falls back to `SampleFAQRetriever` (keyword-based FAQ search over `data/knowledge_base/sample_it_faq.txt`).

---

## 5. Security Considerations

| Concern | Current status |
|---|---|
| API keys / credentials | Backend `.env` only — never in source code or frontend |
| JWT authentication | PyJWT + bcrypt — implemented and tested |
| RBAC | Employee / Support Agent / Admin roles enforced on all protected routes |
| Input validation | Pydantic models with length limits |
| CORS | Open `*` in development — restrict to specific origins in production |
| HTTPS | Not configured — add TLS termination via reverse proxy for production |
| LLM prompt injection | User inputs treated as untrusted; deterministic rules bypass LLM for security decisions |
| IT action authorization | Explicit allowlist; approval workflow for MEDIUM/HIGH risk; no shell execution |
| Sensitive information in logs | API keys and passwords never logged |
| SQLite database | Excluded from Git via `.gitignore` |

---

## 6. Development Phases

| Phase | Status | Description |
|---|---|---|
| Phase 1 | ✅ Complete | FastAPI backend, frontend, health/chat endpoints, sample knowledge base |
| Phase 2 | ✅ Active | LangGraph workflow, JWT auth, tickets, approvals, audit log, conversation history, LLM providers |
| Phase 3 | ⏳ Planned | ChromaDB/FAISS RAG pipeline (Sanskriti), PostgreSQL migration, Docker |
| Phase 4 | ⏳ Planned | CI/CD, HTTPS, rate limiting, production monitoring |

---

## 7. Known Limitations

- IT actions are fully **simulated** against a synthetic in-memory directory. No real enterprise systems (AD, LDAP, Exchange) are connected.
- Conversation memory has no summarisation — capped at 6 turns.
- JWT stored in `sessionStorage` — cleared on browser tab close.
- No ticket assignment workflow in the current UI.
- Vector database RAG pipeline pending (Sanskriti Agarwal).
- Not production-ready — no HTTPS, containerisation, or rate limiting.
