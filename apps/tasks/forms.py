from datetime import timedelta

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Task, TaskComment

User = get_user_model()

FLOATING_LABEL_FIELDS = {"title", "description", "notes"}


class TaskCreationForm(forms.ModelForm):
    assignee = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Assign To",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "assigned_to",
            "priority",
            "due_date",
            "status",
            "estimated_hours",
            "notes",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": " ",
                    "maxlength": 200,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": " ",
                    "style": "height: 160px;",
                }
            ),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "due_date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
            "estimated_hours": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.25",
                    "min": "0",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": " ",
                    "style": "height: 120px;",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        kwargs.setdefault("auto_id", "id_%s")
        super().__init__(*args, **kwargs)

        self.fields["title"].label = "Task Title"
        self.fields["title"].help_text = (
            "Brief, descriptive title for the task (5–200 characters)"
        )

        self.fields["description"].label = "Description"
        self.fields["description"].help_text = (
            "Detailed description of what needs to be done (minimum 10 characters)"
        )

        self.fields["priority"].label = "Priority Level"
        self.fields["priority"].help_text = "Set the importance level of this task"

        self.fields["due_date"].label = "Due Date & Time"
        self.fields["due_date"].help_text = "When should this task be completed?"

        self.fields["due_date"].input_formats = [
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d-%m-%Y",
        ]

        if "assigned_to" in self.fields:
            self.fields["assigned_to"].required = False

        if not self.instance.pk:
            self.fields["status"].required = False
            self.fields["status"].initial = "pending"
            self.fields["status"].widget = forms.HiddenInput()

        if self.instance and getattr(self.instance, "assigned_to", None):
            self.fields["assignee"].initial = self.instance.assigned_to

        for name, field in self.fields.items():
            wid = field.widget
            wid.attrs.setdefault("id", f"id_{name}")
            if name in FLOATING_LABEL_FIELDS:
                wid.attrs.setdefault("placeholder", " ")

    def save(self, commit=True):
        obj = super().save(commit=False)

        if not self.instance.pk and not self.cleaned_data.get("status"):
            obj.status = "pending"

        chosen = self.cleaned_data.get(
            "assignee") or self.cleaned_data.get("assigned_to")
        if chosen is not None:
            obj.assigned_to = chosen

        if commit:
            obj.save()
        return obj

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()
        if len(title) < 5:
            raise ValidationError(
                "Task title must be at least 5 characters long.")
        if len(title) > 200:
            raise ValidationError("Task title cannot exceed 200 characters.")
        forbidden_words = ["spam", "test123", "dummy"]
        if any(word in title.lower() for word in forbidden_words):
            raise ValidationError("Please use a professional task title.")
        return title

    def clean_description(self):
        description = self.cleaned_data.get("description", "").strip()
        if len(description) < 10:
            raise ValidationError(
                "Task description must be at least 10 characters long.")
        if len(description) > 2000:
            raise ValidationError(
                "Task description cannot exceed 2000 characters.")
        return description

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        if not due_date:
            return None

        if timezone.is_naive(due_date):
            due_date = timezone.make_aware(
                due_date, timezone.get_current_timezone())

        at_midnight = (0, 0, 0, 0)
        if (
            due_date.hour,
            due_date.minute,
            due_date.second,
            due_date.microsecond,
        ) == at_midnight:
            due_date = due_date.replace(
                hour=23, minute=59, second=0, microsecond=0)

        now = timezone.now()
        if due_date <= now:
            raise ValidationError("Due date must be in the future.")
        if due_date > now + timedelta(days=365):
            raise ValidationError(
                "Due date cannot be more than 1 year in the future.")

        return due_date

    def clean(self):
        cleaned_data = super().clean()

        priority = cleaned_data.get("priority")
        due_date = cleaned_data.get("due_date")
        status = cleaned_data.get("status")

        if not self.instance.pk and status == "completed":
            raise ValidationError(
                "New tasks cannot be created with completed status.")

        if priority == "urgent" and due_date:
            if due_date > timezone.now() + timedelta(days=3):
                raise ValidationError(
                    "Urgent priority tasks should have a due date within 3 days."
                )

        return cleaned_data


class TaskUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["status"]
        widgets = {"status": forms.Select(attrs={"class": "form-select"})}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        kwargs.setdefault("auto_id", "id_%s")
        super().__init__(*args, **kwargs)

        self.fields["status"].label = "Task Status"
        self.fields["status"].help_text = "Update the current status of this task"
        self.fields["status"].widget.attrs.setdefault("id", "id_status")
        self.fields["status"].widget.attrs.setdefault(
            "aria-describedby", "id_status_helptext")

    def clean_status(self):
        new_status = self.cleaned_data.get("status")
        current_status = self.instance.status if self.instance else "pending"

        valid_transitions = {
            "pending": ["in_progress", "cancelled"],
            "in_progress": ["completed", "pending", "cancelled"],
            "completed": [],
            "cancelled": ["pending"],
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise ValidationError(
                f"Cannot change status from {current_status} to {new_status}."
            )

        if (
            self.user
            and not self.user.groups.filter(name="Managers").exists()
            and current_status == "in_progress"
            and new_status == "pending"
        ):
            raise ValidationError(
                "You cannot set a task back to pending once work has started."
            )

        return new_status


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ["comment"]
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Add your comment...",
                    "maxlength": 1000,
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["comment"].label = "Your Comment"
        self.fields["comment"].help_text = "Share updates, ask questions, or provide feedback"

    def clean_comment(self):
        comment = self.cleaned_data.get("comment", "").strip()
        if len(comment) < 5:
            raise ValidationError(
                "Comment must be at least 5 characters long.")
        if len(comment) > 1000:
            raise ValidationError("Comment cannot exceed 1000 characters.")
        return comment


class TaskFilterForm(forms.Form):
    STATUS_CHOICES = [("", "All Statuses")] + Task.STATUS_CHOICES
    PRIORITY_CHOICES = [("", "All Priorities")] + Task.PRIORITY_CHOICES

    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search tasks by title or description...",
            }
        ),
    )

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label="All Assignees",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user:
            if user.groups.filter(name="Managers").exists():
                employees = User.objects.filter(groups__name="Employees")
                if employees.exists():
                    self.fields["assigned_to"].queryset = employees
                else:
                    self.fields["assigned_to"].queryset = User.objects.filter(
                        is_superuser=False
                    ).exclude(groups__name="Managers")
            else:
                self.fields["assigned_to"].queryset = User.objects.filter(
                    id=user.id)
                self.fields["assigned_to"].initial = user
                self.fields["assigned_to"].widget.attrs["disabled"] = True


TaskForm = TaskCreationForm
