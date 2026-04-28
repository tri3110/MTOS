from django.urls import path
from apps.ai_service.views import ChatBotView

urlpatterns = [
    path('chat/', ChatBotView.as_view(), name='chat'),
]