#!/usr/bin/env python3
"""
Decrypt patient data using raw SQL
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theracare.settings')
django.setup()

from django.db import connection, transaction
from core.security import encryption

def decrypt_with_sql():
    """Decrypt using raw SQL Updates"""
    
    fields = [
        'first_name', 'last_name', 'middle_name', 'email', 'phone', 'phone_secondary',
        'street_address', 'city', 'zip_code', 'ssn', 'medical_record_number',
        'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'
    ]
    
    with connection.cursor() as cursor:
        # Get all patients
        cursor.execute("SELECT id, " + ", ".join(fields) + " FROM patients")
        patients = cursor.fetchall()
        
        print(f"\n{'='*80}")
        print(f"DECRYPTING {len(patients)} PATIENTS USING RAW SQL")
        print(f"{'='*80}\n")
        
        success = 0
        errors = 0
        
        for row in patients:
            patient_id = row[0]
            print(f"Processing patient ID: {patient_id}...", end=' ')
            
            try:
                # Decrypt each field
                decrypted_values = []
                for i, field in enumerate(fields, 1):
                    value = row[i]
                    if value and value.startswith('gAAAAAB'):
                        try:
                            decrypted = encryption.decrypt(value)
                            decrypted_values.append(decrypted)
                        except:
                            decrypted_values.append(value)  # Keep original if fails
                    else:
                        decrypted_values.append(value if value else '')
                
                # Update using raw SQL
                update_sql = f"""
                    UPDATE patients 
                    SET {', '.join([f'{field} = %s' for field in fields])}
                    WHERE id = %s
                """
                
                cursor.execute(update_sql, decrypted_values + [patient_id])
                print("✅")
                success += 1
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                errors += 1
        
        # Commit the transaction
        connection.commit()
        
        print(f"\n{'='*80}")
        print(f"COMPLETE: {success} success, {errors} errors")
        print(f"Verifying data was updated...")
        
        # Verify decryption worked
        cursor.execute("SELECT patient_number, first_name, last_name, email FROM patients LIMIT 3")
        for row in cursor.fetchall():
            print(f"\n  {row[0]}: {row[1]} {row[2]} ({row[3]})")
        
        print(f"{'='*80}\n")

if __name__ == '__main__':
    response = input("⚠️  Decrypt patient data? (yes/no): ")
    if response.lower() == 'yes':
        decrypt_with_sql()
    else:
        print("Cancelled.")
