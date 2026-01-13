from django.db import models
from django.core.validators import RegexValidator
from core.security import encryption
from users.models import User
import uuid


class Patient(models.Model):
    """Patient model with HIPAA-compliant encrypted fields"""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        DISCHARGED = 'discharged', 'Discharged'
        DECEASED = 'deceased', 'Deceased'
    
    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'
        PREFER_NOT_TO_SAY = 'P', 'Prefer not to say'
    
    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_number = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Link to user account (if patient has portal access)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='patient_profile')
    
    # Personal information (encrypted)
    first_name = models.TextField(max_length=500, help_text="Encrypted field")
    last_name = models.TextField(max_length=500, help_text="Encrypted field")
    middle_name = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=Gender.choices)
    
    # Contact information (encrypted)
    email = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    phone = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    phone_secondary = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    
    # Address (encrypted)
    street_address = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    city = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    state = models.CharField(max_length=2, blank=True)
    zip_code = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    country = models.CharField(max_length=2, default='US')
    
    # Medical identifiers (encrypted)
    ssn = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    medical_record_number = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    
    # Emergency contact (encrypted)
    emergency_contact_name = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    emergency_contact_phone = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    emergency_contact_relationship = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    
    # Care team
    primary_therapist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_patients')
    assigned_therapists = models.ManyToManyField(User, through='PatientTherapistAssignment', related_name='assigned_patients')
    
    # Status and administrative
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    admission_date = models.DateField()
    discharge_date = models.DateField(null=True, blank=True)
    
    # Medical information
    allergies = models.TextField(blank=True, help_text="List of known allergies")
    medical_conditions = models.TextField(blank=True, help_text="Current medical conditions")
    medications = models.TextField(blank=True, help_text="Current medications")
    
    # Preferences
    preferred_language = models.CharField(max_length=10, default='en')
    communication_preferences = models.JSONField(default=dict, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_patients')
    
    class Meta:
        db_table = 'patients'
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
        indexes = [
            models.Index(fields=['patient_number']),
            models.Index(fields=['status']),
            models.Index(fields=['primary_therapist']),
            models.Index(fields=['admission_date']),
        ]
        permissions = [
            ('view_patient_phi', 'Can view patient PHI'),
            ('edit_patient_phi', 'Can edit patient PHI'),
            ('delete_patient_phi', 'Can delete patient PHI'),
        ]
    
    def save(self, *args, **kwargs):
        """Override save to encrypt sensitive fields and generate patient number"""
        if not self.patient_number:
            self.patient_number = self.generate_patient_number()
        
        # Encrypt sensitive fields
        fields_to_encrypt = [
            'first_name', 'last_name', 'middle_name', 'email', 'phone', 'phone_secondary',
            'street_address', 'city', 'zip_code', 'ssn', 'medical_record_number',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'
        ]
        
        for field in fields_to_encrypt:
            value = getattr(self, field, None)
            if value and not value.startswith('gAAAAAB'):  # Not already encrypted
                setattr(self, field, encryption.encrypt(value))
        
        super().save(*args, **kwargs)
    
    def generate_patient_number(self):
        """Generate unique patient number"""
        import datetime
        today = datetime.date.today()
        year_suffix = str(today.year)[-2:]
        
        # Get the last patient number for today
        last_patient = Patient.objects.filter(
            patient_number__startswith=f'P{year_suffix}'
        ).order_by('patient_number').last()
        
        if last_patient:
            last_num = int(last_patient.patient_number[3:])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f'P{year_suffix}{new_num:06d}'
    
    def get_decrypted_field(self, field_name):
        """Get decrypted field value"""
        try:
            value = getattr(self, field_name, '')
            return encryption.decrypt(value) if value else ''
        except:
            return getattr(self, field_name, '')
    
    def get_full_name(self):
        """Get full name (decrypted)"""
        first = self.get_decrypted_field('first_name')
        middle = self.get_decrypted_field('middle_name')
        last = self.get_decrypted_field('last_name')
        
        parts = [first]
        if middle:
            parts.append(middle)
        parts.append(last)
        
        return ' '.join(parts).strip()
    
    def get_age(self):
        """Calculate current age"""
        import datetime
        today = datetime.date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def __str__(self):
        return f"{self.patient_number} - {self.get_full_name()}"


class PatientTherapistAssignment(models.Model):
    """Through model for patient-therapist relationships"""
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    therapist = models.ForeignKey(User, on_delete=models.CASCADE)
    assigned_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'patient_therapist_assignments'
        unique_together = ['patient', 'therapist', 'assigned_date']
        indexes = [
            models.Index(fields=['patient', 'is_primary']),
            models.Index(fields=['therapist', 'assigned_date']),
        ]
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.therapist.get_full_name()}"


