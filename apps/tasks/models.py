from datetime import datetime, timedelta
from django.db import models
from django.core.validators import MinLengthValidator
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class Task(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(5, "Title must be at least 5 characters long")],
    )
    description = models.TextField(
        validators=[MinLengthValidator(10, "Description must be at least 10 characters long")],
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assigned_tasks",
        help_text="Employee assigned to this task",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_tasks",
        help_text="Manager who created this task",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    due_date = models.DateTimeField()

    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated time (in hours) required to complete the task",
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Additional notes, special instructions, or context",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __init__(self, *args, **kwargs):
        assignee = kwargs.pop("assignee", None)
        super().__init__(*args, **kwargs)
        if assignee is not None:
            self.assigned_to = assignee

    @property
    def assignee(self):
        return self.assigned_to

    @assignee.setter
    def assignee(self, value):
        self.assigned_to = value

    def __setattr__(self, name, value):
        if name == "due_date" and isinstance(value, datetime):
            from django.utils import timezone as _tz
            if _tz.is_naive(value):
                value = _tz.make_aware(value, _tz.get_current_timezone())
        super().__setattr__(name, value)

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not getattr(self, "due_date", None):
            self.due_date = timezone.now() + timedelta(days=7)

        if isinstance(self.due_date, str):
            try:
                parsed = datetime.fromisoformat(self.due_date.strip())
            except ValueError:
                parsed = datetime.fromisoformat(self.due_date.strip() + ":00")
            self.due_date = parsed

        if timezone.is_naive(self.due_date):
            self.due_date = timezone.make_aware(
                self.due_date,
                timezone.get_current_timezone(),
            )

        if self.status == "completed" and not self.completed_at:
            self.completed_at = timezone.now()
        if self.status != "completed" and self.completed_at:
            self.completed_at = None

        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.status == "completed":
            return False
        return timezone.now() > self.due_date

    @property
    def days_until_due(self):
        if self.status == "completed":
            return 0
        delta = self.due_date - timezone.now()
        return delta.days if delta.days > 0 else 0

    def get_priority_color(self):
        priority_colors = {
            "low": "text-success",
            "medium": "text-warning",
            "high": "text-danger",
            "urgent": "text-dark",
        }
        return priority_colors.get(self.priority, "text-secondary")

    def get_priority_badge_color(self):
        priority_badges = {
            "low": "success",
            "medium": "warning",
            "high": "danger",
            "urgent": "dark",
        }
        return priority_badges.get(self.priority, "secondary")

    def get_status_color(self):
        status_colors = {
            "pending": "secondary",
            "in_progress": "primary",
            "completed": "success",
            "cancelled": "danger",
        }
        return status_colors.get(self.status, "secondary")


class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField(
        validators=[MinLengthValidator(5, "Comment must be at least 5 characters long")]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title}"
