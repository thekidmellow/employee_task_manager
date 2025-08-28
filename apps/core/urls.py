"""
URL patterns for core application views
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/manager/', views.manager_dashboard, name='manager_dashboard'),
    path('dashboard/employee/', views.employee_dashboard, name='employee_dashboard'),
]