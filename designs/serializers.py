from rest_framework import serializers
from .models import Design, DesignRequest

class DesignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Design
        fields = "__all__"

class DesignRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignRequest
        fields = "__all__"
