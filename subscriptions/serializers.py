from rest_framework import serializers
from .models import SubscriptionPlan, Subscription, BillingCycle


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    workflows_remaining = serializers.ReadOnlyField()
    executions_remaining = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'billing_cycle', 'status', 'start_date', 'end_date',
            'auto_renew', 'current_workflow_count', 'current_execution_count',
            'workflows_remaining', 'executions_remaining', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'status', 'start_date', 'end_date', 'current_workflow_count',
            'current_execution_count', 'created_at', 'updated_at'
        ]


class CreateSubscriptionSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    billing_cycle = serializers.ChoiceField(choices=BillingCycle.choices)
    payment_method_id = serializers.CharField(required=False)

    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive plan")


class CancelSubscriptionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)