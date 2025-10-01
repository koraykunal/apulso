from rest_framework import serializers
from .models import TryOnRequest, TryOnUsageStats, TryOnRequestStatus


class TryOnRequestURLSerializer(serializers.Serializer):
    human_image_url = serializers.URLField(required=True, allow_blank=False)
    garment_image_url = serializers.URLField(required=True, allow_blank=False)

    def validate_human_image_url(self, value):
        # Demo için basit validation - sadece boş olmasın
        if not value or value.strip() == '':
            raise serializers.ValidationError("Human image URL is required")
        return value

    def validate_garment_image_url(self, value):
        # Demo için basit validation - sadece boş olmasın
        if not value or value.strip() == '':
            raise serializers.ValidationError("Garment image URL is required")
        return value


class TryOnRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TryOnRequest
        fields = ['human_image', 'garment_image']

    def validate_human_image(self, value):
        if value.size > 10 * 1024 * 1024:  # 10MB
            raise serializers.ValidationError("Human image file too large (max 10MB)")

        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Invalid image format. Allowed: JPEG, PNG, WebP")

        return value

    def validate_garment_image(self, value):
        if value.size > 10 * 1024 * 1024:  # 10MB
            raise serializers.ValidationError("Garment image file too large (max 10MB)")

        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Invalid image format. Allowed: JPEG, PNG, WebP")

        return value


class TryOnRequestSerializer(serializers.ModelSerializer):
    human_image_url = serializers.SerializerMethodField()
    garment_image_url = serializers.SerializerMethodField()

    class Meta:
        model = TryOnRequest
        fields = [
            'id', 'status', 'human_image_url', 'garment_image_url',
            'result_image_url', 'processing_time', 'cost',
            'created_at', 'updated_at', 'completed_at', 'error_message'
        ]
        read_only_fields = [
            'id', 'status', 'result_image_url', 'processing_time',
            'cost', 'created_at', 'updated_at', 'completed_at', 'error_message'
        ]

    def get_human_image_url(self, obj):
        # First check if there's a stored URL (for URL-based requests)
        if obj.human_image_url:
            return obj.human_image_url

        # Then check if there's an uploaded file
        if obj.human_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.human_image.url)
            return obj.human_image.url
        return None

    def get_garment_image_url(self, obj):
        # First check if there's a stored URL (for URL-based requests)
        if obj.garment_image_url:
            return obj.garment_image_url

        # Then check if there's an uploaded file
        if obj.garment_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.garment_image.url)
            return obj.garment_image.url
        return None


class TryOnUsageStatsSerializer(serializers.ModelSerializer):
    success_rate = serializers.ReadOnlyField()

    class Meta:
        model = TryOnUsageStats
        fields = [
            'total_requests', 'successful_requests', 'failed_requests',
            'total_cost', 'success_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']