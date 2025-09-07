# apps/tasks/forms.py
"""
Forms for task management functionality
Demonstrates form validation and user input handling (LO3.1)
"""

from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import Task, TaskComment

User = get_user_model()


class TaskCreationForm(forms.ModelForm):
    # Accept 'assignee' as an alias for the model field 'assigned_to'
    assignee = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label='Assign To',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Task
        fields = [
            'title', 'description',
            'assigned_to',        # keep in the form so tests posting assigned_to work
            'priority', 'due_date',
            'status', 'estimated_hours', 'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a descriptive task title',
                'maxlength': 200
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide detailed task description...'
            }),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.25',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any extra context...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Labels & help text
        self.fields['title'].label = 'Task Title'
        self.fields['title'].help_text = 'Brief, descriptive title for the task (5-200 characters)'

        self.fields['description'].label = 'Description'
        self.fields['description'].help_text = 'Detailed description of what needs to be done (minimum 10 characters)'

        self.fields['priority'].label = 'Priority Level'
        self.fields['priority'].help_text = 'Set the importance level of this task'

        self.fields['due_date'].label = 'Due Date & Time'
        self.fields['due_date'].help_text = 'When should this task be completed?'

        # Accept browser datetime-local and common formats
        self.fields['due_date'].input_formats = [
            '%Y-%m-%dT%H:%M',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d %H:%M:%S',
        ]

        # Make assigned_to optional at the form level (tests may use only `assignee`)
        if 'assigned_to' in self.fields:
            self.fields['assigned_to'].required = False

        # On CREATE: make status optional, default to pending, and hide the field
        if not self.instance.pk:
            self.fields['status'].required = False
            self.fields['status'].initial = 'pending'
            self.fields['status'].widget = forms.HiddenInput()

        # If editing, reflect current assignee into the synthetic field
        if self.instance and getattr(self.instance, 'assigned_to', None):
            self.fields['assignee'].initial = self.instance.assigned_to

        # Do not restrict querysets by role here; tests may not provide request.user
        # (Views enforce permissions.)

    def save(self, commit=True):
        obj = super().save(commit=False)

        # Ensure status default on create
        if not self.instance.pk and not self.cleaned_data.get('status'):
            obj.status = 'pending'

        # Prefer `assignee`, else `assigned_to`
        chosen = self.cleaned_data.get('assignee') or self.cleaned_data.get('assigned_to')
        if chosen is not None:
            obj.assigned_to = chosen

        if commit:
            obj.save()
        return obj

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 5:
            raise ValidationError('Task title must be at least 5 characters long.')
        if len(title) > 200:
            raise ValidationError('Task title cannot exceed 200 characters.')
        forbidden_words = ['spam', 'test123', 'dummy']
        if any(word in title.lower() for word in forbidden_words):
            raise ValidationError('Please use a professional task title.')
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if len(description) < 10:
            raise ValidationError('Task description must be at least 10 characters long.')
        if len(description) > 2000:
            raise ValidationError('Task description cannot exceed 2000 characters.')
        return description

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')

        # Allow blank; the model's save() provides a safe default if missing
        if not due_date:
            return None

        # Make timezone-aware to avoid warnings
        if timezone.is_naive(due_date):
            due_date = timezone.make_aware(due_date, timezone.get_current_timezone())

        now = timezone.now()
        if due_date <= now:
            raise ValidationError('Due date must be in the future.')
        if due_date > now + timedelta(days=365):
            raise ValidationError('Due date cannot be more than 1 year in the future.')

        return due_date

    def clean(self):
        cleaned_data = super().clean()

        # If only `assignee` is provided, copy it into `assigned_to`
        if not cleaned_data.get('assigned_to') and cleaned_data.get('assignee'):
            cleaned_data['assigned_to'] = cleaned_data['assignee']

        # Business rules
        priority = cleaned_data.get('priority')
        due_date = cleaned_data.get('due_date')
        status = cleaned_data.get('status')

        # New tasks cannot start as completed
        if not self.instance.pk and status == 'completed':
            raise ValidationError('New tasks cannot be created with completed status.')

        # Urgent tasks should be within 3 days (only if a due_date was supplied)
        if priority == 'urgent' and due_date:
            if due_date > timezone.now() + timedelta(days=3):
                raise ValidationError('Urgent priority tasks should have a due date within 3 days.')

        return cleaned_data


class TaskUpdateForm(forms.ModelForm):
    """Form for employees to update task status"""

    class Meta:
        model = Task
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['status'].label = 'Task Status'
        self.fields['status'].help_text = 'Update the current status of this task'

    def clean_status(self):
        new_status = self.cleaned_data.get('status')
        current_status = self.instance.status if self.instance else 'pending'

        valid_transitions = {
            'pending': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'pending', 'cancelled'],
            'completed': [],
            'cancelled': ['pending'],
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise ValidationError(f'Cannot change status from {current_status} to {new_status}.')

        # Employees cannot set back to pending after work started
        if (self.user and not self.user.groups.filter(name='Managers').exists()
                and current_status == 'in_progress' and new_status == 'pending'):
            raise ValidationError('You cannot set a task back to pending once you have started working on it.')

        return new_status


class TaskCommentForm(forms.ModelForm):
    """Form for adding comments to tasks"""

    class Meta:
        model = TaskComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add your comment...',
                'maxlength': 1000
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comment'].label = 'Your Comment'
        self.fields['comment'].help_text = 'Share updates, ask questions, or provide feedback'

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        if len(comment) < 5:
            raise ValidationError('Comment must be at least 5 characters long.')
        if len(comment) > 1000:
            raise ValidationError('Comment cannot exceed 1000 characters.')
        return comment


class TaskFilterForm(forms.Form):
    """Form for filtering tasks in list view"""

    STATUS_CHOICES = [('', 'All Statuses')] + Task.STATUS_CHOICES
    PRIORITY_CHOICES = [('', 'All Priorities')] + Task.PRIORITY_CHOICES

    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search tasks by title or description...'
        })
    )

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label='All Assignees',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            if user.groups.filter(name='Managers').exists():
                employees = User.objects.filter(groups__name='Employees')
                if employees.exists():
                    self.fields['assigned_to'].queryset = employees
                else:
                    self.fields['assigned_to'].queryset = User.objects.filter(
                        is_superuser=False
                    ).exclude(groups__name='Managers')
            else:
                self.fields['assigned_to'].queryset = User.objects.filter(id=user.id)
                self.fields['assigned_to'].initial = user
                self.fields['assigned_to'].widget.attrs['disabled'] = True


# Keep this alias so tests can import TaskForm
TaskForm = TaskCreationForm
