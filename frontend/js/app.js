"use strict";

/* ============================================================
   ServiceDesk-AI — Advanced Frontend Application
   ============================================================ */

const API = "http://127.0.0.1:8000";

// State
let authToken   = sessionStorage.getItem("sd_token") || null;
let currentUser = (() => { try { return JSON.parse(sessionStorage.getItem("sd_user")); } catch(_){return null;} })();
let convId      = null;
let isBusy      = false;
let allTickets  = [];
let isDark      = localStorage.getItem("sd_theme") === "dark";

/* ============================================================
   Utility Helpers
   ============================================================ */
const $ = id => document.getElementById(id);
const fmt = s => new Date(s).toLocaleString();
const fmtShort = s => new Date(s).toLocaleDateString();

function escHtml(t){
  const d = document.createElement("div");
  d.textContent = t;
  return d.innerHTML;
}

function toast(msg, type = "info", dur = 3500) {
  const c = $("toastContainer");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  const icons = { success:"✅", error:"❌", warning:"⚠️", info:"ℹ️" };
  el.innerHTML = `<span>${icons[type]||"ℹ️"}</span><span>${escHtml(msg)}</span>`;
  c.appendChild(el);
  setTimeout(() => {
    el.classList.add("toast-out");
    setTimeout(() => el.remove(), 280);
  }, dur);
}

function authHeaders() {
  return authToken ? { "Authorization": `Bearer ${authToken}` } : {};
}

async function apiFetch(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json", ...authHeaders(), ...(opts.headers||{}) },
    ...opts,
  });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { msg = (await res.json()).detail || msg; } catch(_){}
    throw new Error(msg);
  }
  return res.json();
}

/* ============================================================
   Theme
   ============================================================ */
function applyTheme() {
  document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");
  $("themeIcon").textContent = isDark ? "☀️" : "🌙";
}
applyTheme();

$("themeToggle").addEventListener("click", () => {
  isDark = !isDark;
  localStorage.setItem("sd_theme", isDark ? "dark" : "light");
  applyTheme();
});

/* ============================================================
   Navigation / Tabs
   ============================================================ */
const TABS = { chat:"AI Chat Assistant", services:"Live Service Health", tickets:"Support Tickets", approvals:"Approval Requests", analytics:"Analytics Dashboard", audit:"Audit Logs" };

function switchTab(tab) {
  document.querySelectorAll(".nav-item[data-tab]").forEach(b => {
    b.classList.toggle("active", b.dataset.tab === tab);
  });
  document.querySelectorAll(".tab-content").forEach(c => {
    c.classList.toggle("active", c.id === `tab-${tab}`);
  });
  $("breadcrumb").textContent = TABS[tab] || tab;
  if (tab === "tickets")   loadTickets();
  if (tab === "approvals") loadApprovals();
  if (tab === "analytics") loadAnalytics();
  if (tab === "audit")     loadAuditLogs();
  if (tab === "services")  loadServiceHealth();
}

document.querySelectorAll(".nav-item[data-tab]").forEach(btn => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});

// Hamburger (mobile)
$("hamburger").addEventListener("click", () => {
  $("appNav").classList.toggle("open");
});
document.addEventListener("click", e => {
  if (!e.target.closest(".app-nav") && !e.target.closest("#hamburger")) {
    $("appNav").classList.remove("open");
  }
});

/* ============================================================
   Auth
   ============================================================ */
function setAuth(token, user) {
  authToken   = token;
  currentUser = user;
  if (token && user) {
    sessionStorage.setItem("sd_token", token);
    sessionStorage.setItem("sd_user", JSON.stringify(user));
    const role = user.role || "";
    $("navAvatar").textContent    = (user.username||"U")[0].toUpperCase();
    $("navUsername").textContent  = user.username;
    $("navUserrole").textContent  = role.replace("_", " ");
    $("navUserBtn").hidden        = false;
    $("navLogoutBtn").hidden      = false;
    $("navLoginBtn").hidden       = true;
    $("headerLoginBtn").hidden    = true;
    // Show audit tab for admin
    $("auditNavItem").hidden      = role !== "admin";
    // RAG reindex btn
    if ($("reindexBtn")) $("reindexBtn").disabled = !(role==="admin"||role==="support_agent");
  } else {
    sessionStorage.removeItem("sd_token");
    sessionStorage.removeItem("sd_user");
    $("navAvatar").textContent   = "G";
    $("navUsername").textContent = "Guest";
    $("navUserrole").textContent = "";
    $("navUserBtn").hidden       = true;
    $("navLogoutBtn").hidden     = true;
    $("navLoginBtn").hidden      = false;
    $("headerLoginBtn").hidden   = false;
    $("auditNavItem").hidden     = true;
    if ($("reindexBtn")) $("reindexBtn").disabled = true;
  }
}

// Tab switcher — Sign In / Sign Up
$("tabSignIn").addEventListener("click", () => {
  $("tabSignIn").classList.add("active");
  $("tabSignUp").classList.remove("active");
  $("loginForm").hidden = false;
  $("registerForm").hidden = true;
  $("demoDivider").hidden = false;
  document.querySelectorAll(".demo-chip, .guest-btn").forEach(el => el.hidden = false);
});
$("tabSignUp").addEventListener("click", () => {
  $("tabSignUp").classList.add("active");
  $("tabSignIn").classList.remove("active");
  $("loginForm").hidden = true;
  $("registerForm").hidden = false;
  $("demoDivider").hidden = true;
  document.querySelectorAll(".demo-chip, .guest-btn").forEach(el => el.hidden = true);
});

// Register form
$("registerForm").addEventListener("submit", async e => {
  e.preventDefault();
  const btn = $("registerBtn");
  $("registerBtnText").textContent = "Creating…";
  btn.disabled = true;
  $("registerError").hidden = true;
  try {
    await apiFetch("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        username: $("regUsername").value.trim(),
        email: $("regEmail").value.trim(),
        password: $("regPassword").value,
        role: "employee"
      })
    });
    // Auto login after register
    const data = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username: $("regUsername").value.trim(), password: $("regPassword").value })
    });
    setAuth(data.access_token, data.user);
    hideModal("loginModal");
    toast(`Account created! Welcome, ${data.user.username}!`, "success");
    appendMsg("system", `✅ Account created & signed in as <strong>${escHtml(data.user.username)}</strong>`);
    checkHealth(); checkRagStatus();
  } catch(err) {
    $("registerError").textContent = err.message;
    $("registerError").hidden = false;
  } finally {
    $("registerBtnText").textContent = "Create Account";
    btn.disabled = false;
  }
});

// Login form
$("loginForm").addEventListener("submit", async e => {
  e.preventDefault();
  const btn = $("loginBtn");
  $("loginBtnText").textContent = "Signing in…";
  btn.disabled = true;
  $("loginError").hidden = true;
  try {
    const data = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username: $("loginUsername").value.trim(), password: $("loginPassword").value })
    });
    setAuth(data.access_token, data.user);
    hideModal("loginModal");
    toast(`Welcome back, ${data.user.username}!`, "success");
    appendMsg("system", `✅ Signed in as <strong>${escHtml(data.user.username)}</strong> · Role: ${escHtml(data.user.role)}`);
    checkHealth(); checkRagStatus();
  } catch(err) {
    $("loginError").textContent = err.message;
    $("loginError").hidden = false;
  } finally {
    $("loginBtnText").textContent = "Sign In";
    btn.disabled = false;
  }
});

