from django.urls import path
from . import views

app_name = "tasks"

urlpatterns = [
    path("", views.task_list_view, name="task_list"),
    path("create/", views.task_create_view, name="task_create"),
    path("<int:task_id>/", views.task_detail_view, name="task_detail"),
    path("<int:task_id>/edit/", views.task_update_view, name="task_update"),
    path("<int:task_id>/delete/", views.task_delete_view, name="task_delete"),

    # APIs / actions
    path("update-status/", views.update_task_status, name="update_status_ajax"),
    path("<int:task_id>/update-status/",
         views.update_task_status, name="update_task_status"),
    path("api/stats/", views.task_stats_api, name="task_stats_api"),
    path("api/users/", views.user_list_api, name="user_list_api"),
    path("api/comments/", views.task_comment_api, name="task_comment_api"),
]
