// app.js
// MannMitra - Mental Wellbeing Companion
// Handles: welcome screen, text chat, voice input (STT), voice output (TTS),
// crisis banner, and the Voice Orb mode.

const BACKEND_URL = "https://mannmitra-backend-hrrh.onrender.com"; // live backend

// ============ DOM Elements ============
const welcomeScreen = document.getElementById("welcome-screen");
const startChatBtn = document.getElementById("start-chat-btn");
const welcomeHelpBtn = document.getElementById("welcome-help-btn");
const appContainer = document.getElementById("app");
const dashboardScreen = document.getElementById("dashboard");

const chatWindow = document.getElementById("chat-window");
const textInput = document.getElementById("text-input");
const sendBtn = document.getElementById("send-btn");
const micBtn = document.getElementById("mic-btn");
const crisisBanner = document.getElementById("crisis-banner");
const helplineList = document.getElementById("helpline-list");

// Dashboard & Navigation Elements
const dashVoiceBtn = document.getElementById("dash-voice-btn");
const actionChatBtn = document.getElementById("action-chat-btn");
const actionVoiceBtn = document.getElementById("action-voice-btn");
const navDashBtn = document.getElementById("nav-dash-btn");
const navChatBtn = document.getElementById("nav-chat-btn");
const navDashBtnChat = document.getElementById("nav-dash-btn-chat");
const navChatBtnChat = document.getElementById("nav-chat-btn-chat");
const moodBtns = document.querySelectorAll(".mood-btn");
const moodResponseBanner = document.getElementById("mood-response-banner");

// Orb mode elements
const orbToggleBtn = document.getElementById("orb-toggle-btn");
const orbOverlay = document.getElementById("orb-overlay");
const orbCloseBtn = document.getElementById("orb-close-btn");
const orbCircle = document.getElementById("orb-circle");
const orbStatus = document.getElementById("orb-status");
const orbCaption = document.getElementById("orb-caption");
const orbWaveform = document.getElementById("orb-waveform");
const orbStopBtn = document.getElementById("orb-stop-btn");

// ============ State ============
let history = [];
let requestCounter = 0;
const pendingRequests = new Map(); // requestId -> { indicatorEl, aborted }

// ============ Navigation & Views ============
function showView(viewName) {
  if (viewName === "dashboard") {
    if (dashboardScreen) dashboardScreen.classList.remove("hidden");
    if (appContainer) appContainer.classList.add("hidden");
    const resourcesView = document.getElementById("resources-view");
    if (resourcesView) resourcesView.classList.add("hidden");
  } else if (viewName === "chat") {
    if (dashboardScreen) dashboardScreen.classList.add("hidden");
    if (appContainer) appContainer.classList.remove("hidden");
    const resourcesView = document.getElementById("resources-view");
    if (resourcesView) resourcesView.classList.add("hidden");
  } else if (viewName === "resources") {
    if (dashboardScreen) dashboardScreen.classList.add("hidden");
    if (appContainer) appContainer.classList.add("hidden");
    const resourcesView = document.getElementById("resources-view");
    if (resourcesView) {
      resourcesView.classList.remove("hidden");
      loadResources();
    }
  }
}

// ============ Welcome Screen ============
if (startChatBtn) {
  startChatBtn.addEventListener("click", () => {
    welcomeScreen.classList.add("hidden");
    showView("dashboard");
  });
}

if (welcomeHelpBtn) {
  welcomeHelpBtn.addEventListener("click", () => {
    alert("If you're in crisis, please reach out to emergency services or a crisis helpline immediately.\n\nEmergency: 112\nNational Helpline: 1800-891-4416\nLPU Wellbeing: Contact your campus counselor");
  });
}

// ============ Status Indicator Functions ============
function createStatusIndicator(status, requestId) {
  const div = document.createElement("div");
  div.className = "message bot";
  div.setAttribute("data-request-id", requestId);

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  const img = document.createElement("img");
  img.src = "assets/mannmitra-icon.png";
  img.alt = "MannMitra";
  img.className = "bot-logo-img";
  avatar.appendChild(img);
  div.appendChild(avatar);

  const bubble = document.createElement("div");
  bubble.className = "message-bubble status-indicator";
  bubble.setAttribute("aria-live", "polite");
  bubble.setAttribute("aria-label", status);

  const para = document.createElement("p");
  para.innerHTML = `${status}<span class="typing-dots"><span>.</span><span>.</span><span>.</span></span>`;
  bubble.appendChild(para);
  div.appendChild(bubble);

  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return div;
}

