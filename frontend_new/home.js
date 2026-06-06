const BASE_URL = "http://127.0.0.1:8000";
const FRONTEND_BUILD = "home.js v44";

let isProcessing = false;
let keepDetectModalOpen = false;
let allowManualClose = false;
let modalGuardObserver = null;
let modalGuardTimer = null;
let historyManageMode = false;

function updateDebug(msg) {
  const panel = document.getElementById("debugPanel");
  if (panel) {
    const time = new Date().toLocaleTimeString();
    panel.innerHTML = `[${time}] ${msg}<br>` + panel.innerHTML;
  }
  console.log(msg);
}

function escapeHtml(text) {
  if (text === null || text === undefined) return "";
  const div = document.createElement("div");
  div.textContent = String(text);
  return div.innerHTML;
}

function normalizeConfidence(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return 0;
  if (n > 1) return Math.max(0, Math.min(n / 100, 1));
  return Math.max(0, Math.min(n, 1));
}

async function translateUiStrings(strings) {
  const lang = (localStorage.getItem("selectedLanguage") || "en").toLowerCase();
  if (lang === "en" || typeof window.translateTextBatch !== "function") {
    return strings;
  }
  try {
    return await window.translateTextBatch(strings, lang);
  } catch {
    return strings;
  }
}

async function tOne(text) {
  const translated = await translateUiStrings([text]);
  return translated[0] || text;
}

async function translateValueText(text) {
  const value = String(text || "").trim();
  if (!value) return "";
  const [translated] = await translateUiStrings([value]);
  return translated || value;
}

async function showLocalizedAlert(text) {
  alert(await tOne(text));
}

async function parseApiPayload(res) {
  const contentType = (res.headers.get("content-type") || "").toLowerCase();
  if (contentType.includes("application/json")) {
    try {
      return await res.json();
    } catch {
      return {};
    }
  }

  const raw = await res.text();
  const cleaned = String(raw || "").replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
  return { message: cleaned || `HTTP ${res.status}` };
}

