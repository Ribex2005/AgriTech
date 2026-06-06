from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .detect_serializer import DetectSerializer
from api.ml_model import predict_image
from api.mongo_client import get_db, is_mongo_available

import os
import datetime
import logging
import threading
import traceback

logger = logging.getLogger(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def _save_to_mongo(user_id, is_guest, crop_name, image_filename, image_path,
                   predicted_disease, confidence, details):
    """
    Save result in background thread with proper error handling
    """
    try:
        if not user_id:
            logger.info("Guest user detected - skipping detection save")
            return

        # Check if MongoDB is available
        if not is_mongo_available():
            logger.warning("MongoDB not available - skipping save")
            return
            
        db = get_db()
        if db is None:
            logger.warning("MongoDB connection is None - skipping save")
            return

        # Insert disease record
        result = db.disease_records.insert_one({
            "user_id": user_id,
            "is_guest": is_guest,
            "crop_name": crop_name,
            "image_name": image_filename,
            "image_path": image_path,
            "disease_name": predicted_disease,
            "confidence": confidence,
            "cause": details.get("cause") or details.get("disease", ""),
            "remedy": details.get("cure", ""),
            "created_at": datetime.datetime.utcnow()
        })
        
        logger.info(f"Saved detection to MongoDB: {result.inserted_id}")

        # Save user activity if logged in
        if user_id:
            db.user_activity.insert_one({
                "user_id": user_id,
                "type": "disease",
                "data": {
                    "image": image_filename,
                    "prediction": predicted_disease,
                    "crop": crop_name,
                    "confidence": confidence
                },
                "timestamp": datetime.datetime.utcnow()
            })
            logger.info(f"Saved user activity for: {user_id}")

    except Exception as e:
        logger.error(f"MongoDB save failed (background): {e}")
        logger.error(traceback.format_exc())


def cleanup_file_after_delay(image_path, delay=5):
    """Delete file after delay"""
    def delete_file():
        import time
        time.sleep(delay)
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                logger.info(f"Cleaned up: {image_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {image_path}: {e}")
    
    thread = threading.Thread(target=delete_file, daemon=True)
    thread.start()


@method_decorator(csrf_exempt, name='dispatch')
class DetectDisease(GenericAPIView):

    serializer_class = DetectSerializer
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        logger.info("=" * 60)
        logger.info("New detection request received")
        
        try:
            # Validate serializer
            serializer = self.get_serializer(data=request.data)

            if not serializer.is_valid():
                logger.warning(f"Serializer validation failed: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Get user info
            user_id = getattr(request, "user_id", None)
            is_guest = not bool(user_id)
            logger.info(f"User: {'Guest' if is_guest else user_id}")

            # Get image
            image = request.FILES.get("image")

            if not image:
                logger.warning("No image in request")
                return Response({"error": "No image uploaded"}, status=400)

            logger.info(f"Image: {image.name}, Size: {image.size} bytes")

            # Validate image size (10 MB limit)
            if image.size > 10 * 1024 * 1024:
                logger.warning(f"Image too large: {image.size}")
                return Response({"error": "Image too large. Maximum 10MB."}, status=400)

            # Save image
            timestamp = int(datetime.datetime.utcnow().timestamp())
            image_filename = f"{timestamp}_{image.name.replace(' ', '_')}"
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)

            try:
                with open(image_path, "wb+") as destination:
                    for chunk in image.chunks():
                        destination.write(chunk)
                logger.info(f"Image saved: {image_path}")
            except Exception as e:
                logger.error(f"Failed to save image: {e}")
                return Response({"error": f"Failed to save image: {str(e)}"}, status=500)

            # Run model prediction
            logger.info("Running model prediction...")
            try:
                result = predict_image(image_path)
                logger.info(f"Prediction result: {result}")
            except Exception as e:
                logger.error(f"Prediction failed: {e}")
                logger.error(traceback.format_exc())
                cleanup_file_after_delay(image_path)
                return Response({"error": f"Prediction failed: {str(e)}"}, status=500)

            # Check for model error
            if "error" in result:
                logger.error(f"Model error: {result['error']}")
                cleanup_file_after_delay(image_path)
                return Response({"error": result['error']}, status=500)

            # Extract results
            predicted_disease = result.get("predicted_class", "Unknown")
            confidence_raw = result.get("confidence", 0)
            
            # 🔧 FIX: Normalize confidence (if > 1, treat as percentage and divide by 100)
            if confidence_raw > 1:
                confidence = confidence_raw / 100.0
            else:
                confidence = confidence_raw
                
            details = result.get("details", {}) or {}
            top_3 = result.get("top_3", [])
            warning = result.get("warning", None)

            # Get crop name and readable disease name
            crop_name = details.get("crop", "Unknown")
            if crop_name == "Unknown" and predicted_disease != "Unknown":
                crop_name = predicted_disease.split("_")[0] if "_" in predicted_disease else "Unknown"
            
            # Get readable disease name from details (not the raw class name)
            readable_disease = details.get("disease", predicted_disease)

            logger.info(f"Detection result - Crop: {crop_name}, Disease: {readable_disease}, Confidence: {confidence:.2%}")

            # Save to MongoDB in background (logged-in users only)
            if user_id and is_mongo_available():
                try:
                    thread = threading.Thread(
                        target=_save_to_mongo,
                        args=(
                            user_id,
                            is_guest,
                            crop_name,
                            image_filename,
                            image_path,
                            predicted_disease,
                            confidence,
                            details
                        ),
                        daemon=True
                    )
                    thread.start()
                    logger.info("Started background save to MongoDB")
                except Exception as e:
                    logger.warning(f"Failed to start background save: {e}")
            elif not user_id:
                logger.info("Guest detection - not saving to history")
            else:
                logger.info("MongoDB not available - skipping save")

            # Schedule file cleanup
            cleanup_file_after_delay(image_path, delay=5)

            # Prepare and send response
            response_data = {
                "message": "Detection successful",
                "disease": readable_disease,
                "crop_name": crop_name,
                "confidence": confidence,  # Now always 0-1
                "details": details,
                "top_3": top_3,
                "warning": warning,
                "is_guest": is_guest
            }

            logger.info("Sending successful response")
            logger.info("=" * 60)
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.error(traceback.format_exc())
            return Response({"error": f"Server error: {str(e)}"}, status=500)