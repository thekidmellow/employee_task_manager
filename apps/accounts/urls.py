from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),

    path('api/check-username/', views.check_username_availability, name='check_username'),
    path('api/users/', views.user_list_api, name='user_list_api'),
]
