
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from apps.stores.models import StoreModel
from apps.stores.serializers import StoreSerializer
from apps.users.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated

class StoreView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            objs = StoreModel.objects.filter(is_active=True).order_by('-id')
            data = StoreSerializer(objs, many=True).data

            return Response({
                "data": data,
            })
        except Exception as e:
            return Response({'message': 'Server error'})
    
    def post(self, request):
        try:
            serializer = StoreSerializer(data=request.data)

            if serializer.is_valid():
                data = serializer.save(created_by=request.user)
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

                return Response({
                    'message': "Store delete successfully"
                }, status=status.HTTP_201_CREATED)
                
        except:
            return Response({'message': 'Delete error'})
        
class StoreUserView(APIView):
    def get(self, request):
        try:
            objs = StoreModel.objects.filter(is_active=True)
            data = StoreSerializer(objs, many=True).data

            return Response({
                "data": data,
            })
        
        except Exception as e:
            return Response({'message': 'Server error'})
