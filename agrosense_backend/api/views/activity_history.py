from rest_framework.decorators import api_view
from rest_framework.response import Response
from bson import ObjectId

from api.mongo_client import get_db


def _to_iso(value):
    try:
        return value.isoformat() if value else None
    except Exception:
        return str(value) if value is not None else None


@api_view(["GET"])
def activity_history(request):
    user_id = getattr(request, "user_id", None)
    if not user_id:
        return Response({"message": "Login required"}, status=401)

    db = get_db()
    if db is None:
        return Response({"message": "History service unavailable"}, status=503)

    items = []

    disease_records = db.disease_records.find(
        {"user_id": user_id, "is_guest": False}
    )
    for rec in disease_records:
        items.append(
            {
                "record_id": str(rec.get("_id")),
                "source": "disease_records",
                "type": "detection",
                "title": rec.get("crop_name") or "Crop Detection",
                "subtitle": rec.get("disease_name") or "-",
                "meta": {
                    "confidence": rec.get("confidence"),
                    "image": rec.get("image_name") or rec.get("image_path"),
                },
                "timestamp": _to_iso(rec.get("created_at")),
            }
        )

    chat_records = db.user_activity.find(
        {"user_id": user_id, "type": "chat"}
    )
    for rec in chat_records:
        data = rec.get("data", {})
        items.append(
            {
                "record_id": str(rec.get("_id")),
                "source": "user_activity",
                "type": "chat",
                "title": data.get("input") or "Chat Query",
                "subtitle": data.get("output") or "-",
                "meta": {
                    "intent": data.get("intent") or "general",
                },
                "timestamp": _to_iso(rec.get("timestamp")),
            }
        )

    market_records = db.market_price.find({"user_id": user_id})
    for rec in market_records:
        items.append(
            {
                "record_id": str(rec.get("_id")),
                "source": "market_price",
                "type": "market",
                "title": rec.get("crop_name") or "Market Price",
                "subtitle": rec.get("region") or "India",
                "meta": {
                    "min_price": rec.get("min_price"),
                    "max_price": rec.get("max_price"),
                    "avg_price": rec.get("avg_price"),
                },
                "timestamp": _to_iso(rec.get("created_at") or rec.get("date")),
            }
        )

    scheme_records = db.scheme_search_history.find({"user_id": user_id})
    for rec in scheme_records:
        if rec.get("action") == "view":
            items.append(
                {
                    "record_id": str(rec.get("_id")),
                    "source": "scheme_search_history",
                    "type": "schemes",
                    "title": rec.get("scheme_title") or "Scheme Viewed",
                    "subtitle": "Viewed details",
                    "meta": {
                        "action": "view",
                        "category": rec.get("category"),
                    },
                    "timestamp": _to_iso(rec.get("created_at")),
                }
            )
            continue

        filters = rec.get("filters", {})
        if not any([
            bool(filters.get("crop_name")),
            bool(filters.get("state")),
            bool(filters.get("category")),
            bool(filters.get("search")),
        ]):
            continue

        scheme_query = filters.get("search") or filters.get("crop_name") or "Scheme Search"
        items.append(
            {
                "record_id": str(rec.get("_id")),
                "source": "scheme_search_history",
                "type": "schemes",
                "title": scheme_query,
                "subtitle": filters.get("state") or filters.get("category") or "All",
                "meta": {
                    "filters": filters,
                    "result_count": rec.get("result_count", 0),
                },
                "timestamp": _to_iso(rec.get("created_at")),
            }
        )

    items.sort(key=lambda x: x.get("timestamp") or "", reverse=True)

    return Response({"count": len(items), "items": items})


@api_view(["POST"])
def delete_activity_history(request):
    user_id = getattr(request, "user_id", None)
    if not user_id:
        return Response({"message": "Login required"}, status=401)

    db = get_db()
    if db is None:
        return Response({"message": "History service unavailable"}, status=503)

    mode = str(request.data.get("mode") or "selected").strip().lower()

    deleted = 0
    if mode == "all":
        deleted += db.disease_records.delete_many({"user_id": user_id, "is_guest": False}).deleted_count
        deleted += db.user_activity.delete_many({"user_id": user_id, "type": "chat"}).deleted_count
        deleted += db.market_price.delete_many({"user_id": user_id}).deleted_count
        deleted += db.scheme_search_history.delete_many({"user_id": user_id}).deleted_count
        return Response({"message": "Activity history cleared", "deleted": deleted}, status=200)

    entries = request.data.get("entries") or []
    if not isinstance(entries, list) or not entries:
        return Response({"message": "entries list is required"}, status=400)

    collection_map = {
        "disease_records": db.disease_records,
        "user_activity": db.user_activity,
        "market_price": db.market_price,
        "scheme_search_history": db.scheme_search_history,
    }

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        source = entry.get("source")
        record_id = entry.get("record_id")
        coll = collection_map.get(source)
        if coll is None or not record_id:
            continue

        try:
            oid = ObjectId(str(record_id))
        except Exception:
            continue

        deleted += coll.delete_one({"_id": oid, "user_id": user_id}).deleted_count

    return Response({"message": "Selected activity deleted", "deleted": deleted}, status=200)
