from rest_framework import serializers
from .models import Conversation, Message
class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    is_mine = serializers.SerializerMethodField()
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'sender_name', 'content', 'attachments',
            'is_edited', 'is_deleted', 'created_at', 'is_mine'
        ]
        read_only_fields = ['id', 'sender', 'created_at']
    
    def get_is_mine(self, obj):
        request = self.context.get('request')
        return request and obj.sender == request.user

class ConversationSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()
    last_message_sender = serializers.CharField(source='last_message_by.get_full_name', read_only=True)
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'participants', 'title', 'order',
            'last_message', 'last_message_at', 'last_message_sender',
            'created_at', 'updated_at'
        ]
    
    def get_participants(self, obj):
        return [
            {'id': p.id, 'name': p.get_full_name(), 'role': p.role}
            for p in obj.participants.all()
        ]

class CreateMessageSerializer(serializers.Serializer):
    content = serializers.CharField()
    attachments = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        allow_empty=True
    )


class StartConversationSerializer(serializers.Serializer):
    recipient_id = serializers.IntegerField()
    order_id = serializers.IntegerField(required=False)
    message = serializers.CharField()