from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.mongo_client import db
from .jwt_utils import generate_token
from datetime import datetime
import uuid


def generate_user_id():
    return f"USR_{uuid.uuid4().hex[:6]}"


@api_view(["POST"])
def verify_otp(request):
    email = request.data.get("email")
    otp = request.data.get("otp")
    name = request.data.get("name")  # optional

    if not email or not otp:
        return Response(
            {"message": "Email and OTP are required"},
            status=400
        )

    # 1️⃣ Check OTP validity
    record = db.otp_store.find_one({
        "email": email,
        "otp": otp
    })

    if not record:
        return Response(
            {"message": "Invalid or expired OTP"},
            status=400
        )

    # 2️⃣ Find or create user
    user = db.users.find_one({"email": email})

    if not user:
        user = {
            "user_id": generate_user_id(),
            "email": email,
            "name": name if name else email.split("@")[0],
            "language": "en",
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow()
        }
        db.users.insert_one(user)
    else:
        update_data = {"last_login": datetime.utcnow()}
        if name:
            update_data["name"] = name

        db.users.update_one(
            {"email": email},
            {"$set": update_data}
        )

        # 🔥 IMPORTANT: refresh user object
        user = db.users.find_one({"email": email})

    # 3️⃣ OTP is single-use → delete
    db.otp_store.delete_many({"email": email})

    # 🔥 4️⃣ GENERATE JWT TOKEN (THIS IS THE NEW PART)
    token = generate_token(user["user_id"])

    # 🔥 5️⃣ RETURN TOKEN + USER INFO
    return Response({
        "message": "Login successful",
        "user_id": user["user_id"],
        "email": email,
        "token": token   # ⭐ VERY IMPORTANT
    })
