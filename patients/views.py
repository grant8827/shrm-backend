"""
Patient views for TheraCare EHR System.
HIPAA-compliant patient management with role-based access.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import Patient
from .serializers import PatientListSerializer, PatientDetailSerializer
from users.email_service import send_registration_email
import logging

logger = logging.getLogger('theracare.audit')


class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for patient management.
    - Admins can see all patients
    - Therapists can see their assigned patients
    - Clients (patients) can see their own profile
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Use list serializer for list view, detail for everything else."""
        if self.action == 'list':
            return PatientListSerializer
        return PatientDetailSerializer
    
    def get_queryset(self):
        """Filter patients based on user role."""
        user = self.request.user
        queryset = Patient.objects.select_related('primary_therapist', 'user').prefetch_related('assigned_therapists')
        
        # Admins and therapists can see all patients
        if user.role in ['admin', 'therapist']:
            return queryset.all()
        
        # Clients can see only their own patient profile
        elif user.role == 'client':
            if hasattr(user, 'patient_profile'):
                return queryset.filter(id=user.patient_profile.id)
            return queryset.none()
        
        # Default: no access
        return queryset.none()
    
    def perform_create(self, serializer):
        """Set created_by when creating a patient.
        
        Note: Email sending is handled by the serializer's create() method,
        which sends token-based registration emails when portal access is requested.
        """
        serializer.save(created_by=self.request.user)
        
        logger.info(
            'Patient created',
            extra={
                'event_type': 'patient_create',
                'user_id': str(self.request.user.id),
                'patient_id': str(serializer.instance.id),
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    def perform_update(self, serializer):
        """Audit log patient updates."""
        serializer.save()
        
        logger.info(
            'Patient updated',
            extra={
                'event_type': 'patient_update',
                'user_id': str(self.request.user.id),
                'patient_id': str(serializer.instance.id),
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    def perform_destroy(self, instance):
        """Audit log patient deletion (soft delete recommended in production)."""
        patient_id = str(instance.id)
        instance.delete()
        
        logger.warning(
            'Patient deleted',
            extra={
                'event_type': 'patient_delete',
                'user_id': str(self.request.user.id),
                'patient_id': patient_id,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    @action(detail=True, methods=['get'])
    def appointments(self, request, pk=None):
        """Get all appointments for a patient."""
        patient = self.get_object()
        # TODO: Implement appointment retrieval
        return Response({'message': 'Appointments endpoint not yet implemented'})
    
    @action(detail=True, methods=['get'])
    def notes(self, request, pk=None):
        """Get all SOAP notes for a patient."""
        patient = self.get_object()
        # TODO: Implement SOAP notes retrieval
        return Response({'message': 'SOAP notes endpoint not yet implemented'})
    
    @action(detail=True, methods=['post'])
    def resend_welcome_email(self, request, pk=None):
        """Resend token-based registration email to patient."""
        patient = self.get_object()
        
        # Check if user has permission (admin or therapist only)
        if request.user.role not in ['admin', 'therapist']:
            return Response(
                {'error': 'Only administrators and therapists can resend registration emails'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Registration email is only for patients without an existing user account
        if patient.user:
            return Response(
                {'error': 'Patient already has portal access. Use password reset instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not patient.email:
            return Response(
                {'error': 'Patient does not have an email address'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Send registration email
        try:
            email_sent, _ = send_registration_email(
                email=patient.email,
                first_name=patient.first_name,
                last_name=patient.last_name,
                phone_number=patient.phone or ''
            )
            
            logger.info(
                'Welcome email resent',
                extra={
                    'event_type': 'email_resend',
                    'user_id': str(request.user.id),
                    'patient_id': str(patient.id),
                    'timestamp': timezone.now().isoformat(),
                }
            )
            
            if email_sent:
                return Response({
                    'message': 'Registration email sent successfully',
                    'email': patient.email
                })
            else:
                return Response(
                    {'error': 'Failed to send email. Please check email configuration.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(
                f'Error resending welcome email: {str(e)}',
                extra={
                    'event_type': 'email_resend_error',
                    'user_id': str(request.user.id),
                    'patient_id': str(patient.id),
                    'error': str(e),
                    'timestamp': timezone.now().isoformat(),
                }
            )
            return Response(
                {'error': f'Error sending email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
