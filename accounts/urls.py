from django.urls import path
from .views import (
    RegisterView, login_view, UserDetailView, UserProfileView,
    verify_email, resend_verification_email, request_email_change, verify_email_change
)
from .custom_views import refresh_token_view, logout_view, csrf_token_view

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('verify-email/', verify_email, name='verify_email'),
    path('resend-verification/', resend_verification_email, name='resend_verification'),
    path('request-email-change/', request_email_change, name='request_email_change'),
    path('verify-email-change/', verify_email_change, name='verify_email_change'),
    path('token/refresh/', refresh_token_view, name='token_refresh'),
    path('csrf/', csrf_token_view, name='csrf_token'),
    path('profile/', UserDetailView.as_view(), name='user_profile'),
    path('profile/details/', UserProfileView.as_view(), name='user_profile_details'),
]