// Password visibility
$("passwordToggle").addEventListener("click", () => {
  const inp = $("loginPassword");
  inp.type = inp.type === "password" ? "text" : "password";
});

// Skip login
$("skipLoginBtn").addEventListener("click", () => {
  setAuth(null, null);
  hideModal("loginModal");
  toast("Continuing as Guest", "info");
  appendMsg("system", "👋 Operating as <strong>Guest</strong>. Describe your IT issue to get started.");
  checkHealth(); checkRagStatus();
});

// Demo chips
document.addEventListener("click", e => {
  const chip = e.target.closest(".demo-chip");
  if (chip) {
    $("loginUsername").value = chip.dataset.user;
    $("loginPassword").value = chip.dataset.pass;
    $("loginForm").dispatchEvent(new Event("submit", { cancelable: true }));
  }
});

// Logout
$("navLogoutBtn").addEventListener("click", () => {
  setAuth(null, null);
  convId = null;
  clearChatUI();
  toast("Signed out successfully", "info");
  showModal("loginModal");
});
$("navLoginBtn").addEventListener("click", () => showModal("loginModal"));
$("headerLoginBtn").addEventListener("click", () => showModal("loginModal"));

/* ============================================================
   Modal Helpers
   ============================================================ */
function showModal(id) { $(id).hidden = false; }
function hideModal(id) { $(id).hidden = true; }

$("closeTicketModal").addEventListener("click", () => hideModal("ticketModal"));
$("closeNewTicketModal").addEventListener("click", () => hideModal("newTicketModal"));

/* ============================================================
   Health & RAG Status
   ============================================================ */
async function checkHealth() {
  try {
    const d = await apiFetch("/api/health");
    const dot = $("navStatusDot");
    dot.className = "status-dot online";
    $("navStatusText").textContent = "API Online";
    const prov = (d.llm_provider || "AI").toUpperCase();
    const mock = d.mode === "mock/demo" || d.mode === "mock";
    $("llmBadgeText").textContent = mock ? `${prov} · Mock` : `${prov} · Live`;
  } catch(_) {
    $("navStatusDot").className = "status-dot offline";
    $("navStatusText").textContent = "API Offline";
    $("llmBadgeText").textContent = "Offline";
  }
}

async function checkRagStatus() {
  try {
    const d = await apiFetch("/api/rag/status");
    const active = d.rag_enabled && d.status !== "error";
    $("ragTopText").textContent = active ? `RAG · ${d.document_count||0} chunks` : "RAG: Off";
    if ($("ragStatusPill")) $("ragStatusPill").textContent = active ? "Active" : "Disabled";
    if ($("ragChunks"))     $("ragChunks").textContent     = d.document_count || 0;
    if ($("ragDocs"))       $("ragDocs").textContent       = d.collection_name ? "Loaded" : "—";
    if ($("ragModel"))      $("ragModel").textContent      = (d.embedding_model || "—").split("/").pop().replace("all-","").split("-v")[0];
  } catch(_) {
    if ($("ragStatusPill")) $("ragStatusPill").textContent = "Error";
  }
}

// Re-index
$("reindexBtn") && $("reindexBtn").addEventListener("click", async () => {
  if (!authToken) { toast("Login required to re-index", "warning"); showModal("loginModal"); return; }
  $("reindexBtn").disabled = true;
  $("reindexBtn").textContent = "⏳ Indexing…";
  try {
    const d = await apiFetch("/api/rag/ingest", { method: "POST", body: JSON.stringify({ reset: false }) });
    toast(`KB indexed: ${d.chunks_indexed} chunks in ${d.total_in_db} total`, "success");
    checkRagStatus();
  } catch(err) {
    toast("Re-index failed: " + err.message, "error");
  } finally {
    $("reindexBtn").disabled = false;
    $("reindexBtn").textContent = "🔄 Re-Index KB";
  }
});

/* ============================================================
   Chat — Message Rendering  (with AI typing effect)
   ============================================================ */
