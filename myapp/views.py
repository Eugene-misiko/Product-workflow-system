from django.shortcuts import render
from .serializers import BookSerializer
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from .models import Book
#Create your views here.
class BookView(APIView):

    def get(self, request, *args, **kwargs):
        result = Book.objects.all()
        serializers = BookSerializer(result, many=True)
        return Response({'status': 'success', "books": serializers.data}, status=200)
    
    def post(self, request):
        serializer = BookSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data":serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"status": "error", "data":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    def put(self, request, *args, **kwargs):
        try:
            book = Book.objects.get(id=kwargs['id'])
        except Book.DoesNotExist:
            return Response({"status" : "error", "data": "Book not found"}, status=status.HTTP_404_NOT_FOUND)    
        serializer = BookSerializer(book, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status" : "success", "data" : serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"status":"error", "data": serializer.errors}, status=status.HTTP_404_NOT_FOUND)
        
    def delete(self, request, *args, **kwargs):
        try:
            book = Book.objects.get(id=kwargs['id'])
        except Book.DoesNotExist:
            return Response({"status" : "error", "data": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        book.delete()
        return Response({"status": "success", "data": "Book deleted successfully"}, status=status.HTTP_200_OK)      

 

        