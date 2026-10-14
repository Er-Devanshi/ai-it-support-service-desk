/**
 * ServiceDesk-AI — Frontend Application
 * Phase 2: Login, JWT auth, ticket/approval panel, conversation memory, mode badge.
 *
 * Security note: the JWT is stored in sessionStorage (cleared on tab close).
 * No API keys are present in this file.
 */

"use strict";

const API_BASE_URL = "http://127.0.0.1:8000";

// Session state
let currentConversationId = null;
let authToken = sessionStorage.getItem("sd_token") || null;
let currentUser = null;
try {
  const stored = sessionStorage.getItem("sd_user");
  if (stored) currentUser = JSON.parse(stored);
} catch (_) {}

// ---------------------------------------------------------------------------
// DOM references
// ---------------------------------------------------------------------------
const loginModal     = document.getElementById("loginModal");
const loginForm      = document.getElementById("loginForm");
const loginError     = document.getElementById("loginError");
const loginBtn       = document.getElementById("loginBtn");
const skipLoginBtn   = document.getElementById("skipLoginBtn");
const chatMessages   = document.getElementById("chatMessages");
const chatForm       = document.getElementById("chatForm");
const messageInput   = document.getElementById("messageInput");
const sendBtn        = document.getElementById("sendBtn");
const statusDot      = document.getElementById("statusDot");
const statusText     = document.getElementById("statusText");
const modeBadge      = document.getElementById("modeBadge");
const authPill       = document.getElementById("authPill");
const authUsername   = document.getElementById("authUsername");
const logoutBtn      = document.getElementById("logoutBtn");
const topicList      = document.getElementById("topicList");
const actionList     = document.getElementById("actionList");
const infoPanel      = document.getElementById("infoPanel");
const ticketInfo     = document.getElementById("ticketInfo");
const ticketDetails  = document.getElementById("ticketDetails");
const approvalInfo   = document.getElementById("approvalInfo");
const approvalDetails = document.getElementById("approvalDetails");
const escalationInfo = document.getElementById("escalationInfo");
const escalationDetails = document.getElementById("escalationDetails");

// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------

function setAuthState(token, user) {
  authToken = token;
  currentUser = user;
  if (token) {
    sessionStorage.setItem("sd_token", token);
    sessionStorage.setItem("sd_user", JSON.stringify(user));
    authUsername.textContent = `${user.username} (${user.role})`;
    logoutBtn.hidden = false;
  } else {
    sessionStorage.removeItem("sd_token");
    sessionStorage.removeItem("sd_user");
    authUsername.textContent = "Anonymous";
    logoutBtn.hidden = true;
  }
}

function getAuthHeaders() {
  if (authToken) return { "Authorization": `Bearer ${authToken}` };
  return {};
}

// ---------------------------------------------------------------------------
// Login modal
// ---------------------------------------------------------------------------

function showLoginModal() {
  loginModal.hidden = false;
}

function hideLoginModal() {
  loginModal.hidden = true;
}

skipLoginBtn.addEventListener("click", () => {
  setAuthState(null, null);
  authUsername.textContent = "Anonymous";
  logoutBtn.hidden = true;
  hideLoginModal();
  checkHealth();
  appendMessage("system", "👋 Welcome to ServiceDesk-AI (anonymous mode). Describe your IT issue or select a topic from the sidebar.");
});

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = document.getElementById("loginUsername").value.trim();
  const password = document.getElementById("loginPassword").value;
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
      loginError.textContent = data.detail || "Login failed.";
      loginError.hidden = false;
    } else {
      setAuthState(data.access_token, data.user);
      hideLoginModal();
      checkHealth();
      appendMessage("system", `✅ Signed in as ${data.user.username} (${data.user.role}). Welcome to ServiceDesk-AI.`);
    }
  } catch (err) {
    loginError.textContent = "Could not reach the backend. Ensure the server is running.";
    loginError.hidden = false;
  } finally {
    loginBtn.disabled = false;
    loginBtn.textContent = "Sign In";
  }
});

logoutBtn.addEventListener("click", () => {
  setAuthState(null, null);
  currentConversationId = null;
  chatMessages.innerHTML = "";
  appendMessage("system", "You have been signed out. Refresh the page to sign in again.");
});

// ---------------------------------------------------------------------------
// Scroll
// ---------------------------------------------------------------------------
function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ---------------------------------------------------------------------------
// Message rendering
// ---------------------------------------------------------------------------

