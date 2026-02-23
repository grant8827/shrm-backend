#!/usr/bin/env python3
"""
Delete all existing patients with encrypted data.
This allows starting fresh with the new non-encrypted Patient model.
"""

import os
import sys
import django

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theracare.settings")
django.setup()

from patients.models import Patient
from django.contrib.auth import get_user_model

User = get_user_model()


def delete_all_patients():
    """Delete all patients and their associated user accounts."""

    print("\n" + "=" * 60)
    print("DELETING ALL PATIENTS WITH ENCRYPTED DATA")
    print("=" * 60 + "\n")

    # Get all patients
    patients = Patient.objects.all()
    patient_count = patients.count()

    print(f"Found {patient_count} patients to delete:\n")

    # Track user accounts to delete
    user_ids_to_delete = []

    for patient in patients:
        print(f"  • Patient Number: {patient.patient_number}")
        if patient.user:
            user_ids_to_delete.append(patient.user.id)
            print(f"    Associated User: {patient.user.username}")

    print(f"\n{'─'*60}\n")

    # Delete patients
    deleted_patients, _ = Patient.objects.all().delete()
    print(f"✅ Deleted {deleted_patients} patient record(s)")

    # Delete associated user accounts
    if user_ids_to_delete:
        deleted_users = User.objects.filter(id__in=user_ids_to_delete).delete()[0]
        print(f"✅ Deleted {deleted_users} associated user account(s)")

    print(f"\n{'─'*60}\n")
    print("✅ CLEANUP COMPLETE - Ready for fresh patient data")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        delete_all_patients()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
