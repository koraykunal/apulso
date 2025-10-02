from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import Service, ServicePlan, UserServiceSubscription, SubscriptionStatus, UsageLog
from .serializers import (
    ServiceSerializer, ServicePlanSerializer,
    UserServiceSubscriptionSerializer, CreateSubscriptionSerializer, UsageLogSerializer
)


class ServiceListView(generics.ListAPIView):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [permissions.AllowAny]


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def service_plans_view(request, service_id):
    try:
        service = Service.objects.get(id=service_id, is_active=True)
    except Service.DoesNotExist:
        return Response({
            'error': 'Service not found'
        }, status=status.HTTP_404_NOT_FOUND)

    plans = ServicePlan.objects.filter(service=service, is_active=True)
    serializer = ServicePlanSerializer(plans, many=True)

    return Response({
        'service': ServiceSerializer(service).data,
        'plans': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_subscriptions_view(request):
    subscriptions = UserServiceSubscription.objects.filter(
        user=request.user
    ).select_related('service', 'plan')

    serializer = UserServiceSubscriptionSerializer(subscriptions, many=True)
    return Response({
        'subscriptions': serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_subscription_view(request):
    serializer = CreateSubscriptionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user
    service_id = serializer.validated_data['service_id']
    plan_id = serializer.validated_data['plan_id']
    billing_cycle = serializer.validated_data['billing_cycle']

    try:
        service = Service.objects.get(id=service_id, is_active=True)
        plan = ServicePlan.objects.get(id=plan_id, service=service, is_active=True)
    except (Service.DoesNotExist, ServicePlan.DoesNotExist):
        return Response({
            'error': 'Invalid service or plan'
        }, status=status.HTTP_400_BAD_REQUEST)

    if UserServiceSubscription.objects.filter(user=user, service=service).exists():
        return Response({
            'error': 'You already have a subscription for this service'
        }, status=status.HTTP_400_BAD_REQUEST)

    start_date = timezone.now()
    if billing_cycle == 'yearly':
        end_date = start_date + timedelta(days=365)
    else:
        end_date = start_date + timedelta(days=30)

    subscription = UserServiceSubscription.objects.create(
        user=user,
        service=service,
        plan=plan,
        billing_cycle=billing_cycle,
        status=SubscriptionStatus.PENDING,
        start_date=start_date,
        end_date=end_date
    )

    return Response({
        'subscription': UserServiceSubscriptionSerializer(subscription).data,
        'message': 'Subscription created successfully. Complete payment to activate.'
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_subscription_view(request, subscription_id):
    try:
        subscription = UserServiceSubscription.objects.get(
            id=subscription_id,
            user=request.user
        )
    except UserServiceSubscription.DoesNotExist:
        return Response({
            'error': 'Subscription not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if subscription.status == SubscriptionStatus.CANCELLED:
        return Response({
            'error': 'Subscription is already cancelled'
        }, status=status.HTTP_400_BAD_REQUEST)

    subscription.status = SubscriptionStatus.CANCELLED
    subscription.auto_renew = False
    subscription.save()

    return Response({
        'message': 'Subscription cancelled successfully',
        'subscription': UserServiceSubscriptionSerializer(subscription).data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_service_access_view(request, service_type):
    if request.user.role == 'corporate':
        return Response({
            'has_access': True,
            'is_corporate': True
        })

    try:
        subscription = UserServiceSubscription.objects.select_related('service', 'plan').get(
            user=request.user,
            service__service_type=service_type
        )
    except UserServiceSubscription.DoesNotExist:
        return Response({
            'has_access': False,
            'requires_subscription': True,
            'service_type': service_type
        })

    return Response({
        'has_access': subscription.can_use_service(),
        'subscription': UserServiceSubscriptionSerializer(subscription).data
    })
