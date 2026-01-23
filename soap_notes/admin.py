"""
Django admin configuration for SOAP Notes.
"""
from django.contrib import admin
from .models import SOAPNote


@admin.register(SOAPNote)
class SOAPNoteAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'therapist', 'session_date', 'status', 'created_at']
    list_filter = ['status', 'session_date', 'created_at']
    search_fields = ['patient__username', 'patient__email', 'therapist__username', 'chief_complaint']
    readonly_fields = ['id', 'created_at', 'updated_at', 'finalized_at']
    date_hierarchy = 'session_date'
    
    fieldsets = (
        ('Session Information', {
            'fields': ('patient', 'therapist', 'appointment', 'session_date', 'session_duration', 'chief_complaint')
        }),
        ('SOAP Note', {
            'fields': ('subjective', 'objective', 'assessment', 'plan')
        }),
        ('Status & Metadata', {
            'fields': ('status', 'id', 'created_at', 'updated_at', 'finalized_at')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('patient', 'therapist', 'appointment')
