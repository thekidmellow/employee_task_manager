"""
Task management views with role-based access control
Demonstrates business logic and data manipulation (LO2)
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Task, TaskComment
from .forms import TaskCreationForm, TaskUpdateForm, TaskCommentForm
from accounts.models import UserProfile


@login_required
def task_list_view(request):
    """
    Display tasks based on user role
    Demonstrates role-based content access (LO3.3)
    """
    user_profile = request.user.userprofile
    
    # Filter tasks based on user role
    if user_profile.is_manager:
        # Managers can see all tasks
        tasks = Task.objects.select_related('assigned_to', 'created_by').all()
    else:
        # Employees can only see their assigned tasks
        tasks = Task.objects.select_related('assigned_to', 'created_by').filter(
            assigned_to=request.user
        )
    
    # Apply filters from GET parameters
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    search_query = request.GET.get('search')
    
    if status_filter and status_filter != 'all':
        tasks = tasks.filter(status=status_filter)
    
    if priority_filter and priority_filter != 'all':
        tasks = tasks.filter(priority=priority_filter)
    
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics for managers
    stats = {}
    if user_profile.is_manager:
        stats = {
            'total_tasks': Task.objects.count(),
            'pending_tasks': Task.objects.filter(status='pending').count(),
            'in_progress_tasks': Task.objects.filter(status='in_progress').count(),
            'completed_tasks': Task.objects.filter(status='completed').count(),
            'overdue_tasks': Task.objects.filter(
                due_date__lt=timezone.now(),
                status__in=['pending', 'in_progress']
            ).count(),
        }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'current_filters': {
            'status': status_filter,
            'priority': priority_filter,
            'search': search_query,
        }
    }
    
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_create_view(request):
    """
    Create new task (Manager only)
    Demonstrates authorization and form validation (LO3.1, LO2.4)
    """
    # Check if user is manager
    if not request.user.userprofile.is_manager:
        messages.error(request, 'Only managers can create tasks.')
        return redirect('tasks:task_list')
    
    if request.method == 'POST':
        form = TaskCreationForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            
            messages.success(request, f'Task "{task.title}" created successfully!')
            
            # Notify assigned user (placeholder for future notification system)
            # This demonstrates business logic implementation
            assigned_user = task.assigned_to
            print(f"[NOTIFICATION] Task '{task.title}' assigned to {assigned_user.username}")
            
            return redirect('tasks:task_detail', task_id=task.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = TaskCreationForm()
    
    context = {'form': form}
    return render(request, 'tasks/task_create.html', context)