function removeStatusIndicator(requestId) {
  if (!pendingRequests.has(requestId)) return;
  const request = pendingRequests.get(requestId);
  if (request.indicatorEl && request.indicatorEl.parentNode === chatWindow) {
    chatWindow.removeChild(request.indicatorEl);
  }
  pendingRequests.delete(requestId);
}

function isRequestStillPending(requestId) {
  return pendingRequests.has(requestId) && !pendingRequests.get(requestId).aborted;
}

// ============ Message Display ============
function addMessage(text, sender) {
  const div = document.createElement("div");
  div.className = `message ${sender}`;

  if (sender === "bot") {
    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    const img = document.createElement("img");
    img.src = "assets/mannmitra-icon.png";
    img.alt = "MannMitra";
    img.className = "bot-logo-img";
    avatar.appendChild(img);
    div.appendChild(avatar);
  }

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  const para = document.createElement("p");
  para.textContent = text;
  bubble.appendChild(para);
  div.appendChild(bubble);

  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// ============ Crisis Banner ============
function showCrisisBanner(helplines) {
  if (!helplines || helplines.length === 0) return;
  helplineList.innerHTML = helplines
    .map(h => `<div class="helpline-item">${h.name}: <strong>${h.number}</strong></div>`)
    .join("");
  crisisBanner.classList.remove("hidden");
}

// ============ Text-to-Speech (TTS) ============
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

// ============ Send Message to Backend ============
async function sendMessage(message, speakReply, onReply) {
  if (!message.trim()) return;

  addMessage(message, "user");
  textInput.value = "";

  const requestId = ++requestCounter;
  const thinkingIndicator = createStatusIndicator("MM is thinking...", requestId);
  pendingRequests.set(requestId, { indicatorEl: thinkingIndicator, aborted: false });

  try {
    const res = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });

    if (!isRequestStillPending(requestId)) return;
    if (!res.ok) throw new Error("Backend error");

    const data = await res.json();

    if (!isRequestStillPending(requestId)) return;

    // Show typing indicator
    removeStatusIndicator(requestId);
    const typingIndicator = createStatusIndicator("MM is typing...", requestId);
    pendingRequests.set(requestId, { indicatorEl: typingIndicator, aborted: false });

    // Minimal delay
    const baseDelay = 150;
    const lengthDelay = Math.min(Math.floor(data.reply.length / 80) * 50, 250);
    const totalDelay = baseDelay + lengthDelay;
    await new Promise(resolve => setTimeout(resolve, totalDelay));

    if (!isRequestStillPending(requestId)) return;

    removeStatusIndicator(requestId);
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
    if (!isRequestStillPending(requestId)) return;
    removeStatusIndicator(requestId);
    const errMsg = "I'm having trouble connecting right now. Please make sure the backend server is running.";
    addMessage(errMsg, "bot");
    console.error(err);
    if (speakReply) speak(errMsg, () => { if (onReply) onReply(null); });
    else if (onReply) onReply(null);
  }
}

// ============ Normal Text Chat ============
sendBtn.addEventListener("click", () => sendMessage(textInput.value, false));
textInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage(textInput.value, false);
});

// ============ Normal Chat Microphone (Text-Only Response) ============
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
    // STEP 1: Normal chat mic -> text response ONLY (no TTS)
    sendMessage(transcript, false);
  };

  recognition.onend = () => micBtn.classList.remove("listening");
  recognition.onerror = () => micBtn.classList.remove("listening");
} else {
  micBtn.disabled = true;
  micBtn.title = "Voice input not supported in this browser - try Chrome";
}

// ============ Voice Orb Mode — Brand polish + audio-reactive ============
let orbAudioContext = null;
let orbAnalyser = null;
let orbMicStream = null;
let orbVolumeRaf = null;
let orbFakePulseTimer = null;

function getOrbCenterContainer() {
  return document.getElementById("orb-center-container");
}

function setOrbState(state, statusText) {
  orbCircle.classList.remove("idle", "listening", "thinking", "speaking");
  if (state) orbCircle.classList.add(state);
  // keep base class
  if (!orbCircle.classList.contains("orb-circle")) orbCircle.classList.add("orb-circle");
  orbStatus.textContent = statusText;

  const center = getOrbCenterContainer();
  const isSonar = state === "listening" || state === "speaking";
  if (center) {
    center.classList.toggle("sonar", isSonar);
    center.classList.toggle("ambient-listening", state === "listening");
    center.classList.toggle("ambient-speaking", state === "speaking");
  }

  if (state === "listening" || state === "speaking") {
    orbWaveform.classList.add("active");
  } else {
    orbWaveform.classList.remove("active");
  }

  if (state !== "listening") stopOrbAudioReactive();
}

