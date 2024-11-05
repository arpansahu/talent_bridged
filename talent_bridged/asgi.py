import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import celery_progress_custom_app.routing as celery_progress_custom_app_routing


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_bridged.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                celery_progress_custom_app_routing.websocket_urlpatterns
            )
        ),
    ),
})