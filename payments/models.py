from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class PaymentProvider(models.TextChoices):
    STRIPE = 'stripe', 'Stripe'
    IYZICO = 'iyzico', 'iyzico'
    PAYTR = 'paytr', 'PayTR'


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    CANCELLED = 'cancelled', 'Cancelled'
    REFUNDED = 'refunded', 'Refunded'


class PaymentType(models.TextChoices):
    SUBSCRIPTION = 'subscription', 'Subscription'
    WORKFLOW_PURCHASE = 'workflow_purchase', 'Workflow Purchase'
    ONE_TIME = 'one_time', 'One Time Payment'


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    payment_id = models.CharField(max_length=100, unique=True)
    provider = models.CharField(max_length=20, choices=PaymentProvider.choices)
    payment_type = models.CharField(max_length=30, choices=PaymentType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='TRY')
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    provider_payment_id = models.CharField(max_length=200, blank=True)
    provider_response = models.JSONField(default=dict)

    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)

    subscription_id = models.ForeignKey(
        'subscriptions.UserServiceSubscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.amount} {self.currency} - {self.status}"

    @property
    def is_successful(self):
        return self.status == PaymentStatus.COMPLETED


class PaymentMethod(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    provider = models.CharField(max_length=20, choices=PaymentProvider.choices)
    provider_method_id = models.CharField(max_length=200)
    card_last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - **** {self.card_last_four} ({self.card_brand})"


class Invoice(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)

    billing_name = models.CharField(max_length=100)
    billing_email = models.EmailField()
    billing_address = models.TextField()
    billing_city = models.CharField(max_length=50)
    billing_country = models.CharField(max_length=50)
    billing_postal_code = models.CharField(max_length=20)

    tax_number = models.CharField(max_length=20, blank=True)
    company_name = models.CharField(max_length=100, blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.total_amount}"


class Refund(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    refund_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=PaymentStatus.choices)
    provider_refund_id = models.CharField(max_length=200, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Refund {self.refund_id} - {self.amount}"
