from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'accounts'

urlpatterns = [
    # ✅ Logout (GET allowed) – redirect after logout
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),

    # Registration & profile
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),

    # AJAX
    path('api/check-username/', views.check_username_availability, name='check_username'),
    path('api/users/', views.user_list_api, name='user_list_api'),
]
