import uuid

from apps.carts.models import Cart, CartItem
from apps.orders.models import Order, OrderItem, OrderItemOption, OrderItemTopping, OrderVoucher
from apps.users.authentication import CookieJWTAuthentication
from apps.vouchers.models import Voucher
from apps.vouchers.service import apply_voucher
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from common.constants import Constant
from common.redis_client import redis_client
from common.kafka_producer import send_order_created
from common.utils import get_distance

class PaymentView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            with transaction.atomic():

                user = request.user
                data = request.data
                shipping_voucher = data.get("shipping_voucher")
                order_voucher = data.get("order_voucher")

                lock_key = f"lock_order_{user.id}"
                if not redis_client.set(lock_key, 1, ex=10, nx=True):
                    return Response({"error": "Đang xử lý đơn hàng"}, status=400)

                try:
                    rate_key = f"rate_{user.id}"
                    count = redis_client.incr(rate_key)

                    if count == 1:
                        redis_client.expire(rate_key, 60)

                    if count > 5:
                        return Response({"error": "Too many requests"}, status=429)

                    cart, _ = Cart.objects.get_or_create(user=user)
                    cart_items = cart_items.prefetch_related("options__option","toppings__topping")

                    if not cart_items:
                        return Response({"error": "Cart is empty"}, status=400)

                    order = Order.objects.create(
                        user=user,
                        customer_name=user.full_name or user.email,
                        idempotency_key=str(uuid.uuid4()),
                        total_price=0,
                        delivery_address=data.get("delivery_address", ""),
                        status="PENDING"
                    )

                    shipping_fee = Constant.SHIPPING_FEE

                    if shipping_voucher != -1:
                        shipping_fee = 0

                    total = 0

                    for item in cart_items:
                        base_price = item.price_snapshot or item.product.price
                        order_item = OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            quantity=item.quantity,
                            price=base_price
                        )

                        total += base_price * item.quantity

                        for item_option in item.options.all():
                            option_price = item_option.option.price
                            OrderItemOption.objects.create(
                                order_item=order_item,
                                option=item_option.option,
                                price=option_price
                            )
                            total += option_price * item.quantity

                        for item_topping in item.toppings.all():
                            OrderItemTopping.objects.create(
                                order_item=order_item,
                                topping=item_topping.topping,
                                price=item_topping.price,
                                quantity=item_topping.quantity
                            )
                            total += item_topping.price * item_topping.quantity

                    discount_amount = 0
                    if order_voucher != -1:
                        try:
                            voucher = Voucher.objects.get(id=order_voucher)
                        except Voucher.DoesNotExist:
                            return Response({"error": "Voucher không tồn tại"}, status=400)

                        if voucher.voucher_type != "order":
                            return Response({"error": "Voucher không hợp lệ cho đơn hàng"}, status=400)

                        discount_amount = apply_voucher(voucher, user, total)
                        OrderVoucher.objects.create(
                            order=order,
                            voucher=voucher,
                            discount_amount=discount_amount
                        )

                    order.total_price = max(0, total + shipping_fee - discount_amount)
                    order.save()

                    transaction.on_commit(lambda: send_order_created(order))

                    return Response({
                        "order_id": order.id,
                        "status": "PROCESSING"
                    })

                finally:
                    redis_client.delete(lock_key)

        except Exception as e:
            return Response({"message": str(e)}, status=400)

class MomoIPNView(APIView):
    def post(self, request):
        data = request.data

        order_id = data.get("orderId")
        result_code = data.get("resultCode")

        try:
            order = Order.objects.get(id=order_id)

            if result_code == 0:
                order.status = "confirmed"
            else:
                order.status = "cancelled"

            order.save()

            cartItem = CartItem.objects.filter(cart__user=order.user)
            if cartItem:
                cartItem.delete()

        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        return Response({"message": "OK"})

class DistanceView(APIView):

    def post(self, request):
        origin = request.data.get("origin")
        destination = request.data.get("destination")

        if not origin or not destination:
            return Response({"error": "Missing origin or destination"}, status=400)

        try:
            data = get_distance(origin, destination)

            return Response(data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)