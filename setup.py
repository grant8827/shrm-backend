#!/usr/bin/env python3
"""
Quick setup script for TheraCare EHR System
Creates database tables and superuser
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theracare.settings')

# Setup Django
django.setup()

def main():
    """Run setup commands."""
    print("🏥 TheraCare EHR System Setup")
    print("=" * 40)
    
    try:
        # Run migrations
        print("\n📊 Creating database tables...")
        execute_from_command_line(['manage.py', 'makemigrations'])
        execute_from_command_line(['manage.py', 'migrate'])
        
        # Create test users (including superuser)
        print("\n👤 Creating test users...")
        execute_from_command_line(['manage.py', 'create_test_users'])
        
        print("\n✅ Setup completed successfully!")
        print("\n🌐 Next steps:")
        print("   1. Start the backend: python manage.py runserver")
        print("   2. Start the frontend: cd ../frontend && npm run dev")
        print("   3. Access admin at: http://localhost:8000/admin/")
        print("   4. Access app at: http://localhost:3000/")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()