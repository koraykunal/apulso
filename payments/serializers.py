from rest_framework import serializers
from .models import Payment, PaymentMethod, Invoice, PaymentProvider, PaymentType


class PaymentSerializer(serializers.ModelSerializer):
    is_successful = serializers.ReadOnlyField()

    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'provider', 'payment_type', 'amount', 'currency',
            'status', 'description', 'is_successful', 'paid_at', 'created_at'
        ]
        read_only_fields = [
            'payment_id', 'status', 'provider_payment_id', 'paid_at', 'created_at'
        ]


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'provider', 'card_last_four', 'card_brand',
            'is_default', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']


class CreatePaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(default='TRY', max_length=3)
    provider = serializers.ChoiceField(choices=PaymentProvider.choices)
    payment_type = serializers.ChoiceField(choices=PaymentType.choices)
    description = serializers.CharField(required=False, allow_blank=True)

    subscription_id = serializers.IntegerField(required=False)
    workflow_id = serializers.IntegerField(required=False)

    return_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)

    def validate(self, attrs):
        payment_type = attrs.get('payment_type')

        if payment_type == PaymentType.SUBSCRIPTION and not attrs.get('subscription_id'):
            raise serializers.ValidationError(
                "subscription_id is required for subscription payments"
            )

        if payment_type == PaymentType.WORKFLOW_PURCHASE and not attrs.get('workflow_id'):
            raise serializers.ValidationError(
                "workflow_id is required for workflow purchase payments"
            )

        return attrs


class InvoiceSerializer(serializers.ModelSerializer):
    payment = PaymentSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['invoice_number', 'issued_at']