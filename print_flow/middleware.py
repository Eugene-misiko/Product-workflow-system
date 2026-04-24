from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from urllib.parse import parse_qs

class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        import jwt
        from django.conf import settings
        from django.contrib.auth import get_user_model
        
        User = get_user_model()

        @database_sync_to_async
        def get_user(user_id):
            try:
                return User.objects.get(id=user_id)
            except (User.DoesNotExist, ValueError, TypeError):
                return AnonymousUser()

        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token_list = query_params.get("token", [None])
        token = token_list[0] if token_list else None

        if token:
            try:
                decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user_id = decoded_data.get("user_id")
                scope["user"] = await get_user(user_id)
            except Exception:
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)
