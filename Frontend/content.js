(() => {
  if (document.getElementById("ai-scraper-root")) return;

  /* ROOT */
  const root = document.createElement("div");
  root.id = "ai-scraper-root";

  Object.assign(root.style, {
    position: "fixed",
    top: "0",
    right: "0",
    height: "100vh",
    width: "400px",
    zIndex: "2147483647",
    transition: "width 0.25s ease",
    pointerEvents: "auto",
    background: "transparent"
  });

  document.body.appendChild(root);

  /* SHADOW */
  const shadow = root.attachShadow({ mode: "open" });

  /* STYLES */
  const style = document.createElement("style");
  style.textContent = `
    * { box-sizing: border-box; }

    .panel {
      height: 100%;
      background: #0F0F0F;
      color: #EDEDED;
      display: flex;
      flex-direction: column;
      box-shadow: -4px 0 16px rgba(0,0,0,0.4);
      overflow: hidden;
    }

    .header {
      height: 56px;
      padding: 0 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-weight: 600;
      border-bottom: 1px solid #2A2A2A;
      background: #0F0F0F;
      flex-shrink: 0;
    }

    .toggle {
      width: 28px;
      height: 28px;
      border-radius: 6px;
      border: none;
      cursor: pointer;
      background: #1DB954;
      font-weight: bold;
    }

    .body {
      flex: 1;
      display: flex;
      flex-direction: column;
    }

    .chat {
      flex: 1;
      padding: 12px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .msg.user {
      align-self: flex-end;
      background: #1DB954;
      color: #000;
      padding: 10px 12px;
      border-radius: 12px;
      max-width: 80%;
      font-size: 0.9rem;
    }

    .msg.bot {
      align-self: flex-start;
      background: #1e1e1e;
      color: #ededed;
      padding: 10px 12px;
      border-radius: 12px;
      max-width: 80%;
      font-size: 0.9rem;
      white-space: pre-wrap;
    }

    .input {
      display: flex;
      gap: 8px;
      padding: 12px;
      border-top: 1px solid #2A2A2A;
    }

    input {
      flex: 1;
      padding: 8px 10px;
      border-radius: 20px;
      border: none;
      outline: none;
    }

    .send {
      width: 38px;
      height: 38px;
      border-radius: 50%;
      border: none;
      background: #1DB954;
      cursor: pointer;
    }

    .collapsed {
      width: 48px;
    }

    .collapsed .body {
      display: none;
    }

    .collapsed .header span {
      display: none;
    }

    .collapsed .header {
      justify-content: center;
    }
  `;

  /* HTML */
  const panel = document.createElement("div");
  panel.className = "panel";
  panel.innerHTML = `
    <div class="header">
      <span>AI SCRAPER</span>
      <button class="toggle" id="toggle">‹</button>
    </div>

    <div class="body">
      <div class="chat" id="chat"></div>
      <div class="input">
        <input id="query" placeholder="What do you want to scrape?" />
        <button class="send" id="send">➤</button>
      </div>
    </div>
  `;

  shadow.appendChild(style);
  shadow.appendChild(panel);

  const toggle = shadow.getElementById("toggle");
  const input = shadow.getElementById("query");
  const send = shadow.getElementById("send");
  const chat = shadow.getElementById("chat");

  let collapsed = false;

  toggle.onclick = () => {
    collapsed = !collapsed;
    if (collapsed) {
      root.style.width = "48px";
      panel.classList.add("collapsed");
      toggle.textContent = "›";
    } else {
      root.style.width = "400px";
      panel.classList.remove("collapsed");
      toggle.textContent = "‹";
    }
  };

  function addBotMessage(text) {
    const msg = document.createElement("div");
    msg.className = "msg bot";
    msg.textContent = text;
    chat.appendChild(msg);
    chat.scrollTop = chat.scrollHeight;
  }

  const port = chrome.runtime.connect({ name: "ai-scraper-ui" });

  port.onMessage.addListener((response) => {
    if (response.success) {
      addBotMessage(
        response.data?.summary ||
        JSON.stringify(response.data?.records || response.data, null, 2)
      );
    } else {
      addBotMessage("❌ Error: " + response.error);
    }
  });

  function handleSend() {
    const text = input.value.trim();
    if (!text) return;

    const msg = document.createElement("div");
    msg.className = "msg user";
    msg.textContent = text;
    chat.appendChild(msg);
    chat.scrollTop = chat.scrollHeight;

    port.postMessage({
      type: "USER_SCRAPE_REQUEST",
      payload: {
        URL: window.location.href,
        UserPrompt: text
      }
    });

    input.value = "";
  }

  send.onclick = handleSend;

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSend();
    }
  });
})();
