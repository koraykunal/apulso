from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class WorkflowCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class WorkflowStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    ARCHIVED = 'archived', 'Archived'


class Workflow(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(WorkflowCategory, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    n8n_workflow_data = models.JSONField(help_text="N8N workflow JSON data")
    preview_images = models.JSONField(default=list, help_text="List of preview image URLs")
    tags = models.JSONField(default=list, help_text="List of tags")
    status = models.CharField(max_length=20, choices=WorkflowStatus.choices, default=WorkflowStatus.DRAFT)
    is_featured = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    purchase_count = models.IntegerField(default=0)
    rating_average = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_published(self):
        return self.status == WorkflowStatus.ACTIVE


class PurchasedWorkflow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchased_workflows')
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'workflow']

    def __str__(self):
        return f"{self.user.email} - {self.workflow.title}"


class WorkflowExecution(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    execution_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=50)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    execution_data = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.workflow.title} - {self.execution_id}"


class WorkflowRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'workflow']

    def __str__(self):
        return f"{self.workflow.title} - {self.rating}/5"
