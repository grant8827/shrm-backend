#!/usr/bin/env python3
"""
Check database connection and verify user exists
"""
import os
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theracare.settings")
django.setup()

from django.conf import settings
from users.models import User

print("=" * 60)
print("DATABASE CONNECTION CHECK")
print("=" * 60)

# Check database configuration
db_config = settings.DATABASES["default"]
print(f"\nDatabase Engine: {db_config['ENGINE']}")
print(f"Database Name: {db_config['NAME']}")
print(f"Database Host: {db_config['HOST']}")
print(f"Database Port: {db_config['PORT']}")

print("\n" + "=" * 60)
print("CHECKING USER: grant8827")
print("=" * 60)

try:
    user = User.objects.filter(username="grant8827").first()

    if user:
        print(f"\n✓ User found!")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  First Name: {user.first_name}")
        print(f"  Last Name: {user.last_name}")
        print(f"  Role: {user.role}")
        print(f"  Is Active: {user.is_active}")
        print(f"  Is Staff: {user.is_staff}")
        print(f"  Is Superuser: {user.is_superuser}")

        # Test password
        password_check = user.check_password("AdminPass123!")
        print(f"\n  Password 'AdminPass123!' is correct: {password_check}")

        if not password_check:
            print("\n⚠️  Password does not match! Resetting password...")
            user.set_password("AdminPass123!")
            user.save()
            print("✓ Password has been reset to 'AdminPass123!'")
    else:
        print("\n✗ User 'grant8827' NOT FOUND in database!")
        print("\nCreating user...")

        user = User.objects.create_user(
            username="grant8827",
            email="grant88271@gmail.com",
            password="AdminPass123!",
            first_name="Grant",
            last_name="Gregory",
            role="admin",
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        print(f"✓ Created user: {user.username}")

    print("\n" + "=" * 60)
    print("LOGIN CREDENTIALS")
    print("=" * 60)
    print(f"Username: grant8827")
    print(f"Password: AdminPass123!")
    print(f"Email: grant88271@gmail.com")
    print("=" * 60)

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback

    traceback.print_exc()
