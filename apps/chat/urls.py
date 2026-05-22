from django.urls import path
from apps.chat.views import ConversationCreateAPIView, ConversationListAPIView, ConversationMessageListAPIView, GroupUserAPIView, SendMessageAPIView

urlpatterns = [
    path("conversations/", ConversationListAPIView.as_view(), name="conversation-list"),
    path(
        "conversations/<int:conversation_id>/messages/", 
        ConversationMessageListAPIView.as_view(), 
        name="conversation-message-list"
    ),
    path(
        "conversations/<int:conversation_id>/send/",
        SendMessageAPIView.as_view()
    ),
    path(
        "conversations/<int:conversation_id>/remove-user/",
        GroupUserAPIView.as_view()
    ),

    path(
        "conversations/create/",
        ConversationCreateAPIView.as_view()
    )
]