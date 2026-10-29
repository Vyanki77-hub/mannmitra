// app.js — MannMitra Desktop-First Mental Wellbeing Companion
// Step 2: Complete Navigation Architecture & Dedicated Wellness Sections

const BACKEND_URL = "http://127.0.0.1:8000";

// ==================== STATE MANAGEMENT ====================
const state = {
  activeView: "chat",
  currentUserName: "Vyankatesh",
  isGuest: false,
  greetingSpoken: false,
  settings: {
    theme: "light",
    accent: "pink-purple",
    autoGreeting: true,
    speechRate: 0.95,
    voiceLocale: "en-IN",
    reducedMotion: false,
    fontSize: "default",
  },
  currentIntention: "Breathe before reacting",
  currentMood: "Good",
  moodHistory: [
    { date: "2026-10-28", mood: "Good", emoji: "😊", note: "Drafted my assignments calmly." },
    { date: "2026-10-27", mood: "Okay", emoji: "😐", note: "Busy day in classes." },
    { date: "2026-10-26", mood: "Sad", emoji: "😔", note: "Felt isolated in hostel room." },
    { date: "2026-10-25", mood: "Great", emoji: "🌟", note: "Had a great walk on campus." },
    { date: "2026-10-24", mood: "Good", emoji: "😊", note: "Managed my exam stress well." },
  ],
  bookmarkedGuides: new Set([1, 4]),
  breatheSoundEnabled: false,
  breatheActiveExercise: "box",
  breatheDurationMins: 1,
  breatheTimer: null,
  breathePhaseIndex: 0,
  breatheElapsedSec: 0,
  breatheIsPaused: false,
  activeJourney: null,
  activeJourneyStep: 0,
};

// ==================== DOM ELEMENTS ====================
// Overlays & Top-Level Screens
const loginView = document.getElementById("login-view");
const greetingOverlay = document.getElementById("greeting-overlay");
const desktopDashboard = document.getElementById("desktop-dashboard");
const dashboardRightPanel = document.getElementById("dashboard-right-panel");

// Login Elements
const startChatBtn = document.getElementById("start-chat-btn");
const guestEnterBtn = document.getElementById("guest-enter-btn");
const welcomeHelpBtn = document.getElementById("welcome-help-btn");
const loginEmailInput = document.getElementById("login-email");
const loginPasswordInput = document.getElementById("login-password");
const togglePasswordBtn = document.getElementById("toggle-password-btn");

// Greeting Elements
const greetingHeading = document.getElementById("greeting-heading");
const greetingSubtitle = document.getElementById("greeting-subtitle");
const greetingContinueBtn = document.getElementById("greeting-continue-btn");
const greetingSkipBtn = document.getElementById("greeting-skip-btn");

// Header Elements
const currentViewTitle = document.getElementById("current-view-title");
const headerUserName = document.getElementById("header-user-name");
const headerUserInitial = document.getElementById("header-user-initial");
const sidebarDisplayName = document.getElementById("sidebar-display-name");
const sidebarUserInitial = document.getElementById("sidebar-user-initial");
const dashVoiceBtn = document.getElementById("dash-voice-btn");

// Main Views Map
const views = {
  "chat": document.getElementById("app"),
  "wellbeing": document.getElementById("view-wellbeing"),
  "mood-tracker": document.getElementById("view-mood-tracker"),
  "relax-breathe": document.getElementById("view-relax-breathe"),
  "guided-support": document.getElementById("view-guided-support"),
  "college-help": document.getElementById("view-college-help"),
  "resources-library": document.getElementById("view-resources-library"),
  "my-journey": document.getElementById("view-my-journey"),
  "settings": document.getElementById("view-settings"),
};

const viewTitles = {
  "chat": "Chat with MM",
  "wellbeing": "My Wellbeing",
  "mood-tracker": "Mood Tracker",
  "relax-breathe": "Relax & Breathe",
  "guided-support": "Guided Support",
  "college-help": "College Help (LPU)",
  "resources-library": "Resources Library",
  "my-journey": "My Journey",
  "settings": "Settings",
};

// Chat Elements
const chatWindow = document.getElementById("chat-window");
const textInput = document.getElementById("text-input");
const sendBtn = document.getElementById("send-btn");
const micBtn = document.getElementById("mic-btn");
const crisisBanner = document.getElementById("crisis-banner");
const helplineList = document.getElementById("helpline-list");
const promptChips = document.querySelectorAll(".prompt-chip");

// Orb Elements
const orbOverlay = document.getElementById("orb-overlay");
const orbCloseBtn = document.getElementById("orb-close-btn");
const orbCircle = document.getElementById("orb-circle");
const orbStatus = document.getElementById("orb-status");
const orbCaption = document.getElementById("orb-caption");
const orbWaveform = document.getElementById("orb-waveform");
const orbStopBtn = document.getElementById("orb-stop-btn");

// Breathing Overlay Elements
const breathingOverlay = document.getElementById("breathing-overlay");
const breathingCloseBtn = document.getElementById("breathing-close-btn");
const breathingCircle = document.getElementById("breathing-circle");
const breathingStatus = document.getElementById("breathing-status");

// Audio Context for Ambient Chimes
let synthAudioContext = null;

// ==================== SPEECH RECOGNITION & SYNTHESIS ====================
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

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
  const clean = cleanTextForSpeech(text);
  if (!clean) {
    if (onEnd) onEnd();
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.lang = state.settings.voiceLocale || "en-IN";
  utterance.rate = state.settings.speechRate || 0.95;
  utterance.pitch = 1;
  utterance.volume = 1;

  utterance.onend = () => { if (onEnd) onEnd(); };
  utterance.onerror = () => { if (onEnd) onEnd(); };

  try {
    window.speechSynthesis.speak(utterance);
  } catch (_) {
    if (onEnd) onEnd();
  }
}

// Gentle audio chime for breathing / sound toggle
function playGentleChime(freq = 432, duration = 1.2) {
  if (!state.breatheSoundEnabled) return;
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    if (!synthAudioContext) synthAudioContext = new AC();
    if (synthAudioContext.state === "suspended") synthAudioContext.resume();

    const osc = synthAudioContext.createOscillator();
    const gain = synthAudioContext.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(freq, synthAudioContext.currentTime);

    gain.gain.setValueAtTime(0.01, synthAudioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.18, synthAudioContext.currentTime + 0.1);
    gain.gain.exponentialRampToValueAtTime(0.001, synthAudioContext.currentTime + duration);

    osc.connect(gain);
    gain.connect(synthAudioContext.destination);

    osc.start();
    osc.stop(synthAudioContext.currentTime + duration);
  } catch (_) {}
}

// ==================== NAVIGATION ARCHITECTURE ====================
function navigateTo(viewKey) {
  if (!views[viewKey]) return;

  // 1. Hide all main views
  Object.keys(views).forEach(key => {
    if (views[key]) views[key].classList.add("hidden");
  });

  // 2. Show selected view
  views[viewKey].classList.remove("hidden");
  state.activeView = viewKey;

  // 3. Update sidebar active item
  document.querySelectorAll(".sidebar-nav-item").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-view") === viewKey);
  });

  // 4. Update Header Title
  if (currentViewTitle) {
    currentViewTitle.textContent = viewTitles[viewKey] || "MannMitra Sanctuary";
  }

  // 5. Contextual Right Panel Handling
  if (dashboardRightPanel) {
    if (viewKey === "settings") {
      dashboardRightPanel.classList.add("hidden");
    } else {
      dashboardRightPanel.classList.remove("hidden");
      updateContextualRightPanel(viewKey);
    }
  }

  // 6. View-specific on-mount triggers
  if (viewKey === "mood-tracker") renderMoodCalendar();
  if (viewKey === "resources-library") renderResourcesLibrary();
  if (viewKey === "college-help") filterCampusCards("all");
}

