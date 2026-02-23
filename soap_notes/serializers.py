"""
Serializers for SOAP Notes
"""

from rest_framework import serializers
from .models import SOAPNote


class SOAPNoteSerializer(serializers.ModelSerializer):
    """Serializer for SOAPNote model"""

    patient_name = serializers.SerializerMethodField()
    therapist_name = serializers.SerializerMethodField()
    appointment_details = serializers.SerializerMethodField()

    class Meta:
        model = SOAPNote
        fields = [
            "id",
            "patient",
            "patient_name",
            "therapist",
            "therapist_name",
            "appointment",
            "appointment_details",
            "session_date",
            "session_duration",
            "chief_complaint",
            "subjective",
            "objective",
            "assessment",
            "plan",
            "status",
            "created_at",
            "updated_at",
            "finalized_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "finalized_at"]

    def get_patient_name(self, obj):
        """Get patient's full name"""
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return None

    def get_therapist_name(self, obj):
        """Get therapist's full name"""
        if obj.therapist:
            return f"{obj.therapist.first_name} {obj.therapist.last_name}"
        return None

    def get_appointment_details(self, obj):
        """Get appointment details if linked"""
        if obj.appointment:
            return {
                "id": str(obj.appointment.id),
                "start_datetime": obj.appointment.start_datetime,
                "end_datetime": obj.appointment.end_datetime,
                "appointment_type": (
                    obj.appointment.appointment_type.name
                    if obj.appointment.appointment_type
                    else None
                ),
            }
        return None


class SOAPNoteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating SOAP notes"""

    class Meta:
        model = SOAPNote
        fields = [
            "patient",
            "therapist",
            "appointment",
            "session_date",
            "session_duration",
            "chief_complaint",
            "subjective",
            "objective",
            "assessment",
            "plan",
            "status",
        ]

    def validate_patient(self, value):
        """Ensure patient has the correct role"""
        if value.role != "client":
            raise serializers.ValidationError("Selected user is not a patient.")
        return value

    def validate_therapist(self, value):
        """Ensure therapist has the correct role"""
        if value.role not in ["therapist", "admin", "staff"]:
            raise serializers.ValidationError("Selected user is not a therapist.")
        return value
