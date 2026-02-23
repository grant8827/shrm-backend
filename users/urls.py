# backend/users/urls.py
"""
URL configuration for user authentication and management endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenVerifyView
from . import views

app_name = "users"

# API endpoints
urlpatterns = [
    # Authentication endpoints
    path("login/", views.CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", views.CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("verify/", TokenVerifyView.as_view(), name="token_verify"),
    path(
        "validate/", TokenVerifyView.as_view(), name="token_validate"
    ),  # Alias for verify
    path("logout/", views.LogoutView.as_view(), name="logout"),
    # User registration and profile
    path("register/", views.UserRegistrationView.as_view(), name="user_register"),
    path("profile/", views.UserProfileView.as_view(), name="user_profile"),
    path(
        "profile/<uuid:pk>/",
        views.UserProfileView.as_view(),
        name="user_profile_detail",
    ),
    path("current/", views.current_user, name="current_user"),
    # Password management
    path(
        "password/change/", views.PasswordChangeView.as_view(), name="password_change"
    ),
    path(
        "password/reset/",
        views.PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),
    path(
        "password/reset/confirm/<str:uidb64>/<str:token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    # User management (admin only)
    path("", views.UserListView.as_view(), name="user_list"),
    path("<uuid:pk>/", views.UserDetailView.as_view(), name="user_detail"),
    path(
        "<uuid:user_id>/unlock/", views.unlock_user_account, name="unlock_user_account"
    ),
    path(
        "<uuid:user_id>/force-password-change/",
        views.force_password_change,
        name="force_password_change",
    ),
    # Patient registration completion
    path(
        "registration/send-email/",
        views.send_patient_registration_email,
        name="send_registration_email",
    ),
    path(
        "registration/validate-token/",
        views.validate_registration_token,
        name="validate_registration_token",
    ),
    path(
        "registration/complete/",
        views.complete_registration,
        name="complete_registration",
    ),
]
