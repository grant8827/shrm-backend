#!/usr/bin/env python3
"""
Test encryption/decryption directly
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theracare.settings')
django.setup()

from core.security import encryption

# Get a sample encrypted value from database
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT first_name FROM patients LIMIT 1")
    encrypted_value = cursor.fetchone()[0]
    
    print(f"\nEncrypted value: {encrypted_value[:50]}...")
    print(f"\nAttempting to decrypt...\n")
    
    try:
        decrypted = encryption.decrypt(encrypted_value)
        print(f"✅ Decryption successful!")
        print(f"Decrypted value: {decrypted}")
    except Exception as e:
        print(f"❌ Decryption failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
