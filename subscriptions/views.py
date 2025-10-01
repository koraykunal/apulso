from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import SubscriptionPlan, Subscription, SubscriptionStatus, SubscriptionHistory
from .serializers import (
    SubscriptionPlanSerializer, SubscriptionSerializer,
    CreateSubscriptionSerializer, CancelSubscriptionSerializer
)


class SubscriptionPlanListView(generics.ListAPIView):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


class UserSubscriptionView(generics.RetrieveAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return self.request.user.subscription
        except Subscription.DoesNotExist:
            return None

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response({
                'detail': 'No active subscription found',
                'has_subscription': False
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance)
        return Response({
            'subscription': serializer.data,
            'has_subscription': True
        })


class CreateSubscriptionView(generics.CreateAPIView):
    serializer_class = CreateSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        plan_id = serializer.validated_data['plan_id']
        billing_cycle = serializer.validated_data['billing_cycle']

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({
                'error': 'Invalid plan'
            }, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(user, 'subscription') and user.subscription.is_active:
            return Response({
                'error': 'User already has an active subscription'
            }, status=status.HTTP_400_BAD_REQUEST)

        start_date = timezone.now()
        if billing_cycle == 'yearly':
            end_date = start_date + timedelta(days=365)
        else:
            end_date = start_date + timedelta(days=30)

        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            billing_cycle=billing_cycle,
            status=SubscriptionStatus.PENDING,
            start_date=start_date,
            end_date=end_date
        )

        SubscriptionHistory.objects.create(
            user=user,
            subscription=subscription,
            action='created',
            new_status=SubscriptionStatus.PENDING,
            description=f'Subscription created for plan {plan.name}'
        )

        return Response({
            'subscription': SubscriptionSerializer(subscription).data,
            'message': 'Subscription created successfully. Complete payment to activate.'
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_subscription_view(request):
    try:
        subscription = request.user.subscription
    except Subscription.DoesNotExist:
        return Response({
            'error': 'No active subscription found'
        }, status=status.HTTP_404_NOT_FOUND)

    if not subscription.is_active:
        return Response({
            'error': 'Subscription is not active'
        }, status=status.HTTP_400_BAD_REQUEST)

    serializer = CancelSubscriptionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    reason = serializer.validated_data.get('reason', 'User requested cancellation')

    previous_status = subscription.status
    subscription.status = SubscriptionStatus.CANCELLED
    subscription.auto_renew = False
    subscription.save()

    SubscriptionHistory.objects.create(
        user=request.user,
        subscription=subscription,
        action='cancelled',
        previous_status=previous_status,
        new_status=SubscriptionStatus.CANCELLED,
        description=f'Subscription cancelled. Reason: {reason}'
    )

    return Response({
        'message': 'Subscription cancelled successfully',
        'subscription': SubscriptionSerializer(subscription).data
    })


class CancelSubscriptionView(generics.GenericAPIView):
    serializer_class = CancelSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return cancel_subscription_view(request)
