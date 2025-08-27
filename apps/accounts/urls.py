# accounts/urls.py
"""
URL patterns for user authentication and profile management
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Registration
    path('register/', views.register_view, name='register'),
    
    # Profile management
    path('profile/', views.profile_view, name='profile'),
    
    # AJAX endpoints
    path('api/check-username/', views.check_username_availability, name='check_username'),
    path('api/users/', views.user_list_api, name='user_list_api'),
]
