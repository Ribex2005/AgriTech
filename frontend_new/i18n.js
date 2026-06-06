const I18N_BASE_URL = "http://127.0.0.1:8000";
const I18N_DEFAULT_LANG = "en";
const I18N_CACHE_KEY = "i18nCacheV2";
const I18N_REQUEST_TIMEOUT_MS = 25000;
const I18N_CHUNK_SIZE = 25;
const I18N_RETRY_UNCHANGED_ROUNDS = 2;

const I18N_LANG_ALIASES = {
  od: "or",
  oriya: "or",
  oriya_in: "or",
  punjabi: "pa",
  assamese: "as",
  kashmiri: "ks",
  manipuri: "mni",
  bodo: "brx",
  sindhi: "sd",
  dogri: "doi",
  maithili: "mai",
  santali: "sat"
};

let i18nApplyToken = 0;
let i18nObserver = null;
let i18nObserverMuted = false;
const i18nInFlight = new Map();

function chunkArray(values, size) {
  const safeSize = Math.max(1, Number(size) || 1);
  const chunks = [];
  for (let i = 0; i < values.length; i += safeSize) {
    chunks.push(values.slice(i, i + safeSize));
  }
  return chunks;
}

function loadI18nCache() {
  try {
    const raw = localStorage.getItem(I18N_CACHE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveI18nCache(cache) {
  try {
    localStorage.setItem(I18N_CACHE_KEY, JSON.stringify(cache));
  } catch {
    // Ignore storage failures.
  }
}

function cacheKey(lang, text) {
  return `${lang}::${text}`;
}

function normalizeLangCode(lang) {
  const code = String(lang || I18N_DEFAULT_LANG).trim().toLowerCase();
  return I18N_LANG_ALIASES[code] || code || I18N_DEFAULT_LANG;
}

async function translateTextBatch(texts, targetLang) {
  targetLang = normalizeLangCode(targetLang);
  if (!Array.isArray(texts) || texts.length === 0) return [];
  if (!targetLang || targetLang === "en") return texts;

  const cache = loadI18nCache();
  const result = new Array(texts.length);
  const missByText = new Map();
  const missTexts = [];

  texts.forEach((txt, idx) => {
    const source = String(txt || "");
    const key = cacheKey(targetLang, source);
    if (cache[key]) {
      result[idx] = cache[key];
    } else {
      if (!missByText.has(source)) {
        missByText.set(source, []);
        missTexts.push(source);
      }
      missByText.get(source).push(idx);
    }
  });

  if (missTexts.length === 0) {
    return result;
  }

  const fetchChunk = async (chunkTexts) => {
    const requestKey = `${targetLang}::${chunkTexts.join("\u0001")}`;
    let pending = i18nInFlight.get(requestKey);

    if (!pending) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), I18N_REQUEST_TIMEOUT_MS);

      pending = fetch(`${I18N_BASE_URL}/api/translate-ui/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_lang: targetLang, texts: chunkTexts }),
        signal: controller.signal
      }).finally(() => {
        clearTimeout(timeoutId);
        i18nInFlight.delete(requestKey);
      });

      i18nInFlight.set(requestKey, pending);
    }

    try {
      const res = await pending;
      if (!res.ok) return chunkTexts;
      const data = await res.json();
      if (!Array.isArray(data.translations)) return chunkTexts;
      return chunkTexts.map((source, i) => data.translations[i] || source);
    } catch {
      return chunkTexts;
    }
  };

  const chunks = chunkArray(missTexts, I18N_CHUNK_SIZE);
  const translatedBySource = new Map();

  for (const chunk of chunks) {
    const firstPass = await fetchChunk(chunk);
    firstPass.forEach((translated, idx) => {
      translatedBySource.set(chunk[idx], translated || chunk[idx]);
    });
  }

  for (let round = 0; round < I18N_RETRY_UNCHANGED_ROUNDS; round += 1) {
    const unchanged = [];
    missTexts.forEach((source) => {
      const translated = translatedBySource.get(source);
      if (!translated || translated === source) unchanged.push(source);
    });

    if (unchanged.length === 0) break;

    for (const chunk of chunkArray(unchanged, Math.max(1, Math.floor(I18N_CHUNK_SIZE / 2)))) {
      const retried = await fetchChunk(chunk);
      retried.forEach((translated, idx) => {
        const source = chunk[idx];
        if (translated && translated !== source) {
          translatedBySource.set(source, translated);
        }
      });
    }
  }

  missTexts.forEach((source) => {
    const translated = translatedBySource.get(source) || source;
    (missByText.get(source) || []).forEach((idx) => {
      result[idx] = translated;
    });

    if (translated !== source) cache[cacheKey(targetLang, source)] = translated;
  });

  saveI18nCache(cache);
  return result;
}

function collectTranslatableItems() {
  const items = [];

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    if (!el.dataset.i18nEn) {
      el.dataset.i18nEn = el.textContent.trim();
    }

    items.push({
      type: "text",
      el,
      source: el.dataset.i18nEn
    });
  });

  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    if (!el.dataset.i18nPlaceholderEn) {
      el.dataset.i18nPlaceholderEn = el.getAttribute("placeholder") || "";
    }

    items.push({
      type: "placeholder",
      el,
      source: el.dataset.i18nPlaceholderEn
    });
  });

  document.querySelectorAll("[data-i18n-title]").forEach((el) => {
    if (!el.dataset.i18nTitleEn) {
      el.dataset.i18nTitleEn = el.getAttribute("title") || "";
    }

    items.push({
      type: "title",
      el,
      source: el.dataset.i18nTitleEn
    });
  });

  return items;
}

async function applyLanguageToRoot(root, lang) {
  if (!root) return;

  const items = [];
  const collectElement = (el) => {
    if (el.matches("[data-i18n]")) {
      if (!el.dataset.i18nEn) {
        el.dataset.i18nEn = el.textContent.trim();
      }
      items.push({ type: "text", el, source: el.dataset.i18nEn });
    }

    if (el.matches("[data-i18n-placeholder]")) {
      if (!el.dataset.i18nPlaceholderEn) {
        el.dataset.i18nPlaceholderEn = el.getAttribute("placeholder") || "";
      }
      items.push({ type: "placeholder", el, source: el.dataset.i18nPlaceholderEn });
    }

    if (el.matches("[data-i18n-title]")) {
      if (!el.dataset.i18nTitleEn) {
        el.dataset.i18nTitleEn = el.getAttribute("title") || "";
      }
      items.push({ type: "title", el, source: el.dataset.i18nTitleEn });
    }
  };

  const pushFrom = (scope) => {
    collectElement(scope);

    scope.querySelectorAll("[data-i18n]").forEach((el) => {
      if (!el.dataset.i18nEn) {
        el.dataset.i18nEn = el.textContent.trim();
      }
      items.push({ type: "text", el, source: el.dataset.i18nEn });
    });

    scope.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      if (!el.dataset.i18nPlaceholderEn) {
        el.dataset.i18nPlaceholderEn = el.getAttribute("placeholder") || "";
      }
      items.push({ type: "placeholder", el, source: el.dataset.i18nPlaceholderEn });
    });

    scope.querySelectorAll("[data-i18n-title]").forEach((el) => {
      if (!el.dataset.i18nTitleEn) {
        el.dataset.i18nTitleEn = el.getAttribute("title") || "";
      }
      items.push({ type: "title", el, source: el.dataset.i18nTitleEn });
    });
  };

  pushFrom(root);
  if (items.length === 0) return;

  const sources = items.map((i) => i.source);
  const translated = await translateTextBatch(sources, lang);

  i18nObserverMuted = true;
  items.forEach((item, idx) => {
    const value = lang === "en" ? item.source : (translated[idx] || item.source);
    if (item.type === "text") item.el.textContent = value;
    if (item.type === "placeholder") item.el.setAttribute("placeholder", value);
    if (item.type === "title") item.el.setAttribute("title", value);
  });
  i18nObserverMuted = false;
}

function setupDynamicTranslationObserver() {
  if (i18nObserver) return;

  i18nObserver = new MutationObserver((mutations) => {
    if (i18nObserverMuted) return;
    const lang = normalizeLangCode(localStorage.getItem("selectedLanguage") || I18N_DEFAULT_LANG);
    if (lang === "en") return;

    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (!(node instanceof Element)) return;
        applyLanguageToRoot(node, lang);
      });
    });
  });

  i18nObserver.observe(document.body, { childList: true, subtree: true });
}

async function applySiteLanguage(lang) {
  const token = ++i18nApplyToken;
  const selectedLang = normalizeLangCode(lang || localStorage.getItem("selectedLanguage") || I18N_DEFAULT_LANG);
  localStorage.setItem("selectedLanguage", selectedLang);
  document.documentElement.lang = selectedLang;

  const select = document.getElementById("languageSelect");
  if (select) {
    select.value = selectedLang;
  }

  const items = collectTranslatableItems();
  const sources = items.map((i) => i.source);
  const translated = await translateTextBatch(sources, selectedLang);

  // Ignore stale async responses from old language selections.
  if (token !== i18nApplyToken) return;

  items.forEach((item, idx) => {
    const value = selectedLang === "en" ? item.source : (translated[idx] || item.source);

    if (item.type === "text") {
      item.el.textContent = value;
    } else if (item.type === "placeholder") {
      item.el.setAttribute("placeholder", value);
    } else if (item.type === "title") {
      item.el.setAttribute("title", value);
    }
  });

  document.dispatchEvent(new CustomEvent("site-language-applied", { detail: { lang: selectedLang } }));
}

function saveLanguage() {
  const select = document.getElementById("languageSelect");
  const selectedLang = normalizeLangCode(select ? select.value : I18N_DEFAULT_LANG);
  applySiteLanguage(selectedLang);
}

window.translateTextBatch = translateTextBatch;
window.applySiteLanguage = applySiteLanguage;
window.saveLanguage = saveLanguage;

document.addEventListener("DOMContentLoaded", () => {
  const selected = normalizeLangCode(localStorage.getItem("selectedLanguage") || I18N_DEFAULT_LANG);
  localStorage.setItem("selectedLanguage", selected);
  applySiteLanguage(selected);
  setupDynamicTranslationObserver();
});
