from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.mongo_client import get_db

@api_view(["GET"])
def market_price_history(request):
    user_id = request.GET.get("user_id")

    if not user_id:
        return Response({"message": "user_id required"}, status=400)

    db = get_db()
    records = list(
        db.market_price.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1)
    )

    return Response({
        "count": len(records),
        "records": records
    })
