/**
 * ServiceDesk-AI — Enterprise IT Support Frontend Application
 *
 * Implements:
 * - JWT authentication with session persistence
 * - Real-time backend health & LLM mode synchronization
 * - RAG vector database status & knowledge base re-indexing
 * - Expandable / collapsible semantic citations with relevance scores
 * - Interactive multi-turn chat with Enter-to-send and Shift+Enter newlines
 * - Action approval cards, ticket references, and escalation indicators
 * - Quick-prompt IT inquiry shortcuts and 1-click demo login credentials
 */

"use strict";

const API_BASE_URL = "http://127.0.0.1:8000";

// Session & workflow state
let currentConversationId = null;
let authToken = sessionStorage.getItem("sd_token") || null;
let currentUser = null;
let isProcessing = false;

try {
  const storedUser = sessionStorage.getItem("sd_user");
  if (storedUser) currentUser = JSON.parse(storedUser);
} catch (_) {}

// ---------------------------------------------------------------------------
// DOM References
// ---------------------------------------------------------------------------
const loginModal        = document.getElementById("loginModal");
const loginForm         = document.getElementById("loginForm");
const loginError        = document.getElementById("loginError");
const loginBtn          = document.getElementById("loginBtn");
const skipLoginBtn      = document.getElementById("skipLoginBtn");
const loginUsername     = document.getElementById("loginUsername");
const loginPassword     = document.getElementById("loginPassword");

const chatMessages      = document.getElementById("chatMessages");
const emptyState        = document.getElementById("emptyState");
const chatForm          = document.getElementById("chatForm");
const messageInput      = document.getElementById("messageInput");
const sendBtn           = document.getElementById("sendBtn");
const clearChatBtn      = document.getElementById("clearChatBtn");

const statusDot         = document.getElementById("statusDot");
const statusText        = document.getElementById("statusText");
const modeBadge         = document.getElementById("modeBadge");
const ragBadgeText      = document.getElementById("ragBadgeText");

const authPill          = document.getElementById("authPill");
const authUsername      = document.getElementById("authUsername");
const userAvatar        = document.getElementById("userAvatar");
const logoutBtn         = document.getElementById("logoutBtn");

const topicList         = document.getElementById("topicList");
const actionList        = document.getElementById("actionList");

const infoPanel         = document.getElementById("infoPanel");
const ticketInfo        = document.getElementById("ticketInfo");
const ticketDetails     = document.getElementById("ticketDetails");
const approvalInfo      = document.getElementById("approvalInfo");
const approvalDetails   = document.getElementById("approvalDetails");
const escalationInfo    = document.getElementById("escalationInfo");
const escalationDetails = document.getElementById("escalationDetails");

const ragCardBadge      = document.getElementById("ragCardBadge");
const ragVectorDbVal    = document.getElementById("ragVectorDbVal");
const ragModelVal       = document.getElementById("ragModelVal");
const ragChunksVal      = document.getElementById("ragChunksVal");
const reindexBtn        = document.getElementById("reindexBtn");

// ---------------------------------------------------------------------------
// Authentication & RBAC Helpers
// ---------------------------------------------------------------------------

function setAuthState(token, user) {
  authToken = token;
  currentUser = user;

  if (token && user) {
    sessionStorage.setItem("sd_token", token);
    sessionStorage.setItem("sd_user", JSON.stringify(user));
    authUsername.textContent = `${user.username} (${user.role})`;
    userAvatar.textContent = (user.username || "U")[0].toUpperCase();
    logoutBtn.hidden = false;

    // Enable re-index button if user has admin or support_agent role
    if (reindexBtn) {
      const role = (user.role || "").toLowerCase();
      reindexBtn.disabled = !(role === "admin" || role === "support_agent");
    }
  } else {
    sessionStorage.removeItem("sd_token");
    sessionStorage.removeItem("sd_user");
    authUsername.textContent = "Guest";
    userAvatar.textContent = "G";
    logoutBtn.hidden = true;
    if (reindexBtn) reindexBtn.disabled = true;
  }
}

function getAuthHeaders() {
  if (authToken) return { "Authorization": `Bearer ${authToken}` };
  return {};
}

function showLoginModal() {
  if (loginModal) loginModal.hidden = false;
}

function hideLoginModal() {
  if (loginModal) loginModal.hidden = true;
}

