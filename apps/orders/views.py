from rest_framework.views import APIView
from rest_framework.response import Response
from apps.users.authentication import CookieJWTAuthentication
from apps.orders.models import Order
from common.permissions import IsAdminOrReadOnly
from .serializers import OrderSerializer

class OrderDetailView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, id):
        try:
            order = (
                Order.objects
                .select_related("user", "store", "voucher")
                .prefetch_related(
                    "items__product",
                    "items__toppings__topping"
                )
                .filter(id=id, user=request.user)
                .first()
            )

            if not order:
                return Response({"error": "Order not found"}, status=404)

            serializer = OrderSerializer(order)

            return Response(serializer.data)

        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

ALLOWED_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["preparing", "cancelled"],
    "preparing": ["delivering"],
    "delivering": ["completed"],
    "completed": [],
    "cancelled": [],
}

class AdminOrderView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        orders = Order.objects.select_related(
            'store', 'voucher', 'user'
        ).prefetch_related(
            'items__product',
            'items__toppings__topping'
        ).order_by('-created_at')

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    
    def post(self, request, id):
        new_status = request.data.get("status")

        order = Order.objects.only("id", "status").filter(id=id).first()

        if not order:
            return Response({"error": "Order not found"}, status=404)

        allowed = ALLOWED_TRANSITIONS.get(order.status, [])

        if new_status not in allowed:
            return Response({
                "error": f"Cannot change from {order.status} to {new_status}"
            }, status=400)

        Order.objects.filter(id=id).update(status=new_status)

        return Response({"message": "Status updated"})
    
    def delete(self, request, id):
        updated = Order.objects.filter(id=id).update(is_deleted=True)

        if not updated:
            return Response({"error": "Not found"}, status=404)

        return Response({"message": "Order cancelled"})