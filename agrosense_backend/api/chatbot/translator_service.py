import logging
import os
import re
import time
from typing import Dict

try:
    from langdetect import detect
    HAS_LANGDETECT = True
except Exception:
    HAS_LANGDETECT = False

    def detect(_text):
        return "en"

try:
    from deep_translator import GoogleTranslator
    HAS_DEEP_TRANSLATOR = True
except Exception:
    HAS_DEEP_TRANSLATOR = False

# Create logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
translator_ready = False
models_ready = False
model_load_attempted = False

# Keep HF models optional to avoid runtime failures on restricted/private repos.
ENABLE_INDICTRANS2 = os.getenv("ENABLE_INDICTRANS2", "1").strip() == "1"
PREFER_LOCAL_TRANSLATION = os.getenv("PREFER_LOCAL_TRANSLATION", "1").strip() == "1"
WARM_TRANSLATOR_ON_START = os.getenv("WARM_TRANSLATOR_ON_START", "0").strip() == "1"

tokenizer_indic_en = None
model_indic_en = None
tokenizer_en_indic = None
model_en_indic = None

# Translation cache and transient failure controls for external translators.
_TRANSLATION_CACHE: Dict[str, str] = {}
_TRANSLATION_CACHE_MAX = 8000
_GOOGLE_FAIL_UNTIL = 0.0
_GOOGLE_FAIL_STREAK = 0
_LOG_THROTTLE_TS: Dict[str, float] = {}

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    HAS_TRANSFORMERS = True
except Exception as exc:
    HAS_TRANSFORMERS = False
    logger.warning("Transformers is not available. Multilingual translation disabled: %s", exc)


# Supported Indic language codes for IndicTrans2
INDIC_LANGUAGES: Dict[str, str] = {
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",
    "sa": "Sanskrit",
    "ne": "Nepali",
    "gom": "Konkani",
    "sd": "Sindhi",
    "ks": "Kashmiri",
    "mni": "Manipuri",
    "brx": "Bodo",
    "doi": "Dogri",
    "mai": "Maithili",
    "sat": "Santali",
}

# Some low-resource codes are not reliably supported by external providers.
# Map them to a close high-resource language to avoid hard failures.
FALLBACK_TARGET_LANG_MAP: Dict[str, str] = {
    "gom": "mr",
    "mni": "hi",
    "brx": "hi",
    "doi": "hi",
    "mai": "hi",
    "sat": "hi",
    "ks": "ur",
    "sd": "ur",
    "sa": "hi",
}


def _contains_devanagari(text: str) -> bool:
    # Devanagari block helps stabilize Hindi detection when langdetect is uncertain.
    return any("\u0900" <= ch <= "\u097F" for ch in text)


def _is_ascii_english_like(text: str) -> bool:
    return all(ord(ch) < 128 for ch in text)


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())


def _has_translatable_content(text: str) -> bool:
    cleaned = _clean_text(text)
    # Skip pure emoji/symbol/punctuation strings.
    return any(ch.isalnum() for ch in cleaned)


def _cache_key(source_lang: str, target_lang: str, text: str) -> str:
    return f"{source_lang}->{target_lang}::{text}"


def _cache_get(source_lang: str, target_lang: str, text: str):
    return _TRANSLATION_CACHE.get(_cache_key(source_lang, target_lang, text))


def _cache_set(source_lang: str, target_lang: str, text: str, translated: str):
    if len(_TRANSLATION_CACHE) >= _TRANSLATION_CACHE_MAX:
        _TRANSLATION_CACHE.clear()
    _TRANSLATION_CACHE[_cache_key(source_lang, target_lang, text)] = translated


def _throttled_log(level: str, key: str, message: str, *args):
    now = time.time()
    last = _LOG_THROTTLE_TS.get(key, 0.0)
    if now - last < 30:
        return
    _LOG_THROTTLE_TS[key] = now
    log_fn = logger.warning if level == "warning" else logger.error
    log_fn(message, *args)


