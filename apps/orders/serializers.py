
from rest_framework import serializers
from apps.orders.models import Order, OrderItem, OrderItemTopping

class OrderItemToppingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItemTopping
        fields = ["id", "topping", "price", "quantity"]
        
class OrderItemSerializer(serializers.ModelSerializer):
    toppings = OrderItemToppingSerializer(many=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "price", "quantity", "toppings"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'store',
            'voucher',
            'customer_name',
            'total_price',
            'earned_points',
            'status',
            'payment_method',
            'idempotency_key',
            'payment_url',
            'qr_code',
            'created_at',
            'items',
        ]
        read_only_fields = ['total_price', 'status', 'created_at']

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance