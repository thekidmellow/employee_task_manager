# core/urls.py
"""
URL configuration for core app
"""

from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path(
        "dashboard/manager/",
        views.manager_dashboard_view,
        name="manager_dashboard",
    ),
    path(
        "dashboard/employee/",
        views.employee_dashboard_view,
        name="employee_dashboard",
    ),
    path("about/", views.about_view, name="about"),
    path("contact/", views.contact_view, name="contact"),
]
