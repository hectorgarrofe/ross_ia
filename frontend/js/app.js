const chatContainer = document.getElementById("chat-container");
const messagesDiv = document.getElementById("messages");
const welcomeDiv = document.getElementById("welcome");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const statusDot = document.querySelector(".status-dot");
const statusText = document.querySelector(".status-text");

let isGenerating = false;

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
function addMessage(text, role) {
  welcomeDiv.style.display = "none";

  const msg = document.createElement("div");
  msg.className = `message message-${role}`;

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = text;

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

  // Typing indicator
  const typingBubble = addTypingIndicator();

  try {
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

    // Remove typing, add empty assistant bubble
    removeTypingIndicator();
    const assistantBubble = addMessage("", "assistant");

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let fullResponse = "";

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
          if (data.token) {
            fullResponse += data.token;
            assistantBubble.textContent = fullResponse;
            scrollToBottom();
          }
          if (data.error) {
            assistantBubble.textContent = `Error: ${data.error}`;
          }
        } catch {
          // skip malformed JSON
        }
      }
    }

    if (!fullResponse) {
      assistantBubble.textContent =
        "No he podido generar una respuesta. Comprueba que Ollama está funcionando.";
    }
  } catch (err) {
    removeTypingIndicator();
    addMessage(
      `Error de conexión: ${err.message}. Comprueba que el servidor está funcionando.`,
      "assistant"
    );
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
checkHealth();
setInterval(checkHealth, 30000);
messageInput.focus();
