const chatContainer = document.getElementById("chat-container");
const messagesDiv = document.getElementById("messages");
const welcomeDiv = document.getElementById("welcome");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const statusDot = document.querySelector(".status-dot");
const statusText = document.querySelector(".status-text");
const modelDropdown = document.getElementById("model-dropdown");
const modelToggle = document.getElementById("model-toggle");
const modelNameEl = document.getElementById("model-name");
const modelMenu = document.getElementById("model-menu");

let isGenerating = false;
let selectedModel = null;
let thinkingEnabled = true;
let currentModelThinks = false;

// --- Debug panel ---
const debugPanel = document.getElementById("debug-panel");
const debugToggle = document.getElementById("debug-toggle");
const debugHeader = document.querySelector(".debug-header");
const debugState = document.getElementById("debug-state");
const debugLog = document.getElementById("debug-log");

const dbg = {
  model: document.getElementById("dbg-model"),
  elapsed: document.getElementById("dbg-elapsed"),
  phase: document.getElementById("dbg-phase"),
  speed: document.getElementById("dbg-speed"),
  promptTokens: document.getElementById("dbg-prompt-tokens"),
  thinkingTokens: document.getElementById("dbg-thinking-tokens"),
  responseTokens: document.getElementById("dbg-response-tokens"),
  barPrompt: document.getElementById("dbg-bar-prompt"),
  barThinking: document.getElementById("dbg-bar-thinking"),
  barResponse: document.getElementById("dbg-bar-response"),
  tLoad: document.getElementById("dbg-t-load"),
  tPrompt: document.getElementById("dbg-t-prompt"),
  tGen: document.getElementById("dbg-t-gen"),
  tTotal: document.getElementById("dbg-t-total"),
};

let debugTimer = null;
let debugStartTime = 0;
let debugThinkingCount = 0;
let debugResponseCount = 0;

debugToggle.addEventListener("click", () => {
  debugPanel.classList.remove("collapsed");
});

debugHeader.addEventListener("click", () => {
  debugPanel.classList.add("collapsed");
});

function setDebugState(state, label) {
  debugState.className = "debug-state " + state;
  debugState.querySelector(".debug-state-text").textContent = label;
  dbg.phase.textContent = label;
}

function debugLogEntry(type, msg) {
  const el = document.createElement("div");
  el.className = "debug-log-entry log-" + type;
  const now = new Date();
  const ts = [now.getHours(), now.getMinutes(), now.getSeconds()]
    .map((n) => String(n).padStart(2, "0")).join(":");
  el.innerHTML = `<span class="log-time">${ts}</span><span class="log-msg">${msg}</span>`;
  debugLog.appendChild(el);
  debugLog.scrollTop = debugLog.scrollHeight;
  // Keep max 30 entries
  while (debugLog.children.length > 30) debugLog.removeChild(debugLog.firstChild);
}

function startDebugTimer() {
  debugStartTime = performance.now();
  debugThinkingCount = 0;
  debugResponseCount = 0;
  dbg.thinkingTokens.textContent = "0";
  dbg.responseTokens.textContent = "0";
  dbg.promptTokens.textContent = "--";
  dbg.speed.textContent = "-- t/s";
  dbg.tLoad.textContent = "--";
  dbg.tPrompt.textContent = "--";
  dbg.tGen.textContent = "--";
  dbg.tTotal.textContent = "--";
  dbg.barPrompt.style.width = "0%";
  dbg.barThinking.style.width = "0%";
  dbg.barResponse.style.width = "0%";
  clearInterval(debugTimer);
  debugTimer = setInterval(() => {
    const s = (performance.now() - debugStartTime) / 1000;
    dbg.elapsed.textContent = s < 60 ? s.toFixed(1) + "s" : Math.floor(s / 60) + "m " + (s % 60).toFixed(0) + "s";
    // Live speed
    const totalTokens = debugThinkingCount + debugResponseCount;
    if (totalTokens > 0 && s > 0) {
      dbg.speed.textContent = (totalTokens / s).toFixed(1) + " t/s";
    }
  }, 100);
}

