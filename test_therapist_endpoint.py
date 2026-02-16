#!/usr/bin/env python3
"""
Test script to verify the therapist/admin user endpoint is working correctly.
Run this to test: python3 test_therapist_endpoint.py
"""

import django
import os
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theracare.settings')
django.setup()

from users.models import User
from users.serializers import UserListSerializer

print("=" * 60)
print("TESTING THERAPIST/ADMIN USER ENDPOINT")
print("=" * 60)

# Test 1: Check users in database
print("\n✅ Test 1: Users in database")
print("-" * 60)
all_users = User.objects.all()
print(f"Total users in database: {all_users.count()}")

admin_therapist_users = User.objects.filter(role__in=['admin', 'therapist'])
print(f"Admin/Therapist users: {admin_therapist_users.count()}")

for user in admin_therapist_users:
    print(f"  - {user.role.upper()}: {user.get_full_name()} (ID: {user.id})")
    print(f"    Email: {user.email}, Active: {user.is_active}")

# Test 2: Check serializer output
print("\n✅ Test 2: Serializer output")
print("-" * 60)
serializer = UserListSerializer(admin_therapist_users, many=True)
data = serializer.data
print(f"Serialized {len(data)} users:")
for user_data in data:
    print(f"  - {user_data.get('full_name')} ({user_data.get('role')})")
    print(f"    ID: {user_data.get('id')}")
    print(f"    Username: {user_data.get('username')}")

# Test 3: Check what frontend would receive
print("\n✅ Test 3: Frontend mapping")
print("-" * 60)
print("Frontend should receive array like:")
frontend_data = []
for user_data in data:
    frontend_user = {
        'id': user_data.get('id'),
        'name': user_data.get('full_name') or user_data.get('username') or 'Unknown'
    }
    frontend_data.append(frontend_user)
    print(f"  {{ id: '{frontend_user['id']}', name: '{frontend_user['name']}' }}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
if len(frontend_data) > 0:
    print(f"✅ SUCCESS: {len(frontend_data)} therapist(s)/admin(s) should appear in dropdown")
    print("   If dropdown is still empty, check:")
    print("   1. Browser console (F12) for errors")
    print("   2. Are you logged in as admin?")
    print("   3. Did you rebuild the frontend? (npm run build if needed)")
    print("   4. Clear browser cache and refresh")
else:
    print("❌ NO USERS FOUND: No therapists or admins in database")
    print("   Create an admin user first using: python3 create_superuser.py")

print("=" * 60)
