from rest_framework import serializers
from .models import MpesaRequest, MpesaResponse

class MpesaRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaRequest
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["amount"] = str(instance.amount)
        return data

class MpesaResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaResponse
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data