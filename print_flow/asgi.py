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
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
import notifications.routing  # we will create this

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
application = ProtocolTypeRouter({
    "http": get_asgi_application(),

    "websocket": AuthMiddlewareStack(
        URLRouter(
            notifications.routing.websocket_urlpatterns
        )
    ),
})
