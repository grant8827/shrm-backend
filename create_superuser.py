#!/usr/bin/env python3
"""
Create a superuser in the database
"""
import os
import django
import getpass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theracare.settings")
django.setup()

from users.models import User

print("=" * 60)
print("CREATE SUPERUSER")
print("=" * 60)

# Get user input
username = input("\nUsername: ").strip()
email = input("Email: ").strip()
first_name = input("First Name: ").strip()
last_name = input("Last Name: ").strip()
password = getpass.getpass("Password: ").strip()
password_confirm = getpass.getpass("Confirm Password: ").strip()

if password != password_confirm:
    print("\n✗ Passwords do not match!")
    exit(1)

try:
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        print(f"\n✗ User with username '{username}' already exists!")
        update = input("Update existing user? (yes/no): ").strip().lower()
        if update == "yes":
            user = User.objects.get(username=username)
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.set_password(password)
            user.role = "admin"
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()
            print(f"\n✓ Updated user: {username}")
        else:
            exit(0)
    else:
        # Create new superuser
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role="admin",
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        print(f"\n✓ Created superuser: {username}")

    print("\n" + "=" * 60)
    print("LOGIN CREDENTIALS")
    print("=" * 60)
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Email: {email}")
    print(f"Role: admin")
    print("=" * 60)

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback

    traceback.print_exc()
