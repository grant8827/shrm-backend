#!/usr/bin/env python3
"""
Send registration email for existing patient
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theracare.settings')
django.setup()

from patients.models import Patient
from users.email_service import send_registration_email
import logging

logger = logging.getLogger('theracare.audit')

def send_patient_registration_email(patient_number):
    """Send registration email for a specific patient"""
    
    try:
        # Get the patient
        patient = Patient.objects.get(patient_number=patient_number)
        print(f"Found patient: {patient_number}")
        
        # Decrypt patient data
        first_name = patient.get_decrypted_field('first_name')
        last_name = patient.get_decrypted_field('last_name')
        email = patient.get_decrypted_field('email')
        phone = patient.get_decrypted_field('phone') or ''
        
        print(f"Patient: {first_name} {last_name}")
        print(f"Email: {email}")
        print(f"\nSending registration email...")
        
        # Send the email
        send_registration_email(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone
        )
        
        print(f"✅ Registration email sent successfully to {email}!")
        print(f"\nThe patient will receive:")
        print(f"  - A registration completion link")  
        print(f"  - Link expires in 7 days")
        print(f"  - Patient can create their own password")
        print(f"\n📧 Check inbox at: {email}")
        print(f"📧 Check spam/junk folder if not in inbox")
        
    except Patient.DoesNotExist:
        print(f"❌ Patient {patient_number} not found!")
        print("\nAvailable patients:")
        for p in Patient.objects.all()[:10]:
            print(f"  - {p.patient_number}: {p.get_decrypted_field('first_name')} {p.get_decrypted_field('last_name')}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Send email for the recently created patient
    patient_number = 'P26000005'  # The patient created earlier
    send_patient_registration_email(patient_number)
