from django.db import models
from apps.users.models import User

class Voucher(models.Model):
    DISCOUNT_TYPE = [
        ('percent', 'Percent'),
        ('fixed', 'Fixed'),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)

    max_usage = models.IntegerField()
    used_count = models.IntegerField(default=0)

    expired_at = models.DateTimeField()

    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="voucher_created")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="voucher_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class VoucherUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'voucher')