async function startOrbAudioReactive() {
  // Try real mic volume via Web Audio API; fall back to rhythmic random pulse
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) throw new Error("no getUserMedia");
    // Reuse existing stream if still live
    if (orbMicStream && orbMicStream.getTracks().some(t => t.readyState === "live")) {
      startOrbAnalyserLoop();
      return;
    }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    orbMicStream = stream;
    const AC = window.AudioContext || /** @type {any} */ (window).webkitAudioContext;
    if (!AC) throw new Error("no AudioContext");
    orbAudioContext = new AC();
    const src = orbAudioContext.createMediaStreamSource(stream);
    orbAnalyser = orbAudioContext.createAnalyser();
    orbAnalyser.fftSize = 256;
    src.connect(orbAnalyser);
    startOrbAnalyserLoop();
  } catch (_) {
    startOrbFakePulse();
  }
}

function startOrbAnalyserLoop() {
  stopOrbFakePulse();
  if (!orbAnalyser) { startOrbFakePulse(); return; }
  const data = new Uint8Array(orbAnalyser.frequencyBinCount);
  let baseScale = 1.06;
  function tick() {
    if (!orbCircle.classList.contains("listening")) return;
    orbAnalyser.getByteFrequencyData(data);
    // Average low-mid energy as volume proxy
    let sum = 0;
    for (let i = 0; i < data.length; i++) sum += data[i];
    const avg = sum / data.length; // 0-255
    const norm = Math.min(1, avg / 90); // clamp
    // Map norm 0..1 -> scale 1.04 .. 1.18, with smoothing
    const target = 1.04 + norm * 0.14;
    baseScale = baseScale * 0.78 + target * 0.22;
    orbCircle.style.transform = `scale(${baseScale.toFixed(3)})`;
    orbVolumeRaf = requestAnimationFrame(tick);
  }
  orbVolumeRaf = requestAnimationFrame(tick);
}

function startOrbFakePulse() {
  stopOrbFakePulse();
  let phase = 0;
  function tick() {
    if (!orbCircle.classList.contains("listening")) return;
    phase += 0.18 + Math.random() * 0.12;
    const scale = 1.06 + Math.sin(phase) * 0.045 + Math.random() * 0.02;
    orbCircle.style.transform = `scale(${scale.toFixed(3)})`;
    orbFakePulseTimer = setTimeout(() => requestAnimationFrame(tick), 90 + Math.random() * 80);
  }
  tick();
}

function stopOrbFakePulse() {
  if (orbFakePulseTimer) { clearTimeout(orbFakePulseTimer); orbFakePulseTimer = null; }
}

function stopOrbAudioReactive() {
  if (orbVolumeRaf) { cancelAnimationFrame(orbVolumeRaf); orbVolumeRaf = null; }
  stopOrbFakePulse();
  orbCircle.style.transform = "";
  // Keep stream alive briefly for quick re-entry; full cleanup on overlay close
}

function openOrbMode() {
  orbOverlay.classList.remove("hidden");
  setOrbState("idle", "Tap to talk");
  orbCaption.textContent = "Speak freely, I'm here for you.";
}

function closeOrbMode() {
  orbOverlay.classList.add("hidden");
  stopOrbAudioReactive();
  // Full mic stream cleanup on close so permission prompt re-appears correctly next open
  if (orbMicStream) {
    orbMicStream.getTracks().forEach(t => t.stop());
    orbMicStream = null;
  }
  if (orbAudioContext && orbAudioContext.state !== "closed") {
    try { orbAudioContext.close(); } catch (_) {}
    orbAudioContext = null;
    orbAnalyser = null;
  }
  const center = getOrbCenterContainer();
  if (center) {
    center.classList.remove("sonar", "ambient-listening", "ambient-speaking");
  }
  if (recognition) try { recognition.abort(); } catch (_) {}
  window.speechSynthesis.cancel();
}

