from django.urls import path
from .views.health import health
from .auth.send_otp import send_otp
from .auth.verify_otp import verify_otp
from .detect.detect_view import DetectDisease
from .detect.history_view import disease_history
from .chatbot.chat_view import chat_message, chat_history, clear_chat_history, test_chatbot
from api.market.market_price_view import get_market_price
from api.market.history_view import market_price_history
from api.schemes.scheme_view import get_govt_schemes, track_scheme_view
from .views.translate_ui import translate_ui
from .views.translation_health import translation_health
from .views.feedback import submit_feedback
from .views.activity_history import activity_history, delete_activity_history

urlpatterns = [

    path('health/', health),

    path('auth/send-otp/', send_otp),
    path('auth/verify-otp/', verify_otp),

    path('detect/', DetectDisease.as_view()),
    path('disease-history/', disease_history),

    path('market-price/', get_market_price),
    path('market-price-history/', market_price_history),

    path('schemes/', get_govt_schemes),
    path('schemes/view/', track_scheme_view),

    path('chat/message/', chat_message),
    path('chat/history/', chat_history),
    path('chat/clear/', clear_chat_history),
    path('chat/test/', test_chatbot),

    path('translate-ui/', translate_ui),
    path('translation-health/', translation_health),
    path('feedback/', submit_feedback),
    path('activity-history/', activity_history),
    path('activity-history/delete/', delete_activity_history),
]