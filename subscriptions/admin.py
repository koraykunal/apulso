from django.contrib import admin
from .models import Service, ServicePlan, UserServiceSubscription, UsageLog


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'service_type', 'is_active', 'created_at']
    list_filter = ['service_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(ServicePlan)
class ServicePlanAdmin(admin.ModelAdmin):
    list_display = ['service', 'name', 'plan_type', 'price_monthly', 'price_yearly', 'usage_limit', 'is_active']
    list_filter = ['service', 'plan_type', 'is_active']
    search_fields = ['name', 'description']
    raw_id_fields = ['service']


@admin.register(UserServiceSubscription)
class UserServiceSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'service', 'plan', 'status', 'current_usage', 'usage_remaining', 'start_date', 'end_date']
    list_filter = ['status', 'service', 'billing_cycle']
    search_fields = ['user__email', 'user__username']
    raw_id_fields = ['user', 'service', 'plan']
    readonly_fields = ['current_usage', 'last_usage_reset', 'created_at', 'updated_at']


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'amount', 'description', 'created_at']
    list_filter = ['subscription__service', 'created_at']
    search_fields = ['subscription__user__email', 'description']
    raw_id_fields = ['subscription']
    readonly_fields = ['created_at']
