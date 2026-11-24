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
  currentMood: null,
  moodEntries: [],
  sessionActivities: [],
  sessionStats: {
    mindfulMinutes: 0,
    breathingSessionsCompleted: 0,
    journeysCompleted: 0,
  },
  get moodHistory() { return this.moodEntries; },
  set moodHistory(val) { this.moodEntries = val; },
  completedPathways: new Set(),
  journeyUserInputs: {},
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
const loginErrorBanner = document.getElementById("login-error-banner");
const loginErrorText = document.getElementById("login-error-text");
const loginBtnText = document.getElementById("login-btn-text");
const loginSpinner = document.getElementById("login-spinner");
const rememberMeCheckbox = document.getElementById("remember-me");

// Greeting Elements
const greetingHeading = document.getElementById("greeting-heading");
const greetingSubtitle = document.getElementById("greeting-subtitle");
const greetingContinueBtn = document.getElementById("greeting-continue-btn");
const greetingSkipBtn = document.getElementById("greeting-skip-btn");
const hearGreetingBtn = document.getElementById("hear-greeting-btn");
const chatHearGreetingBtn = document.getElementById("chat-hear-greeting-btn");

// Profile & Logout Elements
const headerProfilePill = document.getElementById("header-profile-pill");
const headerProfileDropdown = document.getElementById("header-profile-dropdown");
const profileViewSettingsBtn = document.getElementById("profile-view-settings-btn");
const profileLogoutBtn = document.getElementById("profile-logout-btn");
const logoutConfirmModal = document.getElementById("logout-confirm-modal");
const logoutCancelBtn = document.getElementById("logout-cancel-btn");
const logoutConfirmBtn = document.getElementById("logout-confirm-btn");
const profileDropdownName = document.getElementById("profile-dropdown-name");
const profileDropdownRole = document.getElementById("profile-dropdown-role");
const profileDropdownInitial = document.getElementById("profile-dropdown-initial");

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
  "calm-music": document.getElementById("view-calm-music"),
  "mindful-games": document.getElementById("view-mindful-games"),
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
  "calm-music": "Calm Music & Soundscapes",
  "mindful-games": "Mindful Games",
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
  if (viewKey === "mood-tracker") renderMoodTrackerView();
  if (viewKey === "wellbeing") renderWellbeingView();
  if (viewKey === "my-journey") renderJourneyView();
  if (viewKey === "guided-support") renderGuidedSupportView();
  if (viewKey === "resources-library") renderResourcesLibrary();
  if (viewKey === "college-help") filterCampusCards();
  if (viewKey === "calm-music") renderCalmMusicView();
  if (viewKey === "mindful-games") renderMindfulGamesView();
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
    case "calm-music":
      panelSubtext.textContent = "Acoustic sanctuary to quiet racing thoughts and restore inner peace.";
      break;
    case "mindful-games":
      panelSubtext.textContent = "Gentle, pressure-free micro-games to reset and refresh your mind.";
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

  if (headerUserName) headerUserName.textContent = `Hi, ${display}`;
  if (sidebarDisplayName) sidebarDisplayName.textContent = display;
  if (headerUserInitial && !headerUserInitial.querySelector("svg")) {
    headerUserInitial.textContent = initial;
  }
  if (sidebarUserInitial) sidebarUserInitial.textContent = initial;

  if (profileDropdownName) profileDropdownName.textContent = display;
  if (profileDropdownRole) profileDropdownRole.textContent = state.isGuest ? "Guest Sanctuary Mode" : "Student (LPU Sanctuary)";
  if (profileDropdownInitial) profileDropdownInitial.textContent = initial;

  const chatHeroGreeting = document.getElementById("chat-hero-greeting");
  if (chatHeroGreeting) chatHeroGreeting.textContent = `Welcome, ${display}! I'm MannMitra 👋`;

  const chatInitial = document.getElementById("chat-initial-message");
  if (chatInitial) chatInitial.textContent = "Hey! I'm here. What's on your mind today?";

  const panelGreeting = document.getElementById("panel-greeting-user");
  if (panelGreeting) panelGreeting.textContent = `Namaste, ${display} 🙏`;

  const sdn = document.getElementById("settings-display-name");
  if (sdn) sdn.value = display;
}

function handleLogin(isGuestMode = false) {
  if (loginErrorBanner) loginErrorBanner.classList.add("hidden");

  state.isGuest = isGuestMode;
  const rawEmail = loginEmailInput ? loginEmailInput.value.trim() : "";
  const rawPassword = loginPasswordInput ? loginPasswordInput.value.trim() : "";

  // Validation when not in guest mode
  if (!isGuestMode) {
    if (!rawEmail) {
      if (loginErrorBanner && loginErrorText) {
        loginErrorText.textContent = "Please enter your Student ID or Email to sign in, or click 'Continue as Guest'.";
        loginErrorBanner.classList.remove("hidden");
      }
      if (loginEmailInput) loginEmailInput.focus();
      return;
    }
    if (!rawPassword) {
      if (loginErrorBanner && loginErrorText) {
        loginErrorText.textContent = "Please enter your password to sign in.";
        loginErrorBanner.classList.remove("hidden");
      }
      if (loginPasswordInput) loginPasswordInput.focus();
      return;
    }
  }

  // Remember Me: Store only non-sensitive email/ID (never passwords or tokens)
  if (!isGuestMode && rememberMeCheckbox && rememberMeCheckbox.checked) {
    try {
      localStorage.setItem("mannmitra_remembered_id", rawEmail);
    } catch (_) {}
  } else {
    try {
      localStorage.removeItem("mannmitra_remembered_id");
    } catch (_) {}
  }

  let name = "Vyankatesh";
  if (isGuestMode || !rawEmail) {
    name = isGuestMode ? "Friend" : "Vyankatesh";
  } else if (rawEmail.includes("@")) {
    name = rawEmail.split("@")[0];
    name = name.charAt(0).toUpperCase() + name.slice(1);
  } else {
    name = rawEmail;
  }

  // Visual loading state & prevention of repeated clicks
  if (startChatBtn) {
    startChatBtn.disabled = true;
    if (loginBtnText) loginBtnText.textContent = "Entering Sanctuary...";
    if (loginSpinner) loginSpinner.classList.remove("hidden");
  }

  setTimeout(() => {
    if (startChatBtn) {
      startChatBtn.disabled = false;
      if (loginBtnText) loginBtnText.textContent = "Sign In to Sanctuary";
      if (loginSpinner) loginSpinner.classList.add("hidden");
    }

    updateUserNameDisplays(name);

    // Transition to Greeting Overlay
    if (loginView) loginView.classList.add("hidden");
    if (greetingOverlay) greetingOverlay.classList.remove("hidden");

    // Short greeting: "Hello, {user_name}! How are you today?" or "Hello! How are you today?"
    const shortGreeting = (isGuestMode || !state.currentUserName || state.currentUserName === "Friend")
      ? "Hello! How are you today?"
      : `Hello, ${state.currentUserName}! How are you today?`;

    if (greetingHeading) greetingHeading.textContent = shortGreeting;
    if (greetingSubtitle) greetingSubtitle.textContent = "Take a moment for yourself. I'm here to listen.";

    // Automatic spoken greeting if preference enabled
    if (state.settings.autoGreeting && !state.greetingSpoken) {
      state.greetingSpoken = true;
      setTimeout(() => {
        speak(shortGreeting);
      }, 350);
    }
  }, isGuestMode ? 40 : 250);
}

// Clear error banner on input change
if (loginEmailInput) {
  loginEmailInput.addEventListener("input", () => {
    if (loginErrorBanner) loginErrorBanner.classList.add("hidden");
  });
}
if (loginPasswordInput) {
  loginPasswordInput.addEventListener("input", () => {
    if (loginErrorBanner) loginErrorBanner.classList.add("hidden");
  });
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
let sessionEpoch = 0;
let requestCounter = 0;
const pendingRequests = new Map();

function createStatusIndicator(status, requestId) {
  const div = document.createElement("div");
  div.className = "message bot dynamic-chat-msg";
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
  div.className = `message ${sender} dynamic-chat-msg`;

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

  const myEpoch = sessionEpoch;
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

    if (myEpoch !== sessionEpoch) {
      removeStatusIndicator(requestId);
      return;
    }

    if (!res.ok) throw new Error("Backend error");
    const data = await res.json();

    if (myEpoch !== sessionEpoch) {
      removeStatusIndicator(requestId);
      return;
    }

    removeStatusIndicator(requestId);
    const typingIndicator = createStatusIndicator("MM is typing...", requestId);
    pendingRequests.set(requestId, { indicatorEl: typingIndicator, aborted: false });

    const delay = Math.min(150 + Math.floor((data.reply || "").length / 80) * 40, 240);
    await new Promise(r => setTimeout(r, delay));

    removeStatusIndicator(requestId);
    if (myEpoch !== sessionEpoch) return;

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
    if (myEpoch !== sessionEpoch) return;
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

// ==================== VIEW 2 & 3: SHARED WELLBEING & MOOD ENGINE (PHASE 2C) ====================
const intentionChips = document.querySelectorAll(".intention-chip");
const customIntentionInput = document.getElementById("custom-intention-input");
const saveIntentionBtn = document.getElementById("save-intention-btn");

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

let lastMoodLogTime = 0;
let lastMoodLogVal = null;

function recordMoodEntry(mood, note = "", source = "direct") {
  if (!mood) return null;

  const now = Date.now();
  // Prevent duplicate clicks within 800ms for identical mood
  if (lastMoodLogVal === mood && (now - lastMoodLogTime) < 800) {
    return null;
  }
  lastMoodLogTime = now;
  lastMoodLogVal = mood;

  const dateObj = new Date(now);
  const dateStr = dateObj.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  const timeStr = dateObj.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });

  const entry = {
    id: "mood_" + now + "_" + Math.random().toString(36).substring(2, 7),
    mood: mood,
    emoji: moodEmojiMap[mood] || "😊",
    timestamp: now,
    dateStr: dateStr,
    timeStr: timeStr,
    note: note && note.trim() ? note.trim() : (source === "quick" ? "Quick check-in." : "Routine check-in.")
  };

  state.currentMood = mood;
  state.moodEntries.unshift(entry);

  // Record into session activity
  logSessionActivity("checkin", `Mood Check-in: ${mood} ${entry.emoji}`, entry.note, now);

  // Synchronize all views immediately
  renderAllWellbeingViews();

  return entry;
}

function logSessionActivity(type, title, detail, timestamp = Date.now()) {
  const dateObj = new Date(timestamp);
  const timeStr = dateObj.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  const dateStr = dateObj.toLocaleDateString("en-US", { month: "short", day: "numeric" });

  const act = {
    id: "act_" + timestamp + "_" + Math.random().toString(36).substring(2, 6),
    type: type, // 'checkin' | 'breathe' | 'journey' | 'intention'
    title: title,
    detail: detail,
    timestamp: timestamp,
    timeStr: timeStr,
    dateStr: dateStr,
  };

  state.sessionActivities.unshift(act);
}

function renderAllWellbeingViews() {
  renderRightPanelMood();
  renderRightPanelJourney();
  renderWellbeingView();
  renderMoodTrackerView();
  renderJourneyView();
  if (typeof renderTodaysThought === "function") renderTodaysThought();
}

function renderRightPanelMood() {
  document.querySelectorAll(".mood-btn").forEach(btn => {
    btn.classList.toggle("selected", btn.getAttribute("data-mood") === state.currentMood);
  });
}

