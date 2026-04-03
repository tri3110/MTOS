from rest_framework import serializers
from apps.products.models import Category, Product

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "status"]
        read_only_fields = ["id"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = Product

        fields = [
            "id",
            "name",
            "image",
            "price",
            "status",
            "purchase_count",
            "category",
            "category_id",
        ]