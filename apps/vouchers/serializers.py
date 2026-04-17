from rest_framework import serializers
from apps.vouchers.models import Voucher
from django.utils import timezone

class VoucherSerializer(serializers.ModelSerializer):

    class Meta:
        model = Voucher
        fields = "__all__"

    def get_is_expired(self, obj):
        return obj.expired_at < timezone.now()