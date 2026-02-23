#!/usr/bin/env python
"""
Create a test patient for billing system testing.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theracare.settings")
django.setup()

from patients.models import Patient
from users.models import User
from django.utils import timezone
from datetime import date

# Get or create a therapist/admin user
admin_user = (
    User.objects.filter(role="admin").first()
    or User.objects.filter(role="therapist").first()
)

if not admin_user:
    print("❌ No admin or therapist user found. Please create one first.")
    exit(1)

# Create test patients
test_patients = [
    {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "555-0101",
        "date_of_birth": date(1985, 5, 15),
        "gender": "M",
        "status": "active",
    },
    {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "phone": "555-0102",
        "date_of_birth": date(1990, 8, 22),
        "gender": "F",
        "status": "active",
    },
    {
        "first_name": "Robert",
        "last_name": "Johnson",
        "email": "robert.johnson@example.com",
        "phone": "555-0103",
        "date_of_birth": date(1978, 12, 10),
        "gender": "M",
        "status": "active",
    },
]

print("Creating test patients...")
created = 0

for patient_data in test_patients:
    # Check if patient already exists by patient number or name
    email = patient_data["email"]

    existing = Patient.objects.filter(email=email).first()

    if existing:
        print(
            f"✓ Patient already exists: {patient_data['first_name']} {patient_data['last_name']}"
        )
        continue

    # Create patient
    patient = Patient.objects.create(
        first_name=patient_data["first_name"],
        last_name=patient_data["last_name"],
        email=patient_data["email"],
        phone=patient_data["phone"],
        date_of_birth=patient_data["date_of_birth"],
        gender=patient_data["gender"],
        status=patient_data["status"],
        primary_therapist=admin_user,
        admission_date=timezone.now().date(),
        created_by=admin_user,
    )

    print(
        f"✓ Created patient: {patient_data['first_name']} {patient_data['last_name']} (#{patient.patient_number})"
    )
    created += 1

print(f"\n✅ Done! Created {created} new patients.")
print(f"Total active patients: {Patient.objects.filter(status='active').count()}")
