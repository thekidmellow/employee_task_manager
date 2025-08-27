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
        fields = ['title', 'description', 'assigned_to', 'priority', 'due_date', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a descriptive task title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide detailed task description'
            }),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        # Limit assigned_to field to employees only
        self.fields['assigned_to'].queryset = User.objects.filter(
            userprofile__role='employee'
        ).select_related('userprofile')
    
        # Customize field labels and help text
        self.fields['title'].help_text = 'Brief, descriptive title for the task'
        self.fields['description'].help_text = 'Detailed description of what needs to be done'
        self.fields['assigned_to'].help_text = 'Select an employee to assign this task to'
        self.fields['due_date'].help_text = 'When should this task be completed?'
    
        # Set default due date to 7 days from now
        if not self.instance.pk:
            default_due = timezone.now() + timedelta(days=7)
            self.fields['due_date'].initial = default_due.strftime('%Y-%m-%dT%H:%M')

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



