# backend/users/permissions.py
"""
Custom permissions for TheraCare EHR System.
HIPAA-compliant role-based access control.
"""

from rest_framework import permissions
from django.core.exceptions import ObjectDoesNotExist


class IsAdminUser(permissions.BasePermission):
    """Permission class that only allows admin users."""

    message = "You must be an administrator to perform this action."

    def has_permission(self, request, view):
        """Check if user is authenticated and has admin role."""
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsTherapistOrAdmin(permissions.BasePermission):
    """Permission class that allows therapists and admin users."""

    message = "You must be a therapist or administrator to perform this action."

    def has_permission(self, request, view):
        """Check if user is authenticated and has therapist or admin role."""
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["therapist", "admin"]
        )


class IsStaffOrAdmin(permissions.BasePermission):
    """Permission class that allows staff and admin users."""

    message = "You must be staff or administrator to perform this action."

    def has_permission(self, request, view):
        """Check if user is authenticated and has staff or admin role."""
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["staff", "admin"]
        )


class IsTherapistStaffOrAdmin(permissions.BasePermission):
    """Permission class that allows therapists, staff, and admin users."""

    message = "You must be a therapist, staff member, or administrator to perform this action."

    def has_permission(self, request, view):
        """Check if user is authenticated and has appropriate role."""
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["therapist", "staff", "admin"]
        )


class IsClientUser(permissions.BasePermission):
    """Permission class that only allows client users."""

    message = "This action is only available to client users."

    def has_permission(self, request, view):
        """Check if user is authenticated and has client role."""
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "client"
        )


class IsAdminOrSelf(permissions.BasePermission):
    """Permission class that allows admin users or the user themselves."""

    message = (
        "You can only access your own information unless you are an administrator."
    )

    def has_permission(self, request, view):
        """Check basic authentication."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user is admin or accessing their own object."""
        # Admin can access any user object
        if request.user.role == "admin":
            return True

        # User can access their own object
        if hasattr(obj, "user"):
            return obj.user == request.user
        elif hasattr(obj, "id"):
            return obj.id == request.user.id

        return False


class IsPatientOwnerOrTherapist(permissions.BasePermission):
    """
    Permission class for patient data access.
    Allows:
    - Admin users (full access)
    - Assigned therapists
    - Patient themselves (if they have a user account)
    """

    message = "You can only access patient information you are authorized to view."

    def has_permission(self, request, view):
        """Check basic authentication and role."""
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["admin", "therapist", "staff", "client"]
        )

    def has_object_permission(self, request, view, obj):
        """Check if user can access this specific patient object."""
        # Admin can access any patient
        if request.user.role == "admin":
            return True

        # Get patient object (handle different model types)
        patient = obj
        if hasattr(obj, "patient"):
            patient = obj.patient

        # Check if therapist is assigned to this patient
        if request.user.role in ["therapist", "staff"]:
            try:
                # Check if user is assigned as therapist to this patient
                from patients.models import PatientTherapistAssignment

                return PatientTherapistAssignment.objects.filter(
                    patient=patient, therapist=request.user, is_active=True
                ).exists()
            except (ImportError, ObjectDoesNotExist):
                return False

        # Check if client user is accessing their own patient record
        if request.user.role == "client":
            return hasattr(patient, "user") and patient.user == request.user

        return False


class IsAppointmentParticipant(permissions.BasePermission):
    """
    Permission class for appointment access.
    Allows:
    - Admin users (full access)
    - Assigned therapist
    - Patient (if they have a user account)
    """

    message = "You can only access appointments you are involved in."

    def has_permission(self, request, view):
        """Check basic authentication."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user can access this specific appointment."""
        # Admin can access any appointment
        if request.user.role == "admin":
            return True

        # Get appointment object
        appointment = obj
        if hasattr(obj, "appointment"):
            appointment = obj.appointment

        # Check if user is the therapist for this appointment
        if request.user.role in ["therapist", "staff"]:
            return appointment.therapist == request.user

        # Check if client user is the patient for this appointment
        if request.user.role == "client":
            return (
                hasattr(appointment.patient, "user")
                and appointment.patient.user == request.user
            )

        return False


class IsMessageParticipant(permissions.BasePermission):
    """
    Permission class for message access.
    Allows:
    - Admin users (full access)
    - Message sender
    - Message recipient
    """

    message = "You can only access messages you are involved in."

    def has_permission(self, request, view):
        """Check basic authentication."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user can access this specific message."""
        # Admin can access any message
        if request.user.role == "admin":
            return True

        # Get message object
        message = obj
        if hasattr(obj, "message"):
            message = obj.message

        # Check if user is sender or recipient
        return message.sender == request.user or message.recipient == request.user


