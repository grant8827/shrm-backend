from rest_framework import serializers
from .models import Bill, Payment


class PaymentSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "bill",
            "amount",
            "payment_date",
            "payment_method",
            "transaction_id",
            "notes",
            "recorded_by",
            "recorded_by_name",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "recorded_by_name"]

    def get_recorded_by_name(self, obj):
        if obj.recorded_by:
            return obj.recorded_by.get_full_name()
        return None


class BillSerializer(serializers.ModelSerializer):
    balance_remaining = serializers.ReadOnlyField()
    is_paid = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    created_by_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Bill
        fields = [
            "id",
            "patient",
            "patient_name",
            "created_by",
            "created_by_name",
            "title",
            "description",
            "amount",
            "amount_paid",
            "balance_remaining",
            "status",
            "issue_date",
            "due_date",
            "paid_date",
            "payment_method",
            "transaction_id",
            "notes",
            "is_paid",
            "is_overdue",
            "payments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "balance_remaining",
            "is_paid",
            "is_overdue",
            "patient_name",
            "created_by_name",
        ]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name()
        return None

    def get_patient_name(self, obj):
        return obj.patient.get_full_name()


class BillCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = [
            "patient",
            "title",
            "description",
            "amount",
            "issue_date",
            "due_date",
            "notes",
        ]

    def create(self, validated_data):
        # Set created_by from request user
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class BillUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = [
            "title",
            "description",
            "amount",
            "status",
            "issue_date",
            "due_date",
            "payment_method",
            "transaction_id",
            "notes",
        ]
