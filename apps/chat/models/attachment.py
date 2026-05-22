from django.db import models


class Attachment(models.Model):

    class AttachmentType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        FILE = "file", "File"

    message = models.ForeignKey(
        "chat.Message",
        on_delete=models.CASCADE,
        related_name="attachments"
    )

    type = models.CharField(
        max_length=20,
        choices=AttachmentType.choices
    )

    file_url = models.TextField()

    file_name = models.CharField(max_length=255)

    mime_type = models.CharField(max_length=100)

    file_size = models.BigIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)