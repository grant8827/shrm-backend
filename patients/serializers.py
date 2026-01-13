"""
Patient serializers for TheraCare EHR System.
Handles decryption of PHI fields for API responses.
"""

from rest_framework import serializers
from .models import Patient
from users.serializers import UserListSerializer


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
