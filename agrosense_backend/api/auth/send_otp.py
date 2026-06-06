from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.mail import send_mail
from api.mongo_client import db
from datetime import datetime, timedelta
import random


def generate_otp():
    return str(random.randint(100000, 999999))


@api_view(["POST"])
def send_otp(request):
    email = request.data.get("email")

    if not email:
        return Response(
            {"message": "Email is required"},
            status=400
        )

    now = datetime.utcnow()

    # 🔍 Check if a valid OTP already exists
    existing_otp = db.otp_store.find_one({
        "email": email,
        "expires_at": {"$gt": now}
    })

    if existing_otp:
        return Response({
            "message": "OTP already sent. Please wait before requesting again."
        }, status=429)

    # 🔐 Generate OTP
    otp = generate_otp()

    # 🧹 Remove old OTPs (expired or used)
    db.otp_store.delete_many({"email": email})

    # ⏳ Store OTP (valid for 5 minutes)
    db.otp_store.insert_one({
        "email": email,
        "otp": otp,
        "created_at": now,
        "expires_at": now + timedelta(minutes=5),
        "verified": False
    })

    # 📧 Send OTP email (plain-text fallback + styled HTML)
    plain_message = (
        f"AgriTech Email Verification\n\n"
        f"Your OTP Code: {otp}\n"
        "Valid for 5 minutes only.\n\n"
        "AgriTech Team"
    )

    html_message = f"""
    <div style="margin:0;padding:24px;background:#f4f6f8;font-family:Arial,sans-serif;color:#1f2937;">
        <div style="max-width:620px;margin:0 auto;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #e5e7eb;">
            <div style="background:linear-gradient(135deg,#2e7d32,#66bb6a);padding:28px 24px;text-align:center;color:#ffffff;">
                <div style="font-size:42px;line-height:1;">🌱</div>
                <div style="font-size:36px;font-weight:700;letter-spacing:0.2px;margin-top:6px;">AgriTech</div>
                <div style="font-size:16px;opacity:0.95;margin-top:6px;">Email Verification</div>
            </div>

            <div style="padding:34px 28px 28px 28px;text-align:center;">
                <h2 style="margin:0 0 8px 0;font-size:34px;color:#111827;">Your OTP Code</h2>
                <p style="margin:0 0 22px 0;font-size:16px;color:#4b5563;">Use the following OTP to verify your email:</p>

                <div style="background:#f3f4f6;border:1px solid #e5e7eb;border-radius:14px;padding:22px 16px;margin:0 auto 20px auto;max-width:470px;">
                    <div style="font-size:54px;letter-spacing:12px;font-weight:700;color:#2e7d32;line-height:1.1;">{otp}</div>
                    <div style="margin-top:12px;font-size:16px;color:#6b7280;">⏱ Valid for 5 minutes only</div>
                </div>

                <p style="margin:24px 0 0 0;font-size:14px;color:#6b7280;">If you did not request this OTP, you can safely ignore this email.</p>
            </div>
        </div>
    </div>
    """

    send_mail(
        subject="AgriTech Login OTP",
        message=plain_message,
        from_email=None,  # Uses EMAIL_HOST_USER
        recipient_list=[email],
        fail_silently=False,
        html_message=html_message,
    )

    return Response({
        "message": "OTP sent successfully"
    })
