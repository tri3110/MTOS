from django.db import models

class Voucher(models.Model):
    DISCOUNT_TYPE = [
        ('percent', 'Percent'),
        ('fixed', 'Fixed'),
    ]

    code = models.CharField(max_length=50)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_usage = models.IntegerField()
    used_count = models.IntegerField(default=0)
    expired_at = models.DateTimeField()