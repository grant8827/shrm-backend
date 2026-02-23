"""
SOAP Notes models for TheraCare EHR System.
"""

from django.db import models
from django.conf import settings
import uuid


class SOAPNote(models.Model):
    """
    SOAP (Subjective, Objective, Assessment, Plan) Note model.
    Standard medical documentation format.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="soap_notes_as_patient",
        limit_choices_to={"role": "client"},
    )
    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="soap_notes_as_therapist",
        limit_choices_to={"role__in": ["therapist", "admin"]},
    )
    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="soap_notes",
    )

    # SOAP Components
    subjective = models.TextField(
        help_text="Patient's description of their condition, symptoms, feelings"
    )
    objective = models.TextField(
        help_text="Observable, measurable data (vital signs, test results, observations)"
    )
    assessment = models.TextField(
        help_text="Professional diagnosis or clinical impression"
    )
    plan = models.TextField(
        help_text="Treatment plan, interventions, follow-up actions"
    )

    # Additional Information
    session_date = models.DateTimeField()
    session_duration = models.IntegerField(
        help_text="Duration in minutes", null=True, blank=True
    )
    chief_complaint = models.CharField(max_length=500, blank=True)

    # Status
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("finalized", "Finalized"),
        ("amended", "Amended"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finalized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "soap_notes"
        ordering = ["-session_date"]
        indexes = [
            models.Index(fields=["patient", "session_date"]),
            models.Index(fields=["therapist", "session_date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return (
            f"SOAP Note - {self.patient.get_full_name()} - {self.session_date.date()}"
        )
