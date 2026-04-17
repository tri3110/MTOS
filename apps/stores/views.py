
import json
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from apps.stores.models import StoreModel
from apps.stores.serializers import StoreSerializer
from apps.users.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated
from common.redis_client import redis_client

class StoreView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    CACHE_KEY = "stores:active"
    CACHE_TTL = 300 

    def get(self, request):
        try:
            cached = redis_client.get(self.CACHE_KEY)
            if cached:
                return Response(json.loads(cached))
            
            objs = StoreModel.objects.filter(is_active=True).only("id", "name", "address", "phone").order_by('-id')
            data = StoreSerializer(objs, many=True).data
            response = {"data": data}

            redis_client.set(self.CACHE_KEY, json.dumps(response), ex=self.CACHE_TTL)

            return Response(response)
        
        except Exception as e:
            return Response({'message': 'Server error'})
    
    def post(self, request):
        try:
            serializer = StoreSerializer(data=request.data)

            if serializer.is_valid():
                data = serializer.save(created_by=request.user)

                redis_client.delete(self.CACHE_KEY)

                return Response({
                    'data': StoreSerializer(data).data,
                    'message': "Store created successfully"
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({'message': 'Server error'})
        
    def put(self, request, id):
        try:
            with transaction.atomic():
                item = StoreModel.objects.select_for_update().get(id = id)
                serializer = StoreSerializer(item, data=request.data, partial=True)
                if serializer.is_valid():
                    itemUpdate = serializer.save(updated_by=request.user)

                    redis_client.delete(self.CACHE_KEY)

                    return Response({
                        'data': StoreSerializer(itemUpdate).data,
                        'message': "Store update successfully"
                    }, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except:
            return Response({'message': 'Update error'})
        
    def delete(self, request, id):
        try:
            with transaction.atomic():
                item = StoreModel.objects.select_for_update().get(id = id)
                item.is_active = False
                item.updated_by = request.user
                item.save()

                redis_client.delete(self.CACHE_KEY)

                return Response({
                    'message': "Store delete successfully"
                }, status=status.HTTP_201_CREATED)
                
        except:
            return Response({'message': 'Delete error'})
        
class StoreUserView(APIView):

    CACHE_KEY = "storesHome:active"
    CACHE_TTL = 300 

    def get(self, request):
        try:
            cached = redis_client.get(self.CACHE_KEY)
            if cached:
                return Response(json.loads(cached))
            
            objs = StoreModel.objects.filter(is_active=True).only("id", "name", "address", "phone")
            data = StoreSerializer(objs, many=True).data

            response = {"data": data}

            redis_client.set(self.CACHE_KEY, json.dumps(response), ex=self.CACHE_TTL)

            return Response(response)
        
        except Exception as e:
            return Response({'message': 'Server error'})
