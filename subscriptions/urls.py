from django.urls import path
from .views import (
    SubscriptionPlanListView, UserSubscriptionView,
    CreateSubscriptionView, CancelSubscriptionView
)

app_name = 'subscriptions'

urlpatterns = [
    path('plans/', SubscriptionPlanListView.as_view(), name='plans'),
    path('my-subscription/', UserSubscriptionView.as_view(), name='my_subscription'),
    path('create/', CreateSubscriptionView.as_view(), name='create'),
    path('cancel/', CancelSubscriptionView.as_view(), name='cancel'),
]