function stopDebugTimer() {
  clearInterval(debugTimer);
  const s = (performance.now() - debugStartTime) / 1000;
  dbg.elapsed.textContent = s.toFixed(1) + "s";
}

function updateDebugBars() {
  const max = Math.max(debugThinkingCount, debugResponseCount, 1);
  dbg.barThinking.style.width = ((debugThinkingCount / max) * 100) + "%";
  dbg.barResponse.style.width = ((debugResponseCount / max) * 100) + "%";
}

function fmtNs(ns) {
  const ms = ns / 1e6;
  if (ms < 1000) return ms.toFixed(0) + " ms";
  return (ms / 1000).toFixed(2) + " s";
}

function applyDebugStats(stats) {
  if (stats.prompt_eval_count != null) {
    dbg.promptTokens.textContent = stats.prompt_eval_count;
    const max = Math.max(stats.prompt_eval_count, debugThinkingCount, debugResponseCount, 1);
    dbg.barPrompt.style.width = ((stats.prompt_eval_count / max) * 100) + "%";
    dbg.barThinking.style.width = ((debugThinkingCount / max) * 100) + "%";
    dbg.barResponse.style.width = ((debugResponseCount / max) * 100) + "%";
  }
  if (stats.eval_count != null && stats.eval_duration != null) {
    const tokPerSec = stats.eval_count / (stats.eval_duration / 1e9);
    dbg.speed.textContent = tokPerSec.toFixed(1) + " t/s";
  }
  if (stats.load_duration != null) dbg.tLoad.textContent = fmtNs(stats.load_duration);
  if (stats.prompt_eval_duration != null) dbg.tPrompt.textContent = fmtNs(stats.prompt_eval_duration);
  if (stats.eval_duration != null) dbg.tGen.textContent = fmtNs(stats.eval_duration);
  if (stats.total_duration != null) dbg.tTotal.textContent = fmtNs(stats.total_duration);
}

// --- Model dropdown ---
let modelList = [];

async function loadModels() {
  try {
    const resp = await fetch("/api/models");
    const data = await resp.json();
    modelList = data.models;
    selectedModel = data.default;
    modelNameEl.textContent = selectedModel;
    const defaultInfo = modelList.find((m) => m.name === selectedModel);
    currentModelThinks = defaultInfo ? defaultInfo.thinks : false;
    renderModelMenu(modelList);
    // Warm up default model on app start
    modelToggle.classList.add("loading");
    setDebugState("thinking", "Cargando modelo...");
    dbg.model.textContent = selectedModel;
    debugLogEntry("info", `Precargando ${selectedModel}...`);
    fetch("/api/models/warmup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: selectedModel }),
    })
      .then(() => {
        modelToggle.classList.remove("loading");
        setDebugState("done", "Modelo listo");
        debugLogEntry("done", `${selectedModel} cargado en memoria`);
      })
      .catch(() => {
        modelToggle.classList.remove("loading");
      });
  } catch {
    modelNameEl.textContent = "Sin modelos";
  }
}

function renderModelMenu(models) {
  modelMenu.innerHTML = "";
  for (const m of models) {
    const btn = document.createElement("button");
    btn.className = "model-option" + (m.name === selectedModel ? " active" : "");
    btn.dataset.model = m.name;
    btn.innerHTML = `
      <div class="model-option-info">
        <span class="model-option-name">${m.name}</span>
        <span class="model-option-size">${m.size}</span>
      </div>
      <svg class="model-option-check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <polyline points="20 6 9 17 4 12"/>
      </svg>`;
    btn.addEventListener("click", () => selectModel(m.name));
    modelMenu.appendChild(btn);
  }
  // Thinking toggle
  renderThinkingToggle();
}

