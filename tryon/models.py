from django.db import models
from django.conf import settings
from core.models import DemoInvitation
import uuid


class TryOnRequestStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class TryOnRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tryon_requests', null=True, blank=True)
    demo_invitation = models.ForeignKey(DemoInvitation, on_delete=models.CASCADE, related_name='tryon_requests', null=True, blank=True)

    human_image = models.ImageField(upload_to='tryon/human_images/', blank=True, null=True)
    garment_image = models.ImageField(upload_to='tryon/garment_images/', blank=True, null=True)
    human_image_url = models.URLField(max_length=1000, blank=True, null=True)
    garment_image_url = models.URLField(max_length=1000, blank=True, null=True)
    result_image_url = models.URLField(max_length=1000, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=TryOnRequestStatus.choices,
        default=TryOnRequestStatus.PENDING
    )

    fal_request_id = models.CharField(max_length=255, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    processing_time = models.FloatField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=4, default=0.07)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        if self.user:
            identifier = self.user.email
        elif self.demo_invitation:
            identifier = f"Demo-{self.demo_invitation.customer_name}"
        else:
            identifier = "Unknown"
        return f"TryOn Request {self.id} - {identifier} - {self.status}"

    @property
    def is_demo(self):
        return self.demo_invitation is not None


class TryOnUsageStats(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tryon_stats')
    total_requests = models.PositiveIntegerField(default=0)
    successful_requests = models.PositiveIntegerField(default=0)
    failed_requests = models.PositiveIntegerField(default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=4, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TryOn Stats - {self.user.email}"

    @property
    def success_rate(self):
        if self.total_requests == 0:
            return 0
        return (self.successful_requests / self.total_requests) * 100