// ---------------------------------------------------------------------------
// Text Formatting & Markdown Parsing
// ---------------------------------------------------------------------------

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function formatResponseText(rawText) {
  if (!rawText) return "";
  let text = escapeHtml(rawText);

  // Bold **text**
  text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // Inline code `code`
  text = text.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Lines to paragraphs / lists
  const lines = text.split("\n");
  let inList = false;
  let listType = "ul";
  let formattedLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // Check bullet list item (• or -)
    if (/^[\-\•]\s+(.*)/.test(line)) {
      const itemContent = line.replace(/^[\-\•]\s+/, "");
      if (!inList || listType !== "ul") {
        if (inList) formattedLines.push(`</${listType}>`);
        formattedLines.push("<ul>");
        inList = true;
        listType = "ul";
      }
      formattedLines.push(`<li>${itemContent}</li>`);
      continue;
    }

    // Check numbered step (1. 2.)
    if (/^\d+[\.\)]\s+(.*)/.test(line)) {
      const itemContent = line.replace(/^\d+[\.\)]\s+/, "");
      if (!inList || listType !== "ol") {
        if (inList) formattedLines.push(`</${listType}>`);
        formattedLines.push("<ol>");
        inList = true;
        listType = "ol";
      }
      formattedLines.push(`<li>${itemContent}</li>`);
      continue;
    }

    // Non-list line
    if (inList) {
      formattedLines.push(`</${listType}>`);
      inList = false;
    }

    if (line === "") {
      formattedLines.push("<br>");
    } else {
      formattedLines.push(`<p>${line}</p>`);
    }
  }

  if (inList) formattedLines.push(`</${listType}>`);
  return formattedLines.join("");
}

// ---------------------------------------------------------------------------
// Scroll & Viewport Helpers
// ---------------------------------------------------------------------------

