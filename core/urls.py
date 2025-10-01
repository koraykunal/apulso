from django.urls import path
from .views import (
    ContactMessageCreateView, FAQListView,
    NewsletterSubscribeView, NotificationListView,
    mark_notification_read, mark_all_notifications_read,
    DemoInvitationCreateView, DemoInvitationListView, demo_access
)

app_name = 'core'

urlpatterns = [
    path('contact/', ContactMessageCreateView.as_view(), name='contact'),
    path('faq/', FAQListView.as_view(), name='faq'),
    path('newsletter/subscribe/', NewsletterSubscribeView.as_view(), name='newsletter_subscribe'),
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('notifications/<int:notification_id>/read/', mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', mark_all_notifications_read, name='mark_all_notifications_read'),

    path('demo/invitations/', DemoInvitationCreateView.as_view(), name='create_demo_invitation'),
    path('demo/invitations/list/', DemoInvitationListView.as_view(), name='list_demo_invitations'),
    path('demo/access/<str:token>/', demo_access, name='demo_access'),
]