function getAuthHeaders() {
  const token = localStorage.getItem("token");
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

function isLoggedIn() {
  return Boolean(localStorage.getItem("token"));
}

function applyTheme(mode) {
  const body = document.body;
  if (!body) return;
  if (mode === "dark") {
    body.classList.add("dark-mode");
  } else {
    body.classList.remove("dark-mode");
  }
  localStorage.setItem("themeMode", mode);
}

function initTheme() {
  const saved = localStorage.getItem("themeMode") || "light";
  applyTheme(saved);
  const toggle = document.getElementById("themeToggle");
  if (toggle) toggle.checked = saved === "dark";
}

function ensureUserIdFromToken() {
  const existing = localStorage.getItem("userId");
  if (existing) return existing;

  const token = localStorage.getItem("token");
  if (!token) return "";

  try {
    const parts = token.split(".");
    if (parts.length < 2) return "";
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
    const payload = JSON.parse(atob(padded));
    const userId = payload.user_id || payload.userId || "";
    if (userId) localStorage.setItem("userId", userId);
    return userId;
  } catch {
    return "";
  }
}

function ensureModalVisible() {
  const modal = document.getElementById("chatModal");
  if (!modal) return;
  if (!keepDetectModalOpen) return;

  if (window.getComputedStyle(modal).display === "none") {
    modal.style.setProperty("display", "flex", "important");
    updateDebug("Modal restored");
  }
}

function startModalGuard() {
  const modal = document.getElementById("chatModal");
  if (!modal) return;

  if (modalGuardObserver) modalGuardObserver.disconnect();
  modalGuardObserver = new MutationObserver(() => ensureModalVisible());
  modalGuardObserver.observe(modal, { attributes: true, attributeFilter: ["style", "class"] });

  if (modalGuardTimer) clearInterval(modalGuardTimer);
  modalGuardTimer = setInterval(ensureModalVisible, 80);
}

function stopModalGuard() {
  if (modalGuardObserver) {
    modalGuardObserver.disconnect();
    modalGuardObserver = null;
  }
  if (modalGuardTimer) {
    clearInterval(modalGuardTimer);
    modalGuardTimer = null;
  }
}

function openChat() {
  const modal = document.getElementById("chatModal");
  const resultBox = document.getElementById("detectionResult");
  const container = document.getElementById("imagePreviewContainer");
  const input = document.getElementById("imageInput");

  keepDetectModalOpen = true;
  allowManualClose = false;

  if (modal) {
    modal.style.setProperty("display", "flex", "important");
  }
  if (resultBox) resultBox.innerHTML = "";
  if (container) container.style.display = "none";
  if (input) input.value = "";

  startModalGuard();
  updateDebug("Modal opened");
}

function closeChat(mode = "auto") {
  if (!allowManualClose && mode !== "force") {
    ensureModalVisible();
    updateDebug("Auto-close blocked");
    return;
  }

  if (isProcessing && mode !== "force") {
    showLocalizedAlert("Please wait for detection to complete");
    return;
  }

  const modal = document.getElementById("chatModal");
  keepDetectModalOpen = false;
  allowManualClose = false;

  stopModalGuard();

  if (modal) {
    modal.style.display = "none";
    modal.classList.remove("modal-locked");
  }

  updateDebug("Modal closed");
}

function requestManualClose() {
  allowManualClose = true;
  closeChat("manual");
}

async function renderDetectionResult(data) {
  const resultBox = document.getElementById("detectionResult");
  if (!resultBox) return;

  const labels = await translateUiStrings([
    "Detection Complete",
    "AI-powered analysis",
    "Crop Name",
    "Disease",
    "Confidence Score",
    "Treatment / Cure",
    "References",
    "Top 3 Predictions",
    "Close"
  ]);

  const rawCropName = data.crop_name || "Unknown";
  const rawDiseaseName = data.disease || "Unknown";
  const details = data.details || {};
  const rawCureText = details.cure || data.treatment || "";
  const rawReferenceText = details.reference || details.references || "";

  const top3 = Array.isArray(data.top_3) ? data.top_3.slice(0, 3) : [];
  const valueInputs = [rawCropName, rawDiseaseName, rawCureText, rawReferenceText];
  top3.forEach((pred) => {
    valueInputs.push(pred.class_name || pred.class || "Unknown");
  });
  const valueOutputs = await translateUiStrings(valueInputs);

  const cropName = escapeHtml(valueOutputs[0] || rawCropName);
  const diseaseName = escapeHtml(valueOutputs[1] || rawDiseaseName);
  const cureText = escapeHtml(valueOutputs[2] || rawCureText);
  const referenceText = escapeHtml(valueOutputs[3] || rawReferenceText);

  const confidenceValue = normalizeConfidence(data.confidence);
  const confidencePct = Math.round(confidenceValue * 100);
  const circumference = 2 * Math.PI * 35;
  const dashOffset = circumference * (1 - confidenceValue);

  const top3Html = top3.map((pred, idx) => {
    const translatedName = valueOutputs[4 + idx] || pred.class_name || pred.class || "Unknown";
    const name = escapeHtml(translatedName);
    const conf = Math.round(normalizeConfidence(pred.confidence) * 100);
    const barClass = idx === 0 ? "detect-top-bar best" : "detect-top-bar";

    return `
      <div class="detect-top-item">
        <div class="detect-top-rank">${idx + 1}.</div>
        <div class="detect-top-main">
          <div class="detect-top-line">
            <span>${name}</span>
            <span>${conf}%</span>
          </div>
          <div class="detect-top-track">
            <div class="${barClass}" style="width:${conf}%;"></div>
          </div>
        </div>
      </div>
    `;
  }).join("");

  resultBox.innerHTML = `
    <div class="detect-result-wrap">
      <div class="detect-hero">
        <div class="detect-hero-icon">🌿</div>
        <h3>${labels[0]}</h3>
        <p>${labels[1]}</p>
      </div>

      <div class="detect-info-grid">
        <div class="detect-info-tile">
          <div class="detect-info-emoji">🌾</div>
          <div class="detect-info-label">${labels[2]}</div>
          <div class="detect-info-value crop">${cropName}</div>
        </div>
        <div class="detect-info-tile">
          <div class="detect-info-emoji">🦠</div>
          <div class="detect-info-label">${labels[3]}</div>
          <div class="detect-info-value disease">${diseaseName}</div>
        </div>
      </div>

      <div class="detect-card">
        <div class="detect-card-head">
          <div>
            <div class="detect-muted">${labels[4]}</div>
            <div class="detect-big">${confidencePct}%</div>
          </div>
          <div class="detect-ring">
            <svg width="80" height="80" viewBox="0 0 80 80">
              <circle cx="40" cy="40" r="35" class="detect-ring-bg"></circle>
              <circle cx="40" cy="40" r="35" class="detect-ring-fg" style="stroke-dasharray:${circumference};stroke-dashoffset:${dashOffset};"></circle>
            </svg>
            <span>${confidencePct}%</span>
          </div>
        </div>
        <div class="detect-progress-track">
          <div class="detect-progress-fill" style="width:${confidencePct}%;"></div>
        </div>
      </div>

      ${cureText ? `<div class="detect-card accent-success"><div class="detect-section-title">💊 ${labels[5]}</div><p>${cureText}</p></div>` : ""}
      ${referenceText ? `<div class="detect-card accent-info"><div class="detect-section-title">📚 ${labels[6]}</div><p>${referenceText}</p></div>` : ""}
      ${top3Html ? `<div class="detect-card"><div class="detect-section-title">📊 ${labels[7]}</div><div class="detect-top-list">${top3Html}</div></div>` : ""}

    </div>
  `;

  window.lastResult = data;
  updateDebug("Results displayed");
}

async function detectDisease(e) {
  if (e) {
    e.preventDefault();
    e.stopPropagation();
  }

  if (isProcessing) {
    showLocalizedAlert("Already processing, please wait");
    return;
  }

  const imageInput = document.getElementById("imageInput");
  const resultDiv = document.getElementById("detectionResult");
  const container = document.getElementById("imagePreviewContainer");
  const modal = document.getElementById("chatModal");

  if (!imageInput || !imageInput.files.length) {
    showLocalizedAlert("Please select an image first");
    return;
  }

  isProcessing = true;
  keepDetectModalOpen = true;
  allowManualClose = false;

  startModalGuard();

  if (modal) {
    modal.style.setProperty("display", "flex", "important");
    modal.classList.add("modal-locked");
  }
  if (container) container.style.display = "block";

  const loadingTexts = await translateUiStrings([
    "Analyzing your crop image...",
    "This may take a few seconds"
  ]);

  resultDiv.innerHTML = `
    <div class="detect-loading">
      <div class="detect-spinner"></div>
      <div class="detect-loading-title">${loadingTexts[0]}</div>
      <div class="detect-loading-subtitle">${loadingTexts[1]}</div>
    </div>
  `;

  try {
    updateDebug("Sending request...");

    const formData = new FormData();
    formData.append("image", imageInput.files[0]);

    const response = await fetch(`${BASE_URL}/api/detect/`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData
    });

    const rawText = await response.text();
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${rawText}`);
    }

    const data = JSON.parse(rawText);
    updateDebug("Response parsed");

    await renderDetectionResult(data);

  } catch (err) {
    const errorTexts = await translateUiStrings(["Detection Failed", "Try Again", "Close"]);

    updateDebug(`Error: ${err.message}`);
    resultDiv.innerHTML = `
      <div class="detect-error">
        <div class="detect-error-icon">❌</div>
        <div class="detect-error-title">${errorTexts[0]}</div>
        <div class="detect-error-message">${escapeHtml(err.message)}</div>
        <button type="button" onclick="detectDisease()">${errorTexts[1]}</button>
        <button type="button" style="margin-left:10px;" onclick="requestManualClose()">${errorTexts[2]}</button>
      </div>
    `;
  } finally {
    isProcessing = false;
    if (modal) modal.classList.remove("modal-locked");
    ensureModalVisible();
    updateDebug("Detection finished");
  }
}

function saveToHistory() {
  if (!window.lastResult) {
    showLocalizedAlert("No detection result to save.");
    return;
  }

  if (!isLoggedIn()) {
    showLocalizedAlert("History is available only for logged-in users.");
    return;
  }

  showLocalizedAlert("Detection results are saved automatically for logged-in users.");
}

async function sendMessage() {
  const input = document.getElementById("userInput");
  const message = input.value.trim();
  if (!message) return;

  const chatBox = document.getElementById("chatMessages");
  chatBox.innerHTML += `<div class="user-message">${escapeHtml(message)}</div>`;
  input.value = "";
  chatBox.scrollTop = chatBox.scrollHeight;

  const typingId = "typing-" + Date.now();
  chatBox.innerHTML += `<div class="bot-message" id="${typingId}">...</div>`;
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const response = await fetch(`${BASE_URL}/api/chat/message/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify({ message })
    });

    const data = await response.json();
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();

    const localizedReply = await translateValueText(data.reply || "");
    chatBox.innerHTML += `<div class="bot-message">${escapeHtml(localizedReply || data.reply || "")}</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;
  } catch (err) {
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();
    const serverErrorText = await tOne("Server error");
    chatBox.innerHTML += `<div class="bot-message" style="color:red;">${serverErrorText}: ${escapeHtml(err.message)}</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;
  }
}