function formatText(raw) {
  if (!raw) return "";
  let t = escHtml(raw);
  t = t.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  t = t.replace(/`([^`]+)`/g, "<code>$1</code>");
  const lines = t.split("\n");
  let inList = false, lt = "ul", out = [];
  for (const line of lines) {
    const l = line.trim();
    if (/^[-•]\s+(.*)/.test(l)) {
      if (!inList || lt!=="ul") { if(inList) out.push(`</${lt}>`); out.push("<ul>"); inList=true; lt="ul"; }
      out.push(`<li>${l.replace(/^[-•]\s+/,"")}</li>`); continue;
    }
    if (/^\d+[.)]\s+(.*)/.test(l)) {
      if (!inList || lt!=="ol") { if(inList) out.push(`</${lt}>`); out.push("<ol>"); inList=true; lt="ol"; }
      out.push(`<li>${l.replace(/^\d+[.)]\s+/,"")}</li>`); continue;
    }
    if (inList) { out.push(`</${lt}>`); inList=false; }
    out.push(l === "" ? "<br>" : `<p>${l}</p>`);
  }
  if (inList) out.push(`</${lt}>`);
  return out.join("");
}

// Typewriter effect: renders text char by char into a bubble
function typewriterEffect(bubble, htmlText, onDone) {
  // Strip tags for typing, then swap to full HTML
  const plain = htmlText.replace(/<[^>]+>/g, "");
  let i = 0;
  bubble.innerHTML = "";
  const cursor = document.createElement("span");
  cursor.className = "typing-cursor";
  bubble.appendChild(cursor);

  const interval = setInterval(() => {
    if (i >= plain.length) {
      clearInterval(interval);
      bubble.innerHTML = htmlText; // swap to full formatted HTML
      if (onDone) onDone();
      return;
    }
    // Type char before cursor
    cursor.insertAdjacentText("beforebegin", plain[i]);
    i++;
    $("chatMessages").scrollTop = $("chatMessages").scrollHeight;
  }, 12); // 12ms per char ≈ fast but visible
}

function appendMsg(role, text, meta = {}, useTypewriter = false) {
  const em = $("emptyState");
  if (em) em.style.display = "none";

  const wrap = document.createElement("div");
  wrap.className = `message ${role}`;

  const lbl = document.createElement("span");
  lbl.className = "message-label";
  lbl.textContent = role==="user"?"You":role==="bot"?"ServiceDesk AI":"System";
  wrap.appendChild(lbl);

  const bub = document.createElement("div");
  bub.className = "message-bubble";

  if (role === "bot") {
    const formatted = formatText(text);
    if (useTypewriter && text.length < 1500) {
      typewriterEffect(bub, formatted, () => {
        // Add meta row after typing finishes
        addBotMeta(wrap, meta, text);
      });
    } else {
      bub.innerHTML = formatted;
    }
  } else if (role === "system") {
    bub.innerHTML = formatText(text);
  } else {
    bub.textContent = text;
  }
  wrap.appendChild(bub);

  if (role === "bot" && !useTypewriter) {
    addBotMeta(wrap, meta, text);
  }

  $("chatMessages").appendChild(wrap);
  $("chatMessages").scrollTop = $("chatMessages").scrollHeight;
  return wrap;
}

function addBotMeta(wrap, meta, text) {
  // Citations
  if (meta.citations && meta.citations.length > 0) {
    const box = document.createElement("div");
    box.className = "citations-box";
    const hdr = document.createElement("div");
    hdr.className = "citations-header";
    hdr.innerHTML = `<span>📚 ${meta.citations.length} Knowledge Base Source${meta.citations.length>1?"s":""}</span><span class="citations-toggle">▼</span>`;
    hdr.addEventListener("click", () => box.classList.toggle("collapsed"));
    box.appendChild(hdr);
    const content = document.createElement("div");
    content.className = "citations-content";
    meta.citations.forEach(c => {
      const card = document.createElement("div");
      card.className = "citation-card";
      const pct = c.relevance_score != null ? Math.round(c.relevance_score*100) : null;
      const cls = pct!=null?(pct>=75?"cite-high":pct>=45?"cite-mid":"cite-low"):"cite-low";
      card.innerHTML = `
        <div class="citation-row">
          <span class="citation-title">${escHtml(c.title||"IT Document")}</span>
          ${pct!=null?`<span class="cite-score ${cls}">${pct}%</span>`:""}
        </div>
        <div class="citation-source">${escHtml(c.source||"knowledge_base")}</div>
        ${c.snippet?`<div class="citation-snippet">"${escHtml(c.snippet)}"</div>`:""}
      `;
      content.appendChild(card);
    });
    box.appendChild(content);
    wrap.appendChild(box);
  }

  // Metadata tags
  const metaRow = document.createElement("div");
  metaRow.className = "message-meta";
  const addTag = (text, cls) => {
    const t = document.createElement("span");
    t.className = `tag ${cls}`;
    t.textContent = text;
    metaRow.appendChild(t);
  };
  if (meta.category && meta.category!=="unknown") addTag(meta.category, "tag-cat");
  if (meta.priority) addTag(meta.priority, `tag-${meta.priority.toLowerCase()}`);
  if (meta.status) {
    const cls = {answered:"tag-answered",escalate:"tag-escalate",pending_approval:"tag-pending"}[meta.status]||"tag-unknown";
    addTag(meta.status.replace("_"," "), cls);
  }
  if (meta.ticket_id)   addTag(`🎫 ${meta.ticket_id}`, "tag-ticket");
  if (meta.approval_id) addTag(`⚠️ ${meta.approval_id}`, "tag-approval");
  if (meta.escalated)   addTag("🚨 Escalated", "tag-escalate");
  if (meta.mode && meta.mode!=="rule_fallback") addTag(meta.mode==="mock"?"Mock Mode":`AI: ${meta.mode}`, "tag-mode");
  if (metaRow.children.length) wrap.appendChild(metaRow);

  // Copy button
  const actions = document.createElement("div");
  actions.className = "message-actions";
  const copyBtn = document.createElement("button");
  copyBtn.className = "msg-action-btn";
  copyBtn.textContent = "📋 Copy";
  copyBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(text).then(() => toast("Copied!", "success", 1500));
  });
  actions.appendChild(copyBtn);
  wrap.appendChild(actions);
}

function showTyping() {
  if ($("emptyState")) $("emptyState").style.display = "none";
  const wrap = document.createElement("div");
  wrap.className = "message bot typing-indicator";
  const lbl = document.createElement("span");
  lbl.className = "message-label"; lbl.textContent = "ServiceDesk AI";
  wrap.appendChild(lbl);
  const bub = document.createElement("div");
  bub.className = "message-bubble";
  [1,2,3].forEach(() => { const d=document.createElement("span"); d.className="typing-dot"; bub.appendChild(d); });
  wrap.appendChild(bub);
  $("chatMessages").appendChild(wrap);
  $("chatMessages").scrollTop = $("chatMessages").scrollHeight;
  return wrap;
}

function clearChatUI() {
  const cm = $("chatMessages");
  cm.innerHTML = "";
  const em = $("emptyState");
  if (em) { cm.appendChild(em); em.style.display = "block"; }
  hideContextPanel();
}

/* ============================================================
   Context Panel
   ============================================================ */
function showContextPanel(data) {
  const items = [];
  if (data.ticket_id) items.push(`<div class="context-item ctx-ticket"><span class="ctx-icon">🎫</span><div><div class="ctx-label">Support Ticket Created</div><div class="ctx-detail">${escHtml(data.ticket_id)} · Priority: ${data.priority||"P3"} · Status: OPEN</div></div></div>`);
  if (data.approval_id) items.push(`<div class="context-item ctx-approval"><span class="ctx-icon">⚠️</span><div><div class="ctx-label">Approval Required</div><div class="ctx-detail">ID: ${escHtml(data.approval_id)} · Pending decision</div></div></div>`);
  if (data.escalated) items.push(`<div class="context-item ctx-escalate"><span class="ctx-icon">🚨</span><div><div class="ctx-label">Escalated to IT Operations</div><div class="ctx-detail">${escHtml(data.note||"")}</div></div></div>`);
  if (items.length) {
    $("contextItems").innerHTML = items.join("");
    $("contextPanel").hidden = false;
  }
}
function hideContextPanel() { $("contextPanel").hidden = true; $("contextItems").innerHTML = ""; }
$("closeContextPanel").addEventListener("click", hideContextPanel);

/* ── Textarea auto-resize ── */
function adjustTA(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 120) + "px";
}
$("messageInput").addEventListener("input", () => {
  adjustTA($("messageInput"));
  $("charCounter").textContent = `${$("messageInput").value.length}/2000`;
  updateSuggestions($("messageInput").value);
});
$("messageInput").addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    $("chatForm").dispatchEvent(new Event("submit", { cancelable: true }));
  }
});
$("chatForm").addEventListener("submit", e => {
  e.preventDefault();
  const txt = $("messageInput").value.trim();
  if (txt) handleSend(txt);
});

/* ── Quick prompts ── */
document.addEventListener("click", e => {
  const qp = e.target.closest(".qp-card");
  if (qp?.dataset.prompt) { handleSend(qp.dataset.prompt); return; }
  const li = e.target.closest(".quick-list li");
  if (li?.dataset.msg) {
    $("messageInput").value = li.dataset.msg;
    adjustTA($("messageInput"));
    $("messageInput").focus();
    return;
  }
});

/* ── Clear / Export ── */
$("clearChatBtn").addEventListener("click", () => {
  convId = null; clearChatUI();
  appendMsg("system", "🔄 New conversation started. How can I help you?");
});
$("exportChatBtn").addEventListener("click", () => {
  const msgs = $("chatMessages").querySelectorAll(".message");
  let out = "# ServiceDesk-AI Conversation Export\n\n";
  msgs.forEach(m => {
    const role = m.classList.contains("user")?"You":m.classList.contains("bot")?"ServiceDesk AI":"System";
    const text = m.querySelector(".message-bubble")?.textContent || "";
    out += `**${role}:** ${text.trim()}\n\n`;
  });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([out], { type: "text/markdown" }));
  a.download = `servicedesk-chat-${Date.now()}.md`;
  a.click();
  toast("Conversation exported", "success");
});

/* ============================================================
   Tickets
   ============================================================ */
async function loadTickets() {
  if (!authToken) {
    $("ticketTableWrapper").innerHTML = `<div class="loading-state">Please <button class="link-btn" id="loginToViewTickets">sign in</button> to view tickets.</div>`;
    $("loginToViewTickets") && $("loginToViewTickets").addEventListener("click", () => showModal("loginModal"));
    return;
  }

  const statusF   = $("ticketStatusFilter").value;
  const priorityF = $("ticketPriorityFilter").value;
  const searchQ   = $("ticketSearch").value.toLowerCase();

  $("ticketsLoading").style.display = "block";
  $("ticketTable").hidden = true;
  $("ticketsEmpty").hidden = true;

  try {
    let url = "/api/tickets?limit=200";
    if (statusF)   url += `&status=${statusF}`;
    if (priorityF) url += `&priority=${priorityF}`;
    allTickets = await apiFetch(url);

    let filtered = allTickets;
    if (searchQ) filtered = allTickets.filter(t =>
      t.id.toLowerCase().includes(searchQ) ||
      t.title.toLowerCase().includes(searchQ) ||
      t.category.toLowerCase().includes(searchQ)
    );

    // Update stats
    const counts = { total: allTickets.length, open:0, inprogress:0, escalated:0, resolved:0 };
    allTickets.forEach(t => {
      if (t.status==="OPEN")        counts.open++;
      if (t.status==="IN_PROGRESS") counts.inprogress++;
      if (t.status==="ESCALATED")   counts.escalated++;
      if (t.status==="RESOLVED")    counts.resolved++;
    });
    $("statTotal").textContent      = counts.total;
    $("statOpen").textContent       = counts.open;
    $("statInProgress").textContent = counts.inprogress;
    $("statEscalated").textContent  = counts.escalated;
    $("statResolved").textContent   = counts.resolved;

    $("ticketsLoading").style.display = "none";
    if (!filtered.length) {
      $("ticketsEmpty").hidden = false; return;
    }

    const tbody = $("ticketTableBody");
    tbody.innerHTML = "";
    filtered.forEach(t => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><code class="mono">${escHtml(t.id)}</code></td>
        <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${escHtml(t.title)}">${escHtml(t.title)}</td>
        <td>${escHtml(t.category)}</td>
        <td><span class="badge-pill pill-${t.priority.toLowerCase()}">${t.priority}</span></td>
        <td><span class="badge-pill pill-${t.status.toLowerCase().replace("_","")}">${t.status.replace("_"," ")}</span></td>
        <td style="max-width:130px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${escHtml(t.assigned_group||"—")}</td>
        <td>${fmtShort(t.created_at)}</td>
        <td><button class="link-btn" onclick="viewTicket('${t.id}')">View →</button></td>
      `;
      tbody.appendChild(tr);
    });
    $("ticketTable").hidden = false;
  } catch(err) {
    $("ticketsLoading").style.display = "none";
    $("ticketTableWrapper").innerHTML = `<div class="loading-state">❌ Failed to load tickets: ${escHtml(err.message)}</div>`;
    toast("Failed to load tickets", "error");
  }
}

