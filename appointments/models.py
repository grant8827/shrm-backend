# backend/appointments/models.py
"""
Appointment scheduling and management models for TheraCare EHR System.
HIPAA-compliant appointment tracking with encryption for sensitive data.
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from core.security import encrypt_field, decrypt_field
import uuid
from datetime import timedelta


class AppointmentType(models.Model):
    """Defines types of appointments available in the system."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(15), MaxValueValidator(480)]
    )  # 15 minutes to 8 hours
    color_code = models.CharField(max_length=7, default='#007bff')  # Hex color
    is_telehealth_enabled = models.BooleanField(default=False)
    requires_pre_auth = models.BooleanField(default=False)
    default_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_appointment_types'
    )
    
    class Meta:
        db_table = 'appointment_types'
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.duration_minutes}min)"


class Appointment(models.Model):
    """Main appointment model with HIPAA-compliant encrypted fields."""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('in_session', 'In Session'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Core appointment details
    patient = models.ForeignKey(
        'users.User', 
        on_delete=models.CASCADE, 
        related_name='patient_appointments',
        limit_choices_to={'role': 'client'}
    )
    therapist = models.ForeignKey(
        'users.User', 
        on_delete=models.CASCADE, 
        related_name='therapist_appointments',
        limit_choices_to={'role__in': ['therapist', 'admin']}
    )
    appointment_type = models.ForeignKey(
        AppointmentType, 
        on_delete=models.CASCADE, 
        related_name='appointments'
    )
    
    # Scheduling information
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    timezone = models.CharField(max_length=50, default='America/New_York')
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Encrypted sensitive fields
    _notes = models.TextField(blank=True, null=True)  # Encrypted patient notes
    _chief_complaint = models.TextField(blank=True, null=True)  # Encrypted chief complaint
    _internal_notes = models.TextField(blank=True, null=True)  # Encrypted staff notes
    
    # Telehealth information
    is_telehealth = models.BooleanField(default=False)
    telehealth_room_id = models.CharField(max_length=100, blank=True, null=True)
    telehealth_link = models.URLField(blank=True, null=True)
    
    # Billing and insurance
    estimated_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    insurance_authorized = models.BooleanField(default=False)
    authorization_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Check-in/check-out information
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    # Cancellation/rescheduling
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='cancelled_appointments'
    )
    cancellation_reason = models.TextField(blank=True, null=True)
    rescheduled_from = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='rescheduled_to'
    )
    
    # Reminder settings
    send_reminders = models.BooleanField(default=True)
    reminder_sent_24h = models.BooleanField(default=False)
    reminder_sent_2h = models.BooleanField(default=False)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_appointments'
    )
    last_modified_by = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='modified_appointments'
    )
    
    class Meta:
        db_table = 'appointments'
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['patient', 'start_datetime']),
            models.Index(fields=['therapist', 'start_datetime']),
            models.Index(fields=['status', 'start_datetime']),
            models.Index(fields=['start_datetime', 'end_datetime']),
        ]
        
    def __str__(self):
        return f"{self.appointment_number} - {self.patient.get_display_name()} on {self.start_datetime.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Generate appointment number if not exists
        if not self.appointment_number:
            from django.utils.crypto import get_random_string
            timestamp = timezone.now().strftime('%Y%m%d')
            random_part = get_random_string(6, allowed_chars='0123456789')
            self.appointment_number = f"APT-{timestamp}-{random_part}"
        
        # Set end_datetime based on appointment type duration if not set
        if not self.end_datetime and self.start_datetime and self.appointment_type:
            self.end_datetime = self.start_datetime + timedelta(
                minutes=self.appointment_type.duration_minutes
            )
        
        super().save(*args, **kwargs)
    
    # Encrypted field properties
    @property
    def notes(self):
        return decrypt_field(self._notes) if self._notes else ''
    
    @notes.setter
    def notes(self, value):
        self._notes = encrypt_field(value) if value else None
    
    @property
    def chief_complaint(self):
        return decrypt_field(self._chief_complaint) if self._chief_complaint else ''
    
    @chief_complaint.setter
    def chief_complaint(self, value):
        self._chief_complaint = encrypt_field(value) if value else None
    
    @property
    def internal_notes(self):
        return decrypt_field(self._internal_notes) if self._internal_notes else ''
    
    @internal_notes.setter
    def internal_notes(self, value):
        self._internal_notes = encrypt_field(value) if value else None
    
    def get_duration(self):
        """Calculate actual appointment duration."""
        if self.actual_start_time and self.actual_end_time:
            return self.actual_end_time - self.actual_start_time
        return self.end_datetime - self.start_datetime
    
    def is_past_due(self):
        """Check if appointment is past its scheduled time."""
        return timezone.now() > self.end_datetime
    
    def can_be_cancelled(self):
        """Check if appointment can still be cancelled."""
        return self.status in ['scheduled', 'confirmed'] and not self.is_past_due()
    
    def can_be_rescheduled(self):
        """Check if appointment can be rescheduled."""
        return self.status in ['scheduled', 'confirmed', 'cancelled']


