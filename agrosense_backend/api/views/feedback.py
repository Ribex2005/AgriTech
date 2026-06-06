from datetime import datetime

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.mongo_client import get_db


@api_view(["POST"])
@permission_classes([AllowAny])
def submit_feedback(request):
    db = get_db()
    if db is None:
        return Response({"message": "Feedback service unavailable"}, status=503)

    name = str(request.data.get("name") or "").strip()
    email = str(request.data.get("email") or "").strip()
    message = str(request.data.get("message") or "").strip()
    page = str(request.data.get("page") or "").strip()

    if not name or not message:
        return Response({"message": "Name and message are required"}, status=400)

    if len(message) > 3000:
        return Response({"message": "Feedback message is too long"}, status=400)

    db.feedback.insert_one(
        {
            "name": name,
            "email": email,
            "message": message,
            "page": page,
            "created_at": datetime.utcnow(),
        }
    )

    return Response({"message": "Feedback submitted successfully"}, status=200)