// Ticket filters
["ticketStatusFilter","ticketPriorityFilter"].forEach(id => $(id)?.addEventListener("change", loadTickets));
$("ticketSearch")?.addEventListener("input", loadTickets);
$("refreshTicketsBtn")?.addEventListener("click", loadTickets);

async function viewTicket(id) {
  try {
    const t = await apiFetch(`/api/tickets/${id}`);
    $("ticketModalTitle").textContent = `Ticket ${t.id}`;
    $("ticketModalBody").innerHTML = buildTicketDetail(t);
    showModal("ticketModal");
  } catch(err) {
    toast("Failed to load ticket: " + err.message, "error");
  }
}
window.viewTicket = viewTicket;

function buildTicketDetail(t) {
  const priorityClass = `pill-${t.priority.toLowerCase()}`;
  const statusClass   = `pill-${t.status.toLowerCase().replace("_","")}`;
  const history = (t.status_history||[]).map(h => `
    <div class="timeline-item">
      <div class="tl-dot ${h.new_status.toLowerCase()}"></div>
      <div class="tl-content">
        <div class="tl-status">${escHtml(h.new_status.replace("_"," "))}${h.old_status?" ← "+escHtml(h.old_status.replace("_"," ")):""}</div>
        ${h.notes?`<div class="tl-notes">${escHtml(h.notes)}</div>`:""}
        <div class="tl-time">${fmt(h.timestamp)}</div>
      </div>
    </div>`).join("");

  return `
    <div class="tm-header">
      <div>
        <div class="tm-id">${escHtml(t.id)}</div>
        <div class="tm-title">${escHtml(t.title)}</div>
        <div class="tm-badges">
          <span class="badge-pill ${priorityClass}">${t.priority}</span>
          <span class="badge-pill ${statusClass}">${t.status.replace("_"," ")}</span>
          ${t.is_escalated?'<span class="badge-pill pill-escalated">🚨 Escalated</span>':""}
        </div>
      </div>
    </div>

    <div>
      <div class="tm-section-title">Description</div>
      <div class="tm-desc">${escHtml(t.description)}</div>
    </div>

    <div class="tm-grid">
      <div class="tm-field"><div class="tm-field-label">Category</div><div class="tm-field-val">${escHtml(t.category)} ${t.subcategory?`/ ${escHtml(t.subcategory)}`:"" }</div></div>
      <div class="tm-field"><div class="tm-field-label">Assigned Group</div><div class="tm-field-val">${escHtml(t.assigned_group||"—")}</div></div>
      <div class="tm-field"><div class="tm-field-label">Impact</div><div class="tm-field-val">${escHtml(t.impact)}</div></div>
      <div class="tm-field"><div class="tm-field-label">Urgency</div><div class="tm-field-val">${escHtml(t.urgency)}</div></div>
      <div class="tm-field"><div class="tm-field-label">Created</div><div class="tm-field-val">${fmt(t.created_at)}</div></div>
      <div class="tm-field"><div class="tm-field-label">Updated</div><div class="tm-field-val">${fmt(t.updated_at)}</div></div>
    </div>

    ${t.resolution_notes?`<div><div class="tm-section-title">Resolution</div><div class="tm-desc">${escHtml(t.resolution_notes)}</div></div>`:""}
    ${t.escalation_reason?`<div><div class="tm-section-title">Escalation Reason</div><div class="tm-desc">${escHtml(t.escalation_reason)}</div></div>`:""}

    ${history?`<div><div class="tm-section-title">Status Timeline</div><div class="timeline">${history}</div></div>`:""}
  `;
}

// New Ticket
$("newTicketBtn")?.addEventListener("click", () => {
  if (!authToken) { toast("Sign in to create tickets", "warning"); showModal("loginModal"); return; }
  showModal("newTicketModal");
});

$("newTicketForm")?.addEventListener("submit", async e => {
  e.preventDefault();
  const btn = $("submitNewTicket");
  btn.disabled = true; btn.textContent = "Creating…";
  try {
    const t = await apiFetch("/api/tickets", {
      method: "POST",
      body: JSON.stringify({
        title: $("ntTitle").value.trim(),
        description: $("ntDescription").value.trim(),
        category: $("ntCategory").value,
        priority: $("ntPriority").value,
      })
    });
    hideModal("newTicketModal");
    toast(`Ticket ${t.id} created!`, "success");
    $("newTicketForm").reset();
    loadTickets();
  } catch(err) {
    toast("Failed: " + err.message, "error");
  } finally {
    btn.disabled = false; btn.textContent = "Create Ticket";
  }
});

/* ============================================================
   Approvals
   ============================================================ */
