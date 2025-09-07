# apps/tasks/views.py
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import TaskCreationForm, TaskUpdateForm, TaskCommentForm, TaskFilterForm
from .models import Task, TaskComment


@login_required
def task_list_view(request):
    """Display paginated list of tasks with filtering"""
    user = request.user
    is_manager = getattr(user, 'userprofile', None) and user.userprofile.is_manager

    # Managers see all; others see tasks assigned to them OR created by them
    base_qs = Task.objects.all() if is_manager else Task.objects.filter(
        Q(assigned_to=user) | Q(created_by=user)
    )

    # Apply filters
    filter_form = TaskFilterForm(request.GET, user=user)
    tasks = base_qs
    if filter_form.is_valid():
        search = filter_form.cleaned_data.get('search')
        if search:
            tasks = tasks.filter(Q(title__icontains=search) | Q(description__icontains=search))

        status = filter_form.cleaned_data.get('status')
        if status:
            tasks = tasks.filter(status=status)

        priority = filter_form.cleaned_data.get('priority')
        if priority:
            tasks = tasks.filter(priority=priority)

        assigned_to = filter_form.cleaned_data.get('assigned_to')
        if assigned_to:
            tasks = tasks.filter(assigned_to=assigned_to)

    tasks = tasks.select_related('assigned_to', 'created_by').order_by('-priority', 'due_date', '-created_at')

    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Stats should match what the user can see
    stats_queryset = base_qs
    stats = {
        'total': stats_queryset.count(),
        'pending': stats_queryset.filter(status='pending').count(),
        'in_progress': stats_queryset.filter(status='in_progress').count(),
        'completed': stats_queryset.filter(status='completed').count(),
        'overdue': stats_queryset.filter(
            due_date__lt=timezone.now(),
            status__in=['pending', 'in_progress']
        ).count(),
    }

    return render(request, 'tasks/task_list.html', {
        'page_obj': page_obj,
        'tasks': page_obj.object_list,
        'filter_form': filter_form,
        'is_manager': is_manager,
        'stats': stats,
        'pending_count': stats['pending'],
        'in_progress_count': stats['in_progress'],
        'completed_count': stats['completed'],
        'overdue_count': stats['overdue'],
        'total_count': paginator.count,
        'is_paginated': page_obj.has_other_pages(),
    })


@login_required
def task_create_view(request):
    """Create new task (managers only)"""
    user = request.user
    is_manager = getattr(user, 'userprofile', None) and user.userprofile.is_manager

    # Return 403 Forbidden for non-managers (tests expect 403, not a redirect)
    if not is_manager:
        raise PermissionDenied

    if request.method == 'POST':
        form = TaskCreationForm(request.POST, user=user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = user
            task.save()
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('tasks:task_detail', task_id=task.id)
        else:
            messages.error(request, "Please correct the errors below.")
            # Optional debug: print("Create form errors:", form.errors.as_json())
    else:
        form = TaskCreationForm(user=user)

    return render(request, 'tasks/task_form.html', {
        'form': form,
        'title': 'Create New Task',
        'button_text': 'Create Task',
    })


@login_required
def task_detail_view(request, task_id):
    """Display task details with comments"""
    task = get_object_or_404(Task, id=task_id)
    user = request.user
    is_manager = getattr(user, 'userprofile', None) and user.userprofile.is_manager

    # Permission check: non-managers can only view tasks assigned to them
    if not is_manager and task.assigned_to != user:
        messages.error(request, 'You can only view tasks assigned to you.')
        return redirect('tasks:task_list')

    # Comment form
    if request.method == 'POST':
        comment_form = TaskCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.task = task
            comment.user = user
            comment.save()
            messages.success(request, 'Comment added successfully!')
            return redirect('tasks:task_detail', task_id=task.id)
    else:
        comment_form = TaskCommentForm()

    comments = task.comments.select_related('user').order_by('-created_at')
    can_edit = is_manager or task.assigned_to == user
    can_delete = is_manager

    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'comments': comments,
        'comment_form': comment_form,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'is_manager': is_manager,
    })


