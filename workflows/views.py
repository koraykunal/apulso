from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, F, Avg
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
import uuid

from .models import (
    WorkflowCategory, Workflow, PurchasedWorkflow, WorkflowExecution,
    WorkflowRating, WorkflowStatus
)
from .serializers import (
    WorkflowSerializer, WorkflowDetailSerializer, WorkflowCreateSerializer,
    PurchasedWorkflowSerializer, PurchaseWorkflowSerializer,
    WorkflowExecutionSerializer, ExecuteWorkflowSerializer,
    WorkflowRatingSerializer, CreateRatingSerializer
)
from accounts.permissions import IsVerifiedUser


class WorkflowListView(generics.ListAPIView):
    serializer_class = WorkflowSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'price', 'is_featured']
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'price', 'rating_average', 'purchase_count']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Workflow.objects.filter(status=WorkflowStatus.ACTIVE)

        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset


class WorkflowDetailView(generics.RetrieveAPIView):
    serializer_class = WorkflowDetailSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Workflow.objects.filter(status=WorkflowStatus.ACTIVE)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        Workflow.objects.filter(id=instance.id).update(view_count=F('view_count') + 1)
        instance.refresh_from_db()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class WorkflowCreateView(generics.CreateAPIView):
    serializer_class = WorkflowCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            raise permissions.PermissionDenied(
                "Only admin users can create workflows"
            )
        workflow = serializer.save()


class UserWorkflowsView(generics.ListAPIView):
    serializer_class = WorkflowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        workflow_type = self.request.query_params.get('type', 'purchased')

        if workflow_type == 'purchased':
            purchased_workflow_ids = PurchasedWorkflow.objects.filter(
                user=user, is_active=True
            ).values_list('workflow_id', flat=True)
            return Workflow.objects.filter(id__in=purchased_workflow_ids)

        if workflow_type == 'all' and user.is_superuser:
            return Workflow.objects.all()

        return Workflow.objects.none()


class PurchaseWorkflowView(generics.CreateAPIView):
    serializer_class = PurchaseWorkflowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        workflow_id = serializer.validated_data['workflow_id']
        payment_provider = serializer.validated_data['payment_provider']

        try:
            workflow = Workflow.objects.get(id=workflow_id, status=WorkflowStatus.ACTIVE)
        except Workflow.DoesNotExist:
            return Response({
                'error': 'Workflow not found or not available'
            }, status=status.HTTP_404_NOT_FOUND)

        if PurchasedWorkflow.objects.filter(user=user, workflow=workflow).exists():
            return Response({
                'error': 'You have already purchased this workflow'
            }, status=status.HTTP_400_BAD_REQUEST)


        payment_data = {
            'amount': workflow.price,
            'currency': 'TRY',
            'provider': payment_provider,
            'payment_type': 'workflow_purchase',
            'workflow_id': workflow.id,
            'description': f'Purchase of workflow: {workflow.title}'
        }

        return Response({
            'payment_data': payment_data,
            'workflow': WorkflowSerializer(workflow).data,
            'message': 'Proceed to payment to complete purchase'
        })


class WorkflowExecutionView(generics.CreateAPIView):
    serializer_class = ExecuteWorkflowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        workflow_id = serializer.validated_data['workflow_id']
        execution_data = serializer.validated_data['execution_data']

        try:
            workflow = Workflow.objects.get(id=workflow_id)
        except Workflow.DoesNotExist:
            return Response({
                'error': 'Workflow not found'
            }, status=status.HTTP_404_NOT_FOUND)

        if hasattr(user, 'subscription') and not user.subscription.can_execute_workflow():
            return Response({
                'error': 'You have reached your monthly execution limit'
            }, status=status.HTTP_403_FORBIDDEN)

        execution_id = str(uuid.uuid4())

        execution = WorkflowExecution.objects.create(
            user=user,
            workflow=workflow,
            execution_id=execution_id,
            status='pending',
            started_at=timezone.now(),
            execution_data=execution_data
        )

        if hasattr(user, 'subscription'):
            user.subscription.current_execution_count += 1
            user.subscription.save()

        return Response({
            'execution': WorkflowExecutionSerializer(execution).data,
            'message': 'Workflow execution started'
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def rate_workflow_view(request, pk):
    try:
        workflow = Workflow.objects.get(id=pk)
    except Workflow.DoesNotExist:
        return Response({
            'error': 'Workflow not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if not PurchasedWorkflow.objects.filter(
        user=request.user, workflow=workflow, is_active=True
    ).exists():
        return Response({
            'error': 'You must purchase this workflow to rate it'
        }, status=status.HTTP_403_FORBIDDEN)

    serializer = CreateRatingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    rating, created = WorkflowRating.objects.update_or_create(
        user=request.user,
        workflow=workflow,
        defaults=serializer.validated_data
    )

    workflow.rating_count = workflow.ratings.count()
    workflow.rating_average = workflow.ratings.aggregate(
        avg_rating=Avg('rating')
    )['avg_rating'] or 0
    workflow.save()

    action = 'created' if created else 'updated'
    return Response({
        'rating': WorkflowRatingSerializer(rating).data,
        'message': f'Rating {action} successfully'
    })
