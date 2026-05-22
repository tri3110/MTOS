from django.db import models
from django.conf import settings

from apps.users.models import User


class Conversation(models.Model):

    class ConversationType(models.TextChoices):
        PRIVATE = "private", "Private"
        GROUP = "group", "Group"
        CHANNEL = "channel", "Channel"

    type = models.CharField(
        max_length=20,
        choices=ConversationType.choices
    )

    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    avatar = models.TextField(
        blank=True,
        null=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_conversations"
    )

    last_message = models.ForeignKey(
        "chat.Message",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+"
    )

    last_message_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.type}"