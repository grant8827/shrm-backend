# backend/users/admin.py
"""
Django admin configuration for TheraCare User management.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django import forms
from .models import User
from core.security import encryption


class TheraCareUserCreationForm(UserCreationForm):
    """Custom user creation form."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "first_name", "last_name", "username", "role")


class TheraCareUserChangeForm(UserChangeForm):
    """Custom user change form with decrypted fields."""

    # Override encrypted fields with regular CharFields for editing
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    phone = forms.CharField(max_length=20, required=False)

    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        """Initialize form with decrypted values."""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Populate fields with decrypted values
            self.fields["first_name"].initial = self.instance.get_decrypted_first_name()
            self.fields["last_name"].initial = self.instance.get_decrypted_last_name()
            self.fields["phone"].initial = self.instance.get_decrypted_phone()

    def save(self, commit=True):
        """Save with encryption."""
        user = super().save(commit=False)

        # The model's save() method will handle encryption
        # Just set the values from the form
        if self.cleaned_data.get("first_name"):
            user.first_name = self.cleaned_data["first_name"]
        if self.cleaned_data.get("last_name"):
            user.last_name = self.cleaned_data["last_name"]
        if self.cleaned_data.get("phone"):
            user.phone = self.cleaned_data["phone"]

        if commit:
            user.save()
        return user


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for TheraCare User model."""

    form = TheraCareUserChangeForm
    add_form = TheraCareUserCreationForm

    list_display = [
        "email",
        "get_full_name",
        "role",
        "is_active",
        "is_locked",
        "last_login",
        "date_joined",
    ]
    list_filter = [
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
        "last_login",
    ]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "username", "phone")}),
        (
            "Role & Permissions",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Security",
            {
                "fields": (
                    "must_change_password",
                    "failed_login_attempts",
                    "account_locked_until",
                )
            },
        ),
        (
            "Important Dates",
            {"fields": ("last_login", "date_joined", "last_password_change")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "username",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    readonly_fields = [
        "date_joined",
        "last_login",
        "last_password_change",
        "failed_login_attempts",
        "account_locked_until",
    ]

    def get_full_name(self, obj):
        """Display full name."""
        return obj.get_full_name() or "-"

    get_full_name.short_description = "Full Name"

    def is_locked(self, obj):
        """Display lock status."""
        if obj.is_account_locked():
            return format_html(
                '<span style="color: red; font-weight: bold;">🔒 LOCKED</span>'
            )
        return format_html('<span style="color: green;">✓ Active</span>')

    is_locked.short_description = "Account Status"

    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related()

    actions = ["unlock_accounts", "force_password_change", "deactivate_users"]

    def unlock_accounts(self, request, queryset):
        """Bulk unlock user accounts."""
        count = 0
        for user in queryset:
            if user.is_account_locked():
                user.reset_failed_login_attempts()
                count += 1

        self.message_user(request, f"Successfully unlocked {count} user account(s).")

    unlock_accounts.short_description = "Unlock selected accounts"

    def force_password_change(self, request, queryset):
        """Force password change on next login."""
        count = queryset.update(must_change_password=True)
        self.message_user(
            request, f"Password change required for {count} user(s) on next login."
        )

    force_password_change.short_description = "Force password change on next login"

    def deactivate_users(self, request, queryset):
        """Deactivate user accounts."""
        count = queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {count} user account(s).")

    deactivate_users.short_description = "Deactivate selected accounts"
