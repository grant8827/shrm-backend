from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import Appointment, AppointmentType
from .serializers import (
    AppointmentSerializer,
    AppointmentCreateSerializer,
    AppointmentUpdateSerializer,
    AppointmentTypeSerializer,
)


class AppointmentPermission(permissions.BasePermission):
    """
    Custom permission for appointments:
    - Admin and Staff can view all, create, update, delete
    - Therapists can view their own appointments and create/update them
    - Clients can view their own appointments and update status (confirm)
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Admin and Staff have full access
        if request.user.role in ["admin", "staff"]:
            return True

        # Therapists can create and view
        if request.user.role == "therapist":
            return True

        # Clients can view (GET), update status (PATCH), and confirm/cancel (POST to specific actions)
        if request.user.role == "client":
            # Allow POST for specific client actions like confirm and cancel
            if request.method == "POST" and view.action in ["confirm", "cancel"]:
                return True
            return (
                request.method in permissions.SAFE_METHODS or request.method == "PATCH"
            )

        return False

    def has_object_permission(self, request, view, obj):
        # Admin and Staff can do anything
        if request.user.role in ["admin", "staff"]:
            return True

        # Therapists can manage their own appointments
        if request.user.role == "therapist":
            return obj.therapist == request.user

        # Clients can view and update status of their own appointments
        if request.user.role == "client":
            if obj.patient == request.user:
                # Allow viewing, PATCH, and POST for confirm/cancel actions
                if request.method == "POST" and view.action in ["confirm", "cancel"]:
                    return True
                return (
                    request.method in permissions.SAFE_METHODS
                    or request.method == "PATCH"
                )

        return False


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    permission_classes = [AppointmentPermission]

    def get_queryset(self):
        user = self.request.user

        # Admin and Staff see all appointments
        if user.role in ["admin", "staff"]:
            queryset = Appointment.objects.select_related(
                "patient", "therapist", "appointment_type"
            )

            # Filter by patient if specified
            patient_id = self.request.query_params.get("patient")
            if patient_id:
                queryset = queryset.filter(patient_id=patient_id)

            # Filter by therapist
            therapist_id = self.request.query_params.get("therapist")
            if therapist_id:
                queryset = queryset.filter(therapist_id=therapist_id)

            # Filter by status
            appointment_status = self.request.query_params.get("status")
            if appointment_status:
                queryset = queryset.filter(status=appointment_status)

            # Filter by date range
            start_date = self.request.query_params.get("start_date")
            end_date = self.request.query_params.get("end_date")
            if start_date:
                queryset = queryset.filter(start_datetime__gte=start_date)
            if end_date:
                queryset = queryset.filter(start_datetime__lte=end_date)

            return queryset.order_by("-start_datetime")

        # Therapists see their own appointments
        elif user.role == "therapist":
            return (
                Appointment.objects.filter(therapist=user)
                .select_related("patient", "therapist", "appointment_type")
                .order_by("-start_datetime")
            )

        # Clients see only their own appointments
        elif user.role == "client":
            return (
                Appointment.objects.filter(patient=user)
                .select_related("patient", "therapist", "appointment_type")
                .order_by("-start_datetime")
            )

        return Appointment.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return AppointmentCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return AppointmentUpdateSerializer
        return AppointmentSerializer

    def perform_create(self, serializer):
        appointment = serializer.save()

        # Auto-create telehealth session if appointment is telehealth
        if appointment.is_telehealth:
            from telehealth.models import TelehealthSession

            TelehealthSession.objects.create(
                title=f"Telehealth Session - {appointment.patient.get_full_name()}",
                description=f"Scheduled telehealth appointment with {appointment.therapist.get_full_name()}",
                patient=appointment.patient,
                therapist=appointment.therapist,
                scheduled_at=appointment.start_datetime,
                duration=(appointment.end_datetime - appointment.start_datetime).seconds
                // 60,
                status="scheduled",
            )

    def perform_update(self, serializer):
        appointment = serializer.save()

        # If appointment is cancelled, cancel linked telehealth session
        if appointment.status == "cancelled" and appointment.is_telehealth:
            from telehealth.models import TelehealthSession

            # Find and cancel the telehealth session
            TelehealthSession.objects.filter(
                patient=appointment.patient,
                therapist=appointment.therapist,
                scheduled_at=appointment.start_datetime,
                status="scheduled",
            ).update(status="cancelled")

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel an appointment and linked telehealth session"""
        appointment = self.get_object()
        appointment.status = "cancelled"
        appointment.save()

        # Cancel linked telehealth session if exists
        if appointment.is_telehealth:
            from telehealth.models import TelehealthSession

            TelehealthSession.objects.filter(
                patient=appointment.patient,
                therapist=appointment.therapist,
                scheduled_at=appointment.start_datetime,
                status="scheduled",
            ).update(status="cancelled")

        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """Confirm an appointment"""
        appointment = self.get_object()
        appointment.status = "confirmed"
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def check_in(self, request, pk=None):
        """Check in a patient for their appointment"""
        appointment = self.get_object()
        appointment.status = "checked_in"
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def start_session(self, request, pk=None):
        """Start an appointment session"""
        appointment = self.get_object()
        appointment.status = "in_session"
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Complete an appointment"""
        appointment = self.get_object()
        appointment.status = "completed"
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)


class AppointmentTypeViewSet(viewsets.ModelViewSet):
    queryset = AppointmentType.objects.filter(is_active=True)
    serializer_class = AppointmentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AppointmentType.objects.filter(is_active=True).order_by("name")
