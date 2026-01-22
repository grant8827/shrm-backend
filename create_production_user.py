#!/usr/bin/env python3
"""
Script to create a user in the production database
Run this on Railway using: railway run python create_production_user.py
Or set DATABASE_URL to production and run locally
"""

import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theracare.settings')
django.setup()

from users.models import User

def create_user():
    """Create or update the grant8827 user"""
    
    username = 'grant8827'
    email = 'grant88271@gmail.com'
    password = 'AdminPass123!'  # Change this to your preferred password
    
    try:
        # Try to get existing user
        user = User.objects.filter(username=username).first()
        
        if user:
            print(f"✓ User '{username}' already exists")
            print(f"  Email: {user.email}")
            print(f"  Role: {user.role}")
            print(f"  Active: {user.is_active}")
            
            # Update password
            user.set_password(password)
            user.is_active = True
            user.save()
            print(f"✓ Password updated for {username}")
        else:
            # Create new user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name='Grant',
                last_name='Gregory',
                role='admin',
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            print(f"✓ Created new user: {username}")
            print(f"  Email: {email}")
            print(f"  Role: admin")
        
        print(f"\n✓ Login credentials:")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print(f"  Email: {email}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_user()
