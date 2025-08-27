from django.shortcuts import render

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .forms import UserRegistrationForm, UserProfileForm
from .models import UserProfile


def register_view(request):
    """
    User registration with role selection
    Demonstrates form handling and validation (LO2.4)
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create user
            user = form.save()
            
            # Set user profile role
            role = form.cleaned_data.get('role')
            user_profile = user.userprofile
            user_profile.role = role
            user_profile.department = form.cleaned_data.get('department', '')
            user_profile.phone_number = form.cleaned_data.get('phone_number', '')
            user_profile.save()
            
            # Authenticate and login user
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Account created successfully! Welcome, {user.get_full_name() or user.username}!')
                
                # Redirect based on role
                if user_profile.is_manager:
                    return redirect('core:manager_dashboard')
                else:
                    return redirect('core:employee_dashboard')
            else:
                messages.error(request, 'There was an error logging you in. Please try logging in manually.')
                return redirect('accounts:login')
        else:
            # Form has errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})

