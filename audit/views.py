"""
Audit app views for logging system events (HIPAA compliance)
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import AuditLog
from .serializers import AuditLogSerializer
import logging

logger = logging.getLogger('audit')


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs (admin only).
    Read-only to prevent modification of audit records.
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filterset_fields = ['user', 'action', 'resource_type']
    search_fields = ['action', 'resource_type', 'details']
    ordering_fields = ['timestamp', 'action']


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_audit_log_batch(request):
    """
    Create multiple audit log entries at once.
    This endpoint is called by the frontend to batch audit logs.
    """
    try:
        logs_data = request.data if isinstance(request.data, list) else [request.data]
        created_logs = []
        
        for log_data in logs_data:
            # Extract fields from frontend format
            audit_log = AuditLog.objects.create(
                user=request.user,
                action=log_data.get('action', 'unknown'),
                resource_type=log_data.get('resourceType'),
                resource_id=log_data.get('resourceId'),
                details=log_data.get('details', {}),
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            created_logs.append(audit_log)
            
            # Log to audit file
            logger.info(
                f"Audit: {audit_log.action} by {audit_log.user} "
                f"on {audit_log.resource_type} {audit_log.resource_id}"
            )
        
        serializer = AuditLogSerializer(created_logs, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Failed to create audit log: {str(e)}")
        return Response(
            {'error': 'Failed to create audit log'},
            status=status.HTTP_400_BAD_REQUEST
        )


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