def _google_translate(source_lang: str, target_lang: str, text: str):
    global _GOOGLE_FAIL_UNTIL
    global _GOOGLE_FAIL_STREAK

    if not HAS_DEEP_TRANSLATOR:
        return None

    now = time.time()
    if now < _GOOGLE_FAIL_UNTIL:
        return None

    try:
        translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        _GOOGLE_FAIL_STREAK = 0
        _GOOGLE_FAIL_UNTIL = 0.0
        return translated
    except Exception as exc:
        _GOOGLE_FAIL_STREAK += 1
        backoff_sec = min(120, 2 ** min(_GOOGLE_FAIL_STREAK, 6))
        _GOOGLE_FAIL_UNTIL = now + backoff_sec
        _throttled_log(
            "warning",
            f"google-{source_lang}-{target_lang}",
            "Google translation %s->%s failed; using fallback/cached text for %ds. Error: %s",
            source_lang,
            target_lang,
            backoff_sec,
            exc,
        )
        return None


def _resolve_target_lang(target_lang: str) -> str:
    lang = (target_lang or "").strip().lower()
    return FALLBACK_TARGET_LANG_MAP.get(lang, lang)


def _translate_with_fallback_order(source_lang: str, target_lang: str, text: str):
    source_lang = (source_lang or "").strip().lower()
    target_lang = _resolve_target_lang(target_lang)

    cleaned = _clean_text(text)
    if not cleaned:
        return text

    cached = _cache_get(source_lang, target_lang, cleaned)
    if cached:
        return cached

    # Prefer local model quality/stability for Indic pairs when enabled.
    if PREFER_LOCAL_TRANSLATION and ENABLE_INDICTRANS2 and _load_models():
        translated = _model_translate(source_lang, target_lang, text)
        if translated:
            _cache_set(source_lang, target_lang, cleaned, translated)
            return translated

    translated = _google_translate(source_lang, target_lang, cleaned)
    if translated:
        _cache_set(source_lang, target_lang, cleaned, translated)
        return translated

    if (not PREFER_LOCAL_TRANSLATION) and ENABLE_INDICTRANS2 and _load_models():
        translated = _model_translate(source_lang, target_lang, text)
        if translated:
            _cache_set(source_lang, target_lang, cleaned, translated)
            return translated

    return text


def _model_translate(source_lang: str, target_lang: str, text: str):
    try:
        if source_lang == "en":
            inputs = tokenizer_en_indic(f"<2{target_lang}> {text}", return_tensors="pt", padding=True, truncation=True)
            with torch.no_grad():
                outputs = model_en_indic.generate(**inputs, max_length=256)
            return tokenizer_en_indic.decode(outputs[0], skip_special_tokens=True)

        if target_lang == "en":
            inputs = tokenizer_indic_en(f"<2en> {text}", return_tensors="pt", padding=True, truncation=True)
            with torch.no_grad():
                outputs = model_indic_en.generate(**inputs, max_length=256)
            return tokenizer_indic_en.decode(outputs[0], skip_special_tokens=True)
    except Exception as exc:
        _throttled_log(
            "warning",
            f"model-{source_lang}-{target_lang}",
            "Model translation failed %s->%s: %s",
            source_lang,
            target_lang,
            exc,
        )

    return None


def _detect_by_script(text: str) -> str:
    for ch in text:
        code = ord(ch)
        if 0x0980 <= code <= 0x09FF:
            return "bn"  # Bengali/Assamese script
        if 0x0A00 <= code <= 0x0A7F:
            return "pa"  # Gurmukhi
        if 0x0A80 <= code <= 0x0AFF:
            return "gu"
        if 0x0B00 <= code <= 0x0B7F:
            return "or"
        if 0x0B80 <= code <= 0x0BFF:
            return "ta"
        if 0x0C00 <= code <= 0x0C7F:
            return "te"
        if 0x0C80 <= code <= 0x0CFF:
            return "kn"
        if 0x0D00 <= code <= 0x0D7F:
            return "ml"
        if 0x0600 <= code <= 0x06FF:
            return "ur"  # Urdu/Sindhi/Kashmiri in Perso-Arabic script
    return "en"


