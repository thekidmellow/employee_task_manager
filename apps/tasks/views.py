import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from .forms import TaskForm
from .models import Task, TaskComment


def _is_manager(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True

    userprofile = getattr(user, "userprofile", None)
    if userprofile and getattr(userprofile, "role", None) == "manager":
        return True

    return user.groups.filter(name__in=["Manager", "Managers"]).exists()


def _can_create_task(user):
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True

    userprofile = getattr(user, "userprofile", None)
    if userprofile and getattr(userprofile, "role", None) == "manager":
        return True

    return user.groups.filter(name__in=["Manager", "Managers"]).exists()


def _can_access_task(user, task: Task):
    if not user.is_authenticated:
        return False
    if _is_manager(user):
        return True
    return task.assigned_to_id == user.id or task.created_by_id == user.id


@login_required
def task_list_view(request):
    qs = Task.objects.select_related("assigned_to", "created_by")

    if not _is_manager(request.user):
        qs = qs.filter(Q(assigned_to=request.user)
                       | Q(created_by=request.user))

    now = timezone.now()
    pending_count = qs.filter(status="pending").count()
    in_progress_count = qs.filter(status="in_progress").count()
    completed_count = qs.filter(status="completed").count()
    overdue_count = qs.exclude(status="completed").filter(
        due_date__lt=now).count()

    return render(
        request,
        "tasks/task_list.html",
        {
            "tasks": qs,
            "pending_count": pending_count,
            "in_progress_count": in_progress_count,
            "completed_count": completed_count,
            "overdue_count": overdue_count,
            "is_manager": _is_manager(request.user),
        },
    )


@login_required
def task_detail_view(request, task_id):
    task = get_object_or_404(
        Task.objects.select_related("assigned_to", "created_by"), id=task_id
    )
    if not _can_access_task(request.user, task):
        return HttpResponseForbidden()

    comments = task.comments.select_related("user")
    return render(request, "tasks/task_detail.html", {"task": task, "comments": comments})


@login_required
def task_create_view(request):
    if not _can_create_task(request.user):
        return HttpResponseForbidden()

    if request.method == "POST":
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, "Task created successfully.")
            return redirect("tasks:task_list")
    else:
        form = TaskForm(user=request.user)

    return render(request, "tasks/task_form.html", {"form": form})


@login_required
def task_update_view(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if not _can_access_task(request.user, task):
        return HttpResponseForbidden()

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated successfully.")
            return redirect("tasks:task_detail", task_id=task.id)
    else:
        form = TaskForm(instance=task, user=request.user)

    return render(request, "tasks/task_form.html", {"form": form, "task": task})


@login_required
def task_delete_view(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if not _is_manager(request.user):
        return HttpResponseForbidden()
    if not _can_access_task(request.user, task):
        return HttpResponseForbidden()

    if request.method == "POST":
        task.delete()
        messages.success(request, "Task deleted successfully.")
        return redirect("tasks:task_list")

    return render(request, "tasks/task_confirm_delete.html", {"task": task})


@csrf_protect
@require_http_methods(["POST"])
@login_required
def update_task_status(request, task_id=None):
    content_type = (request.content_type or "").split(";")[0].strip().lower()

    if content_type == "application/json":
        try:
            payload = json.loads((request.body or b"{}").decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        incoming_task_id = payload.get("task_id") or task_id
        new_status = payload.get("status")
    else:
        incoming_task_id = request.POST.get("task_id") or task_id
        new_status = request.POST.get("status")

    if not incoming_task_id:
        return JsonResponse({"success": False, "error": "Missing task_id"}, status=400)
    if not new_status:
        return JsonResponse({"success": False, "error": "Missing status"}, status=400)

    task = get_object_or_404(Task, id=incoming_task_id)
    if not _can_access_task(request.user, task):
        return JsonResponse({"success": False, "error": "Forbidden"}, status=403)

    valid_statuses = {k for k, _ in Task.STATUS_CHOICES}
    if new_status not in valid_statuses:
        return JsonResponse({"success": False, "error": "Invalid status"}, status=400)

    current_status = task.status
    valid_transitions = {
        "pending": {"in_progress", "cancelled"},
        "in_progress": {"completed", "pending", "cancelled"},
        "completed": set(),
        "cancelled": {"pending"},
    }
    if new_status not in valid_transitions.get(current_status, set()):
        return JsonResponse(
            {
                "success": False,
                "error": f"Cannot change status from {current_status} to {new_status}",
            },
            status=400,
        )

    task.status = new_status
    task.save(update_fields=["status"])

    return JsonResponse(
        {"success": True, "task_id": task.id, "new_status": task.status}, status=200
    )


@require_http_methods(["GET"])
@login_required
def task_stats_api(request):
    qs = Task.objects.all()
    if not _is_manager(request.user):
        qs = qs.filter(Q(assigned_to=request.user)
                       | Q(created_by=request.user))

    now = timezone.now()

    total_tasks = qs.count()
    pending_tasks = qs.filter(status="pending").count()
    in_progress_tasks = qs.filter(status="in_progress").count()
    completed_tasks = qs.filter(status="completed").count()
    overdue_tasks = qs.exclude(status="completed").filter(
        due_date__lt=now).count()

    priority_distribution = {k: 0 for k, _ in Task.PRIORITY_CHOICES}
    for row in qs.values("priority").annotate(count=Count("id")):
        if row["priority"] in priority_distribution:
            priority_distribution[row["priority"]] = row["count"]

    status_distribution = {k: 0 for k, _ in Task.STATUS_CHOICES}
    for row in qs.values("status").annotate(count=Count("id")):
        if row["status"] in status_distribution:
            status_distribution[row["status"]] = row["count"]

    return JsonResponse(
        {
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
            "priority_distribution": priority_distribution,
            "status_distribution": status_distribution,
        },
        status=200,
    )


@require_http_methods(["GET"])
def user_list_api(request):
    User = get_user_model()
    users = list(User.objects.order_by("id").values("id", "username"))
    return JsonResponse({"users": users}, status=200)


@csrf_protect
@require_http_methods(["POST"])
@login_required
def task_comment_api(request):
    content_type = (request.content_type or "").split(";")[0].strip().lower()
    if content_type == "application/json":
        try:
            payload = json.loads((request.body or b"{}").decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        task_id = payload.get("task_id")
        comment_text = (payload.get("comment") or "").strip()
    else:
        task_id = request.POST.get("task_id")
        comment_text = (request.POST.get("comment") or "").strip()

    if not task_id:
        return JsonResponse({"success": False, "error": "Missing task_id"}, status=400)
    if not comment_text:
        return JsonResponse({"success": False, "error": "Missing comment"}, status=400)

    task = get_object_or_404(Task, id=task_id)
    if not _can_access_task(request.user, task):
        return JsonResponse({"success": False, "error": "Forbidden"}, status=403)

    model_field_names = {f.name for f in TaskComment._meta.fields}
    text_field = None
    for candidate in ("comment", "content", "text", "body", "message"):
        if candidate in model_field_names:
            text_field = candidate
            break
    if not text_field:
        return JsonResponse(
            {"success": False, "error": "Comment model missing text field"}, status=500
        )

    create_kwargs = {"task": task,
                     "user": request.user, text_field: comment_text}
    created = TaskComment.objects.create(**create_kwargs)

    return JsonResponse(
        {"success": True, "comment_id": created.id, "task_id": task.id}, status=200
    )
