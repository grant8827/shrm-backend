#!/usr/bin/env python
"""Simple test to send plain text email."""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theracare.settings")
django.setup()

from django.core.mail import send_mail
from django.conf import settings
import uuid


def test_simple_email():
    """Send a simple plain text email."""

    room_id = str(uuid.uuid4())
    session_url = f"{settings.FRONTEND_URL}/telehealth/join/{room_id}"

    recipient_email = "grant8827@yahoo.com"

    print("=" * 60)
    print("SENDING SIMPLE PLAIN TEXT EMAIL")
    print("=" * 60)
    print(f"To: {recipient_email}")
    print(f"From: {settings.DEFAULT_FROM_EMAIL}")
    print(f"Backend: {settings.EMAIL_BACKEND}")
    print(f"Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    print(f"User: {settings.EMAIL_HOST_USER}")
    print(f"SSL: {settings.EMAIL_USE_SSL}, TLS: {settings.EMAIL_USE_TLS}")
    print("=" * 60)

    try:
        print("\nSending plain text email...")
        result = send_mail(
            subject="Test Emergency Session from Safe Haven",
            message=f"""
Hello,

This is a test emergency telehealth session invitation.

Your therapist has started an emergency session.

Click this link to join:
{session_url}

If you have any questions, please contact Safe Haven Restoration Ministries.

Thank you,
Safe Haven Team
            """.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )

        print(f"\n✅ Email sent! Result: {result}")
        print(f"\n📧 Check {recipient_email}")
        print("⚠️  Also check your SPAM/JUNK folder!")
        print(f"\nJoin URL: {session_url}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_simple_email()
