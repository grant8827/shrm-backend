from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import Appointment, AppointmentType
from .serializers import (
    AppointmentSerializer, AppointmentCreateSerializer,
    AppointmentUpdateSerializer, AppointmentTypeSerializer
)


class AppointmentPermission(permissions.BasePermission):
    """
    Custom permission for appointments:
    - Admin and Staff can view all, create, update, delete
    - Therapists can view their own appointments and create/update them
    - Clients can only view their own appointments
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Admin and Staff have full access
        if request.user.role in ['admin', 'staff']:
            return True
        
        # Therapists can create and view
        if request.user.role == 'therapist':
            return True
        
        # Clients can only view (GET)
        if request.user.role == 'client' and request.method in permissions.SAFE_METHODS:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Admin and Staff can do anything
        if request.user.role in ['admin', 'staff']:
            return True
        
        # Therapists can manage their own appointments
        if request.user.role == 'therapist':
            return obj.therapist == request.user
        
        # Clients can only view their own appointments
        if request.user.role == 'client':
            return obj.patient == request.user and request.method in permissions.SAFE_METHODS
        
        return False


class AppointmentViewSet(viewsets.ModelViewSet):
    permission_classes = [AppointmentPermission]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin and Staff see all appointments
        if user.role in ['admin', 'staff']:
            queryset = Appointment.objects.select_related(
                'patient', 'therapist', 'appointment_type'
            )
            
            # Filter by patient if specified
            patient_id = self.request.query_params.get('patient')
            if patient_id:
                queryset = queryset.filter(patient_id=patient_id)
            
            # Filter by therapist
            therapist_id = self.request.query_params.get('therapist')
            if therapist_id:
                queryset = queryset.filter(therapist_id=therapist_id)
            
            # Filter by status
            appointment_status = self.request.query_params.get('status')
            if appointment_status:
                queryset = queryset.filter(status=appointment_status)
            
            # Filter by date range
            start_date = self.request.query_params.get('start_date')
            end_date = self.request.query_params.get('end_date')
            if start_date:
                queryset = queryset.filter(start_datetime__gte=start_date)
            if end_date:
                queryset = queryset.filter(start_datetime__lte=end_date)
            
            return queryset.order_by('-start_datetime')
        
        # Therapists see their own appointments
        elif user.role == 'therapist':
            return Appointment.objects.filter(
                therapist=user
            ).select_related(
                'patient', 'therapist', 'appointment_type'
            ).order_by('-start_datetime')
        
        # Clients see only their own appointments
        elif user.role == 'client':
            return Appointment.objects.filter(
                patient=user
            ).select_related(
                'patient', 'therapist', 'appointment_type'
            ).order_by('-start_datetime')
        
        return Appointment.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AppointmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AppointmentUpdateSerializer
        return AppointmentSerializer
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an appointment"""
        appointment = self.get_object()
        appointment.status = 'cancelled'
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm an appointment"""
        appointment = self.get_object()
        appointment.status = 'confirmed'
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        """Check in a patient for their appointment"""
        appointment = self.get_object()
        appointment.status = 'checked_in'
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def start_session(self, request, pk=None):
        """Start an appointment session"""
        appointment = self.get_object()
        appointment.status = 'in_session'
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete an appointment"""
        appointment = self.get_object()
        appointment.status = 'completed'
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)


class AppointmentTypeViewSet(viewsets.ModelViewSet):
    queryset = AppointmentType.objects.filter(is_active=True)
    serializer_class = AppointmentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AppointmentType.objects.filter(is_active=True).order_by('name')
