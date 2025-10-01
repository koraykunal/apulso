from rest_framework import serializers
from .models import (
    WorkflowCategory, Workflow, PurchasedWorkflow,
    WorkflowExecution, WorkflowRating, WorkflowStatus
)
from accounts.serializers import UserSerializer


class WorkflowCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowCategory
        fields = '__all__'


class WorkflowSerializer(serializers.ModelSerializer):
    category = WorkflowCategorySerializer(read_only=True)
    is_published = serializers.ReadOnlyField()

    class Meta:
        model = Workflow
        fields = [
            'id', 'title', 'description', 'category', 'price',
            'preview_images', 'tags', 'status', 'is_featured', 'view_count',
            'purchase_count', 'rating_average', 'rating_count', 'is_published',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'view_count', 'purchase_count', 'rating_average', 'rating_count',
            'created_at', 'updated_at'
        ]


class WorkflowCreateSerializer(serializers.ModelSerializer):
    # Alternatif string input alanları
    preview_images_text = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Comma-separated image URLs: image1.jpg,image2.jpg,image3.jpg"
    )
    tags_text = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Comma-separated tags: automation,email,marketing"
    )
    n8n_workflow_json = serializers.CharField(
        write_only=True,
        required=False,
        help_text="N8N workflow as JSON string"
    )

    class Meta:
        model = Workflow
        fields = [
            'title', 'description', 'category', 'price', 'n8n_workflow_data',
            'preview_images', 'tags', 'status',
            'preview_images_text', 'tags_text', 'n8n_workflow_json'
        ]

    def validate_n8n_workflow_data(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("N8N workflow data must be a valid JSON object")
        return value

    def validate_n8n_workflow_json(self, value):
        if value:
            try:
                import json
                json.loads(value)
                return value
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON format")
        return value

    def create(self, validated_data):
        # String formatlarını JSON'a çevir
        preview_images_text = validated_data.pop('preview_images_text', None)
        tags_text = validated_data.pop('tags_text', None)
        n8n_workflow_json = validated_data.pop('n8n_workflow_json', None)

        if preview_images_text:
            validated_data['preview_images'] = [
                img.strip() for img in preview_images_text.split(',') if img.strip()
            ]

        if tags_text:
            validated_data['tags'] = [
                tag.strip() for tag in tags_text.split(',') if tag.strip()
            ]

        if n8n_workflow_json:
            import json
            validated_data['n8n_workflow_data'] = json.loads(n8n_workflow_json)

        return super().create(validated_data)


class WorkflowDetailSerializer(serializers.ModelSerializer):
    category = WorkflowCategorySerializer(read_only=True)
    is_published = serializers.ReadOnlyField()
    is_purchased = serializers.SerializerMethodField()

    class Meta:
        model = Workflow
        fields = [
            'id', 'title', 'description', 'category', 'price',
            'n8n_workflow_data', 'preview_images', 'tags', 'status',
            'is_featured', 'view_count', 'purchase_count', 'rating_average',
            'rating_count', 'is_published', 'is_purchased', 'created_at'
        ]

    def get_is_purchased(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PurchasedWorkflow.objects.filter(
                user=request.user,
                workflow=obj,
                is_active=True
            ).exists()
        return False


class PurchasedWorkflowSerializer(serializers.ModelSerializer):
    workflow = WorkflowSerializer(read_only=True)

    class Meta:
        model = PurchasedWorkflow
        fields = '__all__'
        read_only_fields = ['user', 'purchase_price', 'payment_id', 'purchased_at']


class PurchaseWorkflowSerializer(serializers.Serializer):
    workflow_id = serializers.IntegerField()
    payment_provider = serializers.CharField(max_length=20)

    def validate_workflow_id(self, value):
        try:
            workflow = Workflow.objects.get(id=value, status=WorkflowStatus.ACTIVE)
            return value
        except Workflow.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive workflow")


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    workflow = WorkflowSerializer(read_only=True)

    class Meta:
        model = WorkflowExecution
        fields = '__all__'
        read_only_fields = ['user', 'execution_id', 'created_at']


class ExecuteWorkflowSerializer(serializers.Serializer):
    workflow_id = serializers.IntegerField()
    execution_data = serializers.JSONField(default=dict)

    def validate_workflow_id(self, value):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required")

        try:
            workflow = Workflow.objects.get(id=value)
            if not PurchasedWorkflow.objects.filter(
                user=request.user,
                workflow=workflow,
                is_active=True
            ).exists():
                raise serializers.ValidationError("Workflow not purchased or access denied")
            return value
        except Workflow.DoesNotExist:
            raise serializers.ValidationError("Workflow not found")


class WorkflowRatingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = WorkflowRating
        fields = ['id', 'user', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']


class CreateRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowRating
        fields = ['rating', 'comment']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value