function updateContextualRightPanel(viewKey) {
  const panelSubtext = document.querySelector(".panel-subtext");
  const panelHeading = document.getElementById("panel-greeting-user");
  if (panelHeading) panelHeading.textContent = `Namaste, ${state.currentUserName} 🙏`;

  if (!panelSubtext) return;
  switch (viewKey) {
    case "chat":
      panelSubtext.textContent = "Your confidential peer companion. Take your time.";
      break;
    case "wellbeing":
      panelSubtext.textContent = `Today's Intention: "${state.currentIntention}".`;
      break;
    case "mood-tracker":
      panelSubtext.textContent = `Current Mood logged: ${state.currentMood}.`;
      break;
    case "relax-breathe":
      panelSubtext.textContent = "Follow the rhythm. Release tension with every out-breath.";
      break;
    case "guided-support":
      panelSubtext.textContent = "Structured journeys for navigating campus challenges.";
      break;
    case "college-help":
      panelSubtext.textContent = "Verified LPU student welfare and counseling support.";
      break;
    case "resources-library":
      panelSubtext.textContent = `${state.bookmarkedGuides.size} guides bookmarked for quick reading.`;
      break;
    case "my-journey":
      panelSubtext.textContent = "Celebrating gentle, steady progress every day.";
      break;
    default:
      panelSubtext.textContent = "Your safe sanctuary.";
  }
}

// Bind all sidebar navigation buttons
document.querySelectorAll(".sidebar-nav-item").forEach(btn => {
  btn.addEventListener("click", () => {
    const targetView = btn.getAttribute("data-view");
    if (targetView) navigateTo(targetView);
  });
});

// Bind all "Back to Chat" buttons in page views
document.querySelectorAll(".back-to-chat-btn").forEach(btn => {
  btn.addEventListener("click", () => navigateTo("chat"));
});

// Chat Inner Tabs
const tabButtons = {
  chat: document.getElementById("tab-chat-btn"),
  voice: document.getElementById("tab-voice-btn"),
  activities: document.getElementById("tab-activities-btn"),
  journal: document.getElementById("tab-journal-btn"),
};

if (tabButtons.chat) {
  tabButtons.chat.addEventListener("click", () => {
    setActiveChatTab("chat");
  });
}
if (tabButtons.voice) {
  tabButtons.voice.addEventListener("click", () => {
    openOrbMode();
  });
}
if (tabButtons.activities) {
  tabButtons.activities.addEventListener("click", () => {
    navigateTo("guided-support");
  });
}
if (tabButtons.journal) {
  tabButtons.journal.addEventListener("click", () => {
    sendMessage("Let's do a short reflective journal check-in together. Ask me one thoughtful question.", false);
  });
}

function setActiveChatTab(tabName) {
  Object.keys(tabButtons).forEach(key => {
    if (tabButtons[key]) tabButtons[key].classList.toggle("active", key === tabName);
  });
}

// ==================== LOGIN & GREETING OVERLAY FLOW ====================
function updateUserNameDisplays(name) {
  const display = name && name.trim() ? name.trim() : "Friend";
  state.currentUserName = display;
  const initial = display.charAt(0).toUpperCase();

  if (headerUserName) headerUserName.textContent = display;
  if (sidebarDisplayName) sidebarDisplayName.textContent = display;
  if (headerUserInitial) headerUserInitial.textContent = initial;
  if (sidebarUserInitial) sidebarUserInitial.textContent = initial;

  const chatHeroGreeting = document.getElementById("chat-hero-greeting");
  if (chatHeroGreeting) chatHeroGreeting.textContent = `Welcome, ${display}! I'm MannMitra 🌸`;

  const chatInitial = document.getElementById("chat-initial-message");
  if (chatInitial) chatInitial.textContent = `Hi ${display}. Take your time, there is no rush here. What's on your mind today?`;

  const panelGreeting = document.getElementById("panel-greeting-user");
  if (panelGreeting) panelGreeting.textContent = `Namaste, ${display} 🙏`;
}

function handleLogin(isGuestMode = false) {
  state.isGuest = isGuestMode;
  const rawEmail = loginEmailInput ? loginEmailInput.value.trim() : "";
  let name = "Vyankatesh";

  if (isGuestMode || !rawEmail) {
    name = isGuestMode ? "Friend" : "Vyankatesh";
  } else if (rawEmail.includes("@")) {
    name = rawEmail.split("@")[0];
    name = name.charAt(0).toUpperCase() + name.slice(1);
  } else {
    name = rawEmail;
  }

  updateUserNameDisplays(name);

  // Transition to Greeting Overlay
  if (loginView) loginView.classList.add("hidden");
  if (greetingOverlay) greetingOverlay.classList.remove("hidden");

  // Prepare short greeting
  const shortGreeting = isGuestMode 
    ? "Hello there, how are you feeling today?" 
    : `Hello ${state.currentUserName}, how are you feeling today?`;

  if (greetingHeading) greetingHeading.textContent = shortGreeting;
  if (greetingSubtitle) greetingSubtitle.textContent = "Take a moment for yourself. I'm here to listen.";

  // Step 1: Automatic spoken greeting (short only, once)
  if (state.settings.autoGreeting && !state.greetingSpoken) {
    state.greetingSpoken = true;
    setTimeout(() => {
      speak(shortGreeting);
    }, 450);
  }
}

if (startChatBtn) startChatBtn.addEventListener("click", () => handleLogin(false));
if (guestEnterBtn) guestEnterBtn.addEventListener("click", () => handleLogin(true));

