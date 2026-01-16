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
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import TelehealthSession
from .serializers import TelehealthSessionSerializer, TelehealthSessionCreateSerializer
import logging
import uuid

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
        """Filter sessions based on user role and query parameters."""
        user = self.request.user
        queryset = TelehealthSession.objects.all()

        # Filter by room_id if provided (for join links)
        room_id = self.request.query_params.get('room_id', None)
        if room_id:
            queryset = queryset.filter(room_id=room_id)
            # For room_id queries, allow patient to see their session
            # even if they wouldn't normally see it
            if user.role == 'client':
                queryset = queryset.filter(patient=user)
            return queryset

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

    @action(detail=False, methods=['post'])
    def create_emergency(self, request):
        """
        Create an emergency session and send link via email.
        Supports two modes:
        1. Existing patient: Provide patient_id
        2. New/External patient: Provide patient_email, patient_first_name, patient_last_name
        Therapist/Admin/Staff only.
        """
        if request.user.role not in ['admin', 'therapist', 'staff']:
            return Response(
                {'error': 'Only therapists, staff, and admins can create emergency sessions.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        patient_id = request.data.get('patient_id')
        patient_email = request.data.get('patient_email')
        patient_first_name = request.data.get('patient_first_name')
        patient_last_name = request.data.get('patient_last_name')
        
        # Determine if using existing patient or external email
        if patient_id:
            # Mode 1: Existing patient
            try:
                from users.models import User
                patient = User.objects.get(id=patient_id)
                patient_name = f"{patient.first_name} {patient.last_name}"
                recipient_email = patient.email
            except User.DoesNotExist:
                return Response(
                    {'error': 'Patient not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif patient_email and patient_first_name and patient_last_name:
            # Mode 2: External patient (no user account)
            patient = None
            patient_name = f"{patient_first_name} {patient_last_name}"
            recipient_email = patient_email
            
            # Validate email format
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            try:
                validate_email(recipient_email)
            except ValidationError:
                return Response(
                    {'error': 'Invalid email address'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'error': 'Either patient_id OR (patient_email, patient_first_name, patient_last_name) is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate unique room_id
        room_id = str(uuid.uuid4())
        
        # Create emergency session
        session = TelehealthSession.objects.create(
            title=f"Emergency Session - {patient_name}",
            patient=patient,  # Will be None for external patients
            therapist=request.user,
            scheduled_at=timezone.now(),
            duration=30,  # Default 30 minutes
            status='in-progress',  # Start immediately
            room_id=room_id,
            session_url=f"{settings.FRONTEND_URL}/telehealth/join/{room_id}",
            notes=f"External patient: {patient_name} ({recipient_email})" if not patient else ""
        )
        
        # Send email
        try:
            email_context = {
                'patient_name': patient_name,
                'therapist_name': f"{request.user.first_name} {request.user.last_name}",
                'session_url': session.session_url,
                'room_id': room_id
            }
            
            email_body = render_to_string('emails/emergency_session.html', email_context)
            
            send_mail(
                subject='Emergency Telehealth Session - Join Now',
                message=f"You have an emergency telehealth session. Join here: {session.session_url}",
                html_message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            
            logger.info(
                'Emergency session created and email sent',
                extra={
                    'event_type': 'emergency_session_created',
                    'session_id': str(session.id),
                    'patient_id': str(patient.id) if patient else 'external',
                    'patient_email': recipient_email,
                    'therapist_id': str(request.user.id),
                    'room_id': room_id,
                    'timestamp': timezone.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Failed to send emergency session email: {str(e)}")
            # Don't fail the request if email fails
        
        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