async function loadApprovals() {
  const grid = $("approvalsGrid");
  if (!authToken || !currentUser || currentUser.role === "employee") {
    grid.innerHTML = `<div class="loading-state">Only Support Agents and Admins can view approvals.</div>`;
    return;
  }

  grid.innerHTML = `<div class="loading-state">Loading approvals…</div>`;
  try {
    const data = await apiFetch("/api/approvals");
    if (!data.length) {
      grid.innerHTML = `<div class="loading-state">✅ No pending approvals.</div>`;
      return;
    }
    grid.innerHTML = data.map(a => `
      <div class="approval-card ${a.risk_level==="HIGH"||a.risk_level==="CRITICAL"?"high":""}">
        <div class="approval-header">
          <div>
            <div class="approval-id">${escHtml(a.id)}</div>
            <div class="approval-action">⚙️ ${escHtml(a.action_name.replace(/_/g," "))}</div>
          </div>
          <span class="badge-pill pill-${a.risk_level.toLowerCase()}">${a.risk_level}</span>
        </div>
        <div class="approval-reason">${escHtml(a.reason)}</div>
        <div class="approval-meta">
          ${a.ticket_id?`<span class="badge-pill pill-open">🎫 ${escHtml(a.ticket_id)}</span>`:""}
          <span class="badge-pill pill-pending">⏳ PENDING</span>
        </div>
        <div class="approval-btns">
          <button class="approve-btn" onclick="decideApproval('${a.id}','APPROVED')">✅ Approve</button>
          <button class="reject-btn"  onclick="decideApproval('${a.id}','REJECTED')">❌ Reject</button>
        </div>
      </div>
    `).join("");
  } catch(err) {
    grid.innerHTML = `<div class="loading-state">❌ ${escHtml(err.message)}</div>`;
  }
}

async function decideApproval(id, decision) {
  const notes = decision === "REJECTED" ? prompt("Optional: reason for rejection?") : null;
  try {
    await apiFetch(`/api/approvals/${id}/decision`, {
      method: "POST",
      body: JSON.stringify({ decision, decision_notes: notes })
    });
    toast(`Approval ${decision.toLowerCase()}`, decision==="APPROVED"?"success":"warning");
    loadApprovals(); loadApprovalBadge();
  } catch(err) {
    toast("Decision failed: " + err.message, "error");
  }
}
window.decideApproval = decideApproval;

$("refreshApprovalsBtn")?.addEventListener("click", loadApprovals);

/* ============================================================
   Smart Suggestions
   ============================================================ */
const SUGGESTION_MAP = {
  "vpn":       ["VPN keeps disconnecting","Check VPN service health","Reset VPN credentials"],
  "wifi":      ["Wi-Fi not connecting","Forget and reconnect Wi-Fi","Check router status"],
  "wi-fi":     ["Wi-Fi not connecting","Forget and reconnect Wi-Fi","Run network diagnostics"],
  "password":  ["Reset my password","My account is locked","Forgot password steps"],
  "email":     ["Outlook not syncing","Email quota full","Calendar not updating"],
  "printer":   ["Printer spooler stuck","Reinstall printer driver","Printer offline fix"],
  "slow":      ["PC running slow fix","Clear temp files","High CPU usage troubleshoot"],
  "mfa":       ["MFA code not working","Reset authenticator app","Lost access to 2FA"],
  "account":   ["Account locked","Check account status","Password reset"],
  "ticket":    ["Create a support ticket","Check my open tickets","Escalate existing ticket"],
  "phishing":  ["Received phishing email","Report suspicious email","Account may be compromised"],
  "screen":    ["Monitor not detected","Display flickering","External screen setup"],
  "install":   ["Software installation request","App not launching","License activation issue"],
};

function updateSuggestions(val) {
  const v = val.toLowerCase();
  if (v.length < 3) { $("suggestionsBar").hidden = true; return; }
  const matched = [];
  for (const [key, chips] of Object.entries(SUGGESTION_MAP)) {
    if (v.includes(key)) { matched.push(...chips); break; }
  }
  if (!matched.length) { $("suggestionsBar").hidden = true; return; }
  const chips = $("suggestionsChips");
  chips.innerHTML = matched.slice(0,4).map(s =>
    `<button class="sugg-chip" data-prompt="${escHtml(s)}">${escHtml(s)}</button>`
  ).join("");
  $("suggestionsBar").hidden = false;
}

document.addEventListener("click", e => {
  const chip = e.target.closest(".sugg-chip");
  if (chip) {
    handleSend(chip.dataset.prompt);
    $("suggestionsBar").hidden = true;
  }
});

/* ============================================================
   Floating Action Button
   ============================================================ */
$("fabBtn").addEventListener("click", () => {
  switchTab("chat");
  $("messageInput").focus();
});
// Hide FAB when on chat tab already
document.querySelectorAll(".nav-item[data-tab]").forEach(btn => {
  btn.addEventListener("click", () => {
    $("fabBtn").style.display = btn.dataset.tab === "chat" ? "none" : "flex";
  });
});

/* ============================================================
   Count-Up Animation for KPI numbers
   ============================================================ */
