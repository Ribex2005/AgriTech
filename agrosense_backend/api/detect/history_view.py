from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.mongo_client import get_db


@api_view(["GET"])
def disease_history(request):
    """
    Fetch disease detection history for logged-in user (JWT based)
    """

    # ✅ GET USER FROM JWT
    user_id = getattr(request, "user_id", None)

    # ❌ No login → block
    if not user_id:
        return Response(
            {"message": "Login required"},
            status=401
        )

    db = get_db()

    # ✅ Fetch only this user's records
    records_cursor = db.disease_records.find(
        {
            "user_id": user_id,
            "is_guest": False
        }
    ).sort("created_at", -1)

    records = []

    for record in records_cursor:
        records.append({
            "crop_name": record.get("crop_name"),
            "disease_name": record.get("disease_name"),
            "image_path": record.get("image_path"),
            "created_at": record.get("created_at")
        })

    return Response({
        "count": len(records),
        "records": records
    })