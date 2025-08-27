"""
Task management models for the Employee Task Manager
Demonstrates data modeling and business logic (LO2)
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
from django.utils import timezone


class Task(models.Model):
    """
    Main Task model representing work assignments
    Demonstrates custom model creation (LO1.4)
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(5, "Title must be at least 5 characters long")]
    )
    description = models.TextField(
        validators=[MinLengthValidator(10, "Description must be at least 10 characters long")]
    )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assigned_tasks',
        help_text="Employee assigned to this task"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_tasks',
        help_text="Manager who created this task"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='medium'
    )
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """
        Custom save method to handle business logic
        Demonstrates compound statements and custom logic (LO1.8, LO1.9)
        """
        # If task is being marked as completed, set completed_at timestamp
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        # If task status is changed from completed, clear completed_at
        if self.status != 'completed' and self.completed_at:
            self.completed_at = None
            
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if self.status == 'completed':
            return False
        return timezone.now() > self.due_date
    
    @property
    def days_until_due(self):
        """Calculate days until due date"""
        if self.status == 'completed':
            return 0
        delta = self.due_date - timezone.now()
        return delta.days if delta.days > 0 else 0




