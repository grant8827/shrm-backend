#!/usr/bin/env python3
"""
Decrypt all encrypted patient data before removing encryption from model
WARNING: This will permanently decrypt all patient data in the database
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theracare.settings')
django.setup()

from patients.models import Patient
from core.security import encryption

def decrypt_all_patients():
    """Decrypt all encrypted fields in all patient records"""
    
    fields_to_decrypt = [
        'first_name', 'last_name', 'middle_name', 'email', 'phone', 'phone_secondary',
        'street_address', 'city', 'zip_code', 'ssn', 'medical_record_number',
        'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'
    ]
    
    patients = Patient.objects.all()
    total = patients.count()
    
    print(f"\n{'='*80}")
    print(f"DECRYPTING {total} PATIENT RECORDS")
    print(f"{'='*80}\n")
    
    success_count = 0
    error_count = 0
    
    for i, patient in enumerate(patients, 1):
        print(f"[{i}/{total}] Processing patient {patient.patient_number}...", end=' ')
        
        try:
            decrypted_data = {}
            
            for field in fields_to_decrypt:
                encrypted_value = getattr(patient, field, '')
                
                if encrypted_value and encrypted_value.startswith('gAAAAAB'):  # Is encrypted
                    try:
                        decrypted_value = encryption.decrypt(encrypted_value)
                        decrypted_data[field] = decrypted_value
                    except Exception as e:
                        print(f"\n   ⚠️  Failed to decrypt {field}: {str(e)}")
                        decrypted_data[field] = encrypted_value  # Keep original if decrypt fails
                else:
                    decrypted_data[field] = encrypted_value  # Already decrypted or empty
            
            # Use queryset update to bypass the save() method entirely
            Patient.objects.filter(pk=patient.pk).update(**decrypted_data)
            
            print("✅ Decrypted")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            error_count += 1
    
    print(f"\n{'='*80}")
    print(f"DECRYPTION COMPLETE")
    print(f"{'='*80}")
    print(f"✅ Successfully decrypted: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"Total processed: {total}")
    print(f"\n⚠️  IMPORTANT: Data has been decrypted in the database!")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    response = input("⚠️  WARNING: This will decrypt ALL patient data. Continue? (yes/no): ")
    if response.lower() == 'yes':
        decrypt_all_patients()
    else:
        print("Operation cancelled.")
