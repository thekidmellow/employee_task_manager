from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"

urlpatterns = [
    # Authentication
    path("login/", views.custom_login_view, name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register_view, name="register"),

    # Profile management
    path("profile/", views.profile_view, name="profile"),

    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(
            template_name="registration/password_change.html",
            success_url=reverse_lazy("accounts:password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "password/change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="registration/password_change_done.html",
        ),
        name="password_change_done",
    ),

    path("delete/", views.delete_account_view, name="delete_account"),

    # AJAX endpoints
    path(
        "api/check-username/",
        views.check_username_availability,
        name="check_username",
    ),

    # Dashboard redirect
    path(
        "dashboard/",
        views.dashboard_redirect_view,
        name="dashboard_redirect",
    ),
]
