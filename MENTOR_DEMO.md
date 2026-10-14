# ServiceDesk-AI — Mentor Demo Guide

> **5-minute demonstration sequence for college project review**

---

## 1. Prerequisites and Startup

### Requirements
- Python 3.11+ (3.13 tested)
- All dependencies installed (`pip install -r backend/requirements.txt`)
- No API key required — the system runs in Mock/Demo mode by default

### Start the backend (PowerShell)
```powershell
cd "C:\Users\srish\Documents\ai-it-support-service-desk\backend"
uvicorn app.main:app --reload
```

Backend starts at: **http://127.0.0.1:8000**  
Interactive API docs: **http://127.0.0.1:8000/docs**

### Open the frontend
Double-click `frontend/index.html` — or run:
```powershell
Start-Process "C:\Users\srish\Documents\ai-it-support-service-desk\frontend\index.html"
```

---

## 2. Demo Accounts (seeded automatically on first startup)

| Role | Username | Password | Can do |
|---|---|---|---|
| Employee | `employee` | `employee123` | Chat, view own tickets |
| Support Agent | `support_agent` | `agent123` | All tickets, approve requests |
| Admin | `admin` | `admin123` | Full access, audit log |

These are **demo credentials, not real secrets**. They are seeded into the SQLite database at startup if they do not already exist.

---

## 3. Five-Minute Demo Sequence

### Step 1 — Login (30 sec)
1. The login modal appears automatically.
2. Enter: username `employee`, password `employee123`.
3. Click **Sign In**.
4. Header shows "employee (employee)" and backend status turns green.

### Step 2 — Routine IT query (1 min)
1. Type or click: **"My Wi-Fi is not working"**
2. Show:
   - Response with step-by-step troubleshooting
   - Category tag: **network**
   - Priority tag: **P3**
   - Mode badge: **GEMINI · Mock/Demo** (or Live if API key configured)
   - No ticket created — routine queries are not escalated automatically

### Step 3 — Explicit ticket creation (1 min)
1. Type: **"Please create a support ticket for my ongoing network issue. My Wi-Fi is not working."**
2. Show:
   - Troubleshooting steps are provided (Wi-Fi knowledge base match)
   - Ticket ID appears in the info panel below the chat (e.g. `TKT-3A1B2C`)
   - Ticket ID tag on the message bubble
   - Priority from triage (P3 for network)
   - The reply includes: "✅ A support ticket is being created for this issue."

### Step 4 — Security escalation (1 min)
1. Type: **"Our servers are infected with ransomware!"**
2. Show:
   - 🚨 CRITICAL SECURITY ALERT response
   - Status: **escalate**
   - P1 ticket auto-created
   - Escalation panel appears below chat
   - Escalated to: Security Operations

### Step 5 — Approval workflow (1.5 min)
1. Type: **"Please unlock account for user john.doe"**
2. Show:
   - Approval Required message
   - Approval ID in the info panel (e.g. `APPR-XY123456`)

3. Now approve it as an agent:
   - Open FastAPI docs: http://127.0.0.1:8000/docs
   - `POST /api/auth/login` → body: `{"username":"support_agent","password":"agent123"}`
   - Copy the `access_token`
   - Click **Authorize** (top right of /docs)
   - `POST /api/approvals/{approval_id}/decision` → body: `{"decision":"APPROVED","decision_notes":"Verified by phone"}`
   - Show: Approval status changes to APPROVED, action executes

### Step 6 — Audit log (30 sec)
1. In FastAPI docs, authenticate as `admin / admin123`
2. `GET /api/audit`
3. Show the logged events: LOGIN_SUCCESS, TICKET_CREATED, APPROVAL_REQUESTED, APPROVAL_APPROVED

---

## 4. Example IT Support Queries

| Message | Expected outcome |
|---|---|
| `My Wi-Fi is not working` | Network troubleshooting, category=network, no ticket |
| `I need to reset my password` | Account troubleshooting, category=account |
| `VPN is not connecting` | VPN steps, category=network |
| `MFA authenticator not working` | MFA steps, category=security |
| `My computer is very slow` | Performance steps, category=performance |
| `Please create a ticket for my VPN issue` | TKT-XXXXXX created, visible in info panel |
| `Our servers are infected with ransomware!` | P1 security escalation + ticket |
| `Please unlock account for user john.doe` | APPR-XXXXXX pending approval |
| `Is VPN service down?` | Simulated service health check |
| `Something very unusual happened` | category=unknown, escalate status |

---

## 5. Showing the LangGraph Workflow

Explain to your mentor that each chat message passes through a **compiled LangGraph StateGraph** with these nodes:

1. **Intake** — starts session, loads conversation history
2. **Triage** — classifies category, impact, urgency, priority (ITIL matrix)
3. **Security Check** — deterministic rule: ransomware/phishing → P1 SecOps escalation
4. **RAG Retrieval** — queries knowledge base (SampleFAQRetriever by default; ChromaDB plug-in ready)
5. **Action Decision** — detects intent to perform IT actions
6. **Action Execution / Approval** — executes low-risk actions directly; high-risk → approval request
7. **Response Generation** — synthesizes reply using LLM (Gemini/Mock) + retrieved context + history
8. **Ticket Creation** — creates ticket for escalations and explicit requests
9. **Verification** — saves assistant reply to conversation history, marks terminal

Show the compiled graph diagram by printing it from `/docs` or by describing the flow.

---

## 6. Which Features Are Simulated

| Feature | Real or Simulated |
|---|---|
| Chat conversation | ✅ Real |
| Ticket creation / persistence (SQLite) | ✅ Real |
| JWT authentication + RBAC | ✅ Real |
| Approval workflow + self-approval prevention | ✅ Real |
| Audit logging | ✅ Real |
| Conversation history (SQLite) | ✅ Real |
| LangGraph multi-agent orchestration | ✅ Real |
| Triage / ITIL priority matrix | ✅ Real |
| AI responses without API key | ✅ Real (Mock provider) |
| AI responses with Gemini API key | ✅ Real (if GEMINI_API_KEY set) |
| Account unlock / password reset | 🔵 **Simulated** against synthetic directory |
| Resource access grant | 🔵 **Simulated** |
| Active Directory / LDAP | 🔵 **Not connected** (by design for safety) |
| Vector database (RAG) | 🟡 **Interface ready** — pending Sanskriti's ChromaDB pipeline |

---

## 7. Remaining Future Work

- **Sanskriti's RAG pipeline**: ChromaDB/FAISS vector store for semantic search
- Password reset email notification
- Ticket assignment workflow in the UI
- Multi-user real-time session support
- Docker containerisation for deployment
- Production HTTPS + rate limiting

---

## 8. Commands to Run Tests

```powershell
cd "C:\Users\srish\Documents\ai-it-support-service-desk"
python -m pytest tests/ -v
```

Expected: **all tests pass**, no live API calls required.

---

## 9. Setting Up Gemini Live Mode (Optional)

1. Get a free API key from https://aistudio.google.com/
2. Copy `.env.example` to `.env`
3. Set `GEMINI_API_KEY=your_actual_key`
4. Set `DEMO_MODE=false`
5. Restart the backend
6. The mode badge will show **GEMINI · Live**

> ⚠️ The test suite does **not** use the Gemini API — all tests run with the MockLLMProvider.
