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
from apps.accounts.models import UserProfile


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


@login_required
def task_detail_view(request, task_id):
    """
    Display task details with comments
    Demonstrates data display and related model access (LO2.2)
    """
    task = get_object_or_404(Task, id=task_id)
    user_profile = request.user.userprofile
    
    # Check permissions
    if not (user_profile.is_manager or task.assigned_to == request.user):
        messages.error(request, 'You do not have permission to view this task.')
        return redirect('tasks:task_list')
    
    # Get comments
    comments = task.comments.select_related('user').all()
    
    # Handle comment form
    comment_form = TaskCommentForm()
    if request.method == 'POST' and 'add_comment' in request.POST:
        comment_form = TaskCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.task = task
            comment.user = request.user
            comment.save()
            
            messages.success(request, 'Comment added successfully!')
            return redirect('tasks:task_detail', task_id=task.id)
    
    context = {
        'task': task,
        'comments': comments,
        'comment_form': comment_form,
        'can_edit': user_profile.is_manager or task.assigned_to == request.user,
        'can_delete': user_profile.is_manager,
    }
    
    return render(request, 'tasks/task_detail.html', context)


@login_required
def task_update_view(request, task_id):
    """
    Update task details
    Demonstrates CRUD operations with authorization (LO2.2, LO3)
    """
    task = get_object_or_404(Task, id=task_id)
    user_profile = request.user.userprofile
    
    # Check permissions
    if not (user_profile.is_manager or task.assigned_to == request.user):
        messages.error(request, 'You do not have permission to edit this task.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    if request.method == 'POST':
        # Different forms based on user role
        if user_profile.is_manager:
            form = TaskCreationForm(request.POST, instance=task)
        else:
            # Employees can only update status
            form = TaskUpdateForm(request.POST, instance=task)
        
        if form.is_valid():
            updated_task = form.save()
            
            messages.success(request, f'Task "{updated_task.title}" updated successfully!')
            
            # Log status change for notifications (LO2.3)
            if 'status' in form.changed_data:
                print(f"[NOTIFICATION] Task '{updated_task.title}' status changed to {updated_task.get_status_display()}")
            
            return redirect('tasks:task_detail', task_id=updated_task.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        if user_profile.is_manager:
            form = TaskCreationForm(instance=task)
        else:
            form = TaskUpdateForm(instance=task)
    
    context = {
        'form': form,
        'task': task,
        'is_manager': user_profile.is_manager,
    }
    
    return render(request, 'tasks/task_update.html', context)


@login_required
def task_delete_view(request, task_id):
    """
    Delete task (Manager only)
    Demonstrates authorization and data deletion (LO3.1, LO2.2)
    """
    task = get_object_or_404(Task, id=task_id)
    
    # Only managers can delete tasks
    if not request.user.userprofile.is_manager:
        messages.error(request, 'Only managers can delete tasks.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'Task "{task_title}" deleted successfully!')
        return redirect('tasks:task_list')
    
    context = {'task': task}
    return render(request, 'tasks/task_delete.html', context)


@login_required
def update_task_status_ajax(request):
    """
    AJAX endpoint for quick status updates
    Demonstrates JavaScript integration and real-time updates (LO4.2)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    task_id = request.POST.get('task_id')
    new_status = request.POST.get('status')
    
    try:
        task = get_object_or_404(Task, id=task_id)
        user_profile = request.user.userprofile
        
        # Check permissions
        if not (user_profile.is_manager or task.assigned_to == request.user):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Validate status
        valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({'error': 'Invalid status'}, status=400)
        
        # Update task
        old_status = task.status
        task.status = new_status
        task.save()
        
        # Log change for notifications
        print(f"[NOTIFICATION] Task '{task.title}' status changed from {old_status} to {new_status}")
        
        return JsonResponse({
            'success': True,
            'message': f'Task status updated to {task.get_status_display()}',
            'new_status': new_status,
            'status_display': task.get_status_display(),
            'status_color': task.get_status_color(),
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@login_required
def task_stats_api(request):
    """
    API endpoint for dashboard statistics
    Demonstrates data aggregation and JSON API (LO2.2)
    """
    user_profile = request.user.userprofile
    
    if user_profile.is_manager:
        # Manager sees all tasks
        tasks = Task.objects.all()
    else:
        # Employee sees only their tasks
        tasks = Task.objects.filter(assigned_to=request.user)
    
    # Calculate statistics
    stats = {
        'total': tasks.count(),
        'pending': tasks.filter(status='pending').count(),
        'in_progress': tasks.filter(status='in_progress').count(),
        'completed': tasks.filter(status='completed').count(),
        'overdue': tasks.filter(
            due_date__lt=timezone.now(),
            status__in=['pending', 'in_progress']
        ).count(),
    }
    
    # Priority breakdown
    priority_stats = {}
    for priority, _ in Task.PRIORITY_CHOICES:
        priority_stats[priority] = tasks.filter(priority=priority).count()
    
    return JsonResponse({
        'status_stats': stats,
        'priority_stats': priority_stats,
        'user_role': user_profile.role,
    })






