// ==================== CONFIGURATION ====================
const BASE_URL = "http://127.0.0.1:8000";
let currentFile = null;
let isDetecting = false;

// ==================== DOM ELEMENTS ====================
let uploadArea, imageInput, preview, detectBtn, resultDiv, debugDiv, backendUrlSpan, statusBadge;

// ==================== DEBUG FUNCTION ====================
function log(message, type = 'info') {
    const time = new Date().toLocaleTimeString();
    const debugDiv = document.getElementById('debug');
    if (debugDiv) {
        const color = type === 'error' ? '#ff6b6b' : (type === 'success' ? '#6bff6b' : '#0f0');
        debugDiv.innerHTML = `<span style="color: ${color}">[${time}]</span> ${message}<br>` + debugDiv.innerHTML;
        // Keep only last 30 messages
        const lines = debugDiv.innerHTML.split('<br>');
        if (lines.length > 30) {
            debugDiv.innerHTML = lines.slice(0, 30).join('<br>');
        }
    }
    console.log(`[${time}] ${message}`);
}

// ==================== CHECK BACKEND STATUS ====================
async function checkBackendStatus() {
    try {
        log("Checking backend status...");
        const response = await fetch(`${BASE_URL}/api/health/`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            log(`✅ Backend is running: ${JSON.stringify(data)}`, 'success');
            if (statusBadge) {
                statusBadge.textContent = 'Connected';
                statusBadge.className = 'status-badge status-success';
            }
            return true;
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        log(`❌ Backend not responding: ${error.message}`, 'error');
        if (statusBadge) {
            statusBadge.textContent = 'Disconnected';
            statusBadge.className = 'status-badge status-error';
        }
        return false;
    }
}

// ==================== IMAGE HANDLING ====================
function selectImage(file) {
    if (!file) return;
    
    currentFile = file;
    log(`Image selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`);
    
    const reader = new FileReader();
    reader.onload = function(evt) {
        preview.src = evt.target.result;
        preview.style.display = 'block';
        log("Image preview loaded");
        
        // Clear previous results
        resultDiv.style.display = 'none';
        resultDiv.innerHTML = '';
    };
    reader.readAsDataURL(file);
}

// ==================== DRAG & DROP HANDLING ====================
function setupDragAndDrop() {
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            selectImage(file);
        } else {
            log("Please drop an image file", 'error');
            alert("Please drop an image file");
        }
    });
    
    uploadArea.addEventListener('click', () => {
        imageInput.click();
    });
    
    imageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            selectImage(file);
        }
    });
}

// ==================== DETECTION FUNCTION ====================
async function detectDisease() {
    // Prevent any default behavior
    if (window.event) {
        window.event.preventDefault();
        window.event.stopPropagation();
    }
    
    if (!currentFile) {
        log("No image selected", 'error');
        alert("Please select an image first");
        return;
    }
    
    if (isDetecting) {
        log("Detection already in progress", 'error');
        alert("Please wait, detection already in progress");
        return;
    }
    
    isDetecting = true;
    detectBtn.disabled = true;
    detectBtn.textContent = '⏳ Detecting...';
    
    resultDiv.style.display = 'block';
    resultDiv.className = 'result loading';
    resultDiv.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Analyzing your crop image...</p>
            <small>This may take 5-10 seconds</small>
        </div>
    `;
    
    log("Sending request to backend...");
    log(`URL: ${BASE_URL}/api/detect/`);
    
    const startTime = Date.now();
    
    try {
        const formData = new FormData();
        formData.append('image', currentFile);
        
        const response = await fetch(`${BASE_URL}/api/detect/`, {
            method: 'POST',
            body: formData,
            redirect: 'manual'  // Prevent automatic redirects
        });
        
        const elapsed = Date.now() - startTime;
        log(`Response received in ${elapsed}ms`, 'success');
        log(`Status: ${response.status} ${response.statusText}`);
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 200)}`);
        }
        
        const data = await response.json();
        log("Data parsed successfully", 'success');
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        log(`ERROR: ${error.message}`, 'error');
        resultDiv.className = 'result error';
        resultDiv.innerHTML = `
            <strong>❌ Detection Failed</strong><br><br>
            ${error.message}<br><br>
            <small>Make sure backend is running at ${BASE_URL}</small>
            <hr>
            <small>Tips:<br>
            - Check if Django server is running<br>
            - Verify backend URL is correct<br>
            - Check browser console for details</small>
            <br><br>
            <button onclick="detectDisease()" style="background: #2e7d32; width: auto; padding: 8px 16px;">Try Again</button>
        `;
    } finally {
        isDetecting = false;
        detectBtn.disabled = false;
        detectBtn.textContent = '🔍 Detect Disease';
        log("Detection process completed");
    }
}

