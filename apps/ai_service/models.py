from django.db import models
from apps.users.models import User

class MessageCache(models.Model):
    message_hash = models.CharField(max_length=32, db_index=True)
    normalized_text = models.TextField()

    parsed_data = models.JSONField()
    parsed_intent = models.CharField(max_length=50)
    response_text = models.TextField(null=True, blank=True)

    is_context_dependent = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

class ChatMessage(models.Model):
    STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('confirming', 'Confirming'),
        ('order', 'Order'),
        ('modify', 'Modify'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idle')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    draft_order = models.JSONField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)