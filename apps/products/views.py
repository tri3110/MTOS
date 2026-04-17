import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from apps.products.models import Category, Option, OptionGroup, Product, ProductOption, ProductTopping, Topping
from apps.products.serializers import CategorySerializer, OptionGroupSerializer, ProductCreateSerializer, ProductSerializer, ToppingBaseSerializer, ToppingSerializer
from apps.sliders.models import Slider
from apps.sliders.serializers import SliderSerializer
from apps.users.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q, Prefetch
from django.utils.text import slugify

class ProductView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.filter(category__status="active", status="active").order_by('-id')
        categories = Category.objects.all()

        option_groups = OptionGroup.objects.filter(status="active").prefetch_related("options").all()
        toppings = Topping.objects.filter(status='active').order_by('-id')

        product_data = ProductSerializer(products, many=True).data
        categorie_data = CategorySerializer(categories, many=True).data
        option_data = OptionGroupSerializer(option_groups, many=True).data
        topping_data = ToppingBaseSerializer(toppings, many=True).data

        return Response({
            "products": product_data,
            "categories": categorie_data,
            "options": option_data,
            "toppings": topping_data
        })
    
    def post(self, request):
        try:
            data = request.data.copy()
            data.pop("toppings", None)
            data.pop("options", None)
            serializer = ProductCreateSerializer(data=data)
            options = json.loads(request.data.get("options", "[]"))
            toppings = json.loads(request.data.get("toppings", "[]"))

            if serializer.is_valid():
                product = serializer.save(created_by=request.user)

                for option_id in options:
                    ProductOption.objects.create(
                        product=product,
                        option_id=option_id,
                        is_required=False
                    )

                for topping in toppings:
                    ProductTopping.objects.create(
                        product=product,
                        topping_id=topping["id"],
                        price=topping.get("price", 0),
                        max_quantity=topping.get("max_quantity", 3),
                        is_required=topping.get("is_required", False)
                    )

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
                product = Product.objects.select_for_update().get(id = id)

                data = request.data.copy()
                data.pop("toppings", None)
                data.pop("options", None)
                serializer = ProductSerializer(product, data=data, partial=True)
                options = json.loads(request.data.get("options", "[]"))
                toppings = json.loads(request.data.get("toppings", "[]"))

                if serializer.is_valid():
                    product = serializer.save(updated_by=request.user)

                    ProductOption.objects.filter(product=product).delete()
                    ProductTopping.objects.filter(product=product).delete()

                    for option_id in options:
                        ProductOption.objects.create(
                            product=product,
                            option_id=option_id,
                            is_required=False
                        )

                    for topping in toppings:
                        ProductTopping.objects.create(
                            product=product,
                            topping_id=topping["id"],
                            price=topping.get("price", 0),
                            max_quantity=topping.get("max_quantity", 3),
                            is_required=topping.get("is_required", False)
                        )

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
                product = Product.objects.select_for_update().get(id = id)
                product.status = "inactive"
                product.updated_by = request.user
                product.save()

                return Response({
                    'message': "Movie delete successfully"
                }, status=status.HTTP_201_CREATED)
                
        except:
            return Response({'message': 'Delete error'})

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
            products = Product.objects.filter(status="active").select_related("category").filter(category__status="active")
            if slug:
                products = products.filter(category__slug=slug)

            categories = Category.objects.filter(status="active")

            product_data = ProductSerializer(products, many=True).data
            categorie_data = CategorySerializer(categories, many=True).data

            return Response({
                "products": product_data,
                "categories": categorie_data,
            })
                
        except Exception as e:
            return Response({'message': str(e)}, status=400)

class HomeDataView(APIView):
    def get(self, request):
        products = (
            Product.objects
            .filter(status="active")
            .prefetch_related(
                Prefetch('product_toppings'),
                Prefetch(
                    'product_options',
                    queryset=ProductOption.objects.select_related('option__group')
                )
            )
            .order_by("-purchase_count")[:4]
        )

        sliders = Slider.objects.filter(is_active=True).order_by('order', '-id')
        
        return Response({
            "products": ProductSerializer(products, many=True).data,
            "sliders": SliderSerializer(sliders, many=True).data
        })

class CategoryView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = Category.objects.filter(status="active").order_by('-id')
        category_data = CategorySerializer(categories, many=True).data

        return Response({
            "data": category_data
        })

    def post(self, request):    
        try:
            data = request.data.copy()

            if not data.get("slug") and data.get("name"):
                base_slug = slugify(data["name"])
                slug = base_slug
                count = 1

                while Category.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{count}"
                    count += 1

                data["slug"] = slug

            serializer = CategorySerializer(data=data)

            if serializer.is_valid():
                category = serializer.save(created_by=request.user)

                return Response({
                    "category": CategorySerializer(category).data,
                    "message": "Category created successfully"
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'message': str(e)}, status=500)
        
    def put(self, request, id):
        try:
            with transaction.atomic():
                category = Category.objects.select_for_update().get(id=id)

                data = request.data.copy()

                if data.get("name") and not data.get("slug"):
                    base_slug = slugify(data["name"])
                    slug = base_slug
                    count = 1

                    while Category.objects.filter(slug=slug).exclude(id=category.id).exists():
                        slug = f"{base_slug}-{count}"
                        count += 1

                    data["slug"] = slug

                serializer = CategorySerializer(category, data=data, partial=True)

                if serializer.is_valid():
                    category = serializer.save(updated_by=request.user)

                    return Response({
                        "category": CategorySerializer(category).data,
                        "message": "Category updated successfully"
                    }, status=status.HTTP_200_OK)

                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Category.DoesNotExist:
            return Response({'message': 'Category not found'}, status=404)

        except Exception as e:
            return Response({'message': str(e)}, status=500)
        
    def delete(self, request, id):
        try:
            with transaction.atomic():
                category = Category.objects.select_for_update().get(id = id)
                category.status = "inactive"
                category.updated_by = request.user
                category.save()

                return Response({
                    'message': "Movie delete successfully"
                }, status=status.HTTP_201_CREATED)
                
        except:
            return Response({'message': 'Delete error'})

class CategoryUserView(APIView):

    def get(self, request):
        categories = Category.objects.filter(status="active").order_by('-id')
        category_data = CategorySerializer(categories, many=True).data

        return Response({
            "data": category_data
        })

class ToppingView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        toppings = Topping.objects.filter(status="active").order_by('-id')
        topping_data = ToppingBaseSerializer(toppings, many=True).data

        return Response({
            "data": topping_data
        })

    def post(self, request):
        try:
            serializer = ToppingBaseSerializer(data=request.data)

            if serializer.is_valid():
                topping = serializer.save(created_by=request.user)
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
                    return Response({
                        'topping': ToppingBaseSerializer(topping).data,
                        'message': "Topping update successfully"
                    }, status=status.HTTP_201_CREATED)
                
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except:
            return Response({'message': 'Update error'})
        
    def delete(self, request, id):
        try:
            with transaction.atomic():
                topping = Topping.objects.select_for_update().get(id = id)
                topping.status = "inactive"
                topping.updated_by = request.user
                topping.save()

                return Response({
                    'message': "Topping delete successfully"
                }, status=status.HTTP_201_CREATED)
                
        except:
            return Response({'message': 'Delete error'})

class OptionGroupView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        options = OptionGroup.objects.filter(status='active').order_by('-id')
        options_data = OptionGroupSerializer(options, many=True).data

        return Response({
            "data": options_data
        })

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

                return Response({
                    'message': "Option Group delete successfully"
                }, status=status.HTTP_201_CREATED)
                
        except:
            return Response({'message': 'Delete error'})

