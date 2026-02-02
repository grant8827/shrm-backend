"""
Service layer for patient management business logic.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from users.models import User
from .utils import generate_username, generate_random_password
import logging

logger = logging.getLogger('theracare.audit')


class PatientRegistrationService:
    """
    Service for handling patient portal registration and account creation.
    """
    
    @staticmethod
    def create_user_account(patient_data, patient_instance=None):
        """
        Create a user account for patient portal access.
        
        Args:
            patient_data (dict): Dictionary containing patient information
            patient_instance: Patient model instance (optional, for linking)
        
        Returns:
            tuple: (User instance, username, temporary_password) or (None, None, None) if creation fails
        """
        try:
            email = patient_data.get('email', '')
            first_name = patient_data.get('first_name', '')
            last_name = patient_data.get('last_name', '')
            
            if not email or not first_name or not last_name:
                logger.error('Cannot create user account: missing required fields (email, first_name, last_name)')
                return None, None, None
            
            # Generate username and password
            username = generate_username(first_name, last_name)
            temporary_password = generate_random_password()
            
            # Create user account
            user = User.objects.create_user(
                username=username,
                email=email,
                password=temporary_password,
                first_name=first_name,
                last_name=last_name,
                role='client',
                is_active=True,
                requires_password_change=True  # Force password change on first login
            )
            
            logger.info(f'Created user account for patient: {username} (User ID: {user.id})')
            
            return user, username, temporary_password
            
        except Exception as e:
            logger.error(f'Error creating user account for patient: {e}')
            return None, None, None
    
    @staticmethod
    def send_welcome_email(patient, username, temporary_password):
        """
        Send welcome email to patient with portal access credentials.
        
        Args:
            patient: Patient model instance
            username (str): Generated username
            temporary_password (str): Temporary password
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            email = patient.get_decrypted_field('email')
            first_name = patient.get_decrypted_field('first_name')
            
            if not email:
                logger.error(f'Cannot send welcome email: no email for patient {patient.id}')
                return False
            
            # Prepare email context
            context = {
                'first_name': first_name,
                'patient_number': patient.patient_number,
                'username': username,
                'temporary_password': temporary_password,
                'portal_url': settings.FRONTEND_URL,
                'support_email': settings.DEFAULT_FROM_EMAIL,
            }
            
            # Render email templates
            subject = 'Welcome to Safe Haven EHR - Patient Portal Access'
            
            # Try HTML template first, fallback to plain text
            try:
                html_message = render_to_string('emails/patient_welcome.html', context)
            except Exception:
                html_message = None
            
            text_message = render_to_string('emails/patient_welcome.txt', context)
            
            # Send email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f'Welcome email sent to patient: {email} (Patient ID: {patient.id})')
            return True
            
        except Exception as e:
            logger.error(f'Error sending welcome email to patient {patient.id}: {e}')
            return False
    
    @staticmethod
    def create_patient_with_portal_access(patient_data):
        """
        Complete flow: Create user account and send welcome email.
        
        Args:
            patient_data (dict): Patient information
        
        Returns:
            tuple: (User instance, username, password) or (None, None, None)
        """
        user, username, password = PatientRegistrationService.create_user_account(patient_data)
        return user, username, password
    
    @staticmethod
    def send_credentials_after_creation(patient):
        """
        Send credentials email after patient is created and has a linked user.
        
        Args:
            patient: Patient model instance with linked user account
        
        Returns:
            bool: True if email sent successfully
        """
        if not patient.user:
            logger.warning(f'Cannot send credentials: patient {patient.id} has no user account')
            return False
        
        # Note: We can't retrieve the original password as it's hashed
        # This should only be called immediately after creation when we still have the password
        logger.warning(f'send_credentials_after_creation called but password is already hashed for patient {patient.id}')
        return False
