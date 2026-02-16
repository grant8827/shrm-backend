#!/usr/bin/env python3
"""
Check patient data directly from database (raw SQL)
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theracare.settings')
django.setup()

from django.db import connection

def check_raw_data():
    """Check raw database values"""
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT patient_number, first_name, last_name, email 
            FROM patients 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        print(f"\n{'='*80}")
        print(f"RAW DATABASE VALUES (No Django ORM)")
        print(f"{'='*80}\n")
        
        for row in cursor.fetchall():
            patient_num, first, last, email = row
            print(f"Patient: {patient_num}")
            print(f"  First Name: {first}")
            print(f"  Last Name: {last}")
            print(f"  Email: {email}")
            print(f"  {'-'*76}")

if __name__ == '__main__':
    check_raw_data()
