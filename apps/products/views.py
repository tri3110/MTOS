from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from apps.products.models import Category, Product
from apps.products.serializers import CategorySerializer, ProductSerializer
from apps.users.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.postgres.search import SearchVector, SearchQuery, TrigramSimilarity
from django.db.models import Q

class ProductView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.filter(category__status="active", status="active").order_by('-id')
        categories = Category.objects.all()

        product_data = ProductSerializer(products, many=True).data
        category_data = CategorySerializer(categories, many=True).data

        return Response({
            "products": product_data,
            "categories": category_data
        })
    

    def post(self, request):
        try:
            serializer = ProductSerializer(data=request.data)
            if serializer.is_valid():
                product = serializer.save(created_by=request.user)
                return Response({
                    'product': ProductSerializer(product).data,
                    'message': "Product created successfully"
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except:
            return Response({'message': 'Product error'})
        
    def put(self, request, id):
        try:
            with transaction.atomic():
                product = Product.objects.select_for_update().get(id = id)
                serializer = ProductSerializer(product, data=request.data, partial=True)
                if serializer.is_valid():
                    product = serializer.save(updated_by=request.user)
                    return Response({
                        'product': ProductSerializer(product).data,
                        'message': "Product update successfully"
                    }, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except:
            return Response({'message': 'Update error'})
        
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
            serializer = CategorySerializer(data=request.data)

            if serializer.is_valid():
                category = serializer.save(created_by=request.user)
                return Response({
                    'category': CategorySerializer(category).data,
                    'message': "Category created successfully"
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({'message': 'Product error'})
        
    def put(self, request, id):
        try:
            with transaction.atomic():
                category = Category.objects.select_for_update().get(id = id)
                serializer = CategorySerializer(category, data=request.data, partial=True)
                if serializer.is_valid():
                    category = serializer.save(updated_by=request.user)
                    return Response({
                        'category': CategorySerializer(category).data,
                        'message': "Category update successfully"
                    }, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except:
            return Response({'message': 'Update error'})
        
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
