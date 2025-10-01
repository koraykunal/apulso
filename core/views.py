from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import ContactMessage, FAQ, NewsletterSubscription, Notification
from .serializers import (
    ContactMessageSerializer, FAQSerializer,
    NewsletterSubscriptionSerializer, NotificationSerializer,
    DemoInvitationCreateSerializer, DemoInvitationSerializer, DemoAccessSerializer
)
from .models import DemoInvitation, DemoUsageLog
import logging

logger = logging.getLogger(__name__)


class ContactMessageCreateView(generics.CreateAPIView):
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contact_message = serializer.save()

        return Response({
            'message': 'Your message has been sent successfully. We will get back to you soon.',
            'id': contact_message.id
        }, status=status.HTTP_201_CREATED)


class FAQListView(generics.ListAPIView):
    queryset = FAQ.objects.filter(is_active=True)
    serializer_class = FAQSerializer
    permission_classes = [permissions.AllowAny]


class NewsletterSubscribeView(generics.CreateAPIView):
    serializer_class = NewsletterSubscriptionSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subscription = serializer.save()

        return Response({
            'message': 'Successfully subscribed to newsletter!',
            'email': subscription.email
        }, status=status.HTTP_201_CREATED)


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        unread_count = queryset.filter(is_read=False).count()

        serializer = self.get_serializer(queryset, many=True)

        return Response({
            'notifications': serializer.data,
            'unread_count': unread_count
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, notification_id):
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        notification.is_read = True
        notification.save()

        return Response({
            'message': 'Notification marked as read'
        })
    except Notification.DoesNotExist:
        return Response({
            'error': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_read(request):
    count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    return Response({
        'message': f'Marked {count} notifications as read'
    })


class DemoInvitationCreateView(generics.CreateAPIView):
    serializer_class = DemoInvitationCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invitation = serializer.save()

        response_serializer = DemoInvitationSerializer(invitation)

        return Response({
            'message': 'Demo invitation created successfully',
            'invitation': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class DemoInvitationListView(generics.ListAPIView):
    serializer_class = DemoInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DemoInvitation.objects.filter(created_by=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'invitations': serializer.data
        })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def demo_access(request, token):
    try:
        invitation = DemoInvitation.objects.get(token=token)

        # Only block expired invitations, allow access to used ones for display purposes
        if invitation.is_expired:
            return Response({
                'error': 'Demo invitation has expired',
                'reason': 'expired'
            }, status=status.HTTP_403_FORBIDDEN)

        # Log access
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        DemoUsageLog.objects.create(
            invitation=invitation,
            action='demo_access',
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={'token': token}
        )

        data = {
            'customer_name': invitation.customer_name,
            'company_name': invitation.company_name,
            'company_logo_url': invitation.company_logo_url,
            'service_type': invitation.service_type,
            'remaining_usage': max(0, invitation.max_usage - invitation.usage_count),
            'expires_at': invitation.expires_at
        }

        serializer = DemoAccessSerializer(data)

        return Response({
            'valid': True,
            'invitation': serializer.data
        })

    except DemoInvitation.DoesNotExist:
        return Response({
            'error': 'Demo invitation not found'
        }, status=status.HTTP_404_NOT_FOUND)
