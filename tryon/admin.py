from django.contrib import admin
from .models import TryOnRequest, TryOnUsageStats


@admin.register(TryOnRequest)
class TryOnRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'cost', 'created_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'processing_time']
    ordering = ['-created_at']

    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'user', 'status')
        }),
        ('Images', {
            'fields': ('human_image', 'garment_image', 'result_image_url')
        }),
        ('Processing Details', {
            'fields': ('fal_request_id', 'processing_time', 'cost', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )


@admin.register(TryOnUsageStats)
class TryOnUsageStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_requests', 'successful_requests', 'failed_requests', 'total_cost', 'success_rate']
    search_fields = ['user__email']
    readonly_fields = ['success_rate', 'created_at', 'updated_at']
    ordering = ['-total_requests']
