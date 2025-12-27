from django.contrib.auth import get_user_model
from apps.tasks.models import Task

User = get_user_model()


def make_user(username="u1", email="u1@example.com", password="pass12345", is_manager=False):
    u = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )
    if is_manager:
        u.is_staff = True
        u.save(update_fields=["is_staff"])
    return u


def make_task(**overrides):
    if "assigned_to" not in overrides:
        overrides["assigned_to"] = make_user(
            username="assignee", email="assignee@example.com")
    if "created_by" not in overrides:
        overrides["created_by"] = overrides["assigned_to"]
    defaults = dict(
        title="T1",
        description="D",
        status="pending",
        priority="medium",
    )
    defaults.update(overrides)
    return Task.objects.create(**defaults)
