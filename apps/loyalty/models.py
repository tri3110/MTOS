from django.db import models
from apps.orders.models import Order
from apps.users.models import User

class LoyaltyTransaction(models.Model):
    TYPE_CHOICES = [
        ('earn', 'Earn'),
        ('redeem', 'Redeem'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    points = models.IntegerField()
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)