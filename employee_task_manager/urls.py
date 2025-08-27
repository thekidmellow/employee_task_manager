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

    # Custom authentication URLs
    path('accounts/', include('accounts.urls')),
    
    # Task management URLs
    path('tasks/', include('tasks.urls')),
    
    # Core application URLs (dashboards, home)
    path('', include('core.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers (optional)
handler404 = 'core.views.custom_404'
handler500 = 'core.views.custom_500'

