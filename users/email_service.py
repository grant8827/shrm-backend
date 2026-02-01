"""
Email service for patient registration
"""

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import RegistrationToken
import secrets
import logging

logger = logging.getLogger('theracare.audit')


def generate_registration_token(email, first_name, last_name, phone_number=''):
    """Generate a unique registration token"""
    token_value = secrets.token_urlsafe(32)
    
    # Token expires in 7 days
    expires_at = timezone.now() + timedelta(days=7)
    
    token = RegistrationToken.objects.create(
        token=token_value,
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        expires_at=expires_at
    )
    
    return token


def send_registration_email(email, first_name, last_name, phone_number=''):
    """Send welcome email with registration completion link"""
    
    try:
        # Generate token
        token = generate_registration_token(email, first_name, last_name, phone_number)
        
        # Build registration URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        registration_url = f"{frontend_url}/complete-registration/{token.token}"
        
        # Email subject and message
        subject = 'Welcome to Safe Haven - Complete Your Registration'
        
        message = f"""
Dear {first_name} {last_name},

Thank you for choosing Safe Haven for your mental health care needs. We're honored to support you on your journey to wellness.

To complete your registration and access your patient portal, please click the link below:

{registration_url}

This link will expire in 7 days for your security.

Once you complete your registration, you'll be able to:
- Schedule and manage appointments
- Communicate securely with your therapist
- Access your medical records and documents
- Participate in telehealth sessions
- View billing information

If you have any questions or need assistance, please don't hesitate to contact us.

Best regards,
The Safe Haven Team

---
This is an automated message. Please do not reply to this email.
If you did not request this registration, please disregard this message.
"""
        
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #1976d2; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; border-top: none; }}
        .button {{ display: inline-block; padding: 12px 30px; background-color: #1976d2; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .button:hover {{ background-color: #1565c0; }}
        .footer {{ margin-top: 20px; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
        .benefits {{ background-color: white; padding: 15px; border-left: 4px solid #1976d2; margin: 20px 0; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 8px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to Safe Haven</h1>
        </div>
        <div class="content">
            <p>Dear {first_name} {last_name},</p>
            
            <p>Thank you for choosing Safe Haven for your mental health care needs. We're honored to support you on your journey to wellness.</p>
            
            <p>To complete your registration and access your patient portal, please click the button below:</p>
            
            <center>
                <a href="{registration_url}" class="button">Complete Registration</a>
            </center>
            
            <p style="font-size: 12px; color: #666;">Or copy and paste this link into your browser:<br>
            <a href="{registration_url}">{registration_url}</a></p>
            
            <p><strong>This link will expire in 7 days for your security.</strong></p>
            
            <div class="benefits">
                <h3 style="margin-top: 0; color: #1976d2;">Once you complete your registration, you'll be able to:</h3>
                <ul>
                    <li>Schedule and manage appointments</li>
                    <li>Communicate securely with your therapist</li>
                    <li>Access your medical records and documents</li>
                    <li>Participate in telehealth sessions</li>
                    <li>View billing information</li>
                </ul>
            </div>
            
            <p>If you have any questions or need assistance, please don't hesitate to contact us.</p>
            
            <p>Best regards,<br>
            <strong>The Safe Haven Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated message. Please do not reply to this email.<br>
            If you did not request this registration, please disregard this message.</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(
            'Registration email sent',
            extra={
                'event_type': 'registration_email_sent',
                'email': email,
                'token_id': str(token.id),
                'expires_at': token.expires_at.isoformat(),
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        return True, token
        
    except Exception as e:
        logger.error(
            f'Failed to send registration email: {str(e)}',
            extra={
                'event_type': 'registration_email_failed',
                'email': email,
                'error': str(e),
                'timestamp': timezone.now().isoformat(),
            }
        )
        return False, None