@login_required
def task_update_view(request, task_id):
    """Update task (permissions based on user role)"""
    task = get_object_or_404(Task, id=task_id)
    user = request.user
    is_manager = getattr(user, 'userprofile', None) and user.userprofile.is_manager

    # Employees can only update their own tasks
    if not is_manager and task.assigned_to != user:
        messages.error(request, 'You can only edit tasks assigned to you.')
        return redirect('tasks:task_list')

    if request.method == 'POST':
        form = (
            TaskCreationForm(request.POST, instance=task, user=user)
            if is_manager else
            TaskUpdateForm(request.POST, instance=task, user=user)
        )
        if form.is_valid():
            updated_task = form.save()
            action = 'updated' if is_manager else 'status updated'
            messages.success(request, f'Task "{updated_task.title}" {action} successfully!')
            return redirect('tasks:task_detail', task_id=updated_task.id)
    else:
        form = (
            TaskCreationForm(instance=task, user=user)
            if is_manager else
            TaskUpdateForm(instance=task, user=user)
        )

    return render(request, 'tasks/task_form.html', {
        'form': form,
        'task': task,
        'title': f'Edit Task: {task.title}',
        'button_text': 'Update Task',
        'is_manager': is_manager,
    })


@login_required
def task_delete_view(request, task_id):
    """Delete task (managers only)"""
    task = get_object_or_404(Task, id=task_id)
    user = request.user
    is_manager = getattr(user, 'userprofile', None) and user.userprofile.is_manager

    if not is_manager:
        messages.error(request, 'Only managers can delete tasks.')
        return redirect('tasks:task_detail', task_id=task.id)

    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'Task "{task_title}" deleted successfully!')
        return redirect('tasks:task_list')

    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
@require_POST
def update_task_status(request, task_id):
    """AJAX endpoint for quick status updates"""
    task = get_object_or_404(Task, id=task_id)
    user = request.user
    is_manager = getattr(user, 'userprofile', None) and user.userprofile.is_manager

    # Parse JSON body
    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'success': False, 'message': 'Invalid request body'}, status=400)

    new_status = data.get('status')

    # Permission check
    if not is_manager and task.assigned_to != user:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

    # Validate status
    valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
    if new_status not in valid_statuses:
        return JsonResponse({'success': False, 'message': 'Invalid status'}, status=400)

    # Update status
    task.status = new_status
    if new_status == "completed":
        task.completed_at = timezone.now()
    task.save()

    return JsonResponse({'success': True, 'new_status': task.get_status_display()})


@login_required
def task_stats_api(request):
    """
    API endpoint for task statistics (used by dashboard widgets)
    """
    user = request.user
    is_manager = getattr(user, 'userprofile', None) and user.userprofile.is_manager

    qs = Task.objects.all() if is_manager else Task.objects.filter(assigned_to=user)

    total = qs.count()
    pending = qs.filter(status='pending').count()
    in_progress = qs.filter(status='in_progress').count()
    completed = qs.filter(status='completed').count()
    cancelled = qs.filter(status='cancelled').count()
    overdue = qs.filter(
        due_date__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    ).count()

    completion_rate = round((completed / total) * 100, 1) if total else 0.0

    priority_breakdown = {}
    for code, name in Task.PRIORITY_CHOICES:
        priority_breakdown[code] = {
            'name': name,
            'count': qs.filter(priority=code).count(),
        }

    data = {
        'total_tasks': total,
        'pending_tasks': pending,
        'in_progress_tasks': in_progress,
        'completed_tasks': completed,
        'cancelled_tasks': cancelled,
        'overdue_tasks': overdue,
        'completion_rate': completion_rate,
        'priority_breakdown': priority_breakdown,
        'is_manager': is_manager,
        'timestamp': timezone.now().isoformat(),
    }

    return JsonResponse(data)
