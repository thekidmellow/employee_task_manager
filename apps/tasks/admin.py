# apps/tasks/admin.py
"""
Admin configuration for tasks app
"""

from django.contrib import admin
from .models import Task, TaskComment


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin for Task model"""

    # Use a computed column instead of a missing 'assignee' field
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

    # Drop the broken 'assignee__username' until we know the real field name
    search_fields = ("title", "description", "created_by__username")

    readonly_fields = ("created_at", "updated_at", "completed_at")
    date_hierarchy = "created_at"

    # Remove 'assignee' from fieldsets (it breaks if the field doesn't exist)
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
        """
        Display an assignee-like user from whichever field exists.
        Tries common names in order; returns an em dash if none.
        """
        user = (
            getattr(obj, "assignee", None)
            or getattr(obj, "assigned_to", None)
            or getattr(obj, "owner", None)
            or getattr(obj, "user", None)
        )
        if not user:
            return "—"

        # Prefer full name when available
        full = getattr(user, "get_full_name", None)
        name = (
            (full() if callable(full) else None)
            or getattr(user, "full_name", None)
            or user.username
        )
        return name

    assignee_display.short_description = "Assignee"
    # If your actual FK field is, e.g., 'assigned_to', set:
    # assignee_display.admin_order_field = "assigned_to"
    # so column sorting works. Otherwise leave it unset.

    def save_model(self, request, obj, form, change):
        """Auto-set created_by if creating a new task."""
        if not change and not getattr(obj, "created_by", None):
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    """Admin for TaskComment model"""

    list_display = ("task", "user", "created_at", "comment_preview")
    list_filter = ("created_at", "task__status")
    search_fields = ("comment", "task__title", "user__username")
    readonly_fields = ("created_at",)

    def comment_preview(self, obj):
        """Show a short preview of the comment text."""
        text = obj.comment or ""
        return text[:50] + "..." if len(text) > 50 else text

    comment_preview.short_description = "Comment Preview"
