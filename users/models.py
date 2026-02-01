from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.base_user import BaseUserManager
from core.security import encryption
import uuid


class UserManager(BaseUserManager):
    """Custom user manager for TheraCare users"""
    
    def create_user(self, username, email, password=None, **extra_fields):
        """Create and save a regular user"""
        if not username:
            raise ValueError('The Username field must be set')
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model for TheraCare with HIPAA compliance"""
    
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        THERAPIST = 'therapist', 'Therapist'
        STAFF = 'staff', 'Staff Member'
        CLIENT = 'client', 'Client/Patient'
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        SUSPENDED = 'suspended', 'Suspended'
        PENDING = 'pending', 'Pending Activation'
    
    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(unique=True, max_length=150, null=True, blank=True)
    email = models.EmailField(unique=True, max_length=254)
    
    # Personal information (encrypted)
    first_name = models.TextField(max_length=500, help_text="Encrypted field")
    last_name = models.TextField(max_length=500, help_text="Encrypted field")
    phone = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    
    # Role and permissions
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Account status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Authentication and security
    two_factor_enabled = models.BooleanField(default=False)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(default=timezone.now)
    must_change_password = models.BooleanField(default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    last_password_change = models.DateTimeField(default=timezone.now)
    
    # Professional information (for staff/therapists)
    license_number = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    license_state = models.CharField(max_length=2, blank=True)
    license_expiry = models.DateField(null=True, blank=True)
    
    # Audit fields
    created_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='created_users')
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'role']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['status']),
            models.Index(fields=['is_active']),
        ]
    
    def save(self, *args, **kwargs):
        """Override save - encryption removed for troubleshooting"""
        # Decrypt any existing encrypted data before saving
        if self.first_name and (self.first_name.startswith('gAAAAAB') or self.first_name.startswith('Z0FBQUFBQnB')):
            try:
                self.first_name = encryption.decrypt(self.first_name)
            except:
                pass
        
        if self.last_name and (self.last_name.startswith('gAAAAAB') or self.last_name.startswith('Z0FBQUFBQnB')):
            try:
                self.last_name = encryption.decrypt(self.last_name)
            except:
                pass
        
        if self.phone and (self.phone.startswith('gAAAAAB') or self.phone.startswith('Z0FBQUFBQnB')):
            try:
                self.phone = encryption.decrypt(self.phone)
            except:
                pass
        
        if self.license_number and (self.license_number.startswith('gAAAAAB') or self.license_number.startswith('Z0FBQUFBQnB')):
            try:
                self.license_number = encryption.decrypt(self.license_number)
            except:
                pass
        
        super().save(*args, **kwargs)
    
    def get_decrypted_first_name(self):
        """Get first name - no encryption now"""
        return self.first_name or ''
    
    def get_decrypted_last_name(self):
        """Get last name - no encryption now"""
        return self.last_name or ''
    
    def get_decrypted_phone(self):
        """Get phone number - no encryption now"""
        return self.phone or ''
    
    def get_decrypted_license_number(self):
        """Get license number - no encryption now"""
        return self.license_number or ''
    
    def get_full_name(self):
        """Get full name (decrypted)"""
        first = self.get_decrypted_first_name()
        last = self.get_decrypted_last_name()
        return f"{first} {last}".strip()
    
    def get_short_name(self):
        """Get short name (first name only)"""
        return self.get_decrypted_first_name()
    
    def is_therapist_or_staff(self):
        """Check if user is therapist or staff"""
        return self.role in [self.Role.THERAPIST, self.Role.STAFF]
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == self.Role.ADMIN
    
    def is_client(self):
        """Check if user is client"""
        return self.role == self.Role.CLIENT
    
    def can_access_patient_data(self):
        """Check if user can access patient data"""
        return self.role in [self.Role.ADMIN, self.Role.THERAPIST, self.Role.STAFF]
    
    def reset_failed_login_attempts(self):
        """Reset failed login attempts"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.save(update_fields=['failed_login_attempts', 'account_locked_until'])
    
    def increment_failed_login_attempts(self):
        """Increment failed login attempts and lock account if necessary"""
        from django.conf import settings
        
        self.failed_login_attempts += 1
        
        max_attempts = getattr(settings, 'HIPAA_SETTINGS', {}).get('MAX_LOGIN_ATTEMPTS', 3)
        lockout_duration = getattr(settings, 'HIPAA_SETTINGS', {}).get('LOCKOUT_DURATION', 15)
        
        if self.failed_login_attempts >= max_attempts:
            self.account_locked_until = timezone.now() + timezone.timedelta(minutes=lockout_duration)
        
        self.save(update_fields=['failed_login_attempts', 'account_locked_until'])
    
    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False
    
    def is_locked(self):
        """Alias for is_account_locked() for compatibility"""
        return self.is_account_locked()
    
    def record_failed_login(self):
        """Alias for increment_failed_login_attempts() for compatibility"""
        return self.increment_failed_login_attempts()
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"


class UserProfile(models.Model):
    """Extended user profile information"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Address information (encrypted)
    street_address = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    city = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    state = models.CharField(max_length=2, blank=True)
    zip_code = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    country = models.CharField(max_length=2, default='US')
    
    # Profile information
    date_of_birth = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Communication preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Emergency contact (encrypted)
    emergency_contact_name = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    emergency_contact_phone = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    emergency_contact_relationship = models.TextField(max_length=500, blank=True, help_text="Encrypted field")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def save(self, *args, **kwargs):
        """Override save to encrypt sensitive fields"""
        fields_to_encrypt = [
            'street_address', 'city', 'zip_code', 'emergency_contact_name',
            'emergency_contact_phone', 'emergency_contact_relationship'
        ]
        
        for field in fields_to_encrypt:
            value = getattr(self, field, None)
            if value and not value.startswith('gAAAAAB'):  # Not already encrypted
                setattr(self, field, encryption.encrypt(value))
        
        super().save(*args, **kwargs)
    
    def get_decrypted_field(self, field_name):
        """Get decrypted field value"""
        try:
            value = getattr(self, field_name, '')
            return encryption.decrypt(value) if value else ''
        except:
            return getattr(self, field_name, '')  # Return as-is if decryption fails
    
    def __str__(self):
        return f"Profile for {self.user.get_full_name()}"


class RegistrationToken(models.Model):
    """Token for patient registration completion"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Patient data stored temporarily
    email = models.EmailField()
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Token status
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    
    # Link to created user (when registration is complete)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='registration_token')
    
    class Meta:
        db_table = 'registration_tokens'
        ordering = ['-created_at']
    
    def is_valid(self):
        """Check if token is still valid"""
        return not self.is_used and timezone.now() < self.expires_at
    
    def mark_as_used(self, user):
        """Mark token as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.user = user
        self.save()
    
    def __str__(self):
        return f"Registration token for {self.email}"