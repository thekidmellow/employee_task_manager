# core/views.py
"""
Core application views
Handles main application pages and dashboard functionality
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta

from apps.tasks.models import Task


def home_view(request):
    """
    Home page view with platform statistics
    Demonstrates context data preparation (LO1.3)
    """
    # Calculate platform statistics for display
    total_users = User.objects.count()
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(status='completed').count()
    
    # Get recent activities for display (last 5 tasks)
    recent_tasks = Task.objects.select_related(
        'assigned_to', 'created_by'
    ).order_by('-created_at')[:5]
    
    context = {
        'total_users': total_users,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'recent_tasks': recent_tasks,
        'platform_name': 'Employee Task Manager'
    }
    
    return render(request, 'core/home.html', context)


@login_required
def dashboard_view(request):
    """
    Main dashboard - redirects to role-specific dashboard
    """
    user = request.user
    is_manager = getattr(user, 'userprofile', None) and user.userprofile.is_manager
    return redirect('core:manager_dashboard' if is_manager else 'core:employee_dashboard')



@login_required
def manager_dashboard_view(request):
    """
    Manager dashboard with team overview and statistics
    """
    user = request.user
    is_manager = getattr(user, 'userprofile', None) and user.userprofile.is_manager
    if not is_manager:
        return redirect('core:employee_dashboard')

    # Get all tasks for statistics
    all_tasks = Task.objects.select_related('assigned_to', 'created_by')

    # Raw counts
    total_tasks = all_tasks.count()
    pending_count = all_tasks.filter(status='pending').count()
    in_progress_count = all_tasks.filter(status='in_progress').count()
    completed_count = all_tasks.filter(status='completed').count()
    overdue_count = all_tasks.filter(
        due_date__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    ).count()

    # Recent activities (last 10 tasks)
    recent_activities = all_tasks.order_by('-created_at')[:10]

    # Team performance
    team_performance = []
    employees = User.objects.filter(groups__name='Employees')
    for employee in employees:
        employee_tasks = all_tasks.filter(assigned_to=employee)
        assigned_count = employee_tasks.count()
        completed_count_emp = employee_tasks.filter(status='completed').count()
        completion_rate = round((completed_count_emp / assigned_count) * 100, 1) if assigned_count else 0
        team_performance.append({
            'name': employee.get_full_name() or employee.username,
            'assigned_count': assigned_count,
            'completed_count': completed_count_emp,
            'completion_rate': completion_rate
        })
    team_performance.sort(key=lambda x: x['completion_rate'], reverse=True)

    context = {
        'total_tasks': total_tasks,
        'pending_tasks': pending_count,
        'in_progress_tasks': in_progress_count,
        'completed_tasks': completed_count,
        'overdue_tasks': overdue_count,
        'recent_activities': recent_activities,
        'team_performance': team_performance[:10],
        'dashboard_type': 'manager'
    }
    return render(request, 'core/manager_dashboard.html', context)


@login_required
def employee_dashboard_view(request):
    """
    Employee dashboard with personal task overview
    """
    user = request.user

    # Only the user's assigned tasks
    my_tasks = Task.objects.filter(assigned_to=user)

    # Personal stats
    my_tasks_count = my_tasks.count()
    pending_count = my_tasks.filter(status='pending').count()
    in_progress_count = my_tasks.filter(status='in_progress').count()
    completed_count = my_tasks.filter(status='completed').count()

    # Overdue (assuming due_date is a DateTimeField)
    overdue_count = my_tasks.filter(
        due_date__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    ).count()

    # Completion %
    completion_percentage = round((completed_count / my_tasks_count) * 100, 1) if my_tasks_count else 0

    # Today's tasks (due today or already overdue)
    today = timezone.now().date()
    todays_tasks = my_tasks.filter(
        Q(due_date__date=today) |
        Q(due_date__lt=timezone.now(), status__in=['pending', 'in_progress'])
    ).order_by('due_date', 'priority')[:5]

    # Recent activity (last 7 days)
    recent_activities = my_tasks.filter(
        updated_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-updated_at')[:5]

    # Weekly progress (last 7 days)
    weekly_progress = []
    for i in range(7):
        day = today - timedelta(days=6 - i)
        day_tasks = my_tasks.filter(due_date__date=day)
        total_day_tasks = day_tasks.count()
        completed_day_tasks = day_tasks.filter(status='completed').count()
        completion_rate = round((completed_day_tasks / total_day_tasks) * 100) if total_day_tasks else 0

        weekly_progress.append({
            'day_name': day.strftime('%a'),
            'date': day,
            'total': total_day_tasks,
            'completed': completed_day_tasks,
            'completion_rate': completion_rate,
        })

    context = {
        'my_tasks_count': my_tasks_count,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'overdue_count': overdue_count,
        'completion_percentage': completion_percentage,
        'todays_tasks': todays_tasks,
        'recent_activities': recent_activities,
        'weekly_progress': weekly_progress,
        'dashboard_type': 'employee',
    }
    return render(request, 'core/employee_dashboard.html', context)


def about_view(request):
    """
    About page view
    """
    context = {
        'page_title': 'About Employee Task Manager',
        'features': [
            {
                'title': 'Task Management',
                'description': 'Create, assign, and track tasks with priority levels and due dates.',
                'icon': 'fas fa-tasks'
            },
            {
                'title': 'Role-Based Access',
                'description': 'Separate dashboards and permissions for managers and employees.',
                'icon': 'fas fa-users'
            },
            {
                'title': 'Real-Time Updates',
                'description': 'Get instant updates on task status changes and comments.',
                'icon': 'fas fa-sync'
            },
            {
                'title': 'Analytics',
                'description': 'Track performance with detailed statistics and progress reports.',
                'icon': 'fas fa-chart-line'
            }
        ]
    }
    
    return render(request, 'core/about.html', context)


def contact_view(request):
    """
    Contact page view
    """
    context = {
        'page_title': 'Contact Us',
        'contact_info': {
            'email': 'support@employeetaskmanager.com',
            'phone': '+1 (555) 123-4567',
            'address': '123 Business St, Suite 100, City, State 12345'
        }
    }
    
    return render(request, 'core/contact.html', context)