class IsSOAPNoteAuthorOrTherapist(permissions.BasePermission):
    """
    Permission class for SOAP note access.
    Allows:
    - Admin users (full access)
    - Note author
    - Assigned therapists for the patient
    - Patient themselves (read-only)
    """

    message = "You can only access SOAP notes you are authorized to view."

    def has_permission(self, request, view):
        """Check basic authentication and role."""
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["admin", "therapist", "staff", "client"]
        )

    def has_object_permission(self, request, view, obj):
        """Check if user can access this specific SOAP note."""
        # Admin can access any SOAP note
        if request.user.role == "admin":
            return True

        # Get SOAP note object
        soap_note = obj
        if hasattr(obj, "soap_note"):
            soap_note = obj.soap_note

        # Check if user is the author
        if hasattr(soap_note, "author") and soap_note.author == request.user:
            return True

        # Check if therapist is assigned to the patient
        if request.user.role in ["therapist", "staff"]:
            try:
                from patients.models import PatientTherapistAssignment

                return PatientTherapistAssignment.objects.filter(
                    patient=soap_note.patient, therapist=request.user, is_active=True
                ).exists()
            except (ImportError, ObjectDoesNotExist):
                return False

        # Check if client user is accessing their own SOAP notes (read-only)
        if request.user.role == "client":
            if request.method not in permissions.SAFE_METHODS:
                return False  # Clients can only read SOAP notes
            return (
                hasattr(soap_note.patient, "user")
                and soap_note.patient.user == request.user
            )

        return False


class IsBillingAuthorized(permissions.BasePermission):
    """
    Permission class for billing information access.
    Allows:
    - Admin users (full access)
    - Staff with billing permissions
    - Patient themselves (limited access)
    """

    message = "You are not authorized to access billing information."

    def has_permission(self, request, view):
        """Check basic authentication and role."""
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["admin", "staff", "client"]
        )

    def has_object_permission(self, request, view, obj):
        """Check if user can access this specific billing object."""
        # Admin can access any billing information
        if request.user.role == "admin":
            return True

        # Staff can access billing information
        if request.user.role == "staff":
            return True

        # Get billing object
        billing = obj
        if hasattr(obj, "billing"):
            billing = obj.billing

        # Check if client user is accessing their own billing information
        if request.user.role == "client":
            if hasattr(billing, "patient"):
                return (
                    hasattr(billing.patient, "user")
                    and billing.patient.user == request.user
                )
            elif hasattr(billing, "user"):
                return billing.user == request.user

        return False


class ReadOnlyOrCreateOnly(permissions.BasePermission):
    """
    Permission class that allows read operations and create operations,
    but restricts update and delete operations.
    """

    message = "You can only view or create this resource."

    def has_permission(self, request, view):
        """Allow GET, HEAD, OPTIONS, and POST methods."""
        return request.method in ["GET", "HEAD", "OPTIONS", "POST"]


class HIPAACompliancePermission(permissions.BasePermission):
    """
    Special permission class for HIPAA compliance.
    Logs all access attempts to sensitive data.
    """

    def has_permission(self, request, view):
        """Log access attempt and check basic authentication."""
        import logging
        from django.utils import timezone

        logger = logging.getLogger("theracare.audit")

        # Log access attempt
        logger.info(
            "PHI access attempt",
            extra={
                "event_type": "phi_access_attempt",
                "user_id": (
                    str(request.user.id) if request.user.is_authenticated else None
                ),
                "username": (
                    request.user.username if request.user.is_authenticated else None
                ),
                "view_name": view.__class__.__name__,
                "method": request.method,
                "path": request.path,
                "ip_address": request.META.get("REMOTE_ADDR"),
                "user_agent": request.META.get("HTTP_USER_AGENT"),
                "timestamp": timezone.now().isoformat(),
            },
        )

        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Log specific object access."""
        import logging
        from django.utils import timezone

        logger = logging.getLogger("theracare.audit")

        # Log object access
        logger.info(
            "PHI object access",
            extra={
                "event_type": "phi_object_access",
                "user_id": str(request.user.id),
                "username": request.user.username,
                "object_type": obj.__class__.__name__,
                "object_id": str(getattr(obj, "id", None)),
                "method": request.method,
                "timestamp": timezone.now().isoformat(),
            },
        )

        return True  # Actual permission check should be combined with other permissions
