# backend/telehealth/views.py
"""
Telehealth views for TheraCare EHR System.
HIPAA-compliant telehealth session management.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from .models import TelehealthSession
from .serializers import TelehealthSessionSerializer, TelehealthSessionCreateSerializer
import logging

logger = logging.getLogger('theracare.audit')


class TelehealthSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing telehealth sessions.
    
    Endpoints:
    - GET /api/telehealth/sessions/ - List all sessions (filtered by user)
    - POST /api/telehealth/sessions/ - Create new session
    - GET /api/telehealth/sessions/{id}/ - Get session details
    - PUT/PATCH /api/telehealth/sessions/{id}/ - Update session
    - DELETE /api/telehealth/sessions/{id}/ - Delete session
    - GET /api/telehealth/sessions/my-sessions/ - Get current user's sessions
    - GET /api/telehealth/sessions/upcoming/ - Get upcoming sessions
    """
    queryset = TelehealthSession.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == 'create':
            return TelehealthSessionCreateSerializer
        return TelehealthSessionSerializer

    def get_queryset(self):
        """Filter sessions based on user role."""
        user = self.request.user
        queryset = TelehealthSession.objects.all()

        # Admin sees all sessions
        if user.role == 'admin':
            return queryset

        # Therapists see sessions where they are the therapist
        if user.role in ['therapist', 'staff']:
            queryset = queryset.filter(therapist=user)

        # Patients see only their own sessions
        if user.role == 'client':
            queryset = queryset.filter(patient=user)

        return queryset

    def perform_create(self, serializer):
        """Create session with audit logging."""
        session = serializer.save()
        
        logger.info(
            'Telehealth session created',
            extra={
                'event_type': 'telehealth_session_created',
                'session_id': str(session.id),
                'patient_id': str(session.patient.id),
                'therapist_id': str(session.therapist.id),
                'created_by': str(self.request.user.id),
                'timestamp': timezone.now().isoformat(),
            }
        )

    def perform_update(self, serializer):
        """Update session with audit logging."""
        session = serializer.save()
        
        logger.info(
            'Telehealth session updated',
            extra={
                'event_type': 'telehealth_session_updated',
                'session_id': str(session.id),
                'updated_by': str(self.request.user.id),
                'timestamp': timezone.now().isoformat(),
            }
        )

    @action(detail=False, methods=['get'])
    def my_sessions(self, request):
        """Get sessions for the current user (as patient or therapist)."""
        user = request.user
        sessions = TelehealthSession.objects.filter(
            Q(patient=user) | Q(therapist=user)
        ).order_by('-scheduled_at')
        
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming sessions for the current user."""
        user = request.user
        now = timezone.now()
        
        sessions = TelehealthSession.objects.filter(
            Q(patient=user) | Q(therapist=user),
            scheduled_at__gte=now,
            status='scheduled'
        ).order_by('scheduled_at')
        
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Mark session as started."""
        session = self.get_object()
        
        if session.status != 'scheduled':
            return Response(
                {'error': 'Session must be scheduled to start.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'in-progress'
        session.started_at = timezone.now()
        session.save()
        
        logger.info(
            'Telehealth session started',
            extra={
                'event_type': 'telehealth_session_started',
                'session_id': str(session.id),
                'started_by': str(request.user.id),
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        serializer = self.get_serializer(session)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """Mark session as completed."""
        session = self.get_object()
        
        if session.status != 'in-progress':
            return Response(
                {'error': 'Session must be in progress to end.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'completed'
        session.ended_at = timezone.now()
        session.save()
        
        logger.info(
            'Telehealth session ended',
            extra={
                'event_type': 'telehealth_session_ended',
                'session_id': str(session.id),
                'ended_by': str(request.user.id),
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        serializer = self.get_serializer(session)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a session."""
        session = self.get_object()
        
        if session.status in ['completed', 'cancelled']:
            return Response(
                {'error': 'Cannot cancel a completed or already cancelled session.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'cancelled'
        session.save()
        
        logger.info(
            'Telehealth session cancelled',
            extra={
                'event_type': 'telehealth_session_cancelled',
                'session_id': str(session.id),
                'cancelled_by': str(request.user.id),
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        serializer = self.get_serializer(session)
        return Response(serializer.data)
