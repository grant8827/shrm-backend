#!/usr/bin/env python3
"""
Test script to send email via Mailgun
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theracare.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    """Send a test email"""
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print("\nSending test email...")
    
    try:
        result = send_mail(
            subject='Test Email from Safe Haven EHR',
            message='This is a test email to verify Mailgun configuration is working correctly.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['grant8827@yahoo.com'],  # Your email
            fail_silently=False,
        )
        print(f"\n✅ Email sent successfully! Result: {result}")
        print("Check your inbox at grant8827@yahoo.com (and spam folder)")
        return True
    except Exception as e:
        print(f"\n❌ Error sending email: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_email()