function renderRightPanelJourney() {
  const levelPill = document.getElementById("right-panel-journey-level");
  const xpFill = document.getElementById("right-panel-xp-fill");
  const xpText = document.getElementById("right-panel-xp-text");

  const actCount = state.sessionActivities.length;
  const mindfulMins = state.sessionStats.mindfulMinutes;

  let level = 1;
  let targetXp = 100;
  if (actCount >= 4) {
    level = 3;
    targetXp = 300;
  } else if (actCount >= 2) {
    level = 2;
    targetXp = 200;
  }

  const currentXp = Math.min(targetXp, (actCount * 40) + (mindfulMins * 20));
  const pct = targetXp > 0 ? Math.round((currentXp / targetXp) * 100) : 0;

  if (levelPill) levelPill.textContent = `Level ${level}`;
  if (xpFill) xpFill.style.width = `${pct}%`;
  if (xpText) xpText.textContent = `${currentXp} / ${targetXp} XP`;

  // Badges in right panel
  const bCheckin = document.getElementById("rp-badge-checkin");
  const bBreathe = document.getElementById("rp-badge-breathe");
  const bReflect = document.getElementById("rp-badge-reflect");
  const bFocus = document.getElementById("rp-badge-focus");

  if (bCheckin) bCheckin.className = `journey-badge-item ${state.moodEntries.length > 0 ? "unlocked" : "in-progress"}`;
  if (bBreathe) bBreathe.className = `journey-badge-item ${state.sessionStats.breathingSessionsCompleted > 0 ? "unlocked" : "in-progress"}`;
  if (bReflect) bReflect.className = `journey-badge-item ${state.sessionStats.journeysCompleted > 0 ? "unlocked" : "in-progress"}`;
  if (bFocus) bFocus.className = `journey-badge-item ${state.sessionActivities.length >= 3 ? "unlocked" : "in-progress"}`;
}

function renderWellbeingView() {
  // 1. Check-in status & count
  const checkinCount = document.getElementById("wellbeing-checkin-count");
  const checkinStatus = document.getElementById("wellbeing-checkin-status");
  const checkinLabel = document.getElementById("wellbeing-checkin-label");

  const totalEntries = state.moodEntries.length;
  if (checkinCount) checkinCount.textContent = totalEntries;
  if (checkinStatus) {
    if (totalEntries > 0) {
      checkinStatus.textContent = "Active Today";
      checkinStatus.className = "status-pill-green";
    } else {
      checkinStatus.textContent = "Not Yet Checked In";
      checkinStatus.className = "status-pill-muted";
    }
  }
  if (checkinLabel) {
    checkinLabel.textContent = totalEntries === 1 ? "Check-in this session" : "Check-ins this session";
  }

  // 2. Current Mood
  const moodTag = document.getElementById("wellbeing-current-mood-tag");
  if (moodTag) {
    if (state.currentMood) {
      moodTag.textContent = `${state.currentMood} ${moodEmojiMap[state.currentMood] || "😊"}`;
      moodTag.className = "status-pill-purple";
    } else {
      moodTag.textContent = "Not logged yet";
      moodTag.className = "status-pill-muted";
    }
  }

  // 3. Recent Reflections
  const reflectionsEmpty = document.getElementById("reflections-empty-state");
  const reflectionsList = document.getElementById("wellbeing-reflections-list");
  const validReflections = state.moodEntries.filter(e => e.note && e.note !== "Routine check-in." && e.note !== "Quick check-in.");
  const journeyReflections = state.sessionActivities.filter(a => a.type === "journey");

  if (reflectionsEmpty && reflectionsList) {
    if (validReflections.length === 0 && journeyReflections.length === 0) {
      reflectionsEmpty.classList.remove("hidden");
      reflectionsList.classList.add("hidden");
      reflectionsList.innerHTML = "";
    } else {
      reflectionsEmpty.classList.add("hidden");
      reflectionsList.classList.remove("hidden");
      const items = [
        ...validReflections.map(r => `
          <div class="reflection-item">
            <div>
              <strong>${r.emoji} Mood Note (${r.mood})</strong>
              <span>${r.note}</span>
            </div>
            <small>${r.timeStr || r.dateStr}</small>
          </div>
        `),
        ...journeyReflections.map(j => `
          <div class="reflection-item">
            <div>
              <strong>🧭 ${j.title}</strong>
              <span>${j.detail}</span>
            </div>
            <small>${j.timeStr}</small>
          </div>
        `)
      ];
      reflectionsList.innerHTML = items.slice(0, 4).join("");
    }
  }

  // 4. Weekly Snapshot Dots
  const weeklyDotsContainer = document.getElementById("wellbeing-weekly-dots");
  if (weeklyDotsContainer) {
    const todayIndex = (new Date().getDay() + 6) % 7; // 0=Mon, 6=Sun
    const dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    weeklyDotsContainer.innerHTML = dayNames.map((day, idx) => {
      let dotClass = "";
      if (idx === todayIndex) {
        dotClass = totalEntries > 0 ? "done" : "active";
      }
      return `<div class="day-dot-item"><span class="dot ${dotClass}"></span><small>${day}</small></div>`;
    }).join("");
  }
}

function renderMoodTrackerView() {
  renderMoodCalendar();
  renderMoodHistoryList();
  renderMoodDistribution();

  if (moodSelectButtons) {
    moodSelectButtons.forEach(btn => {
      btn.classList.toggle("selected", btn.getAttribute("data-mood") === (selectedMoodForLogging || state.currentMood));
    });
  }
}

function renderMoodDistribution() {
  const container = document.getElementById("mood-distribution-bars");
  if (!container) return;

  const total = state.moodEntries.length;
  if (total === 0) {
    container.innerHTML = `
      <div class="clean-empty-state" style="padding: 16px 8px;">
        <span class="empty-icon">📊</span>
        <p>No mood entries recorded yet in this session.</p>
        <small>Select your feeling above or from the side panel to start tracking distribution.</small>
      </div>
    `;
    return;
  }

  const counts = { Great: 0, Good: 0, Okay: 0, Sad: 0, Terrible: 0 };
  state.moodEntries.forEach(entry => {
    if (counts[entry.mood] !== undefined) {
      counts[entry.mood]++;
    }
  });

  const moodsList = [
    { key: "Great", label: "🌟 Great", class: "great" },
    { key: "Good", label: "😊 Good", class: "good" },
    { key: "Okay", label: "😐 Okay", class: "okay" },
    { key: "Sad", label: "😔 Sad", class: "sad" },
    { key: "Terrible", label: "😭 Terrible", class: "terrible" }
  ];

  container.innerHTML = moodsList.map(m => {
    const count = counts[m.key];
    const pct = Math.round((count / total) * 100);
    return `
      <div class="dist-row">
        <span>${m.label}</span>
        <div class="bar-track"><div class="bar-fill ${m.class}" style="width: ${pct}%;"></div></div>
        <span>${pct}%</span>
      </div>
    `;
  }).join("");
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

  const now = new Date();
  const count = calendarMode === "weekly" ? 7 : 28;
  const daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  const entryDateMap = {};
  state.moodEntries.forEach(entry => {
    const dStr = new Date(entry.timestamp).toDateString();
    if (!entryDateMap[dStr]) {
      entryDateMap[dStr] = entry;
    }
  });

  for (let i = count - 1; i >= 0; i--) {
    const targetDate = new Date(now);
    targetDate.setDate(now.getDate() - i);
    const dayLabel = daysOfWeek[targetDate.getDay()];
    const dateNum = targetDate.getDate();
    const dStr = targetDate.toDateString();

    const dayCell = document.createElement("div");
    dayCell.className = "cal-day-cell";
    if (i === 0) dayCell.classList.add("today-cell");

    const match = entryDateMap[dStr];
    if (match) {
      dayCell.classList.add("has-mood");
      dayCell.title = `${match.dateStr}: ${match.mood} — ${match.note}`;
      dayCell.innerHTML = `<span>${dateNum}</span><strong>${match.emoji}</strong>`;
    } else {
      dayCell.innerHTML = `<span>${dateNum}</span><small class="text-muted">${dayLabel}</small>`;
    }
    moodCalendarContainer.appendChild(dayCell);
  }
}

function renderMoodHistoryList() {
  if (!moodHistoryList) return;

  if (state.moodEntries.length === 0) {
    moodHistoryList.innerHTML = `
      <li class="clean-empty-state" style="padding: 14px 8px;">
        <span class="empty-icon">📝</span>
        <p>No mood logs yet this session.</p>
        <small>Use the options above or the side panel to record how you feel.</small>
      </li>
    `;
    return;
  }

  moodHistoryList.innerHTML = state.moodEntries.slice(0, 7).map(item => `
    <li class="mood-history-item" data-id="${item.id}">
      <span>${item.emoji} <strong>${item.mood}</strong> — ${item.note}</span>
      <span class="text-muted">${item.timeStr || item.dateStr}</span>
    </li>
  `).join("");
}

function renderJourneyView() {
  const statSessions = document.getElementById("journey-stat-sessions");
  const statMinutes = document.getElementById("journey-stat-minutes");
  const statActivities = document.getElementById("journey-stat-activities");
  const statMilestones = document.getElementById("journey-stat-milestones");

  const totalActs = state.sessionActivities.length;
  const mindfulMins = state.sessionStats.mindfulMinutes;
  const completedSessions = (state.sessionStats.breathingSessionsCompleted || 0) + (state.sessionStats.journeysCompleted || 0);

  if (statSessions) statSessions.textContent = completedSessions;
  if (statMinutes) statMinutes.textContent = mindfulMins;
  if (statActivities) statActivities.textContent = totalActs;

  const hasCheckin = state.moodEntries.length >= 1;
  const hasBreathe = state.sessionStats.breathingSessionsCompleted >= 1;
  const hasJourney = state.sessionStats.journeysCompleted >= 1;
  const hasFocus = totalActs >= 3;

  let unlockedCount = 0;
  if (hasCheckin) unlockedCount++;
  if (hasBreathe) unlockedCount++;
  if (hasJourney) unlockedCount++;
  if (hasFocus) unlockedCount++;

  if (statMilestones) statMilestones.textContent = `${unlockedCount} / 4`;

  updateMilestoneBadge("milestone-checkin", "milestone-checkin-desc", hasCheckin, "First Check-in", "Unlocked in this session", "Log your first feeling");
  updateMilestoneBadge("milestone-breathe", "milestone-breathe-desc", hasBreathe, "Breathe Easy", "Unlocked in this session", "Complete 1 breathing session");
  updateMilestoneBadge("milestone-journey", "milestone-journey-desc", hasJourney, "Guided Journey", "Unlocked in this session", "Complete 1 guided reflection");
  updateMilestoneBadge("milestone-consistent", "milestone-consistent-desc", hasFocus, "Mindful Focus", "Unlocked in this session", "Complete 3 self-care activities");

  const timelineContainer = document.getElementById("journey-timeline-container");
  if (timelineContainer) {
    if (totalActs === 0) {
      timelineContainer.innerHTML = `
        <div class="clean-empty-state">
          <span class="empty-icon">🛤️</span>
          <p>No activities recorded yet in this session.</p>
          <small>Log a mood, try a breathing pause, or complete a guided journey to see your mindful timeline grow.</small>
        </div>
      `;
    } else {
      timelineContainer.innerHTML = state.sessionActivities.map(act => `
        <div class="timeline-entry">
          <div class="timeline-dot ${act.type}"></div>
          <div class="timeline-content">
            <div class="entry-header">
              <strong>${act.title}</strong>
              <span class="entry-time">${act.timeStr}</span>
            </div>
            <p>${act.detail}</p>
          </div>
        </div>
      `).join("");
    }
  }
}

function updateMilestoneBadge(elemId, descId, isUnlocked, title, unlockedDesc, lockedDesc) {
  const elem = document.getElementById(elemId);
  const desc = document.getElementById(descId);
  if (elem) {
    elem.className = `milestone-badge-item ${isUnlocked ? "unlocked" : "in-progress"}`;
  }
  if (desc) {
    desc.textContent = isUnlocked ? unlockedDesc : lockedDesc;
  }
}

