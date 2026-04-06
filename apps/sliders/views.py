from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from apps.sliders.models import Slider
from apps.sliders.serializers import SliderSerializer
from apps.users.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db.models import Max

class SliderView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sliders = Slider.objects.filter(is_active=True).order_by('order', '-id')

        slider_data = SliderSerializer(sliders, many=True).data

        return Response({
            "data": slider_data,
        })
    

    def post(self, request):
        try:
            max_order = Slider.objects.aggregate(max=Max('order'))['max'] or 0
            data = request.data.copy()
            data['order'] = max_order + 20
            serializer = SliderSerializer(data=data)
            if serializer.is_valid():
                slider = serializer.save(created_by=request.user)
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

                return Response({
                    'message': "Slider delete successfully"
                }, status=status.HTTP_201_CREATED)
                
        except:
            return Response({'message': 'Delete error'})
        
class SliderHomeView(APIView):
    
    def get(self, request):
        sliders = Slider.objects.filter(is_active=True).order_by('order', '-id')
        slider_data = SliderSerializer(sliders, many=True).data
        return Response({
            "data": slider_data,
        })
