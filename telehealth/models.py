# backend/telehealth/models.py
"""
Telehealth models for TheraCare EHR System.
HIPAA-compliant telehealth session management.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class TelehealthSession(models.Model):
    """
    Telehealth session model for video consultations.
    """
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # Use AutoField since the existing table has an integer id
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Participants
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_sessions',
        null=True,
        blank=True
    )
    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='therapist_sessions'
    )
    
    # Scheduling
    scheduled_at = models.DateTimeField()
    duration = models.IntegerField(help_text="Duration in minutes", default=30)
    
    # Session details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    session_url = models.URLField(blank=True, null=True, help_text="Video call URL")
    room_id = models.CharField(max_length=255, blank=True, null=True, help_text="Video room ID")
    
    # Session content
    notes = models.TextField(blank=True, null=True, help_text="Session notes")
    has_recording = models.BooleanField(default=False)
    has_transcript = models.BooleanField(default=False)
    recording_url = models.URLField(blank=True, null=True)
    transcript_url = models.URLField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'telehealth_session'
        ordering = ['-scheduled_at']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['therapist', 'status']),
            models.Index(fields=['scheduled_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.scheduled_at}"

    @property
    def is_upcoming(self):
        """Check if session is upcoming."""
        return self.scheduled_at > timezone.now() and self.status == 'scheduled'

    @property
    def is_past(self):
        """Check if session is in the past."""
        return self.scheduled_at < timezone.now()

    @property
    def actual_duration(self):
        """Calculate actual session duration if started and ended."""
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            return int(delta.total_seconds() / 60)
        return None
