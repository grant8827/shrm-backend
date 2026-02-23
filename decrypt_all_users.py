#!/usr/bin/env python3
"""
Decrypt all user data and save as plain text (no encryption).
This will fix the encrypted text display issue permanently.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theracare.settings")
django.setup()

from users.models import User
from core.security import encryption


def decrypt_all_users():
    """Decrypt all users and save without encryption."""
    users = User.objects.all()

    print(f"Found {users.count()} users to decrypt...")

    for user in users:
        print(f"\nProcessing: {user.email}")
        changed = False

        # Decrypt first_name if encrypted (check for both gAAAAAB and Z0FBQUFBQnB formats)
        if user.first_name and (
            user.first_name.startswith("gAAAAAB")
            or user.first_name.startswith("Z0FBQUFBQnB")
        ):
            try:
                decrypted = encryption.decrypt(user.first_name)
                user.first_name = decrypted
                print(f"  ✓ Decrypted first_name: {decrypted}")
                changed = True
            except Exception as e:
                print(f"  ✗ Failed to decrypt first_name: {e}")
        else:
            print(f"  - First name already plain: {user.first_name}")

        # Decrypt last_name if encrypted
        if user.last_name and (
            user.last_name.startswith("gAAAAAB")
            or user.last_name.startswith("Z0FBQUFBQnB")
        ):
            try:
                decrypted = encryption.decrypt(user.last_name)
                user.last_name = decrypted
                print(f"  ✓ Decrypted last_name: {decrypted}")
                changed = True
            except Exception as e:
                print(f"  ✗ Failed to decrypt last_name: {e}")
        else:
            print(f"  - Last name already plain: {user.last_name}")

        # Decrypt phone if encrypted
        if user.phone and (
            user.phone.startswith("gAAAAAB") or user.phone.startswith("Z0FBQUFBQnB")
        ):
            try:
                decrypted = encryption.decrypt(user.phone)
                user.phone = decrypted
                print(f"  ✓ Decrypted phone: {decrypted}")
                changed = True
            except Exception as e:
                print(f"  ✗ Failed to decrypt phone: {e}")
        elif user.phone:
            print(f"  - Phone already plain: {user.phone}")

        # Decrypt license_number if encrypted
        if user.license_number and (
            user.license_number.startswith("gAAAAAB")
            or user.license_number.startswith("Z0FBQUFBQnB")
        ):
            try:
                decrypted = encryption.decrypt(user.license_number)
                user.license_number = decrypted
                print(f"  ✓ Decrypted license_number: {decrypted}")
                changed = True
            except Exception as e:
                print(f"  ✗ Failed to decrypt license_number: {e}")
        elif user.license_number:
            print(f"  - License already plain: {user.license_number}")

        if changed:
            # Save without re-encrypting (save() now decrypts instead of encrypts)
            user.save()
            print(f"  ✅ User saved with plain text data")
        else:
            print(f"  ℹ️  No changes needed")

    print("\n✅ All users processed! All data is now stored as plain text.")
    print("⚠️  NOTE: Encryption has been disabled. Re-enable for production if needed.")


if __name__ == "__main__":
    decrypt_all_users()
