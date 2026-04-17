from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.users.authentication import CookieJWTAuthentication
from apps.orders.models import Order
from .serializers import OrderSerializer
from rest_framework import status

class OrderDetailView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            order = Order.objects.prefetch_related(
                "items__toppings"
            ).get(id=id, user=request.user)

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
    permission_classes = [IsAuthenticated]

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

        order = Order.objects.filter(id=id).first()

        if not order:
            return Response({"error": "Order not found"}, status=404)

        allowed = ALLOWED_TRANSITIONS.get(order.status, [])

        if new_status not in allowed:
            return Response({
                "error": f"Cannot change from {order.status} to {new_status}"
            }, status=400)

        order.status = new_status
        order.save()

        return Response({"message": "Status updated"})
    
    def delete(self, request, id):
        order = Order.objects.filter(id=id).first()

        if not order:
            return Response({"error": "Not found"}, status=404)

        order.is_deleted = True
        order.save()

        return Response({"message": "Order cancelled"})