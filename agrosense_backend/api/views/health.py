from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.mongo_client import get_db

@api_view(['GET'])
def health(request):
    try:
        db = get_db()
        if db is None:
            return Response({"status": "warning", "message": "Backend running, but MongoDB not connected."})
        collection_names = db.list_collection_names()
        return Response({
            "status": "ok",
            "message": "Backend and MongoDB connected successfully!",
            "collections": collection_names
        })
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=500)
