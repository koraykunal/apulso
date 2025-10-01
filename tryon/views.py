from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
import logging

from .models import TryOnRequest, TryOnRequestStatus
from .serializers import (
    TryOnRequestCreateSerializer,
    TryOnRequestURLSerializer,
    TryOnRequestSerializer,
    TryOnUsageStatsSerializer
)
from .services import FalAITryOnService
from core.models import DemoInvitation, DemoUsageLog

logger = logging.getLogger(__name__)


class TryOnRequestCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        content_type = self.request.content_type
        if content_type and 'multipart/form-data' in content_type:
            return TryOnRequestCreateSerializer
        return TryOnRequestURLSerializer

    def get_parser_classes(self):
        content_type = self.request.content_type
        if content_type and 'multipart/form-data' in content_type:
            return [MultiPartParser, FormParser]
        return super().get_parser_classes()

    def create(self, request, *args, **kwargs):
        # Debug logging
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Request data: {request.data}")
        logger.info(f"Serializer class: {self.get_serializer_class()}")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            service = FalAITryOnService()

            # Check if it's file upload or URL-based request
            content_type = self.request.content_type
            is_file_upload = content_type and 'multipart/form-data' in content_type

            if is_file_upload:
                # File upload
                tryon_request = service.create_try_on_request(
                    user=request.user,
                    human_image=serializer.validated_data['human_image'],
                    garment_image=serializer.validated_data['garment_image']
                )
                success = service.process_try_on_request(tryon_request)
            else:
                # URL-based request
                tryon_request = service.create_try_on_request_from_urls(
                    user=request.user,
                    human_image_url=serializer.validated_data['human_image_url'],
                    garment_image_url=serializer.validated_data['garment_image_url']
                )
                success = service.process_try_on_request_from_urls(
                    tryon_request,
                    serializer.validated_data['human_image_url'],
                    serializer.validated_data['garment_image_url']
                )

            response_serializer = TryOnRequestSerializer(
                tryon_request,
                context={'request': request}
            )

            if success:
                return Response({
                    'message': 'Try-on request processed successfully',
                    'data': response_serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'message': 'Try-on request failed to process',
                    'data': response_serializer.data
                }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in try-on request: {str(e)}")
            return Response({
                'error': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TryOnRequestListView(generics.ListAPIView):
    serializer_class = TryOnRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TryOnRequest.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class TryOnRequestDetailView(generics.RetrieveAPIView):
    serializer_class = TryOnRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TryOnRequest.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_tryon_stats(request):
    try:
        service = FalAITryOnService()
        stats = service.get_user_stats(request.user)
        serializer = TryOnUsageStatsSerializer(stats)

        return Response({
            'stats': serializer.data
        })
    except Exception as e:
        logger.error(f"Error fetching user stats: {str(e)}")
        return Response({
            'error': 'Failed to fetch user statistics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_request_status(request, request_id):
    try:
        tryon_request = TryOnRequest.objects.get(
            id=request_id,
            user=request.user
        )

        serializer = TryOnRequestSerializer(
            tryon_request,
            context={'request': request}
        )

        return Response({
            'data': serializer.data
        })
    except TryOnRequest.DoesNotExist:
        return Response({
            'error': 'Try-on request not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def demo_tryon(request, token):
    try:
        invitation = DemoInvitation.objects.get(token=token, service_type='tryon')

        # Check if demo is expired
        if invitation.is_expired:
            return Response({
                'error': 'Demo invitation has expired',
                'reason': 'expired'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if usage is exceeded
        if invitation.is_usage_exceeded:
            return Response({
                'error': 'Demo usage limit exceeded',
                'reason': 'usage_exceeded'
            }, status=status.HTTP_403_FORBIDDEN)

        # Log access
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Determine if it's file upload or URL
        content_type = request.content_type
        is_file_upload = content_type and 'multipart/form-data' in content_type

        if is_file_upload:
            serializer = TryOnRequestCreateSerializer(data=request.data)
        else:
            serializer = TryOnRequestURLSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        try:
            service = FalAITryOnService()

            if is_file_upload:
                tryon_request = service.create_try_on_request(
                    user=None,
                    demo_invitation=invitation,
                    human_image=serializer.validated_data['human_image'],
                    garment_image=serializer.validated_data['garment_image']
                )
                success = service.process_try_on_request(tryon_request)
            else:
                tryon_request = service.create_try_on_request_from_urls(
                    user=None,
                    demo_invitation=invitation,
                    human_image_url=serializer.validated_data['human_image_url'],
                    garment_image_url=serializer.validated_data['garment_image_url']
                )
                success = service.process_try_on_request_from_urls(
                    tryon_request,
                    serializer.validated_data['human_image_url'],
                    serializer.validated_data['garment_image_url']
                )

            # Log usage
            DemoUsageLog.objects.create(
                invitation=invitation,
                action='tryon_request',
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={'request_id': str(tryon_request.id), 'success': success}
            )

            # Increment usage count only for successful requests
            if success:
                invitation.increment_usage()
                # Refresh invitation from database to get updated usage_count
                invitation.refresh_from_db()

            response_serializer = TryOnRequestSerializer(
                tryon_request,
                context={'request': request}
            )

            response_data = response_serializer.data
            response_data['demo_info'] = {
                'watermark': True,
                'remaining_usage': invitation.max_usage - invitation.usage_count,
                'expires_at': invitation.expires_at,
                'customer_name': invitation.customer_name,
                'company_name': invitation.company_name
            }

            if success:
                return Response({
                    'message': 'Demo try-on request processed successfully',
                    'data': response_data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'message': 'Demo try-on request failed to process',
                    'data': response_data
                }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        except Exception as e:
            logger.error(f"Error in demo try-on request: {str(e)}")
            return Response({
                'error': 'Demo request failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except DemoInvitation.DoesNotExist:
        return Response({
            'error': 'Demo invitation not found'
        }, status=status.HTTP_404_NOT_FOUND)
