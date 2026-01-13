# backend/core/signals.py
"""
Django signals for TheraCare core functionality.
"""

from django.db.models.signals import post_save, pre_delete
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger('theracare.signals')
User = get_user_model()


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """Handle successful user login."""
    try:
        # Reset failed login attempts on successful login
        if hasattr(user, 'reset_failed_login_attempts'):
            user.reset_failed_login_attempts()
        
        # Log successful login for audit
        from core.security import AccessLogging
        AccessLogging.log_phi_access(
            user_id=str(user.id),
            patient_id='N/A',
            action='LOGIN_SUCCESS',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info(f"User {user.email} logged in successfully")
        
    except Exception as e:
        logger.error(f"Error in login handler: {str(e)}")


@receiver(user_login_failed)
def user_login_failed_handler(sender, credentials, request, **kwargs):
    """Handle failed login attempts."""
    try:
        email = credentials.get('email') or credentials.get('username')
        
        if email:
            try:
                user = User.objects.get(email=email)
                # Increment failed login attempts
                if hasattr(user, 'increment_failed_login_attempts'):
                    user.increment_failed_login_attempts()
                
                logger.warning(f"Failed login attempt for user {email}")
                
            except User.DoesNotExist:
                logger.warning(f"Failed login attempt for non-existent user {email}")
        
        # Log failed access attempt
        from core.security import AccessLogging
        AccessLogging.log_failed_access(
            user_id=email,
            resource='LOGIN',
            ip_address=get_client_ip(request),
            reason='INVALID_CREDENTIALS'
        )
        
    except Exception as e:
        logger.error(f"Error in failed login handler: {str(e)}")


@receiver(post_save, sender=User)
def user_post_save_handler(sender, instance, created, **kwargs):
    """Handle user creation and updates."""
    try:
        if created:
            logger.info(f"New user created: {instance.email} with role {instance.role}")
            
            # Create user profile if it doesn't exist
            from users.models import UserProfile
            if not hasattr(instance, 'profile'):
                UserProfile.objects.create(user=instance)
        else:
            logger.info(f"User updated: {instance.email}")
            
    except Exception as e:
        logger.error(f"Error in user post_save handler: {str(e)}")


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or 'unknown'


# Additional signals can be added here for:
# - Audit logging
# - HIPAA compliance tracking
# - Real-time notifications
# - Data synchronization