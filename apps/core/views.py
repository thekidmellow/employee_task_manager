"""
Core application views including dashboards and home page
Demonstrates role-based content display (LO3.2) 
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task
from accounts.models import UserProfile


def home_view(request):
    """
    Home page view with role-based redirect
    Demonstrates authentication state reflection (LO3.2)
    """
    if request.user.is_authenticated:
        user_profile = request.user.userprofile
        if user_profile.is_manager:
            return redirect('core:manager_dashboard')
        else:
            return redirect('core:employee_dashboard')
    
    context = {
        'total_users': UserProfile.objects.count(),
        'total_tasks': Task.objects.count(),
        'completed_tasks': Task.objects.filter(status='completed').count(),
    }
    return render(request, 'core/home.html', context)


@login_required
def manager_dashboard(request):
    """
    Manager dashboard with comprehensive task overview
    Demonstrates role-based access control (LO3.1)
    """
    user_profile = request.user.userprofile
    if not user_profile.is_manager:
        messages.error(request, 'Access denied. Manager privileges required.')
        return redirect('core:employee_dashboard')
    
    total_tasks = Task.objects.count()
    pending_tasks = Task.objects.filter(status='pending')
    in_progress_tasks = Task.objects.filter(status='in_progress')
    completed_tasks = Task.objects.filter(status='completed')
    
    overdue_tasks = Task.objects.filter(
        due_date__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    )
    
    recent_tasks = Task.objects.select_related('assigned_to', 'created_by').order_by('-created_at')[:10]
    
    employee_workload = UserProfile.objects.filter(role='employee').select_related('user').annotate(
        total_tasks=Count('user__assigned_tasks'),
        pending_tasks=Count('user__assigned_tasks', filter=Q(user__assigned_tasks__status='pending')),
        in_progress_tasks=Count('user__assigned_tasks', filter=Q(user__assigned_tasks__status='in_progress'))
    )
    
    priority_stats = {priority: Task.objects.filter(priority=priority).count() for priority, _ in Task.PRIORITY_CHOICES}
    
    weekly_stats = []
    for i in range(4):
        week_start = timezone.now() - timedelta(weeks=i+1)
        week_end = timezone.now() - timedelta(weeks=i)
        week_tasks = Task.objects.filter(created_at__gte=week_start, created_at__lt=week_end).count()
        weekly_stats.append({'week': f"Week {4-i}", 'tasks': week_tasks})
    
    context = {
        'user_profile': user_profile,
        'stats': {
            'total_tasks': total_tasks,
            'pending_count': pending_tasks.count(),
            'in_progress_count': in_progress_tasks.count(),
            'completed_count': completed_tasks.count(),
            'overdue_count': overdue_tasks.count(),
        },
        'recent_tasks': recent_tasks,
        'overdue_tasks': overdue_tasks[:5],
        'employee_workload': employee_workload,
        'priority_stats': priority_stats,
        'weekly_stats': weekly_stats,
    }
    
    return render(request, 'core/manager_dashboard.html', context)


@login_required
def employee_dashboard(request):
    """
    Employee dashboard showing assigned tasks
    Demonstrates personalized content display (LO3.2)
    """
    user_profile = request.user.userprofile
    user_tasks = Task.objects.filter(assigned_to=request.user)
    
    pending_tasks = user_tasks.filter(status='pending')
    in_progress_tasks = user_tasks.filter(status='in_progress')
    completed_tasks = user_tasks.filter(status='completed')
    
    overdue_tasks = user_tasks.filter(due_date__lt=timezone.now(), status__in=['pending', 'in_progress'])
    
    upcoming_deadline = timezone.now() + timedelta(days=7)
    upcoming_tasks = user_tasks.filter(due_date__lte=upcoming_deadline, status__in=['pending', 'in_progress']).order_by('due_date')
    
    recent_tasks = user_tasks.order_by('-updated_at')[:10]
    
    total_assigned = user_tasks.count()
    total_completed = completed_tasks.count()
    completion_rate = (total_completed / total_assigned * 100) if total_assigned > 0 else 0
    
    monthly_stats = []
    for i in range(6):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        month_completed = user_tasks.filter(completed_at__gte=month_start, completed_at__lt=month_end, status='completed').count()
        monthly_stats.append({'month': month_start.strftime('%b %Y'), 'completed': month_completed})
    
    context = {
        'user_profile': user_profile,
        'stats': {
            'total_tasks': total_assigned,
            'pending_count': pending_tasks.count(),
            'in_progress_count': in_progress_tasks.count(),
            'completed_count': total_completed,
            'overdue_count': overdue_tasks.count(),
            'completion_rate': round(completion_rate, 1),
        },
        'upcoming_tasks': upcoming_tasks[:5],
        'overdue_tasks': overdue_tasks[:5],
        'recent_tasks': recent_tasks,
        'monthly_stats': list(reversed(monthly_stats)),
    }
    
    return render(request, 'core/employee_dashboard.html', context)


def custom_404(request, exception):
    """
    Custom 404 error page
    Demonstrates error handling (LO6.2)
    """
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    """
    Custom 500 error page
    Demonstrates error handling (LO6.2)
    """
    return render(request, 'errors/500.html', status=500)

