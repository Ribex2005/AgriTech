import os
import certifi
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI")

client = None
db = None

if not MONGO_URI:
    logger.warning("MONGO_URI is not set in environment variables; MongoDB features will be disabled.")
else:
    try:
        client = MongoClient(
            MONGO_URI, 
            tlsCAFile=certifi.where(), 
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        # Test connection
        client.admin.command("ping")
        db = client["AgroSense"]
        logger.info("✅ MongoDB connected successfully")
    except Exception as e:
        logger.warning(f"Could not connect to MongoDB: {e}")
        client = None
        db = None


def get_db(raise_on_missing: bool = False):
    """Return the `db` instance, or None if not available."""
    if db is None:
        if raise_on_missing:
            raise RuntimeError("MongoDB is not available")
        else:
            logger.debug("MongoDB not available")
    return db


def is_mongo_available():
    """Check if MongoDB is available"""
    return db is not None