function scrollToBottom() {
  if (chatMessages) {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
}

// ---------------------------------------------------------------------------
// Message Rendering
// ---------------------------------------------------------------------------

function appendMessage(role, text, meta = {}) {
  // Hide empty state once a message is displayed
  if (emptyState) emptyState.style.display = "none";

  const wrapper = document.createElement("div");
  wrapper.classList.add("message", role);

  const label = document.createElement("span");
  label.classList.add("message-label");
  label.textContent = role === "user" ? "You" : role === "bot" ? "ServiceDesk-AI" : "System Notification";
  wrapper.appendChild(label);

  const bubble = document.createElement("div");
  bubble.classList.add("message-bubble");

  if (role === "bot" || role === "system") {
    bubble.innerHTML = formatResponseText(text);
  } else {
    bubble.textContent = text;
  }
  wrapper.appendChild(bubble);

  // Render Knowledge Base Citations Accordion on Bot Messages
  if (role === "bot") {
    if (meta.citations && meta.citations.length > 0) {
      const citationsBox = document.createElement("div");
      citationsBox.classList.add("citations-box");

      const citationsHeader = document.createElement("div");
      citationsHeader.classList.add("citations-header");
      citationsHeader.innerHTML = `
        <span>📚 Knowledge Base References (${meta.citations.length} sources)</span>
        <span class="citations-toggle-icon">▼</span>
      `;

      // Accordion toggle handler
      citationsHeader.addEventListener("click", () => {
        citationsBox.classList.toggle("collapsed");
      });

      citationsBox.appendChild(citationsHeader);

      const citationsContent = document.createElement("div");
      citationsContent.classList.add("citations-content");

      meta.citations.forEach((c) => {
        const card = document.createElement("div");
        card.classList.add("citation-card");

        const scoreVal = typeof c.relevance_score === "number" ? c.relevance_score : null;
        let scoreClass = "match-low";
        let scoreLabel = "";
        if (scoreVal !== null) {
          const pct = Math.round(scoreVal * 100);
          scoreLabel = `${pct}% match`;
          if (pct >= 75) scoreClass = "match-high";
          else if (pct >= 45) scoreClass = "match-mid";
        }

        const topRow = document.createElement("div");
        topRow.classList.add("citation-top-row");
        topRow.innerHTML = `
          <span class="citation-title">${escapeHtml(c.title || "IT Document")}</span>
          ${scoreLabel ? `<span class="citation-match-score ${scoreClass}">${scoreLabel}</span>` : ""}
        `;
        card.appendChild(topRow);

        const sourcePath = document.createElement("div");
        sourcePath.classList.add("citation-source-path");
        sourcePath.textContent = `Source: ${c.source || "knowledge_base"}`;
        card.appendChild(sourcePath);

        if (c.snippet) {
          const snippetBox = document.createElement("div");
          snippetBox.classList.add("citation-snippet");
          snippetBox.textContent = `"${c.snippet}"`;
          card.appendChild(snippetBox);
        }

        citationsContent.appendChild(card);
      });

      citationsBox.appendChild(citationsContent);
      wrapper.appendChild(citationsBox);
    }

    // Metadata Tags Row
    const metaRow = document.createElement("div");
    metaRow.classList.add("message-meta");
    let hasMeta = false;

    const addTag = (label, cls, extraStyle = null) => {
      const tag = document.createElement("span");
      tag.classList.add("tag");
      if (cls) tag.classList.add(cls);
      if (extraStyle) tag.style.cssText = extraStyle;
      tag.textContent = label;
      metaRow.appendChild(tag);
      hasMeta = true;
    };

    if (meta.category && meta.category !== "unknown") {
      addTag(`Category: ${meta.category}`, "tag-category");
    }
    if (meta.priority) {
      addTag(`Priority: ${meta.priority}`, `tag-priority-${meta.priority.toLowerCase()}`);
    }
    if (meta.status) {
      addTag(meta.status.replace("_", " "), `tag-status-${meta.status}`);
    }
    if (meta.ticket_id) {
      addTag(`Ticket: ${meta.ticket_id}`, null, "background:#e0e7ff;color:#3730a3;border:1px solid #c7d2fe;");
    }
    if (meta.approval_id) {
      addTag(`Approval: ${meta.approval_id}`, null, "background:#fef3c7;color:#92400e;border:1px solid #fde68a;");
    }
    if (meta.escalated) {
      addTag("Escalated to SecOps/Tier-2", null, "background:#fee2e2;color:#991b1b;border:1px solid #fecaca;");
    }
    if (meta.mode && meta.mode !== "rule_fallback") {
      const modeText = meta.mode === "mock" ? "Mock Mode" : `AI: ${meta.mode}`;
      addTag(modeText, null, "background:#f1f5f9;color:#475569;border:1px solid #e2e8f0;");
    }

    if (hasMeta) wrapper.appendChild(metaRow);
  }

  chatMessages.appendChild(wrapper);
  scrollToBottom();
  return wrapper;
}

function showTypingIndicator() {
  if (emptyState) emptyState.style.display = "none";

  const wrapper = document.createElement("div");
  wrapper.classList.add("message", "bot", "typing-indicator");

  const label = document.createElement("span");
  label.classList.add("message-label");
  label.textContent = "ServiceDesk-AI";
  wrapper.appendChild(label);

  const bubble = document.createElement("div");
  bubble.classList.add("message-bubble");
  [1, 2, 3].forEach(() => {
    const dot = document.createElement("span");
    dot.classList.add("typing-dot");
    bubble.appendChild(dot);
  });
  wrapper.appendChild(bubble);

  chatMessages.appendChild(wrapper);
  scrollToBottom();
  return wrapper;
}

// ---------------------------------------------------------------------------
// Info Panel Context (Tickets / Approvals / Escalation)
// ---------------------------------------------------------------------------

function updateInfoPanel(data) {
  let showPanel = false;

  if (data.ticket_id) {
    ticketInfo.hidden = false;
    ticketDetails.textContent = `Ticket ID: ${data.ticket_id}  |  Priority: ${data.priority || "P3"}  |  Status: OPEN`;
    showPanel = true;
  }

  if (data.approval_id) {
    approvalInfo.hidden = false;
    approvalDetails.textContent = `Request ID: ${data.approval_id}  |  Status: PENDING — Awaiting Agent/Admin Decision`;
    showPanel = true;
  }

  if (data.escalated || data.status === "escalate") {
    escalationInfo.hidden = false;
    escalationDetails.textContent = data.escalation_reason || "Flagged for human technician escalation.";
    showPanel = true;
  }

  if (showPanel) infoPanel.hidden = false;
}

function resetInfoPanel() {
  if (infoPanel) infoPanel.hidden = true;
  if (ticketInfo) ticketInfo.hidden = true;
  if (approvalInfo) approvalInfo.hidden = true;
  if (escalationInfo) escalationInfo.hidden = true;
}

// ---------------------------------------------------------------------------
// Status & Diagnostics Synchronization
// ---------------------------------------------------------------------------

function setStatus(state, info = {}) {
  statusDot.className = "status-dot";

  if (state === "online") {
    statusDot.classList.add("online");
    statusText.textContent = "Backend online";

    if (modeBadge) {
      const prov = (info.llm_provider || "AI").toUpperCase();
      const isMock = info.mode === "mock/demo" || info.mode === "mock";
      modeBadge.textContent = isMock ? `${prov} · Mock Mode` : `${prov} · Live LLM`;
      modeBadge.style.background = isMock ? "rgba(245, 158, 11, 0.25)" : "rgba(16, 185, 129, 0.25)";
    }
  } else if (state === "offline") {
    statusDot.classList.add("offline");
    statusText.textContent = "Backend offline";
    if (modeBadge) {
      modeBadge.textContent = "Offline";
      modeBadge.style.background = "rgba(239, 68, 68, 0.25)";
    }
  } else {
    statusText.textContent = "Connecting…";
    if (modeBadge) modeBadge.textContent = "Mode: —";
  }
}

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`, { method: "GET" });
    if (res.ok) {
      const data = await res.json();
      setStatus("online", data);
    } else {
      setStatus("offline");
    }
  } catch (_) {
    setStatus("offline");
  }
}

async function checkRagStatus() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/rag/status`, { method: "GET" });
    if (res.ok) {
      const data = await res.json();
      if (ragBadgeText) {
        ragBadgeText.textContent = data.rag_enabled ? `RAG: ChromaDB (${data.document_count || 0})` : "RAG: Disabled";
      }
      if (ragCardBadge) {
        ragCardBadge.textContent = data.rag_enabled ? "Active" : "Disabled";
        ragCardBadge.className = data.rag_enabled ? "rag-status-badge online" : "rag-status-badge offline";
      }
      if (ragChunksVal) ragChunksVal.textContent = `${data.document_count || 0} chunks`;
      if (ragModelVal) ragModelVal.textContent = data.embedding_model || "all-MiniLM-L6-v2";
      if (ragVectorDbVal) ragVectorDbVal.textContent = data.collection_name ? `ChromaDB (${data.collection_name})` : "ChromaDB";
    }
  } catch (_) {
    if (ragCardBadge) {
      ragCardBadge.textContent = "Offline";
      ragCardBadge.className = "rag-status-badge offline";
    }
  }
}

