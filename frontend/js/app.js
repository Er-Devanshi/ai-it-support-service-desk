/**
 * ServiceDesk-AI — Frontend Application
 * Phase 1 Foundation
 *
 * Responsibilities:
 *  - Check backend health on load and update the status indicator.
 *  - Send user messages to POST /api/chat and display responses.
 *  - Render chat bubbles with category/status metadata tags.
 *  - Populate the input from sidebar quick-topic clicks.
 */

"use strict";

// ---------------------------------------------------------------------------
// Configuration
// Change API_BASE_URL if you run the backend on a different port.
// ---------------------------------------------------------------------------
const API_BASE_URL = "http://127.0.0.1:8000";

// ---------------------------------------------------------------------------
// DOM references
// ---------------------------------------------------------------------------
const chatMessages  = document.getElementById("chatMessages");
const chatForm      = document.getElementById("chatForm");
const messageInput  = document.getElementById("messageInput");
const sendBtn       = document.getElementById("sendBtn");
const statusDot     = document.getElementById("statusDot");
const statusText    = document.getElementById("statusText");
const topicList     = document.getElementById("topicList");

// ---------------------------------------------------------------------------
// Utility — scroll to bottom of message list
// ---------------------------------------------------------------------------
function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ---------------------------------------------------------------------------
// Render helpers
// ---------------------------------------------------------------------------

/**
 * Append a message bubble to the chat window.
 *
 * @param {"user"|"bot"|"system"} role
 * @param {string} text
 * @param {{ category?: string, status?: string }} [meta]
 */
function appendMessage(role, text, meta = {}) {
  const wrapper = document.createElement("div");
  wrapper.classList.add("message", role);

  // Label (User / ServiceDesk-AI / System)
  const label = document.createElement("span");
  label.classList.add("message-label");
  label.textContent = role === "user" ? "You" : role === "bot" ? "ServiceDesk-AI" : "System";
  wrapper.appendChild(label);

  // Bubble
  const bubble = document.createElement("div");
  bubble.classList.add("message-bubble");
  bubble.textContent = text;
  wrapper.appendChild(bubble);

  // Metadata tags (only for bot messages)
  if (role === "bot" && (meta.category || meta.status)) {
    const metaRow = document.createElement("div");
    metaRow.classList.add("message-meta");

    if (meta.category) {
      const tag = document.createElement("span");
      tag.classList.add("tag", "tag-category");
      tag.textContent = meta.category;
      metaRow.appendChild(tag);
    }

    if (meta.status) {
      const tag = document.createElement("span");
      tag.classList.add("tag", `tag-status-${meta.status}`);
      tag.textContent = meta.status;
      metaRow.appendChild(tag);
    }

    wrapper.appendChild(metaRow);
  }

  chatMessages.appendChild(wrapper);
  scrollToBottom();
  return wrapper;
}

/**
 * Show an animated "typing…" indicator while waiting for the backend.
 * Returns the element so the caller can remove it later.
 */
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
// Status indicator helpers
// ---------------------------------------------------------------------------

function setStatus(state) {
  // state: "connecting" | "online" | "offline"
  statusDot.className = "status-dot";   // reset classes
  if (state === "online") {
    statusDot.classList.add("online");
    statusText.textContent = "Backend online";
  } else if (state === "offline") {
    statusDot.classList.add("offline");
    statusText.textContent = "Backend offline";
  } else {
    statusText.textContent = "Connecting…";
  }
}

// ---------------------------------------------------------------------------
// Backend communication
// ---------------------------------------------------------------------------

/**
 * Call GET /api/health to check if the backend is reachable.
 */
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`);
    if (res.ok) {
      setStatus("online");
    } else {
      setStatus("offline");
    }
  } catch {
    setStatus("offline");
    appendMessage(
      "system",
      "⚠️ Could not reach the backend. Make sure the FastAPI server is running on " +
        API_BASE_URL
    );
  }
}

/**
 * Send a message to POST /api/chat and return the parsed response.
 *
 * @param {string} message
 * @returns {Promise<{reply: string, category: string, status: string, note: string}>}
 */
async function sendChatMessage(message) {
  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    throw new Error(`Server responded with status ${res.status}`);
  }

  return res.json();
}

// ---------------------------------------------------------------------------
// Form submit handler
// ---------------------------------------------------------------------------

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = messageInput.value.trim();
  if (!message) return;

  // Show the user's message immediately
  appendMessage("user", message);
  messageInput.value = "";
  sendBtn.disabled = true;

  // Show typing indicator while we wait
  const typingEl = showTypingIndicator();

  try {
    const data = await sendChatMessage(message);
    typingEl.remove();
    appendMessage("bot", data.reply, {
      category: data.category,
      status: data.status,
    });
  } catch (err) {
    typingEl.remove();
    appendMessage(
      "system",
      "❌ Failed to get a response from the backend. " +
        "Please check that the server is running and try again."
    );
    console.error("Chat error:", err);
  } finally {
    sendBtn.disabled = false;
    messageInput.focus();
  }
});

// ---------------------------------------------------------------------------
// Sidebar quick-topic click handler
// ---------------------------------------------------------------------------

topicList.addEventListener("click", (event) => {
  const li = event.target.closest("li");
  if (!li) return;
  const msg = li.dataset.msg;
  if (msg) {
    messageInput.value = msg;
    messageInput.focus();
  }
});

// ---------------------------------------------------------------------------
// Initialise on page load
// ---------------------------------------------------------------------------

(function init() {
  // Welcome system message
  appendMessage(
    "system",
    "👋 Welcome to ServiceDesk-AI. Describe your IT issue below or pick a topic from the sidebar."
  );

  // Check backend health
  checkHealth();
})();