// Event Listeners for Intention & Mood
intentionChips.forEach(chip => {
  chip.addEventListener("click", () => {
    intentionChips.forEach(c => c.classList.remove("active"));
    chip.classList.add("active");
    state.currentIntention = chip.getAttribute("data-intention");
    logSessionActivity("intention", "Daily Intention Selected", `"${state.currentIntention}"`);
    updateContextualRightPanel("wellbeing");
    renderAllWellbeingViews();
  });
});

if (saveIntentionBtn && customIntentionInput) {
  saveIntentionBtn.addEventListener("click", () => {
    const custom = customIntentionInput.value.trim();
    if (custom) {
      state.currentIntention = custom;
      intentionChips.forEach(c => c.classList.remove("active"));
      customIntentionInput.value = "";
      logSessionActivity("intention", "Daily Intention Set", `"${state.currentIntention}"`);
      updateContextualRightPanel("wellbeing");
      renderAllWellbeingViews();
    }
  });
}

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

moodSelectButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    moodSelectButtons.forEach(b => b.classList.remove("selected"));
    btn.classList.add("selected");
    selectedMoodForLogging = btn.getAttribute("data-mood");
  });
});

if (saveMoodEntryBtn) {
  saveMoodEntryBtn.addEventListener("click", () => {
    saveMoodEntryBtn.disabled = true;
    const note = moodNoteInput ? moodNoteInput.value.trim() : "";
    recordMoodEntry(selectedMoodForLogging, note, "direct");

    if (moodNoteInput) moodNoteInput.value = "";
    if (moodSaveStatus) {
      moodSaveStatus.classList.remove("hidden");
      setTimeout(() => moodSaveStatus.classList.add("hidden"), 2000);
    }
    setTimeout(() => { saveMoodEntryBtn.disabled = false; }, 600);
  });
}

if (cancelMoodEntryBtn && moodNoteInput) {
  cancelMoodEntryBtn.addEventListener("click", () => {
    moodNoteInput.value = "";
  });
}

// Right panel mood quick check-in buttons
document.querySelectorAll(".mood-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const mood = btn.getAttribute("data-mood");
    recordMoodEntry(mood, "Quick check-in.", "quick");

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
  state.breatheElapsedSec = 0;
  state.breathePhaseIndex = 0;

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

  const duration = state.breatheDurationMins || 1;
  state.sessionStats.mindfulMinutes += duration;
  state.sessionStats.breathingSessionsCompleted += 1;

  const exName = (breatheExercises[state.breatheActiveExercise] && breatheExercises[state.breatheActiveExercise].name) || "Breathing";
  logSessionActivity("breathe", `${exName} Completed`, `Completed ${duration} min(s) of mindful pacing.`);

  renderAllWellbeingViews();
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
    navigateTo("calm-music");
  });
}

const toolAffirmationsBtn = document.getElementById("tool-affirmations-btn");
if (toolAffirmationsBtn) {
  toolAffirmationsBtn.addEventListener("click", () => {
    navigateTo("chat");
    sendMessage("Could you share a gentle, encouraging affirmation for today?", false);
  });
}

const toolMindfulGamesBtn = document.getElementById("tool-mindful-games-btn");
if (toolMindfulGamesBtn) {
  toolMindfulGamesBtn.addEventListener("click", () => {
    navigateTo("mindful-games");
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
const runnerStepBody = document.getElementById("runner-step-body");
const runnerCompletionBody = document.getElementById("runner-completion-body");
const runnerCompletionTitle = document.getElementById("runner-completion-title");
const runnerCompletionText = document.getElementById("runner-completion-text");
const runnerReturnBtn = document.getElementById("runner-return-btn");
const runnerChatDiscussBtn = document.getElementById("runner-chat-discuss-btn");
const runnerFooterControls = document.getElementById("runner-footer-controls");
const runnerBackBtn = document.getElementById("runner-back-btn");
const runnerSkipBtn = document.getElementById("runner-skip-btn");
const runnerNextBtn = document.getElementById("runner-next-btn");
const exitJourneyBtn = document.getElementById("exit-journey-btn");

function renderGuidedSupportView() {
  // Update status tags on pathway cards
  document.querySelectorAll(".journey-card-interactive").forEach(card => {
    const jKey = card.getAttribute("data-journey");
    if (!jKey) return;
    const isCompleted = state.completedPathways.has(jKey);
    let badge = card.querySelector(".journey-status-badge");
    if (isCompleted) {
      if (!badge) {
        badge = document.createElement("span");
        badge.className = "journey-status-badge completed";
        badge.innerHTML = "✓ Completed";
        const meta = card.querySelector(".journey-meta");
        if (meta) meta.appendChild(badge);
      }
    } else if (badge) {
      badge.remove();
    }
  });
}

document.querySelectorAll(".journey-card-interactive").forEach(card => {
  card.addEventListener("click", (e) => {
    const jKey = card.getAttribute("data-journey");
    if (jKey) startJourney(jKey);
  });
});

document.querySelectorAll(".start-journey-btn").forEach(btn => {
  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    const jKey = btn.getAttribute("data-journey");
    if (jKey) startJourney(jKey);
  });
});

function startJourney(jKey) {
  const data = journeysData[jKey];
  if (!data) return;

  state.activeJourney = jKey;
  state.activeJourneyStep = 0;

  if (runnerStepBody) runnerStepBody.classList.remove("hidden");
  if (runnerFooterControls) runnerFooterControls.classList.remove("hidden");
  if (runnerCompletionBody) runnerCompletionBody.classList.add("hidden");

  if (journeysGridSection) journeysGridSection.classList.add("hidden");
  if (activeJourneyRunner) activeJourneyRunner.classList.remove("hidden");

  renderCurrentJourneyStep();
}

function renderCurrentJourneyStep() {
  const data = journeysData[state.activeJourney];
  if (!data) return;

  const totalSteps = data.steps.length;
  const current = data.steps[state.activeJourneyStep];
  const stepKey = `${state.activeJourney}_${state.activeJourneyStep}`;
  const savedInput = state.journeyUserInputs[stepKey] || "";

  if (runnerJourneyTitle) runnerJourneyTitle.textContent = data.title;
  if (runnerStepCounter) runnerStepCounter.textContent = `Step ${state.activeJourneyStep + 1} of ${totalSteps}`;
  
  const progressBar = document.querySelector(".runner-progress-bar");
  if (progressBar) {
    progressBar.setAttribute("aria-valuenow", state.activeJourneyStep + 1);
    progressBar.setAttribute("aria-valuemax", totalSteps);
  }
  if (runnerProgressFill) {
    const pct = ((state.activeJourneyStep + 1) / totalSteps) * 100;
    runnerProgressFill.style.width = `${pct}%`;
  }

  if (runnerStepHeading) runnerStepHeading.textContent = current.heading;
  if (runnerStepContent) runnerStepContent.textContent = current.content;

  if (runnerInteractionArea) {
    runnerInteractionArea.innerHTML = `
      <label for="journey-step-input" style="font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px; display: block;">${current.prompt}</label>
      <textarea id="journey-step-input" rows="3" placeholder="Type your gentle thoughts here... (saved automatically in this session)">${savedInput}</textarea>
    `;
    const textarea = document.getElementById("journey-step-input");
    if (textarea) {
      textarea.addEventListener("input", (e) => {
        state.journeyUserInputs[stepKey] = e.target.value;
      });
    }
  }

  if (runnerBackBtn) runnerBackBtn.disabled = state.activeJourneyStep === 0;
  if (runnerNextBtn) {
    runnerNextBtn.textContent = (state.activeJourneyStep === totalSteps - 1) ? "Complete Reflection ✨" : "Continue →";
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
      // Final step: complete pathway with duplicate prevention
      const isNewCompletion = !state.completedPathways.has(state.activeJourney);
      if (isNewCompletion) {
        state.completedPathways.add(state.activeJourney);
        state.sessionStats.journeysCompleted += 1;
        logSessionActivity("journey", `Guided Support: ${data.title}`, "Completed guided reflection pathway.");
        renderAllWellbeingViews();
      }

      // Show in-card completion view
      if (runnerStepBody) runnerStepBody.classList.add("hidden");
      if (runnerFooterControls) runnerFooterControls.classList.add("hidden");
      if (runnerCompletionBody) {
        runnerCompletionBody.classList.remove("hidden");
        if (runnerCompletionTitle) runnerCompletionTitle.textContent = `${data.title} Completed ✨`;
        if (runnerCompletionText) {
          runnerCompletionText.textContent = isNewCompletion
            ? "Great job taking intentional time for your wellbeing. Your reflection pathway has been completed."
            : "You revisited this reflection pathway. Taking repeated gentle moments strengthens your inner calm.";
        }
      }
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
  renderGuidedSupportView();
}

if (exitJourneyBtn) exitJourneyBtn.addEventListener("click", exitJourney);
if (runnerReturnBtn) runnerReturnBtn.addEventListener("click", exitJourney);
if (runnerChatDiscussBtn) {
  runnerChatDiscussBtn.addEventListener("click", () => {
    const jKey = state.activeJourney;
    const title = journeysData[jKey]?.title || "guided pathway";
    exitJourney();
    navigateTo("chat");
    sendMessage(`I just completed the guided reflection pathway on '${title}'. Can we talk about it?`, false);
  });
}

// ==================== VIEW 6: COLLEGE HELP (LPU) LOGIC ====================
let activeCampusCategory = "all";
const campusSearchInput = document.getElementById("campus-search-input");
const campusEmptyState = document.getElementById("campus-empty-state");
const campusClearFilterBtn = document.getElementById("campus-clear-filter-btn");

function filterCampusCards(category) {
  if (category) activeCampusCategory = category;
  const currentCat = activeCampusCategory || "all";
  const query = campusSearchInput ? campusSearchInput.value.toLowerCase().trim() : "";

  document.querySelectorAll(".campus-cat-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-cat") === currentCat);
  });

  let visibleCount = 0;
  document.querySelectorAll(".campus-resource-card").forEach(card => {
    const cardCat = card.getAttribute("data-cat");
    const matchesCat = currentCat === "all" || cardCat === currentCat;
    const cardText = card.textContent.toLowerCase();
    const matchesQuery = !query || cardText.includes(query);

    if (matchesCat && matchesQuery) {
      card.classList.remove("hidden");
      visibleCount++;
    } else {
      card.classList.add("hidden");
    }
  });

  if (campusEmptyState) {
    if (visibleCount === 0) {
      campusEmptyState.classList.remove("hidden");
    } else {
      campusEmptyState.classList.add("hidden");
    }
  }
}

document.querySelectorAll(".campus-cat-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const cat = btn.getAttribute("data-cat") || "all";
    filterCampusCards(cat);
  });
});

if (campusSearchInput) {
  campusSearchInput.addEventListener("input", () => {
    filterCampusCards();
  });
}

if (campusClearFilterBtn) {
  campusClearFilterBtn.addEventListener("click", () => {
    if (campusSearchInput) campusSearchInput.value = "";
    filterCampusCards("all");
  });
}

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
        <li>Severe panic or racing thoughts that interfere with examinations.</li>
      </ul>
      <p>At LPU, the Department of Counseling and Happiness is free, confidential, and located in Building 8, Room 208.</p>
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
const bookmarkGuideBtn = document.getElementById("bookmark-guide-btn");
const discussGuideWithMmBtn = document.getElementById("discuss-guide-with-mm-btn");

let activeLibCategory = "all";
let currentDetailGuide = null;
let lastFocusedElement = null;

