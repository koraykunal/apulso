from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import ContactMessage, FAQ, NewsletterSubscription, Notification, DemoInvitation, ServiceType


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'order']


class NewsletterSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscription
        fields = ['email']

    def create(self, validated_data):
        email = validated_data['email']
        subscription, created = NewsletterSubscription.objects.get_or_create(
            email=email,
            defaults={'is_active': True}
        )

        if not created and not subscription.is_active:
            subscription.is_active = True
            subscription.save()

        return subscription


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type',
            'is_read', 'action_url', 'created_at'
        ]
        read_only_fields = ['created_at']


class DemoInvitationCreateSerializer(serializers.ModelSerializer):
    expires_hours = serializers.IntegerField(default=24, min_value=1, max_value=168, write_only=True)

    class Meta:
        model = DemoInvitation
        fields = [
            'customer_name', 'customer_email', 'company_name', 'company_logo_url',
            'service_type', 'max_usage', 'notes', 'expires_hours'
        ]

    def create(self, validated_data):
        expires_hours = validated_data.pop('expires_hours', 24)
        validated_data['expires_at'] = timezone.now() + timedelta(hours=expires_hours)
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DemoInvitationSerializer(serializers.ModelSerializer):
    demo_url = serializers.ReadOnlyField()
    is_valid = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    remaining_usage = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DemoInvitation
        fields = [
            'id', 'token', 'customer_name', 'customer_email', 'company_name', 'company_logo_url',
            'service_type', 'created_by_name', 'expires_at', 'created_at',
            'is_used', 'used_at', 'max_usage', 'usage_count', 'notes',
            'demo_url', 'is_valid', 'is_expired', 'remaining_usage'
        ]
        read_only_fields = ['id', 'token', 'created_at', 'is_used', 'used_at', 'usage_count']

    def get_remaining_usage(self, obj):
        return max(0, obj.max_usage - obj.usage_count)

    def get_created_by_name(self, obj):
        return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.email


class DemoAccessSerializer(serializers.Serializer):
    customer_name = serializers.CharField(read_only=True)
    company_name = serializers.CharField(read_only=True)
    company_logo_url = serializers.URLField(read_only=True)
    service_type = serializers.CharField(read_only=True)
    remaining_usage = serializers.IntegerField(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True)