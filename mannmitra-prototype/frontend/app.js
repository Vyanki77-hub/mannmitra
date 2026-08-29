// app.js
// Handles: sending messages to the backend, showing replies, voice input (STT),
// voice output (TTS), the crisis banner, and the blue orb voice-only mode.

const BACKEND_URL = "https://mannmitra-backend-hrrh.onrender.com"; // your live backend

const chatWindow = document.getElementById("chat-window");
const textInput = document.getElementById("text-input");
const sendBtn = document.getElementById("send-btn");
const micBtn = document.getElementById("mic-btn");
const crisisBanner = document.getElementById("crisis-banner");
const helplineList = document.getElementById("helpline-list");

// Orb mode elements
const orbToggleBtn = document.getElementById("orb-toggle-btn");
const orbOverlay = document.getElementById("orb-overlay");
const orbCloseBtn = document.getElementById("orb-close-btn");
const orbCircle = document.getElementById("orb-circle");
const orbStatus = document.getElementById("orb-status");
const orbCaption = document.getElementById("orb-caption");

let history = [];

function addMessage(text, sender) {
  const div = document.createElement("div");
  div.className = `message ${sender}`;
  div.textContent = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function showCrisisBanner(helplines) {
  if (!helplines || helplines.length === 0) return;
  helplineList.innerHTML = helplines
    .map(h => `<div class="helpline-item">${h.name}: <strong>${h.number}</strong></div>`)
    .join("");
  crisisBanner.classList.remove("hidden");
}

function cleanTextForSpeech(text) {
  return text
    .replace(/[\p{Extended_Pictographic}\p{Emoji_Presentation}]/gu, "")
    .replace(/[*_#`~]/g, "")
    .replace(/[→←↑↓⇒⇐✓✔•▪◦]/g, "")
    .replace(/https?:\/\/\S+/gi, "")
    .replace(/([!?.,])\1+/g, "$1")
    .replace(/\s+/g, " ")
    .trim();
}

function speak(text, onEnd) {
  if (!("speechSynthesis" in window)) {
    if (onEnd) onEnd();
    return;
  }
  const cleanText = cleanTextForSpeech(text);
  if (!cleanText) {
    if (onEnd) onEnd();
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.lang = "en-IN";
  utterance.rate = 0.95;
  utterance.pitch = 1;
  utterance.volume = 1;

  utterance.onend = () => { if (onEnd) onEnd(); };
  utterance.onerror = () => { if (onEnd) onEnd(); };

  window.speechSynthesis.speak(utterance);
}

/**
 * Sends a message to the backend.
 * @param {string} message - what the user said/typed
 * @param {boolean} speakReply - whether the reply should be read aloud
 *   (true for voice input, false for typed text)
 * @param {function} onReply - optional callback(data) once the reply arrives,
 *   used by orb mode to drive the orb's visual state
 */
async function sendMessage(message, speakReply, onReply) {
  if (!message.trim()) return;

  addMessage(message, "user");
  textInput.value = "";

  try {
    const res = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });

    if (!res.ok) throw new Error("Backend error");

    const data = await res.json();

    addMessage(data.reply, "bot");

    if (data.risk_level === "high") {
      showCrisisBanner(data.helplines);
    }

    history.push({ role: "user", content: message });
    history.push({ role: "assistant", content: data.reply });
    if (history.length > 10) history = history.slice(-10);

    if (speakReply) {
      speak(data.reply, () => { if (onReply) onReply(data); });
    } else {
      if (onReply) onReply(data);
    }
  } catch (err) {
    const errMsg = "I'm having trouble connecting right now. Please make sure the backend server is running.";
    addMessage(errMsg, "bot");
    console.error(err);
    if (speakReply) speak(errMsg, () => { if (onReply) onReply(null); });
    else if (onReply) onReply(null);
  }
}

// ---------- Text chat (typed messages never get spoken aloud) ----------
sendBtn.addEventListener("click", () => sendMessage(textInput.value, false));
textInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage(textInput.value, false);
});

// ---------- Mic button inside the normal chat (voice input, spoken reply) ----------
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.lang = "en-IN";
  recognition.interimResults = false;

  micBtn.addEventListener("click", () => {
    micBtn.classList.add("listening");
    recognition.start();
  });

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    sendMessage(transcript, true);
  };
  recognition.onend = () => micBtn.classList.remove("listening");
  recognition.onerror = () => micBtn.classList.remove("listening");
} else {
  micBtn.disabled = true;
  micBtn.title = "Voice input not supported in this browser - try Chrome";
}

// ---------- Blue Orb voice-only mode ----------
function setOrbState(state, statusText) {
  orbCircle.className = "orb-circle " + state;
  orbStatus.textContent = statusText;
}

function openOrbMode() {
  orbOverlay.classList.remove("hidden");
  setOrbState("idle", "Tap the orb to talk");
  orbCaption.textContent = "";
}

function closeOrbMode() {
  orbOverlay.classList.add("hidden");
  if (recognition) recognition.abort();
  window.speechSynthesis.cancel();
}

function orbListen() {
  if (!recognition) {
    setOrbState("idle", "Voice not supported in this browser");
    return;
  }
  setOrbState("listening", "Listening...");

  const orbRecognition = new SpeechRecognition();
  orbRecognition.lang = "en-IN";
  orbRecognition.interimResults = false;

  orbRecognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    orbCaption.textContent = `You: "${transcript}"`;
    setOrbState("thinking", "Thinking...");

    sendMessage(transcript, false, (data) => {
      if (!data) {
        setOrbState("idle", "Tap the orb to talk");
        return;
      }
      orbCaption.textContent = data.reply;
      setOrbState("speaking", "Speaking...");
      speak(data.reply, () => {
        setOrbState("idle", "Tap the orb to talk");
      });
    });
  };

  orbRecognition.onerror = () => setOrbState("idle", "Tap the orb to talk");
  orbRecognition.onend = () => {
    if (orbCircle.classList.contains("listening")) {
      setOrbState("idle", "Tap the orb to talk");
    }
  };

  orbRecognition.start();
}

if (orbToggleBtn) orbToggleBtn.addEventListener("click", openOrbMode);
if (orbCloseBtn) orbCloseBtn.addEventListener("click", closeOrbMode);
if (orbCircle) orbCircle.addEventListener("click", () => {
  if (orbCircle.className.trim() === "orb-circle" || orbCircle.classList.contains("idle")) {
    orbListen();
  }
});
