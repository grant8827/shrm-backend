# backend/telehealth/serializers.py
"""
Telehealth serializers for TheraCare EHR System.
"""

from rest_framework import serializers
from .models import TelehealthSession, TelehealthTranscript
from users.serializers import UserListSerializer


class TelehealthSessionSerializer(serializers.ModelSerializer):
    """Serializer for telehealth sessions."""

    patient_details = UserListSerializer(source="patient", read_only=True)
    therapist_details = UserListSerializer(source="therapist", read_only=True)
    is_upcoming = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()
    actual_duration = serializers.ReadOnlyField()

    class Meta:
        model = TelehealthSession
        fields = [
            "id",
            "title",
            "description",
            "patient",
            "patient_details",
            "therapist",
            "therapist_details",
            "scheduled_at",
            "duration",
            "status",
            "is_emergency",
            "session_url",
            "room_id",
            "notes",
            "has_recording",
            "has_transcript",
            "recording_url",
            "transcript_url",
            "created_at",
            "updated_at",
            "started_at",
            "ended_at",
            "is_upcoming",
            "is_past",
            "actual_duration",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_scheduled_at(self, value):
        """Validate that scheduled time is in the future."""
        from django.utils import timezone

        if value < timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future.")
        return value

    def validate(self, data):
        """Cross-field validation."""
        # Ensure patient and therapist are different (only if both exist)
        if "patient" in data and "therapist" in data:
            if (
                data["patient"]
                and data["therapist"]
                and data["patient"] == data["therapist"]
            ):
                raise serializers.ValidationError(
                    "Patient and therapist must be different users."
                )
        return data


class TelehealthSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating telehealth sessions."""

    class Meta:
        model = TelehealthSession
        fields = [
            "title",
            "description",
            "patient",
            "therapist",
            "scheduled_at",
            "duration",
            "is_emergency",
            "notes",
        ]

    def validate_scheduled_at(self, value):
        """Validate that scheduled time is in the future."""
        from django.utils import timezone

        if value < timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future.")
        return value


class TelehealthTranscriptSerializer(serializers.ModelSerializer):
    """Serializer for persisted telehealth transcripts."""

    session_time = serializers.DateTimeField(
        source="session.scheduled_at", read_only=True
    )
    session_title = serializers.CharField(source="session.title", read_only=True)
    patient_name = serializers.SerializerMethodField()
    therapist_name = serializers.SerializerMethodField()

    class Meta:
        model = TelehealthTranscript
        fields = [
            "id",
            "session",
            "session_time",
            "session_title",
            "patient",
            "patient_name",
            "therapist",
            "therapist_name",
            "created_by",
            "transcript",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_patient_name(self, obj):
        if not obj.patient:
            return "Unknown Patient"
        return (
            f"{obj.patient.first_name or ''} {obj.patient.last_name or ''}".strip()
            or obj.patient.email
        )

    def get_therapist_name(self, obj):
        return (
            f"{obj.therapist.first_name or ''} {obj.therapist.last_name or ''}".strip()
            or obj.therapist.email
        )
