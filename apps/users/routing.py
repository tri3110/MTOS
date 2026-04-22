from django.urls import re_path
from .consumers import UserConsumer

websocket_urlpatterns = [
    re_path(r"ws/user/(?P<user_id>\d+)/$", UserConsumer.as_asgi()),
]