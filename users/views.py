# backend/users/views.py
"""
User authentication and management views for TheraCare EHR System.
HIPAA-compliant user management with comprehensive audit logging.
"""

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from .models import User, RegistrationToken
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    UserListSerializer,
    UserDetailSerializer,
    RegistrationTokenSerializer,
    CompleteRegistrationSerializer
)
from .permissions import IsAdminOrSelf, IsAdminUser, IsTherapistOrAdmin
from .email_service import send_registration_email
import logging

logger = logging.getLogger('theracare.audit')


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view with enhanced security and audit logging."""
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    """Custom token refresh view with audit logging."""
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Log token refresh
            logger.info(
                'JWT token refreshed',
                extra={
                    'event_type': 'token_refresh',
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT'),
                    'timestamp': timezone.now().isoformat(),
                }
            )
        
        return response


class LogoutView(APIView):
    """User logout view with token blacklisting."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Logout user and blacklist refresh token."""
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Log logout
            logger.info(
                'User logged out',
                extra={
                    'event_type': 'user_logout',
                    'user_id': str(request.user.id),
                    'username': request.user.username,
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'timestamp': timezone.now().isoformat(),
                }
            )
            
            return Response(
                {'message': 'Successfully logged out.'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(
                'Logout error',
                extra={
                    'event_type': 'logout_error',
                    'user_id': str(request.user.id) if request.user.is_authenticated else None,
                    'error': str(e),
                    'timestamp': timezone.now().isoformat(),
                }
            )
            return Response(
                {'error': 'An error occurred during logout.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserRegistrationView(generics.CreateAPIView):
    """User registration view with role-based permissions."""
    
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    
    def get_permissions(self):
        """Set permissions based on user role being created."""
        if self.request.method == 'POST':
            # DEVELOPMENT: Allow all role registrations for testing
            # TODO: Restore role-based restrictions in production
            return [permissions.AllowAny()]
            
            # PRODUCTION CODE (commented out for development):
            # Check if this is self-registration or admin creating user
            # role = self.request.data.get('role', 'client')
            # if role == 'client':
            #     # Allow anonymous client registration
            #     return [permissions.AllowAny()]
            # else:
            #     # Require admin permission for staff/therapist creation
            #     return [IsAdminUser()]
        return [permissions.AllowAny()]
    
    def perform_create(self, serializer):
        """Create user with additional audit logging."""
        user = serializer.save()
        
        # Send welcome email for new users (temporarily disabled for development)
        # self.send_welcome_email(user)
        
        return user
    
    def send_welcome_email(self, user):
        """Send welcome email to new user."""
        try:
            subject = f'Welcome to SafeHaven EHR - {user.get_role_display()}'
            message = render_to_string('emails/welcome_email.txt', {
                'user': user,
                'login_url': f"{settings.FRONTEND_URL}/login"
            })
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            logger.info(
                'Welcome email sent',
                extra={
                    'event_type': 'welcome_email_sent',
                    'user_id': str(user.id),
                    'email': user.email,
                    'timestamp': timezone.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(
                'Welcome email failed',
                extra={
                    'event_type': 'welcome_email_failed',
                    'user_id': str(user.id),
                    'email': user.email,
                    'error': str(e),
                    'timestamp': timezone.now().isoformat(),
                }
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile view for authenticated users."""
    
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSelf]
    
    def get_object(self):
        """Get user object - self or specified user for admins."""
        user_id = self.kwargs.get('pk')
        if user_id:
            return get_object_or_404(User, id=user_id)
        return self.request.user
    
    def perform_update(self, serializer):
        """Update user profile with audit logging."""
        old_data = {
            'email': self.get_object().email,
            'first_name': self.get_object().first_name,
            'last_name': self.get_object().last_name,
            'phone_number': self.get_object().phone_number,
        }
        
        user = serializer.save()
        
        # Log profile update
        changed_fields = []
        for field, old_value in old_data.items():
            new_value = getattr(user, field)
            if old_value != new_value:
                changed_fields.append(field)
        
        if changed_fields:
            logger.info(
                'User profile updated',
                extra={
                    'event_type': 'profile_updated',
                    'user_id': str(user.id),
                    'username': user.username,
                    'changed_fields': changed_fields,
                    'updated_by': str(self.request.user.id),
                    'timestamp': timezone.now().isoformat(),
                }
            )


class PasswordChangeView(APIView):
    """Password change view for authenticated users."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Change user password."""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Password changed successfully.'},
                status=status.HTTP_200_OK
            )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class PasswordResetRequestView(APIView):
    """Password reset request view for unauthenticated users."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Send password reset email."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email, is_active=True)
                self.send_reset_email(user, request)
                
                logger.info(
                    'Password reset requested',
                    extra={
                        'event_type': 'password_reset_requested',
                        'user_id': str(user.id),
                        'email': email,
                        'ip_address': request.META.get('REMOTE_ADDR'),
                        'timestamp': timezone.now().isoformat(),
                    }
                )
            except User.DoesNotExist:
                # Don't reveal if email exists or not
                logger.warning(
                    'Password reset requested for non-existent email',
                    extra={
                        'event_type': 'password_reset_invalid_email',
                        'email': email,
                        'ip_address': request.META.get('REMOTE_ADDR'),
                        'timestamp': timezone.now().isoformat(),
                    }
                )
            
            # Always return success to prevent email enumeration
            return Response(
                {'message': 'If the email address is registered, you will receive password reset instructions.'},
                status=status.HTTP_200_OK
            )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def send_reset_email(self, user, request):
        """Send password reset email."""
        try:
            # Generate reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset URL
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
            
            # Send email
            subject = 'SafeHaven EHR - Password Reset Request'
            message = render_to_string('emails/password_reset_email.txt', {
                'user': user,
                'reset_url': reset_url,
                'domain': request.get_host(),
            })
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
        except Exception as e:
            logger.error(
                'Password reset email failed',
                extra={
                    'event_type': 'password_reset_email_failed',
                    'user_id': str(user.id),
                    'email': user.email,
                    'error': str(e),
                    'timestamp': timezone.now().isoformat(),
                }
            )


class PasswordResetConfirmView(APIView):
    """Password reset confirmation view."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, uidb64, token):
        """Confirm password reset with token."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Decode user ID
                uid = force_str(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid)
                
                # Verify token
                if not default_token_generator.check_token(user, token):
                    return Response(
                        {'error': 'Invalid or expired reset token.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Update password
                new_password = serializer.validated_data['new_password']
                user.set_password(new_password)
                user.requires_password_change = False
                user.password_changed_at = timezone.now()
                user.reset_failed_login_attempts()  # Reset any lockout
                user.save()
                
                logger.info(
                    'Password reset completed',
                    extra={
                        'event_type': 'password_reset_completed',
                        'user_id': str(user.id),
                        'username': user.username,
                        'ip_address': request.META.get('REMOTE_ADDR'),
                        'timestamp': timezone.now().isoformat(),
                    }
                )
                
                return Response(
                    {'message': 'Password reset successfully.'},
                    status=status.HTTP_200_OK
                )
                
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response(
                    {'error': 'Invalid reset link.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class UserListView(generics.ListAPIView):
    """List users based on role and permissions."""
    
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user role and permissions."""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Admins and therapists can see all users
        if user.role in ['admin', 'therapist']:
            pass  # No filtering needed - show all users
        
        # Patients can see their therapist and admins
        elif user.role == 'client':
            queryset = queryset.filter(
                Q(role='admin') | 
                Q(role='therapist')  # In production, filter by assigned therapist only
            )
        
        # Staff can see admins and therapists
        elif user.role == 'staff':
            queryset = queryset.filter(
                Q(role='admin') | 
                Q(role='therapist')
            )
        
        # Additional query parameter filters (only for admins)
        if user.role == 'admin':
            # Filter by role (supports comma-separated values like "therapist,admin")
            role = self.request.query_params.get('role')
            if role:
                roles = [r.strip() for r in role.split(',')]
                queryset = queryset.filter(role__in=roles)
            
            # Filter by active status
            is_active = self.request.query_params.get('is_active')
            if is_active is not None:
                queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
            # Search by name or username
            search = self.request.query_params.get('search')
            if search:
                queryset = queryset.filter(
                    Q(username__icontains=search) |
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search) |
                    Q(email__icontains=search)
                )
        
        return queryset


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """User detail view - admin only or self."""
    
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def check_permissions(self, request):
        """Override to ensure authenticated users can access."""
        super().check_permissions(request)
    
    def check_object_permissions(self, request, obj):
        """Check if user has permission to access this specific user object."""
        # Admin can access any user
        if request.user.role == 'admin':
            return
        
        # Users can only access their own object
        if obj.id != request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only access your own information unless you are an administrator.")
        
        super().check_object_permissions(request, obj)
    
    def perform_update(self, serializer):
        """Update user with audit logging."""
        try:
            # Get the current state before updating
            instance = self.get_object()
            old_is_active = instance.is_active
            old_role = instance.role
            
            # Save the updated user
            user = serializer.save()
            
            # Log significant changes
            if old_is_active != user.is_active:
                logger.warning(
                    f'User account {"activated" if user.is_active else "deactivated"}',
                    extra={
                        'event_type': 'user_status_changed',
                        'user_id': str(user.id),
                        'username': user.username,
                        'is_active': user.is_active,
                        'changed_by': str(self.request.user.id),
                        'timestamp': timezone.now().isoformat(),
                    }
                )
            
            if old_role != user.role:
                logger.warning(
                    'User role changed',
                    extra={
                        'event_type': 'user_role_changed',
                        'user_id': str(user.id),
                        'username': user.username,
                        'old_role': old_role,
                        'new_role': user.role,
                        'changed_by': str(self.request.user.id),
                        'timestamp': timezone.now().isoformat(),
                    }
                )
            return user
        except Exception as e:
            logger.error(
                f'Error updating user: {str(e)}',
                extra={
                    'event_type': 'user_update_error',
                    'error': str(e),
                    'changed_by': str(self.request.user.id),
                    'timestamp': timezone.now().isoformat(),
                }
            )
            raise
    
    def destroy(self, request, *args, **kwargs):
        """Delete user account permanently."""
        instance = self.get_object()
        
        # Prevent deleting yourself
        if instance.id == request.user.id:
            return Response(
                {'error': 'You cannot delete your own account.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log before deletion
        logger.warning(
            'User account deleted permanently',
            extra={
                'event_type': 'user_deleted',
                'user_id': str(instance.id),
                'username': instance.username,
                'deleted_by': str(request.user.id),
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        # Actually delete the user
        instance.delete()
        
        return Response(
            {'message': 'User deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def unlock_user_account(request, user_id):
    """Unlock a locked user account - admin only."""
    try:
        user = get_object_or_404(User, id=user_id)
        
        user.reset_failed_login_attempts()
        
        logger.info(
            'User account unlocked',
            extra={
                'event_type': 'user_account_unlocked',
                'user_id': str(user.id),
                'username': user.username,
                'unlocked_by': str(request.user.id),
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        return Response(
            {'message': f'Account for {user.username} has been unlocked.'},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to unlock account.'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def force_password_change(request, user_id):
    """Force user to change password on next login - admin only."""
    try:
        user = get_object_or_404(User, id=user_id)
        
        user.requires_password_change = True
        user.save(update_fields=['requires_password_change'])
        
        logger.info(
            'Force password change set',
            extra={
                'event_type': 'force_password_change',
                'user_id': str(user.id),
                'username': user.username,
                'set_by': str(request.user.id),
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        return Response(
            {'message': f'{user.username} will be required to change password on next login.'},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to set password change requirement.'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    """Get current authenticated user information."""
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def validate_registration_token(request):
    """Validate a registration token and return patient data"""
    token_value = request.data.get('token')
    
    if not token_value:
        return Response(
            {'error': 'Token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        token = RegistrationToken.objects.get(token=token_value)
        
        if not token.is_valid():
            return Response(
                {'error': 'This registration link has expired or has already been used.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = RegistrationTokenSerializer(token)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except RegistrationToken.DoesNotExist:
        return Response(
            {'error': 'Invalid registration link.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def send_patient_registration_email(request):
    """Send registration email to a new patient"""
    email = request.data.get('email')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    phone_number = request.data.get('phone_number', '')
    
    if not all([email, first_name, last_name]):
        return Response(
            {'error': 'Email, first name, and last name are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    success, token = send_registration_email(email, first_name, last_name, phone_number)
    
    if success:
        return Response({
            'message': 'Registration email sent successfully',
            'token_id': str(token.id)
        }, status=status.HTTP_200_OK)
    else:
        return Response(
            {'error': 'Failed to send registration email'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def complete_registration(request):
    """Complete patient registration by creating user account"""
    serializer = CompleteRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Log successful registration
        logger.info(
            'Patient completed registration',
            extra={
                'event_type': 'registration_completed',
                'user_id': str(user.id),
                'username': user.username,
                'email': user.email,
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        # Generate tokens for auto-login
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Registration completed successfully',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)