async function searchMarket() {
  const crop = document.getElementById("cropName").value.trim();
  const location = document.getElementById("marketLocation").value.trim();
  const result = document.getElementById("marketResult");

  if (!crop || !location) {
    const [missingInputText] = await translateUiStrings([
      "Please enter both crop name and location."
    ]);
    result.innerHTML = `<p style="color:orange;">${escapeHtml(missingInputText)}</p>`;
    return;
  }

  const loadingText = await tOne("Fetching market price...");
  result.innerHTML = `⏳ ${escapeHtml(loadingText)}`;

  try {
    const userId = localStorage.getItem("userId") || ensureUserIdFromToken();
    const query = `${BASE_URL}/api/market-price/?crop_name=${encodeURIComponent(crop)}&region=${encodeURIComponent(location)}${userId ? `&user_id=${encodeURIComponent(userId)}` : ""}`;
    const response = await fetch(query, { headers: getAuthHeaders() });
    if (!response.ok) {
      let message = `Server error ${response.status}`;
      try {
        const errData = await response.json();
        message = errData.message || errData.error || message;
      } catch {
        // Keep default message.
      }
      throw new Error(message);
    }

    const data = await response.json();
    const marketLabels = await translateUiStrings([
      "Crop",
      "Region",
      "Min",
      "Max",
      "Avg"
    ]);
    const translatedCrop = await translateValueText(crop);
    const translatedRegion = await translateValueText(data.region || "");
    result.innerHTML = `
      <div style="padding:12px;background:#e8f5e9;border-radius:8px;margin-top:10px;">
        <strong>🌾 ${marketLabels[0]}:</strong> ${escapeHtml(translatedCrop || crop)}<br>
        <strong>📍 ${marketLabels[1]}:</strong> ${escapeHtml(translatedRegion || data.region)}<br>
        <strong>📉 ${marketLabels[2]}:</strong> ₹${data.min_price}<br>
        <strong>📈 ${marketLabels[3]}:</strong> ₹${data.max_price}<br>
        <strong>⚖️ ${marketLabels[4]}:</strong> ₹${data.avg_price}
      </div>
    `;
  } catch (err) {
    const errorText = await tOne("Error");
    result.innerHTML = `<p style="color:red;">${errorText}: ${escapeHtml(err.message)}</p>`;
  }
}

