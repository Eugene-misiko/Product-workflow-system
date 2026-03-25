from django.shortcuts import render
from rest_framework import generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Conversation, Message
from .serializers import (
    MessageSerializer, ConversationSerializer,
    CreateMessageSerializer, StartConversationSerializer
)
# Create your views here.
class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer
    
    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).order_by('-last_message_at')


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    
    def get_queryset(self):
        return Message.objects.filter(
            conversation__participants=self.request.user
        ).order_by('-created_at')


class ConversationMessagesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    
    def get_queryset(self):
        conversation = get_object_or_404(
            Conversation,
            pk=self.kwargs['pk'],
            participants=self.request.user
        )
        return Message.objects.filter(conversation=conversation).order_by('created_at')
class StartConversationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = StartConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        recipient_id = serializer.validated_data['recipient_id']
        order_id = serializer.validated_data.get('order_id')
        message_content = serializer.validated_data['message']
        
        # Check for existing conversation
        existing = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants__id=recipient_id
        ).filter(
            order_id=order_id if order_id else None
        ).first()
        
        if existing:
            msg = Message.objects.create(
                conversation=existing,
                sender=request.user,
                content=message_content
            )
            existing.last_message = message_content
            existing.last_message_at = timezone.now()
            existing.last_message_by = request.user
            existing.save()
            
            return Response({
                'conversation': ConversationSerializer(existing).data,
                'message': MessageSerializer(msg).data
            })
        
        # Create new conversation
        conversation = Conversation.objects.create(
            company=request.user.company,
            order_id=order_id
        )
        conversation.participants.add(request.user)
        conversation.participants.add(recipient_id)
        
        msg = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_content
        )
        conversation.last_message = message_content
        conversation.last_message_at = timezone.now()
        conversation.last_message_by = request.user
        conversation.save()
        return Response({
            'conversation': ConversationSerializer(conversation).data,
            'message': MessageSerializer(msg).data
        }, status=201)

class SetTypingStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        return Response({'status': 'ok'})


class UnreadConversationsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer
    
    def get_queryset(self):
        # Return conversations with unread messages
        return Conversation.objects.filter(
            participants=self.request.user
        ).exclude(
            messages__read_by=self.request.user
        ).distinct()

