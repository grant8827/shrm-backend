"""
HIPAA-compliant validators for TheraCare EHR system.
Provides comprehensive validation for healthcare data and security compliance.
"""

import re
import os
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.core.validators import RegexValidator
from django.conf import settings


class CustomPasswordValidator:
    """
    Enhanced password validator with HIPAA-compliant security requirements.
    Enforces strong password policies for healthcare systems.
    """
    
    def __init__(self, min_length=12, max_length=128):
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, password, user=None):
        """
        Validate password against HIPAA security requirements.
        """
        errors = []
        
        # Basic length check
        if len(password) < self.min_length:
            errors.append(_(
                f'This password is too short. It must contain at least {self.min_length} characters.'
            ))
        
        if len(password) > self.max_length:
            errors.append(_(
                f'This password is too long. It must contain no more than {self.max_length} characters.'
            ))
        
        # Check character requirements
        if not any(c.isupper() for c in password):
            errors.append(_('This password must contain at least one uppercase letter.'))
        
        if not any(c.islower() for c in password):
            errors.append(_('This password must contain at least one lowercase letter.'))
        
        if not any(c.isdigit() for c in password):
            errors.append(_('This password must contain at least one digit.'))
        
        if not any(c in "!@#$%^&*(),.?\":{}|<>" for c in password):
            errors.append(_('This password must contain at least one special character.'))
        
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        """Return help text for password requirements"""
        return _(
            f'Your password must contain at least {self.min_length} characters '
            'including uppercase and lowercase letters, numbers, and special characters.'
        )


class PHIFieldValidator:
    """
    Validator for Protected Health Information (PHI) fields.
    Ensures PHI data meets HIPAA compliance standards.
    """
    
    @staticmethod
    def validate_ssn(value):
        """Validate Social Security Number format"""
        if not value:
            return
            
        # Remove any formatting characters
        ssn_clean = re.sub(r'[^\d]', '', value)
        
        # Check length
        if len(ssn_clean) != 9:
            raise ValidationError(_('SSN must be exactly 9 digits.'))
        
        # Check for invalid patterns
        invalid_patterns = [
            '000000000', '111111111', '222222222', '333333333',
            '444444444', '555555555', '666666666', '777777777',
            '888888888', '999999999', '123456789', '987654321'
        ]
        
        if ssn_clean in invalid_patterns:
            raise ValidationError(_('Invalid SSN format.'))

    @staticmethod  
    def validate_phone_number(value):
        """Validate phone number format"""
        if not value:
            return
            
        # Remove formatting characters
        phone_clean = re.sub(r'[^\d]', '', value)
        
        # Check length (US numbers)
        if len(phone_clean) not in [10, 11]:
            raise ValidationError(_('Phone number must be 10 or 11 digits.'))

    @staticmethod
    def validate_mrn(value):
        """Validate Medical Record Number"""
        if not value:
            return
            
        # MRN should be alphanumeric, 6-20 characters
        if not re.match(r'^[A-Za-z0-9]{6,20}$', value):
            raise ValidationError(_(
                'Medical Record Number must be 6-20 alphanumeric characters.'
            ))


class HIPAAFieldValidator:
    """
    General HIPAA field validator for various healthcare data types.
    """
    
    @staticmethod
    def validate_date_of_birth(value):
        """Validate date of birth"""
        if not value:
            return
            
        from datetime import date, timedelta
        
        today = date.today()
        min_age_date = today - timedelta(days=150 * 365)  # 150 years max
        
        if value > today:
            raise ValidationError(_('Date of birth cannot be in the future.'))
        
        if value < min_age_date:
            raise ValidationError(_('Date of birth is too far in the past.'))


class SecurityValidator:
    """
    Security-related validators for HIPAA compliance.
    """
    
    @staticmethod
    def validate_file_upload(file):
        """Validate uploaded file for security"""
        if not file:
            return
            
        # Check file size (50MB max for security)
        max_size = 50 * 1024 * 1024  # 50MB
        if file.size > max_size:
            raise ValidationError(_('File size cannot exceed 50MB.'))


# Custom regex validators for common healthcare patterns
healthcare_validators = {
    'medication_name': RegexValidator(
        regex=r'^[A-Za-z0-9\s\-\(\)\.]{2,100}$',
        message=_('Medication name must be 2-100 characters, letters, numbers, spaces, hyphens, parentheses, and periods only.')
    ),
    
    'insurance_number': RegexValidator(
        regex=r'^[A-Za-z0-9\-]{5,30}$',
        message=_('Insurance number must be 5-30 characters, letters, numbers, and hyphens only.')
    )
}