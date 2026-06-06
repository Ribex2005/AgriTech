from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from datetime import datetime
from api.mongo_client import get_db

from .chatbot import get_bot_response


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def chat_message(request):
    """
    Send a message to the chatbot.
    Request: {"message": "..."}
    Response: {"reply": "...", "message_type": "...", "context": {...}}
    """

    user_message = request.data.get("message")
    user_id = getattr(request, "user_id", None)

    if not user_message or not str(user_message).strip():
        return Response({"error": "Message required"}, status=400)

    bot_result = get_bot_response(user_message)
    if isinstance(bot_result, dict):
        reply = bot_result.get("response", "")
        intent = bot_result.get("intent", "general")
        context = bot_result.get("context", {})
    else:
        reply = str(bot_result)
        intent = "general"
        context = {}

    # Save chat history only for authenticated users.
    if user_id:
        try:
            db = get_db()
            db.user_activity.insert_one({
                "user_id": user_id,
                "type": "chat",
                "data": {
                    "input": user_message,
                    "output": reply,
                    "intent": intent,
                    "context": context
                },
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            print("Chat history error:", e)

    return Response({
        "reply": reply,
        "message_type": intent,
        "intent": intent,
        "context": context,
        "is_authenticated": bool(user_id)
    })


# 🔥 GET CHAT HISTORY
@api_view(['GET'])
def chat_history(request):
    """
    Get authenticated user's chat history (JWT middleware based).
    Query param: ?limit=20
    """

    user_id = getattr(request, "user_id", None)

    if not user_id:
        return Response({"error": "Login required"}, status=401)

    try:
        limit = int(request.query_params.get("limit", 20))
    except ValueError:
        limit = 20

    db = get_db()

    history = list(db.user_activity.find({
        "user_id": user_id,
        "type": "chat"
    }).sort("timestamp", -1).limit(limit))

    formatted = []
    for item in history:
        data = item.get("data", {})
        formatted.append({
            "id": str(item.get("_id")),
            "message": data.get("input", ""),
            "reply": data.get("output", ""),
            "message_type": data.get("intent", "general"),
            "context": data.get("context", {}),
            "timestamp": item.get("timestamp")
        })

    return Response(formatted)


# 🔥 CLEAR CHAT HISTORY
@api_view(['DELETE'])
def clear_chat_history(request):

    user_id = getattr(request, "user_id", None)

    if not user_id:
        return Response({"error": "Login required"}, status=401)

    db = get_db()

    db.user_activity.delete_many({
        "user_id": user_id,
        "type": "chat"
    })

    return Response({"message": "Chat history cleared"})


@api_view(['GET'])
@permission_classes([AllowAny])
def test_chatbot(_request):
    return Response({
        "status": "Chatbot is running",
        "endpoints": {
            "message": "/api/chat/message/ (POST, guest allowed)",
            "history": "/api/chat/history/ (GET, JWT required)",
            "clear": "/api/chat/clear/ (DELETE, JWT required)"
        }
    })