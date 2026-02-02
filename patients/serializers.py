"""
Patient serializers for TheraCare EHR System.
Handles decryption of PHI fields for API responses.
"""

from rest_framework import serializers
from .models import Patient
from users.serializers import UserListSerializer
from users.models import User
from django.db import transaction
from .services import PatientRegistrationService
import logging

logger = logging.getLogger('theracare.audit')


class PatientListSerializer(serializers.ModelSerializer):
    """Serializer for patient list with decrypted fields."""
    
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    primary_therapist_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = [
            'id',
            'patient_number',
            'first_name',
            'last_name',
            'phone',
            'email',
            'date_of_birth',
            'gender',
            'status',
            'primary_therapist',
            'primary_therapist_name',
            'assigned_therapists',
            'admission_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'patient_number', 'created_at', 'updated_at']
    
    def get_first_name(self, obj):
        """Decrypt first name."""
        return obj.get_decrypted_field('first_name')
    
    def get_last_name(self, obj):
        """Decrypt last name."""
        return obj.get_decrypted_field('last_name')
    
    def get_phone(self, obj):
        """Decrypt phone."""
        return obj.get_decrypted_field('phone')
    
    def get_email(self, obj):
        """Decrypt email."""
        return obj.get_decrypted_field('email')
    
    def get_primary_therapist_name(self, obj):
        """Get primary therapist full name."""
        if obj.primary_therapist:
            return f"{obj.primary_therapist.first_name} {obj.primary_therapist.last_name}"
        return None


class PatientDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed patient view with all decrypted fields."""
    
    # Read fields (decrypted)
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    middle_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    phone_secondary = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    street_address = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    zip_code = serializers.SerializerMethodField()
    ssn = serializers.SerializerMethodField()
    medical_record_number = serializers.SerializerMethodField()
    emergency_contact_name = serializers.SerializerMethodField()
    emergency_contact_phone = serializers.SerializerMethodField()
    emergency_contact_relationship = serializers.SerializerMethodField()
    primary_therapist_info = UserListSerializer(source='primary_therapist', read_only=True)
    
    # Write fields (for create/update)
    first_name_write = serializers.CharField(write_only=True, required=True, source='first_name')
    last_name_write = serializers.CharField(write_only=True, required=True, source='last_name')
    middle_name_write = serializers.CharField(write_only=True, required=False, allow_blank=True, source='middle_name')
    email_write = serializers.EmailField(write_only=True, required=True, source='email')
    phone_write = serializers.CharField(write_only=True, required=False, allow_blank=True, source='phone')
    phone_secondary_write = serializers.CharField(write_only=True, required=False, allow_blank=True, source='phone_secondary')
    street_address_write = serializers.CharField(write_only=True, required=False, allow_blank=True, source='street_address')
    city_write = serializers.CharField(write_only=True, required=False, allow_blank=True, source='city')
    zip_code_write = serializers.CharField(write_only=True, required=False, allow_blank=True, source='zip_code')
    ssn_write = serializers.CharField(write_only=True, required=False, allow_blank=True, source='ssn')
    medical_record_number_write = serializers.CharField(write_only=True, required=False, allow_blank=True, source='medical_record_number')
    emergency_contact_name_write = serializers.CharField(write_only=True, required=False, allow_blank=True, source='emergency_contact_name')
    emergency_contact_phone_write = serializers.CharField(write_only=True, required=False, allow_blank=True, source='emergency_contact_phone')
    emergency_contact_relationship_write = serializers.CharField(write_only=True, required=False, allow_blank=True, source='emergency_contact_relationship')
    
    # Optional flag to enable portal access (auto-generates username/password)
    create_portal_access = serializers.BooleanField(write_only=True, required=False, default=True)
    
    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ['id', 'patient_number', 'created_at', 'updated_at', 'created_by']
    
    def get_first_name(self, obj):
        return obj.get_decrypted_field('first_name')
    
    def get_last_name(self, obj):
        return obj.get_decrypted_field('last_name')
    
    def get_middle_name(self, obj):
        return obj.get_decrypted_field('middle_name')
    
    def get_phone(self, obj):
        return obj.get_decrypted_field('phone')
    
    def get_phone_secondary(self, obj):
        return obj.get_decrypted_field('phone_secondary')
    
    def get_email(self, obj):
        return obj.get_decrypted_field('email')
    
    def get_street_address(self, obj):
        return obj.get_decrypted_field('street_address')
    
    def get_city(self, obj):
        return obj.get_decrypted_field('city')
    
    def get_zip_code(self, obj):
        return obj.get_decrypted_field('zip_code')
    
    def get_ssn(self, obj):
        return obj.get_decrypted_field('ssn')
    
    def get_medical_record_number(self, obj):
        return obj.get_decrypted_field('medical_record_number')
    
    def get_emergency_contact_name(self, obj):
        return obj.get_decrypted_field('emergency_contact_name')
    
    def get_emergency_contact_phone(self, obj):
        return obj.get_decrypted_field('emergency_contact_phone')
    
    def get_emergency_contact_relationship(self, obj):
        return obj.get_decrypted_field('emergency_contact_relationship')
    
    @transaction.atomic
    def create(self, validated_data):
        """Create patient and automatically create portal access with welcome email."""
        # Check if portal access should be created (default: True)
        create_portal = validated_data.pop('create_portal_access', True)
        
        user = None
        username = None
        temp_password = None
        
        # Auto-generate user account credentials if portal access requested
        if create_portal:
            user, username, temp_password = PatientRegistrationService.create_user_account(validated_data)
        
        # Link user to patient
        validated_data['user'] = user
        
        # Set created_by if available in context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        
        # Create patient
        patient = Patient.objects.create(**validated_data)
        
        # Send welcome email with credentials (only if user was created)
        if user and username and temp_password:
            email_sent = PatientRegistrationService.send_welcome_email(patient, username, temp_password)
            if email_sent:
                logger.info(f'Created patient {patient.patient_number} with portal access. Welcome email sent to {username}')
            else:
                logger.warning(f'Created patient {patient.patient_number} with portal access, but welcome email failed to send')
        else:
            logger.info(f'Created patient {patient.patient_number} without portal access')
        
        return patient
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """Update patient and sync user account if exists, or create portal access if requested."""
        # Check if portal access should be created
        create_portal = validated_data.pop('create_portal_access', False)
        
        # Update existing user account
        if instance.user:
            email = validated_data.get('email')
            first_name = validated_data.get('first_name')
            last_name = validated_data.get('last_name')
            
            if email:
                instance.user.email = email
            if first_name:
                instance.user.first_name = first_name
            if last_name:
                instance.user.last_name = last_name
            
            instance.user.save()
            logger.info(f'Updated user account for patient: {instance.user.username}')
        
        # Create portal access for existing patient if requested
        elif create_portal:
            user, username, temp_password = PatientRegistrationService.create_user_account(validated_data, instance)
            if user:
                instance.user = user
                # Send welcome email
                email_sent = PatientRegistrationService.send_welcome_email(instance, username, temp_password)
                if email_sent:
                    logger.info(f'Added portal access for existing patient {instance.patient_number}. Welcome email sent.')
                else:
                    logger.warning(f'Added portal access for patient {instance.patient_number}, but email failed to send')
        
        # Update patient fields
        for field, value in validated_data.items():
            setattr(instance, field, value)
        
        instance.save()
        
        logger.info(f'Updated patient: {instance.patient_number}')
        
        return instance
