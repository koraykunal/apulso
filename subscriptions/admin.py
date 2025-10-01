from django.contrib import admin
from .models import SubscriptionPlan, Subscription, SubscriptionHistory


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price_monthly', 'price_yearly', 'is_active']
    list_filter = ['plan_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'billing_cycle', 'start_date', 'end_date']
    list_filter = ['status', 'billing_cycle', 'plan__plan_type']
    search_fields = ['user__email', 'user__username']
    raw_id_fields = ['user']


@admin.register(SubscriptionHistory)
class SubscriptionHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'previous_status', 'new_status', 'created_at']
    list_filter = ['action', 'previous_status', 'new_status']
    search_fields = ['user__email']
    readonly_fields = ['created_at']
