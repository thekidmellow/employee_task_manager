from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


def make_user(username, email=None, group=None, password="pass12345"):
    u = User.objects.create_user(
        username=username,
        email=email or f"{username}@example.com",
        password=password,
    )
    if group:
        g, _ = Group.objects.get_or_create(name=group)
        u.groups.add(g)
    return u
