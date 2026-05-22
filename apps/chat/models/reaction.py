from django.db import models
from apps.users.models import User

class MessageReaction(models.Model):

    message = models.ForeignKey(
        "chat.Message",
        on_delete=models.CASCADE,
        related_name="reactions"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    reaction = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            "message",
            "user",
            "reaction"
        )