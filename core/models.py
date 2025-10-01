from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import uuid
import secrets

User = get_user_model()


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default="Apulso")
    site_description = models.TextField(blank=True)
    maintenance_mode = models.BooleanField(default=False)
    allow_registration = models.BooleanField(default=True)
    max_file_upload_size = models.IntegerField(default=5242880)  # 5MB
    stripe_publishable_key = models.CharField(max_length=200, blank=True)
    n8n_webhook_url = models.URLField(blank=True)
    email_from_address = models.EmailField(default="noreply@apulso.com")

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.site_name

    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"


class NewsletterSubscription(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.question


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, default='info')
    is_read = models.BooleanField(default=False)
    action_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.title}"


class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.action}"


class ServiceType(models.TextChoices):
    TRYON = 'tryon', 'AI Try-On'
    EMAIL_AUTOMATION = 'email_automation', 'Email Automation'
    CRM_INTEGRATION = 'crm_integration', 'CRM Integration'
    SOCIAL_MEDIA = 'social_media', 'Social Media Management'
    DOCUMENT_AUTOMATION = 'document_automation', 'Document Automation'
    APPOINTMENT_MANAGEMENT = 'appointment_management', 'Appointment Management'


class DemoInvitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=32, unique=True)

    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    company_name = models.CharField(max_length=200, blank=True)
    company_logo_url = models.URLField(blank=True)

    service_type = models.CharField(max_length=50, choices=ServiceType.choices)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='demo_invitations')

    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)

    max_usage = models.PositiveIntegerField(default=3)
    usage_count = models.PositiveIntegerField(default=0)

    notes = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['service_type', 'expires_at']),
            models.Index(fields=['created_by', '-created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(16)[:32]
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_usage_exceeded(self):
        return self.usage_count >= self.max_usage

    @property
    def is_valid(self):
        return not self.is_expired and not self.is_usage_exceeded

    @property
    def demo_url(self):
        return f"/demo/{self.token}"

    def mark_as_used(self):
        if not self.is_used:
            self.is_used = True
            self.used_at = timezone.now()
            self.save(update_fields=['is_used', 'used_at'])

    def increment_usage(self):
        self.usage_count += 1
        self.save(update_fields=['usage_count'])

        # Mark as used only when usage is completely exhausted
        if self.usage_count >= self.max_usage:
            self.mark_as_used()

    def __str__(self):
        return f"Demo {self.service_type} - {self.customer_name} ({self.token})"


class DemoUsageLog(models.Model):
    invitation = models.ForeignKey(DemoInvitation, on_delete=models.CASCADE, related_name='usage_logs')
    action = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.invitation.service_type} - {self.action} - {self.timestamp}"
