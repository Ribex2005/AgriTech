import logging
import time

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.chatbot import translator_service


logger = logging.getLogger(__name__)


UI_TRANSLATION_CACHE = {}
UI_TRANSLATION_CACHE_MAX = 10000
UI_TRANSLATION_CACHE_NS = "v2"
UI_TRANSLATION_MAX_MS = 20000

TARGET_LANG_ALIASES = {
    "od": "or",
    "oriya": "or",
    "punjabi": "pa",
    "assamese": "as",
    "kashmiri": "ks",
    "manipuri": "mni",
    "bodo": "brx",
    "sindhi": "sd",
    "dogri": "doi",
    "maithili": "mai",
    "santali": "sat",
}


def normalize_target_lang(lang: str) -> str:
    code = (lang or "en").strip().lower()
    return TARGET_LANG_ALIASES.get(code, code)


@api_view(["POST"])
@permission_classes([AllowAny])
def translate_ui(request):
    started = time.perf_counter()
    target_lang = normalize_target_lang(request.data.get("target_lang") or "en")
    texts = request.data.get("texts", [])

    if not isinstance(texts, list):
        return Response({"error": "texts must be a list"}, status=400)

    if len(texts) > 400:
        return Response({"error": "Too many text items"}, status=400)

    if target_lang == "en":
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info("translate_ui lang=en items=%d ms=%d", len(texts), elapsed_ms)
        return Response({"target_lang": "en", "translations": [str(t or "") for t in texts]})

    translations = []
    request_cache = {}
    stats = {
        "items": 0,
        "blank_or_symbol": 0,
        "request_cache_hits": 0,
        "global_cache_hits": 0,
        "translated": 0,
        "fallback_same_text": 0,
        "timed_out_items": 0,
    }

    for idx, item in enumerate(texts):
        elapsed_now_ms = int((time.perf_counter() - started) * 1000)
        if elapsed_now_ms >= UI_TRANSLATION_MAX_MS:
            remaining = texts[idx:]
            stats["timed_out_items"] += len(remaining)
            translations.extend([str(x or "") for x in remaining])
            break

        stats["items"] += 1
        source = str(item or "")
        cleaned = " ".join(source.split())

        if not cleaned:
            stats["blank_or_symbol"] += 1
            translations.append(source)
            continue

        if not any(ch.isalnum() for ch in cleaned):
            stats["blank_or_symbol"] += 1
            translations.append(source)
            continue

        if source in request_cache:
            stats["request_cache_hits"] += 1
            translations.append(request_cache[source])
            continue

        global_key = f"{UI_TRANSLATION_CACHE_NS}::{target_lang}::{cleaned}"
        if global_key in UI_TRANSLATION_CACHE:
            stats["global_cache_hits"] += 1
            translated = UI_TRANSLATION_CACHE[global_key]
            request_cache[source] = translated
            translations.append(translated)
            continue

        try:
            translated = translator_service.translate_from_english(source, target_lang)
            if not translated:
                translated = source
        except Exception:
            translated = source

        request_cache[source] = translated
        # Do not persist fallback English values as cache hits for non-English targets.
        if translated != source:
            stats["translated"] += 1
            if len(UI_TRANSLATION_CACHE) >= UI_TRANSLATION_CACHE_MAX:
                UI_TRANSLATION_CACHE.clear()
            UI_TRANSLATION_CACHE[global_key] = translated
        else:
            stats["fallback_same_text"] += 1
        translations.append(translated)

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    logger.info(
        "translate_ui lang=%s items=%d ms=%d req_cache=%d global_cache=%d translated=%d fallback=%d skipped=%d timed_out=%d",
        target_lang,
        stats["items"],
        elapsed_ms,
        stats["request_cache_hits"],
        stats["global_cache_hits"],
        stats["translated"],
        stats["fallback_same_text"],
        stats["blank_or_symbol"],
        stats["timed_out_items"],
    )

    return Response({"target_lang": target_lang, "translations": translations})
