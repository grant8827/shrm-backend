# backend/users/serializers.py
"""
User authentication and management serializers for TheraCare EHR System.
HIPAA-compliant serialization with proper field validation and security.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.utils import timezone
from django.conf import settings
from .models import User, RegistrationToken
import logging

logger = logging.getLogger('theracare.audit')


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with enhanced security and audit logging."""
    
    def validate(self, attrs):
        """Validate credentials and track login attempts."""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if not username or not password:
            raise serializers.ValidationError(
                'Both username and password are required.',
                code='missing_credentials'
            )
        
                # Get user for login attempt tracking
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Log failed login attempt
            logger.warning(
                'Failed login attempt for non-existent user',
                extra={
                    'event_type': 'failed_login',
                    'username': username,
                    'reason': 'user_not_found',
                    'ip_address': self.context.get('request').META.get('REMOTE_ADDR'),
                    'user_agent': self.context.get('request').META.get('HTTP_USER_AGENT'),
                    'timestamp': timezone.now().isoformat(),
                }
            )
            raise serializers.ValidationError(
                'Invalid credentials.',
                code='invalid_credentials'
            )
        
        # Check if account is locked
        if user.is_locked():
            logger.warning(
                'Login attempt on locked account',
                extra={
                    'event_type': 'locked_account_login',
                    'user_id': str(user.id),
                    'username': username,
                    'ip_address': self.context.get('request').META.get('REMOTE_ADDR'),
                    'timestamp': timezone.now().isoformat(),
                }
            )
            raise serializers.ValidationError(
                'Account is temporarily locked due to too many failed login attempts. Please contact support.',
                code='account_locked'
            )
        
        # Check if account is active
        if not user.is_active:
            logger.warning(
                'Login attempt on inactive account',
                extra={
                    'event_type': 'inactive_account_login',
                    'user_id': str(user.id),
                    'username': username,
                    'ip_address': self.context.get('request').META.get('REMOTE_ADDR'),
                    'timestamp': timezone.now().isoformat(),
                }
            )
            raise serializers.ValidationError(
                'Account is inactive. Please contact support.',
                code='account_inactive'
            )
        
        # Authenticate user
        user = authenticate(
            request=self.context.get('request'),
            username=username,
            password=password
        )
        
        if not user:
            # Record failed login attempt
            try:
                existing_user = User.objects.get(username=username)
                existing_user.record_failed_login()
                
                logger.warning(
                    'Failed login attempt',
                    extra={
                        'event_type': 'failed_login',
                        'user_id': str(existing_user.id),
                        'username': username,
                        'reason': 'invalid_password',
                        'failed_attempts': existing_user.failed_login_attempts,
                        'ip_address': self.context.get('request').META.get('REMOTE_ADDR'),
                        'user_agent': self.context.get('request').META.get('HTTP_USER_AGENT'),
                        'timestamp': timezone.now().isoformat(),
                    }
                )
            except User.DoesNotExist:
                pass
            
            raise serializers.ValidationError(
                'Invalid credentials.',
                code='invalid_credentials'
            )
        
        # Reset failed login attempts on successful login
        user.reset_failed_login_attempts()
        
        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Log successful login
        logger.info(
            'Successful user login',
            extra={
                'event_type': 'successful_login',
                'user_id': str(user.id),
                'username': username,
                'role': user.role,
                'ip_address': self.context.get('request').META.get('REMOTE_ADDR'),
                'user_agent': self.context.get('request').META.get('HTTP_USER_AGENT'),
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        # Get token data
        data = super().validate(attrs)
        
        # Add custom claims to token
        refresh = self.get_token(user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        
        # Add user data to response
        try:
            first_name = user.get_decrypted_first_name()
        except Exception as e:
            logger.error(f'Error decrypting first_name during login for user {user.id}: {e}')
            first_name = '[Decryption Error]'
        
        try:
            last_name = user.get_decrypted_last_name()
        except Exception as e:
            logger.error(f'Error decrypting last_name during login for user {user.id}: {e}')
            last_name = '[Decryption Error]'
        
        data['user'] = {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'first_name': first_name,
            'last_name': last_name,
            'is_active': user.is_active,
            'must_change_password': user.must_change_password,
            'last_login': user.last_login.isoformat() if user.last_login else None,
        }
        
        return data
    
    @classmethod
    def get_token(cls, user):
        """Add custom claims to JWT token."""
        token = super().get_token(user)
        
        # Add custom claims
        token['user_id'] = str(user.id)
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        token['is_staff'] = user.is_staff
        token['is_active'] = user.is_active
        
        return token


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with comprehensive validation."""
    
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role', 'phone',
            'is_active'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'is_active': {'default': True}
        }
    
    def validate_username(self, value):
        """Validate username uniqueness and format."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'A user with this username already exists.'
            )
        
        # Username validation rules
        if len(value) < 3:
            raise serializers.ValidationError(
                'Username must be at least 3 characters long.'
            )
        
        if not value.replace('_', '').replace('.', '').isalnum():
            raise serializers.ValidationError(
                'Username can only contain letters, numbers, underscores, and periods.'
            )
        
        return value
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'A user with this email address already exists.'
            )
        return value
    
    def validate_role(self, value):
        """Validate role assignment permissions."""
        # DEVELOPMENT: Allow all roles for testing
        # TODO: Restore role restrictions in production
        return value
        
        # PRODUCTION CODE (commented out for development):
        # request = self.context.get('request')
        # if not request or not request.user.is_authenticated:
        #     # Allow client registration without authentication
        #     if value != 'client':
        #         raise serializers.ValidationError(
        #             'Only client accounts can be self-registered.'
        #         )
        # else:
        #     # Only admin users can create staff/therapist accounts
        #     if value in ['admin', 'therapist', 'staff'] and request.user.role != 'admin':
        #         raise serializers.ValidationError(
        #             'You do not have permission to create accounts with this role.'
        #         )
        # 
        # return value
    
    def validate_password(self, value):
        """Validate password strength using Django's validators."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password != password_confirm:
            raise serializers.ValidationError(
                {'password_confirm': 'Passwords do not match.'}
            )
        
        return attrs
    
    def create(self, validated_data):
        """Create new user with encrypted sensitive fields."""
        # Remove password confirmation from validated data
        validated_data.pop('password_confirm', None)
        
        # Extract password for separate handling
        password = validated_data.pop('password')
        
        # Create user instance
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Log user creation
        logger.info(
            'New user account created',
            extra={
                'event_type': 'user_created',
                'user_id': str(user.id),
                'username': user.username,
                'role': user.role,
                'created_by': str(self.context.get('request').user.id) if self.context.get('request') and self.context.get('request').user.is_authenticated else 'self_registration',
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile information with encrypted fields."""
    
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'phone_number', 'is_active', 'date_joined', 'last_login',
            'requires_password_change'
        ]
        read_only_fields = ['id', 'username', 'role', 'date_joined', 'last_login']
    
    def get_first_name(self, obj):
        """Get decrypted first name."""
        try:
            return obj.get_decrypted_first_name()
        except Exception as e:
            logger.error(f'Error decrypting first_name for user {obj.id}: {e}')
            return '[Decryption Error]'
    
    def get_last_name(self, obj):
        """Get decrypted last name."""
        try:
            return obj.get_decrypted_last_name()
        except Exception as e:
            logger.error(f'Error decrypting last_name for user {obj.id}: {e}')
            return '[Decryption Error]'
    
    def get_full_name(self, obj):
        """Get user's full name."""
        try:
            return obj.get_full_name()
        except Exception as e:
            logger.error(f'Error getting full_name for user {obj.id}: {e}')
            return '[Decryption Error]'


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change with current password verification."""
    
    current_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_current_password(self, value):
        """Validate current password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                'Current password is incorrect.'
            )
        return value
    
    def validate_new_password(self, value):
        """Validate new password strength."""
        try:
            validate_password(value, user=self.context['request'].user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        current_password = attrs.get('current_password')
        
        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {'new_password_confirm': 'New passwords do not match.'}
            )
        
        if new_password == current_password:
            raise serializers.ValidationError(
                {'new_password': 'New password cannot be the same as current password.'}
            )
        
        return attrs
    
    def save(self, **kwargs):
        """Update user password and log the change."""
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        
        user.set_password(new_password)
        user.must_change_password = False
        user.password_changed_at = timezone.now()
        user.last_password_change = timezone.now()
        user.save(update_fields=['password', 'must_change_password', 'password_changed_at', 'last_password_change'])
        
        # Log password change
        logger.info(
            'User password changed',
            extra={
                'event_type': 'password_changed',
                'user_id': str(user.id),
                'username': user.username,
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validate email exists in system."""
        try:
            user = User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""
    
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_new_password(self, value):
        """Validate new password strength."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {'new_password_confirm': 'Passwords do not match.'}
            )
        
        return attrs


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for user list view with limited fields."""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'role', 
            'is_active', 'date_joined', 'last_login'
        ]
    
    def get_full_name(self, obj):
        """Get user's full name."""
        return obj.get_full_name()


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested relationships (e.g., in messages)."""
    
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'role']
        read_only_fields = ['id', 'username', 'email', 'role']
    
    def get_first_name(self, obj):
        """Get decrypted first name."""
        try:
            return obj.get_decrypted_first_name()
        except Exception as e:
            logger.error(f'Error decrypting first_name for user {obj.id}: {e}')
            return '[Decryption Error]'
    
    def get_last_name(self, obj):
        """Get decrypted last name."""
        try:
            return obj.get_decrypted_last_name()
        except Exception as e:
            logger.error(f'Error decrypting last_name for user {obj.id}: {e}')
            return '[Decryption Error]'
    
    def get_full_name(self, obj):
        """Get user's full name."""
        try:
            return obj.get_full_name()
        except Exception as e:
            logger.error(f'Error getting full_name for user {obj.id}: {e}')
            return '[Decryption Error]'


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed user view with all safe fields."""
    
    # Read-only fields for display
    full_name = serializers.SerializerMethodField()
    # Map phone_number to phone model field
    phone_number = serializers.CharField(source='phone', required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'phone_number', 'is_active', 'is_staff', 'date_joined', 
            'last_login', 'requires_password_change', 'failed_login_attempts',
            'locked_until', 'password_changed_at'
        ]
        read_only_fields = [
            'id', 'username', 'date_joined', 'last_login', 'failed_login_attempts', 
            'locked_until', 'password_changed_at', 'full_name'
        ]
    
    def get_full_name(self, obj):
        """Get user's full name."""
        return obj.get_full_name()
    
    def to_representation(self, instance):
        """Custom representation to get decrypted values."""
        data = super().to_representation(instance)
        try:
            data['first_name'] = instance.get_decrypted_first_name()
        except Exception as e:
            logger.error(f'Error decrypting first_name for user {instance.id}: {e}')
            data['first_name'] = '[Decryption Error]'
        
        try:
            data['last_name'] = instance.get_decrypted_last_name()
        except Exception as e:
            logger.error(f'Error decrypting last_name for user {instance.id}: {e}')
            data['last_name'] = '[Decryption Error]'
        
        return data
    
    def update(self, instance, validated_data):
        """Update user instance with validated data."""
        # Only update fields that are actually in the validated_data
        # Don't touch encrypted fields unless explicitly provided
        for field in ['email', 'role', 'is_active', 'is_staff', 'requires_password_change']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        
        # Handle mapped field (phone_number -> phone)
        if 'phone' in validated_data:
            instance.phone = validated_data['phone']
        
        # Only update encrypted fields if they're provided
        # Skip them if not in validated_data to avoid save() issues
        if 'first_name' in validated_data:
            instance.first_name = validated_data['first_name']
        if 'last_name' in validated_data:
            instance.last_name = validated_data['last_name']
        
        instance.save()
        return instance


class RegistrationTokenSerializer(serializers.ModelSerializer):
    """Serializer for registration token"""
    
    class Meta:
        model = RegistrationToken
        fields = ['token', 'email', 'first_name', 'last_name', 'phone_number', 'is_valid']
    
    is_valid = serializers.SerializerMethodField()
    
    def get_is_valid(self, obj):
        return obj.is_valid()


class CompleteRegistrationSerializer(serializers.Serializer):
    """Serializer for completing patient registration"""
    
    token = serializers.CharField(required=True)
    username = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    
    def validate_token(self, value):
        """Validate token exists and is valid"""
        try:
            token = RegistrationToken.objects.get(token=value)
            if not token.is_valid():
                raise serializers.ValidationError('This registration link has expired or has already been used.')
            return value
        except RegistrationToken.DoesNotExist:
            raise serializers.ValidationError('Invalid registration link.')
    
    def validate_username(self, value):
        """Check if username is already taken"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value
    
    def validate(self, attrs):
        """Validate passwords match"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})

        token = RegistrationToken.objects.get(token=attrs['token'])
        if User.objects.filter(email__iexact=token.email).exists():
            raise serializers.ValidationError({
                'token': 'An account for this email already exists. Please sign in or reset your password.'
            })
        
        # Validate password strength
        try:
            validate_password(attrs['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        
        return attrs
    
    def create(self, validated_data):
        """Create user from registration token"""
        token_value = validated_data['token']
        token = RegistrationToken.objects.get(token=token_value)

        try:
            # Create user account
            user = User.objects.create_user(
                username=validated_data['username'],
                email=token.email,
                password=validated_data['password'],
                first_name=token.first_name,
                last_name=token.last_name,
                phone=token.phone_number,
                role=User.Role.CLIENT,
                status=User.Status.ACTIVE
            )
        except IntegrityError:
            raise serializers.ValidationError({
                'token': 'An account for this email already exists. Please sign in or reset your password.'
            })
        
        # Mark token as used
        token.mark_as_used(user)

        # Link user to patient record created earlier (if present)
        try:
            from patients.models import Patient

            patient = (
                Patient.objects.filter(
                    user__isnull=True,
                    email__iexact=token.email,
                    first_name__iexact=token.first_name,
                    last_name__iexact=token.last_name,
                )
                .order_by('-created_at')
                .first()
            )

            if patient:
                patient.user = user
                patient.save(update_fields=['user'])
        except Exception as e:
            logger.error(f'Failed to link patient record for registration token {token.id}: {e}')
        
        return user