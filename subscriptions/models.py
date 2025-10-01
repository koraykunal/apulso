from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class PlanType(models.TextChoices):
    BASIC = 'basic', 'Basic'
    PRO = 'pro', 'Pro'
    ENTERPRISE = 'enterprise', 'Enterprise'


class BillingCycle(models.TextChoices):
    MONTHLY = 'monthly', 'Monthly'
    YEARLY = 'yearly', 'Yearly'


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50)
    plan_type = models.CharField(max_length=20, choices=PlanType.choices)
    description = models.TextField()
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2)
    workflow_limit = models.IntegerField(help_text="Maximum number of workflows")
    execution_limit = models.IntegerField(help_text="Monthly execution limit")
    storage_limit = models.IntegerField(help_text="Storage limit in MB")
    support_level = models.CharField(max_length=50, default="Email")
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=list, help_text="List of features")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.plan_type}"

    def get_price(self, billing_cycle):
        return self.price_yearly if billing_cycle == BillingCycle.YEARLY else self.price_monthly


class SubscriptionStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    CANCELLED = 'cancelled', 'Cancelled'
    EXPIRED = 'expired', 'Expired'
    PENDING = 'pending', 'Pending'


class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    billing_cycle = models.CharField(max_length=10, choices=BillingCycle.choices, default=BillingCycle.MONTHLY)
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.PENDING)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    current_workflow_count = models.IntegerField(default=0)
    current_execution_count = models.IntegerField(default=0)
    last_execution_reset = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"

    @property
    def is_active(self):
        return self.status == SubscriptionStatus.ACTIVE

    @property
    def workflows_remaining(self):
        return max(0, self.plan.workflow_limit - self.current_workflow_count)

    @property
    def executions_remaining(self):
        return max(0, self.plan.execution_limit - self.current_execution_count)

    def can_create_workflow(self):
        return self.is_active and self.workflows_remaining > 0

    def can_execute_workflow(self):
        return self.is_active and self.executions_remaining > 0


class SubscriptionHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.action}"
