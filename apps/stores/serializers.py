from rest_framework import serializers
from apps.stores.models import StoreModel

class StoreSerializer(serializers.ModelSerializer):

    class Meta:
        model = StoreModel
        fields = [
            "id",
            "name",
            "address",
            "phone",
        ]