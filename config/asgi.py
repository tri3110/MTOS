import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack # Thêm cái này nếu cần auth
import apps.users.routing # Import trực tiếp module routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Khởi tạo Django ASGI app sớm để đảm bảo các model được nạp
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            apps.users.routing.websocket_urlpatterns
        )
    ),
})