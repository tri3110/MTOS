from django.db import models
from apps.users.models import User

class MessageRead(models.Model):

    message = models.ForeignKey(
        "chat.Message",
        on_delete=models.CASCADE,
        related_name="reads"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("message", "user")

        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["message"]),
        ]