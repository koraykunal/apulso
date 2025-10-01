from django.contrib import admin
from .models import WorkflowCategory, Workflow, PurchasedWorkflow, WorkflowExecution, WorkflowRating
from .forms import WorkflowAdminForm


@admin.register(WorkflowCategory)
class WorkflowCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    form = WorkflowAdminForm
    list_display = ['title', 'category', 'price', 'status', 'view_count', 'purchase_count', 'is_featured']
    list_filter = ['status', 'category', 'is_featured', 'created_at']
    search_fields = ['title', 'description', 'tags']
    readonly_fields = ['view_count', 'purchase_count', 'rating_average', 'rating_count']

    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('title', 'description', 'category', 'price', 'status')
        }),
        ('Medya ve Etiketler', {
            'fields': ('preview_images_text', 'tags_text')
        }),
        ('N8N Workflow Verisi', {
            'fields': ('n8n_workflow_json',),
            'classes': ('collapse',)
        }),
        ('Özellikler', {
            'fields': ('is_featured',)
        }),
        ('İstatistikler', {
            'fields': ('view_count', 'purchase_count', 'rating_average', 'rating_count'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PurchasedWorkflow)
class PurchasedWorkflowAdmin(admin.ModelAdmin):
    list_display = ['user', 'workflow', 'purchase_price', 'purchased_at']
    list_filter = ['purchased_at', 'is_active']
    search_fields = ['user__email', 'workflow__title']
    raw_id_fields = ['user', 'workflow']


@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'user', 'execution_id', 'status', 'started_at']
    list_filter = ['status', 'started_at']
    search_fields = ['user__email', 'workflow__title', 'execution_id']
    raw_id_fields = ['user', 'workflow']


@admin.register(WorkflowRating)
class WorkflowRatingAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__email', 'workflow__title']
    raw_id_fields = ['user', 'workflow']
