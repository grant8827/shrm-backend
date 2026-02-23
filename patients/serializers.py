"""
Patient serializers for TheraCare EHR System.
Handles decryption of PHI fields for API responses.
"""

from rest_framework import serializers
from .models import Patient
from users.serializers import UserListSerializer
from users.models import User
from django.db import transaction
from users.email_service import send_registration_email
import logging

logger = logging.getLogger("theracare.audit")


class PatientListSerializer(serializers.ModelSerializer):
    """Serializer for patient list."""

    primary_therapist_name = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            "id",
            "patient_number",
            "first_name",
            "last_name",
            "phone",
            "email",
            "date_of_birth",
            "gender",
            "status",
            "primary_therapist",
            "primary_therapist_name",
            "assigned_therapists",
            "admission_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "patient_number", "created_at", "updated_at"]

    def get_primary_therapist_name(self, obj):
        """Get primary therapist full name."""
        if obj.primary_therapist:
            return (
                f"{obj.primary_therapist.first_name} {obj.primary_therapist.last_name}"
            )
        return None


class PatientDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed patient view."""

    primary_therapist_info = UserListSerializer(
        source="primary_therapist", read_only=True
    )

    # Write fields (for create/update) - use _write suffix to avoid conflicts
    first_name_write = serializers.CharField(
        write_only=True, required=True, source="first_name"
    )
    last_name_write = serializers.CharField(
        write_only=True, required=True, source="last_name"
    )
    middle_name_write = serializers.CharField(
        write_only=True, required=False, allow_blank=True, source="middle_name"
    )
    email_write = serializers.EmailField(write_only=True, required=True, source="email")
    phone_write = serializers.CharField(
        write_only=True, required=False, allow_blank=True, source="phone"
    )
    phone_secondary_write = serializers.CharField(
        write_only=True, required=False, allow_blank=True, source="phone_secondary"
    )
    street_address_write = serializers.CharField(
        write_only=True, required=False, allow_blank=True, source="street_address"
    )
    city_write = serializers.CharField(
        write_only=True, required=False, allow_blank=True, source="city"
    )
    zip_code_write = serializers.CharField(
        write_only=True, required=False, allow_blank=True, source="zip_code"
    )
    ssn_write = serializers.CharField(
        write_only=True, required=False, allow_blank=True, source="ssn"
    )
    medical_record_number_write = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        source="medical_record_number",
    )
    emergency_contact_name_write = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        source="emergency_contact_name",
    )
    emergency_contact_phone_write = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        source="emergency_contact_phone",
    )
    emergency_contact_relationship_write = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        source="emergency_contact_relationship",
    )

    # Optional flag to enable portal access (auto-generates username/password)
    create_portal_access = serializers.BooleanField(
        write_only=True, required=False, default=True
    )

    class Meta:
        model = Patient
        fields = "__all__"
        read_only_fields = [
            "id",
            "patient_number",
            "created_at",
            "updated_at",
            "created_by",
        ]

    def get_fields(self):
        fields = super().get_fields()
        for field_name in ["first_name", "last_name", "email", "phone"]:
            if field_name in fields:
                fields[field_name].required = False
        return fields

    def validate(self, attrs):
        """Validate patient data before creation."""
        # Check if portal access requested and email will be unique
        create_portal = attrs.get("create_portal_access", True)
        email = attrs.get("email", "")

        if create_portal and email:
            # Check if email already exists in User table
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError(
                    {
                        "email": f'A user with email "{email}" already exists. Each patient must have a unique email address for portal access.'
                    }
                )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """Create patient and send token-based registration email for portal access."""
        # Check if portal access should be created (default: True)
        create_portal = validated_data.pop("create_portal_access", True)

        # Token-based flow creates user later when patient completes registration
        validated_data["user"] = None

        # Set created_by if available in context
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["created_by"] = request.user

        # Create patient
        patient = Patient.objects.create(**validated_data)

        # Send registration completion email (token-based)
        if create_portal:
            try:
                # Get email from the created patient instance
                email = patient.email
                first_name = patient.first_name
                last_name = patient.last_name

                success, token = send_registration_email(
                    email=email, first_name=first_name, last_name=last_name
                )

                if success:
                    logger.info(
                        f"Created patient {patient.patient_number}. Registration email sent to {email}"
                    )
                else:
                    logger.warning(
                        f"Created patient {patient.patient_number}, but registration email failed to send"
                    )
            except Exception as e:
                logger.error(
                    f"Failed to send registration email for patient {patient.patient_number}: {e}"
                )
        else:
            logger.info(
                f"Created patient {patient.patient_number} without portal access"
            )

        return patient

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update patient and optionally send registration email for portal access."""
        # Check if portal access should be created
        create_portal = validated_data.pop("create_portal_access", False)

        # Update existing user account
        if instance.user:
            email = validated_data.get("email")
            first_name = validated_data.get("first_name")
            last_name = validated_data.get("last_name")

            # Check if email is being changed and if new email already exists
            if email and email != instance.user.email:
                if (
                    User.objects.filter(email=email)
                    .exclude(id=instance.user.id)
                    .exists()
                ):
                    raise serializers.ValidationError(
                        {
                            "email": f'A user with email "{email}" already exists. Each patient must have a unique email address.'
                        }
                    )
                instance.user.email = email

            if first_name:
                instance.user.first_name = first_name
            if last_name:
                instance.user.last_name = last_name

            instance.user.save()
            logger.info(f"Updated user account for patient: {instance.user.username}")

        # Create portal access for existing patient if requested (token-based email)
        elif create_portal:
            email = validated_data.get("email", instance.email)
            first_name = validated_data.get("first_name", instance.first_name)
            last_name = validated_data.get("last_name", instance.last_name)

            try:
                success, _ = send_registration_email(
                    email=email, first_name=first_name, last_name=last_name
                )
                if success:
                    logger.info(
                        f"Registration email sent for existing patient {instance.patient_number}."
                    )
                else:
                    logger.warning(
                        f"Failed to send registration email for patient {instance.patient_number}."
                    )
            except Exception as e:
                logger.error(
                    f"Failed to send registration email for patient {instance.patient_number}: {e}"
                )

        # Update patient fields
        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()

        logger.info(f"Updated patient: {instance.patient_number}")

        return instance
