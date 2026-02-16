from rest_framework import serializers
from .models import MpesaRequest, MpesaResponse

class MpesaRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaRequest
        fields = "__all__"

class MpesaResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaResponse
        fields = "__all__"

