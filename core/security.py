# Core encryption and security utilities for HIPAA compliance

import base64
import hashlib
import logging
from typing import Any, Dict, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, timedelta
import json

logger = logging.getLogger('theracare.security')


class HIPAAEncryption:
    """HIPAA-compliant encryption utility class"""
    
    def __init__(self):
        self.encryption_key = self._get_encryption_key()
        self.fernet = Fernet(self.encryption_key)
    
    def _get_encryption_key(self) -> bytes:
        """Generate or retrieve encryption key"""
        key_string = getattr(settings, 'HIPAA_SETTINGS', {}).get('ENCRYPTION_KEY')
        if not key_string:
            raise ValueError("ENCRYPTION_KEY not found in HIPAA_SETTINGS")
        
        # Derive key from password using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'theracare_salt',  # In production, use a random salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_string.encode()))
        return key
    
    def encrypt(self, data: Union[str, Dict[str, Any]]) -> str:
        """Encrypt sensitive data"""
        try:
            if isinstance(data, dict):
                data = json.dumps(data)
            
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            encrypted_data = self.fernet.encrypt(data)
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode('utf-8')
        
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            raise
    
    def decrypt_json(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt and parse JSON data"""
        decrypted_string = self.decrypt(encrypted_data)
        return json.loads(decrypted_string)
    
    def hash_data(self, data: str) -> str:
        """Create SHA-256 hash of data for integrity verification"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def verify_hash(self, data: str, expected_hash: str) -> bool:
        """Verify data integrity using hash"""
        return self.hash_data(data) == expected_hash


class SessionSecurity:
    """Session security and timeout management"""
    
    @staticmethod
    def get_session_timeout_minutes() -> int:
        """Get session timeout from settings"""
        return getattr(settings, 'HIPAA_SETTINGS', {}).get('SESSION_TIMEOUT', 30)
    
    @staticmethod
    def is_session_expired(last_activity: datetime) -> bool:
        """Check if session has expired"""
        timeout_minutes = SessionSecurity.get_session_timeout_minutes()
        expiry_time = last_activity + timedelta(minutes=timeout_minutes)
        return datetime.now() > expiry_time
    
    @staticmethod
    def update_session_activity(session_key: str) -> None:
        """Update session last activity time"""
        cache_key = f"session_activity_{session_key}"
        cache.set(cache_key, datetime.now(), timeout=3600)  # Store for 1 hour
    
    @staticmethod
    def get_session_activity(session_key: str) -> Optional[datetime]:
        """Get session last activity time"""
        cache_key = f"session_activity_{session_key}"
        return cache.get(cache_key)


class PasswordPolicy:
    """HIPAA-compliant password policy enforcement"""
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Union[bool, str]]:
        """Validate password against HIPAA requirements"""
        errors = []
        
        # Minimum length
        if len(password) < 12:
            errors.append("Password must be at least 12 characters long")
        
        # Character requirements
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*(),.?\":{}|<>" for c in password)
        
        character_types = sum([has_upper, has_lower, has_digit, has_special])
        
        if character_types < 3:
            errors.append("Password must contain at least 3 different character types (uppercase, lowercase, digits, special characters)")
        
        # Common password check
        common_passwords = ['password', '123456', 'qwerty', 'admin', 'user']
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }


class AccessLogging:
    """HIPAA access logging utilities"""
    
    @staticmethod
    def log_phi_access(user_id: str, patient_id: str, action: str, ip_address: str, user_agent: str) -> None:
        """Log PHI access for HIPAA compliance"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'patient_id': patient_id,
            'action': action,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'compliance_type': 'HIPAA_PHI_ACCESS'
        }
        
        # Log to dedicated audit logger
        audit_logger = logging.getLogger('audit')
        audit_logger.info(f"PHI_ACCESS: {json.dumps(log_data)}")
    
    @staticmethod
    def log_failed_access(user_id: Optional[str], resource: str, ip_address: str, reason: str) -> None:
        """Log failed access attempts"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id or 'unknown',
            'resource': resource,
            'ip_address': ip_address,
            'reason': reason,
            'event_type': 'FAILED_ACCESS'
        }
        
        audit_logger = logging.getLogger('audit')
        audit_logger.warning(f"FAILED_ACCESS: {json.dumps(log_data)}")


class DataMasking:
    """Data masking utilities for HIPAA compliance"""
    
    @staticmethod
    def mask_ssn(ssn: str) -> str:
        """Mask SSN for display purposes"""
        if len(ssn) >= 4:
            return f"***-**-{ssn[-4:]}"
        return "***-**-****"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask phone number for display purposes"""
        if len(phone) >= 4:
            return f"***-***-{phone[-4:]}"
        return "***-***-****"
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email for display purposes"""
        if '@' in email:
            username, domain = email.split('@', 1)
            if len(username) > 2:
                masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
            else:
                masked_username = '*' * len(username)
            return f"{masked_username}@{domain}"
        return email
    
    @staticmethod
    def mask_address(address: str) -> str:
        """Mask address for display purposes"""
        words = address.split()
        if len(words) > 2:
            return f"{words[0]} *** {words[-1]}"
        return "*** ***"


# Initialize encryption instance
encryption = HIPAAEncryption()

# Convenience functions for model field encryption
def encrypt_field(value: str) -> str:
    """Encrypt a field value for database storage"""
    if not value:
        return value
    try:
        return encryption.encrypt(value)
    except Exception as e:
        logger.error(f"Field encryption error: {str(e)}")
        return value  # Return original value if encryption fails

def decrypt_field(encrypted_value: str) -> str:
    """Decrypt a field value from database"""
    if not encrypted_value:
        return encrypted_value
    try:
        return encryption.decrypt(encrypted_value)
    except Exception as e:
        logger.error(f"Field decryption error: {str(e)} - This likely means the ENCRYPTION_KEY has changed or is different between environments")
        return "[Message could not be decrypted - encryption key mismatch]"  # Clear error message instead of gibberish