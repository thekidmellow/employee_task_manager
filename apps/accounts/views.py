from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .forms import UserRegistrationForm, UserProfileForm
from apps.tasks.models import Task


def custom_login_view(request):
    next_url = request.GET.get("next") or request.POST.get("next") or "/"

    if request.user.is_authenticated:
        return redirect(next_url)

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            remember_me = request.POST.get("remember_me") == "on"
            request.session.set_expiry(60 * 60 * 24 * 30 if remember_me else 0)

            if next_url and next_url != "/":
                return redirect(next_url)

            if user.groups.filter(name="Managers").exists():
                return redirect("core:manager_dashboard")
            return redirect("core:employee_dashboard")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm(request)

    return render(
        request,
        "registration/login.html",
        {"form": form, "next": next_url},
    )


def register_view(request):

    if request.user.is_authenticated and request.method != "POST":
        form = UserRegistrationForm()
        return render(
            request,
            "registration/register.html",
            {
                "form": form,
                "page_title": "Create Your Account",
                "already_authenticated": True,
            },
        )

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            role = form.cleaned_data.get("role", "employee")
            group_name = "Managers" if role == "manager" else "Employees"
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)

            user = authenticate(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password1"],
            )
            if user:
                login(request, user)
                messages.success(
                    request,
                    (
                        "Welcome to Employee Task Manager, "
                        f"{user.get_full_name() or user.username}!"
                    ),
                )
                return redirect("core:dashboard")
    else:
        form = UserRegistrationForm()

    return render(
        request,
        "registration/register.html",
        {
            "form": form,
            "page_title": "Create Your Account",
        },
    )


@login_required
def profile_view(request):
    user = request.user
    profile = getattr(user, "userprofile", None)

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save()

            user.first_name = form.cleaned_data.get(
                "first_name", user.first_name)
            user.last_name = form.cleaned_data.get("last_name", user.last_name)
            email = form.cleaned_data.get("email")
            if email is not None:
                user.email = email
            user.save()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Profile updated successfully!",
                        "user": {
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "email": user.email,
                            "department": profile.department or "",
                        },
                    }
                )

            messages.success(
                request, "Your profile has been updated successfully!")
            return redirect("accounts:profile")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": False,
                    "message": "Please correct the errors in the form.",
                    "errors": form.errors,
                }
            )
    else:
        form = UserProfileForm(
            instance=profile,
            initial={
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
            },
        )

    user_tasks = Task.objects.filter(assigned_to=user)
    user_stats = {
        "total_tasks": user_tasks.count(),
        "completed_tasks": user_tasks.filter(status="completed").count(),
        "pending_tasks": user_tasks.filter(status="pending").count(),
        "in_progress_tasks": user_tasks.filter(status="in_progress").count(),
    }
    user_stats["completion_rate"] = (
        round((user_stats["completed_tasks"] /
              user_stats["total_tasks"]) * 100, 1)
        if user_stats["total_tasks"]
        else 0
    )

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "user_stats": user_stats,
            "page_title": "My Profile",
        },
    )


@require_http_methods(["GET", "POST"])
def check_username_availability(request):
    if request.method == "GET":
        username = request.GET.get("username", "").strip()
    else:
        username = request.POST.get("username", "").strip()

    if not username:
        return JsonResponse({"available": False, "message": "Username is required"})
    if len(username) < 3:
        return JsonResponse(
            {
                "available": False,
                "message": "Username must be at least 3 characters long",
            }
        )

    exists = User.objects.filter(username__iexact=username).exists()
    if exists:
        return JsonResponse(
            {"available": False, "message": "This username is already taken"}
        )
    return JsonResponse({"available": True, "message": "Username is available"})


@login_required
def dashboard_redirect_view(request):
    user = request.user
    if user.groups.filter(name="Managers").exists():
        return redirect("core:manager_dashboard")
    return redirect("core:employee_dashboard")


@login_required
def change_password_view(request):
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash

    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(
                request, "Your password has been changed successfully!")
            return redirect("accounts:profile")
    else:
        form = PasswordChangeForm(request.user)

    return render(
        request,
        "registration/password_change.html",
        {
            "form": form,
            "page_title": "Change Password",
        },
    )


@login_required
def delete_account_view(request):
    if request.method == "POST":
        pending_tasks = (
            Task.objects.filter(
                assigned_to=request.user, status__in=["pending", "in_progress"]
            ).count()
        )

        if pending_tasks > 0:
            messages.error(
                request,
                (
                    "Cannot delete account. You have "
                    f"{pending_tasks} pending tasks. "
                    "Please complete or transfer them first."
                ),
            )
            return redirect("accounts:profile")

        username = request.user.username
        request.user.delete()
        messages.success(
            request,
            f"Account {username} has been deleted successfully.",
        )
        return redirect("core:home")

    user_tasks = Task.objects.filter(assigned_to=request.user)
    task_counts = {
        "total": user_tasks.count(),
        "pending": user_tasks.filter(status="pending").count(),
        "in_progress": user_tasks.filter(status="in_progress").count(),
        "completed": user_tasks.filter(status="completed").count(),
    }

    return render(
        request,
        "accounts/delete_account.html",
        {
            "task_counts": task_counts,
            "page_title": "Delete Account",
        },
    )


@login_required
def user_list_api(request):
    """
    Minimal user list for assignment/autocomplete.
    Security: Managers only; expose non-sensitive fields only.
    """
    is_manager = request.user.groups.filter(name="Managers").exists()
    if not is_manager:
        return JsonResponse({"detail": "Forbidden"}, status=403)

    users = User.objects.all().order_by("username").values(
        "id", "username", "first_name", "last_name"
    )
    return JsonResponse({"users": list(users)}, status=200)
