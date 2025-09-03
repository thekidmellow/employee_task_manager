"""
Task management forms with validation
Demonstrates form handling and business logic (LO2.4)
"""

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Task, TaskComment


class TaskCreationForm(forms.ModelForm):
    """
    Form for creating and editing tasks (Manager access)
    Demonstrates complex form validation and business rules
    """
    class Meta:
        model = Task
        # ⬇️ Remove 'status' so it defaults to 'pending'
        # ⬇️ Add 'estimated_hours' so you can set it on create
        fields = ['title', 'description', 'assigned_to', 'priority', 'estimated_hours', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter a descriptive task title'}),
            'description': forms.Textarea(attrs={'class': 'form-control','rows': 4,'placeholder': 'Provide detailed task description'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0',
                'placeholder': 'e.g. 1, 1.5, 2'
            }),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control','type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Limit assigned_to field to employees only
        self.fields['assigned_to'].queryset = User.objects.filter(
            userprofile__role='employee'
        ).select_related('userprofile')

        # Customize labels/help
        self.fields['title'].help_text = 'Brief, descriptive title for the task'
        self.fields['description'].help_text = 'Detailed description of what needs to be done'
        self.fields['assigned_to'].help_text = 'Select an employee to assign this task to'
        self.fields['estimated_hours'].help_text = 'Estimated effort in hours (e.g., 1, 1.5, 2)'
        self.fields['due_date'].help_text = 'When should this task be completed?'

        # Set default due date to 7 days from now
        if not self.instance.pk:
            default_due = timezone.now() + timedelta(days=7)
            # Match the datetime-local format
            self.fields['due_date'].initial = default_due.strftime('%Y-%m-%dT%H:%M')

        # Accept the browser's datetime-local format
        self.fields['due_date'].input_formats = ['%Y-%m-%dT%H:%M']


    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')

        if due_date:
            if due_date <= timezone.now():
                raise ValidationError("Due date must be in the future.")

            max_future_date = timezone.now() + timedelta(days=365)
            if due_date > max_future_date:
                raise ValidationError("Due date cannot be more than 1 year in the future.")

            min_time = timezone.now() + timedelta(hours=2)
            if due_date < min_time:
                raise ValidationError("Please allow at least 2 hours for task completion.")

        return due_date

    def clean_title(self):
        title = self.cleaned_data.get('title')

        if title:
            title = title.strip()

            if len(title) < 5:
                raise ValidationError("Task title must be at least 5 characters long.")

            if len(title) > 200:
                raise ValidationError("Task title must be less than 200 characters.")

            inappropriate_words = ['spam', 'test123', 'dummy']
            if any(word in title.lower() for word in inappropriate_words):
                raise ValidationError("Please use a professional task title.")

        return title

    def clean(self):
        cleaned_data = super().clean()
        # status is not on the form; model default handles it
        due_date = cleaned_data.get('due_date')
        priority = cleaned_data.get('priority')

        # Keep your urgent rule
        if priority == 'urgent' and due_date:
            max_urgent_date = timezone.now() + timedelta(days=3)
            if due_date > max_urgent_date:
                raise ValidationError("Urgent tasks should be due within 3 days.")

        return cleaned_data

    

class TaskUpdateForm(forms.ModelForm):
    """
    Limited form for employees to update task status
    Demonstrates role-based form restrictions (LO3)
    """
    
    class Meta:
        model = Task
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        if self.instance and self.instance.status != 'pending':
            status_choices = [
                choice for choice in Task.STATUS_CHOICES 
                if choice[0] != 'pending'
            ]
            self.fields['status'].choices = status_choices
    
        self.fields['status'].help_text = 'Update the current status of this task'

    def clean_status(self):
        new_status = self.cleaned_data.get('status')
        current_status = self.instance.status if self.instance else None
    
        valid_transitions = {
            'pending': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'pending'],
            'completed': ['in_progress'],  
            'cancelled': ['pending', 'in_progress'],
        }
    
        if current_status and new_status:
            if new_status not in valid_transitions.get(current_status, []):
                raise ValidationError(
                    f"Cannot change status from {current_status} to {new_status}."
                )
    
        return new_status
    

class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add a comment about this task...'
            }),
        }
    
    def clean_comment(self):
        comment = self.cleaned_data.get('comment')
        
        if comment:
            comment = comment.strip()
            
            if len(comment) < 5:
                raise ValidationError("Comments must be at least 5 characters long.")
            
            if len(comment) > 1000:
                raise ValidationError("Comments must be less than 1000 characters.")
        
        return comment


class TaskFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search tasks...'
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('all', 'All Statuses')] + Task.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    priority = forms.ChoiceField(
        required=False,
        choices=[('all', 'All Priorities')] + Task.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    assigned_to = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.filter(userprofile__role='employee'),
        empty_label="All Employees",
        widget=forms.Select(attrs={'class': 'form-control'})
    )