function appendMessage(role, text, meta = {}) {
  const wrapper = document.createElement("div");
  wrapper.classList.add("message", role);

  const label = document.createElement("span");
  label.classList.add("message-label");
  label.textContent = role === "user" ? "You" : role === "bot" ? "ServiceDesk-AI" : "System";
  wrapper.appendChild(label);

  const bubble = document.createElement("div");
  bubble.classList.add("message-bubble");
  bubble.textContent = text;
  wrapper.appendChild(bubble);

  // Citations
  if (role === "bot" && meta.citations && meta.citations.length > 0) {
    const box = document.createElement("div");
    box.classList.add("citations-box");
    const title = document.createElement("h5");
    title.textContent = "📚 Knowledge Base References:";
    box.appendChild(title);
    meta.citations.forEach((c) => {
      const item = document.createElement("div");
      item.classList.add("citation-item");
      const score = c.relevance_score ? ` (${Math.round(c.relevance_score * 100)}% match)` : "";
      item.textContent = `• ${c.title}${score} — ${c.source}`;
      box.appendChild(item);
    });
    wrapper.appendChild(box);
  }

  // Metadata tags
  if (role === "bot") {
    const metaRow = document.createElement("div");
    metaRow.classList.add("message-meta");
    let hasMeta = false;

    const addTag = (text, cls, extraStyle) => {
      const tag = document.createElement("span");
      tag.classList.add("tag");
      if (cls) tag.classList.add(cls);
      if (extraStyle) tag.style.cssText = extraStyle;
      tag.textContent = text;
      metaRow.appendChild(tag);
      hasMeta = true;
    };

    if (meta.category) addTag(meta.category, "tag-category");
    if (meta.priority) {
      addTag(`Priority: ${meta.priority}`, `tag-priority-${meta.priority.toLowerCase()}`);
    }
    if (meta.status) addTag(meta.status.replace("_", " "), `tag-status-${meta.status}`);
    if (meta.ticket_id) addTag(`Ticket: ${meta.ticket_id}`, null, "background:#e0e7ff;color:#3730a3");
    if (meta.approval_id) addTag(`Approval: ${meta.approval_id}`, null, "background:#fef08a;color:#854d0e");
    if (meta.escalated) addTag("Escalated", null, "background:#fee2e2;color:#b91c1c");
    if (meta.mode && meta.mode !== "rule_fallback") {
      const modeLabel = meta.mode === "mock" ? "Demo/Mock" : `AI: ${meta.mode}`;
      addTag(modeLabel, null, "background:#f1f5f9;color:#64748b");
    }

    if (hasMeta) wrapper.appendChild(metaRow);
  }

  chatMessages.appendChild(wrapper);
  scrollToBottom();
  return wrapper;
}

function showTypingIndicator() {
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
// Info panel (ticket / approval / escalation)
// ---------------------------------------------------------------------------

function updateInfoPanel(data) {
  let showPanel = false;

  if (data.ticket_id) {
    ticketInfo.hidden = false;
    ticketDetails.textContent = `ID: ${data.ticket_id}  |  Priority: ${data.priority || "—"}  |  Status: OPEN`;
    showPanel = true;
  }

  if (data.approval_id) {
    approvalInfo.hidden = false;
    approvalDetails.textContent = `Approval ID: ${data.approval_id}  |  Status: PENDING — Awaiting agent/admin decision`;
    showPanel = true;
  }

  if (data.escalated || data.status === "escalate") {
    escalationInfo.hidden = false;
    escalationDetails.textContent = data.escalation_reason || "Issue escalated to IT Operations team.";
    showPanel = true;
  }

  if (showPanel) infoPanel.hidden = false;
}

function resetInfoPanel() {
  infoPanel.hidden = true;
  ticketInfo.hidden = true;
  approvalInfo.hidden = true;
  escalationInfo.hidden = true;
}

// ---------------------------------------------------------------------------
// Status / mode badge
// ---------------------------------------------------------------------------

function setStatus(state, info = {}) {
  statusDot.className = "status-dot";
  if (state === "online") {
    statusDot.classList.add("online");
    statusText.textContent = "Backend online";
    if (modeBadge) {
      const p = (info.llm_provider || "AI").toUpperCase();
      const m = info.mode === "mock/demo" ? " · Mock/Demo" : " · Live";
      modeBadge.textContent = `${p}${m}`;
    }
  } else if (state === "offline") {
    statusDot.classList.add("offline");
    statusText.textContent = "Backend offline";
    if (modeBadge) modeBadge.textContent = "Offline";
  } else {
    statusText.textContent = "Connecting…";
    if (modeBadge) modeBadge.textContent = "Mode: —";
  }
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`);
    if (res.ok) {
      setStatus("online", await res.json());
    } else {
      setStatus("offline");
    }
  } catch {
    setStatus("offline");
    appendMessage("system", "⚠️ Could not reach the backend at " + API_BASE_URL + ". Make sure uvicorn is running.");
  }
}

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
  if (!res.ok) throw new Error(`Server error ${res.status}`);
  const data = await res.json();
  if (data.conversation_id) currentConversationId = data.conversation_id;
  return data;
}

// ---------------------------------------------------------------------------
// Chat form submit
// ---------------------------------------------------------------------------

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;

  appendMessage("user", message);
  messageInput.value = "";
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
      citations: data.citations,
      escalated: data.escalated,
      mode: data.mode,
    });
    updateInfoPanel(data);
  } catch (err) {
    typingEl.remove();
    appendMessage("system", "❌ Failed to get a response. Check the backend is running and try again.");
    console.error("Chat error:", err);
  } finally {
    sendBtn.disabled = false;
    messageInput.focus();
  }
});

// ---------------------------------------------------------------------------
// Sidebar quick-clicks
// ---------------------------------------------------------------------------
[topicList, actionList].forEach((list) => {
  if (!list) return;
  list.addEventListener("click", (e) => {
    const li = e.target.closest("li");
    if (li && li.dataset.msg) {
      messageInput.value = li.dataset.msg;
      messageInput.focus();
    }
  });
});

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
(function init() {
  // If already authenticated from a previous sessionStorage entry, skip modal
  if (authToken && currentUser) {
    setAuthState(authToken, currentUser);
    hideLoginModal();
    checkHealth();
    appendMessage("system", `✅ Resumed session as ${currentUser.username}. Welcome back to ServiceDesk-AI.`);
  } else {
    showLoginModal();
  }
})();
