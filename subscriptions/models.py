from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class ServiceType(models.TextChoices):
    TRYON = 'tryon', 'AI Virtual Try-On'
    EMAIL = 'email', 'Email Automation'
    CRM = 'crm', 'CRM Integration'
    SOCIAL = 'social', 'Social Media Management'
    DOCUMENT = 'document', 'Document Automation'
    APPOINTMENT = 'appointment', 'Appointment Management'


class PlanType(models.TextChoices):
    BASIC = 'basic', 'Basic'
    PRO = 'pro', 'Pro'
    ENTERPRISE = 'enterprise', 'Enterprise'


class BillingCycle(models.TextChoices):
    MONTHLY = 'monthly', 'Monthly'
    YEARLY = 'yearly', 'Yearly'


class Service(models.Model):
    service_type = models.CharField(max_length=20, choices=ServiceType.choices, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    icon = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['service_type']


class ServicePlan(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='plans')
    name = models.CharField(max_length=50)
    plan_type = models.CharField(max_length=20, choices=PlanType.choices)
    description = models.TextField()
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2)
    usage_limit = models.IntegerField(help_text="Monthly usage limit (e.g., tries, emails sent)")
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=list, help_text="List of features")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.service.name} - {self.name}"

    def get_price(self, billing_cycle):
        return self.price_yearly if billing_cycle == BillingCycle.YEARLY else self.price_monthly

    class Meta:
        ordering = ['service', 'price_monthly']


class SubscriptionStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    CANCELLED = 'cancelled', 'Cancelled'
    EXPIRED = 'expired', 'Expired'
    PENDING = 'pending', 'Pending'


class UserServiceSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_subscriptions')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    plan = models.ForeignKey(ServicePlan, on_delete=models.PROTECT)
    billing_cycle = models.CharField(max_length=10, choices=BillingCycle.choices, default=BillingCycle.MONTHLY)
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.PENDING)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    current_usage = models.IntegerField(default=0)
    last_usage_reset = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.service.name}"

    @property
    def is_active(self):
        return self.status == SubscriptionStatus.ACTIVE and timezone.now() <= self.end_date

    @property
    def usage_remaining(self):
        return max(0, self.plan.usage_limit - self.current_usage)

    @property
    def usage_percentage(self):
        if self.plan.usage_limit == 0:
            return 0
        return int((self.current_usage / self.plan.usage_limit) * 100)

    def can_use_service(self):
        return self.is_active and (self.plan.usage_limit == -1 or self.usage_remaining > 0)

    def increment_usage(self, amount=1):
        self.current_usage += amount
        self.save(update_fields=['current_usage', 'updated_at'])

    def reset_usage(self):
        self.current_usage = 0
        self.last_usage_reset = timezone.now().date()
        self.save(update_fields=['current_usage', 'last_usage_reset', 'updated_at'])

    class Meta:
        unique_together = ['user', 'service']
        ordering = ['-created_at']


class UsageLog(models.Model):
    subscription = models.ForeignKey(UserServiceSubscription, on_delete=models.CASCADE, related_name='usage_logs')
    amount = models.IntegerField(default=1)
    description = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subscription.user.email} - {self.subscription.service.name} - {self.amount}"

    class Meta:
        ordering = ['-created_at']