function orbListen() {
  if (!SpeechRecognition) {
    setOrbState("idle", "Voice not supported in this browser");
    return;
  }
  setOrbState("listening", "I'm listening...");
  // Start audio-reactive scaling (real AnalyserNode or fallback pulse) — never blocks SpeechRecognition
  startOrbAudioReactive().catch(() => {});

  const orbRecognition = new SpeechRecognition();
  orbRecognition.lang = "en-IN";
  orbRecognition.interimResults = false;

  orbRecognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    orbCaption.textContent = `You: "${transcript}"`;
    setOrbState("thinking", "Thinking...");

    sendMessage(transcript, false, (data) => {
      if (!data) {
        setOrbState("idle", "Tap to talk");
        return;
      }
      orbCaption.textContent = data.reply;
      setOrbState("speaking", "Speaking...");
      speak(data.reply, () => {
        setOrbState("idle", "Tap to talk");
      });
    });
  };

  orbRecognition.onerror = () => setOrbState("idle", "Tap to talk");
  orbRecognition.onend = () => {
    if (orbCircle.classList.contains("listening")) {
      setOrbState("idle", "Tap to talk");
    }
  };

  try { orbRecognition.start(); } catch (_) { setOrbState("idle", "Tap to talk"); }
}

// ============ Orb Event Handlers ============
if (orbToggleBtn) orbToggleBtn.addEventListener("click", openOrbMode);
if (orbCloseBtn) orbCloseBtn.addEventListener("click", closeOrbMode);
if (orbStopBtn) orbStopBtn.addEventListener("click", closeOrbMode);

if (orbCircle) {
  orbCircle.addEventListener("click", () => {
    const currentClass = orbCircle.className.trim();
    if (currentClass === "orb-circle" || currentClass === "orb-circle idle") {
      orbListen();
    }
  });
}

// ============ Dashboard & Navigation Event Handlers ============
if (navDashBtn) navDashBtn.addEventListener("click", () => showView("dashboard"));
if (navChatBtn) navChatBtn.addEventListener("click", () => showView("chat"));
if (navDashBtnChat) navDashBtnChat.addEventListener("click", () => showView("dashboard"));
if (navChatBtnChat) navChatBtnChat.addEventListener("click", () => showView("chat"));

if (actionChatBtn) actionChatBtn.addEventListener("click", () => showView("chat"));
if (actionVoiceBtn) actionVoiceBtn.addEventListener("click", openOrbMode);
if (dashVoiceBtn) dashVoiceBtn.addEventListener("click", openOrbMode);

// Mood Check-in Handling
const moodResponses = {
  Great: "Awesome to hear that! Keep spreading the positive vibes. 😊",
  Okay: "Taking it one step at a time is totally okay. I'm here if you want to chat. 💙",
  Stressed: "Take a deep breath. You're doing the best you can. Want to talk about it? 🫂",
  Anxious: "Feeling anxious can be overwhelming. Remember to pause and ground yourself. I'm here. 🌸",
  Low: "I'm really sorry you're feeling down. You're not alone, and it's okay to feel this way. 💖"
};

moodBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    moodBtns.forEach((b) => b.classList.remove("selected"));
    btn.classList.add("selected");

    const mood = btn.getAttribute("data-mood");
    if (moodResponseBanner && moodResponses[mood]) {
      moodResponseBanner.textContent = moodResponses[mood];
      moodResponseBanner.classList.remove("hidden");
    }
  });
});

// ============ Guided Breathing Exercise ============
const breathingOverlay = document.getElementById("breathing-overlay");
const breathingCloseBtn = document.getElementById("breathing-close-btn");
const breathingCircle = document.getElementById("breathing-circle");
const breathingStatus = document.getElementById("breathing-status");
const actionBreathingBtn = document.getElementById("action-breathing-btn");

let breathingCycle = null;
let breathingRingTimer = null;
const BREATHING_CIRCUMFERENCE = 2 * Math.PI * 108; // must match r=108 in SVG (~678.58)

function setBreathingRing(phase, progress) {
  const ring = document.getElementById("breathing-progress-ring");
  if (!ring) return;
  // Ensure dasharray matches circumference (guard against CSS override)
  ring.style.strokeDasharray = String(BREATHING_CIRCUMFERENCE);
  let offset;
  if (phase === "in") {
    // fills 0 -> 100%
    offset = BREATHING_CIRCUMFERENCE * (1 - progress);
  } else if (phase === "hold-in") {
    offset = 0; // full
  } else if (phase === "out") {
    // empties 100% -> 0%
    offset = BREATHING_CIRCUMFERENCE * progress;
  } else {
    // hold-out: empty
    offset = BREATHING_CIRCUMFERENCE;
  }
  ring.style.strokeDashoffset = String(offset);
}

