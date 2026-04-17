from rest_framework import serializers
from apps.products.models import Category, Option, OptionGroup, Product, ProductTopping, Topping

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "status", "slug"]
        read_only_fields = ["id"]

class ToppingSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='topping.id')
    name = serializers.CharField(source='topping.name')
    image = serializers.ImageField(source='topping.image')

    class Meta:
        model = ProductTopping
        fields = ['id', 'name', 'price', 'image', 'max_quantity', 'is_required']

class ToppingBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topping
        fields = ['id', 'name', 'image', 'price']

class ProductCreateSerializer(serializers.ModelSerializer):
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

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )

    toppings = ToppingSerializer(
        source='product_toppings',
        many=True
    )

    option_groups = serializers.SerializerMethodField()

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
            "toppings",
            "option_groups"
        ]

    def get_toppings(self, obj):
        toppings = obj.product_toppings.filter(status='active')

        return ToppingSerializer(toppings, many=True).data

    def get_option_groups(self, obj):
        groups = {}

        for po in obj.product_options.all():
            opt = po.option
            group = opt.group

            if not group or group.status != "active":
                continue

            if group.id not in groups:
                groups[group.id] = {
                    "id": group.id,
                    "name": group.name,
                    "options": []
                }

            groups[group.id]["options"].append({
                "id": opt.id,
                "name": opt.name,
                "price": opt.price,
                "is_required": po.is_required
            })

        return sorted(groups.values(), key=lambda x: x["id"])

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'name', 'price']
    
class OptionGroupSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = OptionGroup
        fields = ["id", "name", "options"]

    def get_options(self, obj):
        return OptionSerializer(obj.options.all(), many=True).data