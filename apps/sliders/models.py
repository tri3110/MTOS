from django.db import models
from apps.users.models import User

class Slider(models.Model):
    title = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='sliders/')
    link = models.CharField(max_length=255, blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="slider_created")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="slider_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']