function countUp(el, target, dur = 800) {
  const start = performance.now();
  const from = parseInt(el.textContent) || 0;
  function step(now) {
    const progress = Math.min((now - start) / dur, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    el.textContent = Math.round(from + (target - from) * eased);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

/* ============================================================
   Service Health Tab
   ============================================================ */
const SERVICE_DEFINITIONS = [
  { id:"vpn",     name:"VPN Gateway",       icon:"🌐", cluster:"us-east-vpn" },
  { id:"email",   name:"Email / Exchange",   icon:"✉️", cluster:"m365-tenant" },
  { id:"wifi",    name:"Wi-Fi Access Points",icon:"📶", cluster:"hq-access-points" },
  { id:"jira",    name:"Jira / Ticketing",   icon:"🎫", cluster:"jira-prod-01" },
  { id:"payroll", name:"Payroll / ERP",      icon:"💰", cluster:"erp-prod" },
  { id:"ad",      name:"Active Directory",   icon:"🔐", cluster:"dc-primary" },
  { id:"storage", name:"File Storage",       icon:"💾", cluster:"nas-cluster-01" },
];

const INCIDENTS = [
  { title:"Jira intermittent slowness", detail:"Users may experience slow load times on Jira dashboards.", time:"2h ago", resolved:false },
  { title:"VPN maintenance window", detail:"Scheduled maintenance on us-east-vpn completed successfully.", time:"Yesterday", resolved:true },
  { title:"Email delivery delay (resolved)", detail:"Brief delay in outbound email delivery has been resolved.", time:"2 days ago", resolved:true },
];

async function loadServiceHealth() {
  const grid = $("servicesGrid");
  grid.innerHTML = `<div class="loading-state">Fetching service statuses…</div>`;

  // Fetch real status from backend action registry
  let realStatuses = {};
  try {
    const vpnRes = await apiFetch("/api/actions/check_service_health/execute", {
      method: "POST", body: JSON.stringify({ params:{ service_name:"vpn" } })
    }).catch(() => null);
    const wifiRes = await apiFetch("/api/actions/check_service_health/execute", {
      method: "POST", body: JSON.stringify({ params:{ service_name:"wifi" } })
    }).catch(() => null);
    const emailRes = await apiFetch("/api/actions/check_service_health/execute", {
      method: "POST", body: JSON.stringify({ params:{ service_name:"email" } })
    }).catch(() => null);
    if (vpnRes?.details)   realStatuses["vpn"]   = vpnRes.details;
    if (wifiRes?.details)  realStatuses["wifi"]  = wifiRes.details;
    if (emailRes?.details) realStatuses["email"] = emailRes.details;
  } catch(_){}

  grid.innerHTML = "";
  let allOp = true, anyDown = false;

  const cards = SERVICE_DEFINITIONS.map(svc => {
    const real = realStatuses[svc.id];
    const rawStatus = real?.status || (svc.id==="jira"?"DEGRADED":"OPERATIONAL");
    const uptime   = real?.uptime  || (svc.id==="jira"?"98.50%":svc.id==="ad"?"99.99%":"99.97%");
    const isOp  = rawStatus === "OPERATIONAL";
    const isDeg = rawStatus === "DEGRADED";
    const isDown= rawStatus === "DOWN";
    if (isDeg || isDown) allOp = false;
    if (isDown) anyDown = true;

    const statusClass = isDown?"down":isDeg?"degraded":"";
    const statusLabel = isDown?"🔴 Down":isDeg?"🟡 Degraded":"🟢 Operational";
    const uptimePct   = parseFloat(uptime);
    const fillClass   = isDown?"down":isDeg?"degraded":"";

    return `
      <div class="service-card ${statusClass}">
        <div class="service-card-top">
          <div class="service-icon-wrap">${svc.icon}</div>
          <div class="service-status-dot ${statusClass}"></div>
        </div>
        <div class="service-name">${escHtml(svc.name)}</div>
        <div class="service-status ${statusClass}">${statusLabel}</div>
        <div class="service-metrics">
          <div class="svc-metric">
            <div class="svc-metric-val">${escHtml(uptime)}</div>
            <div class="svc-metric-label">Uptime</div>
          </div>
          <div class="svc-metric">
            <div class="svc-metric-val">${isDown?"—":isOp?"✅":"⚠️"}</div>
            <div class="svc-metric-label">Status</div>
          </div>
          <div class="svc-metric">
            <div class="svc-metric-val" style="font-size:.68rem">${escHtml(svc.cluster)}</div>
            <div class="svc-metric-label">Cluster</div>
          </div>
        </div>
        <div class="uptime-bar-wrap">
          <div class="uptime-bar-label">
            <span>Uptime (30d)</span><span>${escHtml(uptime)}</span>
          </div>
          <div class="uptime-bar">
            <div class="uptime-bar-fill ${fillClass}" style="width:${Math.min(uptimePct,100)}%"></div>
          </div>
        </div>
      </div>`;
  });
  grid.innerHTML = cards.join("");

  // Overall banner
  const banner = $("overallStatusBanner");
  if (anyDown) {
    banner.className = "overall-status-banner down";
    $("overallIcon").textContent  = "🔴";
    $("overallTitle").textContent = "Service Disruption Detected";
    $("overallUptime").textContent = "Incidents Active";
  } else if (!allOp) {
    banner.className = "overall-status-banner degraded";
    $("overallIcon").textContent  = "🟡";
    $("overallTitle").textContent = "Partial System Degradation";
    $("overallUptime").textContent = "Some services degraded";
  } else {
    banner.className = "overall-status-banner";
    $("overallIcon").textContent  = "✅";
    $("overallTitle").textContent = "All Systems Operational";
    $("overallUptime").textContent = "99.97% avg uptime";
  }
  const now = new Date().toLocaleTimeString();
  $("overallSub").textContent = `${SERVICE_DEFINITIONS.length} services monitored · Last checked ${now}`;
  $("uptimeClock").textContent = `Last refreshed: ${now}`;

  // Incidents
  $("incidentList").innerHTML = INCIDENTS.map(inc => `
    <div class="incident-item ${inc.resolved?"resolved":""}">
      <span class="incident-icon">${inc.resolved?"✅":"⚠️"}</span>
      <div>
        <div class="incident-title">${escHtml(inc.title)}</div>
        <div class="incident-detail">${escHtml(inc.detail)}</div>
      </div>
      <div class="incident-time">${inc.time}</div>
    </div>`).join("");

  // Show badge
  $("servicesBadge").hidden = false;
}

$("refreshServicesBtn")?.addEventListener("click", loadServiceHealth);

/* ============================================================
   Analytics — with count-up
   ============================================================ */
async function loadAnalytics() {
  if (!authToken) {
    toast("Sign in to view analytics", "info"); return;
  }
  try {
    const [tickets, approvals] = await Promise.all([
      apiFetch("/api/tickets?limit=500"),
      apiFetch("/api/approvals").catch(() => [])
    ]);

    // KPIs with count-up animation
    countUp($("kpiTotal"),    tickets.length);
    countUp($("kpiP1"),       tickets.filter(t=>t.priority==="P1").length);
    countUp($("kpiResolved"), tickets.filter(t=>t.status==="RESOLVED"||t.status==="CLOSED").length);
    countUp($("kpiPending"),  approvals.length);

    // Category chart
    const catMap = {};
    tickets.forEach(t => { catMap[t.category] = (catMap[t.category]||0)+1; });
    const maxCat = Math.max(...Object.values(catMap), 1);
    $("categoryChart").innerHTML = Object.entries(catMap)
      .sort((a,b)=>b[1]-a[1])
      .map(([cat, cnt]) => `
        <div class="bar-row">
          <div class="bar-label">${escHtml(cat)}</div>
          <div class="bar-track"><div class="bar-fill" style="width:${(cnt/maxCat*100).toFixed(1)}%"></div></div>
          <div class="bar-count">${cnt}</div>
        </div>`).join("");

    // Priority donut
    const priColors = { P1:"#dc2626", P2:"#ea580c", P3:"#d97706", P4:"#64748b" };
    const priMap = { P1:0,P2:0,P3:0,P4:0 };
    tickets.forEach(t => { if(priMap[t.priority]!==undefined) priMap[t.priority]++; });
    buildDonut($("priorityDonut"), $("priorityLegend"), priMap, priColors, tickets.length);

    // Status chart
    const statColors = { OPEN:"#2563eb",IN_PROGRESS:"#d97706",ESCALATED:"#dc2626",RESOLVED:"#10b981",CLOSED:"#64748b",PENDING_APPROVAL:"#f59e0b" };
    const statMap = {};
    tickets.forEach(t => { statMap[t.status]=(statMap[t.status]||0)+1; });
    const maxStat = Math.max(...Object.values(statMap),1);
    $("statusChart").innerHTML = Object.entries(statMap).map(([s,c])=>`
      <div class="status-block">
        <div class="status-block-val">${c}</div>
        <div class="status-bar-outer">
          <div class="status-bar-inner" style="height:${(c/maxStat*80).toFixed(0)}px;background:${statColors[s]||"#94a3b8"}"></div>
        </div>
        <div class="status-block-label">${s.replace("_"," ")}</div>
      </div>`).join("");

    // Activity feed (recent tickets)
    const recent = [...tickets].sort((a,b)=>new Date(b.created_at)-new Date(a.created_at)).slice(0,8);
    $("activityFeed").innerHTML = recent.map(t=>`
      <div class="activity-item">
        <div class="activity-dot" style="background:${statColors[t.status]||"#94a3b8"}"></div>
        <div style="flex:1">
          <div class="activity-text">${escHtml(t.title.substring(0,50))}${t.title.length>50?"…":""}</div>
          <div style="display:flex;gap:.4rem;align-items:center;margin-top:.2rem;">
            <span class="badge-pill pill-${t.priority.toLowerCase()}" style="font-size:.62rem;padding:.08rem .4rem">${t.priority}</span>
            <span style="font-size:.68rem;color:var(--text3)">${escHtml(t.category)}</span>
          </div>
        </div>
        <div class="activity-time">${fmtShort(t.created_at)}</div>
      </div>`).join("");

  } catch(err) {
    toast("Analytics load failed: " + err.message, "error");
  }
}

function buildDonut(svgContainer, legendEl, dataMap, colors, total) {
  const entries = Object.entries(dataMap).filter(([,v])=>v>0);
  const r = 38, cx = 50, cy = 50, circ = 2*Math.PI*r;
  let offset = 0;
  const paths = entries.map(([key, val]) => {
    const pct = val/Math.max(total,1);
    const dasharray = `${(pct*circ).toFixed(2)} ${circ.toFixed(2)}`;
    const dashoffset = -offset * circ;
    offset += pct;
    return `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${colors[key]||"#94a3b8"}" stroke-width="12" stroke-dasharray="${dasharray}" stroke-dashoffset="${dashoffset}" />`;
  });
  svgContainer.innerHTML = `
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">${paths.join("")}</svg>
    <div class="donut-center-text"><div class="donut-center-num">${total}</div><div>tickets</div></div>
  `;
  legendEl.innerHTML = entries.map(([key,val])=>`
    <div class="legend-item">
      <div class="legend-dot" style="background:${colors[key]||"#94a3b8"}"></div>
      <span>${key}</span><span style="margin-left:auto;font-weight:700">${val}</span>
    </div>`).join("");
}

/* ============================================================
   Audit Logs
   ============================================================ */
async function loadAuditLogs() {
  if (!authToken || !currentUser || currentUser.role !== "admin") {
    $("auditLoading").style.display = "block";
    $("auditLoading").textContent = "Admin access required to view audit logs.";
    return;
  }
  const eventFilter = $("auditEventFilter").value;
  let url = "/api/audit?limit=100";
  if (eventFilter) url += `&event_type=${eventFilter}`;

  $("auditLoading").style.display = "block";
  $("auditTable").hidden = true;
  $("auditEmpty").hidden = true;

  try {
    const data = await apiFetch(url);
    $("auditLoading").style.display = "none";
    if (!data.length) { $("auditEmpty").hidden = false; return; }
    const eventIcons = {
      LOGIN_SUCCESS:"✅",LOGIN_FAILED:"❌",USER_REGISTERED:"👤",
      TICKET_CREATED:"🎫",TICKET_ESCALATED:"🚨",TICKET_RESOLVED:"✅",
      APPROVAL_APPROVED:"👍",APPROVAL_REJECTED:"👎",SELF_APPROVAL_BLOCKED:"🚫",
    };
    $("auditTableBody").innerHTML = data.map(e=>`
      <tr>
        <td style="white-space:nowrap;font-family:var(--mono);font-size:.75rem">${fmt(e.timestamp)}</td>
        <td><span style="font-size:.82rem">${eventIcons[e.event_type]||"📋"}</span> ${escHtml(e.event_type.replace(/_/g," "))}</td>
        <td>${escHtml(e.actor_username||"—")}</td>
        <td>${e.target_type?escHtml(e.target_type)+" "+escHtml(e.target_id||""):"—"}</td>
        <td style="font-size:.78rem;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escHtml(e.details||"")}">${escHtml((e.details||"").substring(0,80))}</td>
      </tr>`).join("");
    $("auditTable").hidden = false;
  } catch(err) {
    $("auditLoading").textContent = `❌ ${err.message}`;
  }
}
$("auditEventFilter")?.addEventListener("change", loadAuditLogs);
$("refreshAuditBtn")?.addEventListener("click", loadAuditLogs);

/* ============================================================
   Initialization
   ============================================================ */
(function init() {
  if (authToken && currentUser) {
    setAuth(authToken, currentUser);
    hideModal("loginModal");
    loadTicketBadge();
    loadApprovalBadge();
  } else {
    setAuth(null, null);
    showModal("loginModal");
  }
  checkHealth();
  checkRagStatus();
  // Periodic refresh every 30s
  setInterval(() => { checkHealth(); checkRagStatus(); loadTicketBadge(); loadApprovalBadge(); }, 30000);
})();

/* ============================================================
   NOTIFICATION SYSTEM
   ============================================================ */
let notifications = [];
let notifOpen = false;

function addNotif(icon, title, desc, onClick = null) {
  const n = {
    id: Date.now(),
    icon, title, desc,
    time: new Date().toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' }),
    unread: true,
    onClick
  };
  notifications.unshift(n);
  renderNotifList();
  // Flash bell
  const bell = $("notifBell");
  $("notifDot").hidden = false;
  bell.classList.remove("ringing");
  void bell.offsetWidth; // reflow to restart animation
  bell.classList.add("ringing");
}

function renderNotifList() {
  const list = $("notifList");
  if (!notifications.length) {
    list.innerHTML = `<div class="notif-empty">No new notifications</div>`;
    $("notifDot").hidden = true;
    return;
  }
  const unread = notifications.filter(n => n.unread).length;
  $("notifDot").hidden = unread === 0;
  list.innerHTML = notifications.slice(0, 10).map(n => `
    <div class="notif-item ${n.unread ? 'unread' : ''}" data-notif-id="${n.id}">
      <span class="notif-item-icon">${n.icon}</span>
      <div class="notif-item-body">
        <div class="notif-item-title">${escHtml(n.title)}</div>
        <div class="notif-item-desc">${escHtml(n.desc)}</div>
        <div class="notif-item-time">${n.time}</div>
      </div>
    </div>`).join("");
}

$("notifBell").addEventListener("click", (e) => {
  e.stopPropagation();
  notifOpen = !notifOpen;
  $("notifDropdown").hidden = !notifOpen;
  if (notifOpen) {
    // Mark all read
    notifications.forEach(n => n.unread = false);
    renderNotifList();
  }
});

document.addEventListener("click", e => {
  if (notifOpen && !e.target.closest("#notifDropdown") && !e.target.closest("#notifBell")) {
    notifOpen = false;
    $("notifDropdown").hidden = true;
  }
  const ni = e.target.closest(".notif-item");
  if (ni) {
    const id = parseInt(ni.dataset.notifId);
    const notif = notifications.find(n => n.id === id);
    if (notif?.onClick) { notif.onClick(); notifOpen = false; $("notifDropdown").hidden = true; }
  }
});

$("clearNotifsBtn").addEventListener("click", () => {
  notifications = [];
  renderNotifList();
  notifOpen = false;
  $("notifDropdown").hidden = true;
});

/* ── Hook notifications into chat responses ── */
const _origLoadTicketBadge = loadTicketBadge;

/* Override handleSend to emit notifications */
const _origHandleSend = handleSend;

/* Watch for new tickets/approvals in chat responses */
function notifyFromChatData(data) {
  if (data.ticket_id) {
    addNotif("🎫", "Ticket Created", `${data.ticket_id} · Priority ${data.priority || 'P3'}`,
      () => switchTab("tickets"));
  }
  if (data.approval_id) {
    addNotif("⚠️", "Approval Required", `${data.approval_id} needs your decision`,
      () => switchTab("approvals"));
  }
  if (data.escalated) {
    addNotif("🚨", "Issue Escalated", "Your request was escalated to IT Operations");
  }
}

/* ============================================================
   AI CONFIDENCE METER
   ============================================================ */
function appendConfidenceMeter(parentWrap, confidencePct) {
  if (confidencePct == null) return;
  const cls = confidencePct >= 75 ? "" : confidencePct >= 45 ? "mid" : "low";
  const bar = document.createElement("div");
  bar.className = "confidence-bar";
  bar.innerHTML = `
    <span class="confidence-label">AI Confidence</span>
    <div class="confidence-track">
      <div class="confidence-fill ${cls}" style="width:0%"></div>
    </div>
    <span class="confidence-pct ${cls}">${confidencePct}%</span>
  `;
  parentWrap.appendChild(bar);
  // Animate fill after paint
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      bar.querySelector(".confidence-fill").style.width = confidencePct + "%";
    });
  });
}