function renderResourcesLibrary() {
  if (!libCardsGrid) return;
  const rawQuery = libSearchInput ? libSearchInput.value.trim() : "";
  const query = rawQuery.toLowerCase();

  // Update active state on category buttons
  libCategoryButtons.forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-category") === activeLibCategory);
  });

  const filtered = wellnessGuides.filter(g => {
    const matchesCat = activeLibCategory === "all"
      ? true
      : activeLibCategory === "bookmarks"
        ? state.bookmarkedGuides.has(g.id)
        : g.category === activeLibCategory;

    const matchesQuery = !query ||
      g.title.toLowerCase().includes(query) ||
      g.summary.toLowerCase().includes(query) ||
      g.categoryLabel.toLowerCase().includes(query) ||
      g.content.toLowerCase().includes(query);

    return matchesCat && matchesQuery;
  });

  if (filtered.length === 0) {
    let emptyIcon = "📖";
    let emptyTitle = "No guides in this category yet.";
    let emptySub = "We are continually curating new evidence-informed student guides.";
    let emptyBtnText = "View All Topics";

    if (activeLibCategory === "bookmarks") {
      emptyIcon = "★";
      emptyTitle = "No saved guides yet.";
      emptySub = "Click the star icon on any guide or in the reader modal to save articles for quick reading.";
      emptyBtnText = "Browse All Guides";
    } else if (query) {
      emptyIcon = "🔍";
      emptyTitle = `No guides match "${escapeHtml(rawQuery)}".`;
      emptySub = "Try a broader keyword or switch to another category.";
      emptyBtnText = "Clear Search & Filters";
    }

    libCardsGrid.innerHTML = `
      <div class="clean-empty-state" style="grid-column: 1 / -1; padding: 40px 20px;">
        <span class="empty-icon">${emptyIcon}</span>
        <p>${emptyTitle}</p>
        <small>${emptySub}</small>
        <button id="lib-empty-reset-btn" class="btn-outline-pill small-btn empty-action-btn">${emptyBtnText}</button>
      </div>
    `;

    const resetAllBtn = document.getElementById("lib-empty-reset-btn");
    if (resetAllBtn) {
      resetAllBtn.addEventListener("click", () => {
        if (libSearchInput) libSearchInput.value = "";
        activeLibCategory = "all";
        renderResourcesLibrary();
      });
    }
    return;
  }

  libCardsGrid.innerHTML = filtered.map(g => {
    const isBookmarked = state.bookmarkedGuides.has(g.id);
    return `
      <div class="lib-article-card" data-guide-id="${g.id}">
        <div>
          <div class="lib-card-top">
            <span class="lib-tag">${g.categoryLabel}</span>
            <button class="lib-bookmark-btn ${isBookmarked ? 'active' : ''}" data-id="${g.id}" title="${isBookmarked ? 'Remove Bookmark' : 'Bookmark Guide'}" aria-label="${isBookmarked ? 'Remove Bookmark' : 'Bookmark Guide'}">
              ${isBookmarked ? '★' : '☆'}
            </button>
          </div>
          <h4>${g.title}</h4>
          <p>${g.summary}</p>
        </div>
        <div class="lib-card-footer">
          <span class="read-time">${g.readTime}</span>
          <button class="btn-outline-pill small-btn open-guide-btn" data-id="${g.id}" aria-label="Read guide: ${g.title}">Read Guide →</button>
        </div>
      </div>
    `;
  }).join("");

  // Bind guide click events
  document.querySelectorAll(".open-guide-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const gid = parseInt(btn.getAttribute("data-id"), 10);
      openGuideDetail(gid, btn);
    });
  });

  document.querySelectorAll(".lib-article-card").forEach(card => {
    card.addEventListener("click", (e) => {
      if (e.target.closest(".lib-bookmark-btn")) return;
      const gid = parseInt(card.getAttribute("data-guide-id"), 10);
      openGuideDetail(gid, card);
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

function openGuideDetail(guideId, triggerEl = null) {
  const guide = wellnessGuides.find(g => g.id === guideId);
  if (!guide || !libDetailModal) return;

  lastFocusedElement = triggerEl || document.activeElement;
  currentDetailGuide = guide;
  if (detailCategoryTag) detailCategoryTag.textContent = guide.categoryLabel;
  if (detailTitle) detailTitle.textContent = guide.title;
  if (detailReadTime) detailReadTime.textContent = `📖 ${guide.readTime}`;
  if (detailContent) detailContent.innerHTML = guide.content;

  if (bookmarkGuideBtn) {
    const isBookmarked = state.bookmarkedGuides.has(guide.id);
    bookmarkGuideBtn.textContent = isBookmarked ? "★ Bookmarked" : "☆ Bookmark Guide";
    bookmarkGuideBtn.classList.toggle("active", isBookmarked);
  }

  libDetailModal.classList.remove("hidden");
  if (closeLibDetailBtn) closeLibDetailBtn.focus();
}

function closeGuideDetail() {
  if (libDetailModal) libDetailModal.classList.add("hidden");
  currentDetailGuide = null;
  if (lastFocusedElement && typeof lastFocusedElement.focus === "function") {
    lastFocusedElement.focus();
  }
}

if (closeLibDetailBtn && libDetailModal) {
  closeLibDetailBtn.addEventListener("click", closeGuideDetail);
}

if (libDetailModal) {
  libDetailModal.addEventListener("click", (e) => {
    if (e.target === libDetailModal) {
      closeGuideDetail();
    }
  });
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && libDetailModal && !libDetailModal.classList.contains("hidden")) {
    closeGuideDetail();
  }
});

if (bookmarkGuideBtn) {
  bookmarkGuideBtn.addEventListener("click", () => {
    if (!currentDetailGuide) return;
    if (state.bookmarkedGuides.has(currentDetailGuide.id)) {
      state.bookmarkedGuides.delete(currentDetailGuide.id);
      bookmarkGuideBtn.textContent = "☆ Bookmark Guide";
      bookmarkGuideBtn.classList.remove("active");
    } else {
      state.bookmarkedGuides.add(currentDetailGuide.id);
      bookmarkGuideBtn.textContent = "★ Bookmarked";
      bookmarkGuideBtn.classList.add("active");
    }
    renderResourcesLibrary();
    updateContextualRightPanel("resources-library");
  });
}

if (discussGuideWithMmBtn) {
  discussGuideWithMmBtn.addEventListener("click", () => {
    if (!currentDetailGuide) return;
    const title = currentDetailGuide.title;
    closeGuideDetail();
    navigateTo("chat");
    sendMessage(`I was reading the guide "${title}". Can we talk about how to apply it in my routine?`, false);
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

// ==================== VIEW 9: SETTINGS & APPEARANCE ENGINE (PHASE 2B) ====================
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

// Namespaced non-sensitive appearance preferences storage key
const PREFERENCES_STORAGE_KEY = "mannmitra_appearance_preferences";
const DEFAULT_PREFERENCES = {
  theme: "light",
  accent: "pink-purple",
  speechRate: 0.95,
  autoGreeting: true,
  reducedMotion: false,
  fontSize: "default",
};

function loadSavedPreferences() {
  let loaded = {};
  try {
    const raw = localStorage.getItem(PREFERENCES_STORAGE_KEY);
    if (raw) loaded = JSON.parse(raw) || {};
  } catch (_) {}

  const theme = ["light", "dark", "system"].includes(loaded.theme) ? loaded.theme : DEFAULT_PREFERENCES.theme;
  const accent = ["pink-purple", "lavender", "teal", "warm-peach"].includes(loaded.accent) ? loaded.accent : DEFAULT_PREFERENCES.accent;
  const speechRate = (typeof loaded.speechRate === "number" && loaded.speechRate >= 0.75 && loaded.speechRate <= 1.25)
    ? loaded.speechRate
    : DEFAULT_PREFERENCES.speechRate;
  const autoGreeting = typeof loaded.autoGreeting === "boolean" ? loaded.autoGreeting : DEFAULT_PREFERENCES.autoGreeting;
  const reducedMotion = typeof loaded.reducedMotion === "boolean" ? loaded.reducedMotion : DEFAULT_PREFERENCES.reducedMotion;
  const fontSize = ["default", "large", "xlarge"].includes(loaded.fontSize) ? loaded.fontSize : DEFAULT_PREFERENCES.fontSize;

  return { theme, accent, speechRate, autoGreeting, reducedMotion, fontSize };
}

function savePreferences() {
  try {
    const toSave = {
      theme: state.settings.theme,
      accent: state.settings.accent,
      speechRate: state.settings.speechRate,
      autoGreeting: state.settings.autoGreeting,
      reducedMotion: state.settings.reducedMotion,
      fontSize: state.settings.fontSize,
    };
    localStorage.setItem(PREFERENCES_STORAGE_KEY, JSON.stringify(toSave));
  } catch (_) {}
}

function applyTheme(themeKey) {
  state.settings.theme = themeKey;
  let effectiveTheme = themeKey;
  if (themeKey === "system") {
    effectiveTheme = (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light";
  }
  document.body.setAttribute("data-theme", effectiveTheme);
  document.documentElement.setAttribute("data-theme", effectiveTheme);

  if (themeButtons) {
    themeButtons.forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-theme") === themeKey);
    });
  }
}

function applyAccent(accentKey) {
  state.settings.accent = accentKey;
  document.body.setAttribute("data-accent", accentKey);
  document.documentElement.setAttribute("data-accent", accentKey);

  if (accentButtons) {
    accentButtons.forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-accent") === accentKey);
    });
  }
}

function applyFontSize(sizeKey) {
  state.settings.fontSize = sizeKey;
  document.body.classList.remove("font-large", "font-xlarge");
  if (sizeKey === "large") document.body.classList.add("font-large");
  if (sizeKey === "xlarge") document.body.classList.add("font-xlarge");

  if (fontSizeButtons) {
    fontSizeButtons.forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-size") === sizeKey);
    });
  }
}

function applyReducedMotion(isReduced) {
  state.settings.reducedMotion = isReduced;
  document.body.classList.toggle("reduced-motion", isReduced);
  if (reducedMotionToggle) reducedMotionToggle.checked = isReduced;
}

function applySpeechRate(rate) {
  state.settings.speechRate = rate;
  if (speechRateInput) speechRateInput.value = rate;
  if (speechRateVal) speechRateVal.textContent = `${rate.toFixed(2)}x`;
}

function applyAutoGreeting(enabled) {
  state.settings.autoGreeting = enabled;
  if (autoGreetingToggle) autoGreetingToggle.checked = enabled;
}

function initAppearanceEngine() {
  const prefs = loadSavedPreferences();
  state.settings = { ...state.settings, ...prefs };

  applyTheme(prefs.theme);
  applyAccent(prefs.accent);
  applyFontSize(prefs.fontSize);
  applyReducedMotion(prefs.reducedMotion);
  applySpeechRate(prefs.speechRate);
  applyAutoGreeting(prefs.autoGreeting);

  if (window.matchMedia) {
    try {
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
        if (state.settings.theme === "system") {
          applyTheme("system");
        }
      });
    } catch (_) {}
  }
}

// Display Name Handler
if (saveDisplayNameBtn && settingsDisplayName) {
  saveDisplayNameBtn.addEventListener("click", () => {
    const val = settingsDisplayName.value.trim();
    if (val) {
      updateUserNameDisplays(val);
      alert("Display name updated!");
    }
  });
}

// Theme Selectors
themeButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    const theme = btn.getAttribute("data-theme") || "light";
    applyTheme(theme);
    savePreferences();
  });
});

// Accent Selectors
accentButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    const accent = btn.getAttribute("data-accent") || "pink-purple";
    applyAccent(accent);
    savePreferences();
  });
});

// Auto Greeting Toggle
if (autoGreetingToggle) {
  autoGreetingToggle.addEventListener("change", (e) => {
    applyAutoGreeting(e.target.checked);
    savePreferences();
  });
}

// Speech Rate Slider
if (speechRateInput && speechRateVal) {
  speechRateInput.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value);
    applySpeechRate(val);
    savePreferences();
  });
}

// Voice Locale Select
if (voiceLocaleSelect) {
  voiceLocaleSelect.addEventListener("change", (e) => {
    state.settings.voiceLocale = e.target.value;
  });
}

// Reduced Motion Toggle
if (reducedMotionToggle) {
  reducedMotionToggle.addEventListener("change", (e) => {
    applyReducedMotion(e.target.checked);
    savePreferences();
  });
}

