from pymongo import MongoClient
import certifi
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")


def test_connection():
    """Simple helper to test Mongo connectivity when run manually."""
    if not MONGO_URI:
        print("MONGO_URI is not set; skipping Mongo test.")
        return

    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
        db = client.get_database("AgroSense")

        test_col = db.test_connection
        res = test_col.insert_one({"hello": "world"})
        print("Inserted ID:", res.inserted_id)

        doc = test_col.find_one({"_id": res.inserted_id})
        print("Fetched Document:", doc)

        test_col.delete_one({"_id": res.inserted_id})
        print("✅ MongoDB connection successful!")
    except Exception as e:
        print("MongoDB test failed:", e)


if __name__ == "__main__":
    test_connection()