/* Patch handleSend to add confidence + notification ── */
async function handleSend(msg) {
  if (!msg || isBusy) return;
  isBusy = true;
  appendMsg("user", msg);
  $("messageInput").value = "";
  adjustTA($("messageInput"));
  $("sendBtn").disabled = true;
  $("charCounter").textContent = "0/2000";
  $("suggestionsBar").hidden = true;
  hideContextPanel();

  const typing = showTyping();
  try {
    const data = await apiFetch("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message: msg, conversation_id: convId })
    });
    convId = data.conversation_id || convId;
    typing.remove();

    const msgWrap = appendMsg("bot", data.reply, {
      category: data.category, status: data.status, priority: data.priority,
      ticket_id: data.ticket_id, approval_id: data.approval_id,
      citations: data.citations || [], escalated: data.escalated, mode: data.mode,
      note: data.note,
    }, true);

    // Confidence meter from triage
    const triage = data._triage || {};
    const confidence = triage.confidence
      ? Math.round(triage.confidence * 100)
      : (data.mode === "mock" ? 62 : data.status === "answered" ? 88 : 55);
    appendConfidenceMeter(msgWrap, confidence);

    showContextPanel(data);
    notifyFromChatData(data);
    loadTicketBadge();
    loadApprovalBadge();

    // Store message for summary
    chatHistory.push({ role: "user", text: msg });
    chatHistory.push({ role: "bot", text: data.reply, category: data.category, priority: data.priority });

  } catch(err) {
    typing.remove();
    appendMsg("system", `❌ Request failed. Backend may be offline. (${err.message})`);
    toast("Chat request failed: " + err.message, "error");
  } finally {
    isBusy = false;
    $("sendBtn").disabled = false;
    $("messageInput").focus();
  }
}