function renderThinkingToggle() {
  let toggle = modelMenu.querySelector(".thinking-toggle-row");
  if (toggle) toggle.remove();

  if (!currentModelThinks) return;

  const row = document.createElement("div");
  row.className = "thinking-toggle-row";
  row.innerHTML = `
    <div class="thinking-toggle-label">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2a7 7 0 0 1 7 7c0 2.4-1.2 4.5-3 5.7V17a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2v-2.3C6.2 13.5 5 11.4 5 9a7 7 0 0 1 7-7z"/>
        <line x1="9" y1="22" x2="15" y2="22"/>
      </svg>
      <span>Thinking</span>
    </div>
    <label class="thinking-switch">
      <input type="checkbox" id="thinking-checkbox" ${thinkingEnabled ? "checked" : ""}>
      <span class="thinking-slider"></span>
    </label>`;
  row.addEventListener("click", (e) => e.stopPropagation());
  row.querySelector("#thinking-checkbox").addEventListener("change", (e) => {
    thinkingEnabled = e.target.checked;
    debugLogEntry("info", `Thinking ${thinkingEnabled ? "activado" : "desactivado"}`);
  });
  modelMenu.prepend(row);
}

function selectModel(model) {
  selectedModel = model;
  modelNameEl.textContent = model;
  const info = modelList.find((m) => m.name === model);
  currentModelThinks = info ? info.thinks : false;
  modelDropdown.classList.remove("open");
  modelMenu.querySelectorAll(".model-option").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.model === model);
  });
  renderThinkingToggle();
  // Warm up: pre-load model into memory
  modelToggle.classList.add("loading");
  setDebugState("thinking", "Cargando modelo...");
  debugLogEntry("info", `Precargando ${model}...`);
  fetch("/api/models/warmup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model }),
  })
    .then(() => {
      modelToggle.classList.remove("loading");
      setDebugState("done", "Modelo listo");
      debugLogEntry("done", `${model} cargado en memoria`);
    })
    .catch(() => {
      modelToggle.classList.remove("loading");
      setDebugState("error", "Error de carga");
    });
  dbg.model.textContent = model;
}

modelToggle.addEventListener("click", () => {
  modelDropdown.classList.toggle("open");
});

document.addEventListener("click", (e) => {
  if (!modelDropdown.contains(e.target)) {
    modelDropdown.classList.remove("open");
  }
});

// --- Health check ---
async function checkHealth() {
  try {
    const resp = await fetch("/api/health");
    const data = await resp.json();
    if (data.ollama) {
      statusDot.className = "status-dot online";
      statusText.textContent = "En línea";
    } else {
      statusDot.className = "status-dot offline";
      statusText.textContent = "Ollama no disponible";
    }
  } catch {
    statusDot.className = "status-dot offline";
    statusText.textContent = "Sin conexión";
  }
}

// --- Message rendering ---
function formatText(text) {
  if (!text) return "";
  let formatted = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");

  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
  formatted = formatted.replace(/\n/g, '<br>');

  return formatted;
}

function addMessage(text, role) {
  welcomeDiv.style.display = "none";

  const msg = document.createElement("div");
  msg.className = `message message-${role}`;

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.innerHTML = formatText(text);

  msg.appendChild(bubble);
  messagesDiv.appendChild(msg);
  scrollToBottom();
  return bubble;
}

function addTypingIndicator() {
  welcomeDiv.style.display = "none";

  const msg = document.createElement("div");
  msg.className = "message message-assistant";
  msg.id = "typing-msg";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";

  const indicator = document.createElement("div");
  indicator.className = "typing-indicator";
  indicator.innerHTML = "<span></span><span></span><span></span>";

  bubble.appendChild(indicator);
  msg.appendChild(bubble);
  messagesDiv.appendChild(msg);
  scrollToBottom();
  return bubble;
}

function removeTypingIndicator() {
  const el = document.getElementById("typing-msg");
  if (el) el.remove();
}

