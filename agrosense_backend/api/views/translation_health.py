from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.chatbot import translator_service


BEST_EFFORT_LANGS = {"ks", "mni", "brx", "sd", "sa", "doi", "mai", "sat", "gom"}


@api_view(["GET"])
@permission_classes([AllowAny])
def translation_health(request):
    language_support = {}

    for code in translator_service.INDIC_LANGUAGES.keys():
        tier = "best-effort" if code in BEST_EFFORT_LANGS else "high-accuracy"
        language_support[code] = {
            "tier": tier,
            "display_name": translator_service.INDIC_LANGUAGES.get(code, code),
        }

    return Response(
        {
            "ok": True,
            "providers": {
                "local_model_enabled": bool(getattr(translator_service, "ENABLE_INDICTRANS2", False)),
                "local_model_loaded": bool(getattr(translator_service, "models_ready", False)),
                "deep_translator_available": bool(getattr(translator_service, "HAS_DEEP_TRANSLATOR", False)),
                "prefer_local_translation": bool(getattr(translator_service, "PREFER_LOCAL_TRANSLATION", False)),
            },
            "language_support": language_support,
        }
    )
