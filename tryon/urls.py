from django.urls import path
from . import views

app_name = 'tryon'

urlpatterns = [
    path('create/', views.TryOnRequestCreateView.as_view(), name='create-request'),
    path('requests/', views.TryOnRequestListView.as_view(), name='list-requests'),
    path('requests/<uuid:pk>/', views.TryOnRequestDetailView.as_view(), name='request-detail'),
    path('requests/<uuid:request_id>/status/', views.check_request_status, name='check-status'),
    path('stats/', views.user_tryon_stats, name='user-stats'),

    path('demo/<str:token>/', views.demo_tryon, name='demo-tryon'),
]