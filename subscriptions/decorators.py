from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from .models import UserServiceSubscription, ServiceType, UsageLog


def require_service_access(service_type: str, increment_usage=True):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated:
                return Response({
                    'error': 'Authentication required'
                }, status=status.HTTP_401_UNAUTHORIZED)

            if user.role == 'corporate':
                return view_func(request, *args, **kwargs)

            try:
                subscription = UserServiceSubscription.objects.select_related('service', 'plan').get(
                    user=user,
                    service__service_type=service_type
                )
            except UserServiceSubscription.DoesNotExist:
                return Response({
                    'error': f'You do not have an active subscription for this service',
                    'requires_subscription': True,
                    'service_type': service_type
                }, status=status.HTTP_403_FORBIDDEN)

            if not subscription.can_use_service():
                if not subscription.is_active:
                    return Response({
                        'error': 'Your subscription has expired',
                        'requires_subscription': True,
                        'service_type': service_type
                    }, status=status.HTTP_403_FORBIDDEN)
                else:
                    return Response({
                        'error': 'You have reached your usage limit for this service',
                        'usage_limit_reached': True,
                        'service_type': service_type,
                        'current_usage': subscription.current_usage,
                        'usage_limit': subscription.plan.usage_limit
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            if increment_usage:
                subscription.increment_usage()
                UsageLog.objects.create(
                    subscription=subscription,
                    amount=1,
                    description=f'{service_type} usage',
                    metadata={
                        'endpoint': request.path,
                        'method': request.method
                    }
                )

            request.subscription = subscription
            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator
