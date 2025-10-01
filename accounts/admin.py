from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['email', 'username', 'role', 'is_verified', 'is_active', 'created_at']
    list_filter = ['role', 'is_verified', 'is_active', 'created_at']
    search_fields = ['email', 'username', 'company_name']
    ordering = ['-created_at']

    fieldsets = UserAdmin.fieldsets + (
        ('Ek Bilgiler', {
            'fields': ('role', 'phone', 'company_name', 'tax_number', 'is_verified')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Ek Bilgiler', {
            'fields': ('email', 'role', 'phone', 'company_name', 'tax_number')
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'country']
    list_filter = ['country', 'city']
    search_fields = ['user__email', 'user__username']