function startBreathingCycle() {
  if (breathingCycle !== null) return;

  const phases = [
    { status: "Breathe in...", animation: "in", duration: 4000 },
    { status: "Hold...", animation: "hold-in", duration: 4000 },
    { status: "Breathe out...", animation: "out", duration: 4000 },
    { status: "Hold...", animation: "hold-out", duration: 4000 }
  ];

  let phaseIndex = 0;
  let phaseStart = 0;

  function tickRing() {
    const phase = phases[phaseIndex % phases.length];
    const elapsed = Date.now() - phaseStart;
    const progress = Math.min(1, elapsed / phase.duration);
    setBreathingRing(phase.animation, progress);
    if (breathingCycle !== null) {
      breathingRingTimer = requestAnimationFrame(tickRing);
    }
  }

  function runPhase() {
    const phase = phases[phaseIndex % phases.length];
    breathingStatus.textContent = phase.status;
    breathingCircle.classList.remove("in", "hold-in", "out", "hold-out");
    // force reflow so re-adding same class restarts animation reliably across cycles
    void breathingCircle.offsetWidth;
    breathingCircle.classList.add(phase.animation);
    phaseStart = Date.now();
    // kick ring loop for this phase
    if (breathingRingTimer) cancelAnimationFrame(breathingRingTimer);
    tickRing();
    phaseIndex++;
    breathingCycle = setTimeout(runPhase, phase.duration);
  }

  runPhase();
}

function stopBreathingCycle() {
  if (breathingCycle !== null) {
    clearTimeout(breathingCycle);
    breathingCycle = null;
  }
  if (breathingRingTimer) { cancelAnimationFrame(breathingRingTimer); breathingRingTimer = null; }
  breathingCircle.classList.remove("in", "hold-in", "out", "hold-out");
  setBreathingRing("hold-out", 1);
}

if (actionBreathingBtn) {
  actionBreathingBtn.addEventListener("click", () => {
    breathingOverlay.classList.remove("hidden");
    startBreathingCycle();
  });
}

if (breathingCloseBtn) {
  breathingCloseBtn.addEventListener("click", () => {
    stopBreathingCycle();
    breathingOverlay.classList.add("hidden");
  });
}

// ============ Resources Page ============
async function loadResources() {
  const resourcesList = document.getElementById("resources-list");
  if (!resourcesList) return;

  try {
    const res = await fetch(`${BACKEND_URL}/resources`);
    if (!res.ok) throw new Error("Failed to fetch resources");

    const resources = await res.json();

    // Filter out resources with PLACEHOLDER in the answer
    const validResources = resources.filter(r => !r.answer.includes("PLACEHOLDER"));

    if (validResources.length === 0) {
      resourcesList.innerHTML = '<p style="color: #B0B0C4; text-align: center;">No verified resources available yet.</p>';
      return;
    }

    resourcesList.innerHTML = validResources
      .map(r => `
        <div class="resource-card">
          <p class="resource-topic">${r.topic}</p>
          <p class="resource-answer">${r.answer}</p>
        </div>
      `)
      .join("");
  } catch (err) {
    console.error("Error loading resources:", err);
    resourcesList.innerHTML = '<p style="color: #B0B0C4; text-align: center;">Error loading resources. Please try again.</p>';
  }
}

// Resources navigation
const navResourcesBtns = document.querySelectorAll('[id*="nav-resources-btn"]');
const navDashResourcesBtn = document.getElementById("nav-dash-btn-resources");
const navChatResourcesBtn = document.getElementById("nav-chat-btn-resources");

navResourcesBtns.forEach(btn => {
  if (btn && btn.id !== "nav-resources-btn" && btn.id !== "nav-resources-btn-chat") {
    btn.addEventListener("click", () => showView("resources"));
  }
});

// Dashboard Resources button
if (document.getElementById("nav-resources-btn")) {
  document.getElementById("nav-resources-btn").addEventListener("click", () => showView("resources"));
}

// Chat view Resources button
if (document.getElementById("nav-resources-btn-chat")) {
  document.getElementById("nav-resources-btn-chat").addEventListener("click", () => showView("resources"));
}

// Resources view navigation
if (navDashResourcesBtn) {
  navDashResourcesBtn.addEventListener("click", () => showView("dashboard"));
}

if (navChatResourcesBtn) {
  navChatResourcesBtn.addEventListener("click", () => showView("chat"));
}