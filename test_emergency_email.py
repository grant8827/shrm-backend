#!/usr/bin/env python
"""Test script to send emergency session email."""

import os
import sys
import django

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theracare.settings')
django.setup()

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import uuid

def test_emergency_email():
    """Send a test emergency session email."""
    
    # Generate a test room_id
    room_id = str(uuid.uuid4())
    session_url = f"{settings.FRONTEND_URL}/telehealth/join/{room_id}"
    
    recipient_email = "greggrant3760@gmail.com"
    
    print("=" * 60)
    print("TESTING EMERGENCY SESSION EMAIL")
    print("=" * 60)
    print(f"To: {recipient_email}")
    print(f"From: {settings.DEFAULT_FROM_EMAIL}")
    print(f"Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    print(f"SSL: {settings.EMAIL_USE_SSL}, TLS: {settings.EMAIL_USE_TLS}")
    print(f"Session URL: {session_url}")
    print("=" * 60)
    
    email_context = {
        'patient_name': 'Test Patient',
        'therapist_name': 'Dr. Test Therapist',
        'session_url': session_url,
        'room_id': room_id
    }
    
    try:
        email_body = render_to_string('emails/emergency_session.html', email_context)
        
        print("\nSending email...")
        result = send_mail(
            subject='Emergency Telehealth Session - Join Now',
            message=f"You have an emergency telehealth session. Join here: {session_url}",
            html_message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
        print(f"✅ Email sent successfully! Result: {result}")
        print(f"Check your inbox at {recipient_email}")
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_emergency_email()