// Font Size Buttons
fontSizeButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    const sz = btn.getAttribute("data-size") || "default";
    applyFontSize(sz);
    savePreferences();
  });
});

// Clear Local Demo Data
if (clearDemoDataBtn) {
  clearDemoDataBtn.addEventListener("click", () => {
    if (confirm("Clear local prototype reflections, mood entries, and chat history?")) {
      conversationHistory = [];
      state.currentMood = null;
      state.moodEntries = [];
      state.sessionActivities = [];
      state.sessionStats = { mindfulMinutes: 0, breathingSessionsCompleted: 0, journeysCompleted: 0 };
      state.bookmarkedGuides.clear();
      state.completedPathways.clear();
      state.journeyUserInputs = {};
      renderAllWellbeingViews();
      renderGuidedSupportView();
      renderResourcesLibrary();
      filterCampusCards("all");
      const banner = document.getElementById("mood-response-banner");
      if (banner) banner.classList.add("hidden");
      if (clearDataStatus) {
        clearDataStatus.classList.remove("hidden");
        setTimeout(() => clearDataStatus.classList.add("hidden"), 2000);
      }
    }
  });
}

// Initialize theme and appearance engine on startup
initAppearanceEngine();

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

// ==================== TODAY'S THOUGHT CONTROLLER ====================
let currentDailyThought = null;
let lastThoughtDateStr = "";

function renderTodaysThought(forcedThought = null) {
  const badgeEl = document.getElementById("thought-theme-badge");
  const quoteEl = document.getElementById("thought-quote-text");
  const authorEl = document.getElementById("thought-author-text");

  let thought = forcedThought;
  if (!thought) {
    if (typeof getDailyThought === "function") {
      thought = getDailyThought();
    } else {
      thought = {
        id: 1,
        quote: "Progress, not perfection, is what truly matters.",
        author: "Student Resilience",
        theme: "⚡ Daily Fuel"
      };
    }
  }

  currentDailyThought = thought;
  lastThoughtDateStr = new Date().toDateString();

  if (badgeEl) badgeEl.textContent = thought.theme || "⚡ Daily Fuel";
  if (quoteEl) quoteEl.innerHTML = `"${thought.quote.replace(/\n/g, "<br>")}"`;
  if (authorEl) authorEl.textContent = `~ ${thought.author || "MannMitra"}`;
}

const thoughtRefreshBtn = document.getElementById("thought-refresh-btn");
if (thoughtRefreshBtn) {
  thoughtRefreshBtn.addEventListener("click", () => {
    thoughtRefreshBtn.classList.add("rotating");
    const wrapper = document.querySelector(".thought-content-wrapper");
    if (wrapper) wrapper.classList.add("thought-fade-transition");

    setTimeout(() => {
      if (typeof getRandomThought === "function") {
        const nextThought = getRandomThought(currentDailyThought ? currentDailyThought.id : null);
        renderTodaysThought(nextThought);
      }
      thoughtRefreshBtn.classList.remove("rotating");
      if (wrapper) {
        setTimeout(() => wrapper.classList.remove("thought-fade-transition"), 50);
      }
    }, 300);
  });
}

const thoughtSpeakBtn = document.getElementById("thought-speak-btn");
if (thoughtSpeakBtn) {
  thoughtSpeakBtn.addEventListener("click", () => {
    if (currentDailyThought) {
      speak(`${currentDailyThought.quote}. By ${currentDailyThought.author}`);
    } else {
      speak("Progress, not perfection, is what truly matters.");
    }
  });
}

const safeSetInterval = (fn, ms) => (typeof setInterval !== "undefined" ? setInterval(fn, ms) : null);
const safeClearInterval = (id) => { if (typeof clearInterval !== "undefined" && id) clearInterval(id); };
const safeRequestAnimationFrame = (cb) => (typeof requestAnimationFrame !== "undefined" ? requestAnimationFrame(cb) : null);
const safeCancelAnimationFrame = (id) => { if (typeof cancelAnimationFrame !== "undefined" && id) cancelAnimationFrame(id); };

// Midnight date check for automatic daily thought updates
safeSetInterval(() => {
  const nowStr = new Date().toDateString();
  if (nowStr !== lastThoughtDateStr) {
    renderTodaysThought();
  }
}, 60000);

// ==================== VIEW 10: CALM MUSIC & SOUNDSCAPES ENGINE ====================
const calmMusicTracks = [
  {
    id: "rain",
    title: "Gentle Rain & Soft Thunder",
    category: "Nature Sounds",
    freq: "432Hz Harmonic",
    icon: "🌧️",
    desc: "Soothing precipitation with distant peaceful rumble to quiet racing thoughts.",
    type: "rain"
  },
  {
    id: "ocean",
    title: "Ocean Sunset Waves",
    category: "Coastal",
    freq: "6 Breaths/min",
    icon: "🌊",
    desc: "Rhythmic gentle surf swells that naturally slow your breathing rate.",
    type: "ocean"
  },
  {
    id: "lofi",
    title: "Lo-Fi Study Beats",
    category: "Lo-Fi",
    freq: "Warm Keys",
    icon: "☕",
    desc: "Warm electric piano chords, mellow bass, and subtle tape warmth for late night study.",
    type: "lofi"
  },
  {
    id: "meditation",
    title: "Deep Meditation Drone",
    category: "Ambient",
    freq: "528Hz Solfeggio",
    icon: "🧘",
    desc: "Harmonic singing bowls and tranquil drone frequencies for emotional grounding.",
    type: "meditation"
  },
  {
    id: "forest",
    title: "Whispering Forest & Birds",
    category: "Forest",
    freq: "Wind & Birds",
    icon: "🌲",
    desc: "Gentle breeze through pine needles with sweet birdsong for fresh mental energy.",
    type: "forest"
  },
  {
    id: "starlight",
    title: "Celestial Starlight",
    category: "Cosmic",
    freq: "Delta Waves",
    icon: "🌌",
    desc: "Ethereal floating chord pads for evening relaxation, decompression, and sleep.",
    type: "starlight"
  }
];

let musicAudioCtx = null;
let musicMasterGain = null;
let musicAnalyser = null;
let musicActiveNodes = [];
let musicActiveIntervals = [];
let currentMusicTrackId = "rain";
let isMusicPlaying = false;
let musicVolumeLevel = 0.70;
let musicVisualizerMode = "waves";
let musicTimerMinutes = 0;
let musicTimerSecondsLeft = 0;
let musicTimerCountdownId = null;
let musicVisualizerRaf = null;

function ensureMusicAudioContext() {
  if (!musicAudioCtx) {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return false;
    musicAudioCtx = new AC();
  }
  if (musicAudioCtx.state === "suspended") {
    musicAudioCtx.resume();
  }
  if (!musicMasterGain) {
    musicMasterGain = musicAudioCtx.createGain();
    musicMasterGain.gain.setValueAtTime(musicVolumeLevel, musicAudioCtx.currentTime);
  }
  if (!musicAnalyser) {
    musicAnalyser = musicAudioCtx.createAnalyser();
    musicAnalyser.fftSize = 128;
    musicMasterGain.connect(musicAnalyser);
    musicAnalyser.connect(musicAudioCtx.destination);
  }
  return true;
}

function stopCurrentSoundNodes() {
  musicActiveNodes.forEach(node => {
    try {
      if (node.stop) node.stop();
      if (node.disconnect) node.disconnect();
    } catch (_) {}
  });
  musicActiveNodes = [];

  musicActiveIntervals.forEach(id => safeClearInterval(id));
  musicActiveIntervals = [];
}

function generatePinkNoiseBuffer(ctx, durationSec = 3) {
  const bufferSize = ctx.sampleRate * durationSec;
  const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
  const data = buffer.getChannelData(0);
  let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
  for (let i = 0; i < bufferSize; i++) {
    const white = Math.random() * 2 - 1;
    b0 = 0.99886 * b0 + white * 0.0555179;
    b1 = 0.99332 * b1 + white * 0.0750759;
    b2 = 0.96900 * b2 + white * 0.1538520;
    b3 = 0.86650 * b3 + white * 0.3104856;
    b4 = 0.55000 * b4 + white * 0.5329522;
    b5 = -0.7616 * b5 - white * 0.0168980;
    data[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362) * 0.11;
    b6 = white * 0.115926;
  }
  return buffer;
}