// Password Show/Hide Toggle
if (togglePasswordBtn && loginPasswordInput) {
  togglePasswordBtn.addEventListener("click", () => {
    const isPassword = loginPasswordInput.type === "password";
    loginPasswordInput.type = isPassword ? "text" : "password";
    togglePasswordBtn.innerHTML = isPassword
      ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`
      : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
  });
}

if (welcomeHelpBtn) {
  welcomeHelpBtn.addEventListener("click", () => {
    alert("Immediate 24/7 Helpline Contacts:\n\n• National Emergency: 112\n• Tele-MANAS: 1800-891-4416 (or 14416)\n• Vandrevala Foundation: 9999 666 555\n• LPU Department of Counseling & Happiness: Building 8, Room 208\n\nYou are not alone. Support is available right now.");
  });
}

function enterSanctuaryFromGreeting() {
  window.speechSynthesis.cancel();
  if (greetingOverlay) greetingOverlay.classList.add("hidden");
  if (desktopDashboard) desktopDashboard.classList.remove("hidden");
  navigateTo("chat");
}

if (greetingContinueBtn) greetingContinueBtn.addEventListener("click", enterSanctuaryFromGreeting);
if (greetingSkipBtn) greetingSkipBtn.addEventListener("click", enterSanctuaryFromGreeting);

// ==================== CHAT & MESSAGING LOGIC ====================
let conversationHistory = [];
let requestCounter = 0;
const pendingRequests = new Map();

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

  const para = document.createElement("p");
  para.innerHTML = `${status}<span class="typing-dots"><span></span><span></span><span></span></span>`;
  bubble.appendChild(para);
  div.appendChild(bubble);

  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return div;
}

function removeStatusIndicator(requestId) {
  if (!pendingRequests.has(requestId)) return;
  const req = pendingRequests.get(requestId);
  if (req.indicatorEl && req.indicatorEl.parentNode === chatWindow) {
    chatWindow.removeChild(req.indicatorEl);
  }
  pendingRequests.delete(requestId);
}

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

function showCrisisBanner(helplines) {
  if (!helplines || helplines.length === 0) return;
  if (helplineList) {
    helplineList.innerHTML = helplines
      .map(h => `<div class="helpline-item">${h.name}: <strong>${h.number}</strong></div>`)
      .join("");
  }
  if (crisisBanner) crisisBanner.classList.remove("hidden");
}

async function sendMessage(message, speakReply, onReply) {
  if (!message || !message.trim()) return;

  addMessage(message, "user");
  if (textInput) textInput.value = "";

  const requestId = ++requestCounter;
  const thinkingIndicator = createStatusIndicator("MM is thinking...", requestId);
  pendingRequests.set(requestId, { indicatorEl: thinkingIndicator, aborted: false });

  try {
    const res = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history: conversationHistory }),
    });

    if (!res.ok) throw new Error("Backend error");
    const data = await res.json();

    removeStatusIndicator(requestId);
    const typingIndicator = createStatusIndicator("MM is typing...", requestId);
    pendingRequests.set(requestId, { indicatorEl: typingIndicator, aborted: false });

    const delay = Math.min(150 + Math.floor((data.reply || "").length / 80) * 40, 240);
    await new Promise(r => setTimeout(r, delay));

    removeStatusIndicator(requestId);
    const botReply = data.reply && data.reply.trim() !== "" 
      ? data.reply 
      : "I'm listening. Take your time.";
    addMessage(botReply, "bot");

    if (data.risk_level === "high") {
      showCrisisBanner(data.helplines);
    }

    conversationHistory.push({ role: "user", content: message });
    conversationHistory.push({ role: "assistant", content: botReply });
    if (conversationHistory.length > 10) conversationHistory = conversationHistory.slice(-10);

    if (speakReply) {
      speak(botReply, () => { if (onReply) onReply(data); });
    } else if (onReply) {
      onReply(data);
    }
  } catch (err) {
    removeStatusIndicator(requestId);
    const fallbackMsg = "I'm having a little trouble connecting to my server right now, but please know that I'm right here with you.";
    addMessage(fallbackMsg, "bot");
    if (speakReply) speak(fallbackMsg, () => { if (onReply) onReply(null); });
    else if (onReply) onReply(null);
  }
}

if (sendBtn) sendBtn.addEventListener("click", () => sendMessage(textInput.value, false));
if (textInput) {
  textInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage(textInput.value, false);
  });
}

// Quick Prompt Chips
promptChips.forEach(chip => {
  chip.addEventListener("click", () => {
    const prompt = chip.getAttribute("data-prompt");
    if (prompt) sendMessage(prompt, false);
  });
});

// Normal Chat Mic (STT text-only)
if (SpeechRecognition && micBtn) {
  recognition = new SpeechRecognition();
  recognition.lang = state.settings.voiceLocale || "en-IN";
  recognition.interimResults = false;

  micBtn.addEventListener("click", () => {
    micBtn.classList.add("listening");
    recognition.start();
  });

  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    sendMessage(transcript, false);
  };

  recognition.onend = () => micBtn.classList.remove("listening");
  recognition.onerror = () => micBtn.classList.remove("listening");
} else if (micBtn) {
  micBtn.disabled = true;
  micBtn.title = "Voice recognition not supported in this browser";
}

// ==================== VIEW 2: MY WELLBEING LOGIC ====================
const intentionChips = document.querySelectorAll(".intention-chip");
const customIntentionInput = document.getElementById("custom-intention-input");
const saveIntentionBtn = document.getElementById("save-intention-btn");

intentionChips.forEach(chip => {
  chip.addEventListener("click", () => {
    intentionChips.forEach(c => c.classList.remove("active"));
    chip.classList.add("active");
    state.currentIntention = chip.getAttribute("data-intention");
    updateContextualRightPanel("wellbeing");
  });
});

if (saveIntentionBtn && customIntentionInput) {
  saveIntentionBtn.addEventListener("click", () => {
    const custom = customIntentionInput.value.trim();
    if (custom) {
      state.currentIntention = custom;
      intentionChips.forEach(c => c.classList.remove("active"));
      customIntentionInput.value = "";
      updateContextualRightPanel("wellbeing");
    }
  });
}

// Suggested Activities buttons in Wellbeing
document.querySelectorAll(".activity-suggestion-item").forEach(item => {
  item.addEventListener("click", () => {
    const target = item.getAttribute("data-action");
    if (target) navigateTo(target);
  });
});

const wellbeingLogMoodBtn = document.getElementById("wellbeing-log-mood-btn");
if (wellbeingLogMoodBtn) {
  wellbeingLogMoodBtn.addEventListener("click", () => navigateTo("mood-tracker"));
}

const wellbeingToCollegeHelpBtn = document.getElementById("wellbeing-to-college-help-btn");
if (wellbeingToCollegeHelpBtn) {
  wellbeingToCollegeHelpBtn.addEventListener("click", () => navigateTo("college-help"));
}

// ==================== VIEW 3: MOOD TRACKER LOGIC ====================
let selectedMoodForLogging = "Good";
const moodSelectButtons = document.querySelectorAll(".mood-select-btn");
const moodNoteInput = document.getElementById("mood-note-input");
const saveMoodEntryBtn = document.getElementById("save-mood-entry-btn");
const cancelMoodEntryBtn = document.getElementById("cancel-mood-entry-btn");
const moodSaveStatus = document.getElementById("mood-save-status");
const moodCalendarContainer = document.getElementById("mood-calendar-container");
const moodHistoryList = document.getElementById("mood-history-list");
const moodViewWeeklyBtn = document.getElementById("mood-view-weekly-btn");
const moodViewMonthlyBtn = document.getElementById("mood-view-monthly-btn");

const moodEmojiMap = {
  "Terrible": "😭",
  "Sad": "😔",
  "Okay": "😐",
  "Good": "😊",
  "Great": "🌟"
};

moodSelectButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    moodSelectButtons.forEach(b => b.classList.remove("selected"));
    btn.classList.add("selected");
    selectedMoodForLogging = btn.getAttribute("data-mood");
  });
});

if (saveMoodEntryBtn) {
  saveMoodEntryBtn.addEventListener("click", () => {
    const note = moodNoteInput ? moodNoteInput.value.trim() : "";
    const todayStr = new Date().toISOString().split("T")[0];

    state.currentMood = selectedMoodForLogging;
    state.moodHistory.unshift({
      date: todayStr,
      mood: selectedMoodForLogging,
      emoji: moodEmojiMap[selectedMoodForLogging] || "😊",
      note: note || "Routine check-in."
    });

    const wellbeingMoodTag = document.getElementById("wellbeing-current-mood-tag");
    if (wellbeingMoodTag) wellbeingMoodTag.textContent = `${selectedMoodForLogging} ${moodEmojiMap[selectedMoodForLogging]}`;

    if (moodNoteInput) moodNoteInput.value = "";
    if (moodSaveStatus) {
      moodSaveStatus.classList.remove("hidden");
      setTimeout(() => moodSaveStatus.classList.add("hidden"), 2000);
    }

    renderMoodCalendar();
    updateContextualRightPanel(state.activeView);
  });
}

if (cancelMoodEntryBtn && moodNoteInput) {
  cancelMoodEntryBtn.addEventListener("click", () => {
    moodNoteInput.value = "";
  });
}

let calendarMode = "weekly";
if (moodViewWeeklyBtn) {
  moodViewWeeklyBtn.addEventListener("click", () => {
    calendarMode = "weekly";
    moodViewWeeklyBtn.classList.add("active");
    if (moodViewMonthlyBtn) moodViewMonthlyBtn.classList.remove("active");
    renderMoodCalendar();
  });
}
if (moodViewMonthlyBtn) {
  moodViewMonthlyBtn.addEventListener("click", () => {
    calendarMode = "monthly";
    moodViewMonthlyBtn.classList.add("active");
    if (moodViewWeeklyBtn) moodViewWeeklyBtn.classList.remove("active");
    renderMoodCalendar();
  });
}

function renderMoodCalendar() {
  if (!moodCalendarContainer) return;
  moodCalendarContainer.innerHTML = "";

  const count = calendarMode === "weekly" ? 7 : 28;
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  for (let i = 0; i < count; i++) {
    const dayCell = document.createElement("div");
    dayCell.className = "cal-day-cell";
    const dayLabel = days[i % 7];
    const dateNum = (i + 1);

    const historyMatch = state.moodHistory[i % state.moodHistory.length];
    if (historyMatch && i < 5) {
      dayCell.classList.add("has-mood");
      dayCell.innerHTML = `<span>${dateNum}</span><strong>${historyMatch.emoji}</strong>`;
    } else {
      dayCell.innerHTML = `<span>${dateNum}</span><small class="text-muted">${dayLabel}</small>`;
    }
    moodCalendarContainer.appendChild(dayCell);
  }

  // Also update history list
  if (moodHistoryList) {
    moodHistoryList.innerHTML = state.moodHistory.slice(0, 5).map(item => `
      <li class="mood-history-item">
        <span>${item.emoji} <strong>${item.mood}</strong> — ${item.note}</span>
        <span class="text-muted">${item.date}</span>
      </li>
    `).join("");
  }
}

// Right panel mood quick check-in buttons
document.querySelectorAll(".mood-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".mood-btn").forEach(b => b.classList.remove("selected"));
    btn.classList.add("selected");
    const mood = btn.getAttribute("data-mood");
    state.currentMood = mood;

    const banner = document.getElementById("mood-response-banner");
    if (banner) {
      const msgs = {
        Terrible: "I'm so sorry you're hurting right now. Take a deep breath. You are safe here. 🫂",
        Sad: "It's completely okay to feel low. You don't have to put on a brave face with me. 💙",
        Okay: "Taking things one moment at a time is totally fine. I'm here to listen. 🌸",
        Good: "Glad to hear things are feeling steady! Celebrate your small wins. ✨",
        Great: "Wonderful! Cherish this energy and keep being gentle with yourself! 🌟"
      };
      banner.textContent = msgs[mood] || "Thank you for checking in.";
      banner.classList.remove("hidden");
    }
  });
});

// ==================== VIEW 4: RELAX & BREATHE LOGIC ====================
const breatheExercises = {
  box: { name: "Box Breathing", phases: [
    { text: "Breathe in...", class: "in", dur: 4000 },
    { text: "Hold gently...", class: "hold-in", dur: 4000 },
    { text: "Breathe out...", class: "out", dur: 4000 },
    { text: "Hold empty...", class: "hold-out", dur: 4000 }
  ]},
  gentle: { name: "Gentle Paced Breathing", phases: [
    { text: "Breathe in...", class: "in", dur: 4000 },
    { text: "Slow exhale...", class: "out", dur: 6000 }
  ]},
  grounding: { name: "5-4-3-2-1 Sensory Grounding", phases: [
    { text: "Notice 5 things you can see...", class: "hold-in", dur: 5000 },
    { text: "Notice 4 things you can touch...", class: "in", dur: 5000 },
    { text: "Notice 3 things you can hear...", class: "out", dur: 5000 },
    { text: "Notice 2 things you can smell...", class: "hold-out", dur: 5000 },
    { text: "Notice 1 thing you can taste...", class: "in", dur: 4000 }
  ]},
  pause: { name: "Short Calm Pause", phases: [
    { text: "Gentle inhale...", class: "in", dur: 3500 },
    { text: "Release and relax shoulders...", class: "out", dur: 4500 }
  ]}
};

const breatheTabCards = document.querySelectorAll(".breathe-tab-card");
const durationButtons = document.querySelectorAll(".duration-btn");
const soundToggleBtn = document.getElementById("sound-toggle-btn");
const pageBreatheOrb = document.getElementById("page-breathe-orb");
const pageBreatheRing = document.getElementById("page-breathe-ring");
const pageBreathePhaseText = document.getElementById("page-breathe-phase-text");
const pageBreatheGuideText = document.getElementById("page-breathe-guide-text");
const breatheStartBtn = document.getElementById("breathe-start-btn");
const breathePauseBtn = document.getElementById("breathe-pause-btn");
const breatheStopBtn = document.getElementById("breathe-stop-btn");
const breatheCompletionCard = document.getElementById("breathe-completion-card");
const openOverlayBreatheBtn = document.getElementById("open-overlay-breathe-btn");

breatheTabCards.forEach(card => {
  card.addEventListener("click", () => {
    breatheTabCards.forEach(c => c.classList.remove("active"));
    card.classList.add("active");
    state.breatheActiveExercise = card.getAttribute("data-exercise") || "box";
    stopPageBreathing();
  });
});

durationButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    durationButtons.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    state.breatheDurationMins = parseInt(btn.getAttribute("data-mins"), 10) || 1;
  });
});

if (soundToggleBtn) {
  soundToggleBtn.addEventListener("click", () => {
    state.breatheSoundEnabled = !state.breatheSoundEnabled;
    const icon = document.getElementById("sound-icon");
    const label = document.getElementById("sound-label");
    if (icon) icon.textContent = state.breatheSoundEnabled ? "🔔" : "🔈";
    if (label) label.textContent = state.breatheSoundEnabled ? "Chimes: On" : "Chimes: Off";
    if (state.breatheSoundEnabled) playGentleChime(528, 0.8);
  });
}

function startPageBreathing() {
  if (breatheCompletionCard) breatheCompletionCard.classList.add("hidden");
  if (breatheStartBtn) breatheStartBtn.classList.add("hidden");
  if (breathePauseBtn) breathePauseBtn.classList.remove("hidden");
  if (breatheStopBtn) breatheStopBtn.classList.remove("hidden");

  state.breatheIsPaused = false;
  state.breatheElapsedSec = 0;
  state.breathePhaseIndex = 0;

  runBreathingStep();
}

function runBreathingStep() {
  const ex = breatheExercises[state.breatheActiveExercise] || breatheExercises.box;
  const phase = ex.phases[state.breathePhaseIndex % ex.phases.length];

  if (pageBreathePhaseText) pageBreathePhaseText.textContent = phase.text;
  if (pageBreatheGuideText) pageBreatheGuideText.textContent = `${ex.name} in progress...`;

  if (pageBreatheOrb) {
    pageBreatheOrb.className = `page-breathe-orb ${phase.class}`;
  }

  // Audio cue
  if (phase.class === "in") playGentleChime(432, 0.9);
  else if (phase.class === "out") playGentleChime(360, 0.9);

  state.breatheTimer = setTimeout(() => {
    state.breathePhaseIndex++;
    state.breatheElapsedSec += (phase.dur / 1000);

    const targetSec = state.breatheDurationMins * 60;
    if (state.breatheElapsedSec >= targetSec) {
      completeBreathingSession();
    } else {
      runBreathingStep();
    }
  }, phase.dur);
}

function pausePageBreathing() {
  if (state.breatheIsPaused) {
    state.breatheIsPaused = false;
    if (breathePauseBtn) breathePauseBtn.querySelector("span").textContent = "Pause";
    runBreathingStep();
  } else {
    state.breatheIsPaused = true;
    if (state.breatheTimer) clearTimeout(state.breatheTimer);
    if (breathePauseBtn) breathePauseBtn.querySelector("span").textContent = "Resume";
    if (pageBreathePhaseText) pageBreathePhaseText.textContent = "Paused";
  }
}

function stopPageBreathing() {
  if (state.breatheTimer) clearTimeout(state.breatheTimer);
  state.breatheTimer = null;
  state.breatheIsPaused = false;

  if (pageBreatheOrb) pageBreatheOrb.className = "page-breathe-orb idle";
  if (pageBreathePhaseText) pageBreathePhaseText.textContent = "Ready to Begin";
  if (pageBreatheGuideText) pageBreatheGuideText.textContent = "Follow the gentle expansion and contraction of the orb.";

  if (breatheStartBtn) breatheStartBtn.classList.remove("hidden");
  if (breathePauseBtn) breathePauseBtn.classList.add("hidden");
  if (breatheStopBtn) breatheStopBtn.classList.add("hidden");
}

function completeBreathingSession() {
  stopPageBreathing();
  if (breatheCompletionCard) breatheCompletionCard.classList.remove("hidden");
  playGentleChime(528, 1.5);
}

if (breatheStartBtn) breatheStartBtn.addEventListener("click", startPageBreathing);
if (breathePauseBtn) breathePauseBtn.addEventListener("click", pausePageBreathing);
if (breatheStopBtn) breatheStopBtn.addEventListener("click", stopPageBreathing);

document.querySelectorAll(".to-chat-reflect-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const msg = btn.getAttribute("data-msg") || "I just completed a breathing session.";
    navigateTo("chat");
    sendMessage(msg, false);
  });
});

if (openOverlayBreatheBtn) {
  openOverlayBreatheBtn.addEventListener("click", () => {
    if (breathingOverlay) breathingOverlay.classList.remove("hidden");
    startBreathingCycle();
  });
}

// Quick tools action buttons
const actionBreathingBtn = document.getElementById("action-breathing-btn");
if (actionBreathingBtn) {
  actionBreathingBtn.addEventListener("click", () => navigateTo("relax-breathe"));
}

const toolCalmMusicBtn = document.getElementById("tool-calm-music-btn");
if (toolCalmMusicBtn) {
  toolCalmMusicBtn.addEventListener("click", () => {
    state.breatheSoundEnabled = true;
    playGentleChime(528, 1.5);
    alert("🎶 Playing gentle ambient chimes. Take three slow breaths and let your shoulders drop.");
  });
}

const toolAffirmationsBtn = document.getElementById("tool-affirmations-btn");
if (toolAffirmationsBtn) {
  toolAffirmationsBtn.addEventListener("click", () => {
    navigateTo("chat");
    sendMessage("Could you share a gentle, encouraging affirmation for today?", false);
  });
}

// ==================== VIEW 5: GUIDED SUPPORT LOGIC ====================
const journeysData = {
  exam: {
    title: "Exam & Assignment Pressure",
    steps: [
      {
        heading: "1. Acknowledge the Weight",
        content: "When deadlines pile up and examiners feel intimidating, your brain treats it like an emergency. Take a slow breath. You are more than a grade.",
        prompt: "What is currently the heaviest single assignment or exam on your mind?"
      },
      {
        heading: "2. Break Down the Mountain",
        content: "We don't need to finish everything right now. We only need the very next ten minutes. What is one tiny, bite-sized step you can take today?",
        prompt: "e.g., Opening one PDF, writing one sentence, or reading page 1..."
      },
      {
        heading: "3. Challenge Academic Perfectionism",
        content: "A done submission is infinitely better than a postponed masterpiece. Give yourself permission to do a rough draft first.",
        prompt: "What is a gentle thought you can tell yourself when panic strikes?"
      },
      {
        heading: "4. Compassionate Grounding",
        content: "You have weathered tough exam cycles before. Drink a sip of water, shake out your hands, and celebrate your effort.",
        prompt: "How are you feeling after reflecting on this?"
      }
    ]
  },
  hostel: {
    title: "Hostel Loneliness & Belonging",
    steps: [
      {
        heading: "1. The Illusion of Everyone Else",
        content: "Walking past rooms where groups are laughing can make you feel entirely invisible. The truth is: many students are quietly feeling just as disconnected.",
        prompt: "What feels most isolating about hostel life today?"
      },
      {
        heading: "2. Gentle Micro-Connections",
        content: "Connection doesn't require finding a best friend overnight. A simple nod in the mess, saying hi to the guard, or smiling at a hallmate builds safety.",
        prompt: "What is one small social touchpoint you feel comfortable with?"
      },
      {
        heading: "3. Making Your Room a Sanctuary",
        content: "Even in a shared or plain room, keeping cozy lighting, warm tea, or a comforting playlist makes your private space soothing rather than hollow.",
        prompt: "What brings you a little comfort in your hostel room?"
      },
      {
        heading: "4. Knowing Help is Close",
        content: "Remember that the Department of Counseling and Happiness (Building 8, Room 208) is a dedicated physical campus space where students talk about loneliness every day.",
        prompt: "Would you like to explore campus activities or chat with MannMitra?"
      }
    ]
  },
  overwhelm: {
    title: "Feeling Overwhelmed",
    steps: [
      {
        heading: "1. Stop and Drop Your Shoulders",
        content: "Right now, your sympathetic nervous system is on overdrive. Unclench your jaw. Drop your shoulders away from your ears. Feel your feet flat on the ground.",
        prompt: "Take three slow breaths. Type 'I am here' when you feel anchored."
      },
      {
        heading: "2. The Brain Dump",
        content: "Racing thoughts multiply when kept in working memory. Get them out of your head onto paper or text.",
        prompt: "List the top 3 thoughts creating noise right now..."
      },
      {
        heading: "3. One Single Step",
        content: "You only have to live this next minute. Everything else can wait. You are safe in this moment.",
        prompt: "What is one soothing thing you can do for yourself right now?"
      }
    ]
  },
  confidence: {
    title: "Self-Confidence & Comparison",
    steps: [
      {
        heading: "1. The Comparison Trap",
        content: "Comparing your behind-the-scenes struggles to other students' highlight reels will always feel unfair. Everyone has hidden doubts.",
        prompt: "Who or what has triggered self-doubt recently?"
      },
      {
        heading: "2. Recognizing Your Strengths",
        content: "You got into this university through your own resilience and ability. You belong here.",
        prompt: "Name one skill or character quality you appreciate about yourself."
      },
      {
        heading: "3. Reframe the Inner Critic",
        content: "Notice how harshly you speak to yourself. Would you speak to a friend in that tone? Speak with warmth instead.",
        prompt: "What would a kind friend say to you right now?"
      },
      {
        heading: "4. Moving Forward",
        content: "Hold your head high. You are growing every single day.",
        prompt: "What is your affirmation for tomorrow?"
      }
    ]
  },
  daily: {
    title: "Daily Evening Decompression",
    steps: [
      {
        heading: "1. Close Mental Tabs",
        content: "The day is done. Whatever was left unfinished can wait for tomorrow's energy. Acknowledge that you did your best with the energy you had.",
        prompt: "What is one thing that went okay today?"
      },
      {
        heading: "2. Release Lingering Tension",
        content: "Gently stretch your neck and roll your wrists. Release whatever stress you accumulated in lectures or study blocks.",
        prompt: "What are you ready to let go of before sleep?"
      },
      {
        heading: "3. Welcome Restful Sleep",
        content: "Give your mind permission to turn off. You deserve peaceful rest.",
        prompt: "Wish yourself a peaceful, nourishing night."
      }
    ]
  }
};

const journeysGridSection = document.getElementById("journeys-grid-section");
const activeJourneyRunner = document.getElementById("active-journey-runner");
const runnerJourneyTitle = document.getElementById("runner-journey-title");
const runnerStepCounter = document.getElementById("runner-step-counter");
const runnerProgressFill = document.getElementById("runner-progress-fill");
const runnerStepHeading = document.getElementById("runner-step-heading");
const runnerStepContent = document.getElementById("runner-step-content");
const runnerInteractionArea = document.getElementById("runner-interaction-area");
const runnerBackBtn = document.getElementById("runner-back-btn");
const runnerSkipBtn = document.getElementById("runner-skip-btn");
const runnerNextBtn = document.getElementById("runner-next-btn");
const exitJourneyBtn = document.getElementById("exit-journey-btn");

document.querySelectorAll(".start-journey-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const jKey = btn.getAttribute("data-journey");
    startJourney(jKey);
  });
});

function startJourney(jKey) {
  const data = journeysData[jKey];
  if (!data) return;

  state.activeJourney = jKey;
  state.activeJourneyStep = 0;

  if (journeysGridSection) journeysGridSection.classList.add("hidden");
  if (activeJourneyRunner) activeJourneyRunner.classList.remove("hidden");

  renderCurrentJourneyStep();
}

function renderCurrentJourneyStep() {
  const data = journeysData[state.activeJourney];
  if (!data) return;

  const totalSteps = data.steps.length;
  const current = data.steps[state.activeJourneyStep];

  if (runnerJourneyTitle) runnerJourneyTitle.textContent = data.title;
  if (runnerStepCounter) runnerStepCounter.textContent = `Step ${state.activeJourneyStep + 1} of ${totalSteps}`;
  if (runnerProgressFill) {
    const pct = ((state.activeJourneyStep + 1) / totalSteps) * 100;
    runnerProgressFill.style.width = `${pct}%`;
  }

  if (runnerStepHeading) runnerStepHeading.textContent = current.heading;
  if (runnerStepContent) runnerStepContent.textContent = current.content;

  if (runnerInteractionArea) {
    runnerInteractionArea.innerHTML = `
      <label style="font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px; display: block;">${current.prompt}</label>
      <textarea id="journey-step-input" rows="3" placeholder="Type your gentle thoughts here..."></textarea>
    `;
  }

  if (runnerBackBtn) runnerBackBtn.disabled = state.activeJourneyStep === 0;
  if (runnerNextBtn) {
    runnerNextBtn.textContent = (state.activeJourneyStep === totalSteps - 1) ? "Complete Journey ✨" : "Continue →";
  }
}

if (runnerNextBtn) {
  runnerNextBtn.addEventListener("click", () => {
    const data = journeysData[state.activeJourney];
    if (!data) return;

    if (state.activeJourneyStep < data.steps.length - 1) {
      state.activeJourneyStep++;
      renderCurrentJourneyStep();
    } else {
      // Completed!
      alert("✨ You have completed this Guided Reflection Journey! Great job taking this time for your wellbeing.");
      exitJourney();
    }
  });
}

if (runnerSkipBtn) {
  runnerSkipBtn.addEventListener("click", () => {
    const data = journeysData[state.activeJourney];
    if (!data) return;
    if (state.activeJourneyStep < data.steps.length - 1) {
      state.activeJourneyStep++;
      renderCurrentJourneyStep();
    } else {
      exitJourney();
    }
  });
}

if (runnerBackBtn) {
  runnerBackBtn.addEventListener("click", () => {
    if (state.activeJourneyStep > 0) {
      state.activeJourneyStep--;
      renderCurrentJourneyStep();
    }
  });
}

function exitJourney() {
  state.activeJourney = null;
  state.activeJourneyStep = 0;
  if (activeJourneyRunner) activeJourneyRunner.classList.add("hidden");
  if (journeysGridSection) journeysGridSection.classList.remove("hidden");
}

if (exitJourneyBtn) exitJourneyBtn.addEventListener("click", exitJourney);

// ==================== VIEW 6: COLLEGE HELP (LPU) LOGIC ====================
function filterCampusCards(category) {
  document.querySelectorAll(".campus-cat-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-cat") === category);
  });

  document.querySelectorAll(".campus-resource-card").forEach(card => {
    const cardCat = card.getAttribute("data-cat");
    if (category === "all" || cardCat === category) {
      card.classList.remove("hidden");
    } else {
      card.classList.add("hidden");
    }
  });
}

document.querySelectorAll(".campus-cat-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const cat = btn.getAttribute("data-cat") || "all";
    filterCampusCards(cat);
  });
});

// ==================== VIEW 7: GENERAL RESOURCES LIBRARY ====================
const wellnessGuides = [
  {
    id: 1,
    title: "Overcoming Assignment Paralysis",
    category: "stress",
    categoryLabel: "Stress & Study",
    readTime: "3 min read",
    summary: "A gentle strategy for breaking out of freeze mode when academic workload feels insurmountable.",
    content: `
      <h4>Why Does Freeze Mode Happen?</h4>
      <p>When deadlines pile up, our nervous system perceives an emergency. Pushing harder often triggers deeper exhaustion. Instead, lower the bar intentionally.</p>
      <h4>Actionable Reset Protocol:</h4>
      <ul>
        <li><strong>The 5-Minute Rule:</strong> Commit to opening the file and writing for just 5 minutes. You can stop after that.</li>
        <li><strong>Micro-Chunking:</strong> Don't write 'Finish Research Paper'. Write 'Write 2 bullet points of introduction'.</li>
        <li><strong>Body Warm-up:</strong> Shake out your hands, take a glass of water, and change your seated posture.</li>
      </ul>
    `
  },
  {
    id: 2,
    title: "Navigating Hostel Roommate Friction",
    category: "relationships",
    categoryLabel: "Relationships",
    readTime: "4 min read",
    summary: "Clear, non-confrontational boundary setting for sharing tight university living quarters.",
    content: `
      <h4>Living in Close Quarters</h4>
      <p>Hostel living means two or three students with totally different sleep schedules and hygiene habits sharing 120 square feet. Friction is inevitable, but escalating fights are not.</p>
      <h4>Direct Communication Tips:</h4>
      <ul>
        <li>Use 'I' statements: 'I find it hard to sleep with the light on past 11 PM' instead of 'You always keep the lights on'.</li>
        <li>Agree on quiet hours during exam weeks in advance.</li>
        <li>Have dedicated noise-cancelling headphones or foam earplugs as a personal boundary tool.</li>
      </ul>
    `
  },
  {
    id: 3,
    title: "The 2-Minute Campus Grounding Scan",
    category: "mindfulness",
    categoryLabel: "Mindfulness",
    readTime: "2 min read",
    summary: "A quick somatic technique you can do between lectures or in the library to halt racing thoughts.",
    content: `
      <h4>Grounding on Campus</h4>
      <p>You can do this while sitting on a campus bench or at your study desk without anyone noticing.</p>
      <ul>
        <li>Press your feet firmly into the floor. Feel the solidity of the earth beneath you.</li>
        <li>Notice three distinct ambient sounds—a fan whirring, footsteps in the corridor, distant traffic.</li>
        <li>Inhale for 4 seconds, exhale for 6 seconds. Remind yourself: 'Right here, right now, I am safe.'</li>
      </ul>
    `
  },
  {
    id: 4,
    title: "The Digital Sunset: Protecting Sleep",
    category: "sleep",
    categoryLabel: "Sleep & Routine",
    readTime: "4 min read",
    summary: "How evening screen exposure scrambles melatonin and strategies to wind down peacefully.",
    content: `
      <h4>Blue Light and Melatonin</h4>
      <p>Staring at your phone in bed tricks the pineal gland into thinking it's noon, delaying deep restorative sleep.</p>
      <h4>Evening Habits:</h4>
      <ul>
        <li>Set night mode / amber filter on your phone after 9 PM.</li>
        <li>Keep an offline book or calming podcast for bed instead of endless social media doom-scrolling.</li>
        <li>Keep your room temperature comfortable and air well-circulated.</li>
      </ul>
    `
  },
  {
    id: 5,
    title: "The Brain-Dump Journaling Protocol",
    category: "journaling",
    categoryLabel: "Journaling",
    readTime: "3 min read",
    summary: "Clearing mental clutter by externalizing unorganized thoughts onto paper.",
    content: `
      <h4>Externalizing Your Internal Monologue</h4>
      <p>Your working memory is only meant for processing, not for storing 50 nagging to-do items and worries.</p>
      <ul>
        <li>Grab a blank sheet of paper and write everything down without grammar rules or neatness.</li>
        <li>Sort items into: 'In my control today', 'Things to address tomorrow', and 'Things out of my control'.</li>
        <li>Notice the physical relief when your thoughts are outside of your skull.</li>
      </ul>
    `
  },
  {
    id: 6,
    title: "When to Seek Professional Support",
    category: "support",
    categoryLabel: "Help & Support",
    readTime: "4 min read",
    summary: "Recognizing red flags and understanding that reaching out for counseling is a sign of wisdom.",
    content: `
      <h4>You Don't Have to Hit Rock Bottom First</h4>
      <p>Therapy and student counseling are proactive health tools, not just for extreme crises.</p>
      <h4>Signals It's Time to Reach Out:</h4>
      <ul>
        <li>Persistent low mood, numbness, or inability to enjoy things for more than two weeks.</li>
        <li>Sleep disturbances that disrupt your ability to attend lectures or eat nutritious meals.</li>
        <li>Severe panic or racing heart that prevents you from entering exam halls.</li>
      </ul>
      <p>At LPU, you can walk directly into Building 8, Room 208 for confidential guidance.</p>
    `
  }
];

const libCardsGrid = document.getElementById("lib-cards-grid");
const libSearchInput = document.getElementById("lib-search-input");
const libCategoryButtons = document.querySelectorAll(".lib-cat-btn");
const libDetailModal = document.getElementById("lib-detail-modal");
const closeLibDetailBtn = document.getElementById("close-lib-detail-btn");
const detailCategoryTag = document.getElementById("detail-category-tag");
const detailTitle = document.getElementById("detail-title");
const detailReadTime = document.getElementById("detail-read-time");
const detailContent = document.getElementById("detail-content");
const discussGuideWithMmBtn = document.getElementById("discuss-guide-with-mm-btn");
const bookmarkGuideBtn = document.getElementById("bookmark-guide-btn");

let activeLibCategory = "all";
let currentDetailGuide = null;

function renderResourcesLibrary() {
  if (!libCardsGrid) return;
  const query = libSearchInput ? libSearchInput.value.toLowerCase().trim() : "";

  const filtered = wellnessGuides.filter(g => {
    const matchesCat = activeLibCategory === "all" || g.category === activeLibCategory;
    const matchesQuery = !query || g.title.toLowerCase().includes(query) || g.summary.toLowerCase().includes(query);
    return matchesCat && matchesQuery;
  });

  if (filtered.length === 0) {
    libCardsGrid.innerHTML = `
      <div class="clean-empty-state" style="grid-column: 1 / -1; padding: 40px 20px;">
        <span class="empty-icon">🔍</span>
        <p>No guides match your search.</p>
        <small>Try a broader keyword or switch categories.</small>
      </div>
    `;
    return;
  }

  libCardsGrid.innerHTML = filtered.map(g => {
    const isBookmarked = state.bookmarkedGuides.has(g.id);
    return `
      <div class="lib-article-card" data-guide-id="${g.id}">
        <div>
          <div class="lib-card-top">
            <span class="lib-tag">${g.categoryLabel}</span>
            <button class="lib-bookmark-btn ${isBookmarked ? 'active' : ''}" data-id="${g.id}" title="Bookmark Guide">
              ${isBookmarked ? '★' : '☆'}
            </button>
          </div>
          <h4>${g.title}</h4>
          <p>${g.summary}</p>
        </div>
        <div class="lib-card-footer">
          <span class="read-time">${g.readTime}</span>
          <button class="btn-outline-pill small-btn open-guide-btn" data-id="${g.id}">Read Guide →</button>
        </div>
      </div>
    `;
  }).join("");

  // Bind guide click events
  document.querySelectorAll(".open-guide-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const gid = parseInt(btn.getAttribute("data-id"), 10);
      openGuideDetail(gid);
    });
  });

  document.querySelectorAll(".lib-bookmark-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const gid = parseInt(btn.getAttribute("data-id"), 10);
      if (state.bookmarkedGuides.has(gid)) {
        state.bookmarkedGuides.delete(gid);
      } else {
        state.bookmarkedGuides.add(gid);
      }
      renderResourcesLibrary();
      updateContextualRightPanel("resources-library");
    });
  });
}

function openGuideDetail(guideId) {
  const guide = wellnessGuides.find(g => g.id === guideId);
  if (!guide || !libDetailModal) return;

  currentDetailGuide = guide;
  if (detailCategoryTag) detailCategoryTag.textContent = guide.categoryLabel;
  if (detailTitle) detailTitle.textContent = guide.title;
  if (detailReadTime) detailReadTime.textContent = `📖 ${guide.readTime}`;
  if (detailContent) detailContent.innerHTML = guide.content;

  if (bookmarkGuideBtn) {
    bookmarkGuideBtn.textContent = state.bookmarkedGuides.has(guide.id) ? "★ Bookmarked" : "☆ Bookmark Guide";
  }

  libDetailModal.classList.remove("hidden");
}

if (closeLibDetailBtn && libDetailModal) {
  closeLibDetailBtn.addEventListener("click", () => {
    libDetailModal.classList.add("hidden");
  });
}

if (bookmarkGuideBtn) {
  bookmarkGuideBtn.addEventListener("click", () => {
    if (!currentDetailGuide) return;
    if (state.bookmarkedGuides.has(currentDetailGuide.id)) {
      state.bookmarkedGuides.delete(currentDetailGuide.id);
      bookmarkGuideBtn.textContent = "☆ Bookmark Guide";
    } else {
      state.bookmarkedGuides.add(currentDetailGuide.id);
      bookmarkGuideBtn.textContent = "★ Bookmarked";
    }
    renderResourcesLibrary();
  });
}

if (discussGuideWithMmBtn) {
  discussGuideWithMmBtn.addEventListener("click", () => {
    if (!currentDetailGuide) return;
    libDetailModal.classList.add("hidden");
    navigateTo("chat");
    sendMessage(`I was reading the guide "${currentDetailGuide.title}". Can we talk about how to apply it in my routine?`, false);
  });
}

libCategoryButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    libCategoryButtons.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    activeLibCategory = btn.getAttribute("data-category") || "all";
    renderResourcesLibrary();
  });
});

if (libSearchInput) {
  libSearchInput.addEventListener("input", () => renderResourcesLibrary());
}

// ==================== VIEW 9: SETTINGS LOGIC ====================
const settingsDisplayName = document.getElementById("settings-display-name");
const saveDisplayNameBtn = document.getElementById("save-display-name-btn");
const themeButtons = document.querySelectorAll(".theme-opt-btn");
const accentButtons = document.querySelectorAll(".accent-opt-btn");
const autoGreetingToggle = document.getElementById("settings-auto-greeting-toggle");
const speechRateInput = document.getElementById("settings-speech-rate");
const speechRateVal = document.getElementById("speech-rate-val");
const voiceLocaleSelect = document.getElementById("settings-voice-locale");
const reducedMotionToggle = document.getElementById("settings-reduced-motion-toggle");
const fontSizeButtons = document.querySelectorAll(".font-opt-btn");
const clearDemoDataBtn = document.getElementById("clear-demo-data-btn");
const clearDataStatus = document.getElementById("clear-data-status");

if (saveDisplayNameBtn && settingsDisplayName) {
  saveDisplayNameBtn.addEventListener("click", () => {
    const val = settingsDisplayName.value.trim();
    if (val) {
      updateUserNameDisplays(val);
      alert("Display name updated!");
    }
  });
}

themeButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    themeButtons.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const theme = btn.getAttribute("data-theme") || "light";
    document.body.setAttribute("data-theme", theme);
    state.settings.theme = theme;
  });
});

accentButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    accentButtons.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    state.settings.accent = btn.getAttribute("data-accent");
  });
});

if (autoGreetingToggle) {
  autoGreetingToggle.addEventListener("change", (e) => {
    state.settings.autoGreeting = e.target.checked;
  });
}

if (speechRateInput && speechRateVal) {
  speechRateInput.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value);
    state.settings.speechRate = val;
    speechRateVal.textContent = `${val.toFixed(2)}x`;
  });
}

if (voiceLocaleSelect) {
  voiceLocaleSelect.addEventListener("change", (e) => {
    state.settings.voiceLocale = e.target.value;
  });
}

if (reducedMotionToggle) {
  reducedMotionToggle.addEventListener("change", (e) => {
    document.body.classList.toggle("reduced-motion", e.target.checked);
    state.settings.reducedMotion = e.target.checked;
  });
}

fontSizeButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    fontSizeButtons.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const sz = btn.getAttribute("data-size");
    document.body.classList.remove("font-large", "font-xlarge");
    if (sz === "large") document.body.classList.add("font-large");
    if (sz === "xlarge") document.body.classList.add("font-xlarge");
    state.settings.fontSize = sz;
  });
});

if (clearDemoDataBtn) {
  clearDemoDataBtn.addEventListener("click", () => {
    if (confirm("Clear local prototype reflections, mood entries, and chat history?")) {
      conversationHistory = [];
      state.moodHistory = [];
      state.bookmarkedGuides.clear();
      renderMoodCalendar();
      renderResourcesLibrary();
      if (clearDataStatus) {
        clearDataStatus.classList.remove("hidden");
        setTimeout(() => clearDataStatus.classList.add("hidden"), 2000);
      }
    }
  });
}

// ==================== VOICE ORB OVERLAY (PRESERVED) ====================
let orbAudioContext = null;
let orbAnalyser = null;
let orbMicStream = null;
let orbVolumeRaf = null;

function setOrbState(orbState, statusText) {
  if (!orbCircle) return;
  orbCircle.classList.remove("idle", "listening", "thinking", "speaking");
  if (orbState) orbCircle.classList.add(orbState);
  if (orbStatus) orbStatus.textContent = statusText;

  const center = document.getElementById("orb-center-container");
  const isSonar = orbState === "listening" || orbState === "speaking";
  if (center) center.classList.toggle("sonar", isSonar);

  if (orbWaveform) {
    orbWaveform.classList.toggle("active", isSonar);
  }
}

async function startOrbAudioReactive() {
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    orbMicStream = stream;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    orbAudioContext = new AC();
    const src = orbAudioContext.createMediaStreamSource(stream);
    orbAnalyser = orbAudioContext.createAnalyser();
    orbAnalyser.fftSize = 256;
    src.connect(orbAnalyser);

    const data = new Uint8Array(orbAnalyser.frequencyBinCount);
    function tick() {
      if (!orbCircle || !orbCircle.classList.contains("listening")) return;
      orbAnalyser.getByteFrequencyData(data);
      let sum = 0;
      for (let i = 0; i < data.length; i++) sum += data[i];
      const avg = sum / data.length;
      const targetScale = 1.02 + Math.min(avg / 90, 1) * 0.12;
      orbCircle.style.transform = `scale(${targetScale.toFixed(3)})`;
      orbVolumeRaf = requestAnimationFrame(tick);
    }
    tick();
  } catch (_) {}
}

function stopOrbAudioReactive() {
  if (orbVolumeRaf) { cancelAnimationFrame(orbVolumeRaf); orbVolumeRaf = null; }
  if (orbMicStream) {
    orbMicStream.getTracks().forEach(t => t.stop());
    orbMicStream = null;
  }
  if (orbAudioContext && orbAudioContext.state !== "closed") {
    try { orbAudioContext.close(); } catch (_) {}
    orbAudioContext = null;
  }
  if (orbCircle) orbCircle.style.transform = "";
}

function openOrbMode() {
  if (orbOverlay) orbOverlay.classList.remove("hidden");
  setOrbState("idle", "Tap to talk");
  if (orbCaption) orbCaption.textContent = "Speak freely, I'm here for you.";
}

function closeOrbMode() {
  if (orbOverlay) orbOverlay.classList.add("hidden");
  stopOrbAudioReactive();
  window.speechSynthesis.cancel();
}

function orbListen() {
  if (!SpeechRecognition) {
    setOrbState("idle", "Voice not supported in this browser");
    return;
  }
  setOrbState("listening", "I'm listening...");
  if (orbCaption) orbCaption.textContent = "Take your time.";
  startOrbAudioReactive();

  const orbRec = new SpeechRecognition();
  orbRec.lang = state.settings.voiceLocale || "en-IN";
  orbRec.interimResults = false;

  orbRec.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    if (orbCaption) orbCaption.textContent = `You: "${transcript}"`;
    setOrbState("thinking", "Thinking...");

    sendMessage(transcript, false, (data) => {
      if (!data) {
        setOrbState("idle", "Tap to talk");
        return;
      }
      if (orbCaption) orbCaption.textContent = data.reply;
      setOrbState("speaking", "Speaking...");
      speak(data.reply, () => {
        setOrbState("idle", "Tap to talk");
        if (orbCaption) orbCaption.textContent = "Speak freely, I'm here for you.";
      });
    });
  };

  orbRec.onerror = () => { setOrbState("idle", "Tap to talk"); };
  orbRec.onend = () => {
    if (orbCircle && orbCircle.classList.contains("listening")) {
      setOrbState("idle", "Tap to talk");
    }
  };

  try { orbRec.start(); } catch (_) { setOrbState("idle", "Tap to talk"); }
}

if (orbCloseBtn) orbCloseBtn.addEventListener("click", closeOrbMode);
if (orbStopBtn) orbStopBtn.addEventListener("click", closeOrbMode);
if (orbCircle) orbCircle.addEventListener("click", orbListen);
if (dashVoiceBtn) dashVoiceBtn.addEventListener("click", openOrbMode);

// ==================== GUIDED BREATHING OVERLAY (PRESERVED) ====================
let breathingCycle = null;
const BREATHING_CIRCUMFERENCE = 2 * Math.PI * 108;

function startBreathingCycle() {
  if (breathingCycle !== null) return;
  const phases = [
    { status: "Breathe in...", animation: "in", duration: 4000 },
    { status: "Hold...", animation: "hold-in", duration: 4000 },
    { status: "Breathe out...", animation: "out", duration: 4000 },
    { status: "Hold...", animation: "hold-out", duration: 4000 }
  ];
  let pIndex = 0;

  function runPhase() {
    const p = phases[pIndex % phases.length];
    if (breathingStatus) breathingStatus.textContent = p.status;
    if (breathingCircle) {
      breathingCircle.classList.remove("in", "hold-in", "out", "hold-out");
      void breathingCircle.offsetWidth;
      breathingCircle.classList.add(p.animation);
    }
    pIndex++;
    breathingCycle = setTimeout(runPhase, p.duration);
  }
  runPhase();
}

function stopBreathingCycle() {
  if (breathingCycle !== null) {
    clearTimeout(breathingCycle);
    breathingCycle = null;
  }
  if (breathingCircle) breathingCircle.classList.remove("in", "hold-in", "out", "hold-out");
}

if (breathingCloseBtn) {
  breathingCloseBtn.addEventListener("click", () => {
    stopBreathingCycle();
    if (breathingOverlay) breathingOverlay.classList.add("hidden");
  });
}

// Initial initialization
renderMoodCalendar();
renderResourcesLibrary();
