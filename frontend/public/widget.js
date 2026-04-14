/**
 * Botlixio Chat Widget v2
 * Embeddable self-contained chat widget — no external dependencies.
 *
 * Usage:
 *   <script
 *     src="https://your-domain.com/widget.js"
 *     data-agent-id="abc123"
 *     data-api-url="https://api.botlixio.com"
 *     data-theme="light"
 *     data-position="bottom-right">
 *   </script>
 */
(function () {
  "use strict";

  /* ── Read script attributes (must happen synchronously before any async code) ── */
  var currentScript = document.currentScript;
  var agentId    = currentScript && currentScript.getAttribute("data-agent-id");
  var apiUrl     = ((currentScript && currentScript.getAttribute("data-api-url")) || "http://localhost:8000").replace(/\/$/, "");
  var theme      = (currentScript && currentScript.getAttribute("data-theme")) || "light";
  var position   = (currentScript && currentScript.getAttribute("data-position")) || "bottom-right";

  if (!agentId) {
    console.warn("[Botlixio] data-agent-id attribute is required.");
    return;
  }

  /* ── State ── */
  var sessionId    = null;
  var primaryColor = "#2513EC";
  var agentName    = "Support Bot";
  var isOpen       = false;
  var isFlying     = false; // request in flight
  var welcomeShown = false;
  var ui           = null;

  /* ── UUID v4 generator ── */
  function uuidv4() {
    if (typeof crypto !== "undefined" && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      var r = (Math.random() * 16) | 0;
      var v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  /* ── Session helpers ── */
  function getOrCreateSession() {
    var key = "btlx_session_" + agentId;
    var stored = null;
    try { stored = localStorage.getItem(key); } catch (e) {}
    if (!stored) {
      stored = uuidv4();
      try { localStorage.setItem(key, stored); } catch (e) {}
    }
    return stored;
  }

  /* ── Theme tokens ── */
  var THEMES = {
    light: {
      bg:          "#ffffff",
      surface:     "#f1f5f9",
      border:      "#e2e8f0",
      text:        "#1e293b",
      textMuted:   "#64748b",
      inputBg:     "#ffffff",
      bubbleBot:   "#f1f5f9",
      bubbleBotTxt:"#1e293b",
    },
    dark: {
      bg:          "#1e1e2e",
      surface:     "#2a2a3e",
      border:      "#3a3a50",
      text:        "#e2e8f0",
      textMuted:   "#94a3b8",
      inputBg:     "#2a2a3e",
      bubbleBot:   "#2a2a3e",
      bubbleBotTxt:"#e2e8f0",
    },
  };

  function tok(name) {
    return "var(--btlx-" + name + ")";
  }

  /* ── CSS injection ── */
  function buildCSS(pos) {
    var isRight = pos !== "bottom-left";
    var side    = isRight ? "right" : "left";
    return [
      /* Reset scope */
      "#btlx-btn, #btlx-panel, #btlx-panel * {",
      "  box-sizing: border-box; margin: 0; padding: 0;",
      "}",

      /* Launcher button */
      "#btlx-btn {",
      "  position: fixed; bottom: 24px; " + side + ": 24px; z-index: 2147483647;",
      "  width: 56px; height: 56px; border-radius: 50%; border: none;",
      "  background: " + tok("accent") + "; color: #fff; cursor: pointer;",
      "  display: flex; align-items: center; justify-content: center;",
      "  box-shadow: 0 4px 24px rgba(0,0,0,0.22);",
      "  transition: transform 0.2s, box-shadow 0.2s;",
      "  outline: none;",
      "}",
      "#btlx-btn:hover { transform: scale(1.08); box-shadow: 0 6px 28px rgba(0,0,0,0.28); }",
      "#btlx-btn:focus-visible { outline: 3px solid " + tok("accent") + "; outline-offset: 3px; }",

      /* Panel */
      "#btlx-panel {",
      "  position: fixed; bottom: 92px; " + side + ": 24px; z-index: 2147483646;",
      "  width: 360px; height: 520px;",
      "  background: " + tok("bg") + ";",
      "  border: 1px solid " + tok("border") + ";",
      "  border-radius: 16px;",
      "  box-shadow: 0 8px 48px rgba(0,0,0,0.18);",
      "  display: flex; flex-direction: column; overflow: hidden;",
      "  transition: opacity 0.22s ease, transform 0.22s ease;",
      "  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;",
      "  font-size: 14px; line-height: 1.5;",
      "  color: " + tok("text") + ";",
      "}",
      "#btlx-panel.btlx-hidden {",
      "  opacity: 0; pointer-events: none; transform: translateY(14px);",
      "}",

      /* Header */
      "#btlx-header {",
      "  background: " + tok("accent") + "; padding: 14px 16px;",
      "  display: flex; align-items: center; gap: 10px; flex-shrink: 0;",
      "}",
      "#btlx-avatar {",
      "  width: 38px; height: 38px; border-radius: 50%;",
      "  background: rgba(255,255,255,0.2);",
      "  display: flex; align-items: center; justify-content: center; flex-shrink: 0;",
      "}",
      "#btlx-header-info { flex: 1; overflow: hidden; }",
      "#btlx-header-name {",
      "  font-weight: 700; font-size: 15px; color: #fff;",
      "  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;",
      "}",
      "#btlx-header-status {",
      "  font-size: 12px; color: rgba(255,255,255,0.85);",
      "  display: flex; align-items: center; gap: 5px; margin-top: 1px;",
      "}",
      "#btlx-online-dot {",
      "  width: 7px; height: 7px; background: #4ade80; border-radius: 50%; flex-shrink: 0;",
      "}",
      "#btlx-close {",
      "  background: rgba(255,255,255,0.15); border: none; cursor: pointer;",
      "  color: #fff; border-radius: 8px; width: 30px; height: 30px;",
      "  display: flex; align-items: center; justify-content: center;",
      "  flex-shrink: 0; transition: background 0.15s;",
      "}",
      "#btlx-close:hover { background: rgba(255,255,255,0.28); }",

      /* Messages area */
      "#btlx-messages {",
      "  flex: 1; overflow-y: auto; padding: 14px 16px;",
      "  display: flex; flex-direction: column; gap: 10px;",
      "  scroll-behavior: smooth;",
      "  background: " + tok("bg") + ";",
      "}",
      "#btlx-messages::-webkit-scrollbar { width: 4px; }",
      "#btlx-messages::-webkit-scrollbar-track { background: transparent; }",
      "#btlx-messages::-webkit-scrollbar-thumb { background: " + tok("border") + "; border-radius: 4px; }",

      /* Message bubbles */
      ".btlx-msg-wrap { display: flex; flex-direction: column; }",
      ".btlx-msg-wrap.btlx-user { align-items: flex-end; }",
      ".btlx-msg-wrap.btlx-bot  { align-items: flex-start; }",
      ".btlx-bubble {",
      "  max-width: 80%; padding: 10px 14px; border-radius: 18px;",
      "  font-size: 14px; line-height: 1.55; word-break: break-word;",
      "}",
      ".btlx-bot  .btlx-bubble {",
      "  background: " + tok("bubbleBot") + ";",
      "  color: " + tok("bubbleBotTxt") + ";",
      "  border-bottom-left-radius: 4px;",
      "}",
      ".btlx-user .btlx-bubble {",
      "  background: " + tok("accent") + ";",
      "  color: #fff; border-bottom-right-radius: 4px;",
      "}",

      /* Sources */
      ".btlx-sources {",
      "  display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; max-width: 80%;",
      "}",
      ".btlx-source-link {",
      "  font-size: 11px; color: " + tok("textMuted") + ";",
      "  background: " + tok("surface") + ";",
      "  border: 1px solid " + tok("border") + ";",
      "  border-radius: 6px; padding: 3px 8px;",
      "  text-decoration: none; white-space: nowrap;",
      "  overflow: hidden; text-overflow: ellipsis; max-width: 160px;",
      "  transition: background 0.15s;",
      "}",
      ".btlx-source-link:hover { background: " + tok("border") + "; }",

      /* Typing indicator */
      ".btlx-typing {",
      "  align-self: flex-start; background: " + tok("bubbleBot") + ";",
      "  padding: 12px 16px; border-radius: 18px; border-bottom-left-radius: 4px;",
      "  display: flex; align-items: center; gap: 4px;",
      "}",
      ".btlx-typing span {",
      "  display: inline-block; width: 7px; height: 7px;",
      "  background: " + tok("textMuted") + "; border-radius: 50%;",
      "  animation: btlx-bounce 1.2s infinite ease-in-out;",
      "}",
      ".btlx-typing span:nth-child(2) { animation-delay: 0.2s; }",
      ".btlx-typing span:nth-child(3) { animation-delay: 0.4s; }",
      "@keyframes btlx-bounce {",
      "  0%, 60%, 100% { transform: translateY(0); }",
      "  30% { transform: translateY(-6px); }",
      "}",

      /* Error bubble */
      ".btlx-error .btlx-bubble {",
      "  background: #fee2e2; color: #991b1b; border-bottom-left-radius: 4px;",
      "}",

      /* Footer / input row */
      "#btlx-footer {",
      "  padding: 10px 12px; border-top: 1px solid " + tok("border") + ";",
      "  display: flex; gap: 8px; align-items: flex-end; flex-shrink: 0;",
      "  background: " + tok("bg") + ";",
      "}",
      "#btlx-input {",
      "  flex: 1; border: 1.5px solid " + tok("border") + ";",
      "  border-radius: 10px; padding: 9px 12px;",
      "  font-size: 14px; font-family: inherit;",
      "  resize: none; outline: none; line-height: 1.4;",
      "  background: " + tok("inputBg") + "; color: " + tok("text") + ";",
      "  max-height: 100px; overflow-y: auto;",
      "  transition: border-color 0.15s;",
      "}",
      "#btlx-input:focus { border-color: " + tok("accent") + "; }",
      "#btlx-input::placeholder { color: " + tok("textMuted") + "; }",
      "#btlx-send {",
      "  width: 38px; height: 38px; border-radius: 10px; border: none;",
      "  background: " + tok("accent") + "; color: #fff; cursor: pointer;",
      "  display: flex; align-items: center; justify-content: center;",
      "  flex-shrink: 0; transition: opacity 0.15s;",
      "}",
      "#btlx-send:disabled { opacity: 0.45; cursor: not-allowed; }",
      "#btlx-send:not(:disabled):hover { opacity: 0.88; }",

      /* Responsive */
      "@media (max-width: 480px) {",
      "  #btlx-panel { width: calc(100vw - 16px); " + side + ": 8px; bottom: 80px; height: 460px; }",
      "  #btlx-btn   { bottom: 16px; " + side + ": 16px; }",
      "}",
    ].join("\n");
  }

  /* ── SVG icons ── */
  function svgIcon(pathData, size, stroke) {
    var ns = "http://www.w3.org/2000/svg";
    var s = document.createElementNS(ns, "svg");
    s.setAttribute("width",  size || "22");
    s.setAttribute("height", size || "22");
    s.setAttribute("viewBox", "0 0 24 24");
    s.setAttribute("fill", "none");
    s.setAttribute("stroke", stroke || "currentColor");
    s.setAttribute("stroke-width", "2");
    s.setAttribute("stroke-linecap", "round");
    s.setAttribute("stroke-linejoin", "round");
    s.innerHTML = pathData;
    return s;
  }

  var PATH_CHAT  = '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>';
  var PATH_CLOSE = '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>';
  var PATH_SEND  = '<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>';
  var PATH_BOT   = '<rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="7" r="3"/><line x1="8" y1="14" x2="8" y2="14"/><line x1="16" y1="14" x2="16" y2="14"/>';

  /* ── DOM helpers ── */
  function h(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === "className")    node.className = attrs[k];
        else if (k === "style")   node.style.cssText = attrs[k];
        else                      node.setAttribute(k, attrs[k]);
      });
    }
    if (children) {
      children.forEach(function (c) {
        if (!c && c !== 0) return;
        node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
      });
    }
    return node;
  }

  /* ── Build the full widget DOM ── */
  function buildUI() {
    var t = THEMES[theme] || THEMES.light;

    /* Inject CSS variables + stylesheet */
    var vars = [
      ":root {",
      "  --btlx-accent:       " + primaryColor + ";",
      "  --btlx-bg:           " + t.bg + ";",
      "  --btlx-surface:      " + t.surface + ";",
      "  --btlx-border:       " + t.border + ";",
      "  --btlx-text:         " + t.text + ";",
      "  --btlx-textMuted:    " + t.textMuted + ";",
      "  --btlx-inputBg:      " + t.inputBg + ";",
      "  --btlx-bubbleBot:    " + t.bubbleBot + ";",
      "  --btlx-bubbleBotTxt: " + t.bubbleBotTxt + ";",
      "}",
    ].join("\n");

    var style = document.createElement("style");
    style.id  = "btlx-styles";
    style.textContent = vars + "\n" + buildCSS(position);
    document.head.appendChild(style);

    /* Header */
    var headerName   = h("div", { id: "btlx-header-name" }, [agentName]);
    var onlineDot    = h("div", { id: "btlx-online-dot" });
    var headerStatus = h("div", { id: "btlx-header-status" }, [onlineDot, "Online"]);
    var headerInfo   = h("div", { id: "btlx-header-info" }, [headerName, headerStatus]);
    var avatar       = h("div", { id: "btlx-avatar" }, [svgIcon(PATH_BOT, "20", "white")]);
    var closeBtn     = h("button", { id: "btlx-close", "aria-label": "Close chat" }, [svgIcon(PATH_CLOSE, "16", "white")]);
    var header       = h("div", { id: "btlx-header" }, [avatar, headerInfo, closeBtn]);

    /* Messages */
    var msgsArea = h("div", { id: "btlx-messages", role: "log", "aria-live": "polite" });

    /* Footer */
    var input  = h("textarea", {
      id: "btlx-input",
      placeholder: "Type a message…",
      rows: "1",
      "aria-label": "Chat message",
    });
    var sendBtn = h("button", { id: "btlx-send", "aria-label": "Send message" }, [svgIcon(PATH_SEND, "17", "white")]);
    var footer  = h("div", { id: "btlx-footer" }, [input, sendBtn]);

    /* Panel */
    var panel = h("div", { id: "btlx-panel", className: "btlx-hidden", role: "dialog", "aria-label": "Chat with " + agentName }, [header, msgsArea, footer]);

    /* Launcher button */
    var launcher = h("button", { id: "btlx-btn", "aria-label": "Open chat", "aria-expanded": "false" }, [svgIcon(PATH_CHAT, "24", "white")]);

    document.body.appendChild(panel);
    document.body.appendChild(launcher);

    /* Auto-resize textarea */
    input.addEventListener("input", function () {
      input.style.height = "auto";
      input.style.height = Math.min(input.scrollHeight, 96) + "px";
    });

    /* Events */
    launcher.addEventListener("click", function () { togglePanel(panel, launcher, input); });
    closeBtn.addEventListener("click", function () { closePanel(panel, launcher); });
    sendBtn.addEventListener("click", function () { submitMessage(input, sendBtn, msgsArea); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        submitMessage(input, sendBtn, msgsArea);
      }
    });

    return { panel: panel, launcher: launcher, msgs: msgsArea, input: input, send: sendBtn, headerName: headerName };
  }

  /* ── Panel open / close ── */
  function togglePanel(panel, launcher, input) {
    if (isOpen) {
      closePanel(panel, launcher);
    } else {
      openPanel(panel, launcher, input);
    }
  }

  function openPanel(panel, launcher, input) {
    isOpen = true;
    panel.classList.remove("btlx-hidden");
    launcher.setAttribute("aria-expanded", "true");
    launcher.innerHTML = "";
    launcher.appendChild(svgIcon(PATH_CLOSE, "22", "white"));
    if (!welcomeShown && ui && ui.msgs && agentName) {
      var welcome = ui.msgs.dataset.welcome || "Hi! How can I help you today?";
      appendMessage(ui.msgs, welcome, "btlx-bot");
      welcomeShown = true;
    }
    if (input) setTimeout(function () { input.focus(); }, 50);
  }

  function closePanel(panel, launcher) {
    isOpen = false;
    panel.classList.add("btlx-hidden");
    launcher.setAttribute("aria-expanded", "false");
    launcher.innerHTML = "";
    launcher.appendChild(svgIcon(PATH_CHAT, "24", "white"));
  }

  /* ── Scroll to bottom ── */
  function scrollToBottom(msgsArea) {
    msgsArea.scrollTop = msgsArea.scrollHeight;
  }

  /* ── Append a message bubble ── */
  function appendMessage(msgsArea, text, role, isError) {
    var wrapClass = "btlx-msg-wrap " + role + (isError ? " btlx-error" : "");
    var bubble    = h("div", { className: "btlx-bubble" }, [text]);
    var wrap      = h("div", { className: wrapClass }, [bubble]);
    msgsArea.appendChild(wrap);
    scrollToBottom(msgsArea);
    return wrap;
  }

  /* ── Append sources row below a bubble wrap ── */
  function appendSources(wrap, sources) {
    if (!sources || !sources.length) return;
    var links = sources.map(function (src) {
      if (!src || !src.title) return null;
      var a = h("a", {
        href:   src.url || "#",
        target: "_blank",
        rel:    "noopener noreferrer",
        className: "btlx-source-link",
        title:  src.title,
      }, [src.title]);
      return a;
    }).filter(Boolean);

    if (!links.length) return;
    var row = h("div", { className: "btlx-sources" }, links);
    wrap.appendChild(row);
  }

  /* ── Typing indicator ── */
  function showTyping(msgsArea) {
    var indicator = h("div", { id: "btlx-typing", className: "btlx-typing" }, [h("span"), h("span"), h("span")]);
    msgsArea.appendChild(indicator);
    scrollToBottom(msgsArea);
    return indicator;
  }

  function hideTyping() {
    var el = document.getElementById("btlx-typing");
    if (el && el.parentNode) el.parentNode.removeChild(el);
  }

  /* ── Send message ── */
  function submitMessage(input, sendBtn, msgsArea) {
    var text = input.value.trim();
    if (!text || isFlying) return;

    input.value = "";
    input.style.height = "auto";
    isFlying = true;
    sendBtn.disabled = true;
    input.disabled   = true;

    appendMessage(msgsArea, text, "btlx-user");
    showTyping(msgsArea);

    fetch(apiUrl + "/api/v1/widget/" + agentId + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    })
    .then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    })
    .then(function (data) {
      hideTyping();

      /* Persist session ID */
      if (data.session_id) {
        sessionId = data.session_id;
        try { localStorage.setItem("btlx_session_" + agentId, sessionId); } catch (e) {}
      }

      var reply = (data.reply || "").trim() || "Sorry, I didn\u2019t get that. Please try again.";
      var wrap  = appendMessage(msgsArea, reply, "btlx-bot");

      /* Attach sources */
      if (data.sources && data.sources.length) {
        appendSources(wrap, data.sources);
        scrollToBottom(msgsArea);
      }
    })
    .catch(function () {
      hideTyping();
      appendMessage(msgsArea, "Something went wrong. Please try again.", "btlx-bot", true);
    })
    .finally(function () {
      isFlying         = false;
      sendBtn.disabled = false;
      input.disabled   = false;
      input.focus();
    });
  }

  /* ── Initialise: fetch agent status then build UI ── */
  function init() {
    fetch(apiUrl + "/api/v1/widget/" + agentId + "/status")
      .then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.json();
      })
      .then(function (data) {
        /* If agent is not live, render nothing */
        if (!data.is_live) return;

        agentName    = data.name    || agentName;
        primaryColor = data.primary_color || primaryColor;

        /* Load or create session */
        sessionId = getOrCreateSession();

        /* Build DOM */
        ui = buildUI();

        /* Update CSS accent variable in case it differed */
        var styleEl = document.getElementById("btlx-styles");
        if (styleEl) {
          styleEl.textContent = styleEl.textContent.replace(
            /--btlx-accent:\s*[^;]+;/,
            "--btlx-accent: " + primaryColor + ";"
          );
        }

        /* Update header name text */
        if (ui.headerName) ui.headerName.textContent = agentName;

        /* Store welcome message — shown on first panel open */
        var welcome = (data.welcome_message || "").trim() || "Hi! How can I help you today?";
        ui.msgs.dataset.welcome = welcome;
      })
      .catch(function (err) {
        console.warn("[Botlixio] Could not initialise widget:", err && err.message);
      });
  }

  /* ── Boot when DOM is ready ── */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

})();
