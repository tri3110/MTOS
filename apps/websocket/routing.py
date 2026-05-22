from django.urls import re_path
from .consumers import ChatConsumer, UserConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_id>\w+)/$", ChatConsumer.as_asgi()),
    re_path(r"ws/user/(?P<user_id>\d+)/$", UserConsumer.as_asgi()),
]