function startSoundscape(trackType) {
  if (!ensureMusicAudioContext()) return;
  stopCurrentSoundNodes();

  const ctx = musicAudioCtx;
  const master = musicMasterGain;
  const now = ctx.currentTime;

  if (trackType === "rain") {
    // Rain: filtered continuous pink noise with subtle thunder
    const noiseBuffer = generatePinkNoiseBuffer(ctx, 4);
    const noiseSource = ctx.createBufferSource();
    noiseSource.buffer = noiseBuffer;
    noiseSource.loop = true;

    const filter = ctx.createBiquadFilter();
    filter.type = "bandpass";
    filter.frequency.setValueAtTime(850, now);
    filter.Q.setValueAtTime(0.8, now);

    const rainGain = ctx.createGain();
    rainGain.gain.setValueAtTime(0.55, now);

    noiseSource.connect(filter);
    filter.connect(rainGain);
    rainGain.connect(master);
    noiseSource.start();
    musicActiveNodes.push(noiseSource, filter, rainGain);

    // Periodic soft distant rumble (thunder)
    const thunderInt = safeSetInterval(() => {
      if (!isMusicPlaying || !musicAudioCtx) return;
      try {
        const thOsc = ctx.createOscillator();
        const thGain = ctx.createGain();
        const thFilter = ctx.createBiquadFilter();
        const t = ctx.currentTime;

        thOsc.type = "sine";
        thOsc.frequency.setValueAtTime(45, t);
        thOsc.frequency.exponentialRampToValueAtTime(30, t + 2.5);

        thFilter.type = "lowpass";
        thFilter.frequency.setValueAtTime(90, t);

        thGain.gain.setValueAtTime(0.001, t);
        thGain.gain.exponentialRampToValueAtTime(0.25, t + 0.4);
        thGain.gain.exponentialRampToValueAtTime(0.001, t + 3.0);

        thOsc.connect(thFilter);
        thFilter.connect(thGain);
        thGain.connect(master);

        thOsc.start(t);
        thOsc.stop(t + 3.1);
      } catch (_) {}
    }, 9000);
    musicActiveIntervals.push(thunderInt);

  } else if (trackType === "ocean") {
    // Ocean Sunset: rhythmic surf swells (10s breath cycle)
    const noiseBuffer = generatePinkNoiseBuffer(ctx, 4);
    const noiseSource = ctx.createBufferSource();
    noiseSource.buffer = noiseBuffer;
    noiseSource.loop = true;

    const filter = ctx.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.setValueAtTime(400, now);

    const swellGain = ctx.createGain();
    swellGain.gain.setValueAtTime(0.05, now);

    // LFO modulating surf swell volume
    const lfo = ctx.createOscillator();
    lfo.type = "sine";
    lfo.frequency.setValueAtTime(0.1, now); // 10 second period (~6 breaths/min)
    const lfoGain = ctx.createGain();
    lfoGain.gain.setValueAtTime(0.45, now);

    lfo.connect(lfoGain);
    lfoGain.connect(swellGain.gain);

    noiseSource.connect(filter);
    filter.connect(swellGain);
    swellGain.connect(master);

    noiseSource.start();
    lfo.start();
    musicActiveNodes.push(noiseSource, filter, swellGain, lfo, lfoGain);

  } else if (trackType === "lofi") {
    // Lo-Fi Study Beats: warm repeating chords with vinyl warmth
    const chords = [
      [293.66, 349.23, 440.0, 523.25], // Dm7
      [261.63, 329.63, 392.0, 493.88], // Cmaj7
      [220.00, 261.63, 329.63, 392.0], // Am7
      [246.94, 293.66, 370.0, 440.0]  // Bm7b5
    ];
    let chordIdx = 0;

    const playChordStep = () => {
      if (!isMusicPlaying || !musicAudioCtx) return;
      try {
        const chord = chords[chordIdx % chords.length];
        chordIdx++;
        const t = ctx.currentTime;
        chord.forEach(freq => {
          const osc = ctx.createOscillator();
          const g = ctx.createGain();
          const f = ctx.createBiquadFilter();

          osc.type = "triangle";
          osc.frequency.setValueAtTime(freq, t);

          f.type = "lowpass";
          f.frequency.setValueAtTime(950, t);

          g.gain.setValueAtTime(0.001, t);
          g.gain.linearRampToValueAtTime(0.09, t + 0.3);
          g.gain.exponentialRampToValueAtTime(0.001, t + 2.4);

          osc.connect(f);
          f.connect(g);
          g.connect(master);

          osc.start(t);
          osc.stop(t + 2.5);
        });
      } catch (_) {}
    };

    playChordStep();
    const lofiInt = safeSetInterval(playChordStep, 2500);
    musicActiveIntervals.push(lofiInt);

  } else if (trackType === "meditation") {
    // Deep Meditation: 432Hz fundamental + 528Hz Solfeggio harmony + 108Hz sub-bass
    const freqs = [108, 216, 432, 528];
    freqs.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const g = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(freq + (idx === 2 ? 0.2 : 0), now); // Subtle binaural beat

      const baseAmp = idx === 0 ? 0.22 : (idx === 2 ? 0.16 : 0.10);
      g.gain.setValueAtTime(baseAmp, now);

      osc.connect(g);
      g.connect(master);
      osc.start();
      musicActiveNodes.push(osc, g);
    });

  } else if (trackType === "forest") {
    // Whispering Forest & Birds: soft wind background + periodic sweet birdsong
    const noiseBuffer = generatePinkNoiseBuffer(ctx, 3);
    const noiseSource = ctx.createBufferSource();
    noiseSource.buffer = noiseBuffer;
    noiseSource.loop = true;

    const windFilter = ctx.createBiquadFilter();
    windFilter.type = "bandpass";
    windFilter.frequency.setValueAtTime(1400, now);
    windFilter.Q.setValueAtTime(0.5, now);

    const windGain = ctx.createGain();
    windGain.gain.setValueAtTime(0.18, now);

    noiseSource.connect(windFilter);
    windFilter.connect(windGain);
    windGain.connect(master);
    noiseSource.start();
    musicActiveNodes.push(noiseSource, windFilter, windGain);

    // Periodic cheerful, gentle birdsong chirp
    const birdInt = safeSetInterval(() => {
      if (!isMusicPlaying || !musicAudioCtx) return;
      try {
        const t = ctx.currentTime;
        const bOsc = ctx.createOscillator();
        const bGain = ctx.createGain();
        bOsc.type = "sine";

        const startFreq = 2400 + Math.random() * 800;
        bOsc.frequency.setValueAtTime(startFreq, t);
        bOsc.frequency.exponentialRampToValueAtTime(startFreq + 900, t + 0.12);
        bOsc.frequency.exponentialRampToValueAtTime(startFreq + 300, t + 0.22);

        bGain.gain.setValueAtTime(0.001, t);
        bGain.gain.linearRampToValueAtTime(0.08, t + 0.05);
        bGain.gain.exponentialRampToValueAtTime(0.001, t + 0.25);

        bOsc.connect(bGain);
        bGain.connect(master);
        bOsc.start(t);
        bOsc.stop(t + 0.26);
      } catch (_) {}
    }, 4500);
    musicActiveIntervals.push(birdInt);

  } else if (trackType === "starlight") {
    // Celestial Starlight: floating triad pads with slow sweep
    const chordPad = [261.63, 329.63, 392.00, 523.25]; // Cmaj
    chordPad.forEach(freq => {
      const osc = ctx.createOscillator();
      const g = ctx.createGain();
      const f = ctx.createBiquadFilter();

      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, now);

      f.type = "lowpass";
      f.frequency.setValueAtTime(650, now);

      g.gain.setValueAtTime(0.07, now);

      osc.connect(f);
      f.connect(g);
      g.connect(master);
      osc.start();
      musicActiveNodes.push(osc, f, g);
    });
  }
}

function updateMusicPlayerUI() {
  const track = calmMusicTracks.find(t => t.id === currentMusicTrackId) || calmMusicTracks[0];

  const iconEl = document.getElementById("music-current-icon");
  const catEl = document.getElementById("music-current-category");
  const freqEl = document.getElementById("music-current-freq");
  const titleEl = document.getElementById("music-current-title");
  const descEl = document.getElementById("music-current-desc");
  const liveBadge = document.getElementById("music-live-badge");
  const liveText = document.getElementById("music-live-status-text");
  const playLabel = document.getElementById("music-play-label");
  const playIcon = document.getElementById("music-play-icon");

  if (iconEl) iconEl.textContent = track.icon;
  if (catEl) catEl.textContent = track.category;
  if (freqEl) freqEl.textContent = track.freq;
  if (titleEl) titleEl.textContent = track.title;
  if (descEl) descEl.textContent = track.desc;

  if (liveBadge && liveText) {
    if (isMusicPlaying) {
      liveBadge.className = "music-live-badge playing";
      liveText.textContent = "Harmonizing Now";
    } else {
      liveBadge.className = "music-live-badge paused";
      liveText.textContent = "Paused";
    }
  }

  if (playLabel) {
    playLabel.textContent = isMusicPlaying ? "Pause Sound" : "Play Sound";
  }
  if (playIcon) {
    if (isMusicPlaying) {
      playIcon.innerHTML = `<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16" rx="1"></rect><rect x="14" y="4" width="4" height="16" rx="1"></rect></svg>`;
    } else {
      playIcon.innerHTML = `<svg viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>`;
    }
  }

  // Update track library cards active state
  document.querySelectorAll(".music-track-card").forEach(card => {
    const cardTrackId = card.getAttribute("data-track-id");
    card.classList.toggle("active", cardTrackId === currentMusicTrackId);
    const playBtn = card.querySelector(".btn-track-play");
    if (playBtn) {
      if (cardTrackId === currentMusicTrackId && isMusicPlaying) {
        playBtn.textContent = "Pause";
        playBtn.classList.add("playing");
      } else {
        playBtn.textContent = "Play Track";
        playBtn.classList.remove("playing");
      }
    }
  });
}

function playTrackById(trackId) {
  currentMusicTrackId = trackId;
  isMusicPlaying = true;
  startSoundscape(trackId);
  updateMusicPlayerUI();
  startMusicVisualizer();
}

function toggleCalmMusicPlayback() {
  if (isMusicPlaying) {
    isMusicPlaying = false;
    stopCurrentSoundNodes();
    updateMusicPlayerUI();
  } else {
    playTrackById(currentMusicTrackId);
  }
}

function stopCalmMusic() {
  isMusicPlaying = false;
  stopCurrentSoundNodes();
  if (musicTimerCountdownId) {
    safeClearInterval(musicTimerCountdownId);
    musicTimerCountdownId = null;
  }
  const timerDisplay = document.getElementById("music-timer-display");
  if (timerDisplay) timerDisplay.classList.add("hidden");
  updateMusicPlayerUI();
}

// Track navigation
function nextCalmMusicTrack() {
  const curIdx = calmMusicTracks.findIndex(t => t.id === currentMusicTrackId);
  const nextIdx = (curIdx + 1) % calmMusicTracks.length;
  playTrackById(calmMusicTracks[nextIdx].id);
}

function prevCalmMusicTrack() {
  const curIdx = calmMusicTracks.findIndex(t => t.id === currentMusicTrackId);
  const prevIdx = (curIdx - 1 + calmMusicTracks.length) % calmMusicTracks.length;
  playTrackById(calmMusicTracks[prevIdx].id);
}

// Sleep / Calm Timer
function setMusicTimer(minutes) {
  if (musicTimerCountdownId) {
    safeClearInterval(musicTimerCountdownId);
    musicTimerCountdownId = null;
  }
  musicTimerMinutes = minutes;
  const display = document.getElementById("music-timer-display");

  if (minutes <= 0) {
    musicTimerSecondsLeft = 0;
    if (display) display.classList.add("hidden");
    return;
  }

  musicTimerSecondsLeft = minutes * 60;
  if (display) {
    display.classList.remove("hidden");
    display.textContent = `${minutes}:00`;
  }

  musicTimerCountdownId = safeSetInterval(() => {
    musicTimerSecondsLeft--;
    if (musicTimerSecondsLeft <= 0) {
      safeClearInterval(musicTimerCountdownId);
      musicTimerCountdownId = null;
      stopCalmMusic();
      if (display) {
        display.textContent = "Complete ✨";
        setTimeout(() => display.classList.add("hidden"), 3000);
      }
      return;
    }
    const mins = Math.floor(musicTimerSecondsLeft / 60);
    const secs = musicTimerSecondsLeft % 60;
    if (display) {
      display.textContent = `${mins}:${secs < 10 ? "0" : ""}${secs}`;
    }
  }, 1000);
}

// Music Visualizer Canvas Rendering
function startMusicVisualizer() {
  const canvas = document.getElementById("music-visualizer-canvas");
  if (!canvas || typeof canvas.getContext !== "function") return;
  if (typeof canvas.getContext !== "function") return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  if (musicVisualizerRaf) {
    safeCancelAnimationFrame(musicVisualizerRaf);
    musicVisualizerRaf = null;
  }

  let phase = 0;
  const bufferLength = musicAnalyser ? musicAnalyser.frequencyBinCount : 64;
  const dataArray = new Uint8Array(bufferLength);

  function renderFrame() {
    musicVisualizerRaf = safeRequestAnimationFrame(renderFrame);

    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    let avgEnergy = 0;
    if (isMusicPlaying && musicAnalyser) {
      musicAnalyser.getByteFrequencyData(dataArray);
      let sum = 0;
      for (let i = 0; i < bufferLength; i++) sum += dataArray[i];
      avgEnergy = sum / bufferLength;
    } else {
      // Gentle breathing idle movement when paused
      avgEnergy = 12 + Math.sin(phase * 0.5) * 8;
    }

    phase += 0.035;

    if (musicVisualizerMode === "waves") {
      // Ambient Waves Mode: 3 smooth layered sinusoidal waves
      const waves = [
        { color: "rgba(255, 143, 171, 0.65)", amp: 14 + avgEnergy * 0.45, freq: 0.012, speed: 1.0, yOffset: h * 0.52 },
        { color: "rgba(168, 85, 247, 0.55)", amp: 18 + avgEnergy * 0.55, freq: 0.018, speed: -0.7, yOffset: h * 0.50 },
        { color: "rgba(56, 189, 248, 0.45)", amp: 10 + avgEnergy * 0.35, freq: 0.024, speed: 1.3, yOffset: h * 0.48 }
      ];

      waves.forEach(wave => {
        ctx.beginPath();
        ctx.moveTo(0, wave.yOffset);
        for (let x = 0; x < w; x += 4) {
          const binIndex = Math.min(Math.floor((x / w) * bufferLength), bufferLength - 1);
          const energyFactor = isMusicPlaying ? (dataArray[binIndex] / 255) * 12 : 0;
          const y = wave.yOffset + Math.sin(x * wave.freq + phase * wave.speed) * (wave.amp + energyFactor);
          ctx.lineTo(x, y);
        }
        ctx.strokeStyle = wave.color;
        ctx.lineWidth = 2.5;
        ctx.stroke();
      });

    } else {
      // Breathing Rings Mode: concentric pulsing circles
      const centerX = w / 2;
      const centerY = h / 2;
      const ringCount = 3;

      for (let r = 1; r <= ringCount; r++) {
        const radius = (r * 18) + (avgEnergy * 0.55 * r * 0.4) + Math.sin(phase + r) * 4;
        ctx.beginPath();
        ctx.arc(centerX, centerY, Math.max(radius, 6), 0, Math.PI * 2);
        const alpha = Math.max(0.15, 0.75 - r * 0.2);
        ctx.strokeStyle = r === 1
          ? `rgba(255, 143, 171, ${alpha})`
          : (r === 2 ? `rgba(168, 85, 247, ${alpha})` : `rgba(56, 189, 248, ${alpha})`);
        ctx.lineWidth = 2.2;
        ctx.stroke();
      }
    }
  }

  renderFrame();
}

