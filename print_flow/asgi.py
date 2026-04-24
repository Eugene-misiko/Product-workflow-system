"""
ASGI config for print_flow project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

# import os
# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'print_flow.settings')

# application = get_asgi_application()
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'print_flow.settings')
# django.setup()

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),

#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             notifications.routing.websocket_urlpatterns
#         )
#     ),
# })
import os
import django
from django.core.asgi import get_asgi_application

# A. Set settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'print_flow.settings')

# B. Start Django HTTP (This MUST happen first)
django_asgi_app = get_asgi_application()

# C. Import Channels stuff ONLY AFTER B is done
from channels.routing import ProtocolTypeRouter, URLRouter
from print_flow.middleware import JWTAuthMiddleware
import notifications.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(notifications.routing.websocket_urlpatterns)
    ),
})