function scrollToBottom() {
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

// --- Streaming chat ---
async function sendMessage(text) {
  if (!text.trim() || isGenerating) return;

  isGenerating = true;
  sendBtn.disabled = true;
  messageInput.disabled = true;

  // User message
  addMessage(text, "user");

  // Debug: start
  dbg.model.textContent = selectedModel || "default";
  setDebugState("thinking", "Enviando...");
  startDebugTimer();
  debugLogEntry("info", `Petición → ${selectedModel || "default"}`);

  // Typing indicator
  const typingBubble = addTypingIndicator();

  try {
    const useThinking = currentModelThinks && thinkingEnabled;
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, model: selectedModel, think: useThinking }),
    });

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

    setDebugState("thinking", "Procesando prompt...");
    debugLogEntry("info", "Conexión establecida, esperando tokens...");

    // Remove typing, add empty assistant bubble
    removeTypingIndicator();
    const assistantBubble = addMessage("", "assistant");

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let fullThinking = "";
    let fullResponse = "";
    let thinkingEl = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop(); // keep incomplete line

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const jsonStr = line.slice(6);
        try {
          const data = JSON.parse(jsonStr);
          if (data.type === "thinking" && data.token) {
            if (!thinkingEl) {
              thinkingEl = document.createElement("details");
              thinkingEl.className = "thinking-block";
              thinkingEl.open = true;
              thinkingEl.innerHTML = '<summary>Pensando...</summary><div class="thinking-content"></div>';
              assistantBubble.appendChild(thinkingEl);
              setDebugState("thinking", "Pensando");
              debugLogEntry("thinking", "Fase de razonamiento iniciada");
            }
            fullThinking += data.token;
            debugThinkingCount++;
            dbg.thinkingTokens.textContent = debugThinkingCount;
            updateDebugBars();
            thinkingEl.querySelector(".thinking-content").innerHTML = formatText(fullThinking);
            scrollToBottom();
          }
          if (data.type === "response" && data.token) {
            if (thinkingEl && !assistantBubble.querySelector(".response-text")) {
              thinkingEl.open = false;
              const responseEl = document.createElement("div");
              responseEl.className = "response-text";
              assistantBubble.appendChild(responseEl);
              setDebugState("generating", "Generando");
              debugLogEntry("response", `Pensamiento completo (${debugThinkingCount} tokens)`);
            }
            if (!thinkingEl && debugResponseCount === 0) {
              setDebugState("generating", "Generando");
              debugLogEntry("response", "Generando respuesta");
            }
            fullResponse += data.token;
            debugResponseCount++;
            dbg.responseTokens.textContent = debugResponseCount;
            updateDebugBars();
            const target = assistantBubble.querySelector(".response-text") || assistantBubble;
            target.innerHTML = formatText(fullResponse);
            scrollToBottom();
          }
          if (data.type === "stats") {
            applyDebugStats(data.stats);
            debugLogEntry("done", `Finalizado — ${(data.stats.eval_count || 0)} tokens generados`);
          }
          if (data.error) {
            assistantBubble.innerHTML = formatText(`Error: ${data.error}`);
            setDebugState("error", "Error");
            debugLogEntry("error", data.error);
          }
        } catch {
          // skip malformed JSON
        }
      }
    }

    if (!fullResponse && !fullThinking) {
      assistantBubble.innerHTML = formatText(
        "No he podido generar una respuesta. Comprueba que Ollama está funcionando."
      );
      setDebugState("error", "Sin respuesta");
    } else {
      setDebugState("done", "Completado");
    }
    stopDebugTimer();
  } catch (err) {
    removeTypingIndicator();
    addMessage(
      `Error de conexión: ${err.message}. Comprueba que el servidor está funcionando.`,
      "assistant"
    );
    setDebugState("error", "Error");
    stopDebugTimer();
    debugLogEntry("error", err.message);
  } finally {
    isGenerating = false;
    sendBtn.disabled = false;
    messageInput.disabled = false;
    messageInput.focus();
    updateSendBtn();
  }
}

// --- Auto-resize textarea ---
function autoResize() {
  messageInput.style.height = "auto";
  messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + "px";
}

function updateSendBtn() {
  sendBtn.disabled = !messageInput.value.trim() || isGenerating;
}

// --- Events ---
chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = messageInput.value.trim();
  if (text) {
    messageInput.value = "";
    autoResize();
    sendMessage(text);
  }
});

messageInput.addEventListener("input", () => {
  autoResize();
  updateSendBtn();
});

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event("submit"));
  }
});

// Suggestion buttons
document.querySelectorAll(".suggestion-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const question = btn.dataset.question;
    sendMessage(question);
  });
});

// --- Init ---
loadModels();
checkHealth();
setInterval(checkHealth, 30000);
messageInput.focus();
