// app.js
// Handles: sending messages to the backend, showing replies, voice input (STT),
// voice output (TTS), and showing the crisis banner when the backend flags risk.

const BACKEND_URL = "http://127.0.0.1:8000"; // change this once you deploy the backend

const chatWindow = document.getElementById("chat-window");
const textInput = document.getElementById("text-input");
const sendBtn = document.getElementById("send-btn");
const micBtn = document.getElementById("mic-btn");
const crisisBanner = document.getElementById("crisis-banner");
const helplineList = document.getElementById("helpline-list");

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
    // Remove emojis and most symbols
    .replace(/[\p{Extended_Pictographic}\p{Emoji_Presentation}]/gu, "")

    // Remove markdown formatting
    .replace(/[*_#`~]/g, "")

    // Remove decorative arrows and symbols
    .replace(/[→←↑↓⇒⇐✓✔•▪◦]/g, "")

    // Remove URLs
    .replace(/https?:\/\/\S+/gi, "")

    // Remove excessive punctuation
    .replace(/([!?.,])\1+/g, "$1")

    // Replace multiple spaces/newlines
    .replace(/\s+/g, " ")

    .trim();
}


function speak(text) {
  if (!("speechSynthesis" in window)) {
    console.error("Text-to-Speech is not supported in this browser.");
    return;
  }

  const cleanText = cleanTextForSpeech(text);

  if (!cleanText) {
    return;
  }

  // Stop previous speech
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(cleanText);

  utterance.lang = "en-IN";
  utterance.rate = 0.95;
  utterance.pitch = 1;
  utterance.volume = 1;

  utterance.onstart = () => {
    console.log("MannMitra started speaking");
  };

  utterance.onend = () => {
    console.log("MannMitra finished speaking");
  };

  utterance.onerror = (event) => {
    console.error("Speech synthesis error:", event);
  };

  window.speechSynthesis.speak(utterance);
}

async function sendMessage(message) {
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
    speak(data.reply);

    if (data.risk_level === "high") {
      showCrisisBanner(data.helplines);
    }

    history.push({ role: "user", content: message });
    history.push({ role: "assistant", content: data.reply });

// Keep only the most recent 10 messages
    if (history.length > 10) {
      history = history.slice(-10);
    }
  } catch (err) {
    addMessage("I'm having trouble connecting right now. Please make sure the backend server is running.", "bot");
    console.error(err);
  }
}

sendBtn.addEventListener("click", () => sendMessage(textInput.value));
textInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage(textInput.value);
});

// Voice input using the browser's built-in Web Speech API (Chrome works best)
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
  const recognition = new SpeechRecognition();
  recognition.lang = "en-IN";
  recognition.interimResults = false;

  micBtn.addEventListener("click", () => {
    micBtn.classList.add("listening");
    recognition.start();
  });

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    sendMessage(transcript);
  };

  recognition.onend = () => micBtn.classList.remove("listening");
  recognition.onerror = () => micBtn.classList.remove("listening");
} else {
  micBtn.disabled = true;
  micBtn.title = "Voice input not supported in this browser - try Chrome";
}
