from django.contrib import admin
from .models import Task, TaskComment


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "assignee_display",
        "created_by",
        "status",
        "priority",
        "due_date",
        "created_at",
    )
    list_filter = ("status", "priority", "created_at", "due_date")

    search_fields = ("title", "description", "created_by__username")

    readonly_fields = ("created_at", "updated_at", "completed_at")
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Task Information",
            {
                "fields": ("title", "description", "created_by"),
            },
        ),
        (
            "Task Details",
            {
                "fields": ("status", "priority", "due_date"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at", "completed_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def assignee_display(self, obj):

        user = (
            getattr(obj, "assignee", None)
            or getattr(obj, "assigned_to", None)
            or getattr(obj, "owner", None)
            or getattr(obj, "user", None)
        )
        if not user:
            return "—"

        full = getattr(user, "get_full_name", None)
        name = (
            (full() if callable(full) else None)
            or getattr(user, "full_name", None)
            or user.username
        )
        return name

    assignee_display.short_description = "Assignee"

    def save_model(self, request, obj, form, change):

        if not change and not getattr(obj, "created_by", None):
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):

    list_display = ("task", "user", "created_at", "comment_preview")
    list_filter = ("created_at", "task__status")
    search_fields = ("comment", "task__title", "user__username")
    readonly_fields = ("created_at",)

    def comment_preview(self, obj):

        text = obj.comment or ""
        return text[:50] + "..." if len(text) > 50 else text

    comment_preview.short_description = "Comment Preview"
