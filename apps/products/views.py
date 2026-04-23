import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction, IntegrityError
from apps.orders.models import OrderItem
from apps.products.models import Category, Option, OptionGroup, Product, ProductOption, ProductTopping, Topping
from apps.products.serializers import CategorySerializer, OptionGroupSerializer, ProductCreateSerializer, ProductSerializer, ToppingBaseSerializer, ToppingSerializer
from apps.sliders.models import Slider
from apps.sliders.serializers import SliderSerializer
from apps.users.authentication import CookieJWTAuthentication
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q, Prefetch
from django.utils.text import slugify
from apps.users.models import User
from common.constants import CategoryCache, HomeCache, OptionGroupCache, ProductCache, ToppingCache
from common.permissions import IsAdminOrReadOnly
from common.redis_client import redis_client

class ProductView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        cache = ProductCache.FULL_DATA
        cached = redis_client.get(cache.key)

        if cached:
            return Response(json.loads(cached))

        products = (
            Product.objects
            .select_related("category")
            .prefetch_related(
                "product_options__option__group",
                "product_toppings__topping"
            )
            .filter(category__status="active", status="active")
            .order_by("-id")
        )

        categories = Category.objects.only("id", "name", "status")

        option_groups = (
            OptionGroup.objects
            .filter(status="active")
            .prefetch_related("options")
        )

        toppings = Topping.objects.filter(status="active").only("id", "name")

        response_data = {
            "products": ProductSerializer(products, many=True).data,
            "categories": CategorySerializer(categories, many=True).data,
            "options": OptionGroupSerializer(option_groups, many=True).data,
            "toppings": ToppingBaseSerializer(toppings, many=True).data
        }

        redis_client.set(
            cache.key, 
            json.dumps(response_data, default=str), 
            ex=cache.ttl
        )

        return Response(response_data)
    
    def post(self, request):
        try:
            data = request.data.copy()
            data.pop("toppings", None)
            data.pop("options", None)
            serializer = ProductCreateSerializer(data=data)

            options = json.loads(request.data.get("options", "[]"))
            toppings = json.loads(request.data.get("toppings", "[]"))

            if serializer.is_valid():
                with transaction.atomic():
                    product = serializer.save(created_by=request.user)

                    ProductOption.objects.bulk_create([
                        ProductOption(
                            product=product,
                            option_id=option_id,
                            is_required=False
                        )
                        for option_id in options
                    ])

                    ProductTopping.objects.bulk_create([
                        ProductTopping(
                            product=product,
                            topping_id=t["id"],
                            price=t.get("price", 0),
                            max_quantity=t.get("max_quantity", 3),
                            is_required=t.get("is_required", False)
                        )
                        for t in toppings
                    ])

                    redis_client.delete(ProductCache.FULL_DATA.key)

                    return Response({
                        'product': ProductSerializer(product).data,
                        'message': "Product created successfully"
                    }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({'message': str(e)}, status=400)
        
    def put(self, request, id):
        try:
            with transaction.atomic():
                product = (
                    Product.objects
                    .select_for_update()
                    .filter(id=id)
                    .first()
                )

                if not product:
                    return Response({"message": "Not found"}, status=404)

                data = request.data.copy()
                data.pop("toppings", None)
                data.pop("options", None)
                serializer = ProductSerializer(product, data=data, partial=True)
                options = json.loads(request.data.get("options", "[]"))
                toppings = json.loads(request.data.get("toppings", "[]"))

                if serializer.is_valid(raise_exception=True):
                    product = serializer.save(updated_by=request.user)

                    ProductOption.objects.filter(product=product).delete()
                    ProductTopping.objects.filter(product=product).delete()

                    ProductOption.objects.bulk_create([
                        ProductOption(
                            product=product,
                            option_id=option_id,
                            is_required=False
                        )
                        for option_id in options
                    ])

                    ProductTopping.objects.bulk_create([
                        ProductTopping(
                            product=product,
                            topping_id=t["id"],
                            price=t.get("price", 0),
                            max_quantity=t.get("max_quantity", 3),
                            is_required=t.get("is_required", False)
                        )
                        for t in toppings
                    ])

                    redis_client.delete(ProductCache.FULL_DATA.key)

                    return Response({
                        'product': ProductSerializer(product).data,
                        'message': "Product updated successfully"
                    }, status=status.HTTP_200_OK)

                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({'message': str(e)}, status=400)
        
    def delete(self, request, id):
        try:
            with transaction.atomic():
                product = (
                    Product.objects
                    .select_for_update()
                    .filter(id=id)
                    .first()
                )

                if not product:
                    return Response({"message": "Not found"}, status=404)

                product.status = "inactive"
                product.updated_by = request.user
                product.save()

                redis_client.delete(ProductCache.FULL_DATA.key)

                return Response({
                    "message": "Product deleted successfully"
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": str(e)}, status=400)

class ProductSearchView(APIView):
    def get(self, request):
        keyword = request.GET.get("q", "").strip()

        products = Product.objects.filter(
            status="active",
            category__status="active"
        )

        if keyword:
            products = products.annotate(
                similarity=TrigramSimilarity('name', keyword)
            ).filter(Q(name__icontains=keyword) | Q(similarity__gt=0.1)
            ).order_by('-similarity')

        products = products.order_by('-purchase_count')[:20]

        return Response(ProductSerializer(products, many=True).data)
    
class ProductMenuView(APIView):

    def get(self, request, slug=None):
        try:
            cache_key = f"menu:{slug or 'all'}"
            cached = redis_client.get(cache_key)
            if cached:
                return Response(json.loads(cached))
            
            products = Product.objects.filter(status="active", category__status="active").select_related("category")
            if slug:
                products = products.filter(category__slug=slug)

            categories = Category.objects.filter(status="active")

            product_data = ProductSerializer(products, many=True).data
            categorie_data = CategorySerializer(categories, many=True).data

            response_data = {
                "products": product_data,
                "categories": categorie_data,
            }
            redis_client.set(cache_key, json.dumps(response_data, default=str), ex=300)

            return Response(response_data)
                
        except Exception as e:
            return Response({'message': str(e)}, status=400)

class HomeDataView(APIView):

    def get(self, request):
        cache_key = HomeCache.ACTIVE.key
        cached = redis_client.get(cache_key)

        if cached:
            return Response(json.loads(cached))

        products = (
            Product.objects
            .select_related("category")
            .prefetch_related(
                Prefetch(
                    "product_toppings",
                    queryset=ProductTopping.objects.select_related("topping")
                ),
                Prefetch(
                    "product_options",
                    queryset=ProductOption.objects.select_related("option__group")
                )
            )
            .filter(status="active", category__status="active")
            .only("id", "name", "price", "purchase_count", "category_id")
            .order_by("-purchase_count")[:5]
        )

        sliders = (
            Slider.objects
            .filter(is_active=True)
            .only("id", "image", "order")
            .order_by("order", "-id")
        )

        total_customers = User.objects.filter(role=User.Role.CUSTOMER).count()

        total_drinks = OrderItem.objects.filter(order__status="completed").count()

        response_data = {
            "products": ProductSerializer(products, many=True).data,
            "sliders": SliderSerializer(sliders, many=True).data,
            "total_customers": total_customers,
            "total_drinks": total_drinks
        }

        redis_client.set(
            cache_key,
            json.dumps(response_data, default=str),
            ex=HomeCache.ACTIVE.ttl
        )

        return Response(response_data)

class CategoryView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        cache = CategoryCache.FULL_DATA
        cached = redis_client.get(cache.key)

        if cached:
            return Response(json.loads(cached))

        categories = (
            Category.objects
            .filter(status="active")
            .only("id", "name", "slug", "status")
            .order_by("-id")
        )

        response_data = {
            "data": CategorySerializer(categories, many=True).data
        }

        redis_client.set(
            cache.key,
            json.dumps(response_data),
            ex=cache.ttl
        )

        return Response(response_data)

    def post(self, request):
        try:
            data = request.data.copy()

            if not data.get("slug") and data.get("name"):
                base_slug = slugify(data["name"])
                slug = base_slug
                count = 1

                with transaction.atomic():
                    while True:
                        try:
                            data["slug"] = slug

                            serializer = CategorySerializer(data=data)
                            serializer.is_valid(raise_exception=True)

                            category = serializer.save(created_by=request.user)
                            break

                        except IntegrityError:
                            slug = f"{base_slug}-{count}"
                            count += 1

            else:
                serializer = CategorySerializer(data=data)
                serializer.is_valid(raise_exception=True)

                with transaction.atomic():
                    category = serializer.save(created_by=request.user)

            redis_client.delete(CategoryCache.FULL_DATA.key)

            return Response({
                "category": CategorySerializer(category).data,
                "message": "Category created successfully"
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"message": str(e)}, status=400)
        
    def put(self, request, id):
        try:
            with transaction.atomic():
                category = (
                    Category.objects
                    .select_for_update()
                    .filter(id=id)
                    .first()
                )

                if not category:
                    return Response({"message": "Category not found"}, status=404)

                data = request.data.copy()

                if data.get("name") and not data.get("slug"):
                    base_slug = slugify(data["name"])
                    slug = base_slug
                    count = 1

                    while True:
                        try:
                            data["slug"] = slug

                            serializer = CategorySerializer(category, data=data, partial=True)
                            serializer.is_valid(raise_exception=True)

                            category = serializer.save(updated_by=request.user)
                            break

                        except IntegrityError:
                            slug = f"{base_slug}-{count}"
                            count += 1
                else:
                    serializer = CategorySerializer(category, data=data, partial=True)
                    serializer.is_valid(raise_exception=True)

                    category = serializer.save(updated_by=request.user)

            redis_client.delete(CategoryCache.FULL_DATA.key)

            return Response({
                "category": CategorySerializer(category).data,
                "message": "Category updated successfully"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": str(e)}, status=400)
        
    def delete(self, request, id):
        try:
            with transaction.atomic():
                category = Category.objects.select_for_update().get(id = id)
                category.status = "inactive"
                category.updated_by = request.user
                category.save()

                redis_client.delete(CategoryCache.FULL_DATA.key)

                return Response({
                    'message': "Category delete successfully"
                }, status=status.HTTP_201_CREATED)
                
        except:
            return Response({'message': 'Delete error'})

class CategoryUserView(APIView):

    def get(self, request):
        cache = CategoryCache.FULL_DATA
        cached = redis_client.get(cache.key)

        if cached:
            return Response(json.loads(cached))

        categories = (
            Category.objects
            .filter(status="active")
            .only("id", "name", "slug", "status")
            .order_by("-id")
        )

        response_data = {
            "data": CategorySerializer(categories, many=True).data
        }

        redis_client.set(
            cache.key,
            json.dumps(response_data),
            ex=cache.ttl
        )

        return Response(response_data)

class ToppingView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        cache = ToppingCache.ACTIVE
        cached = redis_client.get(cache.key)
        if cached:
            return Response(json.loads(cached))

        toppings = Topping.objects.filter(status="active").order_by('-id')
        topping_data = ToppingBaseSerializer(toppings, many=True).data

        reponse_data = {"data": topping_data}
        redis_client.set(cache.key, json.dumps(reponse_data), ex=cache.ttl)

        return Response(reponse_data)

    def post(self, request):
        try:
            serializer = ToppingBaseSerializer(data=request.data)

            if serializer.is_valid():
                topping = serializer.save(created_by=request.user)

                redis_client.delete(ToppingCache.ACTIVE.key)

                return Response({
                    'topping': ToppingBaseSerializer(topping).data,
                    'message': "Topping created successfully"
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({'message': 'Product error'})
        
    def put(self, request, id):
        try:
            with transaction.atomic():
                topping = Topping.objects.select_for_update().get(id = id)
                serializer = ToppingBaseSerializer(topping, data=request.data, partial=True)
                if serializer.is_valid():
                    topping = serializer.save(updated_by=request.user)

                    redis_client.delete(ToppingCache.ACTIVE.key)

                    return Response({
                        'topping': ToppingBaseSerializer(topping).data,
                        'message': "Topping update successfully"
                    }, status=status.HTTP_201_CREATED)
                
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({'message': 'Update error'})
        
    def delete(self, request, id):
        try:
            with transaction.atomic():
                topping = Topping.objects.select_for_update().get(id = id)
                topping.status = "inactive"
                topping.updated_by = request.user
                topping.save()

                redis_client.delete(ToppingCache.ACTIVE.key)

                return Response({
                    'message': "Topping delete successfully"
                }, status=status.HTTP_201_CREATED)
                
        except:
            return Response({'message': 'Delete error'})

class OptionGroupView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        cache = OptionGroupCache.ACTIVE
        cached = redis_client.get(cache.key)
        if cached:
            return Response(json.loads(cached))
        
        options = OptionGroup.objects.filter(status='active').order_by('-id')
        options_data = OptionGroupSerializer(options, many=True).data

        reponse_data = {"options": options_data}
        redis_client.set(cache.key, json.dumps(reponse_data), ex=cache.ttl)

        return Response(reponse_data)

    def post(self, request):
        try:
            serializer = OptionGroupSerializer(data=request.data)
            options_data = request.data.pop('options', [])

            if serializer.is_valid():
                option = serializer.save(created_by=request.user)
                for opt in options_data:
                    Option.objects.create(
                        group=option,
                        name=opt['name'],
                        price=opt.get('price', 0)
                    )

                redis_client.delete(OptionGroupCache.ACTIVE.key)
                return Response({
                    'option': OptionGroupSerializer(option).data,
                    'message': "Option Group created successfully"
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({'message': 'Product error'})
        
    def delete(self, request, id):
        try:
            with transaction.atomic():
                option = OptionGroup.objects.select_for_update().get(id = id)
                option.status = "inactive"
                option.updated_by = request.user
                option.save()

                redis_client.delete(OptionGroupCache.ACTIVE.key)

                return Response({
                    'message': "Option Group delete successfully"
                }, status=status.HTTP_201_CREATED)
                
        except:
            return Response({'message': 'Delete error'})

