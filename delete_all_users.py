#!/usr/bin/env python3
"""
Delete all users from the database
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theracare.settings")
django.setup()

from users.models import User

print("=== DELETE ALL USERS ===\n")

# Count current users
user_count = User.objects.count()
print(f"Current users in database: {user_count}")

if user_count == 0:
    print("\n✓ No users to delete")
else:
    # List all users before deleting
    print("\nUsers to be deleted:")
    for user in User.objects.all():
        print(f"  - {user.email} ({user.role})")

    # Delete all users
    User.objects.all().delete()

    print(f"\n✓ Deleted all {user_count} users")

# Verify deletion
remaining = User.objects.count()
print(f"\n=== COMPLETE ===")
print(f"Remaining users: {remaining}")