function renderCalmMusicView() {
  updateMusicPlayerUI();
  startMusicVisualizer();
}

// Wire Calm Music Controls
const musicPlayBtn = document.getElementById("music-play-btn");
if (musicPlayBtn) musicPlayBtn.addEventListener("click", toggleCalmMusicPlayback);

const musicPrevBtn = document.getElementById("music-prev-btn");
if (musicPrevBtn) musicPrevBtn.addEventListener("click", prevCalmMusicTrack);

const musicNextBtn = document.getElementById("music-next-btn");
if (musicNextBtn) musicNextBtn.addEventListener("click", nextCalmMusicTrack);

const musicVolumeSlider = document.getElementById("music-volume-slider");
const musicVolumeText = document.getElementById("music-volume-text");
if (musicVolumeSlider) {
  musicVolumeSlider.addEventListener("input", (e) => {
    const val = parseInt(e.target.value, 10);
    musicVolumeLevel = val / 100;
    if (musicVolumeText) musicVolumeText.textContent = `${val}%`;
    if (musicMasterGain && musicAudioCtx) {
      musicMasterGain.gain.setValueAtTime(musicVolumeLevel, musicAudioCtx.currentTime);
    }
  });
}

// Calm Timer buttons
document.querySelectorAll(".music-timer-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".music-timer-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const mins = parseInt(btn.getAttribute("data-mins") || "0", 10);
    setMusicTimer(mins);
  });
});

// Visualizer Mode toggle buttons
const vizWavesBtn = document.getElementById("viz-mode-waves-btn");
const vizRingsBtn = document.getElementById("viz-mode-rings-btn");
if (vizWavesBtn) {
  vizWavesBtn.addEventListener("click", () => {
    musicVisualizerMode = "waves";
    vizWavesBtn.classList.add("active");
    if (vizRingsBtn) vizRingsBtn.classList.remove("active");
  });
}
if (vizRingsBtn) {
  vizRingsBtn.addEventListener("click", () => {
    musicVisualizerMode = "rings";
    vizRingsBtn.classList.add("active");
    if (vizWavesBtn) vizWavesBtn.classList.remove("active");
  });
}

// Track library card click delegates
document.querySelectorAll(".music-track-card").forEach(card => {
  card.addEventListener("click", (e) => {
    const trackId = card.getAttribute("data-track-id");
    if (!trackId) return;
    if (trackId === currentMusicTrackId && isMusicPlaying) {
      toggleCalmMusicPlayback();
    } else {
      playTrackById(trackId);
    }
  });
});

// ==================== VIEW 11: MINDFUL GAMES ENGINE ====================
let activeMindfulGame = "bubble";
let bubblesPoppedCount = 0;
const bubbleAffirmations = [
  "Breathe 🌸",
  "Let go ✨",
  "Peace 🕊️",
  "You are enough 💖",
  "Present moment 🍃",
  "Lightness ☀️",
  "Unwind 🪷",
  "Calm 🌊",
  "Grace 🌿",
  "Gentle thoughts 💜"
];

// Tab Switching
const gameTabs = {
  bubble: document.getElementById("game-tab-bubble"),
  pattern: document.getElementById("game-tab-pattern"),
  memory: document.getElementById("game-tab-memory")
};
const gamePanels = {
  bubble: document.getElementById("game-panel-bubble"),
  pattern: document.getElementById("game-panel-pattern"),
  memory: document.getElementById("game-panel-memory")
};

function switchMindfulGameTab(gameKey) {
  activeMindfulGame = gameKey;
  Object.keys(gameTabs).forEach(k => {
    if (gameTabs[k]) gameTabs[k].classList.toggle("active", k === gameKey);
  });
  Object.keys(gamePanels).forEach(k => {
    if (gamePanels[k]) gamePanels[k].classList.toggle("hidden", k !== gameKey);
  });

  if (gameKey === "pattern") {
    resizePatternCanvas();
  }
}

Object.keys(gameTabs).forEach(k => {
  if (gameTabs[k]) {
    gameTabs[k].addEventListener("click", () => switchMindfulGameTab(k));
  }
});

// ---------- Game 1: Zen Bubble Pop ----------
function spawnZenBubble(arena, index) {
  const bubble = document.createElement("div");
  bubble.className = "zen-bubble";
  const size = Math.floor(48 + Math.random() * 32);
  bubble.style.width = `${size}px`;
  bubble.style.height = `${size}px`;
  bubble.style.left = `${Math.floor(4 + Math.random() * 88)}%`;
  bubble.style.top = `${Math.floor(6 + Math.random() * 80)}%`;
  bubble.style.animationDelay = `${(Math.random() * 3).toFixed(1)}s`;
  bubble.style.animationDuration = `${(4 + Math.random() * 3).toFixed(1)}s`;

  bubble.addEventListener("click", (e) => {
    e.stopPropagation();
    popZenBubble(bubble, arena, e);
  });

  arena.appendChild(bubble);
}

function popZenBubble(bubble, arena, e) {
  bubblesPoppedCount++;
  const countEl = document.getElementById("bubble-count-num");
  if (countEl) countEl.textContent = bubblesPoppedCount;

  // Gentle chime
  playGentleChime(520 + Math.random() * 360, 0.14);

  // Position for float word
  const arenaRect = arena.getBoundingClientRect();
  const clickX = e.clientX - arenaRect.left;
  const clickY = e.clientY - arenaRect.top;

  // Create floating affirmation word
  const wordEl = document.createElement("div");
  wordEl.className = "bubble-pop-float-word";
  const word = bubbleAffirmations[Math.floor(Math.random() * bubbleAffirmations.length)];
  wordEl.textContent = word;
  wordEl.style.left = `${Math.max(10, Math.min(clickX - 30, arenaRect.width - 90))}px`;
  wordEl.style.top = `${Math.max(10, clickY - 20)}px`;
  arena.appendChild(wordEl);
  setTimeout(() => wordEl.remove(), 1200);

  // Update encouragement HUD
  const affirmMsg = document.getElementById("bubble-affirmation-msg");
  if (affirmMsg) {
    affirmMsg.textContent = `${word} ~ Feel your shoulders soften`;
  }

  // Pop burst ring
  const burst = document.createElement("div");
  burst.className = "bubble-pop-particle";
  burst.style.left = `${clickX}px`;
  burst.style.top = `${clickY}px`;
  arena.appendChild(burst);
  setTimeout(() => burst.remove(), 600);

  // Remove bubble and respawn new bubble after 1.2s
  bubble.remove();
  setTimeout(() => {
    if (arena.children.length < 20) {
      spawnZenBubble(arena, Math.random());
    }
  }, 1200);
}

function initBubblePopGame() {
  const arena = document.getElementById("bubble-arena");
  if (!arena) return;
  arena.innerHTML = "";
  for (let i = 0; i < 18; i++) {
    spawnZenBubble(arena, i);
  }
}

const bubbleRefillBtn = document.getElementById("bubble-refill-btn");
if (bubbleRefillBtn) {
  bubbleRefillBtn.addEventListener("click", () => {
    initBubblePopGame();
    const affirmMsg = document.getElementById("bubble-affirmation-msg");
    if (affirmMsg) affirmMsg.textContent = "Arena refreshed! Pop gently at your own pace 🫧";
  });
}

// ---------- Game 2: Color & Pattern Flow ----------
const patternPalettes = {
  sunset: ["#FF758C", "#FF7EB3", "#FFA07A", "#FBBF24", "#F472B6"],
  ocean: ["#38BDF8", "#0284C7", "#2DD4BF", "#818CF8", "#67E8F9"],
  cherry: ["#FDA4AF", "#F43F5E", "#F472B6", "#FFE4E6", "#FB7185"],
  aurora: ["#34D399", "#10B981", "#06B6D4", "#A855F7", "#818CF8"]
};
let currentPaletteKey = "sunset";
let patternChimesEnabled = true;
let patternRipples = [];
let patternRafId = null;

const pentatonicScale = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25]; // C4, D4, E4, G4, A4, C5

function playPentatonicChime() {
  if (!patternChimesEnabled) return;
  const note = pentatonicScale[Math.floor(Math.random() * pentatonicScale.length)];
  playGentleChime(note, 0.35);
}

function resizePatternCanvas() {
  const canvas = document.getElementById("pattern-flow-canvas");
  if (!canvas) return;
  const parent = canvas.parentElement;
  if (parent && parent.clientWidth > 0) {
    canvas.width = parent.clientWidth;
    canvas.height = 340;
  }
}

function addPatternRipple(x, y) {
  const colors = patternPalettes[currentPaletteKey] || patternPalettes.sunset;
  const color = colors[Math.floor(Math.random() * colors.length)];
  patternRipples.push({
    x,
    y,
    radius: 4,
    maxRadius: 75 + Math.random() * 35,
    color,
    alpha: 0.85,
    speed: 1.8 + Math.random() * 1.2
  });

  if (patternRipples.length > 50) {
    patternRipples.shift();
  }
  playPentatonicChime();
}

function initPatternFlowGame() {
  const canvas = document.getElementById("pattern-flow-canvas");
  if (!canvas) return;
  resizePatternCanvas();
  if (typeof window !== "undefined" && typeof window.addEventListener === "function") {
    window.addEventListener("resize", resizePatternCanvas);
  }

  let isPointerDown = false;

  canvas.addEventListener("pointerdown", (e) => {
    isPointerDown = true;
    const rect = canvas.getBoundingClientRect();
    addPatternRipple(e.clientX - rect.left, e.clientY - rect.top);
  });

  canvas.addEventListener("pointermove", (e) => {
    if (!isPointerDown) return;
    const rect = canvas.getBoundingClientRect();
    if (Math.random() > 0.4) {
      addPatternRipple(e.clientX - rect.left, e.clientY - rect.top);
    }
  });

  if (typeof window !== "undefined" && typeof window.addEventListener === "function") {
    window.addEventListener("pointerup", () => { isPointerDown = false; });
    window.addEventListener("pointercancel", () => { isPointerDown = false; });
  }

  if (typeof canvas.getContext !== "function") return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  if (patternRafId) safeCancelAnimationFrame(patternRafId);

  function animatePattern() {
    patternRafId = safeRequestAnimationFrame(animatePattern);

    // Soft trail fade
    ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (let i = patternRipples.length - 1; i >= 0; i--) {
      const rip = patternRipples[i];
      rip.radius += rip.speed;
      rip.alpha -= 0.012;

      if (rip.alpha <= 0 || rip.radius >= rip.maxRadius) {
        patternRipples.splice(i, 1);
        continue;
      }

      ctx.save();
      ctx.beginPath();
      ctx.arc(rip.x, rip.y, rip.radius, 0, Math.PI * 2);
      ctx.strokeStyle = rip.color;
      ctx.globalAlpha = Math.max(0, rip.alpha);
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Soft center halo
      ctx.beginPath();
      ctx.arc(rip.x, rip.y, Math.max(2, rip.radius * 0.4), 0, Math.PI * 2);
      ctx.fillStyle = rip.color;
      ctx.globalAlpha = Math.max(0, rip.alpha * 0.25);
      ctx.fill();
      ctx.restore();
    }
  }

  animatePattern();
}

// Palette chips
document.querySelectorAll(".palette-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    document.querySelectorAll(".palette-chip").forEach(c => c.classList.remove("active"));
    chip.classList.add("active");
    currentPaletteKey = chip.getAttribute("data-palette") || "sunset";
  });
});

