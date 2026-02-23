#!/usr/bin/env python3
"""
Check all patients in database
"""
import os
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theracare.settings")
django.setup()

from patients.models import Patient


def check_patients():
    """Display all patients"""
    patients = Patient.objects.all().order_by("-created_at")

    print(f"\n{'='*80}")
    print(f"TOTAL PATIENTS IN DATABASE: {patients.count()}")
    print(f"{'='*80}\n")

    if patients.count() == 0:
        print("❌ No patients found in database!")
        return

    for i, patient in enumerate(patients, 1):
        print(f"{i}. Patient Number: {patient.patient_number}")
        print(
            f"   Name: {patient.get_decrypted_field('first_name')} {patient.get_decrypted_field('last_name')}"
        )
        print(f"   Email: {patient.get_decrypted_field('email')}")
        print(f"   Status: {patient.status}")
        print(f"   Created: {patient.created_at}")
        print(f"   Portal Access: {bool(patient.user)}")
        if patient.user:
            print(f"   Username: {patient.user.username}")
        print(f"   {'-'*76}")


if __name__ == "__main__":
    check_patients()
