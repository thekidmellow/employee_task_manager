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
