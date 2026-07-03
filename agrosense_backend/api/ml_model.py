import logging

logger = logging.getLogger(__name__)

logger.info("ml_model imported")

def predict_image(img_path):
    return {
        "predicted_class": "test",
        "confidence": 1.0,
        "details": {},
        "top_3": []
    }