// Chimes toggle
const patternChimesBtn = document.getElementById("pattern-chimes-toggle-btn");
const patternChimesLabel = document.getElementById("pattern-chimes-label");
if (patternChimesBtn) {
  patternChimesBtn.addEventListener("click", () => {
    patternChimesEnabled = !patternChimesEnabled;
    if (patternChimesLabel) {
      patternChimesLabel.textContent = patternChimesEnabled ? "🔔 Chimes: On" : "🔕 Chimes: Mute";
    }
  });
}

// Clear canvas
const patternClearBtn = document.getElementById("pattern-clear-btn");
if (patternClearBtn) {
  patternClearBtn.addEventListener("click", () => {
    patternRipples = [];
    const canvas = document.getElementById("pattern-flow-canvas");
    if (canvas && typeof canvas.getContext === "function") {
      const ctx = canvas.getContext("2d");
      if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  });
}

// ---------- Game 3: Mindful Memory Garden ----------
const memoryBotanicals = [
  { id: "lotus", emoji: "🪷", name: "Lotus", virtue: "Inner Peace" },
  { id: "sunflower", emoji: "🌻", name: "Sunflower", virtue: "Vitality" },
  { id: "lavender", emoji: "🪻", name: "Lavender", virtue: "Deep Calm" },
  { id: "clover", emoji: "🍀", name: "Clover", virtue: "Good Energy" },
  { id: "blossom", emoji: "🌸", name: "Blossom", virtue: "Renewal" },
  { id: "bonsai", emoji: "🪴", name: "Bonsai", virtue: "Patience" }
];

let memoryCardsState = [];
let memoryFlippedCards = [];
let memoryMatchedPairsCount = 0;
let memoryMovesCount = 0;
let isMemoryBoardLocked = false;

function initMemoryGardenGame() {
  const grid = document.getElementById("memory-garden-grid");
  const successBanner = document.getElementById("memory-garden-success");
  const matchesEl = document.getElementById("memory-matched-pairs");
  const movesEl = document.getElementById("memory-moves-num");

  if (!grid) return;
  if (successBanner) successBanner.classList.add("hidden");

  memoryMatchedPairsCount = 0;
  memoryMovesCount = 0;
  memoryFlippedCards = [];
  isMemoryBoardLocked = false;

  if (matchesEl) matchesEl.textContent = "0";
  if (movesEl) movesEl.textContent = "0";

  // Create 12 cards (6 pairs)
  const deck = [];
  memoryBotanicals.forEach(botanical => {
    deck.push({ ...botanical, uid: `${botanical.id}_1` });
    deck.push({ ...botanical, uid: `${botanical.id}_2` });
  });

  // Fisher-Yates Shuffle
  for (let i = deck.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [deck[i], deck[j]] = [deck[j], deck[i]];
  }

  memoryCardsState = deck;
  grid.innerHTML = "";

  deck.forEach((card, idx) => {
    const cardEl = document.createElement("div");
    cardEl.className = "memory-card";
    cardEl.setAttribute("data-uid", card.uid);
    cardEl.setAttribute("data-id", card.id);

    cardEl.innerHTML = `
      <div class="memory-card-inner">
        <div class="memory-card-front">
          <span class="card-sprout-icon">🌱</span>
          <span class="card-hint-text">Breathe</span>
        </div>
        <div class="memory-card-back">
          <span class="card-botanical-emoji">${card.emoji}</span>
          <strong class="card-botanical-name">${card.name}</strong>
          <span class="card-botanical-virtue">${card.virtue}</span>
        </div>
      </div>
    `;

    cardEl.addEventListener("click", () => handleMemoryCardClick(cardEl, card));
    grid.appendChild(cardEl);
  });
}

function handleMemoryCardClick(cardEl, cardData) {
  if (isMemoryBoardLocked) return;
  if (cardEl.classList.contains("flipped") || cardEl.classList.contains("matched")) return;

  playGentleChime(420, 0.12);
  cardEl.classList.add("flipped");
  memoryFlippedCards.push({ el: cardEl, data: cardData });

  if (memoryFlippedCards.length === 2) {
    memoryMovesCount++;
    const movesEl = document.getElementById("memory-moves-num");
    if (movesEl) movesEl.textContent = memoryMovesCount;

    const [first, second] = memoryFlippedCards;
    if (first.data.id === second.data.id) {
      // Match found
      setTimeout(() => {
        playGentleChime(528, 0.3);
        first.el.classList.add("matched");
        second.el.classList.add("matched");
        memoryMatchedPairsCount++;

        const matchesEl = document.getElementById("memory-matched-pairs");
        if (matchesEl) matchesEl.textContent = memoryMatchedPairsCount;

        memoryFlippedCards = [];

        // All matched!
        if (memoryMatchedPairsCount === memoryBotanicals.length) {
          setTimeout(() => {
            const successBanner = document.getElementById("memory-garden-success");
            if (successBanner) successBanner.classList.remove("hidden");
            playGentleChime(659.25, 0.45);
          }, 400);
        }
      }, 350);

    } else {
      // Mismatch: flip back after 900ms
      isMemoryBoardLocked = true;
      setTimeout(() => {
        first.el.classList.remove("flipped");
        second.el.classList.remove("flipped");
        memoryFlippedCards = [];
        isMemoryBoardLocked = false;
      }, 900);
    }
  }
}

const memoryRestartBtn = document.getElementById("memory-restart-btn");
if (memoryRestartBtn) memoryRestartBtn.addEventListener("click", initMemoryGardenGame);

const memoryPlayAgainBtn = document.getElementById("memory-play-again-btn");
if (memoryPlayAgainBtn) memoryPlayAgainBtn.addEventListener("click", initMemoryGardenGame);

function renderMindfulGamesView() {
  switchMindfulGameTab(activeMindfulGame);
}

// Initial initialization
renderAllWellbeingViews();
renderResourcesLibrary();
renderTodaysThought();
initBubblePopGame();
initPatternFlowGame();
initMemoryGardenGame();

// ==================== TASK 3 & 5: GREETING AUDIO & PROFILE/LOGOUT ====================
function playShortGreeting() {
  const shortGreeting = (state.isGuest || !state.currentUserName || state.currentUserName === "Friend")
    ? "Hello! How are you today?"
    : `Hello, ${state.currentUserName}! How are you today?`;
  speak(shortGreeting);
}

if (hearGreetingBtn) {
  hearGreetingBtn.addEventListener("click", () => {
    playShortGreeting();
  });
}

if (chatHearGreetingBtn) {
  chatHearGreetingBtn.addEventListener("click", () => {
    speak("Hey! I'm here. What's on your mind today?");
  });
}

// Remembered Login Identifier Retrieval
try {
  const savedId = localStorage.getItem("mannmitra_remembered_id");
  if (savedId && loginEmailInput) {
    loginEmailInput.value = savedId;
    if (rememberMeCheckbox) rememberMeCheckbox.checked = true;
  }
} catch (_) {}

// Header Profile Dropdown
if (headerProfilePill && headerProfileDropdown) {
  headerProfilePill.addEventListener("click", (e) => {
    e.stopPropagation();
    const isHidden = headerProfileDropdown.classList.contains("hidden");
    headerProfileDropdown.classList.toggle("hidden", !isHidden);
    headerProfilePill.setAttribute("aria-expanded", isHidden ? "true" : "false");
  });

  document.addEventListener("click", (e) => {
    if (!headerProfileDropdown.contains(e.target) && !headerProfilePill.contains(e.target)) {
      headerProfileDropdown.classList.add("hidden");
      headerProfilePill.setAttribute("aria-expanded", "false");
    }
  });
}

if (profileViewSettingsBtn) {
  profileViewSettingsBtn.addEventListener("click", () => {
    if (headerProfileDropdown) headerProfileDropdown.classList.add("hidden");
    navigateTo("settings");
  });
}

// Logout Confirmation Flow
if (profileLogoutBtn) {
  profileLogoutBtn.addEventListener("click", () => {
    if (headerProfileDropdown) headerProfileDropdown.classList.add("hidden");
    if (logoutConfirmModal) logoutConfirmModal.classList.remove("hidden");
  });
}

if (logoutCancelBtn && logoutConfirmModal) {
  logoutCancelBtn.addEventListener("click", () => {
    logoutConfirmModal.classList.add("hidden");
  });
}

function resetUserSessionState() {
  // 1. Invalidate any in-flight chat requests and clear chat state
  sessionEpoch++;
  conversationHistory = [];
  pendingRequests.forEach((_, reqId) => removeStatusIndicator(reqId));
  pendingRequests.clear();

  // 2. Stop active breathing exercises and clear timers safely
  stopPageBreathing();
  if (breatheCompletionCard) breatheCompletionCard.classList.add("hidden");
  stopBreathingCycle();
  if (breathingOverlay) breathingOverlay.classList.add("hidden");
  if (typeof stopCalmMusic === "function") stopCalmMusic();

  // 3. Close any active overlays or modals and stop speech
  closeOrbMode();
  if (libDetailModal && !libDetailModal.classList.contains("hidden")) {
    closeGuideDetail();
  }

  // 4. Clear user-specific in-memory data
  state.currentMood = null;
  state.moodEntries = [];
  state.sessionActivities = [];
  state.sessionStats = {
    mindfulMinutes: 0,
    breathingSessionsCompleted: 0,
    journeysCompleted: 0,
  };
  state.completedPathways.clear();
  state.journeyUserInputs = {};
  state.bookmarkedGuides.clear();
  state.currentIntention = "Breathe before reacting";
  state.greetingSpoken = false;
  state.isGuest = false;
  lastMoodLogTime = 0;
  lastMoodLogVal = null;
  selectedMoodForLogging = "Good";

  // 5. Exit active guided pathway and clear transient inputs
  exitJourney();
  if (textInput) textInput.value = "";
  if (moodNoteInput) moodNoteInput.value = "";
  if (customIntentionInput) customIntentionInput.value = "";
  if (libSearchInput) libSearchInput.value = "";
  if (campusSearchInput) campusSearchInput.value = "";
  activeLibCategory = "all";

  // 6. Reset user-specific UI elements
  if (chatWindow) {
    chatWindow.querySelectorAll(".dynamic-chat-msg").forEach(el => el.remove());
  }
  if (crisisBanner) crisisBanner.classList.add("hidden");
  if (helplineList) helplineList.innerHTML = "";
  const moodResponseBanner = document.getElementById("mood-response-banner");
  if (moodResponseBanner) {
    moodResponseBanner.textContent = "";
    moodResponseBanner.classList.add("hidden");
  }
  if (moodSaveStatus) moodSaveStatus.classList.add("hidden");
  moodSelectButtons.forEach(btn => {
    btn.classList.toggle("selected", btn.getAttribute("data-mood") === "Good");
  });
  intentionChips.forEach(chip => {
    chip.classList.toggle("active", chip.getAttribute("data-intention") === state.currentIntention);
  });
  updateUserNameDisplays("Vyankatesh");

  // 7. Re-render clean logged-out views (appearance preferences & remembered ID stay intact)
  renderAllWellbeingViews();
  renderGuidedSupportView();
  renderResourcesLibrary();
  filterCampusCards("all");
  navigateTo("chat");
  setActiveChatTab("chat");
}

if (logoutConfirmBtn) {
  logoutConfirmBtn.addEventListener("click", () => {
    if (logoutConfirmModal) logoutConfirmModal.classList.add("hidden");
    resetUserSessionState();
    if (desktopDashboard) desktopDashboard.classList.add("hidden");
    if (greetingOverlay) greetingOverlay.classList.add("hidden");
    if (loginView) loginView.classList.remove("hidden");
    if (loginPasswordInput) loginPasswordInput.value = "";
    if (loginErrorBanner) loginErrorBanner.classList.add("hidden");
  });
}
