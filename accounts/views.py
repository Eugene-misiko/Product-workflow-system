from django.shortcuts import render
from rest_framework import generics
from .models import User, Role
from .serializers import RegisterSerializer
# Create your views here.
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        client_role = Role.objects.get(name=Role.CLIENT)
        serializer.save(role=client_role)