class AppointmentReminder(models.Model):
    """Tracks appointment reminders sent to patients."""
    
    REMINDER_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('phone', 'Phone Call'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.ForeignKey(
        Appointment, 
        on_delete=models.CASCADE, 
        related_name='reminders'
    )
    reminder_type = models.CharField(max_length=10, choices=REMINDER_TYPES)
    hours_before = models.PositiveIntegerField()  # Hours before appointment
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Message content (encrypted)
    _message_content = models.TextField(blank=True, null=True)
    
    # Delivery tracking
    delivery_id = models.CharField(max_length=100, blank=True, null=True)  # External service ID
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'appointment_reminders'
        ordering = ['scheduled_for']
        unique_together = ['appointment', 'reminder_type', 'hours_before']
    
    def __str__(self):
        return f"{self.get_reminder_type_display()} reminder for {self.appointment.appointment_number}"
    
    @property
    def message_content(self):
        return decrypt_field(self._message_content) if self._message_content else ''
    
    @message_content.setter
    def message_content(self, value):
        self._message_content = encrypt_field(value) if value else None


class RecurringAppointment(models.Model):
    """Manages recurring appointment patterns."""
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom Pattern'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Pattern definition
    patient = models.ForeignKey(
        'patients.Patient', 
        on_delete=models.CASCADE, 
        related_name='recurring_appointments'
    )
    therapist = models.ForeignKey(
        'users.User', 
        on_delete=models.CASCADE, 
        related_name='recurring_therapist_appointments'
    )
    appointment_type = models.ForeignKey(
        AppointmentType, 
        on_delete=models.CASCADE
    )
    
    # Recurrence pattern
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    interval_value = models.PositiveIntegerField(default=1)  # Every X weeks/months
    days_of_week = models.CharField(max_length=20, blank=True)  # Comma-separated: 0=Mon, 6=Sun
    
    # Schedule boundaries
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    max_occurrences = models.PositiveIntegerField(null=True, blank=True)
    
    # Time information
    start_time = models.TimeField()
    timezone = models.CharField(max_length=50, default='America/New_York')
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    occurrences_created = models.PositiveIntegerField(default=0)
    last_generated_date = models.DateField(null=True, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_recurring_appointments'
    )
    
    class Meta:
        db_table = 'recurring_appointments'
        ordering = ['start_date', 'start_time']
    
    def __str__(self):
        return f"Recurring: {self.patient.get_display_name()} - {self.get_frequency_display()}"
    
    def generate_next_occurrences(self, days_ahead=30):
        """Generate appointment instances for the next specified days."""
        from datetime import date, datetime, timedelta
        import calendar
        
        if self.status != 'active':
            return []
        
        today = date.today()
        end_generate = today + timedelta(days=days_ahead)
        
        # Don't generate past the end date if set
        if self.end_date and end_generate > self.end_date:
            end_generate = self.end_date
        
        # Start from last generated date or start date
        current_date = self.last_generated_date + timedelta(days=1) if self.last_generated_date else self.start_date
        
        if current_date > end_generate:
            return []
        
        appointments_to_create = []
        
        while current_date <= end_generate:
            # Check max occurrences limit
            if self.max_occurrences and self.occurrences_created >= self.max_occurrences:
                break
            
            should_create = False
            
            if self.frequency == 'daily':
                should_create = True
            elif self.frequency == 'weekly':
                if str(current_date.weekday()) in self.days_of_week.split(','):
                    should_create = True
            elif self.frequency == 'biweekly':
                weeks_since_start = (current_date - self.start_date).days // 7
                if weeks_since_start % 2 == 0 and str(current_date.weekday()) in self.days_of_week.split(','):
                    should_create = True
            elif self.frequency == 'monthly':
                if current_date.day == self.start_date.day:
                    should_create = True
            
            if should_create:
                # Create datetime object
                start_datetime = datetime.combine(current_date, self.start_time)
                
                # Check for conflicts before creating
                conflicts = Appointment.objects.filter(
                    therapist=self.therapist,
                    start_datetime__date=current_date,
                    start_datetime__time=self.start_time,
                    status__in=['scheduled', 'confirmed', 'in_session']
                ).exists()
                
                if not conflicts:
                    appointments_to_create.append({
                        'patient': self.patient,
                        'therapist': self.therapist,
                        'appointment_type': self.appointment_type,
                        'start_datetime': start_datetime,
                        'recurring_appointment': self
                    })
            
            current_date += timedelta(days=1)
        
        return appointments_to_create