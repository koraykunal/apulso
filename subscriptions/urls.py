from django.urls import path
from .views import (
    ServiceListView, service_plans_view, user_subscriptions_view,
    create_subscription_view, cancel_subscription_view, check_service_access_view
)

app_name = 'subscriptions'

urlpatterns = [
    path('services/', ServiceListView.as_view(), name='services'),
    path('services/<int:service_id>/plans/', service_plans_view, name='service_plans'),
    path('my-subscriptions/', user_subscriptions_view, name='my_subscriptions'),
    path('create/', create_subscription_view, name='create'),
    path('cancel/<int:subscription_id>/', cancel_subscription_view, name='cancel'),
    path('check-access/<str:service_type>/', check_service_access_view, name='check_access'),
]