// ==================== DISPLAY RESULTS ====================
function displayResults(data) {
    const confidence = Math.round((data.confidence || 0) * 100);
    const cropName = data.crop_name || "Unknown";
    const disease = data.disease || "Unknown";
    const details = data.details || {};
    const cause = details.cause || "";
    const cure = details.cure || "";
    const reference = details.reference || "";
    const warning = data.warning || "";
    const top3 = data.top_3 || [];
    
    // Generate top 3 predictions HTML
    let top3Html = '';
    if (top3.length > 0) {
        top3Html = '<div style="margin-top: 15px;"><strong>📊 Top 3 Predictions:</strong><br><br>';
        top3.slice(0, 3).forEach((pred, idx) => {
            const predName = pred.class_name || pred.class || "Unknown";
            const predConf = Math.round((pred.confidence || 0) * 100);
            top3Html += `
                <div style="margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>${idx + 1}. ${escapeHtml(predName)}</span>
                        <span style="color: #2e7d32;">${predConf}%</span>
                    </div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${predConf}%"></div>
                    </div>
                </div>
            `;
        });
        top3Html += '</div>';
    }
    
    // Warning HTML
    let warningHtml = '';
    if (warning || confidence < 60) {
        warningHtml = `
            <div style="background: #fff3e0; padding: 10px; border-radius: 8px; margin-bottom: 15px;">
                <strong>⚠️ Warning:</strong> ${escapeHtml(warning || `Low confidence (${confidence}%). Please verify manually.`)}
            </div>
        `;
    }
    
    resultDiv.className = 'result success';
    resultDiv.innerHTML = `
        <h3 style="color: #2e7d32; margin-bottom: 15px;">✅ Detection Complete!</h3>
        
        ${warningHtml}
        
        <div class="info-grid">
            <div class="info-card">
                <div style="font-size: 32px;">🌾</div>
                <strong>Crop Name</strong><br>
                <span style="font-size: 18px; color: #2e7d32;">${escapeHtml(cropName)}</span>
            </div>
            <div class="info-card">
                <div style="font-size: 32px;">🦠</div>
                <strong>Disease</strong><br>
                <span style="font-size: 18px; color: #c62828;">${escapeHtml(disease)}</span>
            </div>
        </div>
        
        <div style="margin: 15px 0;">
            <strong>Confidence Score: ${confidence}%</strong>
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: ${confidence}%"></div>
            </div>
        </div>
        
        ${cause ? `<div style="margin: 15px 0; padding: 10px; background: #fff3e0; border-radius: 8px;"><strong>⚠️ Cause:</strong><br>${escapeHtml(cause)}</div>` : ''}
        ${cure ? `<div style="margin: 15px 0; padding: 10px; background: #e8f5e9; border-radius: 8px;"><strong>💊 Treatment / Cure:</strong><br>${escapeHtml(cure)}</div>` : ''}
        ${reference ? `<div style="margin: 15px 0; padding: 10px; background: #e3f2fd; border-radius: 8px;"><strong>📚 References:</strong><br>${escapeHtml(reference)}</div>` : ''}
        ${top3Html}
        
        <hr>
        <div style="display: flex; gap: 10px; margin-top: 15px;">
            <button onclick="saveToHistory()" style="background: #2196f3; width: auto; flex: 1;">💾 Save to History</button>
            <button onclick="resetTest()" style="background: #666; width: auto; flex: 1;">🔄 New Test</button>
        </div>
    `;
    
    // Save to global for history
    window.lastTestResult = data;
    log(`Results displayed - Crop: ${cropName}, Disease: ${disease}, Confidence: ${confidence}%`, 'success');
}

// ==================== HELPER FUNCTIONS ====================
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function saveToHistory() {
    if (!window.lastTestResult) {
        alert("No result to save");
        return;
    }
    
    const history = JSON.parse(localStorage.getItem("testDetectionHistory") || "[]");
    history.unshift({
        ...window.lastTestResult,
        timestamp: new Date().toISOString()
    });
    
    if (history.length > 20) history.length = 20;
    localStorage.setItem("testDetectionHistory", JSON.stringify(history));
    alert("✅ Result saved to local storage!");
    log("Result saved to history");
}

function resetTest() {
    log("Resetting test...");
    currentFile = null;
    isDetecting = false;
    preview.style.display = 'none';
    preview.src = '';
    imageInput.value = '';
    resultDiv.style.display = 'none';
    resultDiv.innerHTML = '';
    detectBtn.disabled = false;
    detectBtn.textContent = '🔍 Detect Disease';
    log("Test reset complete");
}

// ==================== INITIALIZATION ====================
function init() {
    // Get DOM elements
    uploadArea = document.getElementById('uploadArea');
    imageInput = document.getElementById('imageInput');
    preview = document.getElementById('preview');
    detectBtn = document.getElementById('detectBtn');
    resultDiv = document.getElementById('result');
    debugDiv = document.getElementById('debug');
    backendUrlSpan = document.getElementById('backendUrl');
    statusBadge = document.getElementById('statusBadge');
    
    if (!uploadArea || !imageInput || !preview || !detectBtn || !resultDiv) {
        console.error("Required DOM elements not found!");
        return;
    }
    
    // Update backend URL display
    if (backendUrlSpan) {
        backendUrlSpan.textContent = BASE_URL;
    }
    
    // Setup event listeners
    setupDragAndDrop();
    
    detectBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        detectDisease();
    });
    
    // Prevent any form submissions
    document.addEventListener('submit', (e) => {
        e.preventDefault();
        return false;
    });
    
    // Check backend status
    checkBackendStatus();
    
    // Periodic backend check (every 30 seconds)
    setInterval(checkBackendStatus, 30000);
    
    log("Test page initialized", 'success');
    log(`Backend URL: ${BASE_URL}`);
    log("Ready for testing - select an image and click Detect");
}

// Start the app when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}