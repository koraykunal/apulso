from django.contrib import admin
from .models import Payment, PaymentMethod, Invoice, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'user', 'amount', 'currency', 'status', 'provider', 'created_at']
    list_filter = ['status', 'provider', 'payment_type', 'created_at']
    search_fields = ['user__email', 'payment_id', 'provider_payment_id']
    raw_id_fields = ['user']
    readonly_fields = ['payment_id', 'provider_payment_id', 'created_at', 'updated_at']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['user', 'provider', 'card_last_four', 'card_brand', 'is_default', 'is_active']
    list_filter = ['provider', 'card_brand', 'is_default', 'is_active']
    search_fields = ['user__email', 'card_last_four']
    raw_id_fields = ['user']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'billing_name', 'total_amount', 'issued_at']
    list_filter = ['issued_at']
    search_fields = ['invoice_number', 'billing_name', 'billing_email']
    readonly_fields = ['invoice_number', 'issued_at']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['refund_id', 'payment', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['refund_id', 'payment__payment_id']
    raw_id_fields = ['payment']
    readonly_fields = ['refund_id', 'created_at']
