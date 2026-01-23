"""
Views for SOAP Notes
"""
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from .models import SOAPNote
from .serializers import SOAPNoteSerializer, SOAPNoteCreateSerializer


class SOAPNotePermission(permissions.BasePermission):
    """
    Custom permission for SOAP Notes:
    - Therapists can view/edit their own notes
    - Admins and staff can view/edit all notes
    - Patients can only view their own notes (read-only)
    """
    def has_permission(self, request, view):
        # Authenticated users only
        if not request.user.is_authenticated:
            return False
        
        # All authenticated users can list/retrieve
        if view.action in ['list', 'retrieve']:
            return True
        
        # Only therapists, admins, and staff can create/update/delete
        if view.action in ['create', 'update', 'partial_update', 'destroy', 'finalize']:
            return request.user.role in ['therapist', 'admin', 'staff']
        
        return True
    
    def has_object_permission(self, request, view, obj):
        # Admins and staff have full access
        if request.user.role in ['admin', 'staff']:
            return True
        
        # Therapists can view/edit their own notes
        if request.user.role == 'therapist':
            return obj.therapist == request.user
        
        # Patients can only view their own notes
        if request.user.role == 'client':
            return request.method in permissions.SAFE_METHODS and obj.patient == request.user
        
        return False


class SOAPNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SOAP Notes
    """
    queryset = SOAPNote.objects.all()
    permission_classes = [SOAPNotePermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['chief_complaint', 'patient__first_name', 'patient__last_name', 
                     'therapist__first_name', 'therapist__last_name']
    ordering_fields = ['session_date', 'created_at', 'updated_at', 'status']
    ordering = ['-session_date']
    
    def get_serializer_class(self):
        """Use different serializers for create vs read"""
        if self.action == 'create':
            return SOAPNoteCreateSerializer
        return SOAPNoteSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on user role:
        - Therapists see only their own notes
        - Admins and staff see all notes
        - Patients see only their own notes
        """
        user = self.request.user
        queryset = SOAPNote.objects.select_related('patient', 'therapist', 'appointment')
        
        # Role-based filtering first
        if user.role == 'therapist':
            queryset = queryset.filter(therapist=user)
        elif user.role == 'client':
            queryset = queryset.filter(patient=user)
        elif user.role in ['admin', 'staff']:
            # Admins and staff see all notes - no additional filtering
            pass
        else:
            return queryset.none()
        
        # Apply additional filters after role-based filtering
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        week_param = self.request.query_params.get('week', None)
        if week_param == 'current':
            today = timezone.now()
            start_of_week = today - timedelta(days=today.weekday())
            queryset = queryset.filter(session_date__gte=start_of_week)
        
        overdue_param = self.request.query_params.get('overdue', None)
        if overdue_param == 'true':
            # Notes in draft status older than 48 hours
            cutoff = timezone.now() - timedelta(hours=48)
            queryset = queryset.filter(status='draft', created_at__lt=cutoff)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set therapist to current user if not provided"""
        if not serializer.validated_data.get('therapist'):
            serializer.save(therapist=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def finalize(self, request, pk=None):
        """
        Finalize a SOAP note (mark as completed and set finalized_at timestamp)
        """
        note = self.get_object()
        
        if note.status == 'finalized':
            return Response(
                {'detail': 'Note is already finalized.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        note.status = 'finalized'
        note.finalized_at = timezone.now()
        note.save()
        
        serializer = self.get_serializer(note)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get statistics for SOAP notes
        """
        user = request.user
        queryset = self.get_queryset()
        
        # Get counts
        today = timezone.now()
        start_of_week = today - timedelta(days=today.weekday())
        cutoff_48h = today - timedelta(hours=48)
        
        stats = {
            'total': queryset.count(),
            'completed_this_week': queryset.filter(
                status='finalized',
                session_date__gte=start_of_week
            ).count(),
            'draft': queryset.filter(status='draft').count(),
            'overdue': queryset.filter(
                status='draft',
                created_at__lt=cutoff_48h
            ).count(),
        }
        
        return Response(stats)
