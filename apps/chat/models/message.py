from django.db import models
from apps.users.models import User

class Message(models.Model):

    class MessageType(models.TextChoices):
        TEXT = "text", "Text"
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        FILE = "file", "File"
        SYSTEM = "system", "System"

    conversation = models.ForeignKey(
        "chat.Conversation",
        on_delete=models.CASCADE,
        related_name="messages"
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )

    type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT
    )

    content = models.TextField(
        blank=True,
        null=True
    )

    metadata = models.JSONField(
        default=dict,
        blank=True
    )

    reply_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    is_edited = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

        indexes = [
            models.Index(fields=["conversation", "-id"]),
            models.Index(fields=["conversation", "-created_at"]),
            models.Index(fields=["sender"]),
        ]

    def __str__(self):
        return f"{self.id}"