// Store chat for summary
const chatHistory = [];

/* ============================================================
   SESSION SUMMARY
   ============================================================ */
$("summaryBtn").addEventListener("click", async () => {
  if (!chatHistory.length) {
    toast("Start a conversation first!", "info"); return;
  }
  showModal("summaryModal");
  $("summaryContent").innerHTML = `<div class="loading-state">🤖 Generating AI summary…</div>`;

  // Build summary from chatHistory
  const msgs = chatHistory.filter(m => m.role === "user").map(m => m.text);
  const categories = [...new Set(chatHistory.filter(m => m.category).map(m => m.category))];
  const priorities  = [...new Set(chatHistory.filter(m => m.priority).map(m => m.priority))];
  const totalTurns  = chatHistory.filter(m => m.role === "user").length;

  // Try LLM summary via chat (one-shot)
  let aiSummary = "";
  if (authToken && totalTurns >= 2) {
    try {
      const summaryPrompt = `Summarize this IT support session in 2-3 sentences. Issues discussed: ${msgs.slice(0,5).join("; ")}. Keep it concise and professional.`;
      const res = await apiFetch("/api/chat", {
        method: "POST",
        body: JSON.stringify({ message: summaryPrompt, conversation_id: null })
      });
      aiSummary = res.reply;
    } catch(_) {}
  }

  const catTags = categories.length
    ? categories.map(c => `<span class="tag tag-cat">${escHtml(c)}</span>`).join("")
    : `<span class="tag tag-unknown">general</span>`;

  const priTags = priorities.length
    ? priorities.map(p => `<span class="tag tag-${p.toLowerCase()}">${escHtml(p)}</span>`).join("")
    : "";

  $("summaryContent").innerHTML = `
    <div class="summary-block">
      <div class="summary-block-title">📊 Session Overview</div>
      <div class="summary-block-body">
        <strong>${totalTurns}</strong> message${totalTurns !== 1 ? 's' : ''} exchanged in this session.
      </div>
      <div class="summary-tags" style="margin-top:.5rem;">${catTags}${priTags}</div>
    </div>

    ${aiSummary ? `
    <div class="summary-block">
      <div class="summary-block-title">🤖 AI Summary</div>
      <div class="summary-block-body">${escHtml(aiSummary)}</div>
    </div>` : ""}

    <div class="summary-block">
      <div class="summary-block-title">💬 Issues Discussed</div>
      <div class="summary-block-body">
        <ul style="margin-left:1rem;">
          ${msgs.slice(0, 6).map(m => `<li style="margin-bottom:.3rem;">${escHtml(m.substring(0, 90))}${m.length > 90 ? "…" : ""}</li>`).join("")}
        </ul>
      </div>
    </div>

    <div style="display:flex;gap:.5rem;margin-top:.25rem;">
      <button class="primary-btn" style="flex:1" onclick="hideModal('summaryModal')">Close</button>
      <button class="secondary-btn" style="flex:1" onclick="exportSummary()">📥 Export</button>
    </div>
  `;
});

$("closeSummaryModal").addEventListener("click", () => hideModal("summaryModal"));

function exportSummary() {
  const content = $("summaryContent").innerText;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([content], { type: "text/plain" }));
  a.download = `session-summary-${Date.now()}.txt`;
  a.click();
  toast("Summary exported!", "success");
}
window.exportSummary = exportSummary;

/* ============================================================
   Enhanced loadTickets / loadApprovals with notifications
   ============================================================ */
let _prevApprovalCount = 0;
let _prevTicketCount   = 0;

// Override badge loaders to emit notifications on changes
async function loadTicketBadge() {
  if (!authToken) return;
  try {
    const data = await apiFetch("/api/tickets?limit=200");
    const open = data.filter(t => t.status === "OPEN" || t.status === "IN_PROGRESS").length;
    const badge = $("ticketsBadge");
    badge.textContent = open;
    badge.hidden = open === 0;
    if (open > _prevTicketCount && _prevTicketCount > 0) {
      addNotif("🎫", "New Ticket", `${open - _prevTicketCount} new ticket(s) opened`,
        () => switchTab("tickets"));
    }
    _prevTicketCount = open;
  } catch(_) {}
}

async function loadApprovalBadge() {
  if (!authToken || !currentUser || currentUser.role === "employee") return;
  try {
    const data = await apiFetch("/api/approvals");
    const badge = $("approvalsBadge");
    badge.textContent = data.length;
    badge.hidden = data.length === 0;
    if (data.length > _prevApprovalCount && _prevApprovalCount > 0) {
      addNotif("⚠️", "New Approval Request", `${data.length} pending approval(s) need attention`,
        () => switchTab("approvals"));
    }
    _prevApprovalCount = data.length;
  } catch(_) {}
}
