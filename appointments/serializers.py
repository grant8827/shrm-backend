from rest_framework import serializers
from .models import Appointment, AppointmentType
from users.models import User


class AppointmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentType
        fields = [
            'id', 'name', 'description', 'duration_minutes', 'color_code',
            'is_telehealth_enabled', 'requires_pre_auth', 'default_cost',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    therapist_name = serializers.SerializerMethodField()
    appointment_type_name = serializers.CharField(source='appointment_type.name', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'appointment_number', 'patient', 'patient_name',
            'therapist', 'therapist_name', 'appointment_type',
            'appointment_type_name', 'start_datetime', 'end_datetime',
            'timezone', 'status', 'priority', 'is_telehealth',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'appointment_number', 'created_at', 'updated_at']
    
    def get_patient_name(self, obj):
        return obj.patient.get_full_name() if obj.patient else None
    
    def get_therapist_name(self, obj):
        return obj.therapist.get_full_name() if obj.therapist else None


class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'patient', 'therapist', 'appointment_type',
            'start_datetime', 'end_datetime', 'timezone',
            'status', 'priority', 'is_telehealth'
        ]
    
    def validate(self, data):
        # Validate patient role
        patient = data.get('patient')
        if patient and patient.role != 'client':
            raise serializers.ValidationError({
                'patient': 'Selected user must have role "client"'
            })
        
        # Validate therapist role
        therapist = data.get('therapist')
        if therapist and therapist.role not in ['therapist', 'admin']:
            raise serializers.ValidationError({
                'therapist': 'Selected user must have role "therapist" or "admin"'
            })
        
        # Validate end_datetime is after start_datetime
        if data.get('end_datetime') and data.get('start_datetime'):
            if data['end_datetime'] <= data['start_datetime']:
                raise serializers.ValidationError({
                    'end_datetime': 'End time must be after start time'
                })
        
        return data


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'appointment_type', 'start_datetime', 'end_datetime',
            'timezone', 'status', 'priority', 'is_telehealth'
        ]
    
    def validate(self, data):
        # Validate end_datetime is after start_datetime
        start = data.get('start_datetime', self.instance.start_datetime)
        end = data.get('end_datetime', self.instance.end_datetime)
        
        if end and start and end <= start:
            raise serializers.ValidationError({
                'end_datetime': 'End time must be after start time'
            })
        
        return data
