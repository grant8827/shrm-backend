"""
Audit app serializers
"""
from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit log entries."""
    
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'user',
            'username',
            'user_email',
            'action',
            'resource_type',
            'resource_id',
            'details',
            'ip_address',
            'user_agent',
            'timestamp',
        ]
        read_only_fields = ['id', 'timestamp', 'username', 'user_email']
