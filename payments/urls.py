from django.urls import path
from .views import (
    CreatePaymentView, PaymentStatusView, WebhookView,
    PaymentMethodListView, InvoiceDetailView
)

app_name = 'payments'

urlpatterns = [
    path('create/', CreatePaymentView.as_view(), name='create'),
    path('status/<str:payment_id>/', PaymentStatusView.as_view(), name='status'),
    path('webhook/<str:provider>/', WebhookView.as_view(), name='webhook'),
    path('methods/', PaymentMethodListView.as_view(), name='methods'),
    path('invoice/<str:invoice_number>/', InvoiceDetailView.as_view(), name='invoice'),
]