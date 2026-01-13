from rest_framework import serializers
from .models import Message, MessageThread, MessageAttachment
from users.serializers import UserSerializer

class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = ['id', 'file_name', 'file_size', 'mime_type', 'uploaded_at']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    content = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'priority', 'is_read', 'is_starred', 
                 'created_at', 'read_at', 'attachments']
    
    def get_content(self, obj):
        """Return decrypted message content"""
        return obj.content  # Uses the @property which decrypts

class MessageThreadSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = MessageThread
        fields = ['id', 'subject', 'participants', 'last_message', 'unread_count', 
                 'is_archived', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        last_message = obj.messages.first()
        if last_message:
            return MessageSerializer(last_message).data
        return None

    def get_unread_count(self, obj):
        user = self.context['request'].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()

class CreateMessageSerializer(serializers.ModelSerializer):
    recipient_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True)
    content = serializers.CharField(write_only=True)

    class Meta:
        model = Message
        fields = ['recipient_ids', 'content', 'priority']