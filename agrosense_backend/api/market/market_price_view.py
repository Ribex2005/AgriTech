from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.mongo_client import get_db
import requests
from datetime import datetime
import os
import uuid
import logging

DATA_GOV_URL = os.getenv("DATA_GOV_URL")
API_KEY = os.getenv("DATA_GOV_API_KEY")

logger = logging.getLogger(__name__)

MOCK_DATA = {
    "tomato": {"min": 1200, "max": 2000, "avg": 1600},
    "potato": {"min": 800, "max": 1400, "avg": 1100},
    "onion": {"min": 1000, "max": 2200, "avg": 1700},
    "wheat": {"min": 2100, "max": 2400, "avg": 2250},
    "rice": {"min": 1800, "max": 2500, "avg": 2150},
    "corn": {"min": 1500, "max": 1900, "avg": 1700},
    "maize": {"min": 1500, "max": 1900, "avg": 1700},
    "cotton": {"min": 5000, "max": 6500, "avg": 5800},
    "soybean": {"min": 3500, "max": 4200, "avg": 3850},
    "sugarcane": {"min": 280, "max": 350, "avg": 315},
    "pulse": {"min": 4000, "max": 6000, "avg": 5000},
    "bell pepper": {"min": 3000, "max": 5000, "avg": 4000},
    "apple": {"min": 6000, "max": 12000, "avg": 9000},
}


def _fallback_price_payload(crop_name, region, reason):
    data = MOCK_DATA.get(str(crop_name).lower())
    if data:
        return {
            "crop_name": crop_name,
            "min_price": data["min"],
            "max_price": data["max"],
            "avg_price": data["avg"],
            "region": region,
            "source": "offline_fallback",
            "note": reason,
        }

    return None


def _store_market_history(user_id, crop_name, region, min_price, max_price, avg_price, source):
    try:
        db = get_db()
        if db is None:
            return

        record = {
            "priceID": f"PRICE_{uuid.uuid4().hex[:6]}",
            "user_id": user_id,
            "crop_name": crop_name,
            "date": datetime.utcnow(),
            "min_price": min_price,
            "max_price": max_price,
            "avg_price": avg_price,
            "region": region,
            "source": source,
            "created_at": datetime.utcnow(),
        }
        db.market_price.insert_one(record)
    except Exception as db_exc:
        logger.warning("Failed to store market price history: %s", db_exc)

@api_view(["GET"])
def get_market_price(request):
    crop_name = request.GET.get("crop_name")
    user_id = getattr(request, "user_id", None) or request.GET.get("user_id")
    region = request.GET.get("region", "India")

    if not crop_name:
        return Response({"message": "crop_name is required"}, status=400)

    # Fetch from data.gov.in
    params = {
        "api-key": API_KEY,
        "format": "json",
        "filters[commodity]": crop_name
    }
    if not DATA_GOV_URL or not API_KEY:
        payload = _fallback_price_payload(crop_name, region, "Live market API is not configured")
        if payload is None:
            return Response({"message": "No reliable market data found for this crop"}, status=404)
        _store_market_history(
            user_id,
            crop_name,
            region,
            payload.get("min_price"),
            payload.get("max_price"),
            payload.get("avg_price"),
            payload.get("source", "offline_fallback"),
        )
        return Response(payload, status=200)

    try:
        response = requests.get(DATA_GOV_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        records = data.get("records", [])
        prices = []
        for rec in records:
            price_val = rec.get("modal_price")
            if price_val in (None, ""):
                continue
            try:
                prices.append(float(price_val))
            except (TypeError, ValueError):
                continue

        if not prices:
            payload = _fallback_price_payload(crop_name, region, "No valid live records found")
            if payload is None:
                return Response({"message": "No reliable market data found for this crop"}, status=404)
            _store_market_history(
                user_id,
                crop_name,
                region,
                payload.get("min_price"),
                payload.get("max_price"),
                payload.get("avg_price"),
                payload.get("source", "offline_fallback"),
            )
            return Response(payload, status=200)

        min_price = min(prices)
        max_price = max(prices)
        avg_price = round(sum(prices) / len(prices), 2)

        _store_market_history(user_id, crop_name, region, min_price, max_price, avg_price, "data.gov.in")

        return Response({
            "crop_name": crop_name,
            "min_price": min_price,
            "max_price": max_price,
            "avg_price": avg_price,
            "region": region,
            "source": "data.gov.in"
        })
    except requests.RequestException as req_exc:
        logger.warning("Live market API request failed: %s", req_exc)
        payload = _fallback_price_payload(crop_name, region, "Live market API unavailable")
        if payload is None:
            return Response({"message": "No reliable market data found for this crop"}, status=404)
        _store_market_history(
            user_id,
            crop_name,
            region,
            payload.get("min_price"),
            payload.get("max_price"),
            payload.get("avg_price"),
            payload.get("source", "offline_fallback"),
        )
        return Response(payload, status=200)
    except ValueError as parse_exc:
        logger.warning("Live market API parse failed: %s", parse_exc)
        payload = _fallback_price_payload(crop_name, region, "Live market API parse error")
        if payload is None:
            return Response({"message": "No reliable market data found for this crop"}, status=404)
        _store_market_history(
            user_id,
            crop_name,
            region,
            payload.get("min_price"),
            payload.get("max_price"),
            payload.get("avg_price"),
            payload.get("source", "offline_fallback"),
        )
        return Response(payload, status=200)
