#!/usr/bin/env python
"""Test the actual emergency endpoint to verify email recipient."""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theracare.settings")
django.setup()

from django.contrib.auth import get_user_model
from telehealth.views import TelehealthSessionViewSet
from rest_framework.test import APIRequestFactory, force_authenticate
from django.conf import settings

User = get_user_model()


def test_emergency_endpoint():
    """Test creating emergency session via the actual endpoint."""

    # Get or create a therapist user
    therapist, created = User.objects.get_or_create(
        username="test_therapist",
        defaults={
            "first_name": "Test",
            "last_name": "Therapist",
            "email": "therapist@test.com",
            "role": "therapist",
        },
    )
    if created:
        therapist.set_password("test123")
        therapist.save()

    print("=" * 60)
    print("TESTING EMERGENCY ENDPOINT")
    print("=" * 60)
    print(f"Therapist: {therapist.first_name} {therapist.last_name}")
    print(f"Patient Email (NEW): grant8827@yahoo.com")
    print(f"Expected Recipient: grant8827@yahoo.com")
    print(f"SMTP From: {settings.DEFAULT_FROM_EMAIL}")
    print("=" * 60)

    # Create request
    factory = APIRequestFactory()
    request = factory.post(
        "/api/telehealth/sessions/create_emergency/",
        {
            "patient_email": "grant8827@yahoo.com",
            "patient_first_name": "Gregory",
            "patient_last_name": "Grant",
        },
        format="json",
    )

    # Force authentication
    force_authenticate(request, user=therapist)

    # Call the endpoint
    view = TelehealthSessionViewSet.as_view({"post": "create_emergency"})
    response = view(request)

    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Data: {response.data}")

    if response.status_code == 201:
        print("\n✅ Emergency session created!")
        print(f"Session URL: {response.data.get('session_url')}")
        print(f"\n⚠️  Check grant8827@yahoo.com for the email!")
        print("   (Also check spam/junk folder)")
    else:
        print(f"\n❌ Error: {response.data}")


if __name__ == "__main__":
    test_emergency_endpoint()

    # Wait a bit for the background thread to send email
    import time

    print("\nWaiting 3 seconds for email to send...")
    time.sleep(3)
    print("Done!")