function openMarketChat() {
  document.getElementById("marketModal").style.display = "flex";
}

function closeMarketChat() {
  document.getElementById("marketModal").style.display = "none";
}

function openAIChat() {
  document.getElementById("aiChatModal").style.display = "flex";
}

function closeAIChat() {
  document.getElementById("aiChatModal").style.display = "none";
}

function openHelpModal() {
  const modal = document.getElementById("helpModal");
  if (modal) modal.style.display = "flex";
}

function closeHelpModal() {
  const modal = document.getElementById("helpModal");
  if (modal) modal.style.display = "none";
}

async function submitFeedback() {
  const nameEl = document.getElementById("feedbackName");
  const emailEl = document.getElementById("feedbackEmail");
  const msgEl = document.getElementById("feedbackMessage");
  const statusEl = document.getElementById("feedbackStatus");

  if (!nameEl || !emailEl || !msgEl || !statusEl) return;

  const name = nameEl.value.trim();
  const email = emailEl.value.trim() || (localStorage.getItem("userEmail") || "");
  const message = msgEl.value.trim();

  if (!name || !message) {
    statusEl.textContent = await tOne("Please enter your name and feedback message.");
    statusEl.style.color = "#c62828";
    return;
  }

  statusEl.textContent = await tOne("Submitting...");
  statusEl.style.color = "#2e7d32";

  try {
    const res = await fetch(`${BASE_URL}/api/feedback/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        email,
        message,
        page: "home"
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.message || "Failed to submit feedback");

    statusEl.textContent = await tOne("Thanks! Your feedback has been submitted.");
    statusEl.style.color = "#2e7d32";
    msgEl.value = "";
  } catch (err) {
    statusEl.textContent = `${await tOne("Error")}: ${err.message}`;
    statusEl.style.color = "#c62828";
  }
}

function saveLanguage() {
  const select = document.getElementById("languageSelect");
  if (!select) return;
  localStorage.setItem("selectedLanguage", select.value);
  if (typeof window.applySiteLanguage === "function") {
    window.applySiteLanguage(select.value);
  }
}

function toggleProfile() {
  document.getElementById("profileDropdown").classList.toggle("show-profile");
}

function closeProfileDropdown() {
  const dropdown = document.getElementById("profileDropdown");
  if (dropdown) dropdown.classList.remove("show-profile");
}

function refreshProfileUi() {
  const userType = localStorage.getItem("userType");
  const userName = localStorage.getItem("userName");
  const userEmail = localStorage.getItem("userEmail");

  const profileName = document.getElementById("profileName");
  const profileEmail = document.getElementById("profileEmail");
  if (profileName) profileName.innerText = userType === "guest" ? "Guest User" : (userName || "User");
  if (profileEmail) profileEmail.innerText = userType === "guest" ? "" : (userEmail || "");

  const authText = document.getElementById("authText");
  if (authText) authText.innerText = userType === "guest" ? "Login / Sign Up" : "Logout";

  const guestImage = document.getElementById("guestImage");
  const guestImageLarge = document.getElementById("guestImageLarge");
  const letterAvatar = document.getElementById("letterAvatar");
  const letterAvatarLarge = document.getElementById("letterAvatarLarge");
  const userLetter = document.getElementById("userLetter");
  const userLetterLarge = document.getElementById("userLetterLarge");

  if (userType !== "guest" && userName) {
    const letter = userName.charAt(0).toUpperCase();
    if (letterAvatar) letterAvatar.style.display = "flex";
    if (letterAvatarLarge) letterAvatarLarge.style.display = "flex";
    if (userLetter) userLetter.innerText = letter;
    if (userLetterLarge) userLetterLarge.innerText = letter;
    if (guestImage) guestImage.style.display = "none";
    if (guestImageLarge) guestImageLarge.style.display = "none";
  } else {
    if (letterAvatar) letterAvatar.style.display = "none";
    if (letterAvatarLarge) letterAvatarLarge.style.display = "none";
    if (guestImage) guestImage.style.display = "block";
    if (guestImageLarge) guestImageLarge.style.display = "block";
  }
}

function handleAuth() {
  const type = localStorage.getItem("userType");
  if (type === "guest") {
    window.location.href = "login.html";
  } else {
    const selectedLanguage = localStorage.getItem("selectedLanguage") || "en";
    localStorage.clear();
    localStorage.setItem("selectedLanguage", selectedLanguage);
    window.location.href = "login.html";
  }
}

async function getLocation() {
  closeProfileDropdown();
  if (!navigator.geolocation) {
    showLocalizedAlert("Geolocation is not supported.");
    return;
  }
  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      const lat = pos.coords.latitude;
      const lng = pos.coords.longitude;
      const locationValue = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;

      localStorage.setItem("userLocationLat", String(lat));
      localStorage.setItem("userLocationLng", String(lng));

      const marketLocation = document.getElementById("marketLocation");
      if (marketLocation) marketLocation.value = locationValue;

      openMarketChat();
      showLocalizedAlert("Location applied. You can now check market price.");
    },
    async () => {
      showLocalizedAlert("Location access denied.");
    }
  );
}

function openCamera() {
  const input = document.getElementById("imageInput");
  input.setAttribute("capture", "environment");
  input.click();
}

function triggerUpload() {
  const input = document.getElementById("imageInput");
  input.removeAttribute("capture");
  input.click();
}

function openHistory(manageMode = false) {
  closeProfileDropdown();
  const modal = document.getElementById("historyModal");
  const content = document.getElementById("historyContent");
  const actions = document.getElementById("historyActions");
  if (!modal || !content) return;
  historyManageMode = !!manageMode;
  if (actions) actions.style.display = historyManageMode ? "flex" : "none";
  content.innerHTML = '<p data-i18n>Loading activity history...</p>';
  modal.style.display = "flex";
  loadUnifiedHistory();
}

function getSelectedHistoryEntries() {
  const checked = Array.from(document.querySelectorAll(".history-check:checked"));
  return checked
    .map((el) => ({
      source: el.getAttribute("data-source") || "",
      record_id: el.getAttribute("data-record-id") || ""
    }))
    .filter((x) => x.source && x.record_id);
}

async function deleteSelectedHistory() {
  const entries = getSelectedHistoryEntries();
  if (!entries.length) {
    showLocalizedAlert("Select at least one activity item to delete.");
    return;
  }

  try {
    const res = await fetch(`${BASE_URL}/api/activity-history/delete/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify({ mode: "selected", entries })
    });
    const data = await parseApiPayload(res);
    if (!res.ok) throw new Error(data.message || "Delete failed");
    showLocalizedAlert("Selected activity deleted.");
    loadUnifiedHistory();
  } catch (err) {
    showLocalizedAlert(`Error: ${err.message}`);
  }
}

