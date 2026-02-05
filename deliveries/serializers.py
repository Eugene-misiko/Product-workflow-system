from rest_framework import serializers
from .models import Delivery

class DeliverySerializer(serializers.ModelSerializer):
    """
    Delivery note serializer.
    """
    class Meta:
        model = Delivery
        fields = "__all__"