// ---------------------------------------------------------------------------
// Chat API Interaction
// ---------------------------------------------------------------------------

async function sendChatMessage(message) {
  const payload = {
    message,
    conversation_id: currentConversationId,
  };

  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Server returned HTTP ${res.status}: ${errText}`);
  }

  const data = await res.json();
  if (data.conversation_id) currentConversationId = data.conversation_id;
  return data;
}

async function handleMessageSubmit(message) {
  if (!message || isProcessing) return;
  isProcessing = true;

  appendMessage("user", message);
  messageInput.value = "";
  adjustTextareaHeight(messageInput);
  sendBtn.disabled = true;
  resetInfoPanel();

  const typingEl = showTypingIndicator();

  try {
    const data = await sendChatMessage(message);
    typingEl.remove();

    appendMessage("bot", data.reply, {
      category: data.category,
      status: data.status,
      priority: data.priority,
      ticket_id: data.ticket_id,
      approval_id: data.approval_id,
      citations: data.citations || [],
      escalated: data.escalated,
      mode: data.mode,
    });

    updateInfoPanel(data);
  } catch (err) {
    typingEl.remove();
    appendMessage(
      "system",
      `❌ Could not process your request. Ensure the backend server is running on ${API_BASE_URL}. (${err.message})`
    );
    console.error("Chat error:", err);
  } finally {
    isProcessing = false;
    sendBtn.disabled = false;
    messageInput.focus();
  }
}

// ---------------------------------------------------------------------------
// Textarea Auto-Resize & Keyboard Handling
// ---------------------------------------------------------------------------

function adjustTextareaHeight(el) {
  if (!el) return;
  el.style.height = "auto";
  el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
}

messageInput.addEventListener("input", () => {
  adjustTextareaHeight(messageInput);
});

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event("submit", { cancelable: true }));
  }
});

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = messageInput.value.trim();
  if (text) handleMessageSubmit(text);
});

// Clear chat session
clearChatBtn.addEventListener("click", () => {
  currentConversationId = null;
  chatMessages.innerHTML = "";
  if (emptyState) {
    chatMessages.appendChild(emptyState);
    emptyState.style.display = "block";
  }
  resetInfoPanel();
  appendMessage("system", "🔄 New conversation session started. You can now describe your issue.");
});

// ---------------------------------------------------------------------------
// Quick Prompts & Sidebar Clicks
// ---------------------------------------------------------------------------

document.addEventListener("click", (e) => {
  // Empty state prompt card click
  const promptCard = e.target.closest(".quick-prompt-card");
  if (promptCard && promptCard.dataset.prompt) {
    messageInput.value = promptCard.dataset.prompt;
    handleMessageSubmit(promptCard.dataset.prompt);
    return;
  }

  // Sidebar topic/workflow click
  const topicLi = e.target.closest(".topic-list li");
  if (topicLi && topicLi.dataset.msg) {
    messageInput.value = topicLi.dataset.msg;
    adjustTextareaHeight(messageInput);
    messageInput.focus();
    return;
  }

  // 1-Click Demo Account chip in Login Modal
  const demoChip = e.target.closest(".demo-chip");
  if (demoChip) {
    loginUsername.value = demoChip.dataset.user;
    loginPassword.value = demoChip.dataset.pass;
    loginForm.dispatchEvent(new Event("submit", { cancelable: true }));
    return;
  }

  // Demo account item in sidebar
  const accItem = e.target.closest(".demo-acc-item");
  if (accItem) {
    loginUsername.value = accItem.dataset.user;
    loginPassword.value = accItem.dataset.pass;
    showLoginModal();
    return;
  }
});

// ---------------------------------------------------------------------------
// Login Form Handlers
// ---------------------------------------------------------------------------

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = loginUsername.value.trim();
  const password = loginPassword.value;

  loginBtn.disabled = true;
  loginBtn.textContent = "Signing in…";
  loginError.hidden = true;

  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    const data = await res.json();
    if (!res.ok) {
      loginError.textContent = data.detail || "Authentication failed. Check credentials.";
      loginError.hidden = false;
    } else {
      setAuthState(data.access_token, data.user);
      hideLoginModal();
      checkHealth();
      checkRagStatus();
      appendMessage(
        "system",
        `✅ Signed in as <strong>${escapeHtml(data.user.username)}</strong> (Role: ${escapeHtml(data.user.role)}).`
      );
    }
  } catch (err) {
    loginError.textContent = "Could not reach the backend server. Verify that FastAPI/uvicorn is running.";
    loginError.hidden = false;
  } finally {
    loginBtn.disabled = false;
    loginBtn.textContent = "Sign In";
  }
});

skipLoginBtn.addEventListener("click", () => {
  setAuthState(null, null);
  hideLoginModal();
  checkHealth();
  checkRagStatus();
  appendMessage(
    "system",
    "👋 Operating in <strong>Guest / Anonymous</strong> mode. Describe your issue or select a common inquiry from the sidebar."
  );
});

logoutBtn.addEventListener("click", () => {
  setAuthState(null, null);
  currentConversationId = null;
  chatMessages.innerHTML = "";
  if (emptyState) {
    chatMessages.appendChild(emptyState);
    emptyState.style.display = "block";
  }
  resetInfoPanel();
  appendMessage("system", "Signed out successfully.");
  showLoginModal();
});

// ---------------------------------------------------------------------------
// Re-Index Knowledge Base (Protected Action)
// ---------------------------------------------------------------------------

if (reindexBtn) {
  reindexBtn.addEventListener("click", async () => {
    if (!authToken) {
      alert("Please sign in as Admin or Support Agent to re-index the knowledge base.");
      showLoginModal();
      return;
    }

    reindexBtn.disabled = true;
    reindexBtn.textContent = "⏳ Re-Indexing KB…";

    try {
      const res = await fetch(`${API_BASE_URL}/api/rag/ingest`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify({ reset: false }),
      });

      const data = await res.json();
      if (!res.ok) {
        alert(data.detail || "Failed to re-index knowledge base.");
      } else {
        alert(`✅ Knowledge Base Re-Indexed!\nDocuments: ${data.documents_loaded}\nTotal Chunks: ${data.total_in_db}`);
        checkRagStatus();
      }
    } catch (err) {
      alert(`Error reaching backend: ${err.message}`);
    } finally {
      reindexBtn.disabled = false;
      reindexBtn.textContent = "🔄 Re-Index Knowledge Base";
    }
  });
}

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------

(function init() {
  if (authToken && currentUser) {
    setAuthState(authToken, currentUser);
    hideLoginModal();
  } else {
    showLoginModal();
  }

  checkHealth();
  checkRagStatus();

  // Periodic health and vector DB status ping every 30 seconds
  setInterval(() => {
    checkHealth();
    checkRagStatus();
  }, 30000);
})();