async function clearAllActivityHistory() {
  try {
    const res = await fetch(`${BASE_URL}/api/activity-history/delete/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify({ mode: "all" })
    });
    const data = await parseApiPayload(res);
    if (!res.ok) throw new Error(data.message || "Clear failed");
    showLocalizedAlert("Activity history cleared.");
    loadUnifiedHistory();
  } catch (err) {
    showLocalizedAlert(`Error: ${err.message}`);
  }
}

async function loadUnifiedHistory() {
  const content = document.getElementById("historyContent");
  if (!content) return;

  if (!isLoggedIn()) {
    content.innerHTML = `<p>${await tOne("No history available. Login to view full activity history.")}</p>`;
    return;
  }

  try {
    const res = await fetch(`${BASE_URL}/api/activity-history/`, {
      headers: getAuthHeaders()
    });

    if (!res.ok) {
      if (res.status === 401) {
        content.innerHTML = `<p>${await tOne("No history available. Login to view full activity history.")}</p>`;
        return;
      }
      throw new Error(`HTTP ${res.status}`);
    }

    const data = await res.json();
    const items = Array.isArray(data.items) ? data.items : [];

    if (!items.length) {
      content.innerHTML = `<p>${await tOne("No activity found yet.")}</p>`;
      return;
    }

    content.innerHTML = `
      <div class="history-list">
        ${items.slice(0, 40).map((item) => {
          const type = String(item.type || "").toLowerCase();
          const icon = type === "chat" ? "💬" : type === "market" ? "📈" : type === "schemes" ? "📋" : "🌿";
          const typeLabel = type === "schemes"
            ? ((item.meta && item.meta.action === "view") ? "Government Scheme View" : "Government Scheme Search")
            : type === "market"
              ? "Market Price Check"
              : type === "chat"
                ? "AI Chat"
                : type === "detection"
                  ? "Disease Detection"
                  : "Activity";
          const title = escapeHtml(item.title || "-");
          const subtitle = escapeHtml(item.subtitle || "-");
          const ts = item.timestamp ? new Date(item.timestamp).toLocaleString() : "-";
          const recordId = escapeHtml(item.record_id || "");
          const source = escapeHtml(item.source || "");

          let extra = "";
          if (type === "market" && item.meta) {
            extra = `<p><strong>Prices:</strong> Min ₹${item.meta.min_price ?? "-"}, Max ₹${item.meta.max_price ?? "-"}, Avg ₹${item.meta.avg_price ?? "-"}</p>`;
          } else if (type === "detection" && item.meta) {
            const conf = Math.round(normalizeConfidence(item.meta.confidence) * 100);
            extra = `<p><strong>Confidence:</strong> ${conf}%</p>`;
          } else if (type === "schemes" && item.meta) {
            if (item.meta.action === "view") {
              extra = item.meta.category
                ? `<p><strong>Category:</strong> ${escapeHtml(item.meta.category)}</p>`
                : "";
            }
          }

          return `
            <div class="history-item">
              <div class="history-head">
                <h5>${icon} ${title}</h5>
                ${(historyManageMode && recordId && source) ? `<input class="history-check" type="checkbox" data-record-id="${recordId}" data-source="${source}" />` : ""}
              </div>
              <p><strong>Type:</strong> ${escapeHtml(typeLabel)}</p>
              <p><strong>Details:</strong> ${subtitle}</p>
              ${extra}
              <p><strong>Time:</strong> ${escapeHtml(ts)}</p>
            </div>
          `;
        }).join("")}
      </div>
    `;

    if (typeof window.applySiteLanguage === "function") {
      window.applySiteLanguage(localStorage.getItem("selectedLanguage") || "en");
    }
  } catch (err) {
    content.innerHTML = `<p style="color:#c62828;">${await tOne("Failed to load history")}: ${escapeHtml(err.message)}</p>`;
  }
}

function openSettings() {
  closeProfileDropdown();
  const modal = document.getElementById("settingsModal");
  const nameEl = document.getElementById("settingsName");
  const emailEl = document.getElementById("settingsEmail");
  const statusEl = document.getElementById("settingsStatus");

  if (!modal || !nameEl || !emailEl || !statusEl) return;

  nameEl.value = localStorage.getItem("userName") || "";
  emailEl.value = localStorage.getItem("userEmail") || "";
  emailEl.readOnly = true;
  statusEl.textContent = "";

  const themeToggle = document.getElementById("themeToggle");
  if (themeToggle) {
    themeToggle.checked = (localStorage.getItem("themeMode") || "light") === "dark";
  }

  modal.style.display = "flex";
}

function closeHistoryModal() {
  const modal = document.getElementById("historyModal");
  if (modal) modal.style.display = "none";
}

function closeSettingsModal() {
  const modal = document.getElementById("settingsModal");
  if (modal) modal.style.display = "none";
}

async function saveProfileSettings() {
  const nameEl = document.getElementById("settingsName");
  const emailEl = document.getElementById("settingsEmail");
  const statusEl = document.getElementById("settingsStatus");
  if (!nameEl || !emailEl || !statusEl) return;

  const name = nameEl.value.trim();
  const email = emailEl.value.trim();

  if (!name) {
    statusEl.style.color = "#c62828";
    statusEl.textContent = await tOne("Name is required.");
    return;
  }

  localStorage.setItem("userName", name);
  if (email) localStorage.setItem("userEmail", email);

  const themeToggle = document.getElementById("themeToggle");
  applyTheme(themeToggle && themeToggle.checked ? "dark" : "light");

  refreshProfileUi();
  statusEl.style.color = "#2e7d32";
  statusEl.textContent = await tOne("Profile updated successfully.");
}

async function clearLocalHistory() {
  localStorage.removeItem("detectionHistory");
  const statusEl = document.getElementById("settingsStatus");
  if (statusEl) {
    statusEl.style.color = "#2e7d32";
    statusEl.textContent = await tOne("Local detection history cleared.");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  updateDebug(`${FRONTEND_BUILD} loaded`);
  initTheme();
  ensureUserIdFromToken();

  const userType = localStorage.getItem("userType");
  if (!userType) {
    window.location.href = "login.html";
    return;
  }

  const detectBtn = document.getElementById("detectBtn");
  if (detectBtn) detectBtn.onclick = detectDisease;

  const closeBtn = document.getElementById("detectCloseBtn");
  if (closeBtn) {
    closeBtn.onclick = async (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (isProcessing) {
        showLocalizedAlert("Please wait for detection to complete");
        return;
      }
      requestManualClose();
    };
  }

  const cameraBtn = document.getElementById("openCameraBtn");
  if (cameraBtn) cameraBtn.onclick = openCamera;

  const uploadBtn = document.getElementById("uploadBtn");
  if (uploadBtn) uploadBtn.onclick = triggerUpload;

  const scrollBtn = document.getElementById("scrollBtn");
  if (scrollBtn) {
    scrollBtn.onclick = () => {
      const features = document.getElementById("features");
      if (features) features.scrollIntoView({ behavior: "smooth" });
    };
  }

  const helpBtn = document.getElementById("helpBtn");
  if (helpBtn) {
    helpBtn.onclick = openHelpModal;
  }

  const helpCloseBtn = document.getElementById("helpCloseBtn");
  if (helpCloseBtn) helpCloseBtn.onclick = closeHelpModal;

  const feedbackSubmitBtn = document.getElementById("feedbackSubmitBtn");
  if (feedbackSubmitBtn) feedbackSubmitBtn.onclick = submitFeedback;

  const imageInput = document.getElementById("imageInput");
  if (imageInput) {
    imageInput.onchange = (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (evt) => {
        const preview = document.getElementById("imagePreview");
        const container = document.getElementById("imagePreviewContainer");
        const result = document.getElementById("detectionResult");

        if (preview) preview.src = evt.target.result;
        if (container) container.style.display = "block";
        if (result) result.innerHTML = "";
      };
      reader.readAsDataURL(file);
    };
  }

  const userInput = document.getElementById("userInput");
  if (userInput) {
    userInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") sendMessage();
    });
  }

  document.addEventListener("click", (e) => {
    const container = document.querySelector(".profile-container");
    const dropdown = document.getElementById("profileDropdown");
    if (dropdown && container && !container.contains(e.target)) {
      closeProfileDropdown();
    }
  });

  const authText = document.getElementById("authText");
  if (authText) {
    authText.innerText = userType === "guest" ? "Login / Sign Up" : "Logout";
    if (typeof window.applySiteLanguage === "function") {
      window.applySiteLanguage(localStorage.getItem("selectedLanguage") || "en");
    }
  }

  refreshProfileUi();

  const chatModal = document.getElementById("chatModal");
  if (chatModal) {
    chatModal.addEventListener("click", (e) => {
      if (e.target === chatModal && keepDetectModalOpen) {
        e.preventDefault();
        e.stopPropagation();
      }
    });
  }

  const helpModal = document.getElementById("helpModal");
  if (helpModal) {
    helpModal.addEventListener("click", (e) => {
      if (e.target === helpModal) closeHelpModal();
    });
  }

  const historyCloseBtn = document.getElementById("historyCloseBtn");
  if (historyCloseBtn) historyCloseBtn.onclick = closeHistoryModal;

  const settingsCloseBtn = document.getElementById("settingsCloseBtn");
  if (settingsCloseBtn) settingsCloseBtn.onclick = closeSettingsModal;

  const saveSettingsBtn = document.getElementById("settingsSaveBtn");
  if (saveSettingsBtn) saveSettingsBtn.onclick = saveProfileSettings;

  const openHistoryManagerBtn = document.getElementById("openHistoryManagerBtn");
  if (openHistoryManagerBtn) {
    openHistoryManagerBtn.onclick = () => {
      closeSettingsModal();
      openHistory(true);
    };
  }

  const deleteSelectedHistoryBtn = document.getElementById("deleteSelectedHistoryBtn");
  if (deleteSelectedHistoryBtn) deleteSelectedHistoryBtn.onclick = deleteSelectedHistory;

  const clearAllHistoryBtn = document.getElementById("clearAllHistoryBtn");
  if (clearAllHistoryBtn) clearAllHistoryBtn.onclick = clearAllActivityHistory;

  const historyModal = document.getElementById("historyModal");
  if (historyModal) {
    historyModal.addEventListener("click", (e) => {
      if (e.target === historyModal) closeHistoryModal();
    });
  }

  const settingsModal = document.getElementById("settingsModal");
  if (settingsModal) {
    settingsModal.addEventListener("click", (e) => {
      if (e.target === settingsModal) closeSettingsModal();
    });
  }

  startModalGuard();
  updateDebug("Ready");
});
