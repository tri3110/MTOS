import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from apps.sliders.models import Slider
from apps.sliders.serializers import SliderSerializer
from apps.users.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db.models import Max
from common.redis_client import redis_client

class SliderView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    CACHE_KEY = "sliders:active"
    CACHE_TTL = 300 

    def get(self, request):
        cached = redis_client.get(self.CACHE_KEY)
        if cached:
            return Response(json.loads(cached))
        
        sliders = (
            Slider.objects.filter(is_active=True)
            .only("id", "title", "image", "link", "order", "is_active")
            .order_by('order', '-id')
        )

        data = SliderSerializer(sliders, many=True).data
        response = {"data": data}

        redis_client.set(self.CACHE_KEY, json.dumps(response), ex=self.CACHE_TTL)

        return Response(response)
    

    def post(self, request):
        try:
            max_order = Slider.objects.aggregate(max=Max('order'))['max'] or 0
            data = request.data.copy()
            data['order'] = max_order + 20
            serializer = SliderSerializer(data=data)

            if serializer.is_valid():
                slider = serializer.save(created_by=request.user)

                redis_client.delete(self.CACHE_KEY)
                return Response({
                    'slider': SliderSerializer(slider).data,
                    'message': "Slider created successfully"
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except:
            return Response({'message': 'Slider error'})
        
    def put(self, request, id):
        try:
            with transaction.atomic():
                slider = Slider.objects.select_for_update().get(id = id)
                serializer = SliderSerializer(slider, data=request.data, partial=True)
                if serializer.is_valid():
                    slider = serializer.save(updated_by=request.user)
                    
                    redis_client.delete(self.CACHE_KEY)
                    return Response({
                        'slider': SliderSerializer(slider).data,
                        'message': "Slider update successfully"
                    }, status=status.HTTP_201_CREATED)
                
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except:
            return Response({'message': 'Update error'})
        
    def delete(self, request, id):
        try:
            with transaction.atomic():
                slider = Slider.objects.select_for_update().get(id = id)
                slider.is_active = False
                slider.updated_by = request.user
                slider.save()

                redis_client.delete(self.CACHE_KEY)

                return Response({
                    'message': "Slider delete successfully"
                }, status=status.HTTP_201_CREATED)
                
        except:
            return Response({'message': 'Delete error'})
        
class SliderHomeView(APIView):

    CACHE_KEY = "slidersHome:active"
    CACHE_TTL = 300 

    def get(self, request):
        cached = redis_client.get(self.CACHE_KEY)
        if cached:
            return Response(json.loads(cached))
        
        sliders = Slider.objects.filter(is_active=True).order_by('order', '-id')
        slider_data = SliderSerializer(sliders, many=True).data

        response = {"data": slider_data}

        redis_client.set(self.CACHE_KEY, json.dumps(response), ex=self.CACHE_TTL)

        return Response(response)
