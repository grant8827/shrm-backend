#!/usr/bin/env python3
"""
Fix double-encrypted user data by removing one layer of encryption.
This script will decrypt once to get back to properly single-encrypted data.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theracare.settings')
django.setup()

from users.models import User
from core.security import encryption

def fix_double_encryption():
    """Fix users with double-encrypted data."""
    users = User.objects.all()
    
    print(f"Found {users.count()} users to check...")
    
    for user in users:
        print(f"\nProcessing: {user.email}")
        
        # Check first_name
        try:
            # Try to decrypt once
            decrypted_once = encryption.decrypt(user.first_name)
            
            # If it still looks encrypted (starts with gAAAAAB), it was double-encrypted
            if decrypted_once.startswith('gAAAAAB') or decrypted_once.startswith('Z0FBQUFBQnB'):
                print(f"  First name is double-encrypted. Fixing...")
                # Decrypt again to get the actual value
                actual_value = encryption.decrypt(decrypted_once)
                print(f"  Actual first name: {actual_value}")
                
                # Save the single-encrypted version (save() will encrypt it)
                user.first_name = actual_value  # This will be encrypted by save()
                
        except Exception as e:
            print(f"  First name appears OK or error: {e}")
        
        # Check last_name
        try:
            decrypted_once = encryption.decrypt(user.last_name)
            
            if decrypted_once.startswith('gAAAAAB') or decrypted_once.startswith('Z0FBQUFBQnB'):
                print(f"  Last name is double-encrypted. Fixing...")
                actual_value = encryption.decrypt(decrypted_once)
                print(f"  Actual last name: {actual_value}")
                user.last_name = actual_value
                
        except Exception as e:
            print(f"  Last name appears OK or error: {e}")
        
        # Check phone
        if user.phone:
            try:
                decrypted_once = encryption.decrypt(user.phone)
                
                if decrypted_once.startswith('gAAAAAB') or decrypted_once.startswith('Z0FBQUFBQnB'):
                    print(f"  Phone is double-encrypted. Fixing...")
                    actual_value = encryption.decrypt(decrypted_once)
                    print(f"  Actual phone: {actual_value}")
                    user.phone = actual_value
                    
            except Exception as e:
                print(f"  Phone appears OK or error: {e}")
        
        # Save the user (this will re-encrypt with single encryption)
        user.save()
        print(f"  ✓ User saved with corrected encryption")
    
    print("\n✅ All users processed!")

if __name__ == '__main__':
    fix_double_encryption()
