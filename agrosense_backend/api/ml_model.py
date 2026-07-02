import tensorflow as tf
import numpy as np
import json
import os
import logging
import zipfile
import time
import threading
import queue
from functools import lru_cache
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from .disease_info import disease_info

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# PATH SETUP
# =========================

API_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(API_DIR, "models")

MODEL_PATH = os.path.join(MODELS_DIR, "final_model.keras")
CLASS_NAMES_PATH = os.path.join(MODELS_DIR, "classes.json")
MODEL_ARCHIVE_PATH = os.path.join(MODELS_DIR, "final_model_archive.keras")

logger.info(f"Model path: {MODEL_PATH}")
logger.info(f"Class names path: {CLASS_NAMES_PATH}")

# Global variables
_model = None
_model_image_size = (128, 128)
_class_names = []
_prediction_lock = threading.Lock()


def _normalize_keras_path(path):
    """
    If path points to a directory named *.keras (with config.json/weights),
    create a zip-based .keras archive that tf.keras.load_model can consume.
    """
    if not (path.endswith(".keras") and os.path.isdir(path)):
        return path

    archive_path = MODEL_ARCHIVE_PATH

    try:
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(path):
                for filename in files:
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, path)
                    zf.write(full_path, arcname=rel_path)

        logger.info(f"Packed directory model into archive: {archive_path}")
        return archive_path
    except Exception as e:
        logger.error(f"Failed to pack .keras directory '{path}': {e}")
        return path


def load_model_with_timeout(model_path, timeout_seconds=30):
    """Load model with timeout to prevent hanging"""
    result_queue = queue.Queue()
    
    def load_model_thread():
        try:
            effective_path = _normalize_keras_path(model_path)
            logger.info(f"Loading model from: {effective_path}")
            
            # Limit TensorFlow threads to reduce memory
            tf.config.threading.set_inter_op_parallelism_threads(2)
            tf.config.threading.set_intra_op_parallelism_threads(2)
            
            loaded_model = tf.keras.models.load_model(
                effective_path, 
                compile=False, 
                safe_mode=False
            )
            result_queue.put(loaded_model)
        except Exception as e:
            result_queue.put(e)
    
    # Start loading in separate thread
    load_thread = threading.Thread(target=load_model_thread, daemon=True)
    load_thread.start()
    load_thread.join(timeout_seconds)
    
    if load_thread.is_alive():
        logger.error(f"Model loading timed out after {timeout_seconds} seconds")
        return None
    
    result = result_queue.get()
    if isinstance(result, Exception):
        logger.error(f"Model loading failed: {result}")
        return None
    
    return result


def load_class_names():
    """Load class names with error handling"""
    try:
        if not os.path.exists(CLASS_NAMES_PATH):
            logger.error(f"Class names file not found: {CLASS_NAMES_PATH}")
            return []
            
        with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as f:
            names = json.load(f)

        if not isinstance(names, list) or not names:
            logger.error("classes.json must be a non-empty JSON array")
            return []
            
        logger.info(f"Class names loaded. Count={len(names)}")
        return names
    except Exception as e:
        logger.error(f"Class names loading failed: {e}")
        return []


def initialize_model():
    """Initialize model at module load with timeout"""
    global _model, _model_image_size, _class_names
    
    logger.info("Initializing model...")
    
    # Load class names first
    _class_names = load_class_names()
    
    # Load model with timeout
    if os.path.exists(MODEL_PATH):
        _model = load_model_with_timeout(MODEL_PATH, timeout_seconds=30)
        
        if _model is not None:
            # Infer image size from model
            try:
                input_shape = _model.input_shape
                if input_shape and len(input_shape) >= 3:
                    inferred_h = int(input_shape[1])
                    inferred_w = int(input_shape[2])
                    if inferred_h > 0 and inferred_w > 0:
                        _model_image_size = (inferred_h, inferred_w)
                logger.info(f"Model loaded successfully. Input size={_model_image_size}")
            except Exception as e:
                logger.warning(f"Could not infer input shape: {e}")
        else:
            logger.error("Model failed to load")
    else:
        logger.error(f"Model file not found: {MODEL_PATH}")

# Initialize model at module load

def preprocess_image(img_path, target_size=None):
    """Preprocess image with error handling"""
    try:
        size = target_size or _model_image_size
        
        img = image.load_img(img_path, target_size=size)
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        
        return img_array
    except Exception as e:
        logger.error(f"Image preprocessing error: {e}")
        return None


def predict_with_timeout(img_array, timeout_seconds=10):
    """Run prediction with timeout"""
    if _model is None:
        raise Exception("Model not loaded")
    
    result_queue = queue.Queue()
    
    def predict_thread():
        try:
            with _prediction_lock:  # Only one prediction at a time
                prediction = _model.predict(img_array, verbose=0)
                result_queue.put(prediction)
        except Exception as e:
            result_queue.put(e)
    
    # Start prediction in separate thread
    pred_thread = threading.Thread(target=predict_thread, daemon=True)
    pred_thread.start()
    pred_thread.join(timeout_seconds)
    
    if pred_thread.is_alive():
        logger.error(f"Prediction timed out after {timeout_seconds} seconds")
        raise TimeoutError("Prediction timeout")
    
    result = result_queue.get()
    if isinstance(result, Exception):
        raise result
    
    return result


def normalize_confidence(value):
    """
    Normalize confidence value to be between 0 and 1
    Returns 0-1 decimal value
    """
    if value is None:
        return 0.0
    try:
        value = float(value)
        # If value > 1, treat as percentage (0-100) and convert to decimal (0-1)
        if value > 1:
            return min(1.0, max(0.0, value / 100.0))
        # Already in decimal range
        return min(1.0, max(0.0, value))
    except (ValueError, TypeError):
        return 0.0

def predict_image(img_path):
    return {
        "predicted_class": "test",
        "confidence": 1.0,
        "details": {},
        "top_3": []
    }

def test_prediction(image_path=None):
    """Utility function to test prediction with a sample image"""
    if image_path is None:
        # Use a default test image if available
        test_image = os.path.join(API_DIR, "test_image.jpg")
        if os.path.exists(test_image):
            image_path = test_image
        else:
            logger.error("No test image provided and default not found")
            return
    
    logger.info(f"Testing prediction with: {image_path}")
    result = predict_image(image_path)
    logger.info(f"Test result: {json.dumps(result, indent=2)}")
    return result


# Cleanup function for graceful shutdown
def cleanup():
    """Clean up resources"""
    global _model
    logger.info("Cleaning up model resources...")
    if _model:
        tf.keras.backend.clear_session()
        _model = None
    logger.info("Cleanup completed")


# Register cleanup on exit
import atexit
atexit.register(cleanup)


if __name__ == "__main__":
    # Test the model if run directly
    test_prediction()
