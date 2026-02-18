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
from .models import TelehealthSession, TelehealthTranscript
from .serializers import TelehealthSessionSerializer, TelehealthSessionCreateSerializer, TelehealthTranscriptSerializer
import logging
import uuid
import threading

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

    def retrieve(self, request, *args, **kwargs):
        """Get session details, ensuring room_id exists."""
        instance = self.get_object()
        if not instance.room_id:
            import uuid
            instance.room_id = str(uuid.uuid4())
            instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

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

    @action(detail=False, methods=['get'])
    def emergency_sessions(self, request):
        """Get emergency sessions for the current user."""
        user = request.user
        
        sessions = TelehealthSession.objects.filter(
            Q(patient=user) | Q(therapist=user),
            is_emergency=True
        ).order_by('-scheduled_at')
        
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

    @action(detail=True, methods=['post'])
    def save_transcript(self, request, pk=None):
        """Save or update transcript text for a session."""
        if request.user.role not in ['admin', 'therapist']:
            return Response(
                {'error': 'Only therapists and admins can save transcripts.'},
                status=status.HTTP_403_FORBIDDEN
            )

        session = self.get_object()

        if str(session.therapist_id) != str(request.user.id):
            return Response(
                {'error': 'You can only save transcripts for your own sessions.'},
                status=status.HTTP_403_FORBIDDEN
            )

        transcript_text = (request.data.get('transcript') or '').strip()
        if not transcript_text:
            return Response(
                {'error': 'Transcript text is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transcript_record, _ = TelehealthTranscript.objects.update_or_create(
            session=session,
            defaults={
                'patient': session.patient,
                'therapist': session.therapist,
                'created_by': request.user,
                'transcript': transcript_text,
            }
        )

        if not session.has_transcript:
            session.has_transcript = True
            session.save(update_fields=['has_transcript'])

        logger.info(
            'Telehealth transcript saved',
            extra={
                'event_type': 'telehealth_transcript_saved',
                'session_id': str(session.id),
                'saved_by': str(request.user.id),
                'timestamp': timezone.now().isoformat(),
            }
        )

        serializer = TelehealthTranscriptSerializer(transcript_record)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def transcripts(self, request):
        """List saved transcripts for the authenticated therapist/admin's own sessions."""
        if request.user.role not in ['admin', 'therapist']:
            return Response(
                {'error': 'Only therapists and admins can view transcripts.'},
                status=status.HTTP_403_FORBIDDEN
            )

        transcripts = TelehealthTranscript.objects.select_related(
            'session', 'patient', 'therapist', 'created_by'
        ).filter(
            Q(session__therapist=request.user) | Q(created_by=request.user)
        ).distinct().order_by('-created_at')

        serializer = TelehealthTranscriptSerializer(transcripts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def create_emergency(self, request):
        """
        Create an emergency session for an existing internal patient.
        Requires patient_id.
        Therapist/Admin/Staff only.
        """
        if request.user.role not in ['admin', 'therapist', 'staff']:
            return Response(
                {'error': 'Only therapists, staff, and admins can create emergency sessions.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        patient_id = request.data.get('patient_id')
        
        if not patient_id:
            return Response(
                {'error': 'patient_id is required for emergency sessions'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get existing patient
        try:
            from users.models import User
            patient = User.objects.get(id=patient_id)
            
            # Verify patient has correct role
            if patient.role != 'client':
                return Response(
                    {'error': 'Selected user is not a patient'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            patient_name = f"{patient.first_name} {patient.last_name}"
            recipient_email = patient.email
        except User.DoesNotExist:
            return Response(
                {'error': 'Patient not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate unique room_id
        room_id = str(uuid.uuid4())
        
        # Create emergency session
        session = TelehealthSession.objects.create(
            title=f"Emergency Session - {patient_name}",
            patient=patient,
            therapist=request.user,
            scheduled_at=timezone.now(),
            duration=30,  # Default 30 minutes
            status='scheduled',  # Set as scheduled so it appears in upcoming
            is_emergency=True,  # Mark as emergency
            room_id=room_id,
            session_url=f"{settings.FRONTEND_URL}/telehealth/join/{room_id}",
        )
        
        # Send email asynchronously in a separate thread to avoid timeout
        def send_email_async():
            try:
                print("=" * 80)
                print(f"[EMAIL DEBUG] RECIPIENT EMAIL: {recipient_email}")
                print(f"[EMAIL DEBUG] FROM EMAIL: {settings.DEFAULT_FROM_EMAIL}")
                print(f"[EMAIL DEBUG] Session URL: {session.session_url}")
                print(f"[EMAIL DEBUG] Email settings - Host: {settings.EMAIL_HOST}, Port: {settings.EMAIL_PORT}")
                print(f"[EMAIL DEBUG] Email settings - USE_SSL: {settings.EMAIL_USE_SSL}, USE_TLS: {settings.EMAIL_USE_TLS}")
                print("=" * 80)
                
                email_context = {
                    'patient_name': patient_name,
                    'therapist_name': f"{request.user.first_name} {request.user.last_name}",
                    'session_url': session.session_url,
                    'room_id': room_id
                }
                
                email_body = render_to_string('emails/emergency_session.html', email_context)
                
                print(f"[EMAIL DEBUG] About to call send_mail with:")
                print(f"[EMAIL DEBUG]   TO: {recipient_email}")
                print(f"[EMAIL DEBUG]   FROM: {settings.DEFAULT_FROM_EMAIL}")
                
                result = send_mail(
                    subject='Emergency Telehealth Session - Join Now',
                    message=f"You have an emergency telehealth session. Join here: {session.session_url}",
                    html_message=email_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient_email],
                    fail_silently=False,
                )
                
                print(f"[EMAIL DEBUG] ✅ Email sent successfully! Result: {result}")
                print(f"[EMAIL DEBUG] Check inbox at: {recipient_email}")
                
                logger.info(
                    'Emergency session email sent successfully',
                    extra={
                        'event_type': 'emergency_session_email_sent',
                        'session_id': str(session.id),
                        'patient_email': recipient_email,
                        'email_result': result,
                        'timestamp': timezone.now().isoformat(),
                    }
                )
            except Exception as e:
                print(f"[EMAIL DEBUG] FAILED to send email: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                
                logger.error(
                    f"Failed to send emergency session email: {str(e)}",
                    extra={
                        'event_type': 'emergency_session_email_failed',
                        'session_id': str(session.id),
                        'patient_email': recipient_email,
                        'error': str(e),
                        'timestamp': timezone.now().isoformat(),
                    }
                )
        
        # Start email sending in background thread
        email_thread = threading.Thread(target=send_email_async)
        email_thread.daemon = True
        email_thread.start()
        
        # Log session creation
        logger.info(
            'Emergency session created',
            extra={
                'event_type': 'emergency_session_created',
                'session_id': str(session.id),
                'patient_id': str(patient.id),
                'patient_email': recipient_email,
                'therapist_id': str(request.user.id),
                'room_id': room_id,
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

