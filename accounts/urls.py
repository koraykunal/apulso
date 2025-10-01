from django.urls import path
from .views import RegisterView, login_view, UserDetailView, UserProfileView
from .custom_views import refresh_token_view, logout_view, csrf_token_view

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('token/refresh/', refresh_token_view, name='token_refresh'),
    path('csrf/', csrf_token_view, name='csrf_token'),
    path('profile/', UserDetailView.as_view(), name='user_profile'),
    path('profile/details/', UserProfileView.as_view(), name='user_profile_details'),
]