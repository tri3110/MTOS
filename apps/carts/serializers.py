from rest_framework import serializers
from apps.carts.models import CartItem, CartItemOption, CartItemTopping
from apps.products.serializers import ProductSerializer

class CartItemToppingSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="topping.id")
    name = serializers.CharField(source="topping.name")

    class Meta:
        model = CartItemTopping
        fields = ["id", "name", "price", "quantity"]


class CartItemOptionSerializer(serializers.ModelSerializer):
    option_id = serializers.IntegerField(source="option.id")

    class Meta:
        model = CartItemOption
        fields = ["option_id"]


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    toppings = CartItemToppingSerializer(many=True)
    options = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "quantity",
            "price_snapshot",
            "options",
            "toppings",
        ]

    def get_options(self, obj):
        result = {}
        for opt in obj.options.all():
            group_id = opt.option.group_id
            result[group_id] = opt.option.id
        return result