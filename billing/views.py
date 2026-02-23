from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Q
from django.utils import timezone
from .models import Bill, Payment
from .serializers import (
    BillSerializer,
    BillCreateSerializer,
    BillUpdateSerializer,
    PaymentSerializer,
)


class BillingPermission(permissions.BasePermission):
    """
    Custom permission for billing:
    - Staff and Admin can view all, create, update, delete
    - Patients can only view their own bills
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Staff and Admin have full access
        if request.user.role in ["admin", "staff"]:
            return True

        # Clients and Therapists can only view (GET)
        if (
            request.user.role in ["client", "therapist"]
            and request.method in permissions.SAFE_METHODS
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Staff and Admin can do anything
        if request.user.role in ["admin", "staff"]:
            return True

        # Clients can only view their own bills
        if request.user.role == "client":
            return (
                obj.patient == request.user
                and request.method in permissions.SAFE_METHODS
            )

        return False


class BillViewSet(viewsets.ModelViewSet):
    permission_classes = [BillingPermission]

    def get_queryset(self):
        user = self.request.user

        # Staff and Admin see all bills
        if user.role in ["admin", "staff"]:
            queryset = Bill.objects.select_related(
                "patient", "created_by"
            ).prefetch_related("payments")

            # Filter by patient if specified
            patient_id = self.request.query_params.get("patient")
            if patient_id:
                queryset = queryset.filter(patient_id=patient_id)

            # Filter by status
            bill_status = self.request.query_params.get("status")
            if bill_status:
                queryset = queryset.filter(status=bill_status)

            return queryset

        # Clients see only their own bills
        elif user.role == "client":
            return (
                Bill.objects.filter(patient=user)
                .select_related("patient", "created_by")
                .prefetch_related("payments")
            )

        return Bill.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return BillCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return BillUpdateSerializer
        return BillSerializer

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get billing summary for a patient or all patients"""
        user = request.user

        if user.role in ["admin", "staff"]:
            patient_id = request.query_params.get("patient")
            if patient_id:
                bills = Bill.objects.filter(patient_id=patient_id)
            else:
                bills = Bill.objects.all()
        else:
            bills = Bill.objects.filter(patient=user)

        total_billed = bills.aggregate(Sum("amount"))["amount__sum"] or 0
        total_paid = bills.aggregate(Sum("amount_paid"))["amount__sum"] or 0
        total_pending = (
            bills.filter(status="pending").aggregate(Sum("amount"))["amount__sum"] or 0
        )
        total_overdue = (
            bills.filter(status="overdue").aggregate(Sum("amount"))["amount__sum"] or 0
        )

        return Response(
            {
                "total_billed": total_billed,
                "total_paid": total_paid,
                "total_outstanding": total_billed - total_paid,
                "total_pending": total_pending,
                "total_overdue": total_overdue,
                "bill_count": bills.count(),
                "paid_count": bills.filter(status="paid").count(),
                "pending_count": bills.filter(status="pending").count(),
                "overdue_count": bills.filter(status="overdue").count(),
            }
        )

    @action(detail=True, methods=["post"])
    def add_payment(self, request, pk=None):
        """Add a payment to a bill"""
        bill = self.get_object()

        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(bill=bill, recorded_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def mark_paid(self, request, pk=None):
        """Mark a bill as paid"""
        bill = self.get_object()

        bill.status = "paid"
        bill.paid_date = timezone.now().date()
        bill.amount_paid = bill.amount

        payment_method = request.data.get("payment_method", "")
        transaction_id = request.data.get("transaction_id", "")

        if payment_method:
            bill.payment_method = payment_method
        if transaction_id:
            bill.transaction_id = transaction_id

        bill.save()

        serializer = self.get_serializer(bill)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a bill"""
        bill = self.get_object()
        bill.status = "cancelled"
        bill.save()

        serializer = self.get_serializer(bill)
        return Response(serializer.data)


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [BillingPermission]

    def get_queryset(self):
        user = self.request.user

        if user.role in ["admin", "staff"]:
            return Payment.objects.select_related("bill", "recorded_by")
        elif user.role == "patient":
            return Payment.objects.filter(bill__patient__user=user).select_related(
                "bill", "recorded_by"
            )

        return Payment.objects.none()

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)
