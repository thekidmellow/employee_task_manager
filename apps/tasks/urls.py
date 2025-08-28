"""
URL patterns for task management
"""

from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Task CRUD operations
    path('', views.task_list_view, name='task_list'),
    path('create/', views.task_create_view, name='task_create'),
    path('<int:task_id>/', views.task_detail_view, name='task_detail'),
    path('<int:task_id>/edit/', views.task_update_view, name='task_update'),
    path('<int:task_id>/delete/', views.task_delete_view, name='task_delete'),

    # AJAX endpoints
    path('api/update-status/', views.update_task_status_ajax, name='update_status_ajax'),
    path('api/stats/', views.task_stats_api, name='task_stats_api'),
]

