from rest_framework import serializers
from apps.sliders.models import Slider

class SliderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Slider
        fields = [
            "id",
            "title",
            "image",
            "link",
            "order",
        ]