class InsuranceInformation(models.Model):
    """Patient insurance information"""
    
    class InsuranceType(models.TextChoices):
        PRIMARY = 'primary', 'Primary Insurance'
        SECONDARY = 'secondary', 'Secondary Insurance'
        TERTIARY = 'tertiary', 'Tertiary Insurance'
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='insurance_plans')
    insurance_type = models.CharField(max_length=20, choices=InsuranceType.choices, default=InsuranceType.PRIMARY)
    
    # Insurance details (encrypted)
    provider_name = models.TextField(max_length=500, help_text="Encrypted field")
    policy_number = models.TextField(max_length=500, help_text="Encrypted field")
    group_number = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    subscriber_id = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    
    # Subscriber information (encrypted)
    subscriber_name = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    subscriber_dob = models.DateField(null=True, blank=True)
    relationship_to_patient = models.CharField(max_length=20, default='self')
    
    # Coverage details
    effective_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)
    copay_amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    deductible_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    verification_date = models.DateField(null=True, blank=True)
    verification_status = models.CharField(max_length=20, default='pending')
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patient_insurance'
        verbose_name = 'Insurance Information'
        verbose_name_plural = 'Insurance Information'
        indexes = [
            models.Index(fields=['patient', 'insurance_type']),
            models.Index(fields=['is_active']),
        ]
    
    def save(self, *args, **kwargs):
        """Override save to encrypt sensitive fields"""
        fields_to_encrypt = [
            'provider_name', 'policy_number', 'group_number', 
            'subscriber_id', 'subscriber_name'
        ]
        
        for field in fields_to_encrypt:
            value = getattr(self, field, None)
            if value and not value.startswith('gAAAAAB'):  # Not already encrypted
                setattr(self, field, encryption.encrypt(value))
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        provider = self.get_decrypted_field('provider_name')
        return f"{self.patient.get_full_name()} - {provider} ({self.insurance_type})"
    
    def get_decrypted_field(self, field_name):
        """Get decrypted field value"""
        try:
            value = getattr(self, field_name, '')
            return encryption.decrypt(value) if value else ''
        except:
            return getattr(self, field_name, '')


class PatientDocument(models.Model):
    """Patient documents and files"""
    
    class DocumentType(models.TextChoices):
        INTAKE_FORM = 'intake', 'Intake Form'
        CONSENT = 'consent', 'Consent Form'
        INSURANCE_CARD = 'insurance', 'Insurance Card'
        ID_VERIFICATION = 'id', 'ID Verification'
        MEDICAL_RECORDS = 'medical', 'Medical Records'
        LAB_RESULTS = 'lab', 'Lab Results'
        OTHER = 'other', 'Other'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='documents')
    
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # File information
    file = models.FileField(upload_to='patient_documents/')
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=255)
    is_encrypted = models.BooleanField(default=True)
    
    # Access control
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    requires_signature = models.BooleanField(default=False)
    is_signed = models.BooleanField(default=False)
    signed_date = models.DateTimeField(null=True, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patient_documents'
        verbose_name = 'Patient Document'
        verbose_name_plural = 'Patient Documents'
        indexes = [
            models.Index(fields=['patient', 'document_type']),
            models.Index(fields=['is_active']),
        ]
        permissions = [
            ('view_patient_documents', 'Can view patient documents'),
            ('upload_patient_documents', 'Can upload patient documents'),
            ('delete_patient_documents', 'Can delete patient documents'),
        ]
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.title}"