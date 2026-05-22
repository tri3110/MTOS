import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack # Thêm cái này nếu cần auth

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Khởi tạo Django ASGI app sớm để đảm bảo các model được nạp
django_asgi_app = get_asgi_application()

from apps.websocket.routing import websocket_urlpatterns # Import trực tiếp module routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})