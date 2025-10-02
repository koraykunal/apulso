from rest_framework import serializers
from .models import Service, ServicePlan, UserServiceSubscription, UsageLog, BillingCycle


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'service_type', 'name', 'description', 'is_active', 'icon']


class ServicePlanSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = ServicePlan
        fields = [
            'id', 'service', 'name', 'plan_type', 'description',
            'price_monthly', 'price_yearly', 'usage_limit', 'features', 'is_active'
        ]


class UserServiceSubscriptionSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    plan = ServicePlanSerializer(read_only=True)
    usage_percentage = serializers.IntegerField(read_only=True)
    usage_remaining = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserServiceSubscription
        fields = [
            'id', 'service', 'plan', 'billing_cycle', 'status',
            'start_date', 'end_date', 'current_usage', 'usage_percentage',
            'usage_remaining', 'is_active', 'auto_renew', 'created_at'
        ]


class UsageLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageLog
        fields = ['id', 'amount', 'description', 'metadata', 'created_at']


class CreateSubscriptionSerializer(serializers.Serializer):
    service_id = serializers.IntegerField()
    plan_id = serializers.IntegerField()
    billing_cycle = serializers.ChoiceField(choices=BillingCycle.choices)
    payment_method_id = serializers.CharField(required=False)

    def validate(self, attrs):
        try:
            service = Service.objects.get(id=attrs['service_id'], is_active=True)
            plan = ServicePlan.objects.get(id=attrs['plan_id'], service=service, is_active=True)
        except Service.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive service")
        except ServicePlan.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive plan for this service")

        return attrs