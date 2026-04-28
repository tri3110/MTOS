from django.utils import timezone
from apps.vouchers.models import Voucher, VoucherUsage
from django.db import transaction

def validate_voucher(voucher, user, order_total):
    if not voucher.is_active:
        raise Exception("Voucher không hoạt động")

    if voucher.used_count >= voucher.max_usage:
        raise Exception("Voucher đã hết lượt sử dụng")

    if voucher.expired_at < timezone.now():
        raise Exception("Voucher đã hết hạn")

    if order_total < voucher.min_order_value:
        raise Exception("Đơn hàng chưa đủ điều kiện")

    if VoucherUsage.objects.filter(user=user, voucher=voucher).exists():
        raise Exception("Bạn đã dùng voucher này rồi")

    return True

def apply_voucher(voucher: Voucher, user, order_total: float):
    validate_voucher(voucher, user, order_total)

    if voucher.discount_type == 'percent':
        discount = order_total * (voucher.discount_value / 100)
    else:
        discount = voucher.discount_value

    return min(discount, order_total)  # tránh âm tiền

@transaction.atomic
def use_voucher(voucher, user):
    voucher = Voucher.objects.select_for_update().get(id=voucher.id)

    if voucher.used_count >= voucher.max_usage:
        raise Exception("Hết lượt")

    # check user
    if VoucherUsage.objects.filter(user=user, voucher=voucher).exists():
        raise Exception("Bạn đã dùng rồi")

    voucher.used_count += 1
    voucher.save()

    VoucherUsage.objects.create(user=user, voucher=voucher)