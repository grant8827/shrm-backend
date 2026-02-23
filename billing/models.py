from django.db import models
from django.conf import settings
from decimal import Decimal


class Bill(models.Model):
    """
    Model to store billing information for patients (users with role='client').
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("cash", "Cash"),
        ("credit_card", "Credit Card"),
        ("debit_card", "Debit Card"),
        ("insurance", "Insurance"),
        ("check", "Check"),
        ("other", "Other"),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bills",
        help_text="Patient (user) this bill belongs to",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_bills",
        help_text="Staff/Admin who created this bill",
    )

    # Bill details
    title = models.CharField(max_length=255, help_text="Bill title/description")
    description = models.TextField(
        blank=True, help_text="Detailed description of services"
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Total amount to be paid"
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Amount already paid",
    )

    # Status and dates
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Current status of the bill",
    )
    issue_date = models.DateField(help_text="Date when bill was issued")
    due_date = models.DateField(help_text="Payment due date")
    paid_date = models.DateField(
        null=True, blank=True, help_text="Date when bill was fully paid"
    )

    # Payment details
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        help_text="Method of payment",
    )
    transaction_id = models.CharField(
        max_length=100, blank=True, help_text="Transaction/Reference ID"
    )

    # Additional info
    notes = models.TextField(blank=True, help_text="Internal notes")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Bill"
        verbose_name_plural = "Bills"
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.title} - ${self.amount} ({self.status})"

    @property
    def balance_remaining(self):
        """Calculate remaining balance"""
        return self.amount - self.amount_paid

    @property
    def is_paid(self):
        """Check if bill is fully paid"""
        return self.amount_paid >= self.amount

    @property
    def is_overdue(self):
        """Check if bill is overdue"""
        from django.utils import timezone

        return self.status == "pending" and self.due_date < timezone.now().date()

    def save(self, *args, **kwargs):
        """Auto-update status based on payment"""
        from django.utils import timezone

        # Auto-mark as paid if fully paid
        if self.is_paid and self.status == "pending":
            self.status = "paid"
            if not self.paid_date:
                self.paid_date = timezone.now().date()

        # Auto-mark as overdue if past due date
        elif self.is_overdue and self.status == "pending":
            self.status = "overdue"

        super().save(*args, **kwargs)


class Payment(models.Model):
    """
    Model to track individual payments made towards a bill.
    """

    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name="payments",
        help_text="Bill this payment is for",
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Payment amount"
    )
    payment_date = models.DateField(help_text="Date of payment")
    payment_method = models.CharField(
        max_length=20,
        choices=Bill.PAYMENT_METHOD_CHOICES,
        help_text="Payment method used",
    )
    transaction_id = models.CharField(
        max_length=100, blank=True, help_text="Transaction/Reference ID"
    )
    notes = models.TextField(blank=True, help_text="Payment notes")
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Staff who recorded this payment",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date"]
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"Payment of ${self.amount} for {self.bill.title}"

    def save(self, *args, **kwargs):
        """Update bill's amount_paid when payment is saved"""
        super().save(*args, **kwargs)

        # Update bill's total paid amount
        bill = self.bill
        total_paid = bill.payments.aggregate(models.Sum("amount"))[
            "amount__sum"
        ] or Decimal("0.00")
        bill.amount_paid = total_paid
        bill.save()
