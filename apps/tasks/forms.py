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

