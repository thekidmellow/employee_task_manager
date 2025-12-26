def can_create_task(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"can_create_task": False, "is_manager": False}

    is_manager = False
    if user.is_staff or user.is_superuser:
        is_manager = True
    else:
        userprofile = getattr(user, "userprofile", None)
        if userprofile and getattr(userprofile, "role", None) == "manager":
            is_manager = True
        elif user.groups.filter(name__in=["Manager", "Managers"]).exists():
            is_manager = True

    return {"is_manager": is_manager, "can_create_task": is_manager}


def user_permissions(request):
    return can_create_task(request)
