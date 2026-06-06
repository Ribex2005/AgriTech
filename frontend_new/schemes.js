const BASE_URL = "http://127.0.0.1:8000";

function getUserId() {
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

function getAuthHeaders() {
    const token = localStorage.getItem("token");
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
}

function getCurrentLanguage() {
    return (localStorage.getItem("selectedLanguage") || "en").toLowerCase();
}

function applyThemeFromHome() {
    const mode = (localStorage.getItem("themeMode") || "light").toLowerCase();
    if (mode === "dark") {
        document.body.classList.add("dark-mode");
    } else {
        document.body.classList.remove("dark-mode");
    }
}

async function t(text) {
    const lang = getCurrentLanguage();
    if (lang === "en" || typeof window.translateTextBatch !== "function") return text;

    const translated = await window.translateTextBatch([text], lang);
    return translated[0] || text;
}

async function tBatch(texts) {
    const lang = getCurrentLanguage();
    if (lang === "en" || typeof window.translateTextBatch !== "function") return texts;
    const translated = await window.translateTextBatch(texts, lang);
    return Array.isArray(translated) ? translated : texts;
}

document.addEventListener("DOMContentLoaded", () => {
    applyThemeFromHome();
    loadFlagshipSchemes();
    loadAllSchemes();
});

document.addEventListener("site-language-applied", () => {
    loadFlagshipSchemes();
    loadAllSchemes();
});

/* ================= FLAGSHIP ================= */

async function loadFlagshipSchemes() {

    const container = document.getElementById("flagshipContainer");
    container.innerHTML = await t("Loading popular schemes...");

    try {

        const userId = getUserId();
        const response = await fetch(`${BASE_URL}/api/schemes/?flagship=true${userId ? `&user_id=${encodeURIComponent(userId)}` : ""}`, { headers: getAuthHeaders() });
        const data = await response.json();

        renderSchemes(data.schemes, "flagshipContainer");

    } catch (error) {

        container.innerHTML = await t("Failed to load popular schemes");

    }

}

/* ================= ALL SCHEMES ================= */

async function loadAllSchemes() {

    const container = document.getElementById("schemesContainer");
    container.innerHTML = await t("Loading schemes...");

    try {

        const userId = getUserId();
        const response = await fetch(`${BASE_URL}/api/schemes/?${userId ? `user_id=${encodeURIComponent(userId)}` : ""}`, { headers: getAuthHeaders() });
        const data = await response.json();

        renderSchemes(data.schemes, "schemesContainer");

    } catch (error) {

        container.innerHTML = await t("Failed to load schemes");

    }

}

/* ================= FILTERS ================= */

async function applyFilters() {

    const search = document.getElementById("searchInput").value;
    const state = document.getElementById("stateFilter").value;
    const category = document.getElementById("categoryFilter").value;

    let url = `${BASE_URL}/api/schemes/?`;

    if (search) url += `search=${search}&`;
    if (state) url += `state=${state}&`;
    if (category) url += `category=${category}&`;
    const userId = getUserId();
    if (userId) url += `user_id=${encodeURIComponent(userId)}&`;

    const container = document.getElementById("schemesContainer");
    container.innerHTML = await t("Searching schemes...");

    try {

        const response = await fetch(url, { headers: getAuthHeaders() });
        const data = await response.json();

        renderSchemes(data.schemes, "schemesContainer");

    } catch (error) {

        container.innerHTML = await t("Server error");

    }

}

/* ================= RENDER ================= */

async function renderSchemes(schemes, containerId) {

    const container = document.getElementById(containerId);
    container.innerHTML = "";

    if (!schemes || schemes.length === 0) {

        const noSchemesText = await t("No schemes found for selected filters");

        container.innerHTML = `
            <p style="opacity:0.7">
                ${noSchemesText}
            </p>
        `;

        return;
    }

    const viewDetailsText = await t("View Details");

    const valueInputs = [];
    schemes.forEach((scheme) => {
        valueInputs.push(scheme.title || "");
        valueInputs.push(scheme.category || "");
        valueInputs.push((scheme.description || "").substring(0, 120));
    });
    const valueOutputs = await tBatch(valueInputs);

    schemes.forEach((scheme, idx) => {

        const base = idx * 3;
        const translatedTitle = valueOutputs[base] || scheme.title;
        const translatedCategory = valueOutputs[base + 1] || scheme.category;
        const translatedSnippet = valueOutputs[base + 2] || (scheme.description || "").substring(0, 120);

        const badgeClass = "badge-" + String(scheme.category || "General").replace(" ", "");

        const card = document.createElement("div");
        card.className = "scheme-card";

        card.innerHTML = `
            <h3>${translatedTitle}</h3>

            <div class="category-badge ${badgeClass}">
                ${translatedCategory}
            </div>

            <p style="margin-top:10px">
                ${translatedSnippet}...
            </p>

            <button onclick='openDetails(${JSON.stringify(scheme)})'>
                ${viewDetailsText}
            </button>
        `;

        container.appendChild(card);

    });

}

/* ================= DETAILS ================= */

async function openDetails(scheme) {

    try {
        await fetch(`${BASE_URL}/api/schemes/view/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...getAuthHeaders()
            },
            body: JSON.stringify({
                user_id: getUserId(),
                title: scheme.title || "",
                category: scheme.category || "",
                official_link: scheme.official_link || ""
            })
        });
    } catch {
        // Do not block UI if tracking fails.
    }

    const title = scheme.title || "";
    const description = scheme.description || "";
    const benefits = Array.isArray(scheme.benefits) ? scheme.benefits : [];
    const translatedValues = await tBatch([title, description, ...benefits]);

    document.getElementById("modalTitle").innerText = translatedValues[0] || title;
    document.getElementById("modalDescription").innerText = translatedValues[1] || description;

    const benefitsList = document.getElementById("modalBenefits");
    benefitsList.innerHTML = "";

    benefits.forEach((b, idx) => {

        const li = document.createElement("li");
        li.innerText = translatedValues[2 + idx] || b;
        benefitsList.appendChild(li);

    });

    document.getElementById("modalLink").href = scheme.official_link;

    document.getElementById("detailsModal").style.display = "flex";

}

function closeModal() {

    document.getElementById("detailsModal").style.display = "none";

}