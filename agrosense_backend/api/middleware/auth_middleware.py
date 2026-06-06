from api.auth.jwt_utils import decode_token


class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get("Authorization")

        request.user_id = None

        if auth_header:
            try:
                token = auth_header.split(" ")[1]
                data = decode_token(token)
                if data:
                    request.user_id = data.get("user_id")
            except:
                pass

        return self.get_response(request)