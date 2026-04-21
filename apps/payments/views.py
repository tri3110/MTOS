import uuid

from apps.carts.models import Cart, CartItem
from apps.orders.models import Order, OrderItem, OrderItemTopping
from apps.users.authentication import CookieJWTAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from common.permissions import IsAdminOrReadOnly
from common.redis_client import redis_client
from common.kafka_producer import send_order_created

class PaymentView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAdminOrReadOnly]

    def post(self, request):
        try:
            with transaction.atomic():

                user = request.user

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
                    cart_items = cart.items.prefetch_related("options", "toppings")

                    if not cart_items:
                        return Response({"error": "Cart is empty"}, status=400)

                    order = Order.objects.create(
                        user=user,
                        customer_name=user.full_name or user.email,
                        idempotency_key=str(uuid.uuid4()),
                        total_price=0,
                        status="PENDING"
                    )

                    total = 0

                    for item in cart_items:
                        order_item = OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            quantity=item.quantity,
                            price=item.product.price
                        )

                        total += item.product.price * item.quantity

                        for item_topping in item.toppings.all():
                            OrderItemTopping.objects.create(
                                order_item=order_item,
                                topping=item_topping.topping,
                                price=item_topping.price,
                                quantity=item_topping.quantity
                            )
                            total += item_topping.price * item_topping.quantity

                    order.total_price = total
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