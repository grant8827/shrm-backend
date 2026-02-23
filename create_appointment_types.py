#!/usr/bin/env python3
"""
Create default appointment types for the system
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theracare.settings")
django.setup()

from appointments.models import AppointmentType


def create_appointment_types():
    """Create default appointment types"""

    appointment_types = [
        {
            "name": "Initial Consultation",
            "description": "First appointment with a new client",
            "duration_minutes": 60,
            "color_code": "#4CAF50",
            "is_telehealth_enabled": True,
            "requires_pre_auth": False,
            "default_cost": 150.00,
        },
        {
            "name": "Follow-up Session",
            "description": "Regular therapy session",
            "duration_minutes": 50,
            "color_code": "#2196F3",
            "is_telehealth_enabled": True,
            "requires_pre_auth": False,
            "default_cost": 120.00,
        },
        {
            "name": "Group Therapy",
            "description": "Group therapy session",
            "duration_minutes": 90,
            "color_code": "#FF9800",
            "is_telehealth_enabled": True,
            "requires_pre_auth": False,
            "default_cost": 80.00,
        },
        {
            "name": "Assessment",
            "description": "Clinical assessment and evaluation",
            "duration_minutes": 90,
            "color_code": "#9C27B0",
            "is_telehealth_enabled": False,
            "requires_pre_auth": True,
            "default_cost": 200.00,
        },
        {
            "name": "Crisis Intervention",
            "description": "Emergency/crisis session",
            "duration_minutes": 60,
            "color_code": "#F44336",
            "is_telehealth_enabled": True,
            "requires_pre_auth": False,
            "default_cost": 175.00,
        },
    ]

    created_count = 0
    for apt_type_data in appointment_types:
        apt_type, created = AppointmentType.objects.get_or_create(
            name=apt_type_data["name"], defaults=apt_type_data
        )
        if created:
            print(f"✓ Created: {apt_type.name} ({apt_type.duration_minutes} min)")
            created_count += 1
        else:
            print(f"- Already exists: {apt_type.name}")

    print(f"\nTotal appointment types created: {created_count}")
    print(f"Total appointment types in database: {AppointmentType.objects.count()}")

    # Print the first appointment type ID for reference
    first_type = AppointmentType.objects.first()
    if first_type:
        print(f"\nFirst appointment type ID: {first_type.id}")


if __name__ == "__main__":
    create_appointment_types()
