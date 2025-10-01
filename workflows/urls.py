from django.urls import path
from .views import (
    WorkflowListView, WorkflowDetailView, WorkflowCreateView,
    PurchaseWorkflowView, UserWorkflowsView, WorkflowExecutionView,
    rate_workflow_view
)

app_name = 'workflows'

urlpatterns = [
    path('', WorkflowListView.as_view(), name='list'),
    path('<int:pk>/', WorkflowDetailView.as_view(), name='detail'),
    path('create/', WorkflowCreateView.as_view(), name='create'),
    path('purchase/', PurchaseWorkflowView.as_view(), name='purchase'),
    path('my-workflows/', UserWorkflowsView.as_view(), name='my_workflows'),
    path('execute/', WorkflowExecutionView.as_view(), name='execute'),
    path('<int:pk>/rate/', rate_workflow_view, name='rate'),
]