from django.contrib import admin
from .models import Bill, Payment


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ['title', 'patient', 'amount', 'amount_paid', 'balance_remaining', 'status', 'due_date', 'created_at']
    list_filter = ['status', 'issue_date', 'due_date']
    search_fields = ['title', 'patient__first_name', 'patient__last_name', 'transaction_id']
    readonly_fields = ['balance_remaining', 'is_paid', 'is_overdue', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient', 'created_by', 'title', 'description')
        }),
        ('Billing Details', {
            'fields': ('amount', 'amount_paid', 'balance_remaining', 'status')
        }),
        ('Dates', {
            'fields': ('issue_date', 'due_date', 'paid_date')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'transaction_id')
        }),
        ('Additional', {
            'fields': ('notes', 'is_paid', 'is_overdue', 'created_at', 'updated_at')
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['bill', 'amount', 'payment_date', 'payment_method', 'recorded_by', 'created_at']
    list_filter = ['payment_date', 'payment_method']
    search_fields = ['bill__title', 'transaction_id']
    readonly_fields = ['created_at']
