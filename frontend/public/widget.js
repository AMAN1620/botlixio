/**
 * Botlixio Widget — self-contained chat widget
 * Usage: Set window.BotlixioAgentId and window.BotlixioApiUrl before loading this script.
 *
 * <script>
 *   window.BotlixioAgentId = "YOUR_AGENT_ID";
 *   window.BotlixioApiUrl  = "https://your-api.botlixio.com";
 * </script>
 * <script src="https://your-domain.com/widget.js" async></script>
 */
(function () {
  "use strict";

  var agentId = window.BotlixioAgentId;
  var apiUrl = (window.BotlixioApiUrl || "http://localhost:8000").replace(/\/$/, "");

  if (!agentId) {
    console.warn("[Botlixio] window.BotlixioAgentId is not set.");
    return;
  }

  /* ── State ── */
  var sessionId = localStorage.getItem("btlx_session_" + agentId) || null;
  var primaryColor = "#2513EC";
  var agentName = "Support Bot";
  var isOpen = false;
  var isTyping = false;

  /* ── Styles ── */
  var css = `
    #btlx-btn {
      position: fixed; bottom: 24px; right: 24px; z-index: 99999;
      width: 56px; height: 56px; border-radius: 50%; border: none;
      background: var(--btlx-color); color: #fff; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 4px 20px rgba(0,0,0,0.18); transition: transform 0.2s;
    }
    #btlx-btn:hover { transform: scale(1.08); }
    #btlx-panel {
      position: fixed; bottom: 92px; right: 24px; z-index: 99998;
      width: 360px; max-height: 520px; background: #fff;
      border-radius: 16px; box-shadow: 0 8px 40px rgba(0,0,0,0.15);
      display: flex; flex-direction: column; overflow: hidden;
      transition: opacity 0.2s, transform 0.2s;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    #btlx-panel.btlx-hidden { opacity: 0; pointer-events: none; transform: translateY(12px); }
    #btlx-header {
      background: var(--btlx-color); padding: 16px; color: #fff;
      display: flex; align-items: center; gap: 10px;
    }
    #btlx-avatar {
      width: 36px; height: 36px; border-radius: 50%;
      background: rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center;
    }
    #btlx-header-name { font-weight: 700; font-size: 15px; }
    #btlx-header-status { font-size: 12px; opacity: 0.85; display: flex; align-items: center; gap: 4px; }
    #btlx-dot { width: 8px; height: 8px; background: #4ade80; border-radius: 50%; }
    #btlx-messages {
      flex: 1; overflow-y: auto; padding: 16px;
      display: flex; flex-direction: column; gap: 10px;
      scroll-behavior: smooth;
    }
    .btlx-msg {
      max-width: 80%; padding: 10px 14px; border-radius: 18px;
      font-size: 14px; line-height: 1.5; word-break: break-word;
    }
    .btlx-msg-bot { align-self: flex-start; background: #f1f5f9; color: #1e293b; border-bottom-left-radius: 4px; }
    .btlx-msg-user { align-self: flex-end; background: var(--btlx-color); color: #fff; border-bottom-right-radius: 4px; }
    .btlx-typing { align-self: flex-start; background: #f1f5f9; padding: 10px 16px; border-radius: 18px; border-bottom-left-radius: 4px; }
    .btlx-typing span { display: inline-block; width: 8px; height: 8px; background: #94a3b8; border-radius: 50%; margin: 0 2px; animation: btlx-bounce 1.2s infinite; }
    .btlx-typing span:nth-child(2) { animation-delay: 0.2s; }
    .btlx-typing span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes btlx-bounce { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-6px)} }
    #btlx-footer { padding: 12px; border-top: 1px solid #e2e8f0; display: flex; gap: 8px; }
    #btlx-input {
      flex: 1; border: 1.5px solid #e2e8f0; border-radius: 10px;
      padding: 9px 12px; font-size: 14px; outline: none;
      font-family: inherit; resize: none; line-height: 1.4;
    }
    #btlx-input:focus { border-color: var(--btlx-color); }
    #btlx-send {
      width: 40px; height: 40px; border-radius: 10px; border: none;
      background: var(--btlx-color); color: #fff; cursor: pointer;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    #btlx-send:disabled { opacity: 0.5; cursor: not-allowed; }
    @media (max-width: 480px) {
      #btlx-panel { width: calc(100vw - 16px); right: 8px; bottom: 80px; }
    }
  `;

  /* ── DOM helpers ── */
  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) Object.entries(attrs).forEach(function (kv) {
      if (kv[0] === "style") node.style.cssText = kv[1];
      else if (kv[0] === "class") node.className = kv[1];
      else node.setAttribute(kv[0], kv[1]);
    });
    (children || []).forEach(function (c) {
      node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return node;
  }

  /* ── Build UI ── */
  function buildUI() {
    var style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);

    /* Panel */
    var panel = el("div", { id: "btlx-panel", "class": "btlx-hidden" });
    var header = el("div", { id: "btlx-header" }, [
      el("div", { id: "btlx-avatar" }, [svgBot()]),
      el("div", {}, [
        el("div", { id: "btlx-header-name" }, [agentName]),
        el("div", { id: "btlx-header-status" }, [
          el("div", { id: "btlx-dot" }),
          document.createTextNode("Online"),
        ]),
      ]),
    ]);
    var msgs = el("div", { id: "btlx-messages" });
    var footer = el("div", { id: "btlx-footer" });
    var input = el("input", { id: "btlx-input", type: "text", placeholder: "Type a message…" });
    var send = el("button", { id: "btlx-send" }, [svgSend()]);

    footer.appendChild(input);
    footer.appendChild(send);
    panel.appendChild(header);
    panel.appendChild(msgs);
    panel.appendChild(footer);

    /* Toggle button */
    var btn = el("button", { id: "btlx-btn" }, [svgChat()]);

    document.body.appendChild(panel);
    document.body.appendChild(btn);

    /* Set CSS variable */
    document.documentElement.style.setProperty("--btlx-color", primaryColor);

    /* Events */
    btn.addEventListener("click", togglePanel);
    send.addEventListener("click", sendMessage);
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });

    return { panel: panel, msgs: msgs, input: input, send: send };
  }

  /* ── Icons ── */
  function svgChat() {
    var s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    s.setAttribute("width", "26"); s.setAttribute("height", "26");
    s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("fill", "none");
    s.setAttribute("stroke", "currentColor"); s.setAttribute("stroke-width", "2");
    s.setAttribute("stroke-linecap", "round"); s.setAttribute("stroke-linejoin", "round");
    s.innerHTML = '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>';
    return s;
  }
  function svgBot() {
    var s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    s.setAttribute("width", "20"); s.setAttribute("height", "20");
    s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("fill", "none");
    s.setAttribute("stroke", "white"); s.setAttribute("stroke-width", "2");
    s.setAttribute("stroke-linecap", "round"); s.setAttribute("stroke-linejoin", "round");
    s.innerHTML = '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>';
    return s;
  }
  function svgSend() {
    var s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    s.setAttribute("width", "18"); s.setAttribute("height", "18");
    s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("fill", "none");
    s.setAttribute("stroke", "white"); s.setAttribute("stroke-width", "2");
    s.setAttribute("stroke-linecap", "round"); s.setAttribute("stroke-linejoin", "round");
    s.innerHTML = '<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>';
    return s;
  }

  /* ── Logic ── */
  var ui;

  function togglePanel() {
    isOpen = !isOpen;
    ui.panel.classList.toggle("btlx-hidden", !isOpen);
    if (isOpen) ui.input.focus();
  }

  function addMessage(text, role) {
    var div = el("div", { "class": "btlx-msg " + (role === "user" ? "btlx-msg-user" : "btlx-msg-bot") }, [text]);
    ui.msgs.appendChild(div);
    ui.msgs.scrollTop = ui.msgs.scrollHeight;
  }

  function showTyping() {
    var div = el("div", { "class": "btlx-typing", id: "btlx-typing-indicator" }, [
      el("span"), el("span"), el("span"),
    ]);
    ui.msgs.appendChild(div);
    ui.msgs.scrollTop = ui.msgs.scrollHeight;
  }

  function hideTyping() {
    var ind = document.getElementById("btlx-typing-indicator");
    if (ind) ind.parentNode.removeChild(ind);
  }

  async function sendMessage() {
    var text = ui.input.value.trim();
    if (!text || isTyping) return;
    ui.input.value = "";
    addMessage(text, "user");
    isTyping = true;
    ui.send.disabled = true;
    showTyping();

    try {
      var resp = await fetch(apiUrl + "/api/v1/widget/" + agentId + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });
      var data = await resp.json();
      hideTyping();
      if (data.session_id) {
        sessionId = data.session_id;
        localStorage.setItem("btlx_session_" + agentId, sessionId);
      }
      addMessage(data.reply || "Sorry, something went wrong.", "bot");
    } catch (e) {
      hideTyping();
      addMessage("Connection error. Please try again.", "bot");
    } finally {
      isTyping = false;
      ui.send.disabled = false;
      ui.input.focus();
    }
  }

  async function init() {
    try {
      var resp = await fetch(apiUrl + "/api/v1/widget/" + agentId + "/status");
      if (!resp.ok) return;
      var data = await resp.json();
      if (!data.is_live) return; // Don't render widget for non-live agents
      agentName = data.name || agentName;
      primaryColor = data.primary_color || primaryColor;

      ui = buildUI();

      // Show welcome message
      addMessage(data.welcome_message || "Hi! How can I help you?", "bot");

      // Update header name
      var nameEl = document.getElementById("btlx-header-name");
      if (nameEl) nameEl.textContent = agentName;

      // Update color
      document.documentElement.style.setProperty("--btlx-color", primaryColor);
    } catch (e) {
      console.warn("[Botlixio] Could not load agent:", e.message);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
