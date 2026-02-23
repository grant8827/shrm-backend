#!/usr/bin/env python3
"""
Debug script to check all admin users and their password status
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theracare.settings")
django.setup()

from users.models import User
from django.contrib.auth.hashers import check_password

print("=" * 80)
print("ALL ADMIN USERS IN PRODUCTION DATABASE")
print("=" * 80)

admin_users = User.objects.filter(role="admin").order_by("date_joined")

for user in admin_users:
    print(f"\nUsername: {user.username}")
    print(f"Email: {user.email}")
    print(f"Full Name: {user.first_name} {user.last_name}")
    print(f"Is Active: {user.is_active}")
    print(f"Is Staff: {user.is_staff}")
    print(f"Is Superuser: {user.is_superuser}")
    print(f"Date Joined: {user.date_joined}")
    print(f"Last Login: {user.last_login}")
    print(f"Password Hash (first 50 chars): {user.password[:50]}...")

    # Test common passwords
    test_passwords = ["AdminPass123!", "admin123", "Admin123!"]
    print(f"\nTesting passwords:")
    for pwd in test_passwords:
        result = user.check_password(pwd)
        print(f"  '{pwd}': {'✓ CORRECT' if result else '✗ incorrect'}")

    print("-" * 80)

print(f"\nTotal admin users: {admin_users.count()}")
