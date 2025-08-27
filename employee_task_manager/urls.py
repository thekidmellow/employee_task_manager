"""
Main URL configuration for Employee Task Manager
Demonstrates URL routing and app integration (LO1.3)
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Authentication URLs (built-in Django auth views)
    path('accounts/', include('django.contrib.auth.urls')),