def _load_models() -> bool:
    global models_ready
    global model_load_attempted
    global tokenizer_indic_en, model_indic_en, tokenizer_en_indic, model_en_indic

    if models_ready:
        return True

    if model_load_attempted:
        return False

    model_load_attempted = True

    if not HAS_TRANSFORMERS or not ENABLE_INDICTRANS2:
        return False

    try:
        model_name_indic_en = "ai4bharat/indictrans2-indic-en"
        model_name_en_indic = "ai4bharat/indictrans2-en-indic"
        
        # Load HF token if available
        hf_token = os.getenv("HF_TOKEN", None)

        tokenizer_indic_en = AutoTokenizer.from_pretrained(model_name_indic_en, use_fast=False, token=hf_token)
        model_indic_en = AutoModelForSeq2SeqLM.from_pretrained(model_name_indic_en, token=hf_token)

        tokenizer_en_indic = AutoTokenizer.from_pretrained(model_name_en_indic, use_fast=False, token=hf_token)
        model_en_indic = AutoModelForSeq2SeqLM.from_pretrained(model_name_en_indic, token=hf_token)

        if hasattr(model_indic_en, "eval"):
            model_indic_en.eval()
        if hasattr(model_en_indic, "eval"):
            model_en_indic.eval()

        models_ready = True
        logger.info("IndicTrans2 multilingual models loaded successfully.")
        return True
    except Exception as exc:
        models_ready = False
        logger.error("Failed loading IndicTrans2 models: %s", exc)
        return False


def initialize_translator():
    """Initialize translator with lazy IndicTrans2 model loading support."""
    global translator_ready

    if translator_ready:
        return

    translator_ready = True
    if HAS_TRANSFORMERS and ENABLE_INDICTRANS2:
        logger.info("Translator initialized. IndicTrans2 will load lazily on first translation call.")
    else:
        logger.info("Translator initialized with GoogleTranslator mode (IndicTrans2 disabled).")
    if HAS_DEEP_TRANSLATOR:
        logger.info("GoogleTranslator fallback is available.")

    if WARM_TRANSLATOR_ON_START and HAS_TRANSFORMERS and ENABLE_INDICTRANS2:
        _load_models()

# ------------------ 🌐 LANGUAGE TRANSLATION ------------------

def detect_language(text):
    """Detect language with stable English handling and Devanagari hinting."""
    if not text or not str(text).strip():
        return "en"

    normalized = str(text).strip()

    if _contains_devanagari(normalized):
        return "hi"

    script_lang = _detect_by_script(normalized)
    if script_lang != "en":
        return script_lang

    if _is_ascii_english_like(normalized):
        return "en"

    if HAS_LANGDETECT:
        try:
            lang = detect(normalized)
            # Common langdetect aliases to our target set
            alias_map = {"iw": "hi", "in": "id"}
            return alias_map.get(lang, lang)
        except Exception:
            return "en"

    return "en"


def _indic_to_english(text: str) -> str:
    # Auto source uses Google/detected source; local model supports Indic->English directly.
    if ENABLE_INDICTRANS2 and _load_models():
        translated = _translate_with_fallback_order("hi", "en", text)
        if translated and translated != text:
            return translated

    return _translate_with_fallback_order("auto", "en", text)


def _english_to_indic(text: str, tgt_lang: str) -> str:
    cleaned = _clean_text(text)
    if not _has_translatable_content(cleaned):
        return text

    return _translate_with_fallback_order("en", _resolve_target_lang(tgt_lang), text)

def translate_to_english(text):
    """Translate Indic input to English for chatbot logic; keep English untouched."""
    if not text:
        return text

    src_lang = detect_language(text)
    if src_lang == "en":
        return text

    if src_lang not in INDIC_LANGUAGES:
        logger.info("Language '%s' not in Indic set. Using generic auto->en translation.", src_lang)
        return _translate_with_fallback_order("auto", "en", text)

    return _indic_to_english(text)

def translate_from_english(text, target_lang):
    """Translate English chatbot response back to user's Indic language when supported."""
    if not text:
        return text

    if not target_lang or target_lang == "en":
        return text

    effective_target = _resolve_target_lang(target_lang)

    if target_lang not in INDIC_LANGUAGES:
        return _translate_with_fallback_order("en", effective_target, text)

    return _english_to_indic(text, effective_target)


initialize_translator()