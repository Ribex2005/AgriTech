from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.mongo_client import get_db
from datetime import datetime
import re


@api_view(["GET"])
def get_govt_schemes(request):

    crop_name = request.GET.get("crop_name")
    state = request.GET.get("state")
    category = request.GET.get("category")
    search = request.GET.get("search")
    flagship = request.GET.get("flagship")
    user_id = getattr(request, "user_id", None) or request.GET.get("user_id")

    db = get_db()

    query = {}

    # 🔹 Filter by flagship schemes
    if flagship == "true":
        query["is_flagship"] = True

    # 🔹 Filter by crop
    if crop_name:
        query["eligible_crops"] = {
            "$in": [crop_name.lower(), "all"]
        }

    # 🔹 Filter by state
    if state:
        query["eligible_states"] = {
            "$in": [state, "All"]
        }

    # 🔹 Filter by category
    if category:
        query["category"] = category

    # 🔹 Search by scheme title (case-insensitive)
    if search:
        query["title"] = {
            "$regex": re.compile(search, re.IGNORECASE)
        }

    # 🔹 Fetch from MongoDB
    schemes = list(
        db.govt_schemes.find(query, {"_id": 0})
    )

    # 🔐 Log only meaningful user searches (skip auto/background fetches)
    has_meaningful_filters = any([
        bool(crop_name),
        bool(state),
        bool(category),
        bool(search),
    ])

    if user_id and has_meaningful_filters:
        try:
            db.scheme_search_history.insert_one({
                "user_id": user_id,
                "filters": {
                    "crop_name": crop_name,
                    "state": state,
                    "category": category,
                    "search": search,
                    "flagship": flagship
                },
                "result_count": len(schemes),
                "created_at": datetime.utcnow()
            })
        except Exception:
            pass

    return Response({
        "count": len(schemes),
        "schemes": schemes
    })


@api_view(["POST"])
def track_scheme_view(request):
    user_id = getattr(request, "user_id", None) or request.data.get("user_id")
    if not user_id:
        return Response({"message": "Login required"}, status=401)

    scheme_title = str(request.data.get("title") or "").strip()
    if not scheme_title:
        return Response({"message": "title is required"}, status=400)

    db = get_db()
    if db is None:
        return Response({"message": "DB unavailable"}, status=503)

    try:
        db.scheme_search_history.insert_one({
            "user_id": user_id,
            "action": "view",
            "scheme_title": scheme_title,
            "category": request.data.get("category"),
            "official_link": request.data.get("official_link"),
            "created_at": datetime.utcnow(),
        })
    except Exception:
        pass

    return Response({"message": "Scheme view tracked"}, status=200)